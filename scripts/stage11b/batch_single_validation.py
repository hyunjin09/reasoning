"""Bounded technical comparison; never substitutes outputs into native evidence."""
import os
import socket
import time
import gc
import torch
from scripts.stage11b.common import ROOT, load, save, sha, now
from scripts.stage11b.generation import runtime, prepare, generate


def prefix_length(a, b):
    return next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))


def main():
    started = time.monotonic()
    cfg = load(ROOT/'config.json')
    for path, h in cfg['source_sha256'].items():
        assert sha(path) == h
    assert torch.cuda.device_count() == 1
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    comparisons = []
    manifest = load(ROOT/'source_feasible_tasks.json')
    for mode in ['instruct', 'thinking']:
        assert time.monotonic()-started < 300, 'Technical diagnostic must remain bounded'
        proc, model = runtime(cfg['models'][mode])
        rows = next(s['rows'] for s in manifest['shards'] if s['id']==mode+'_0')[:4]
        batch, metas = prepare(proc, rows)
        with torch.inference_mode():
            logits = model(**batch, logits_to_keep=1, use_cache=False).logits[:, -1].float()
            logp = logits.log_softmax(-1)
        batched = generate(proc, model, batch, 512, max_time=90)
        assert all(not r['budget_interrupted'] for r in batched)
        for i, row in enumerate(rows):
            single, single_meta = prepare(proc, [row])
            assert single_meta[0]['input_ids_sha256'] == metas[i]['input_ids_sha256']
            assert single_meta[0]['image_grid_thw'] == metas[i]['image_grid_thw']
            with torch.inference_mode():
                one_logits = model(**single, logits_to_keep=1, use_cache=False).logits[0, -1].float()
                one_logp = one_logits.log_softmax(-1)
                kl = (logp[i].exp()*(logp[i]-one_logp)).sum().item()
            one = generate(proc, model, single, 512, max_time=90)[0]
            assert not one['budget_interrupted']
            original = load(ROOT/'source_feasible/results'/row['task_id']/'generation.json')['generated_token_ids'][:512]
            comparisons.append(dict(task_id=row['task_id'], model_key=mode,
                exact_input_ids_and_grid_match=True, prefill_kl_batch_to_single=kl,
                prefill_max_abs_logit_difference=(logits[i]-one_logits).abs().max().item(),
                prefill_argmax_match=logits[i].argmax().item()==one_logits.argmax().item(),
                batch_tokens=len(batched[i]['generated_token_ids']), single_tokens=len(one['generated_token_ids']),
                common_prefix_batch_single=prefix_length(batched[i]['generated_token_ids'], one['generated_token_ids']),
                common_prefix_original_batch=prefix_length(original, batched[i]['generated_token_ids']),
                batch_single_exact=batched[i]['generated_token_ids']==one['generated_token_ids'],
                original_batch_exact=original==batched[i]['generated_token_ids'],
                single_normal_eos=one['normal_eos'], single_generated_token_ids=one['generated_token_ids'],
                batch_generated_token_ids=batched[i]['generated_token_ids']))
            print('CHECK', row['task_id'], 'KL', kl, 'common_prefix', comparisons[-1]['common_prefix_batch_single'], flush=True)
            del single, one_logits, one_logp, one
        del batch, batched, model, proc, logits, logp
        gc.collect()
        torch.cuda.empty_cache()
    save(ROOT/'audit/batch_single_validation.json', dict(at=now(), diagnostic_completed=True,
        slurm_job_id=os.environ['SLURM_JOB_ID'], node=socket.gethostname(),
        gpu_model=torch.cuda.get_device_name(0), elapsed_seconds=time.monotonic()-started,
        selection='First frozen resumed batch in each arm; all four rows retained, no correctness-based sampling',
        scientific_generation_sources_unchanged=True, never_used_as_native_or_oracle_results=True,
        cap=512, comparisons=comparisons,
        interpretation_boundary='Short-prefix numerical/behavioral comparison only; does not prove equivalence of complete long trajectories or identify the cause of noncompletion.'))
    print('DIAGNOSTIC_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
