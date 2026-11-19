"""Twelve bounded actual-model V1–V6 checks; no scientific answer scoring."""
import gc
import hashlib
import json
import os
import socket
import time
import traceback
from pathlib import Path

import torch
from scripts.stage8c.prepare import save, sha
from scripts.stage9a.run_native import inputs, now
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3c9.streaming import prefill_streaming_state, advance_streaming_state
from visual_reasoning.stage9a_dynamics.access import TemporalAccessMask
from visual_reasoning.stage9a_dynamics.generation import start, resume

ROOT=Path('outputs/stage9a_dynamics/v1')
OLD=Path('outputs/stage9a/v1')


def check(model, processor, row):
    prepared,meta=inputs(processor,row);p=meta['prompt_token_count'];visual=meta['visual_token_indices']
    archived=json.loads((OLD/'native/examples'/row['task_id']/'generation.json').read_text())['generated_token_ids']
    count=min(128,len(archived));assert count>=16
    began=time.perf_counter()
    native,_=start(model,prepared,row['seed'],count)
    assert native.sequences[0,p:].tolist()==archived[:count], 'archived sampled prefix mismatch'
    expected=native.sequences.clone();del native
    with TemporalAccessMask(visual=visual,prompt_length=p,intervals=[]):
        noop,_=start(model,prepared,row['seed'],count)
    assert torch.equal(noop.sequences,expected),'full-access sampled no-op mismatch'
    del noop
    plain,plain_out=start(model,prepared,row['seed'],24,sample=False,logits=True)
    with TemporalAccessMask(visual=visual,prompt_length=p,intervals=[]):
        same,same_out=start(model,prepared,row['seed'],24,sample=False,logits=True)
    assert torch.equal(plain.sequences,same.sequences)
    assert all(torch.equal(a,b) for a,b in zip(plain_out.logits,same_out.logits))
    del plain,plain_out,same,same_out
    base,_=start(model,prepared,row['seed'],7)
    branch,br=resume(model,base,count-7)
    assert torch.equal(branch.sequences,expected),'cache/RNG resume mismatch'
    del branch,br
    midpoint,_=resume(model,base,10,copy_cache=False)
    final,_=resume(model,midpoint,count-17,copy_cache=False)
    assert torch.equal(final.sequences,expected),'repeated cache/RNG resume mismatch'
    del base,midpoint,final
    prefix,_=prefill_streaming_state(model=model,prepared=prepared,seed=row['seed'])
    prefill_logits=prefix.last_logits.clone();del prefix
    audits={}
    for label,intervals,mode in [('local',[(4,8)],'standard'),('cumulative',[(5,None)],'standard'),
                                 ('sink',[(4,8)],'null_sink')]:
        with TemporalAccessMask(visual=visual,prompt_length=p,intervals=intervals,mode=mode,audit=True) as mask:
            state,_=prefill_streaming_state(model=model,prepared=prepared,seed=row['seed'])
            assert torch.equal(state.last_logits,prefill_logits),'prefill changed'
            for token in archived[:12]:
                advance_streaming_state(model=model,state=state,token_ids=[token],seed=row['seed'],chunk_size=1)
            assert state.cache.get_seq_length()==p+12
        blocked=sorted({r['blocked_absolute_queries'][0]-p+1 for r in mask.records if r['blocked_absolute_queries']})
        assert blocked==(list(range(5,13)) if label=='cumulative' else list(range(4,8)))
        reopened=[r for r in mask.records if r['query_start']>=p+7 and not r['blocked_absolute_queries']]
        if label!='cumulative':assert reopened and all(r['unmasked_image_probability_max']>0 for r in reopened)
        if mode=='null_sink':assert all(r.get('nonvisual_probability_max_delta',0)==0 for r in mask.records)
        audits[label]=dict(blocked_times=blocked,records=mask.records)
        del state
    # Branching is also checked across a real mask, with the same pre-mask RNG.
    with TemporalAccessMask(visual=visual,prompt_length=p,intervals=[(7,12)]):
        whole,_=start(model,prepared,row['seed'],32)
    base,_=start(model,prepared,row['seed'],7)
    with TemporalAccessMask(visual=visual,prompt_length=p,intervals=[(7,12)]):
        branched,_=resume(model,base,25)
    assert torch.equal(whole.sequences,branched.sequences),'intervened cache branch mismatch'
    return dict(task_id=row['task_id'],arm=row['arm'],family_id=row['family_id'],pass_all=True,
        V1_full_logits_exact=True,V2_mask_probability_exact_zero=True,V3_local_boundaries=True,
        V4_cumulative_semantics=True,V5_prefill_logits_exact=True,V6_cache_transitions=True,
        native_sampled_prefix_tokens=count,cache_rng_resume_exact=True,masked_branch_exact=True,
        audits=audits,input_sha256=sha(OLD/'native/examples'/row['task_id']/'input.json'),
        elapsed_seconds=time.perf_counter()-began)


def main():
    assert os.environ.get('SLURM_JOB_ID') and torch.cuda.device_count()==1
    cfg=json.loads((OLD/'stage9a_generation_config_node07.json').read_text())
    tasks=json.loads((OLD/'audit/native_tasks.json').read_text())['rows']
    families=sorted({r['family_id'] for r in tasks},key=lambda f:hashlib.sha256(('dynamics_preflight:'+f).encode()).hexdigest())[:4]
    selected=[r for r in tasks if r['family_id'] in families]
    source={str(p):sha(p) for d in ['code/visual_reasoning/stage9a_dynamics','scripts/stage9a_dynamics'] for p in Path(d).glob('*.py')}
    save(ROOT/'audit/preflight/frozen_inputs.json',dict(at=now(),families=families,tasks=[r['task_id'] for r in selected],source_sha256=source))
    checks=[]
    for key in ['instruct','thinking']:
        processor,model=load_runtime(Path(cfg['models'][key]['checkpoint']),'cuda:0')
        save(ROOT/f'audit/preflight/{key}_environment.json',dict(runtime_environment(Path(cfg['models'][key]['checkpoint']),model,128),slurm_job_id=os.environ['SLURM_JOB_ID'],node=socket.gethostname(),at=now()))
        for row in selected:
            if ('thinking' if row['arm']=='thinking' else 'instruct')!=key:continue
            print(json.dumps(dict(event='check_start',task_id=row['task_id'],at=now())),flush=True)
            result=check(model,processor,row);dest=ROOT/'audit/preflight'/f"{row['task_id']}.json"
            save(dest,result);checks.append(str(dest))
            print(json.dumps(dict(event='check_pass',task_id=row['task_id'],seconds=result['elapsed_seconds'],at=now())),flush=True)
            gc.collect();torch.cuda.empty_cache()
        del model,processor;gc.collect();torch.cuda.empty_cache()
    save(ROOT/'stage9a_mask_backend_validation.json',dict(pass_all=True,at=now(),examples=len(checks),checks_sha256={p:sha(p) for p in checks},source_sha256=source,slurm_job_id=os.environ['SLURM_JOB_ID'],mask_backend='native eager',dtype='bfloat16'))


if __name__=='__main__':
    try:main()
    except Exception as exc:
        save(ROOT/'audit/preflight/failure.json',dict(at=now(),error=repr(exc),traceback=traceback.format_exc(),slurm_job_id=os.environ.get('SLURM_JOB_ID')))
        raise
