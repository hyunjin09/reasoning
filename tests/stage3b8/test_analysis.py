import pytest

from visual_reasoning.stage3b8.analysis import summarize_dose_target


def test_summarize_dose_target_passes_clean_monotonic_series() -> None:
    rows = [
        {
            "base_problem_id": str(base),
            "lambda": dose,
            "BVR": dose * (1.0 + 0.1 * base),
            "BVR_O": dose,
            "BVR_C": dose,
            "sham_effect": 0.01 * dose,
            "bidirectionally_source_consistent": dose > 0,
            "native_endpoint_exact": True if dose == 0 else None,
            "reference_endpoint_within_tolerance": True if dose == 1 else None,
            "mechanical_pass": True,
        }
        for base in range(4)
        for dose in (0.0, 0.25, 0.5, 0.75, 1.0)
    ]
    summary = summarize_dose_target(
        rows,
        lambdas=[0.0, 0.25, 0.5, 0.75, 1.0],
        bootstrap_iterations=200,
        seed=1234,
        median_drop_tolerance=0.05,
        median_within_base_spearman_minimum=0.5,
    )
    assert summary["dose_response_gate_passed"] is True
    assert summary["cohort_median_monotonic"] is True
    assert summary["median_within_base_spearman"] == pytest.approx(1.0)
