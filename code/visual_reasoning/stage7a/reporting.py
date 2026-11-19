"""Descriptive summaries that keep missing causal identity and truth separate."""
from collections import defaultdict
import numpy as np


def certified(state):
    return state['tier'] == 1 or (state['tier'] == 2 and state.get('strong_tier2', False))


def family_rate(rows, values, seed=1234):
    """Nested events -> base means -> image-family means, never row-iid CIs."""
    bases, groups = defaultdict(list), {}
    for row, value in zip(rows, values, strict=True):
        if value is None:
            continue
        bases[row['base_id']].append(float(value))
        if row['base_id'] in groups:
            assert groups[row['base_id']] == row['group_id']
        groups[row['base_id']] = row['group_id']
    families = defaultdict(list)
    for base, vals in bases.items():
        families[groups[base]].append(float(np.mean(vals)))
    x = np.array([np.mean(vals) for vals in families.values()])
    interval = None
    if len(x) >= 2:
        rng = np.random.default_rng(seed)
        sampled = np.mean(rng.choice(x, size=(2000, len(x)), replace=True), axis=1)
        interval = np.quantile(sampled, [.025, .975]).tolist()
    return dict(mean=None if not len(x) else float(x.mean()), ci95=interval,
                events=sum(len(v) for v in bases.values()), bases=len(bases),
                independent_families=len(families), family_values=dict(zip(families, x.tolist())))


def semantic_follows(metric, thresholds):
    s = metric['semantic_effects'].get('T')
    if s is None:
        return None
    floor = thresholds['semantic_floor']
    return (s['net_semantic_beyond_sham'] > floor and s['semantic_shift'] > floor and
            abs(s['sham_shift']) <= thresholds['sham_fraction_max'] * s['semantic_shift'])


def faithfulness_summary(entries, states, metrics, thresholds):
    rows = [e for e in entries if e['readout_type'] == 'V' and e['reviewed_claim']['demand'] == 'singleton']
    known = [certified(states[e['id']]) for e in rows]
    source = [states[e['id']]['source_identity'] if k else 'UNKNOWN' for e, k in zip(rows, known)]
    names = {'demand_source_consistency': [s == 'T' for s in source],
             'grounded_evidence_rate': [s in ('T', 'X', 'P') for s in source],
             'wrong_source_read_rate': [s in ('X', 'P') for s in source],
             'prior_fill_rate': [states[e['id']]['state'] == 'PRIOR_FILL' and k for e, k in zip(rows, known)]}
    result = dict(eligible_events=len(rows), eligible_bases=len({e['base_id'] for e in rows}),
                  certified_events=sum(known), unresolved_or_weak_tier2_events=len(rows)-sum(known),
                  scope='Controlled stress sample; source necessity at fixed native prefix; not natural prevalence',
                  denominator='All singleton V claims, with unresolved explicitly retained. Certification lower bounds are not evidence of absence in the remainder.',
                  binding_diagnostics_excluded=True, rates={})
    for name, vals in names.items():
        result['rates'][name] = dict(
            certified_lower_bound_all_claims=family_rate(rows, vals),
            among_certified_only=family_rate(rows, [v if k else None for v, k in zip(vals, known)]))
    result['counterfactual_followability'] = family_rate(rows, [semantic_follows(metrics[e['id']], thresholds) for e in rows])
    result['counterfactual_followability']['denominator'] = 'Only events with measured target semantic and sham controls; missing controls are excluded, measured failures retained.'
    return result


def correctness_matrix(entries, states):
    rows = []
    for e in entries:
        if e['readout_type'] != 'V' or e['reviewed_claim']['demand'] != 'singleton':
            continue
        s = states[e['id']]
        identity = s['source_identity'] if certified(s) else 'UNKNOWN'
        fidelity = ('demanded_source' if identity == 'T' else
                    'other_or_no_source' if identity in ('X', 'P', None) else 'unresolved')
        down = e.get('downstream_review') or {}
        rows.append(dict(id=e['id'], event_id=e['event_id'], base_id=e['base_id'], group_id=e['group_id'],
                         split=e['split'], dataset=e['dataset'], condition=e['condition'],
                         causal_state=s['state'], source_fidelity=fidelity,
                         local_correct=e['reviewed_claim']['locally_correct'],
                         later_error=down.get('later_error', down.get('downstream_error')),
                         integration_error_reviewed=down.get('integration_error_eligible'),
                         final_correct=down.get('final_correct')))
    def count(key):
        out = {}
        for fidelity in ('demanded_source', 'other_or_no_source', 'unresolved'):
            subset = [r for r in rows if r['source_fidelity'] == fidelity]
            out[fidelity] = {str(value): sum(r[key] is value for r in subset) for value in (True, False, None)}
        return out
    return dict(rows=rows, local_correctness=count('local_correct'), final_correctness=count('final_correct'),
                later_error=count('later_error'),
                definition='Source fidelity means certified causal source equals demanded source. It can coexist with a wrong extraction. FAITHFUL_READ state additionally requires local correctness.',
                unknown_final_correctness_is_not_an_error=True,
                intermediate_error_does_not_imply_wrong_final_answer=True)


def state_yields(entries, states):
    selected = [states[e['id']] for e in entries if e['readout_type'] == 'V']
    names = ('FAITHFUL_READ', 'PRIOR_FILL', 'WRONG_SOURCE_READ', 'STALE_SOURCE_READ',
             'SOURCE_COUPLED_EXTRACTION_ERROR', 'DOWNSTREAM_INTEGRATION_ERROR', 'UNRESOLVED')
    return {name: dict(events=sum(s['state'] == name for s in selected),
                       certified_events=sum(s['state'] == name and certified(s) for s in selected),
                       bases=len({s['base_id'] for s in selected if s['state'] == name}),
                       independent_families=len({s['group_id'] for s in selected if s['state'] == name}))
            for name in names}
