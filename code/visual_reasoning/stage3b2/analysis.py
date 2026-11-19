"""Deterministic Stage 3B.2 retrieval-timing analysis."""

from __future__ import annotations

from typing import Any, Literal, Sequence

import numpy as np


def bootstrap_interval(
    values: Sequence[float],
    *,
    statistic: Literal["mean", "median"],
    resamples: int = 10_000,
    seed: int = 1_234,
) -> tuple[float, float]:
    array = np.asarray([float(value) for value in values], dtype=np.float64)
    if array.size == 0 or not np.isfinite(array).all():
        raise ValueError("Bootstrap values must be nonempty and finite")
    if statistic not in {"mean", "median"}:
        raise ValueError(f"Unsupported bootstrap statistic: {statistic}")
    generator = np.random.default_rng(int(seed))
    samples = generator.choice(array, size=(int(resamples), array.size), replace=True)
    estimates = samples.mean(axis=1) if statistic == "mean" else np.median(samples, axis=1)
    low, high = np.quantile(estimates, [0.025, 0.975])
    return float(low), float(high)


def retrieval_category(curve: Sequence[dict]) -> str:
    rows = sorted(curve, key=lambda row: int(row["switch_generated_index"]))
    finite_rows = [row for row in rows if row.get("normalized_BRI_raw") is not None]
    values = [float(row["normalized_BRI_raw"]) for row in finite_rows]
    sign_values = [1 if value > 0 else -1 if value < 0 else 0 for value in values]
    nonzero_signs = [value for value in sign_values if value]
    sign_changes = sum(left != right for left, right in zip(nonzero_signs, nonzero_signs[1:]))
    maximum_step = max(
        (abs(right - left) for left, right in zip(values, values[1:])),
        default=0.0,
    )
    if sign_changes >= 2 or maximum_step > 0.50:
        return "R5_complex_nonmonotonic"

    late = [
        row
        for row in finite_rows
        if "Ed_minus_1" in row.get("labels", []) or "Ed" in row.get("labels", [])
    ]
    if any(
        float(row["normalized_BRI_raw"]) >= 0.50
        and bool(row["bidirectionally_source_consistent"])
        for row in late
    ):
        return "R1_persistent_late_retrieval"

    early = [row for row in finite_rows if int(row.get("tokens_before_ed", 0)) >= 16]
    if early and late:
        early_max = max(float(row["normalized_BRI_raw"]) for row in early)
        late_max = max(float(row["normalized_BRI_raw"]) for row in late)
        if early_max >= 0.50 and late_max < 0.25:
            return "R2_early_retrieval_commitment"

    if values and max(abs(value) for value in values) < 0.25:
        return "R4_weak_identity_specific_retrieval"
    return "R3_gradual_source_influence"


def match_switch_and_cutoff_timings(
    switch_curve: Sequence[dict[str, Any]],
    cutoff_curve: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Join Stage 3B.2 and Stage 3B.1 rows only at identical query indices."""

    cutoff_by_index = {
        int(row["cutoff_generated_index"]): row for row in cutoff_curve
    }
    return [
        {
            "generated_index": int(row["switch_generated_index"]),
            "switch": row,
            "cutoff": cutoff_by_index[int(row["switch_generated_index"])],
        }
        for row in switch_curve
        if int(row["switch_generated_index"]) in cutoff_by_index
    ]


def checkpoint_passes_go_rule(summary: dict[str, Any]) -> bool:
    """Evaluate one checkpoint against the frozen late/early GO criteria."""

    median_ci = summary["BRI"]["median_bootstrap_ci"]
    target_magnitude = float(summary["median_absolute_S_O_to_C"])
    sham_magnitude = float(summary["median_absolute_sham"])
    return bool(
        float(median_ci["ci_low"]) > 0.0
        and float(summary["bidirectional_source_consistency"]["proportion"]) >= 0.70
        and float(summary["normalized_BRI_raw"]["median"]) >= 0.50
        and target_magnitude > 0.0
        and sham_magnitude < 0.20 * target_magnitude
        and bool(summary["all_self_switches_exact"])
    )
