from scripts.stage7a.primary_statistics import contrasts


def test_wrong_source_test_keeps_negative_effects_and_does_not_need_causal_labels():
    entry = dict(id='e', base_id='b', group_id='g', readout_type='V', condition='strong',
                 reviewed_claim=dict(demand='singleton', locally_correct=False, kind='primary', readout_char_end=10),
                 source_separation_valid=True, source_aliases={}, downstream_review=None)
    metric = dict(source_effects={'X_W2': {'EP_token': -2., 'EP_margin': -3.},
                                 'T_W2': {'EP_margin': 1.}},
                  semantic_effects={'X': {'net_semantic_beyond_sham': -4.}}, distribution_similarity={})
    result = contrasts([entry], {'e': metric}, {})
    assert result['3']['X_EP_token']['groups'] == {'g': -2.}
    assert result['3']['X_minus_T_EP_margin']['groups'] == {'g': -4.}
    assert not result['3']['X_EP_token']['directionally_robust']


def test_binding_readout_is_not_counted_as_a_value_state_validation():
    entry = dict(id='binding', readout_type='B', reviewed_claim=dict(demand='singleton'))
    result = contrasts([entry], {}, {})
    assert all(test['status'] == 'UNAVAILABLE' for family in result.values() for test in family.values())
