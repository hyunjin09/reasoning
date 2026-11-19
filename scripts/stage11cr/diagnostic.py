"""Two fixed cases: restore sampling only on the failed SDPA path."""
import argparse
import copy
import os
import socket
import time
from pathlib import Path
import torch
from scripts.stage11cr.common import ROOT,load,save,sha,now,verify_frozen
from scripts.stage11b.generation import runtime,prepare
from scripts.stage11b.protocol import trim_generated
from visual_reasoning.stage0.modeling import runtime_environment


def main(manifest_path, manifest_sha256, shard_id, max_seconds):
    start=time.monotonic();job=os.environ['SLURM_JOB_ID'];cfg=verify_frozen()
    assert sha(manifest_path)==manifest_sha256
    m=load(manifest_path);assert m['frozen'] and m['queue']=='diagnostic'
    for p,d in m['source_sha256'].items():assert sha(p)==d,p
    assert socket.gethostname().split('.')[0] in cfg['allowed_nodes'] and torch.cuda.device_count()==1
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    shard=next(s for s in m['shards'] if s['id']==shard_id)
    info=cfg['models'][shard['model_key']]
    for p,d in info['files_sha256'].items():assert sha(Path(info['checkpoint'])/p)==d
    proc,model=runtime(info);queue=ROOT/'diagnostic'
    save(queue/'workers'/job/'environment.json',dict(at=now(),slurm_job_id=job,node=socket.gethostname(),
        **runtime_environment(Path(info['checkpoint']),model,8192)))
    completed=0
    for row in shard['rows']:
        if time.monotonic()-start>max_seconds-120:break
        dest=queue/'results'/row['task_id'];assert not dest.exists()
        assert sha(row['image'])==row['image_sha256']
        batch,metas=prepare(proc,[row]);save(dest/'input.json',metas[0])
        # Both conditions start with identical fresh-call state. Only decoding differs.
        model.model.rope_deltas=None;torch.manual_seed(row['seed']);torch.cuda.manual_seed_all(row['seed'])
        gen=copy.deepcopy(model.generation_config)
        sampled=row['diagnostic_condition']=='sampling_only'
        gen.do_sample=sampled;gen.temperature=1. if sampled else None
        gen.top_p=.95 if sampled else None;gen.top_k=20 if sampled else None
        gen.repetition_penalty=1.;gen.max_new_tokens=8192;gen.use_cache=True
        gen.pad_token_id=proc.tokenizer.pad_token_id
        eos=gen.eos_token_id;eos={eos} if isinstance(eos,int) else set(eos)
        torch.cuda.reset_peak_memory_stats();torch.cuda.synchronize();t=time.monotonic()
        print('START',row['task_id'],flush=True)
        with torch.inference_mode():
            out=model.generate(**batch,generation_config=gen,return_dict_in_generate=False,
                output_scores=False,output_logits=False,max_time=max(1,max_seconds-(time.monotonic()-start)-45))
        torch.cuda.synchronize();elapsed=time.monotonic()-t
        ids,normal,capped=trim_generated(out[0,batch['input_ids'].shape[1]:].tolist(),eos,8192)
        text=proc.tokenizer.decode(ids,skip_special_tokens=False)
        g=dict(generated_token_ids=ids,raw_decoded_response=text,tokens=len(ids),normal_eos=normal,
            at_length_cap=capped,budget_interrupted=not normal and not capped,batch_seconds=elapsed,
            peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),peak_gpu_reserved_bytes=torch.cuda.max_memory_reserved())
        save(dest/'generation.json',g)
        save(dest/'result.json',dict(at=now(),task_id=row['task_id'],arm=row['arm'],condition=row['diagnostic_condition'],
            item_id=row['item_id'],slurm_job_id=job,cap=8192,generation_sha256=sha(dest/'generation.json'),
            input_sha256=sha(dest/'input.json'),manifest_sha256=manifest_sha256,
            **{k:v for k,v in g.items() if k not in ['generated_token_ids','raw_decoded_response']}))
        completed+=not g['budget_interrupted'];print('COMPLETE',row['task_id'],len(ids),normal,capped,flush=True)
        del batch,out
    save(queue/'workers'/job/'exit.json',dict(at=now(),complete=completed==len(shard['rows']),
        completed=completed,shard_total=len(shard['rows']),elapsed_seconds=time.monotonic()-start,finite_queue=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--manifest-sha256',required=True)
    p.add_argument('--shard',required=True);p.add_argument('--max-seconds',type=int,required=True)
    a=p.parse_args();main(a.manifest,a.manifest_sha256,a.shard,a.max_seconds)
