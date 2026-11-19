from __future__ import annotations

import pytest

from visual_reasoning.a6000_calibration.metrics import (
    acceptance_checklist,
    compare_scores,
    continuity_statistics,
    validate_calibration_cohort,
)


def score(d: float, left: list[float], right: list[float]) -> dict:
    return {
        "D": d,
        "original_candidate": {"token_log_probabilities": left},
        "counterfactual_candidate": {"token_log_probabilities": right},
    }


def test_compare_scores_reports_token_and_aggregate_maxima() -> None:
    comparison = compare_scores(
        score(0.25, [-1.0, -2.0], [-1.5]),
        score(0.250004, [-1.0, -1.999997], [-1.500002]),
        tolerance=1e-5,
    )
    assert comparison["passed"] is True
    assert comparison["aggregate_D_max_abs_delta"] == pytest.approx(4e-6)
    assert comparison["token_log_probability_max_abs_delta"] == pytest.approx(3e-6)


def test_compare_scores_rejects_mismatched_candidate_lengths() -> None:
    with pytest.raises(ValueError, match="candidate token lengths"):
        compare_scores(
            score(0.0, [-1.0], [-2.0]),
            score(0.0, [-1.0, -1.5], [-2.0]),
            tolerance=1e-5,
        )


def test_validate_calibration_cohort_enforces_frozen_composition() -> None:
    cells = [
        *({"base_problem_id": f"s{i}", "effect_stratum": "strong"} for i in range(4)),
        *({"base_problem_id": f"m{i}", "effect_stratum": "medium"} for i in range(4)),
        *(
            {
                "base_problem_id": f"a{i}",
                "effect_stratum": "threshold_adjacent_or_small",
                "long_prefix_stress": i < 3,
            }
            for i in range(4)
        ),
    ]
    for cell in cells[:8]:
        cell["long_prefix_stress"] = False
    audit = validate_calibration_cohort({"cells": cells})
    assert audit["passed"] is True
    assert audit["unique_base_count"] == 12


def test_continuity_statistics_treats_small_cells_as_sensitivity_only() -> None:
    rows = [
        {"stratum": "strong", "a5000": 1.0, "a6000": 0.9},
        {"stratum": "medium", "a5000": 0.4, "a6000": 0.3},
        {"stratum": "threshold_adjacent_or_small", "a5000": 0.04, "a6000": -0.01},
    ]
    result = continuity_statistics(rows, hardware_sensitive_band=0.25)
    assert result["strong_medium_direction_agreement"] == 1.0
    assert result["threshold_adjacent_direction_agreement"] == 0.0
    assert result["hardware_sensitive_count"] == 1


def test_acceptance_checklist_has_exactly_twenty_named_criteria() -> None:
    evidence = {str(index): True for index in range(1, 21)}
    result = acceptance_checklist(evidence)
    assert result["criterion_count"] == 20
    assert result["passed_count"] == 20
    assert result["overall_passed"] is True
    assert [row["criterion_id"] for row in result["criteria"]] == list(range(1, 21))


def test_acceptance_checklist_rejects_missing_criterion() -> None:
    with pytest.raises(ValueError, match="exactly criteria 1 through 20"):
        acceptance_checklist({str(index): True for index in range(1, 20)})

