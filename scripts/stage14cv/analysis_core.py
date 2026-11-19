"""Frozen-family paired estimation; no p-values or data-dependent selection."""
import hashlib
from collections import Counter
import numpy as np

SEED=20261009
DRAWS=10000
STATUSES=('CORRECT','WRONG','UNSCORABLE','TECHNICAL_MISSING')
VALUES=dict(CORRECT=1,WRONG=0,UNSCORABLE=None,TECHNICAL_MISSING=None)


def paired_binary(rows,left,right,stream):
    ordered=sorted(rows,key=lambda r:r['family_id'])
    if len({r['family_id'] for r in ordered})!=len(ordered):raise ValueError('Repeated independence unit')
    if not ordered:raise ValueError('Empty planned cohort')
    for r in ordered:
        if r[left] not in (None,0,1) or r[right] not in (None,0,1):raise ValueError('Invalid binary outcome')
    deltas=[];lower=[];upper=[];directions=Counter()
    for r in ordered:
        a,b=r[left],r[right]
        lower.append((0 if b is None else b)-(1 if a is None else a))
        upper.append((1 if b is None else b)-(0 if a is None else a))
        if a is not None and b is not None:
            delta=b-a;deltas.append(delta);directions[str(delta)]+=1
    if deltas:
        arr=np.asarray(deltas,float)
        seed=int(hashlib.sha256(f'{SEED}|{stream}'.encode()).hexdigest()[:16],16)
        rng=np.random.default_rng(seed);boot=[]
        for start in range(0,DRAWS,128):
            indices=rng.integers(len(arr),size=(min(128,DRAWS-start),len(arr)))
            boot.extend(np.mean(arr[indices],axis=1)*100)
        ci=np.quantile(boot,[.025,.975]).tolist();effect=float(np.mean(arr)*100)
    else:ci=None;effect=None
    return dict(planned_families=len(ordered),paired_scored_families=len(deltas),effect_pp=effect,
        ci95_pp=ci,planned_family_bounds_pp=[float(np.mean(lower)*100),float(np.mean(upper)*100)],
        paired_directions=dict(directions),bootstrap_draws=DRAWS,base_seed=SEED,stream=stream,
        interval='Unadjusted95% paired-family bootstrap over common scored pairs',
        missingness='Unresolved/technical missing bounded, not assigned incorrect')


def transitions(rows,left,right):
    counts={a+'__'+b:0 for a in STATUSES for b in STATUSES}
    for r in rows:
        if r[left] not in STATUSES or r[right] not in STATUSES:raise ValueError('Unknown outcome state')
        counts[r[left]+'__'+r[right]]+=1
    return counts
