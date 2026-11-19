"""The interim gate must preserve units, missingness and fixed thresholds."""
from copy import deepcopy

import pytest

from scripts.stage7a_bench.mathwild_feasibility_v5 import evaluate_gate, METRICS


def packet(n=96):
    reviews, ledger = [], []
    for i in range(n):
        reviews.append(dict(event_id=f'e{i}', base_id=f'b{i}', native_index=i,
                            truncation=False, claims=[dict(locally_correct=False, demand='singleton')]))
        row = dict(event_id=f'e{i}', claim_index=0, independent_local_event=True,
                   source_localizable=False, evidence_verified=True,
                   causal_or_passive_scores_used=False)
        row.update({k: False for k in METRICS})
        ledger.append(row)
    coverage = dict(screen=dict(screen_complete=n == 96, reviewed=n), reviews=reviews,
                    family_map={f'b{i}': f'f{i//2}' for i in range(96)})
    pairs = [dict(base_id=f'b{i}', interpretable_transition=None, evidence_verified=False,
                  causal_or_passive_scores_used=False) for i in range(64)]
    return coverage, ledger, pairs, [f'b{i}' for i in range(64)]


def local_failure(row):
    row.update(source_localizable=True, source_localizable_failure_candidate=True,
               local_visual_value_error_candidate=True,
               wrong_source_or_entity_binding_candidate=True,
               source_coupled_extraction_error_candidate=True)


def test_fixed_A_gate_unions_overlapping_axes_and_nests_family_counts():
    args = packet()
    for row in args[1][:12]: local_failure(row)
    result = evaluate_gate(*args)
    assert result['decision'] == 'CONTINUE_FROZEN_MATHWILD_SAMPLE'
    assert result['criteria']['A']['positive_events'] == 12
    assert result['criteria']['A']['positive_bases'] == 12
    assert result['criteria']['A']['positive_families'] == 6
    assert result['criteria']['C']['unknown_events'] == 64


def test_eleven_A_candidates_and_unassessed_pairs_cannot_be_negative_gate():
    args = packet()
    for row in args[1][:11]: local_failure(row)
    assert evaluate_gate(*args)['decision'] == 'PENDING_SEMANTIC_ELIGIBILITY'


def test_negative_gate_requires_all_potential_criteria_resolved_below_threshold():
    args = packet()
    for pair in args[2]: pair.update(interpretable_transition=False, evidence_verified=True)
    assert evaluate_gate(*args)['decision'] == 'STOP_MATHWILD_LOW_YIELD'


def test_exact_pairs_pass_only_when_generated_review_evidence_verified():
    args = packet()
    for pair in args[2][:10]: pair.update(interpretable_transition=True, evidence_verified=True)
    assert evaluate_gate(*args)['decision'] == 'CONTINUE_FROZEN_MATHWILD_SAMPLE'
    args[2][0]['evidence_verified'] = False
    with pytest.raises(ValueError): evaluate_gate(*args)


def test_primary_gate_never_releases_before_all_exact96_reviews():
    args = packet(54)
    for row in args[1][:12]: local_failure(row)
    with pytest.raises(ValueError): evaluate_gate(*args)
    assert evaluate_gate(*args, require_complete=False)['decision'] is None


@pytest.mark.parametrize('mutation', ['duplicate', 'missing', 'extra', 'score', 'wrong_index', 'no_evidence'])
def test_bad_or_score_contaminated_claim_ledger_rejected(mutation):
    args = packet()
    if mutation == 'duplicate': args[1].append(deepcopy(args[1][0]))
    elif mutation == 'missing': args[1].pop()
    elif mutation == 'extra': args[1][0]['event_id'] = 'outside'
    elif mutation == 'score': args[1][0]['causal_effect_sizes'] = 0.9
    elif mutation == 'wrong_index': args[0]['reviews'][95]['native_index'] = 96
    else:
        local_failure(args[1][0]); args[1][0]['evidence_verified'] = False
    with pytest.raises(ValueError): evaluate_gate(*args)


def test_repeated_claim_does_not_inflate_A():
    args = packet()
    for row in args[1][:12]: local_failure(row)
    args[1][11]['independent_local_event'] = False
    result = evaluate_gate(*args)
    assert result['criteria']['A']['positive_events'] == 11
    assert result['decision'] == 'PENDING_SEMANTIC_ELIGIBILITY'


@pytest.mark.parametrize('problem', ['multi', 'cap', 'correct', 'no_readout', 'no_roi'])
def test_B_requires_oriented_eligible_failure_not_a_prepared_claim(problem):
    args = packet()
    for row in args[1][:16]:
        local_failure(row)
        row.update(proper_pilot_failure_event_eligible=True,
                   clean_demanded_source_roi=True, valid_oriented_local_readout=True)
    if problem == 'multi': args[0]['reviews'][0]['claims'][0]['demand'] = 'multi'
    elif problem == 'cap': args[0]['reviews'][0]['truncation'] = True
    elif problem == 'correct': args[0]['reviews'][0]['claims'][0]['locally_correct'] = True
    elif problem == 'no_readout': args[1][0]['valid_oriented_local_readout'] = None
    else: args[1][0]['clean_demanded_source_roi'] = False
    with pytest.raises(ValueError): evaluate_gate(*args)


def test_accuracy_cannot_change_gate_result():
    args = packet()
    for row in args[1][:12]: local_failure(row)
    a = evaluate_gate(*args)
    args[0]['screen']['final_accuracy'] = {'value': 0.0}
    assert evaluate_gate(*args) == a


def test_B_cannot_count_correct_reads_when_A_is_not_claimed():
    args = packet()
    args[0]['reviews'][0]['claims'][0]['locally_correct'] = True
    args[1][0].update(proper_pilot_failure_event_eligible=True,
                      source_localizable=True, clean_demanded_source_roi=True,
                      valid_oriented_local_readout=True)
    with pytest.raises(ValueError, match='B requires'):
        evaluate_gate(*args)
