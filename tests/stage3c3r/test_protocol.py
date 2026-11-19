from __future__ import annotations

from visual_reasoning.stage3c3r.protocol import (
    approximate_monotonic_decrease,
    redundancy_gate,
    tested_thresholds as compute_tested_thresholds,
)


def test_redundancy_gate_uses_base_level_mean_across_targets() -> None:
    rows = {
        "a": {"target_a": 0.7, "target_b": 0.5},
        "b": {"target_a": 0.4, "target_b": 0.8},
        "c": {"target_a": 0.2, "target_b": 0.4},
    }
    result = redundancy_gate(rows)

    assert result["base_retained"] == {"a": 0.6, "b": 0.6000000000000001, "c": 0.30000000000000004}
    assert result["median_retained"] == 0.6
    assert result["passed"] is True


def test_redundancy_gate_can_pass_on_high_retention_fraction() -> None:
    rows = {
        str(index): {"target_a": value, "target_b": value}
        for index, value in enumerate([0.9, 0.85, 0.1, 0.1, 0.1])
    }
    result = redundancy_gate(rows)

    assert result["fraction_at_least_0_80"] == 0.4
    assert result["passed"] is True


def test_thresholds_use_smallest_tested_lambda_without_interpolation() -> None:
    curve = {1.0: 10.0, 0.75: 9.0, 0.5: 8.2, 0.25: 4.9, 0.1: 2.0, 0.0: 0.0}
    assert approximate_monotonic_decrease(curve)
    result = compute_tested_thresholds(curve)

    assert result["lambda_80"] == 0.5
    assert result["lambda_50"] == 0.5
    assert result["interpolated"] is False


def test_nonmonotonic_curve_has_no_threshold_claim() -> None:
    curve = {1.0: 10.0, 0.75: 8.0, 0.5: 9.5, 0.25: 4.0, 0.1: 2.0, 0.0: 0.0}
    assert not approximate_monotonic_decrease(curve)
    result = compute_tested_thresholds(curve)

    assert result["lambda_80"] is None
    assert result["lambda_50"] is None
