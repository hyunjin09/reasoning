"""Statistical primitives for base-level Stage 3B.9 analysis."""

from __future__ import annotations

import math

import numpy as np


def base_balanced_boolean_fraction(rows: list[dict], *, field: str) -> dict:
    """Average a boolean fold metric within bases, then equally across bases."""

    by_base: dict[str, list[bool]] = {}
    for row in rows:
        by_base.setdefault(str(row["base_problem_id"]), []).append(bool(row[field]))
    per_base = {
        base: float(np.mean(values))
        for base, values in sorted(by_base.items())
    }
    return {
        "per_base": per_base,
        "across_base_mean": float(np.mean(list(per_base.values()))) if per_base else 0.0,
    }


def unclipped_ratio(numerator: float, denominator: float) -> float | None:
    numerator = float(numerator)
    denominator = float(denominator)
    if not math.isfinite(numerator) or not math.isfinite(denominator) or denominator == 0.0:
        return None
    return numerator / denominator


def bootstrap_interval(
    values: np.ndarray | list[float],
    *,
    statistic: str,
    resamples: int = 10_000,
    seed: int = 3_909,
) -> tuple[float, float]:
    array = np.asarray(values, dtype=np.float64)
    array = array[np.isfinite(array)]
    if array.size == 0:
        return (float("nan"), float("nan"))
    if statistic not in {"median", "mean"}:
        raise ValueError("statistic must be median or mean")
    generator = np.random.default_rng(int(seed))
    draws = generator.choice(array, size=(int(resamples), array.size), replace=True)
    sampled = np.median(draws, axis=1) if statistic == "median" else np.mean(draws, axis=1)
    low, high = np.quantile(sampled, [0.025, 0.975])
    return float(low), float(high)


def summarize(values: list[float], *, seed: int = 3_909) -> dict:
    array = np.asarray(values, dtype=np.float64)
    array = array[np.isfinite(array)]
    return {
        "count": int(array.size),
        "median": float(np.median(array)) if array.size else None,
        "mean": float(np.mean(array)) if array.size else None,
        "median_bootstrap_95ci": list(bootstrap_interval(array, statistic="median", seed=seed)) if array.size else [None, None],
        "mean_bootstrap_95ci": list(bootstrap_interval(array, statistic="mean", seed=seed)) if array.size else [None, None],
    }


__all__ = [
    "base_balanced_boolean_fraction",
    "bootstrap_interval",
    "summarize",
    "unclipped_ratio",
]
