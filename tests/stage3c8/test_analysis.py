from __future__ import annotations

from visual_reasoning.stage3c8.analysis import (
    holm_adjust,
    inferential_summary,
    recency_matched_pairs,
    robust_positive,
    summarize_effect,
)


def test_recency_matching_stays_within_base_and_uses_nearest_other_class() -> None:
    rows = [
        {"base_problem_id": "1", "position": 8, "distance": 2, "token_class": "VISUAL_ENTITY", "gain": 0.5},
        {"base_problem_id": "1", "position": 7, "distance": 3, "token_class": "FUNCTION_WORD", "gain": 0.1},
        {"base_problem_id": "1", "position": 2, "distance": 8, "token_class": "PUNCTUATION", "gain": 0.2},
        {"base_problem_id": "2", "position": 8, "distance": 2, "token_class": "VISUAL_ENTITY", "gain": 0.4},
        {"base_problem_id": "2", "position": 6, "distance": 4, "token_class": "FUNCTION_WORD", "gain": 0.2},
    ]
    pairs = recency_matched_pairs(rows, focal_class="VISUAL_ENTITY")
    assert [(row["base_problem_id"], row["control_class"]) for row in pairs] == [
        ("1", "FUNCTION_WORD"), ("2", "FUNCTION_WORD")
    ]
    assert [row["gain_difference"] for row in pairs] == [0.4, 0.2]


def test_effect_summary_uses_base_as_unit_and_reports_positive_fraction() -> None:
    result = summarize_effect({"1": 1.0, "2": 2.0, "3": -1.0, "4": 3.0}, bootstrap_samples=200, seed=4)
    assert result["N_unique_bases"] == 4
    assert result["positive_count"] == 3
    assert result["positive_fraction"] == 0.75
    assert result["median"] == 1.5


def test_holm_adjust_is_monotone_in_sorted_p_values() -> None:
    adjusted = holm_adjust([0.01, 0.04, 0.02])
    assert adjusted == [0.03, 0.04, 0.04]


def test_robust_positive_requires_all_frozen_criteria() -> None:
    assert robust_positive({"holm_p": 0.01, "bootstrap_mean_ci95": [0.2, 0.8], "positive_fraction": 0.8})
    assert not robust_positive({"holm_p": 0.01, "bootstrap_mean_ci95": [-0.1, 0.8], "positive_fraction": 0.8})


def test_inferential_summary_retains_unique_base_count_and_two_sided_test() -> None:
    result = inferential_summary({str(index): float(index) for index in range(1, 13)}, bootstrap_samples=100, seed=1)
    assert result["N_unique_bases"] == 12
    assert result["wilcoxon_alternative"] == "two-sided"
    assert 0.0 <= result["wilcoxon_p"] <= 1.0
