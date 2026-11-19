"""Descriptive frozen-reference shift and genuinely paired primary-image contrast."""
import os
import numpy as np
import pandas as pd
from scripts.stage9a4.common import ROOT,OLD,load,save,sha,now
from visual_reasoning.stage9a3.analysis import bootstrap


def main():
    assert os.environ.get('SLURM_JOB_ID')
    q3=load(ROOT/'audit/r1_decision.json');q25=load(OLD/'stage9a3_qwen25_positive_control.json')
    ref=q25['surface']['l100_t64'];assert abs(ref['damage']+1/96)<1e-12
    q25rows=pd.read_parquet(OLD/'stage9a3_qwen25_coarse_grid.parquet')
    q25rows=q25rows[['query_id','image_id','policy','correct']].drop_duplicates()
    a=q25rows[q25rows.policy.isin(['l100_tFULL','l100_t64'])].pivot(index='query_id',columns='policy',values='correct')
    base=load(ROOT/'stage9a4_qwen3_4b_full_baseline.json')['rows'];masked=load(ROOT/'audit/r1_scored.json')['rows']
    b=pd.DataFrame(base+[r for r in masked if r['policy']=='t64']).pivot(index='query_id',columns='policy',values='correct')
    assert set(a.index)==set(b.index)
    qmap={r['query_id']:r['image_id'] for r in base};images=sorted(set(qmap.values()));values=[]
    for image in images:
        ids=sorted(q for q,i in qmap.items() if i==image);assert len(ids)==2
        q25damage=np.mean([float(a.loc[q,'l100_tFULL'])-float(a.loc[q,'l100_t64']) for q in ids])
        q3damage=np.mean([float(b.loc[q,'full'])-float(b.loc[q,'t64']) for q in ids])
        values.append([q25damage,q3damage,q3damage-q25damage])
    values=np.array(values);draws=bootstrap(values)
    out=dict(at=now(),qwen25_frozen48_damage64=ref['damage'],qwen3_primary32_damage64=q3['surface']['t64']['damage'],
        headline_gamma64=q3['surface']['t64']['damage']-ref['damage'],
        headline_scope='Descriptive unequal cohorts: Qwen2.5 frozen48 vs Qwen3 primary32; no paired CI claimed.',
        paired_primary32=dict(n_images=32,qwen25_damage64=float(values[:,0].mean()),qwen3_damage64=float(values[:,1].mean()),
            gamma64=float(values[:,2].mean()),ci95=np.quantile(draws[:,2],[.025,.975]).tolist(),image_values=values.tolist(),images=images),
        attribution='Checkpoint/generation comparison with different capacity and caps; no architectural causal attribution.',
        qwen25_source_sha256=sha(OLD/'stage9a3_qwen25_coarse_grid.parquet'),qwen3_source_sha256=sha(ROOT/'audit/r1_scored.json'))
    save(ROOT/'stage9a4_qwen25_qwen3_comparison.json',out);print(out,flush=True)


if __name__=='__main__':main()
