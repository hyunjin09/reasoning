import numpy as np
from scripts.stage13d.common import digest,ANALYSIS_SEED
def donor(target,rows):
    return min((r for r in rows if r['item_id']!=target['item_id']),key=lambda r:(abs(r['n']-target['n']),digest(f"stage13d-v1|{target['item_id']}|{r['item_id']}")))
def bootstrap(values,scale=1):
    a=np.asarray(values);n=len(a)
    if not n:return dict(n=0,mean=None,ci=None,positive=0,zero=0,negative=0)
    draws=np.random.default_rng(ANALYSIS_SEED).integers(0,n,(10000,n))
    b=a[draws].sum(axis=1)/(n*scale)
    return dict(n=n,mean=float(a.sum()/(n*scale)),ci=np.quantile(b,[.025,.975]).tolist(),
        positive=int((a>0).sum()),zero=int((a==0).sum()),negative=int((a<0).sum()))
def bootstrap_counts(values):return bootstrap(values,5)
def semantic_decision(n,dummy,base,shuffle):
    return bool(n>=12 and dummy['mean']>=.05 and dummy['ci'][0]>0 and base>0 and shuffle>0)
def buffer_decision(values):
    r=bootstrap(values)
    return bool(r['n']>=8 and r['mean']>0 and r['ci'][0]>0 and r['positive']/r['n']>=.6)
