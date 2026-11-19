"""Freeze and summarize only the approved representative null-sink conditions."""
import argparse,os
from pathlib import Path
import numpy as np
from scripts.stage9a3.prepare import ROOT,load,save,sha,now
from scripts.stage9a3.grid import baseline_alias,policy_id
from visual_reasoning.stage9a3.analysis import image_surface,bootstrap


def freeze(key):
    positive=load(ROOT/'stage9a3_qwen25_positive_control.json')
    assert positive['baseline_valid'] and positive['technical_pass']
    b=load(ROOT/f'stage9a3_{key}_full_access.json');assert b['gates']['pass']
    definitions=[('FULL',1,None),('restricted',0,0)]
    if positive['selected_policy'] and positive['selected_policy']!=positive['zero_policy']:
        definitions.append(('selected_finite',positive['selected_fraction'],positive['selected_token_cutoff']))
    rows=[];logical=[]
    for q in b['rows']:
        for role,f,t in definitions:
            p=policy_id(f,t);reuse=baseline_alias(f,t,q['tokens'],q['normal_eos'])
            dest=ROOT/key/('full_primary/results' if reuse else 'sink_primary/results')/q['query_id']/('full' if reuse else p)
            rows.append(dict(query_id=q['query_id'],image_id=q['image_id'],policy_id=p,fraction=f,token_cutoff=t,mode='null_sink',
                execution='reuse_full' if reuse else 'run',result_path=str(dest/'result.json'),generation_path=str(dest/'generation.json'),
                reuse_result_sha256=sha(dest/'result.json') if reuse else None,
                proof='No generated query is blocked: null-sink wrapper returns original eager attention unchanged.' if reuse else None))
            logical.append(dict(query_id=q['query_id'],image_id=q['image_id'],fraction=f,token_cutoff=t,policy_id=p,role=role))
    paths=['scripts/stage9a3/bounded_controls.py','scripts/stage9a3/worker.py','scripts/stage9a3/runtime.py','code/visual_reasoning/stage9a3/access.py']
    nrun=sum(r['execution']=='run' for r in rows);assert nrun<=128
    save(ROOT/f'audit/{key}_sink_primary_manifest.json',dict(at=now(),frozen=True,model=key,rows=rows,logical_rows=logical,
        config_sha256=sha(ROOT/'config.json'),source_sha256={p:sha(p) for p in paths},
        calibration_sha256=sha(ROOT/'stage9a3_qwen25_positive_control.json'),baseline_sha256=sha(ROOT/f'stage9a3_{key}_full_access.json'),
        conditions=definitions,new_continuations=nrun,restricted_status='confirmed damaging' if positive['clear_restriction_damage'] else 'unconfirmed diagnostic; no clear standard-mask damage',
        finite_status='point-preserving calibration candidate' if len(definitions)==3 else 'no distinct finite calibration candidate',
        no_sink_outcomes_used=True))
    print(dict(model=key,new_continuations=nrun,definitions=definitions),flush=True)


def analyze(key):
    assert os.environ.get('SLURM_JOB_ID')
    standard=load(ROOT/f'audit/{key}_grid_primary_canonical_scored.json')['rows']
    sink=load(ROOT/f'audit/{key}_sink_primary_canonical_scored.json')['rows']
    policies={r['policy'] for r in sink};standard=[r for r in standard if r['policy'] in policies]
    images,ps,a=image_surface(standard);images2,ps2,b=image_surface(sink);assert images==images2 and ps==ps2
    fi=ps.index('l100_tFULL');assert np.array_equal(a[:,fi],b[:,fi])
    av,bv=bootstrap(a),bootstrap(b);da=av[:,fi,None]-av;db=bv[:,fi,None]-bv
    ma=a.mean(axis=0);mb=b.mean(axis=0)
    rows={}
    for i,p in enumerate(ps):
        rows[p]=dict(standard_accuracy=float(ma[i]),sink_accuracy=float(mb[i]),standard_damage=float(ma[fi]-ma[i]),
            sink_damage=float(mb[fi]-mb[i]),standard_ci95=np.quantile(da[:,i],[.025,.975]).tolist(),
            sink_ci95=np.quantile(db[:,i],[.025,.975]).tolist(),damage_difference=float((mb[fi]-mb[i])-(ma[fi]-ma[i])),
            damage_difference_ci95=np.quantile(db[:,i]-da[:,i],[.025,.975]).tolist(),
            sink_preservation_probability=float(np.mean(db[:,i]<=.05+1e-12)))
    save(ROOT/f'audit/{key}_bounded_sink_result.json',dict(at=now(),model=key,n_images=len(images),conditions=rows,
         bootstrap_draws=4000,seed=920260927,paired_images=True,full_identity_reused=True,
         interpretation='A bounded sensitivity to attention redistribution, not a separate complete grid or source-erasure intervention.',
         canonical_scored_sha256=sha(ROOT/f'audit/{key}_sink_primary_canonical_scored.json')))
    print(rows,flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['freeze','analyze']);ap.add_argument('--model',choices=['qwen25','qwen3'],required=True)
    a=ap.parse_args();globals()[a.action](a.model)
