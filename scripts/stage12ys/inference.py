"""Paired family-level descriptive estimates and missingness-aware confirmation."""
import numpy as np
from scripts.stage12ys.protocol import ARMS,majority,support,conjunction,neg
from scripts.stage12xs.inference_v2 import bounded_endpoint

ANALYSIS_SEED=120220260929

def mean_ci(values):
    n=len(values)
    if not n:return dict(n=0,estimate=None,bootstrap95=None)
    x=np.asarray(values,dtype=float);rng=np.random.default_rng(ANALYSIS_SEED)
    draws=x[rng.integers(n,size=(4000,n))].mean(axis=1)
    return dict(n=n,estimate=float(x.mean()),bootstrap95=np.quantile(draws,[.025,.975]).tolist(),
        positive=int(sum(x>0)),zero=int(sum(x==0)),negative=int(sum(x<0)))

def descriptive(rows):
    result={}
    for name,i,t in [('G_img','I_img','T_img'),('G_E','I_E','T_E'),('G_access','E_I','E_T')]:
        selected=[r for r in rows if r[i] is not None and r[t] is not None]
        result[name]=dict(mean_ci([int(r[t])-int(r[i]) for r in selected]),
            I_correct=sum(r[i] for r in selected),T_correct=sum(r[t] for r in selected))
    common=[r for r in rows if all(r[a] is not None for a in ['I_img','T_img','I_E','T_E'])]
    result['A_evidence']=mean_ci([int(r['T_img'])-int(r['I_img'])-int(r['T_E'])+int(r['I_E']) for r in common])
    result['four_task_common_G_img']=mean_ci([int(r['T_img'])-int(r['I_img']) for r in common])
    result['four_task_common_G_E']=mean_ci([int(r['T_E'])-int(r['I_E']) for r in common])
    result.update(n_families=len(rows),bootstrap_draws=4000,analysis_seed=ANALYSIS_SEED,
        independent_unit='Conservative visual family; family-equal paired contrasts',
        interpretation='Single-run screening/descriptive estimates; attenuation is not formal causal mediation.')
    return result

def confirm_families(ids,rows):
    out=[]
    for i in ids:
        r=dict(item_id=i);counts={}
        for a in ARMS:
            values=[x['correct'] for x in sorted(rows,key=lambda x:x['replicate']) if x['item_id']==i and x['arm']==a]
            r[a]=majority(values,3) if values else None
            counts[a]=dict(success=values.count(True),failure=values.count(False),missing=values.count(None),n=len(values))
        r.update(support(r));r['counts']=counts;out.append(r)
    return out

def transfer(ids,rows):
    out=[]
    for i in ids:
        r=dict(item_id=i);panels={}
        for a in ['RT_T','RT_I','Q_I','SH_I']:
            values=[x['correct'] for x in sorted(rows,key=lambda x:x['replicate']) if x['item_id']==i and x['arm']==a]
            r[a]=majority(values,5);panels[a]=values
        r['state_support']=conjunction(r['RT_T'],r['RT_I'],neg(r['Q_I']),neg(r['SH_I']))
        r['controls_resolved']=r['Q_I'] is not None and r['SH_I'] is not None
        r['panels']=panels;out.append(r)
    return out
