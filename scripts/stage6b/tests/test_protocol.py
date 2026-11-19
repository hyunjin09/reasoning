import pytest

from visual_reasoning.stage6b.protocol import candidate_event, c2_roles, assigned_rank


class CharacterTokenizer:
    def encode(self, text, **kwargs):
        return list(map(ord, text))

    def decode(self, ids, **kwargs):
        return ''.join(map(chr, ids))


def test_alignment_only_still_demands_another_image_source():
    roles = c2_roles({'condition': 'A_only', 'demanded_sources': ['X']})
    assert roles == {'focal': 'T', 'aligned': 'T', 'demanded': 'X',
                     'alternative': 'T', 'alignment': True, 'focal_demand': False}
    assert c2_roles({'condition': 'R_only', 'demanded_sources': ['T']})['focal_demand']


def test_inconsistent_frozen_source_mapping_is_rejected():
    with pytest.raises(ValueError, match='demand'):
        c2_roles({'condition': 'AR', 'demanded_sources': ['X']})


def test_wrong_native_readout_does_not_reverse_correct_vs_foil_orientation():
    text = 'The visible source value is 99.'
    tokens = [{'decoded_token': c, 'token_id': ord(c)} for c in text]
    start = text.index('99')
    event = candidate_event(tokens, start, start+2, '10', '14', CharacterTokenizer())
    assert event['history_before_ed_token_ids'] == list(map(ord, text[:start]))
    assert event['original_divergent_suffix_ids'] == [ord('1'), ord('0')]
    assert event['counterfactual_divergent_suffix_ids'] == [ord('1'), ord('4')]
    assert event['native_claim_suffix_ids'] == [ord('9'), ord('9')]
    assert event['candidate_start_token'] == event['current_query_zero_based'] + 1


def test_early_readout_cannot_silently_change_eight_query_execution_shape():
    tokens = [{'decoded_token': c, 'token_id': ord(c)} for c in 'x=10']
    with pytest.raises(ValueError, match='eight'):
        candidate_event(tokens, 2, 4, '10', '14', CharacterTokenizer())


def test_only_two_devices_in_authorized_allocation_are_accepted():
    env = {'SLURM_JOB_ID': '110860', 'WORLD_SIZE': '2', 'LOCAL_RANK': '1'}
    assert assigned_rank(env, 2, '110860') == 1
    with pytest.raises(ValueError):
        assigned_rank(env, 4, '110860')
    with pytest.raises(ValueError):
        assigned_rank(env, 2, '109385')
