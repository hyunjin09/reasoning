"""One bounded two-device allocator comparison after two long-context OOMs."""
import os
rank=int(os.environ['LOCAL_RANK'])
os.environ['PYTORCH_CUDA_ALLOC_CONF']='expandable_segments:True' if rank else 'backend:native'
import argparse,hashlib,time
from pathlib import Path
import torch
from scripts.stage6b.common import ROOT,OUT,read_json,read_jsonl,write_json,sha
from visual_reasoning.stage0.modeling import load_runtime
from visual_reasoning.stage6a.runtime import prepare_condition
from visual_reasoning.stage6b.protocol import assigned_rank
from visual_reasoning.stage6b.text_interface import prefill_condition
from visual_reasoning.stage6b.dense_partition import endpoint_partition
from visual_reasoning.stage3c9.streaming import advance_streaming_state


def stats():
    s=torch.cuda.memory_stats()
    return {k:s.get(k) for k in ['allocated_bytes.all.current','allocated_bytes.all.peak',
        'reserved_bytes.all.current','reserved_bytes.all.peak','inactive_split_bytes.all.current',
        'inactive_split_bytes.all.peak','num_alloc_retries','num_ooms']}


def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);args=p.parse_args()
    config=read_json(OUT/'config/stage6b_config.json')
    assert assigned_rank(os.environ,torch.cuda.device_count(),config['slurm_allocation'])==rank
    torch.cuda.set_device(rank)
    entry=read_jsonl(OUT/'trajectory/residency_mechanics_manifest.jsonl')[0]
    span=max(entry['spans'],key=lambda s:(s['token_end']-8)%2048*s['token_end'])
    end=span['token_end'];boundary,partial,_=endpoint_partition(end)
    processor,model=load_runtime(Path(config['model_checkpoint']),device=f'cuda:{rank}')
    prepared,meta=prepare_condition(processor,entry['row'],f'cuda:{rank}')
    state,audit=prefill_condition(model,prepared,False);del prepared
    ids=read_json(entry['native_generation_path'])['generated_token_ids']
    ranges=[(a,a+2048) for a in range(0,boundary,2048)]+partial
    steps=[];failure=None;start=time.perf_counter()
    for left,right in ranges:
        before=stats()
        try:
            advance_streaming_state(model=model,state=state,token_ids=ids[left:right],seed=1234,chunk_size=2048,release_allocator_cache=True)
        except torch.OutOfMemoryError as exc:
            failure={'left':left,'right':right,'before':before,'after':stats(),'message':str(exc)}
            break
        steps.append({'left':left,'right':right,'memory':stats(),
            'logits_sha256':hashlib.sha256(state.last_logits.float().cpu().numpy().tobytes()).hexdigest()})
        print(f'rank={rank} diagnostic prefix={right} inactive={stats()["inactive_split_bytes.all.current"]}',flush=True)
    write_json(OUT/'raw'/args.run_id/f'rank_{rank:02d}.json',{'rank':rank,'slurm_job_id':os.environ['SLURM_JOB_ID'],
        'allocator':os.environ['PYTORCH_CUDA_ALLOC_CONF'],'event_id':entry['id'],'target_endpoint':end,
        'target_root_generated_length':end-8,'completed':failure is None,'failure':failure,'steps':steps,
        'runtime_seconds':time.perf_counter()-start,'gpu_name':torch.cuda.get_device_name(rank),
        'worker_sha256':sha(ROOT/'scripts/stage6b/diagnose_native_memory.py'),
        'scope':'Canonical single-cache prefix replay for allocator diagnosis only; no causal/passive result or cohort decision.'},freeze=True)
    print(f'rank={rank} DIAGNOSTIC_COMPLETE success={failure is None}',flush=True)


if __name__=='__main__':main()
