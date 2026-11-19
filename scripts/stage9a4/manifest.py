"""Freeze only the next authorized finite queue, with exact identity reuse."""
import argparse
from scripts.stage9a4.common import ROOT,load,save,sha,now,tasks,verify_config


def freeze(stage):
    cfg=verify_config();split='primary';mode='standard'
    if stage=='full':cutoffs=[None]
    else:
        assert load(ROOT/'stage9a4_qwen3_4b_full_baseline.json')['gates']['pass']
        assert load(ROOT/'stage9a4_qwen3_4b_mask_validation.json')['pass_all']
        if stage=='r1':cutoffs=[0,64]
        elif stage in ('t128','t256'):
            prior='r1' if stage=='t128' else 't128';decision=load(ROOT/f'audit/{prior}_decision.json')
            t=int(stage[1:]);assert decision['action']=='run' and decision['cutoff']==t;cutoffs=[t]
        else:
            d=load(ROOT/'audit/selected_cutoff.json');assert d['cutoff'] in (64,128,256)
            cutoffs=[None,0,d['cutoff']]
            if stage=='reserve':assert d['reserve_eligible'];split='reserve'
            elif stage=='sink':mode='null_sink'
            else:raise ValueError(stage)
    rows=[]
    for q in tasks(split):
        for t in cutoffs:
            policy='full' if t is None else f't{t}'
            path=ROOT/stage/'results'/(q['query_id']+'_'+policy)
            r=dict(query_id=q['query_id'],image_id=q['image_id'],policy=policy,cutoff=t,mode=mode,split=split,
                execution='run',generation_path=str(path/'generation.json'),result_path=str(path/'result.json'))
            if stage!='full' and split=='primary':
                base=ROOT/'full/results'/(q['query_id']+'_full');g=load(base/'generation.json')
                if t is None or (g['normal_eos'] and g['tokens']-1<=t):
                    r.update(execution='reuse_full',generation_path=str(base/'generation.json'),result_path=str(base/'result.json'),
                        reuse_generation_sha256=sha(base/'generation.json'),reuse_result_sha256=sha(base/'result.json'))
            rows.append(r)
    source=['scripts/stage9a4/worker.py','scripts/stage9a4/runtime.py','scripts/stage9a4/common.py',
            'code/visual_reasoning/stage9a3/access.py','scripts/stage9a4/decisions.py']
    save(ROOT/f'audit/{stage}_manifest.json',dict(at=now(),frozen=True,stage=stage,rows=rows,
        config_sha256=sha(ROOT/'config.json'),source_sha256={p:sha(p) for p in source},
        logical_rows=len(rows),new_generations=sum(r['execution']=='run' for r in rows)))
    print(stage,len(rows),'new',sum(r['execution']=='run' for r in rows),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage');freeze(p.parse_args().stage)
