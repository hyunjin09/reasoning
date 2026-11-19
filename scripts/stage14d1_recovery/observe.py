"""Read-only diagnostic hooks in the Slurm GPU process; no sampling changes."""
import os, json, hashlib
from pathlib import Path
from vllm.v1.core.sched.scheduler import Scheduler as BaseScheduler
from vllm.v1.worker.gpu_worker import Worker as BaseWorker

def append(name, value):
    root=Path(os.environ['SAVA_RECOVERY_TRACE'])
    root.mkdir(parents=True,exist_ok=True)
    with (root/name).open('a') as f:
        f.write(json.dumps(value)+'\n')

class Scheduler(BaseScheduler):
    def schedule(self):
        result=super().schedule()
        if result.num_scheduled_tokens:
            append('schedule.jsonl',dict(tokens=result.num_scheduled_tokens,
                   total=result.total_num_scheduled_tokens,
                   new=[r.req_id for r in result.scheduled_new_reqs]))
        return result

class Worker(BaseWorker):
    def load_model(self):
        super().load_model()
        import numpy as np
        import vllm.v1.sample.ops.topk_topp_sampler as sampling
        runner=self.model_runner
        original_forward=runner.sampler.forward
        original_random=sampling.random_sample
        current=[]

        def digest(tensor):
            return hashlib.sha256(tensor.cpu().numpy().tobytes()).hexdigest()

        def random_sample(probs,generators):
            selected=[(i,rid) for i,rid in enumerate(current)
                      if rid and rid.startswith('rng_') and ('_107_' in rid or '_33_' in rid)]
            before={i:probs[i].detach().cpu().clone() for i,_ in selected}
            state={i:digest(generators[i].get_state()) for i,_ in selected if i in generators}
            out=original_random(probs,generators)
            for i,rid in selected:
                # original_random divides probabilities in place by exponential noise.
                ratio=probs[i].detach().cpu()
                indices=(before[i]>0).nonzero().flatten()
                append('sampling.jsonl',dict(request_id=rid,step=steps[rid],
                    rng_before=state.get(i),rng_after=digest(generators[i].get_state()) if i in generators else None,
                    seed=generators[i].initial_seed() if i in generators else None,
                    token_ids=indices.tolist(),probabilities=before[i][indices].tolist(),
                    probability_over_noise=ratio[indices].tolist(),sampled_token=int(out[i])))
            return out

        steps={}
        invocations={}
        def forward(logits,sampling_metadata):
            nonlocal current
            current=list(runner.input_batch.req_ids[:logits.shape[0]])
            for i,rid in enumerate(current):
                if not rid or not rid.startswith('rng_'):
                    continue
                steps[rid]=len(sampling_metadata.output_token_ids[i])
                invocations[rid]=invocations.get(rid,0)+1
                if '_107_' not in rid and '_33_' not in rid:
                    continue
                values=logits[i].detach().float().cpu().numpy().copy()
                order=np.argsort(values)[-32:][::-1]
                append('logits.jsonl',dict(request_id=rid,step=steps[rid],
                    logits_sha256=hashlib.sha256(values.tobytes()).hexdigest(),
                    top_ids=order.tolist(),top_logits=values[order].tolist(),batch=list(current),
                    generated_prefix_token_ids=list(sampling_metadata.output_token_ids[i]),invocation=invocations[rid]))
                if steps[rid] in range(28,33) or steps[rid] in range(43,48):
                    np.savez_compressed(Path(os.environ['SAVA_RECOVERY_TRACE'])/f'{rid}_{steps[rid]}_{invocations[rid]}_logits.npz',logits=values)
            return original_forward(logits,sampling_metadata)

        sampling.random_sample=random_sample
        runner.sampler.forward=forward
