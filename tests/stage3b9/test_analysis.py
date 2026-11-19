import numpy as np

from visual_reasoning.stage3b9.analysis import (
    base_balanced_boolean_fraction,
    bootstrap_interval,
    unclipped_ratio,
)


def test_unclipped_ratio_preserves_sign_and_returns_none_at_zero():
    assert unclipped_ratio(2.0, -4.0) == -0.5
    assert unclipped_ratio(1.0, 0.0) is None


def test_bootstrap_interval_is_reproducible():
    values = np.array([1.0, 2.0, 3.0, 4.0])
    first = bootstrap_interval(values, statistic="median", resamples=200, seed=7)
    second = bootstrap_interval(values, statistic="median", resamples=200, seed=7)
    assert first == second
    assert first[0] <= np.median(values) <= first[1]


def test_boolean_fraction_aggregates_folds_within_base_first():
    rows = [
        {"base_problem_id": "a", "positive": True},
        {"base_problem_id": "a", "positive": True},
        {"base_problem_id": "a", "positive": True},
        {"base_problem_id": "b", "positive": False},
    ]
    result = base_balanced_boolean_fraction(rows, field="positive")
    assert result["per_base"] == {"a": 1.0, "b": 0.0}
    assert result["across_base_mean"] == 0.5
