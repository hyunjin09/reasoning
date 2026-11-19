import pytest

from scripts.stage6br.semantic_contract import blind_span, demand_type, transition_type, primary_semantic_eligible


@pytest.mark.parametrize('pre,post,label', [
    (['A'], ['A'], 'T0'), (['A'], ['B'], 'T1'),
    (['A'], ['A', 'B'], 'T2'), (['A', 'B'], ['B'], 'T3'),
    (['A', 'B'], ['B', 'C'], 'T4'), ([], ['A'], 'T5'),
    (['A'], [], 'T5'), (None, ['A'], 'UNRESOLVED'),
    (['A', 'B'], ['C', 'D'], 'T1'), (['B', 'A'], ['A', 'B'], 'T0'),
])
def test_set_transitions(pre, post, label):
    assert transition_type(pre, post) == label


def test_unknown_demand_is_not_empty_visual_demand():
    assert demand_type(None) == 'UNRESOLVED'
    assert demand_type([]) == 'NONE_VISUAL'
    assert transition_type(None, None) == 'UNRESOLVED'


def test_compound_or_empty_hold_is_not_primary_single_source_hold():
    assert primary_semantic_eligible(['A'], ['A'])
    assert primary_semantic_eligible(['A'], ['B'])
    assert not primary_semantic_eligible(['A', 'B'], ['A', 'B'])
    assert not primary_semantic_eligible([], [])
    assert not primary_semantic_eligible(None, ['B'])


def test_blind_packet_does_not_copy_nested_scores_or_outcomes():
    raw = dict(span_id='S1', text='Use AB and CD.', char_start=0, char_end=14,
               token_start=0, token_end=5, normalized_token_progress=.1,
               attention=.8, final_correctness='wrong', native_token_ids=[1, 2],
               source_claims=[{'correct': False}], extra={'VSD': 7},
               demanded_sources=['A'], prior_dynamic_label='FIXATION')
    result = blind_span(raw)
    assert set(result) == {'span_id', 'text', 'char_start', 'char_end',
                           'token_start', 'token_end', 'normalized_token_progress'}
    assert result['text'] == raw['text']
