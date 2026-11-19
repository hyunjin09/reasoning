"""Family-level frozen support rules; missing replicates never become errors."""
from scripts.stage12us.protocol import majority


def neg(value):return None if value is None else not value


def conjunction(*values):
    if any(v is False for v in values):return False
    return None if any(v is None for v in values) else True


def interpret(outcomes,source_evidence,source_derivation):
    m={k:majority(v) for k,v in outcomes.items()}
    no_error=source_evidence in ['E_FULL','E_PARTIAL']
    adequate=no_error and source_derivation=='DERIVATION_VALID'
    flawed=source_evidence=='E_WRONG_OR_CONFLICTING' or source_derivation=='DERIVATION_FLAWED'
    return dict(majority=m,
        PRODUCTION_SUPPORT=conjunction(m['RT_T'],m['RT_I'],neg(m['Q_I'])),
        UTILIZATION_SUPPORT=conjunction(adequate,neg(m['RC_I']),m['RC_T'],neg(m['Q_T'])),
        REPAIR_SUPPORT=conjunction(flawed,neg(m['RC_I']),m['RC_T'],neg(m['Q_T'])),
        TEXT_NOT_SUFFICIENT=neg(m['RT_T']),
        production_trace_dependence=conjunction(m['RT_I'],neg(m['Q_I'])),
        utilization_repair_trace_dependence=conjunction(m['RC_T'],neg(m['Q_T'])))


def decision(primary):
    assert len(primary)==5
    keys=['PRODUCTION_SUPPORT','UTILIZATION_SUPPORT','REPAIR_SUPPORT','TEXT_NOT_SUFFICIENT']
    counts={k:sum(r[k] is True for r in primary) for k in keys}
    tt=sum(r['majority']['RT_T'] is True for r in primary)
    tt_missing=sum(r['majority']['RT_T'] is None for r in primary)
    signals=dict(STATE_PRODUCTION_SIGNAL=tt>=4 and counts['PRODUCTION_SUPPORT']>=3,
                 STATE_UTILIZATION_SIGNAL=counts['UTILIZATION_SUPPORT']>=3,
                 STATE_REPAIR_SIGNAL=counts['REPAIR_SUPPORT']>=3,
                 TEXT_STATE_INSUFFICIENT=tt+tt_missing<3)
    strong=[s for s in signals if signals[s] and s!='TEXT_STATE_INSUFFICIENT']
    # Preserve every threshold flag. Conflicting non-mixed criteria are unresolved,
    # not silently resolved by an invented scientific hierarchy.
    if signals['STATE_PRODUCTION_SIGNAL'] and (signals['STATE_UTILIZATION_SIGNAL'] or signals['STATE_REPAIR_SIGNAL']):
        name='MIXED_STATE_SIGNAL'
    elif len(strong)==1 and not signals['TEXT_STATE_INSUFFICIENT']:name=strong[0]
    elif not strong and signals['TEXT_STATE_INSUFFICIENT']:name='TEXT_STATE_INSUFFICIENT'
    else:name='UNRESOLVED'
    return dict(decision=name,threshold_flags=signals,counts=counts,RT_T_majority_successes=tt,
                RT_T_missing=tt_missing,n_primary=5,
                note='Qualitative mixed/overlap or unlisted intermediate cases without a unique plan-supported state remain unresolved; no threshold tuning.')

