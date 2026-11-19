"""Image-paired bootstrap and the frozen sequential decision after sealed review."""
import argparse,os
import numpy as np
import pandas as pd
from scripts.stage9a4.common import ROOT,load,save,sha,now
from scripts.stage9a4.review import scored_rows
from scripts.stage9a4.decisions import next_cutoff,reserve_eligible
from visual_reasoning.stage9a3.analysis import image_surface,bootstrap


def summarize(rows,raw=False):
    inputs=[dict(r,correct=r['raw_correct'] if raw else r['correct']) for r in rows]
    images,policies,values=image_surface(inputs);means=values.mean(0);b=bootstrap(values)
    fi=policies.index('full');damage=means[fi]-means;draws=b[:,fi,None]-b;ci=np.quantile(draws,[.025,.975],axis=0)
    result={p:dict(accuracy=float(means[i]),damage=float(damage[i]),ci95=ci[:,i].tolist(),
        preservation_probability=float(np.mean(draws[:,i]<=.05+1e-12)),
        paired_images_harmed=int(np.sum(values[:,fi]>values[:,i])),paired_images_improved=int(np.sum(values[:,fi]<values[:,i])),
        paired_images_tied=int(np.sum(values[:,fi]==values[:,i]))) for i,p in enumerate(policies)}
    return dict(n_images=len(images),images=images,independent_unit='image',bootstrap_draws=4000,seed=920260927,surface=result)


def score(stage):
    assert os.environ.get('SLURM_JOB_ID')
    rows=scored_rows(stage)
    save(ROOT/f'audit/{stage}_scored.json',dict(at=now(),rows=rows,review_sha256=sha(ROOT/f'audit/{stage}_review.json')))
    if stage in ('r1','t128','t256'):
        combined=load(ROOT/'stage9a4_qwen3_4b_full_baseline.json')['rows']
        for s in ['r1','t128','t256']:
            path=ROOT/f'audit/{s}_scored.json'
            if path.exists():combined=combined+load(path)['rows']
            if s==stage:break
        out='stage9a4_qwen3_4b_primary64.parquet' if stage=='r1' else f'stage9a4_qwen3_4b_token{stage[1:]}.parquet'
        pd.DataFrame(combined if stage=='r1' else rows).to_parquet(ROOT/out,index=False)
        result=summarize(combined);result['raw_sensitivity']=summarize(combined,True)
        surface=result['surface'];action,t=next_cutoff(surface['t0']['damage'],{int(k[1:]):v['damage'] for k,v in surface.items() if k.startswith('t') and k!='t0'})
        result.update(at=now(),action=action,cutoff=t,stage=stage,source_sha256=sha(__file__))
        save(ROOT/f'audit/{stage}_decision.json',result)
        if action=='selected':
            value=surface[f't{t}'];save(ROOT/'audit/selected_cutoff.json',dict(at=now(),cutoff=t,decision_sha256=sha(ROOT/f'audit/{stage}_decision.json'),
                damage=value['damage'],ci95=value['ci95'],reserve_eligible=reserve_eligible(t,value['damage'],value['ci95'])))
        print(result,flush=True)
    elif stage in ('reserve','sink'):
        result=summarize(rows);result['raw_sensitivity']=summarize(rows,True);result['at']=now()
        if stage=='reserve':
            d=load(ROOT/'audit/selected_cutoff.json');selected=d['cutoff']
            primary=load(ROOT/'stage9a4_qwen3_4b_full_baseline.json')['rows']
            for s in ['r1','t128','t256']:
                path=ROOT/f'audit/{s}_scored.json'
                if path.exists():primary+=load(path)['rows']
            primary=[r for r in primary if r['policy'] in ['full','t0',f't{selected}']]
            result.update(combined=summarize(primary+rows),combined_raw_sensitivity=summarize(primary+rows,True),selected_cutoff=selected)
            name='stage9a4_qwen3_4b_reserve_extension.json'
        else:name='stage9a4_qwen3_4b_null_sink_control.json'
        result['review_sha256']=sha(ROOT/f'audit/{stage}_review.json');save(ROOT/name,result);print(result,flush=True)
    else:raise ValueError(stage)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage');score(p.parse_args().stage)
