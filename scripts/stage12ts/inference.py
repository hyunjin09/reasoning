"""Family-level Thinking endpoints with technical missingness kept explicit."""
from collections import Counter
import numpy as np
from scripts.stage12bs.inference import proportion
from scripts.stage12ts.protocol import scientific_decision

def endpoint(rows,arm='t'):
    values=[r[arm] for r in rows if r[arm] is not None];k=sum(values);n=len(values);total=len(rows)
    return dict(proportion(k,n),frozen_total=total,missing=total-n,
        observed_rescues_over_frozen_total=k/total if total else None,
        missingness_identification_bounds=[k/total,(k+total-n)/total] if total else None)

def transition(a,b):
    if a is None or b is None:return 'UNSCOREABLE_TECHNICAL'
    return ('BOTH_CORRECT' if b else 'FIRST_ONLY') if a else ('THINKING_ONLY' if b else 'BOTH_WRONG')

def paired(rows,first='c'):
    counts=Counter(transition(r[first],r['t']) for r in rows)
    rr=[r for r in rows if r[first] is not None and r['t'] is not None]
    return dict(counts={k:counts[k] for k in ['BOTH_WRONG','FIRST_ONLY','THINKING_ONLY','BOTH_CORRECT','UNSCOREABLE_TECHNICAL']},
         jointly_scoreable=len(rr),frozen_total=len(rows),first_accuracy=proportion(sum(r[first] for r in rr),len(rr)),
         thinking_accuracy=proportion(sum(r['t'] for r in rr),len(rr)),first_arm=first)

def infer(rows,draws=4000,seed=120220260929,technical_pass=True):
    assert len({r['family_id'] for r in rows})==len(rows)
    strata={b:[r for r in rows if r['bottleneck']==b] for b in ['B1','B2','B3','B4']}
    primary={'T-P1':endpoint(strata['B1']),'T-P2':endpoint(strata['B4'])}
    def delta(ss):
        x,y=[endpoint(ss[b])['estimate'] for b in ['B1','B4']]
        return x-y if x is not None and y is not None else None
    rng=np.random.default_rng(seed);samples=[]
    for _ in range(draws):
        ss={b:[strata[b][i] for i in rng.integers(len(strata[b]),size=len(strata[b]))] if strata[b] else [] for b in ['B1','B4']}
        d=delta(ss)
        if d is not None:samples.append(d)
    primary['T-P3']=dict(estimate=delta(strata),percentile95=np.percentile(samples,[2.5,97.5]).tolist() if samples else None,defined_draws=len(samples))
    primary['T-P4']={b:paired(strata[b]) for b in ['B1','B4']}
    def evidence(rr):
        linked=[r for r in rr if r['t'] is True and r['T_trace']=='TRACE_E_FULL']
        only=[r for r in linked if r['c'] is False]
        return dict(evidence_linked_rescues=len(linked),thinking_only_evidence_recovery_rescues=len(only),
            qualifying_families=sorted(r['family_id'] for r in only),
            by_outcome={name:dict(n=len(ss),states=dict(Counter(r['T_trace'] for r in ss)),
                full=proportion(sum(r['T_trace']=='TRACE_E_FULL' for r in ss),len(ss)))
                for outcome,name in [(True,'rescued'),(False,'not_rescued'),(None,'unscoreable')]
                for ss in [[r for r in rr if r['t'] is outcome]]})
    ev=evidence(strata['B1']);b1=primary['T-P1']['numerator'];b4=primary['T-P2']['numerator']
    both=[r for r in rows if all(r[k] is not None for k in ['n','c','t'])]
    return dict(primary=primary,by_stratum={b:endpoint(rr) for b,rr in strata.items()},
        cot_by_stratum={b:endpoint(rr,'c') for b,rr in strata.items()},
        evidence_B1=ev,B1_evidence_transitions=dict(Counter(r['C_trace']+' → '+r['T_trace'] for r in strata['B1'])),
        B1_subtypes={name:dict(thinking=endpoint(ss),cot_thinking=paired(ss),evidence=evidence(ss))
            for explicit,name in [(True,'B1_EXPLICIT_WRONG'),(False,'B1_UNRESOLVED_ONLY')]
            for ss in [[r for r in strata['B1'] if bool(r['e_has_incorrect_atom'])==explicit]]},
        overall=dict(common_joint_n=len(both),common_joint_missing=len(rows)-len(both),
            accuracies={k:proportion(sum(r[k] for r in both),len(both)) for k in ['n','c','t']},
            native_thinking=paired(rows,'n'),cot_thinking=paired(rows,'c')),
        bootstrap_draws=draws,bootstrap_seed=seed,bootstrap_unit='Independent family, equal weight, stratified B1/B4 retaining paired outcomes and missingness.',
        states=scientific_decision(b1,b4,primary['T-P4']['B1']['counts']['THINKING_ONLY'],ev['thinking_only_evidence_recovery_rescues'],technical_pass))
