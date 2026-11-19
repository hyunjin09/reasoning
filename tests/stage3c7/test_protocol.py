from __future__ import annotations

import pytest

from visual_reasoning.stage3c7.protocol import (
    joint_outcome,
    recommendation_for_outcome,
    rescue_effect,
    robust_effect,
)


def test_rescue_effect_sign_aligns_counterfactual_condition_and_does_not_clip() -> None:
    row = rescue_effect(native_d=-4.0, suppressed_d=-2.0, rescued_d=-5.0, condition="C")
    assert row["suppression_loss"] == pytest.approx(2.0)
    assert row["rescue_gain"] == pytest.approx(3.0)
    assert row["rescue_ratio"] == pytest.approx(1.5)
    assert row["rescue_ratio_is_clipped"] is False


def test_robust_effect_requires_holm_ci_and_three_quarters_positive() -> None:
    passing = {"holm_adjusted_p": 0.01, "gain_bootstrap_mean_ci95": [0.01, 1.0], "positive_count": 18, "N": 24}
    assert robust_effect(passing) is True
    assert robust_effect({**passing, "positive_count": 17}) is False
    assert robust_effect({**passing, "gain_bootstrap_mean_ci95": [0.0, 1.0]}) is False
    assert robust_effect({**passing, "holm_adjusted_p": 0.05}) is False


def test_joint_outcome_uses_frozen_priority_order() -> None:
    robust = {"robust_positive": True}
    assert joint_outcome(
        full_cache={**robust, "median_RR": 0.6}, residual={**robust, "median_RR": 0.3},
        downstream_cache={**robust, "median_RR": 0.3}, joint={**robust, "median_RR": 0.85},
        joint_over_residual=robust, joint_over_cache=robust,
    ) == "O3_two_query_synergy"
    assert joint_outcome(
        full_cache={**robust, "median_RR": 0.6}, residual={**robust, "median_RR": 0.3},
        downstream_cache={**robust, "median_RR": 0.3}, joint={**robust, "median_RR": 0.65},
        joint_over_residual=robust, joint_over_cache=robust,
    ) == "O2_residual_cache_complementarity"
    assert joint_outcome(
        full_cache={**robust, "median_RR": 0.6}, residual={**robust, "median_RR": 0.6},
        downstream_cache={**robust, "median_RR": 0.05}, joint={**robust, "median_RR": 0.61},
        joint_over_residual={"robust_positive": False}, joint_over_cache=robust,
    ) == "O4_residual_dominant"


def test_recommendation_is_one_of_frozen_review_only_directions() -> None:
    assert recommendation_for_outcome("O1_prior_cache_carrier", joint_near_complete=False, cache_nonzero=True) == "GO — Token-Type Carrier Atlas"
    assert recommendation_for_outcome("O2_residual_cache_complementarity", joint_near_complete=False, cache_nonzero=True) == "GO — Broader Recent-Cache Interaction"
    assert recommendation_for_outcome("O4_residual_dominant", joint_near_complete=False, cache_nonzero=False) == "GO — Residual Feature Mechanism"

