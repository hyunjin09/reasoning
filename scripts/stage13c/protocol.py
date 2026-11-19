"""Source-only selection, exact controls and predeclared family-level gates."""
import hashlib
from collections import defaultdict
import numpy as np

SEED=120220260929
DRAWS=10000


def digest(s):return hashlib.sha256(s.encode()).hexdigest()


def select(rows):
    assert len(rows)==len({r['family_id'] for r in rows})==96
    strata=defaultdict(list)
    for r in rows:
        key=(r['answer_type'],str(r.get('level','unavailable')),'1' if len(r['facts'])==1 else '2+')
        assert len(r['facts'])>0
        strata[key].append(r['family_id'])
    ordered={k:sorted(v,key=lambda f:digest('stage13c-v1|'+f)) for k,v in strata.items()}
    quotas={k:len(v)//4 for k,v in ordered.items()}
    for k in sorted(ordered,key=lambda k:(-(len(ordered[k])%4),k))[:24-sum(quotas.values())]:quotas[k]+=1
    chosen=sorted([f for k,v in ordered.items() for f in v[:quotas[k]]],key=lambda f:digest('stage13c-v1|'+f))
    remaining=sorted({r['family_id'] for r in rows}-set(chosen),key=lambda f:digest('stage13c-v1|technical4|'+f))
    return dict(scientific=chosen,technical=remaining[:4],
        initial8=sorted(chosen,key=lambda f:digest('stage13c-v1|initial8|'+f))[:8],
        strata=[dict(stratum=list(k),available=len(ordered[k]),selected=quotas[k],ordering=ordered[k]) for k in sorted(ordered)],
        rule='Hamilton proportional quotas, source-stratum lexical ties, within-stratum prescribed SHA256 order; separate technical4 and initial8 hash namespaces.')


def dummy_ids(phrase,n):
    assert phrase and isinstance(n,int) and n>=0
    return (phrase*((n+len(phrase)-1)//len(phrase)))[:n]


def donor(target,lengths):
    assert target in lengths and len(lengths)>1
    return min((d for d in lengths if d!=target),key=lambda d:(abs(lengths[d]-lengths[target]),digest(f'stage13c-v1|{target}|{d}')))


def bootstrap_units(units):
    a=np.asarray(units,dtype=np.int64);n=len(a)
    if not n:return dict(n=0,effect_pp=None,ci95_pp=[None,None],positive=0,zero=0,negative=0)
    rng=np.random.default_rng(SEED)
    means=a[rng.integers(0,n,(DRAWS,n))].sum(axis=1)*100/(5*n)
    return dict(n=n,effect_pp=float(a.sum()*100/(5*n)),ci95_pp=np.quantile(means,[.025,.975]).tolist(),
        positive=int((a>0).sum()),zero=int((a==0).sum()),negative=int((a<0).sum()),seed=SEED,draws=DRAWS)


def signals(buffer,residual,semantic,portable_dummy,portable_shuffle,portable_base):
    def passes(e,n):return e['n']>=n and e['effect_pp']>=5 and e['ci95_pp'][0]>0
    b=passes(buffer,20);r=b and passes(residual,1);s=passes(semantic,12)
    p=(passes(portable_dummy,12) and portable_shuffle['n']>=12 and portable_base['n']>=12
       and portable_shuffle['effect_pp']>0 and portable_base['effect_pp']>0)
    if b and (s or p):decision='COMPLEMENTARY_COMPUTE_AND_SEMANTICS'
    elif s or p:decision='DERIVED_STATE_PRIMING_ONLY'
    elif r:decision='COMPUTE_PARTIAL_SEMANTICS_UNRESOLVED'
    elif b:decision='COMPUTATIONAL_BUFFER_ONLY'
    else:decision='POST_EVIDENCE_MECHANISM_UNRESOLVED'
    return dict(COMPUTATIONAL_BUFFER_SIGNAL=b,COMPUTE_ALONE_INSUFFICIENT=r,DERIVED_SEMANTIC_SIGNAL=s,
        PORTABLE_DERIVED_PRIMING_SIGNAL=p,decision=decision)
