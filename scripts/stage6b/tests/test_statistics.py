import pytest

from visual_reasoning.stage6b.statistics import holm, paired_effect, robustness


def test_holm_adjustment_is_monotone_in_ordered_pvalues():
    assert holm([.01, .04, .03]) == pytest.approx([.03, .06, .06])


def test_identical_zero_effects_are_valid_negative_evidence():
    result = paired_effect([0.] * 12)
    assert result['p_raw'] == 1.
    assert result['bootstrap_mean_ci95'] == [0., 0.]
    assert not robustness(result, 1.)


def test_repeated_events_do_not_inflate_independent_sample_count():
    result = paired_effect([1.] * 12, groups=['one']*6 + ['two']*6)
    assert result['bases'] == 12
    assert result['independent_groups'] == 2
    assert not robustness(result, result['p_raw'])


def test_uniform_positive_family_effect_can_pass_all_predeclared_gates():
    result = paired_effect([.2] * 12)
    assert robustness(result, result['p_raw'])
