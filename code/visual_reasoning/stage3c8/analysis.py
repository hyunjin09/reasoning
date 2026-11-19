"""Base-level descriptive and inferential helpers for Stage 3C.8."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
from scipy.stats import wilcoxon


def holm_adjust(p_values: Sequence[float]) -> list[float]:
    """Return Holm family-wise adjusted p values in original order."""

    values = [float(value) for value in p_values]
    order = sorted(range(len(values)), key=values.__getitem__)
    adjusted = [1.0] * len(values)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(values) - rank) * values[index]))
        adjusted[index] = round(running, 15)
    return adjusted


def robust_positive(summary: Mapping[str, Any]) -> bool:
    """Apply the prospectively frozen Stage 3C8 robust-positive rule."""

    interval = summary.get("bootstrap_mean_ci95", [None, None])
    return bool(
        summary.get("holm_p") is not None
        and float(summary["holm_p"]) < 0.05
        and interval[0] is not None
        and float(interval[0]) > 0.0
        and summary.get("positive_fraction") is not None
        and float(summary["positive_fraction"]) >= 0.75
    )


def recency_matched_pairs(
    rows: Sequence[Mapping[str, Any]], *, focal_class: str,
) -> list[dict[str, Any]]:
    """Pair each focal position to the nearest other-class position within base."""

    by_base: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        by_base[str(row["base_problem_id"])].append(row)
    output = []
    for base in sorted(by_base, key=lambda value: int(value)):
        base_rows = by_base[base]
        focal = [row for row in base_rows if str(row["token_class"]) == focal_class]
        controls = [row for row in base_rows if str(row["token_class"]) != focal_class]
        for row in focal:
            if not controls:
                continue
            control = min(
                controls,
                key=lambda item: (
                    abs(int(item["distance"]) - int(row["distance"])),
                    abs(int(item["position"]) - int(row["position"])),
                    int(item["position"]),
                ),
            )
            output.append({
                "base_problem_id": base,
                "focal_class": focal_class,
                "focal_position": int(row["position"]),
                "focal_distance": int(row["distance"]),
                "focal_gain": float(row["gain"]),
                "control_class": str(control["token_class"]),
                "control_position": int(control["position"]),
                "control_distance": int(control["distance"]),
                "control_gain": float(control["gain"]),
                "gain_difference": float(row["gain"]) - float(control["gain"]),
            })
    return output


def summarize_effect(
    values_by_base: Mapping[str, float], *, bootstrap_samples: int = 10_000, seed: int = 12_348,
) -> dict[str, Any]:
    values = np.asarray([float(values_by_base[base]) for base in sorted(values_by_base, key=lambda value: int(value))], dtype=np.float64)
    if values.size == 0:
        return {"N_unique_bases": 0, "mean": None, "median": None, "positive_count": 0, "positive_fraction": None, "bootstrap_mean_ci95": [None, None]}
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, values.size, size=(int(bootstrap_samples), values.size))
    means = values[indices].mean(axis=1)
    return {
        "N_unique_bases": int(values.size),
        "mean": float(values.mean()),
        "median": float(np.median(values)),
        "positive_count": int(np.count_nonzero(values > 0)),
        "positive_fraction": float(np.mean(values > 0)),
        "bootstrap_mean_ci95": [float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))],
    }


def inferential_summary(
    values_by_base: Mapping[str, float], *, bootstrap_samples: int = 10_000, seed: int = 12_348,
) -> dict[str, Any]:
    """Summarize independent bases and apply the frozen two-sided signed-rank test."""

    result = summarize_effect(values_by_base, bootstrap_samples=bootstrap_samples, seed=seed)
    values = np.asarray([float(values_by_base[base]) for base in sorted(values_by_base, key=lambda value: int(value))], dtype=np.float64)
    if not values.size or np.all(values == 0):
        p_value = 1.0
    else:
        p_value = float(wilcoxon(values, alternative="two-sided").pvalue)
    result.update({"wilcoxon_p": p_value, "wilcoxon_alternative": "two-sided"})
    return result
