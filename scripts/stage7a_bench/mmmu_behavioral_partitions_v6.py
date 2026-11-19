"""Describe the frozen single-model MMMU pairs without inferring causality.

Inputs are full semantic reviews verified by the completed-screen loader. The
published multi-model B-Clean protocol uses a different answer parser; these
local behavioral partitions do not reproduce its labels or select a cohort.
"""
from collections import Counter


CONDITIONS = ('image_present', 'silent_no_image', 'explicit_guess')


def summarize_pairs(groups, paired_base_ids, families):
    expected = set(paired_base_ids)
    if (not expected or len(expected) != len(paired_base_ids) or
            set(groups) != set(CONDITIONS) or not expected <= set(families)):
        raise ValueError('Exact paired universe, three conditions and source families required')
    indexed = {}
    for condition, reviews in groups.items():
        rows = {row['base_id']: row for row in reviews}
        if len(rows) != len(reviews) or any(
                r['benchmark'] != 'mmmu_pro' or r['condition'] != condition for r in reviews):
            raise ValueError('Unique bases and matching MMMU condition reviews required')
        if condition != 'image_present' and not set(rows) <= expected:
            raise ValueError('No-image reviews outside the frozen paired universe')
        indexed[condition] = rows

    evidence = []
    for base in sorted(expected):
        values = {}
        for condition in CONDITIONS:
            row = indexed[condition].get(base)
            if row is None:
                values[condition] = dict(outcome='missing', event_id=None,
                    final_correctness=None, truncated=None,
                    emitted_visual_claim=None, unsupported_claim=None)
                continue
            final, capped = row['final_correctness'], row['truncation']
            if (final is not None and type(final) is not bool or type(capped) is not bool or
                    any(type(row[k]) is not bool for k in
                        ('local_visual_claim_present', 'unsupported_evidence_claim'))):
                raise ValueError('Explicit correctness, truncation and claim judgments required')
            outcome = ('capped' if capped else 'unknown' if final is None else
                       'correct' if final else 'wrong')
            values[condition] = dict(outcome=outcome, event_id=row['event_id'],
                final_correctness=final, truncated=capped,
                emitted_visual_claim=row['local_visual_claim_present'],
                unsupported_claim=row['unsupported_evidence_claim'])
        absent = [values[c]['outcome'] for c in CONDITIONS[1:]]
        partition = ('some_absent_condition_correct' if 'correct' in absent else
                     'both_absent_conditions_wrong' if absent == ['wrong', 'wrong'] else
                     'unresolved_absent_conditions')
        evidence.append(dict(base_id=base, analysis_family_id=families[base],
            conditions=values, behavioral_partition=partition,
            visual_correct_and_both_absent_wrong=(
                values['image_present']['outcome'] == 'correct' and
                partition == 'both_absent_conditions_wrong')))

    def nested(rows):
        return dict(bases=len(rows), source_families=len({r['analysis_family_id'] for r in rows}),
            base_ids=[r['base_id'] for r in rows],
            bases_by_source_family=dict(sorted(Counter(r['analysis_family_id'] for r in rows).items())))

    return dict(status='LOCAL_SINGLE_MODEL_SEMANTIC_BEHAVIOR_ONLY',
        paired_universe=nested(evidence),
        condition_outcomes={c: dict(Counter(r['conditions'][c]['outcome'] for r in evidence))
                            for c in CONDITIONS},
        partitions={name: nested([r for r in evidence if r['behavioral_partition'] == name])
            for name in ('some_absent_condition_correct', 'both_absent_conditions_wrong',
                         'unresolved_absent_conditions')},
        visual_correct_and_both_absent_wrong=nested(
            [r for r in evidence if r['visual_correct_and_both_absent_wrong']]),
        paired_evidence=evidence, published_bclean_labels_reproduced=False,
        causal_states_assigned=False, subset_selected=False,
        scope='One frozen4B model and independently reviewed semantic final correctness; '
            'not the published multi-model/double-bracket-parser B-Clean labels. '
            'Missing, unadjudicated and capped outcomes cannot establish a wrong-answer partition. '
            'Specific visual claims and unsupported claims remain separate from answer correctness. '
            'No-image correctness, image advantage and these behavioral partitions do not certify '
            'PRIOR_FILL, visual dependence, nonvisual reasoning or causal B-Clean.')
