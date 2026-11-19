"""Finite score-blind replay/rerun worker, batch one and fresh call state."""
import argparse
import hashlib
import os
import socket
import time
import traceback
from pathlib import Path
import torch
from scripts.stage11cr.common import ROOT, load, save, sha, now, verify_frozen
from scripts.stage11b.generation import prepare, runtime as failed_runtime, generate as failed_generate
from visual_reasoning.stage0.modeling import load_runtime, generate_once, runtime_environment
from visual_reasoning.stage8b.v2_protocol import prepared_input, generation_parameters


def main(manifest_path, manifest_sha256, shard_id, max_seconds):
    started=time.monotonic();job=os.environ['SLURM_JOB_ID']
    assert sha(manifest_path)==manifest_sha256
    manifest=load(manifest_path);cfg=verify_frozen()
    assert manifest['frozen'] and manifest['config_sha256']==sha(ROOT/'config.json')
    for path,digest in manifest['source_sha256'].items():assert sha(path)==digest,path
    assert torch.cuda.device_count()==1 and socket.gethostname().split('.')[0] in cfg['allowed_nodes']
    torch.backends.cuda.matmul.allow_tf32=False;torch.backends.cudnn.allow_tf32=False
    shard=next(s for s in manifest['shards'] if s['id']==shard_id)
    info=cfg['models'][shard['model_key']]
    for name,digest in info['files_sha256'].items():assert sha(Path(info['checkpoint'])/name)==digest,name
    protocol=manifest['protocol'];queue=ROOT/manifest['queue']
    if protocol in ['historical','historical_greedy']:
        proc,model=load_runtime(Path(info['checkpoint']),'cuda:0')
    else:proc,model=failed_runtime(info)
    save(queue/'workers'/job/'environment.json',dict(at=now(),slurm_job_id=job,node=socket.gethostname(),
        shard_id=shard_id,protocol=protocol,manifest_sha256=manifest_sha256,batch_size=1,tf32=False,
        **runtime_environment(Path(info['checkpoint']),model,max(r['max_new_tokens'] for r in shard['rows']))))
    complete=0
    for row in shard['rows']:
        if (queue/'STOP').exists() or time.monotonic()-started>max_seconds-120:break
        dest=queue/'results'/row['task_id']
        try:
            assert not dest.exists(),'Never overwrite or duplicate an attempted row'
            assert not {'answer','ground_truth_answer','facts'}.intersection(row)
            claim=queue/'claims'/row['task_id'];claim.mkdir(parents=True,exist_ok=False)
            save(claim/'owner.json',dict(at=now(),slurm_job_id=job,shard=shard_id))
            if row['condition']=='native':assert sha(row['image'])==row['image_sha256']
            if protocol in ['historical','historical_greedy'] and row['condition']=='native':
                batch,meta=prepared_input(proc,dict(row,answer=None,question=row['generation_query']))
                assert meta.pop('ground_truth_answer') is None
                meta.update(visual_token_count=len(meta['visual_token_indices']),image_present=True,batch_left_padding=0)
            else:
                batch,metas=prepare(proc,[row]);meta=metas[0]
            if row['condition']!='native':
                assert not any(k in batch for k in ['pixel_values','image_grid_thw','past_key_values'])
                assert meta['visual_token_count']==0
            # Record every prepared tensor identity, allowing a separate input audit.
            meta['tensor_hashes']={k:hashlib.sha256(v.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()
                for k,v in batch.items() if isinstance(v,torch.Tensor)}
            meta['rope_deltas_before_call']=None if model.model.rope_deltas is None else model.model.rope_deltas.detach().cpu().tolist()
            save(dest/'input.json',meta)
            print('START',row['task_id'],'cap',row['max_new_tokens'],flush=True)
            remaining=max(1,max_seconds-(time.monotonic()-started)-45)
            if protocol=='failed':
                out,=failed_generate(proc,model,batch,row['max_new_tokens'],max_time=remaining)
            else:
                kwargs=generation_parameters()
                if protocol=='historical_greedy':kwargs=dict(do_sample=False,temperature=None,top_p=None,top_k=None,repetition_penalty=1.)
                kwargs['max_time']=remaining
                g=generate_once(model,proc,batch,row['max_new_tokens'],recorder=None,
                    generation_kwargs=kwargs,seed=row['seed'],collect_predictive_metrics=False)
                ids=g['generated_token_ids'];eos=model.generation_config.eos_token_id
                eos={eos} if isinstance(eos,int) else set(eos)
                normal=bool(ids and ids[-1] in eos);capped=len(ids)>=row['max_new_tokens'] and not normal
                out=dict(generated_token_ids=ids,raw_decoded_response=g['raw_decoded_response'],tokens=len(ids),
                    normal_eos=normal,at_length_cap=capped,budget_interrupted=not normal and not capped,
                    has_think_end='</think>' in g['raw_decoded_response'],batch_seconds=g['runtime']['elapsed_seconds'],
                    peak_gpu_allocated_bytes=g['runtime']['peak_gpu_allocated_bytes'],
                    peak_gpu_reserved_bytes=g['runtime']['peak_gpu_reserved_bytes'],generation_parameters=g['generation_parameters'])
            save(dest/'generation.json',out)
            receipt={k:v for k,v in out.items() if k not in ['generated_token_ids','raw_decoded_response']}
            save(dest/'result.json',dict(receipt,at=now(),task_id=row['task_id'],arm=row['arm'],family_id=row['family_id'],
                item_id=row['item_id'],condition=row['condition'],cap=row['max_new_tokens'],slurm_job_id=job,
                protocol=protocol,generation_sha256=sha(dest/'generation.json'),input_sha256=sha(dest/'input.json'),
                manifest_sha256=manifest_sha256,config_sha256=sha(ROOT/'config.json')))
            complete+=not out['budget_interrupted']
            print('COMPLETE',row['task_id'],out['tokens'],'cap',out['at_length_cap'],'interrupted',out['budget_interrupted'],flush=True)
            del batch,out
        except Exception as exc:
            save(queue/'workers'/job/'failure.json',dict(at=now(),task_id=row['task_id'],error=repr(exc),traceback=traceback.format_exc()))
            raise
    save(queue/'workers'/job/'exit.json',dict(at=now(),elapsed_seconds=time.monotonic()-started,
        finite_queue=True,completed=complete,shard_total=len(shard['rows']),complete=complete==len(shard['rows'])))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--manifest-sha256',required=True)
    p.add_argument('--shard',required=True);p.add_argument('--max-seconds',type=int,required=True)
    a=p.parse_args();main(a.manifest,a.manifest_sha256,a.shard,a.max_seconds)
