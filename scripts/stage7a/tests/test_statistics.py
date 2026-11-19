from visual_reasoning.stage7a.statistics import collapse_groups, holm_within_family


def test_duplicate_events_cannot_turn_one_base_into_an_independent_cohort():
    rows = [dict(base_id='a', group_id='g1', value=3.)]*100
    rows += [dict(base_id='b', group_id='g1', value=1.), dict(base_id='c', group_id='g2', value=-1.)]
    assert collapse_groups(rows) == {'g1': 2., 'g2': -1.}


def test_holm_and_all_four_robustness_requirements():
    base = dict(median=1., mean_ci95=[.1, 2.], positive_group_fraction=.8)
    result = holm_within_family({'a': {**base, 'p_one_sided': .01},
                                 'b': {**base, 'p_one_sided': .02, 'positive_group_fraction': .7},
                                 'empty': {'p_one_sided': None}})
    assert result['a']['holm_p'] == .02 and result['a']['directionally_robust']
    assert result['b']['holm_p'] == .02 and not result['b']['directionally_robust']
    assert not result['empty']['directionally_robust']
