import pytest

from scripts.stage7a_bench.native_yield_v2 import summarize_condition, paired_comparison


def row(event, base=None, condition='image_present'):
    return dict(event_id=event, base_id=base or event, benchmark='example', condition=condition)


def review(event, correctness=None, label='F6', **extra):
    return dict(event_id=event, base_id=event, screen_label=label,
                final_correctness=correctness, local_visual_claim_present=False,
                local_visual_claim_correctness=None, unsupported_evidence_claim=False,
                abstention_or_caveat=False, **extra)


def test_unknown_accuracy_is_not_zero_and_missing_input_is_not_error():
    manifest = [row('a'), row('b'), row('c')]
    results = [dict(event_id='a', truncated=False, elapsed_seconds=2),
               dict(event_id='b', unavailable=True, unavailable_reason='missing_source', elapsed_seconds=0)]
    s = summarize_condition(manifest, results, [review('a')])
    assert (s['generated'], s['unavailable'], s['pending_generation'], s['reviewed']) == (1, 1, 1, 1)
    assert s['final_accuracy'] == dict(numerator=0, denominator=0, unknown=1, value=None)
    assert s['screen_complete'] is False
    assert s['truncation_rate']['denominator'] == 1


def test_final_accuracy_does_not_create_local_or_causal_labels():
    s = summarize_condition([row('a')], [dict(event_id='a', truncated=False)], [review('a', True)])
    assert s['final_accuracy']['value'] == 1
    assert s['local_visual_error_rate']['value'] is None
    assert s['faithful_control_candidate_rate']['numerator'] == 0
    assert s['eligible_causal_event_rate']['value'] is None
    assert s['screen_complete'] is True


def test_partial_review_and_generated_truncation_have_separate_denominators():
    s = summarize_condition([row('a'), row('b')],
        [dict(event_id='a', truncated=False), dict(event_id='b', truncated=True)],
        [review('a', False, 'F3')])
    assert s['final_accuracy']['denominator'] == 1
    assert s['truncation_rate']['denominator'] == 2
    assert s['pending_review'] == 1
    assert s['screen_complete'] is False


def test_duplicate_or_orphan_review_is_rejected():
    with pytest.raises(ValueError):
        summarize_condition([row('a')], [dict(event_id='a')], [review('a'), review('a')])
    with pytest.raises(ValueError):
        summarize_condition([row('a')], [], [review('a')])


def test_pairwise_denominator_is_common_reviewed_ids_only():
    left = [review('a', True), review('b', True)]
    right = [review('a', False), review('c', False)]
    s = paired_comparison(left, right)
    assert s['paired_reviewed'] == 1
    assert s['final_correctness_disagreement']['value'] == 1
    assert s['left_final_accuracy']['denominator'] == 1
    assert s['right_final_accuracy']['denominator'] == 1
    assert s['causal_label'] is None


def test_phantom_pair_does_not_gain_accuracy_from_agreement():
    s = paired_comparison([review('a')], [review('a')])
    assert s['final_correctness_disagreement']['value'] is None
    assert s['left_final_accuracy']['value'] is None
    assert s['causal_label'] is None


def test_phantom_source_absence_excludes_causal_pilot_without_assigning_state():
    manifest = [dict(row('a'), benchmark='phantom_0', no_image=True)]
    s = summarize_condition(manifest, [dict(event_id='a', truncated=False)],
                            [review('a', label='F3')])
    assert s['eligible_causal_event_rate'] == dict(numerator=0, denominator=1, unknown=0, value=0.)
    assert s['final_accuracy']['value'] is None
    assert s['local_visual_error_rate']['value'] is None
    assert 'No actual visual source' in s['causal_eligibility_basis']
    with pytest.raises(ValueError, match='Phantom'):
        summarize_condition([dict(manifest[0], no_image=False)], [], [])


def test_f5_screen_rate_is_separate_from_generic_caveats():
    judgments = [review('a', label='F5'), review('b', label='F6')]
    for judgment in judgments:
        judgment['abstention_or_caveat'] = True
    s = summarize_condition([row('a'), row('b')],
        [dict(event_id='a', truncated=False), dict(event_id='b', truncated=False)], judgments)
    assert s['uncertainty_abstention_screen_rate']['value'] == .5
    assert s['abstention_or_caveat_rate']['value'] == 1.


def test_pair_preserves_evidence_identity_and_expressed_confidence_without_causal_inference():
    claim = dict(identity='red truck in right lane', quote='A red truck is in the right lane.')
    left = review('a', claims=[claim], output_confidence='asserted confidently', guessed_answer=False)
    right = review('a', claims=[], output_confidence='caveated/uncertain', guessed_answer=False)
    s = paired_comparison([left], [right])
    assert s['paired_evidence'][0]['left_claims'] == [claim]
    assert s['paired_evidence'][0]['right_claims'] == []
    assert s['paired_evidence'][0]['left_output_confidence'] == 'asserted confidently'
    assert s['causal_label'] is None


def test_unadjudicated_class_is_unknown_not_a_negative_failure_candidate():
    s = summarize_condition([row('a'), row('b')],
        [dict(event_id='a', truncated=False), dict(event_id='b', truncated=False)],
        [review('a', label=None), review('b', label='F1')])
    assert s['screen_class_unadjudicated'] == 1
    assert s['screen_classes'] == {'F1': 1}
    assert s['local_error_candidate_per_reviewed_example'] == dict(
        numerator=1, denominator=1, unknown=1, value=1.)
    assert s['screen_complete'] is True
