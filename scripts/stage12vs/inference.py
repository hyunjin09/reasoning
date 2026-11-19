"""Frozen scientific gates; missing/unspecified patterns remain unresolved."""
from scripts.stage12us.inference import conjunction,neg


def causal_step(stable,drop,cf,para,ctrl,redirect=False):
    sensitive=True if cf is False or redirect is True else None if cf is None or redirect is None else False
    return conjunction(stable,neg(drop),sensitive,para,ctrl)


def decision(rows,full_failures):
    assert len(rows)==4
    stable=sum(r['stable'] is True for r in rows)
    causal=sum(r.get('causal') is True for r in rows)
    beyond=sum(r.get('causal') is True and r.get('oracle') is False for r in rows)
    nonmono=sum(r.get('nonmonotonic',False) for r in rows)
    if full_failures>1:name='PORTABILITY_UNSTABLE'
    elif stable>=3 and causal>=3 and beyond>=3:name='DERIVED_STATE_CAUSAL_SIGNAL'
    elif stable>=3 and causal<3:name='PORTABILITY_LOCALIZED_BUT_DISTRIBUTED'
    elif stable<3 and stable+nonmono>=3:name='PORTABILITY_NONMONOTONIC'
    else:name='UNRESOLVED'
    return dict(decision=name,n_primary=4,stable=stable,causal=causal,causal_with_oracle_failure=beyond,
                nonmonotonic=nonmono,full_prefix_failures=full_failures)
