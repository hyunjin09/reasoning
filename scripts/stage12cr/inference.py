"""CoT-only family-level endpoints with explicit technical missingness."""
from collections import Counter
import numpy as np
from scripts.stage12bs.inference import proportion

def endpoint(rows):
    values=[r['c'] for r in rows if r['c'] is not None];k=sum(values);n=len(values);total=len(rows)
    return dict(proportion(k,n),frozen_total=total,missing=total-n,
        observed_rescues_over_frozen_total=k/total if total else None,
        missingness_identification_bounds=[k/total,(k+total-n)/total] if total else None)

def transition(n,c):
    if n is None or c is None:return 'UNSCOREABLE_TECHNICAL'
    return ('BOTH_CORRECT' if c else 'REGRESSION') if n else ('RESCUE' if c else 'BOTH_WRONG')

def infer(rows,draws=4000,seed=120220260929):
    assert len({r['family_id'] for r in rows})==len(rows)
    strata={b:[r for r in rows if r['bottleneck']==b] for b in ['B1','B2','B3','B4']}
    primary={'A-P1':endpoint(strata['B1']),'A-P2':endpoint(strata['B4'])}
    def delta(ss):
        x,y=[endpoint(ss[b])['estimate'] for b in ['B1','B4']]
        return x-y if x is not None and y is not None else None
    rng=np.random.default_rng(seed);samples=[]
    for _ in range(draws):
        ss={b:[strata[b][i] for i in rng.integers(len(strata[b]),size=len(strata[b]))] for b in ['B1','B4']}
        d=delta(ss)
        if d is not None:samples.append(d)
    primary['A-P3']=dict(estimate=delta(strata),percentile95=np.percentile(samples,[2.5,97.5]).tolist() if samples else None,defined_draws=len(samples))
    pairs=[r for r in rows if r['n'] is not None and r['c'] is not None];counts=Counter(transition(r['n'],r['c']) for r in rows)
    return dict(primary=primary,by_stratum={b:endpoint(rr) for b,rr in strata.items()},bootstrap_draws=draws,bootstrap_seed=seed,
        bootstrap_unit='Independent family, equal weights, resample frozen B1/B4 separately retaining missingness.',
        overall_paired=dict(counts={k:counts[k] for k in ['RESCUE','REGRESSION','BOTH_CORRECT','BOTH_WRONG','UNSCOREABLE_TECHNICAL']},
            jointly_scoreable=len(pairs),native_accuracy=proportion(sum(r['n'] for r in pairs),len(pairs)),cot_accuracy=proportion(sum(r['c'] for r in pairs),len(pairs))),
        b1_subtypes={name:dict(endpoint(rr),transitions=dict(Counter(transition(r['n'],r['c']) for r in rr)))
            for name,rr in [(name,[r for r in strata['B1'] if bool(r['e_has_incorrect_atom'])==explicit]) for name,explicit in [('B1_EXPLICIT_WRONG',True),('B1_UNRESOLVED_ONLY',False)]]},
        decision='COT_RESCUE_INFORMATIVE' if any(primary[p]['numerator']>=5 for p in ['A-P1','A-P2']) else 'COT_RESCUE_SPARSE')
