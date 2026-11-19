"""Count explicitly reviewed semantic eligibility under the user-fixed gate.

Callers must verify coverage with mathwild_gate_coverage_v5 and bind each manual
source/readout judgment and exact-pair judgment to its evidence before calling.
This module does not infer eligibility, read model scores, admit a pilot or
release GPU work. Unknown assessments remain unknown, including unrun pairs.
"""
from collections import Counter


METRICS = (
    'local_visual_value_error_candidate', 'wrong_source_or_entity_binding_candidate',
    'source_coupled_extraction_error_candidate', 'faithful_control_candidate',
    'clean_demanded_source_roi', 'plausible_alternative_source',
    'valid_oriented_local_readout', 'source_localizable_failure_candidate',
    'proper_pilot_failure_event_eligible',
)
CLAIM_FIELDS = set(METRICS) | {
    'event_id', 'claim_index', 'independent_local_event', 'source_localizable',
    'evidence_verified', 'causal_or_passive_scores_used',
}
PAIR_FIELDS = {'base_id', 'interpretable_transition', 'evidence_verified',
               'causal_or_passive_scores_used'}


def _bool_or_unknown(value):
    return value is None or type(value) is bool


def _count(rows, field, families):
    positive = [row for row in rows if row[field] is True]
    base_counts = Counter(row['base_id'] for row in positive)
    family_counts = Counter(families[row['base_id']] for row in positive)
    return dict(positive_events=len(positive), negative_events=sum(row[field] is False for row in rows),
                unknown_events=sum(row[field] is None for row in rows),
                positive_bases=len(base_counts), positive_families=len(family_counts),
                positive_events_by_base=dict(sorted(base_counts.items())),
                positive_events_by_family=dict(sorted(family_counts.items())))


def evaluate_gate(coverage, ledger, pairs, expected_paired_base_ids, *, require_complete=True):
    reviews, screen, families = coverage['reviews'], coverage['screen'], coverage['family_map']
    ids = [r['event_id'] for r in reviews]
    indices = [r['native_index'] for r in reviews]
    if (len(ids) != len(set(ids)) or len(indices) != len(set(indices)) or
            any(type(i) is not int or not 0 <= i < 96 for i in indices) or
            screen['reviewed'] != len(reviews)):
        raise ValueError('Gate coverage must contain distinct frozen0..95 native units')
    complete = screen['screen_complete'] is True and set(indices) == set(range(96))
    if require_complete and not complete:
        raise ValueError('All exact96 full native reviews are required before a gate decision')
    expected = {(r['event_id'], i): (r, claim)
                for r in reviews for i, claim in enumerate(r['claims'])}
    keys = [(r.get('event_id'), r.get('claim_index')) for r in ledger]
    if len(keys) != len(set(keys)) or set(keys) != set(expected):
        raise ValueError('Exactly one explicit eligibility record is required for every reviewed claim')
    events = []
    for row in ledger:
        if set(row) != CLAIM_FIELDS:
            raise ValueError('Only the fixed semantic/source/readout fields may enter the gate')
        native, claim = expected[(row['event_id'], row['claim_index'])]
        if (native['base_id'] not in families or not families[native['base_id']] or
                row['causal_or_passive_scores_used'] is not False or
                type(row['independent_local_event']) is not bool or
                type(row['evidence_verified']) is not bool or
                any(not _bool_or_unknown(row[k]) for k in (*METRICS, 'source_localizable'))):
            raise ValueError('Explicit semantic judgments and verified source family are required')
        if any(row[k] is True for k in METRICS) and not row['evidence_verified']:
            raise ValueError('Positive eligibility needs verified manual evidence')
        if row['source_localizable_failure_candidate'] is True and (
                claim['locally_correct'] is not False or row['source_localizable'] is not True or
                not any(row[k] is True for k in METRICS[:3])):
            raise ValueError('A requires an actual local error and independently localizable source')
        if row['proper_pilot_failure_event_eligible'] is True and (
                claim['locally_correct'] is not False or claim['demand'] != 'singleton' or
                native['truncation'] is not False or row['source_localizable'] is not True or
                row['clean_demanded_source_roi'] is not True or
                row['valid_oriented_local_readout'] is not True):
            raise ValueError('B requires completed native demand, source identity and oriented error readout')
        if row['faithful_control_candidate'] is True and claim['locally_correct'] is not True:
            raise ValueError('Faithful-control candidate must have a correctly reviewed local claim')
        if row['independent_local_event']:
            events.append(dict(row, base_id=native['base_id']))
    pair_ids = [r.get('base_id') for r in pairs]
    if (len(expected_paired_base_ids) != len(set(expected_paired_base_ids)) or
            len(pair_ids) != len(set(pair_ids)) or set(pair_ids) != set(expected_paired_base_ids)):
        raise ValueError('Each frozen exact pair needs one explicit transition assessment')
    for pair in pairs:
        if (set(pair) != PAIR_FIELDS or pair['base_id'] not in families or
                pair['causal_or_passive_scores_used'] is not False or
                type(pair['evidence_verified']) is not bool or
                not _bool_or_unknown(pair['interpretable_transition']) or
                pair['interpretable_transition'] is not None and not pair['evidence_verified']):
            raise ValueError('Measured exact-pair transitions require verified semantic native evidence')
    metrics = {key: _count(events, key, families) for key in METRICS}
    criteria = {
        'A': dict(metrics['source_localizable_failure_candidate'], threshold=12),
        'B': dict(metrics['proper_pilot_failure_event_eligible'], threshold=16),
        'C': dict(_count(pairs, 'interpretable_transition', families), threshold=10),
    }
    for row in criteria.values():
        row['outcome'] = ('DEFERRED_UNTIL_96_REVIEWS' if not require_complete else
                          'PASS' if row['positive_events'] >= row['threshold'] else
                          'FAIL' if row['positive_events'] + row['unknown_events'] < row['threshold'] else
                          'UNASSESSED_POTENTIAL')
    decision = None
    if require_complete:
        outcomes = {row['outcome'] for row in criteria.values()}
        decision = ('CONTINUE_FROZEN_MATHWILD_SAMPLE' if 'PASS' in outcomes else
                    'STOP_MATHWILD_LOW_YIELD' if outcomes == {'FAIL'} else
                    'PENDING_SEMANTIC_ELIGIBILITY')
    return dict(status='COMPLETE_96_REVIEW_GATE' if require_complete else 'PROVISIONAL_NO_GATE_DECISION',
                reviewed_native_examples=len(reviews), independent_local_events=len(events),
                excluded_repeated_events=len(ledger)-len(events), metrics=metrics, criteria=criteria,
                decision=decision, thresholds_retuned=False, causal_or_passive_scores_used=False,
                pilot_admission=False, max_mathwild_conditions=264)
