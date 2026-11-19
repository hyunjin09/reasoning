from copy import deepcopy

import pytest

from scripts.stage7a_bench.causal_events_v2 import compile_downstream_review, compile_event
from scripts.stage7a_bench.tests.test_causal_events_v2 import fixture, tokenizer


def evidence():
    raw = 'The selected bar says 12. Therefore twice this value is 25.'
    claim = dict(source_id='selected_bar', locally_correct=True)
    # Keep coordinates literal and checked against the actual response.
    claim.update(readout='12', readout_char_start=raw.index('12'),
                 readout_char_end=raw.index('12')+2)
    review = dict(claims=[claim], correct_local_read_followed_by_later_error=True)
    quote = 'Therefore twice this value is 25.'
    downstream = dict(status='REVIEWED_DOWNSTREAM_ERROR', claim_index=0,
        demanded_source_id='selected_bar', claim_readout_char_start=claim['readout_char_start'],
        claim_readout_char_end=claim['readout_char_end'], integration_error_eligible=True,
        later_error=True, error_quote=quote, error_char_start=raw.index(quote),
        error_char_end=len(raw), error_uses_selected_local_evidence=True,
        error_is_new_visual_read=False, causal_or_passive_scores_used=False,
        review_note='Twice the correctly read12 is24. The later25 is arithmetic, not another source read.')
    return review, 0, [dict(decoded_token=raw)], dict(downstream_review=downstream)


def test_review_retains_exact_later_error_without_inferring_causal_state():
    args = evidence()
    before = deepcopy(args)
    result = compile_downstream_review(*args)
    assert result == args[3]['downstream_review']
    assert result is not args[3]['downstream_review']
    assert args == before
    assert 'causal_state' not in result


def test_absent_review_stays_unavailable_even_when_final_answer_is_wrong():
    args = list(evidence())
    args[0]['final_correctness'] = False
    args[3] = {}
    assert compile_downstream_review(*args) is None


@pytest.mark.parametrize('problem', ['status', 'index', 'source', 'claim_span', 'wrong_local',
    'screen_relation', 'no_later_error', 'ineligible', 'quote', 'offset', 'earlier_error',
    'new_visual_read', 'unrelated_error', 'scores', 'note', 'repeated_quote'])
def test_unbound_or_semantically_ineligible_review_is_rejected(problem):
    args = list(evidence())
    review, _, tokens, annotation = args
    row = annotation['downstream_review']
    if problem == 'status': row['status'] = 'DRAFT'
    if problem == 'index': row['claim_index'] = 1
    if problem == 'source': row['demanded_source_id'] = 'other_bar'
    if problem == 'claim_span': row['claim_readout_char_end'] += 1
    if problem == 'wrong_local': review['claims'][0]['locally_correct'] = False
    if problem == 'screen_relation': review['correct_local_read_followed_by_later_error'] = False
    if problem == 'no_later_error': row['later_error'] = False
    if problem == 'ineligible': row['integration_error_eligible'] = False
    if problem == 'quote': row['error_quote'] = 'An invented later error.'
    if problem == 'offset': row['error_char_start'] -= 1
    if problem == 'earlier_error':
        row.update(error_quote='The selected bar says 12.', error_char_start=0, error_char_end=25)
    if problem == 'new_visual_read': row['error_is_new_visual_read'] = True
    if problem == 'unrelated_error': row['error_uses_selected_local_evidence'] = False
    if problem == 'scores': row['causal_or_passive_scores_used'] = True
    if problem == 'note': row['review_note'] = ''
    if problem == 'repeated_quote': tokens[0]['decoded_token'] += ' '+row['error_quote']
    with pytest.raises(ValueError): compile_downstream_review(*args)


def test_event_compilation_carries_only_bound_downstream_review(tokenizer):
    args = list(fixture(tokenizer))
    claim = args[1]['claims'][0]
    claim.update(locally_correct=True, ground_truth='12')
    args[1]['correct_local_read_followed_by_later_error'] = True
    args[5]['target_ground_truth'] = args[5]['candidates']['correct'] = '12'
    args[5]['alternative']['wrong_claim_matches'] = False
    raw = ''.join(t['decoded_token'] for t in args[4])
    quote = ' Therefore twice this value is 25.'
    args[4].extend(dict(token_id=i, decoded_token=tokenizer.decode([i]))
                   for i in tokenizer.encode(quote, add_special_tokens=False))
    downstream = evidence()[3]['downstream_review']
    downstream.update(demanded_source_id=claim['source_id'],
        claim_readout_char_start=claim['readout_char_start'],
        claim_readout_char_end=claim['readout_char_end'], error_quote=quote,
        error_char_start=len(raw), error_char_end=len(raw)+len(quote))
    args[5]['downstream_review'] = downstream
    entry = compile_event(*args)
    assert entry['downstream_review'] == downstream
    assert entry['causal_state'] is None and entry['causal_pilot_frozen'] is False

    # A valid textual later-error review still needs the inherited T-specific
    # causal and semantic evidence; it cannot manufacture that evidence.
    from visual_reasoning.stage7a.classification import classify
    from scripts.stage7a_bench.tests.test_causal_metrics_v2 import THRESHOLDS
    metrics = dict(source_effects={role+'_W2': dict(VSD=value, EP_token=0.,
        EP_margin=0., EP_claim=0.) for role, value in [('T', 2.), ('X', 0.), ('G', 2.)]},
        semantic_effects={'T': dict(net_semantic_beyond_sham=3., semantic_shift=3., sham_shift=0.)},
        distribution_similarity={})
    assert classify(entry, metrics, THRESHOLDS)['state'] == 'DOWNSTREAM_INTEGRATION_ERROR'
    metrics['semantic_effects'] = {}
    assert classify(entry, metrics, THRESHOLDS)['state'] == 'FAITHFUL_READ'
    metrics['semantic_effects'] = {'T': dict(net_semantic_beyond_sham=0., semantic_shift=0., sham_shift=0.)}
    assert classify(entry, metrics, THRESHOLDS)['state'] == 'UNRESOLVED'
