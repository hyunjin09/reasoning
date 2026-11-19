"""Paired primary-image comparison at the Qwen2.5-selected frozen cutoff."""
import os
import numpy as np
from scripts.stage9a3.prepare import ROOT,load,save,sha,now
from visual_reasoning.stage9a3.analysis import image_surface,bootstrap


def main():
    assert os.environ.get('SLURM_JOB_ID')
    selected=load(ROOT/'stage9a3_qwen25_positive_control.json');assert selected['pass']
    data={};curves={};draws={};means={}
    for key in ['qwen25','qwen3']:
        assert load(ROOT/f'stage9a3_{key}_full_access.json')['gates']['pass']
        data[key]=load(ROOT/f'audit/{key}_grid_primary_canonical_scored.json')['rows']
        curves[key]=image_surface(data[key])
    assert curves['qwen25'][0]==curves['qwen3'][0] and curves['qwen25'][1]==curves['qwen3'][1]
    images,policies,_=curves['qwen25'];assert len(images)==32
    fi=policies.index('l100_tFULL');ci=policies.index(selected['selected_policy'])
    for key in data:
        values=curves[key][2];b=bootstrap(values);draws[key]=b[:,fi,None]-b;means[key]=values[:,fi,None]-values
    gamma=means['qwen3']-means['qwen25'];gb=draws['qwen3']-draws['qwen25']
    same={key:dict(damage=float(means[key][:,ci].mean()),ci95=np.quantile(draws[key][:,ci],[.025,.975]).tolist(),
        family_positive=int(np.sum(means[key][:,ci]>0)),family_negative=int(np.sum(means[key][:,ci]<0)),
        family_tied=int(np.sum(means[key][:,ci]==0))) for key in data}
    gc=gamma[:,ci];gci=np.quantile(gb[:,ci],[.025,.975]).tolist()
    meta={r['policy']:(r['fraction'],r['token_cutoff']) for r in data['qwen25']}
    finite={}
    for key in data:
        median=load(ROOT/f'stage9a3_{key}_full_access.json')['length_summary']['median']
        candidates=[p for i,p in enumerate(policies) if i!=fi and (meta[p][0]<=.75 or (meta[p][1] is not None and meta[p][1]<median))
                    and means[key][:,i].mean()<=.05+1e-12]
        finite[key]=dict(point_preserving_conditions=candidates,has_finite_condition=bool(candidates),
            preservation_probability={p:float(np.mean(draws[key][:,policies.index(p)]<=.05+1e-12)) for p in candidates})
    surface={p:dict(qwen25_damage=float(means['qwen25'][:,i].mean()),qwen3_damage=float(means['qwen3'][:,i].mean()),
        gamma=float(gamma[:,i].mean()),gamma_ci95=np.quantile(gb[:,i],[.025,.975]).tolist()) for i,p in enumerate(policies)}
    result=dict(at=now(),n_paired_images=32,n_queries_per_model=64,independent_unit='image',bootstrap_draws=4000,seed=920260927,
        selected_policy=selected['selected_policy'],selected_fraction=selected['selected_fraction'],selected_token_cutoff=selected['selected_token_cutoff'],
        selection_cohort_images=selected['n_images'],selection_sha256=sha(ROOT/'stage9a3_qwen25_positive_control.json'),
        comparison_uses_original32_only=True,same_cutoff=same,gamma=float(gc.mean()),gamma_ci95=gci,
        family_direction=dict(qwen3_more_damage=int(np.sum(gc>0)),qwen25_more_damage=int(np.sum(gc<0)),tied=int(np.sum(gc==0))),
        finite_access=finite,surface=surface,surface_is_descriptive=True,
        same_cutoff_qwen3_preserved=bool(means['qwen3'][:,ci].mean()<=.05+1e-12),
        positive_shift_interval_excludes_zero=bool(gci[0]>0),negative_shift_interval_excludes_zero=bool(gci[1]<0),
        caveat='Small-scale3B-versus2B checkpoint-family comparison; no attribution to an architectural component, training-data change, or Thinking specialization.')
    save(ROOT/'stage9a3_generation_comparison.json',result)
    print(dict(selected_policy=result['selected_policy'],gamma=result['gamma'],ci=result['gamma_ci95'],same_cutoff_qwen3_preserved=result['same_cutoff_qwen3_preserved']),flush=True)


if __name__=='__main__':main()
