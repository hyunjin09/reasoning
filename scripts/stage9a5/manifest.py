"""Materialize only gated primary Thinking conditions with exact FULL reuse."""
import argparse
from scripts.stage9a5.common import ROOT,load,save,sha,now,tasks,verify_config


def freeze(stage):
    verify_config();assert load(ROOT/'stage9a5_thinking_full_baseline.json')['gates']['pass']
    validation=load(ROOT/'stage9a5_thinking_mask_validation.json');assert validation['pass_all']
    mode='standard'
    if stage=='t1':cutoffs=[0,64,128]
    elif stage=='t256':
        d=load(ROOT/'audit/t1_decision.json');assert d['action']=='run' and d['cutoff']==256;cutoffs=[256]
    elif stage=='sink':
        d=load(ROOT/'audit/absolute_final_decision.json');assert d['action'] in ('selected','stop_no_finite')
        cutoffs=[None,0,d['cutoff']];mode='null_sink'
    else:raise ValueError(stage)
    rows=[]
    for q in tasks('primary'):
        for t in cutoffs:
            policy='full' if t is None else f't{t}';dest=ROOT/stage/'results'/(q['query_id']+'_'+policy)
            r=dict(query_id=q['query_id'],image_id=q['image_id'],policy=policy,cutoff=t,mode=mode,split='primary',execution='run',
                generation_path=str(dest/'generation.json'),result_path=str(dest/'result.json'))
            base=ROOT/'full/results'/(q['query_id']+'_full');g=load(base/'generation.json')
            if t is None or (g['normal_eos'] and g['tokens']-1<=t):
                r.update(execution='reuse_full',generation_path=str(base/'generation.json'),result_path=str(base/'result.json'),
                    reuse_generation_sha256=sha(base/'generation.json'),reuse_result_sha256=sha(base/'result.json'))
            rows.append(r)
    sources=['scripts/stage9a5/common.py','scripts/stage9a5/runtime.py','scripts/stage9a5/worker.py','scripts/stage9a5/native.py',
        'scripts/stage9a5/decisions.py','code/visual_reasoning/stage9a3/access.py']
    save(ROOT/f'audit/{stage}_manifest.json',dict(at=now(),frozen=True,stage=stage,rows=rows,config_sha256=sha(ROOT/'config.json'),
        source_sha256={p:sha(p) for p in sources},logical_rows=len(rows),new_generations=sum(r['execution']=='run' for r in rows)))
    print(stage,len(rows),'new',sum(r['execution']=='run' for r in rows))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage');freeze(p.parse_args().stage)
