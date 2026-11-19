"""Frozen family-equal Stage13A estimands; missing slots are never errors."""
import numpy as np
from scipy.stats import binomtest

ANALYSIS_SEED=120220260929
BOOTSTRAPS=10000

def estimate(values):
    if not values:return dict(n=0,effect_pp=None,median_pp=None,ci95_pp=None,positive=0,zero=0,negative=0)
    raw=np.asarray(values,dtype=float)*3
    units=np.rint(raw).astype(np.int64)
    assert np.allclose(raw,units,rtol=0,atol=1e-12), 'Expected signed thirds from three-replicate families'
    rng=np.random.default_rng(ANALYSIS_SEED)
    sums=units[rng.integers(len(units),size=(BOOTSTRAPS,len(units)))].sum(axis=1)
    return dict(n=len(units),effect_pp=float(units.sum()*100/(3*len(units))),median_pp=float(np.median(units)*100/3),
        ci95_pp=(np.quantile(sums,[.025,.975])*100/(3*len(units))).tolist(),
        positive=int(sum(units>0)),zero=int(sum(units==0)),negative=int(sum(units<0)),
        bootstrap_draws=BOOTSTRAPS,analysis_seed=ANALYSIS_SEED)

def bounds(families):
    lo=[];hi=[]
    for r in families:
        i,t=r['I'],r['T'];assert len(i)==len(t)==3
        lo.append((t.count(True)-i.count(True)-i.count(None))/3)
        hi.append((t.count(True)+t.count(None)-i.count(True))/3)
    low,high=estimate(lo),estimate(hi)
    return dict(n=len(families),lower_pp=low['effect_pp'],upper_pp=high['effect_pp'],
        least_favorable_bootstrap=low,most_favorable_bootstrap=high,
        preserves_positive_gate=bool(lo and low['effect_pp']>=5-1e-12 and low['ci95_pp'][0]>0))

def decision(n,effect,ci,scoreability_gap_pp,bounds_preserve):
    if n<80 or (abs(scoreability_gap_pp)>10+1e-12 and not bounds_preserve):return 'EQUAL_EVIDENCE_TECHNICALLY_UNRESOLVED'
    if effect<=0:return 'EQUAL_EVIDENCE_NO_ADVANTAGE'
    if effect>=5-1e-12 and ci[0]>0:return 'EQUAL_EVIDENCE_THINKING_ADVANTAGE_CONFIRMED'
    return 'EQUAL_EVIDENCE_SIGNAL_PARTIAL'

def majority(values):
    assert len(values)==3
    return True if values.count(True)>=2 else False if values.count(False)>=2 else None

def optional_needed(confirmed,comparable):
    return bool(confirmed and (comparable['n']<80 or comparable['effect_pp']<5-1e-12 or comparable['ci95_pp'][0]<=0))

def transitions(families):
    counts={k:0 for k in ['BOTH_CORRECT','THINKING_ONLY','INSTRUCT_ONLY','BOTH_WRONG','UNRESOLVED']}
    for r in families:
        i,t=majority(r['I']),majority(r['T'])
        k='UNRESOLVED' if i is None or t is None else 'BOTH_CORRECT' if i and t else 'THINKING_ONLY' if t else 'INSTRUCT_ONLY' if i else 'BOTH_WRONG'
        counts[k]+=1
    a,b=counts['THINKING_ONLY'],counts['INSTRUCT_ONLY']
    return dict(counts=counts,net_thinking_only=a-b,discordant_families=a+b,
        exact_two_sided_p=float(binomtest(a,a+b,.5).pvalue) if a+b else 1.0,descriptive_only=True)
