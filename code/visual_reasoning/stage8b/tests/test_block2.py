import numpy as np

from visual_reasoning.stage8b.block2_capture import routing_summary
from visual_reasoning.stage8b.block2_data import source_positions


def test_colliding_grid_cells_are_missing_not_reassigned():
    meta = dict(original_image_size=[8, 4], visual_token_indices=[10, 11],
                visual_mapping=dict(merged_grid_shape=[1, 1, 2]))
    sources = [dict(role='T', roi=[0, 0, 2, 2]), dict(role='X', roi=[2, 0, 4, 2]),
               dict(role='I', roi=[4, 0, 8, 4])]
    mapped, audit = source_positions(sources, meta)
    assert mapped == {'T': [], 'X': [], 'I': [11]}
    assert audit['excluded_shared_local_cells'] == [0]


def test_routing_uses_visual_share_and_missing_confuser_is_not_zero():
    result = routing_summary([[1, 0], [2, 0]], [[.2, .1], [.1, .3]], [[.1, .1], [.05, .3]], [.4, .5], ['T', 'I'])
    assert np.isclose(result['target_share'], .35)
    assert result['qk_T_X'] is None and result['share_T_X'] is None
    assert result['target_consensus'] == .5
    assert result['candidate_count'] == 2


def test_routing_source_order_is_irrelevant_and_single_source_is_not_consensus():
    qk = np.array([[3., 1.], [2., 4.]])
    mass = np.array([[.4, .2], [.2, .3]])
    first = routing_summary(qk, mass, mass, [.8, .6], ['T', 'X'])
    second = routing_summary(qk[:, ::-1], mass[:, ::-1], mass[:, ::-1], [.8, .6], ['X', 'T'])
    for key in ['target_share', 'target_rank', 'target_consensus', 'qk_T_X', 'share_T_X', 'source_entropy']:
        assert np.isclose(first[key], second[key])
    alone = routing_summary([[1]], [[.3]], [[.3]], [.5], ['T'])
    assert alone['target_consensus'] is alone['top2_margin'] is alone['source_entropy'] is None


def test_mixed_label_family_is_resampled_as_one_unit():
    import pandas as pd
    from visual_reasoning.stage8b.block2_statistics import FamilyBootstrap
    frame = pd.DataFrame(dict(family_id=['a', 'a', 'b', 'b'], local=['L+', 'L-', 'L+', 'L-'], value=[1., 3., 5., 7.]))
    bootstrap = FamilyBootstrap(frame, resamples=200)
    assert np.array_equal(bootstrap.weights[:, 0], bootstrap.weights[:, 1])
    assert np.array_equal(bootstrap.weights[:, 2], bootstrap.weights[:, 3])
    result, samples = bootstrap.contrast('value')
    assert result['effect_Lminus_minus_Lplus'] == 2
    assert np.allclose(samples, 2)
    assert np.isclose(result['standardized_effect'], 2/np.sqrt(8))
    # A bootstrap drawing one family repeatedly has zero within-class variance;
    # its standardized effect is unavailable, never infinity or false precision.
    assert result['standardized_ci']['ci95'] is None
    assert result['standardized_ci']['valid_resamples'] < 200


def test_paired_bootstrap_links_pairs_that_share_a_family():
    import pandas as pd
    from visual_reasoning.stage8b.block2_statistics import paired_comparisons
    frame = pd.DataFrame(dict(event_id=['a0', 'a1', 'b', 'c'], family_id=['a', 'a', 'b', 'c'], value=[3., 5., 1., 2.]))
    pairs = [dict(failure='a0', control='b'), dict(failure='a1', control='c')]
    result = paired_comparisons(frame, pairs, ['value'])
    assert result['independent_connected_family_components'] == 1
    assert result['metrics']['value']['mean_paired_difference'] == 2.5
