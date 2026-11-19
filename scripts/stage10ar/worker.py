"""Finite primary image bundles, preserving native cache between frozen anchors."""
import os,time,gc,traceback
import torch
from scripts.stage10ar.common import ROOT,load,save,sha,now
from scripts.stage10ar.runtime import load_runtime,inputs,start,resume,fresh,cached,record,environment
from scripts.stage10ar.protocol import mask_cutoff
from visual_reasoning.stage9a3.access import AccessMask


@torch.inference_mode()
def main():
    mp=ROOT/'audit/primary_manifest.json';m=load(mp);assert m['frozen']
    for p,d in m['source_sha256'].items():assert sha(p)==d,p
    assert load(ROOT/'audit/technical_validation.json')['pass_all'] and m['validation_sha256']==sha(ROOT/'audit/technical_validation.json')
    cfg,processor,model=load_runtime();sid=os.environ['SLURM_JOB_ID'];root=ROOT/'primary';done=[]
    env=environment(model);env['stage10ar_config_sha256']=sha(ROOT/'config.json');save(root/'workers'/sid/'environment.json',env)
    events={r['query_id']:r for r in load(ROOT/'stage10ar_anchor_annotations.json')['rows']}
    for q in m['query_order']:
        rows=[r for r in m['rows'] if r['query_id']==q and r['execution']=='run']
        if not rows:continue
        claim=root/'claims'/q;claim.parent.mkdir(parents=True,exist_ok=True)
        try:claim.mkdir()
        except FileExistsError:continue
        save(claim/'owner.json',dict(at=now(),slurm_job_id=sid));e=events[q];native=None;prefix_seconds=0
        prepared,meta=inputs(processor,model,e['task']);p=meta['prompt_length']
        for r in sorted(rows,key=lambda r:(r['prefix_tokens'],r['condition']!='image_off')):
            n=r['prefix_tokens'];ids=r['prefix_ids'];torch.cuda.reset_peak_memory_stats()
            if r['condition']=='image_off':
                # Existing ZERO is normally reused. This also makes reserve queues finite.
                begin=time.perf_counter();required=max(1,n)
                if native is None:native,_=start(model,prepared,cfg['seed'],required,sample=False)
                else:
                    old=native.sequences.shape[1]-p
                    if required>old:native,_=resume(model,native,required-old,sample=False)
                prefix_seconds+=time.perf_counter()-begin
                expected=load(e['generation_path'])['generated_token_ids'][:required]
                assert native.sequences[0,p:].tolist()==expected and native.cache.get_seq_length()==p+required-1
                with AccessMask(backend='qwen3',visual=meta['visual'],prompt_length=p,layers=36,layer_cutoff=36,token_cutoff=mask_cutoff(n)):
                    if n:g=cached(processor,model,native,p,ids)
                    else:
                        begin=time.perf_counter();branch,_=resume(model,native,511,sample=False)
                        g=record(processor,model,branch.sequences[0,p:].tolist(),[],time.perf_counter()-begin)
                details=dict(mode='cached_image_off',original_cache_preserved=True,prior_prefix_exact=True,input=meta,
                    mask_cutoff=mask_cutoff(n),first_masked_absolute_query=p+max(1,n)-1,A0_prefill_first_token_retained=n==0)
            else:g,details=fresh(processor,model,e['task'],ids,cfg['seed'])
            save(r['generation_path'],g)
            save(r['result_path'],dict(at=now(),query_id=q,condition=r['condition'],anchor=r['anchor'],slurm_job_id=sid,
                generation_sha256=sha(r['generation_path']),manifest_sha256=sha(mp),config_sha256=sha(ROOT/'config.json'),
                prefix_tokens=n,remaining_tokens=512-n,input=details,runtime_seconds=g['runtime_seconds'],
                peak_allocated_bytes=torch.cuda.max_memory_allocated(),peak_reserved_bytes=torch.cuda.max_memory_reserved()))
            done.append(r['task_id']);print('COMPLETE',r['task_id'],g['continuation_tokens'],round(g['runtime_seconds'],3),flush=True)
        save(root/'bundles'/f'{q}.json',dict(at=now(),query_id=q,native_prefix_seconds=prefix_seconds,slurm_job_id=sid,all_native_prefixes_exact=True))
        del prepared,native;gc.collect();torch.cuda.empty_cache()
    save(root/'workers'/sid/'complete.json',dict(at=now(),tasks=done))


if __name__=='__main__':
    try:main()
    except Exception as e:
        save(ROOT/f'audit/worker_failure_{os.environ.get("SLURM_JOB_ID","local")}.json',dict(at=now(),error=repr(e),traceback=traceback.format_exc()));raise
