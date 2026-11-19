from __future__ import annotations

import pytest

from scripts.stage3c6.analyze_phase_a import broad_outcome
from visual_reasoning.stage3c4.analysis import signed_summary
from visual_reasoning.stage3c6.protocol import (
    aligned_evidence_score,
    rescue_effect,
    select_candidate_region,
    threshold_crossings,
)


def test_counterfactual_condition_is_sign_aligned_before_rescue_metrics() -> None:
    assert aligned_evidence_score(3.0, "O") == 3.0
    assert aligned_evidence_score(-3.0, "C") == 3.0
    effect = rescue_effect(native_d=-4.0, suppressed_d=-2.0, rescued_d=-3.5, condition="C")
    assert effect["aligned_native"] == pytest.approx(4.0)
    assert effect["aligned_suppressed"] == pytest.approx(2.0)
    assert effect["suppression_loss"] == pytest.approx(2.0)
    assert effect["rescue_gain"] == pytest.approx(1.5)
    assert effect["rescue_ratio"] == pytest.approx(0.75)


def test_rescue_ratio_is_not_clipped() -> None:
    effect = rescue_effect(native_d=4.0, suppressed_d=2.0, rescued_d=5.0, condition="O")
    assert effect["rescue_ratio"] == pytest.approx(1.5)
    assert effect["rescue_ratio_is_clipped"] is False


def test_thresholds_require_all_robustness_conditions() -> None:
    rows = [
        {"layer": 0, "median_RR": 0.30, "gain_bootstrap_mean_ci95": [-0.01, 0.4], "positive_count": 20, "N": 24, "holm_adjusted_p": 0.01},
        {"layer": 1, "median_RR": 0.25, "gain_bootstrap_mean_ci95": [0.01, 0.4], "positive_count": 17, "N": 24, "holm_adjusted_p": 0.01},
        {"layer": 2, "median_RR": 0.55, "gain_bootstrap_mean_ci95": [0.02, 0.5], "positive_count": 18, "N": 24, "holm_adjusted_p": 0.01},
        {"layer": 3, "median_RR": 0.85, "gain_bootstrap_mean_ci95": [0.03, 0.6], "positive_count": 20, "N": 24, "holm_adjusted_p": 0.01},
    ]
    result = threshold_crossings(rows)
    assert result == {"first_20": 2, "first_50": 2, "first_80": 3}


def test_candidate_region_uses_largest_positive_slope_in_valid_four_layer_window() -> None:
    rows = [
        {"layer": index, "median_gain": value, "holm_adjusted_p": p}
        for index, (value, p) in enumerate(
            [(0.0, 1.0), (0.1, 0.01), (0.2, 0.01), (0.25, 0.01), (0.9, 0.01), (1.0, 0.01)]
        )
    ]
    selected = select_candidate_region(rows, layer_count=6, window_size=4)
    assert selected is not None
    assert selected["layers"] == [1, 2, 3, 4]
    assert selected["largest_positive_slope"] == pytest.approx(0.65)
    assert selected["slope_transition"] == [3, 4]


def test_candidate_region_is_absent_without_adjacent_significant_layers() -> None:
    rows = [
        {"layer": index, "median_gain": float(index), "holm_adjusted_p": 0.01 if index in {1, 3} else 1.0}
        for index in range(6)
    ]
    assert select_candidate_region(rows, layer_count=6, window_size=4) is None


def test_transient_outcome_requires_a_robust_peak() -> None:
    rows = [
        {
            "layer": layer,
            "median_RR": 0.6 if layer == 10 else 0.1,
            "robust_positive": False,
        }
        for layer in range(36)
    ]
    assert broad_outcome(rows, {"first_20": None}) == "R5_no_substantial_residual_rescue"
    rows[10]["robust_positive"] = True
    assert broad_outcome(rows, {"first_20": 10}) == "R4_transient_rescue_decay"


def test_all_zero_signed_effect_is_null_evidence() -> None:
    summary = signed_summary([0.0] * 24)
    assert summary["wilcoxon_one_sided_greater_p"] == 1.0
    assert summary["positive_count"] == 0
