import copy

import pytest

from scripts.stage7a_bench.image_semantic_reviews_v2 import validate_judgment


def judgment():
    return dict(screen_label='F0', final_correctness=False,
        final_correctness_reason='Independent arithmetic check of the final answer.',
        local_visual_claim_present=True, local_visual_claim_correctness=True,
        binding_claim_present=True, binding_claim_correctness=True,
        unsupported_evidence_claim=False,
        correct_local_read_followed_by_later_error=False,
        abstention_or_caveat=False, guessed_answer=False,
        review_note='Read the entire response and the chart.',
        source_review_note='Chart A blue bar is12; chart B blue bar is21.',
        task_quality='valid', output_confidence='unexpressed',
        claims=[dict(quote='Chart A reads12.', readout='12', source_id='chart_A',
            ground_truth='12', locally_correct=True, demand='singleton',
            question_provided=False, conditional=False, arithmetic_result=False)])


def test_wrong_final_does_not_change_locally_correct_screen():
    row = validate_judgment(judgment(), 'Chart A reads12. The sum is wrong.')
    assert row['screen_label'] == 'F0' and row['final_correctness'] is False
    assert row['claims'][0]['readout_char_start'] == 13


def test_claim_and_source_review_required_for_visual_label():
    for field in ('claims', 'source_review_note'):
        row = judgment()
        row[field] = [] if field == 'claims' else ''
        with pytest.raises(ValueError):
            validate_judgment(row, 'Chart A reads12.')


def test_missing_or_repeated_quote_not_silently_aligned():
    for raw in ('Chart B reads12.', 'Chart A reads12. Chart A reads12.'):
        with pytest.raises(ValueError):
            validate_judgment(judgment(), raw)


def test_uncertain_reference_stays_unknown_and_does_not_make_local_error():
    row = judgment()
    row.update(final_correctness=None, task_quality='reference_unverified',
               final_correctness_reason='Clinical reference has not been adjudicated.')
    result = validate_judgment(row, 'Chart A reads12.')
    assert result['final_correctness'] is None and result['local_visual_claim_correctness'] is True


def test_inconsistent_labels_and_truthy_strings_rejected():
    for patch in ({'screen_label': 'F1'}, {'screen_label': 'F2'},
                  {'screen_label': 'F3'}, {'screen_label': 'F4'},
                  {'screen_label': 'F5'}, {'screen_label': 'F6'},
                  {'final_correctness': 'false'}, {'causal_state': 'FAITHFUL_READ'}):
        row = judgment()
        row.update(patch)
        with pytest.raises(ValueError):
            validate_judgment(row, 'Chart A reads12.')


def test_claim_guards_preserve_semantic_not_question_or_arithmetic_read():
    for field in ('question_provided', 'conditional', 'arithmetic_result'):
        row = copy.deepcopy(judgment())
        row['claims'][0][field] = True
        with pytest.raises(ValueError):
            validate_judgment(row, 'Chart A reads12.')


def test_unverified_visual_claim_can_remain_unclassified_with_a_reason():
    row = judgment()
    row.update(screen_label=None, screen_label_reason='Source value cannot be independently adjudicated.',
               local_visual_claim_correctness=None, binding_claim_correctness=None)
    row['claims'][0].update(locally_correct=None, ground_truth=None)
    saved = validate_judgment(row, 'Chart A reads12.')
    assert saved['screen_label'] is None
    assert saved['local_visual_claim_present'] is True
    assert saved['local_visual_claim_correctness'] is None
    row.pop('screen_label_reason')
    with pytest.raises(ValueError):
        validate_judgment(row, 'Chart A reads12.')


def test_known_visual_error_cannot_be_hidden_as_unclassified():
    row = judgment()
    row.update(screen_label=None, screen_label_reason='Unknown', local_visual_claim_correctness=False)
    row['claims'][0].update(locally_correct=False, ground_truth='21')
    with pytest.raises(ValueError):
        validate_judgment(row, 'Chart A reads12.')
