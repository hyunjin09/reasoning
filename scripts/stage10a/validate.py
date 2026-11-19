"""Eight disjoint actual-model checks; no scientific outcomes used for design."""
import os,time,gc,traceback
import torch
from scripts.stage10a.common import ROOT,OLD,load,save,sha,now
from scripts.stage10a.runtime import load_runtime,inputs,text_inputs,start,resume,environment
from scripts.stage10a.protocol import anchor_cutoff
from visual_reasoning.stage9a3.access import AccessMask


@torch.inference_mode()
def main():
    cfg,processor,model=load_runtime()
    env=environment(model);env.update(stage10a_config_sha256=sha(ROOT/'config.json'))
    attempt=ROOT/'audit/technical_attempts'/os.environ['SLURM_JOB_ID']
    save(attempt/'environment.json',env)
    tasks=[r for r in load(OLD/'audit/inference_tasks.json')['rows'] if r['split']=='technical'];paths=[]
    for task in tasks:
        begin=time.perf_counter();prepared,meta=inputs(processor,model,task);p=meta['prompt_length'];n=16
        native,_=start(model,prepared,cfg['seed'],40,sample=False)
        prefix,_=start(model,prepared,cfg['seed'],n,sample=False)
        ids=prefix.sequences[0,p:].tolist();assert len(ids)==n
        cache_before=prefix.cache.get_seq_length();rope_before=prefix.rope.clone()
        original,_=resume(model,prefix,24,sample=False)
        assert torch.equal(original.sequences,native.sequences),'Cached FULL continuation mismatch'
        assert prefix.cache.get_seq_length()==cache_before==p+n-1
        assert torch.equal(prefix.rope,rope_before)
        args=dict(backend='qwen3',visual=meta['visual'],prompt_length=p,layers=36,layer_cutoff=36)
        with AccessMask(**args,token_cutoff=None,audit=True) as noop:
            unchanged,unout=resume(model,prefix,8,sample=False,logits=True)
        reference,refout=resume(model,prefix,8,sample=False,logits=True)
        assert torch.equal(unchanged.sequences,reference.sequences)
        assert all(torch.equal(a,b) for a,b in zip(unout.logits,refout.logits))
        assert all(not r['blocked_absolute_queries'] for r in noop.records)
        with AccessMask(**args,token_cutoff=anchor_cutoff(n),audit=True) as mask:
            masked,_=resume(model,prefix,8,sample=False)
        assert {r['layer'] for r in mask.records}==set(range(36))
        assert min(r['query_start'] for r in mask.records)==p+n-1
        assert all(r['blocked_absolute_queries']==list(range(r['query_start'],r['query_start']+r['query_length']))
                   and r['masked_probability_max']==0 for r in mask.records)
        assert prefix.cache.get_seq_length()==cache_before and torch.equal(prefix.rope,rope_before)
        text,tm=text_inputs(processor,model,task,ids)
        assert not any(k in text for k in ('pixel_values','image_grid_thw','past_key_values'))
        a,ao=start(model,text,cfg['seed'],8,sample=False,logits=True)
        b,bo=start(model,text,cfg['seed'],8,sample=False,logits=True)
        assert torch.equal(a.sequences,b.sequences) and all(torch.equal(x,y) for x,y in zip(ao.logits,bo.logits))
        assert a.cache is not prefix.cache and a.cache.get_seq_length()==text['input_ids'].shape[1]+7
        assert a.sequences[0,tm['prompt_length']:tm['prompt_length']+n].tolist()==ids
        path=attempt/f"{task['query_id']}.json"
        save(path,dict(at=now(),query_id=task['query_id'],pass_all=True,native_input=meta,text_only_input=tm,
            cached_native_parity=True,full_noop_logits_exact=True,original_cache_unchanged=True,
            first_future_query=p+n-1,all36_layers=True,mask_records=mask.records,
            fresh_text_deterministic=True,no_original_state_in_text_replay=True,elapsed_seconds=time.perf_counter()-begin))
        paths.append(path);print('PASS',task['query_id'],round(time.perf_counter()-begin,2),flush=True)
        del native,prefix,original,unchanged,reference,masked,a,b,ao,bo,refout,unout,prepared,text
        gc.collect();torch.cuda.empty_cache()
    save(ROOT/'audit/technical_validation.json',dict(at=now(),pass_all=True,examples=len(paths),
        checks_sha256={str(p):sha(p) for p in paths},config_sha256=sha(ROOT/'config.json'),
        source_sha256={p:sha(p) for p in ['scripts/stage10a/runtime.py','scripts/stage10a/protocol.py','scripts/stage10a/validate.py',
                                      'code/visual_reasoning/stage9a3/access.py']},slurm_job_id=os.environ['SLURM_JOB_ID']))


if __name__=='__main__':
    try:main()
    except Exception as e:
        save(ROOT/f'audit/validation_failure_{os.environ.get("SLURM_JOB_ID","local")}.json',dict(at=now(),error=repr(e),traceback=traceback.format_exc()));raise
