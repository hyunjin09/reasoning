"""Prospective source-only selection and integer family-level inference."""
import hashlib
from collections import defaultdict
import numpy as np

SEED=120220260929
DRAWS=10000


def digest(value):return hashlib.sha256(value.encode()).hexdigest()


def select(rows):
    assert len(rows)==len({r['family_id'] for r in rows})==96
    strata=defaultdict(list)
    for r in rows:
        key=(r['answer_type'], str(r.get('level','unavailable')), '1' if len(r['facts'])==1 else '2+')
        assert len(r['facts'])>=1
        strata[key].append(r['family_id'])
    ordered={k:sorted(v,key=lambda f:digest('stage13b-v1|'+f)) for k,v in strata.items()}
    quotas={k:len(v)//2 for k,v in ordered.items()}
    remaining=48-sum(quotas.values())
    # Hamilton largest remainders; lexicographic source-stratum tie break.
    for k in sorted(ordered,key=lambda k:(-(len(ordered[k])%2),k))[:remaining]:quotas[k]+=1
    scientific=sorted([f for k,v in ordered.items() for f in v[:quotas[k]]],key=lambda f:digest('stage13b-v1|'+f))
    reserve=sorted(set(r['family_id'] for r in rows)-set(scientific),key=lambda f:digest('stage13b-v1|technical4|'+f))
    initial=sorted(scientific,key=lambda f:digest('stage13b-v1|initial8|'+f))[:8]
    return dict(scientific=scientific,technical=reserve[:4],initial8=initial,
                strata=[dict(stratum=list(k),available=len(ordered[k]),selected=quotas[k],ordering=ordered[k]) for k in sorted(ordered)],
                remaining_order=reserve)


def bootstrap_units(units):
    """Each integer unit is one correct replicate / three, including interactions."""
    values=np.asarray(units,dtype=np.int64);n=len(values)
    if not n:return dict(n=0,effect_pp=None,ci95_pp=[None,None])
    rng=np.random.default_rng(SEED)
    means=values[rng.integers(0,n,(DRAWS,n))].sum(axis=1)*100/(3*n)
    return dict(n=n,effect_pp=float(values.sum()*100/(3*n)),ci95_pp=np.quantile(means,[.025,.975]).tolist(),
                positive=int((values>0).sum()),zero=int((values==0).sum()),negative=int((values<0).sum()),
                bootstrap_draws=DRAWS,seed=SEED)


def missing_gate(missing,n):
    assert n==24 and 0<=missing<=n
    return missing/n<=.2


def primary_gate(estimate):
    return estimate['n']>=40 and estimate['effect_pp']>=5 and estimate['ci95_pp'][0]>0
