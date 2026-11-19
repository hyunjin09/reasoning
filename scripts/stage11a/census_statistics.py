"""Small paired-family descriptive statistical family."""
import math
import numpy as np
from scripts.stage11a.common import SEED

def mean_interval(values):
    a=np.asarray(values,dtype=float);n=len(a)
    if not n:return dict(n=0,point=None,ci95=None)
    draw=np.random.default_rng(SEED).integers(0,n,size=(4000,n))
    return dict(n=n,point=float(a.mean()),ci95=np.quantile(a[draw].mean(1),[.025,.975]).tolist())

def rate(values):
    assert all(x in (0,1,False,True) for x in values)
    return dict(mean_interval(values),numerator=int(sum(values)))

def paired_summary(left,right):
    assert len(left)==len(right)
    l=sum(x==1 and y==0 for x,y in zip(left,right));r=sum(x==0 and y==1 for x,y in zip(left,right));n=l+r
    p=min(1.,2*sum(math.comb(n,i) for i in range(min(l,r)+1))/2**n) if n else 1.
    return dict(mean_interval(np.asarray(left,dtype=float)-np.asarray(right,dtype=float)),left_only=l,right_only=r,
        both=sum(x==y==1 for x,y in zip(left,right)),neither=sum(x==y==0 for x,y in zip(left,right)),mcnemar_exact_two_sided_p=p)

def coarse_state(state):
    assert state in ['N0','N1','N2','N3','N4','N5']
    return 'CORRECT_SUFFICIENT' if state=='N2' else 'NOT_EXTERNALIZED' if state=='N5' else 'OBSERVABLE_INSUFFICIENT'
