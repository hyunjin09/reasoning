"""Three disjoint A0 checks plus immutable prior positive-prefix validation."""
import os,traceback
import torch
from scripts.stage10ar.common import ROOT,OLD,PRIOR,load,save,sha,now
from scripts.stage10ar.runtime import load_runtime,inputs,start,resume,text_inputs,environment
from visual_reasoning.stage9a3.access import AccessMask


@torch.inference_mode()
def main():
    prior=load(PRIOR/'audit/technical_validation.json');assert prior['pass_all'] and prior['examples']==8
    for p,d in prior['source_sha256'].items():assert sha(p)==d,p
    for p,d in prior['checks_sha256'].items():assert sha(p)==d,p
    cfg,processor,model=load_runtime();sid=os.environ['SLURM_JOB_ID'];rows=[]
    tasks=[r for r in load(OLD/'audit/inference_tasks.json')['rows'] if r['query_id'] in ('image048_color','image049_shape','image050_color')]
    for task in tasks:
        prepared,meta=inputs(processor,model,task);p=meta['prompt_length']
        first,fo=start(model,prepared,cfg['seed'],1,sample=False,logits=True)
        args=dict(backend='qwen3',visual=meta['visual'],prompt_length=p,layers=36,layer_cutoff=36,token_cutoff=0)
        with AccessMask(**args,audit=True) as full_mask:whole,wo=start(model,prepared,cfg['seed'],9,sample=False,logits=True)
        assert torch.equal(fo.logits[0],wo.logits[0]) and whole.sequences[0,p].item()==first.sequences[0,p].item()
        with AccessMask(**args,audit=True) as mask:branch,_=resume(model,first,8,sample=False)
        assert torch.equal(branch.sequences,whole.sequences)
        assert first.cache.get_seq_length()==p
        assert all(not r['blocked_absolute_queries'] for r in full_mask.records if r['query_start']==0)
        assert len({r['layer'] for r in mask.records})==36
        assert min(r['query_start'] for r in mask.records)==p
        assert all(r['masked_probability_max']==0 and r['blocked_absolute_queries'] for r in mask.records)
        text,tm=text_inputs(processor,model,task,[])
        assert tm['prefix_tokens']==0 and text['input_ids'].shape[1]==tm['prompt_length']
        assert not any(k in text for k in ('pixel_values','image_grid_thw','past_key_values'))
        a,ao=start(model,text,cfg['seed'],8,sample=False,logits=True);b,bo=start(model,text,cfg['seed'],8,sample=False,logits=True)
        assert a.cache is not first.cache and torch.equal(a.sequences,b.sequences)
        assert all(torch.equal(x,y) for x,y in zip(ao.logits,bo.logits))
        rows.append(dict(query_id=task['query_id'],unchanged_prefill_logits=True,A0_matches_existing_ZERO=True,
            first_masked_absolute_query=p,mask_records=mask.records,text_only_empty_prefix=tm,clean_text_cache=True,
            fresh_text_deterministic=True,original_cache_unchanged=True))
        print('PASS_A0',task['query_id'],flush=True)
    paths=['scripts/stage10ar/runtime.py','scripts/stage10ar/validate.py','scripts/stage10ar/protocol.py',
        'scripts/stage10a/runtime.py','code/visual_reasoning/stage9a3/access.py','code/visual_reasoning/stage9a_dynamics/generation.py']
    save(ROOT/'audit/technical_validation.json',dict(at=now(),pass_all=True,examples=3,rows=rows,
        prior_positive_prefix_validation_sha256=sha(PRIOR/'audit/technical_validation.json'),prior_examples_reused=8,
        config_sha256=sha(ROOT/'config.json'),source_sha256={p:sha(p) for p in paths},environment=environment(model),slurm_job_id=sid))


if __name__=='__main__':
    try:main()
    except Exception as e:
        save(ROOT/f'audit/validation_failure_{os.environ.get("SLURM_JOB_ID","local")}.json',dict(at=now(),error=repr(e),traceback=traceback.format_exc()));raise
