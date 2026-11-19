"""Eligibility must remain bound to the actual reviewed claim and its scope."""
from copy import deepcopy

import pytest

from scripts.stage7a_bench.causal_provenance_v2 import object_sha
from scripts.stage7a_bench.mathwild_semantic_ledger_v5 import build_ledger


def packet():
    claim = dict(source_id='net_count', readout='five', ground_truth='six',
                 demand='singleton', locally_correct=False)
    review = dict(event_id='photo', base_id='base', native_index=68,
                  truncation=False, claims=[claim])
    assessment = dict(event_id='photo', base_id='base', native_index=68,
        claim_index=0, source_id='net_count', emitted_readout='five', source_truth='six',
        demand='singleton', claim_sha256=object_sha(claim),
        semantic_review_object_sha256=object_sha(review), causal_or_passive_scores_used=False,
        source_localizable=True, source_localizable_failure_candidate=True,
        local_visual_value_error_candidate=True, proper_pilot_failure_event_eligible=False,
        proper_pilot_eligibility_status='NOT_ADMITTED_PENDING_SEPARATE_READOUT_FRESHNESS_AND_SOURCE_COMPILATION')
    return dict(reviews=[review]), [assessment]


def test_preparation_pending_is_unknown_not_a_measured_failure_ineligibility():
    ledger, _ = build_ledger(*packet())
    assert ledger[0]['source_localizable_failure_candidate'] is True
    assert ledger[0]['proper_pilot_failure_event_eligible'] is None
    assert ledger[0]['valid_oriented_local_readout'] is None


def test_explicit_incidental_exclusion_stays_false():
    coverage, assessments = packet()
    assessments[0].update(proper_pilot_eligibility_status='REVIEWED_EXCLUDED_INCIDENTAL',
                          source_localizable_failure_candidate=False,
                          local_visual_value_error_candidate=False)
    assert build_ledger(coverage, assessments)[0][0]['proper_pilot_failure_event_eligible'] is False


@pytest.mark.parametrize('field,value', [
    ('claim_sha256', 'stale'), ('semantic_review_object_sha256', 'stale'),
    ('source_id', 'other_source'), ('source_truth', 'five'),
    ('native_index', 69), ('causal_or_passive_scores_used', True)])
def test_stale_or_misbound_source_assessment_rejected(field, value):
    coverage, assessments = packet()
    assessments[0][field] = value
    with pytest.raises(ValueError):
        build_ledger(coverage, assessments)


def test_duplicate_assessment_cannot_inflate_or_silently_replace_an_event():
    coverage, assessments = packet()
    assessments.append(deepcopy(assessments[0]))
    with pytest.raises(ValueError):
        build_ledger(coverage, assessments)


@pytest.mark.parametrize('change', ['multi', 'cap'])
def test_unassessed_multi_or_capped_claim_cannot_enter_primary_pilot(change):
    coverage, _ = packet()
    if change == 'multi':
        coverage['reviews'][0]['claims'][0]['demand'] = 'multi'
    else:
        coverage['reviews'][0]['truncation'] = True
    ledger, _ = build_ledger(coverage, [])
    assert ledger[0]['proper_pilot_failure_event_eligible'] is False
    assert ledger[0]['source_localizable_failure_candidate'] is None


def test_correct_read_without_source_review_is_not_certified_faithful_control():
    coverage, _ = packet()
    coverage['reviews'][0]['claims'][0]['locally_correct'] = True
    ledger, _ = build_ledger(coverage, [])
    assert ledger[0]['faithful_control_candidate'] is None
    assert ledger[0]['source_localizable_failure_candidate'] is False
    assert ledger[0]['proper_pilot_failure_event_eligible'] is False


@pytest.mark.parametrize('admitted', [False, True])
def test_correct_read_cannot_remain_a_potential_B_failure_after_source_join(admitted):
    coverage, assessments = packet()
    review = coverage['reviews'][0]
    claim = review['claims'][0]
    claim.update(locally_correct=True, ground_truth='five')
    assessments[0].update(source_truth='five', local_visual_value_error_candidate=False,
        source_localizable_failure_candidate=False, claim_sha256=object_sha(claim),
        semantic_review_object_sha256=object_sha(review),
        proper_pilot_failure_event_eligible=admitted)
    if admitted:
        with pytest.raises(ValueError, match='correct'):
            build_ledger(coverage, assessments)
    else:
        assert build_ledger(coverage, assessments)[0][0]['proper_pilot_failure_event_eligible'] is False


def test_source_assessment_cannot_promote_repeated_event_without_explicit_uniqueness():
    coverage, assessments = packet()
    assessments[0]['independent_local_event'] = False
    assert build_ledger(coverage, assessments)[0][0]['independent_local_event'] is False
