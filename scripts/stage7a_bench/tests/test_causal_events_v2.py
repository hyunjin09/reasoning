from copy import deepcopy

import pytest

from scripts.stage7a_bench.tests.test_causal_readouts_v2 import tokenizer, example
from scripts.stage7a_bench.tests.test_source_mapping_v2 import metadata, segment, box
from scripts.stage7a_bench.causal_events_v2 import compile_event


def fixture(tokenizer):
    tokens, claim = example(tokenizer, '12', source_id='requested_series', ground_truth='10')
    row = dict(event_id='chart__image_present', base_id='chart', benchmark='charxiv',
               condition='image_present', no_image=False, family_id='obsolete_filename_family')
    review = dict(event_id=row['event_id'], base_id=row['base_id'], benchmark=row['benchmark'],
                  condition=row['condition'], claims=[claim], causal_or_passive_scores_used=False)
    meta = dict(metadata(segment('image_1', 10)), event_id=row['event_id'],
                condition=row['condition'], prompt_token_ids=list(range(30)))
    annotation = dict(demanded_source_id='requested_series', target_ground_truth='10',
        target_source_status='available', source_review_note='The requested series is the first field.',
        causal_or_passive_scores_used=False, independently_identified_target_and_alternative=True,
        sources={'T': [box('image_1', [0, 0, 1, 1])], 'X': [box('image_1', [12, 10, 13, 11])]},
        candidates=dict(correct='10', foil='14', target_semantic='14', alternative_original='12',
                        alternative_semantic='16'),
        alternative=dict(source_id='other_series', wrong_claim_matches=True,
                         review_note='The native12 belongs to the other series, whose value is12.'))
    return row, review, 0, meta, tokens, annotation, {'chart': 'verified_shared_source_family'}, tokenizer


def test_compilation_preserves_native_readout_and_uses_verified_family(tokenizer):
    result = compile_event(*fixture(tokenizer))
    assert result['analysis_family_id'] == 'verified_shared_source_family'
    assert result['native_family_id'] == 'obsolete_filename_family'
    assert result['reviewed_claim']['wrong_claim_matches_alternative'] is True
    assert result['source_separation_valid'] is True
    assert result['w2_sources'] == ['T', 'X', 'G']
    assert result['w8_sources'] == ['T', 'X']
    assert result['event']['native_claim_semantic_value'] == '12'
    assert result['causal_state'] is None and result['causal_pilot_frozen'] is False


def test_pixel_disjoint_sources_sharing_a_token_cannot_gain_independence(tokenizer):
    args = list(fixture(tokenizer))
    args[5]['sources']['X'] = [box('image_1', [1, 0, 2, 1])]
    result = compile_event(*args)
    assert result['source_separation_valid'] is False
    assert result['source_mapping']['token_overlaps']['T_X'] == [10]
    assert result['w8_sources'] == ['T', 'X']


@pytest.mark.parametrize('problem', ['no_image', 'phantom', 'family', 'source', 'truth', 'scores', 'metadata'])
def test_no_source_and_mismatched_review_inputs_are_rejected(tokenizer, problem):
    args = list(fixture(tokenizer))
    if problem == 'no_image': args[0]['no_image'] = True
    if problem == 'phantom': args[0]['benchmark'] = 'phantom_0'
    if problem == 'family': args[6] = {}
    if problem == 'source': args[5]['demanded_source_id'] = 'unrelated_series'
    if problem == 'truth': args[5]['target_ground_truth'] = '12'
    if problem == 'scores': args[1]['causal_or_passive_scores_used'] = True
    if problem == 'metadata': args[3]['event_id'] = 'another_input'
    with pytest.raises(ValueError): compile_event(*args)


def test_missing_alternative_remains_missing_and_unreviewed_irrelevant_roi_is_rejected(tokenizer):
    args = list(fixture(tokenizer))
    del args[5]['sources']['X']
    del args[5]['alternative']
    args[5]['independently_identified_target_and_alternative'] = False
    args[5]['candidates'] = dict(correct='10', foil='14')
    result = compile_event(*args)
    assert result['w8_sources'] == ['T'] and result['source_separation_valid'] is False
    assert result['reviewed_claim']['wrong_claim_matches_alternative'] is None
    args[5]['sources']['I'] = [box('image_1', [12, 10, 13, 11])]
    with pytest.raises(ValueError, match='irrelevant'): compile_event(*args)


def test_alternative_match_is_adjudicated_and_cannot_be_inferred_from_token_coincidence(tokenizer):
    args = list(fixture(tokenizer))
    args[5]['alternative']['wrong_claim_matches'] = None
    result = compile_event(*args)
    assert result['event']['candidate_ids']['native'] == result['event']['candidate_ids']['alternative_original']
    assert result['reviewed_claim']['wrong_claim_matches_alternative'] is None
    args[5]['alternative']['wrong_claim_matches'] = True
    args[5]['candidates']['alternative_original'] = '13'
    with pytest.raises(ValueError, match='alternative'): compile_event(*args)


def test_compilation_does_not_mutate_review_or_annotation(tokenizer):
    args = fixture(tokenizer)
    before = deepcopy(args[:-1])
    compile_event(*args)
    assert args[:-1] == before


def test_missing_match_judgment_is_not_silently_recorded_as_reviewed_unknown(tokenizer):
    args = list(fixture(tokenizer))
    del args[5]['alternative']['wrong_claim_matches']
    with pytest.raises(ValueError, match='alternative'): compile_event(*args)


def test_truth_candidate_cannot_be_any_non_native_value(tokenizer):
    args = list(fixture(tokenizer))
    args[5]['candidates']['correct'] = '99'
    with pytest.raises(ValueError, match='literal truth'): compile_event(*args)
