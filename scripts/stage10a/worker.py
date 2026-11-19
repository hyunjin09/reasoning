"""Finite per-image bundles: three clean text replays and three cache-preserving masks."""
import os,time,gc,traceback
import torch
from scripts.stage10a.common import ROOT,load,save,sha,now
from scripts.stage10a.runtime import load_runtime,inputs,start,resume,fresh,cached,environment
from scripts.stage10a.protocol import anchor_cutoff
from visual_reasoning.stage9a3.access import AccessMask


@torch.inference_mode()
def main():
    mp=ROOT/'audit/gate_a_manifest.json';manifest=load(mp)
    assert manifest['frozen'] and manifest['config_sha256']==sha(ROOT/'config.json')
    for p,d in manifest['source_sha256'].items():assert sha(p)==d
    assert manifest['validation_sha256']==sha(ROOT/'audit/technical_validation.json')
    assert load(ROOT/'audit/technical_validation.json')['pass_all']
    cfg,processor,model=load_runtime();sid=os.environ['SLURM_JOB_ID'];root=ROOT/'gate_a'
    env=environment(model);env['stage10a_config_sha256']=sha(ROOT/'config.json')
    save(root/'workers'/sid/'environment.json',env)
    events={r['query_id']:r for r in load(ROOT/'stage10a_event_selection.json')['rows']};done=[]
    for query in manifest['query_order']:
        claim=root/'claims'/query;claim.parent.mkdir(parents=True,exist_ok=True)
        try:claim.mkdir()
        except FileExistsError:continue
        save(claim/'owner.json',dict(at=now(),slurm_job_id=sid));event=events[query]
        print('IMAGE_START',query,now(),flush=True)
        prepared,meta=inputs(processor,model,event['task']);prompt=meta['prompt_length'];native=None;prefix_time=0
        for anchor in ('pre','emit','post'):
            a=event['anchors'][anchor];n=a['native_tokens'];begin=time.perf_counter()
            if native is None:native,_=start(model,prepared,cfg['seed'],n,sample=False)
            else:
                already=native.sequences.shape[1]-prompt
                native,_=resume(model,native,n-already,sample=False)
            prefix_time+=time.perf_counter()-begin
            assert native.sequences[0,prompt:].tolist()==a['prefix_ids'],f'Native prefix mismatch: {query} {anchor}'
            assert native.cache.get_seq_length()==prompt+n-1
            for condition in ('image_off','text_only'):
                row=next(r for r in manifest['rows'] if (r['query_id'],r['anchor'],r['condition'])==(query,anchor,condition))
                torch.cuda.reset_peak_memory_stats()
                if condition=='image_off':
                    with AccessMask(backend='qwen3',visual=meta['visual'],prompt_length=prompt,layers=36,layer_cutoff=36,
                                    token_cutoff=anchor_cutoff(n)):
                        generation=cached(processor,model,native,prompt,a['prefix_ids'])
                    details=dict(mode='cached_image_off',input=meta,original_cache_preserved=True,
                        cache_length_before=prompt+n-1,first_masked_absolute_query=prompt+n-1,
                        mask_cutoff=n-1,prior_prefix_exact=True)
                else:generation,details=fresh(processor,model,event['task'],a['prefix_ids'],cfg['seed'])
                assert generation['tokens']<=512
                save(row['generation_path'],generation)
                save(row['result_path'],dict(at=now(),query_id=query,condition=condition,anchor=anchor,
                    slurm_job_id=sid,generation_sha256=sha(row['generation_path']),manifest_sha256=sha(mp),
                    config_sha256=sha(ROOT/'config.json'),prefix_tokens=n,remaining_tokens=512-n,input=details,
                    runtime_seconds=generation['runtime_seconds'],peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                    peak_reserved_bytes=torch.cuda.max_memory_reserved()))
                done.append(row['task_id']);print('COMPLETE',row['task_id'],generation['continuation_tokens'],round(generation['runtime_seconds'],3),flush=True)
                assert native.cache.get_seq_length()==prompt+n-1
        save(root/'bundles'/f'{query}.json',dict(at=now(),query_id=query,slurm_job_id=sid,native_prefix_seconds=prefix_time,
             native_replay_to_post_tokens=event['anchors']['post']['native_tokens'],conditions_completed=6,all_prefixes_exact=True))
        del prepared,native;gc.collect();torch.cuda.empty_cache()
    save(root/'workers'/sid/'complete.json',dict(at=now(),tasks=done))


if __name__=='__main__':
    try:main()
    except Exception as e:
        save(ROOT/f'audit/worker_failure_{os.environ.get("SLURM_JOB_ID","local")}.json',dict(at=now(),error=repr(e),traceback=traceback.format_exc()));raise
