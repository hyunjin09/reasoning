"""Prospectively gated Stage 3B.8 dose-response summaries."""

from __future__ import annotations

import statistics
from collections import defaultdict
from collections.abc import Sequence
from typing import Any

import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import spearmanr


def _bootstrap_median(values: Sequence[float], *, iterations: int, seed: int) -> list[float]:
    array = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(seed)
    samples = np.median(
        array[rng.integers(0, len(array), size=(int(iterations), len(array)))], axis=1
    )
    return [float(value) for value in np.quantile(samples, [0.025, 0.975])]


def _r2(observed: np.ndarray, predicted: np.ndarray) -> float | None:
    denominator = float(np.square(observed - observed.mean()).sum())
    if denominator == 0.0:
        return None
    return float(1.0 - np.square(observed - predicted).sum() / denominator)


def summarize_dose_target(
    rows: Sequence[dict[str, Any]],
    *,
    lambdas: Sequence[float],
    bootstrap_iterations: int,
    seed: int,
    median_drop_tolerance: float,
    median_within_base_spearman_minimum: float,
) -> dict[str, Any]:
    """Summarize one frozen target and apply the prospective Phase-A gate."""

    expected = [float(value) for value in lambdas]
    by_lambda: dict[float, list[dict[str, Any]]] = defaultdict(list)
    by_base: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        dose = float(row["lambda"])
        by_lambda[dose].append(row)
        by_base[str(row["base_problem_id"])].append(row)
    if sorted(by_lambda) != sorted(expected):
        raise ValueError("Dose rows do not contain the exact frozen lambda grid")
    if any(sorted(float(row["lambda"]) for row in base_rows) != sorted(expected) for base_rows in by_base.values()):
        raise ValueError("Every base must contain the complete lambda grid")
    lambda_summaries = []
    for index, dose in enumerate(expected):
        dose_rows = by_lambda[dose]
        effects = [float(row["BVR"]) for row in dose_rows]
        shams = [float(row["sham_effect"]) for row in dose_rows]
        lambda_summaries.append({
            "lambda": dose,
            "base_count": len(dose_rows),
            "mean_BVR": float(statistics.fmean(effects)),
            "median_BVR": float(statistics.median(effects)),
            "median_BVR_bootstrap_95_CI": _bootstrap_median(
                effects, iterations=bootstrap_iterations, seed=seed + index
            ),
            "bidirectional_fraction": float(np.mean([
                bool(row["bidirectionally_source_consistent"]) for row in dose_rows
            ])),
            "mean_sham_effect": float(statistics.fmean(shams)),
            "median_sham_effect": float(statistics.median(shams)),
        })
    medians = np.asarray([row["median_BVR"] for row in lambda_summaries], dtype=np.float64)
    dose_array = np.asarray(expected, dtype=np.float64)
    cohort_monotonic = bool(
        np.all(np.diff(medians) >= -abs(float(median_drop_tolerance)))
    )
    within_base = []
    for base, base_rows in sorted(by_base.items(), key=lambda item: int(item[0])):
        ordered = sorted(base_rows, key=lambda row: float(row["lambda"]))
        statistic = float(spearmanr(expected, [float(row["BVR"]) for row in ordered]).statistic)
        within_base.append({"base_problem_id": base, "spearman_rho": statistic})
    finite_rhos = [row["spearman_rho"] for row in within_base if np.isfinite(row["spearman_rho"])]
    median_rho = float(statistics.median(finite_rhos)) if finite_rhos else float("nan")
    linear_coefficients = np.polyfit(dose_array, medians, deg=1)
    linear_predicted = np.polyval(linear_coefficients, dose_array)
    saturating = {"fit_succeeded": False, "amplitude": None, "rate": None, "r2": None}
    try:
        parameters, _ = curve_fit(
            lambda value, amplitude, rate: amplitude * (1.0 - np.exp(-rate * value)),
            dose_array,
            medians,
            p0=[float(medians[-1]) if medians[-1] else 1.0, 1.0],
            maxfev=10_000,
        )
        predicted = parameters[0] * (1.0 - np.exp(-parameters[1] * dose_array))
        saturating = {
            "fit_succeeded": True,
            "amplitude": float(parameters[0]),
            "rate": float(parameters[1]),
            "r2": _r2(medians, predicted),
        }
    except (RuntimeError, ValueError, FloatingPointError):
        pass
    native_rows = by_lambda[0.0]
    full_rows = by_lambda[1.0]
    native_exact = all(row.get("native_endpoint_exact") is True for row in native_rows)
    reference_values = [row.get("reference_endpoint_within_tolerance") for row in full_rows]
    reference_exact = all(value is True for value in reference_values) if any(value is not None for value in reference_values) else True
    all_mechanical = all(bool(row["mechanical_pass"]) for row in rows)
    full_median = float(lambda_summaries[-1]["median_BVR"])
    full_sham = float(lambda_summaries[-1]["median_sham_effect"])
    gate = bool(
        native_exact
        and reference_exact
        and all_mechanical
        and cohort_monotonic
        and np.isfinite(median_rho)
        and median_rho >= float(median_within_base_spearman_minimum)
        and full_median > 0.0
        and full_median > full_sham
    )
    return {
        "base_count": len(by_base),
        "lambda_summaries": lambda_summaries,
        "cohort_median_monotonic": cohort_monotonic,
        "median_drop_tolerance": float(median_drop_tolerance),
        "within_base_spearman": within_base,
        "median_within_base_spearman": median_rho,
        "minimum_median_within_base_spearman": float(median_within_base_spearman_minimum),
        "linear_fit": {
            "intercept": float(linear_coefficients[1]),
            "slope": float(linear_coefficients[0]),
            "r2": _r2(medians, linear_predicted),
        },
        "saturating_fit": saturating,
        "native_endpoint_exact": native_exact,
        "stage3b7r_full_endpoint_within_tolerance": reference_exact,
        "all_mechanical_checks_passed": all_mechanical,
        "lambda_1_median_BVR_positive": full_median > 0.0,
        "lambda_1_median_BVR_exceeds_sham": full_median > full_sham,
        "dose_response_gate_passed": gate,
    }


__all__ = ["summarize_dose_target"]
