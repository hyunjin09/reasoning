"""Statistical helpers for Stage 3C.3-R."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np
from scipy.stats import wilcoxon


def bootstrap_summary(
    values: Sequence[float], *, seed: int = 20260904, resamples: int = 10_000
) -> dict[str, Any]:
    data = np.asarray(values, dtype=np.float64)
    if data.ndim != 1 or data.size == 0 or not np.isfinite(data).all():
        raise ValueError("Summary values must be a nonempty finite vector")
    rng = np.random.default_rng(int(seed))
    sampled = data[rng.integers(0, data.size, size=(int(resamples), data.size))].mean(axis=1)
    try:
        p_value = float(wilcoxon(data, alternative="greater").pvalue)
    except ValueError:
        p_value = 1.0
    return {
        "N": int(data.size),
        "mean": float(data.mean()),
        "median": float(np.median(data)),
        "bootstrap_mean_ci95": [float(value) for value in np.quantile(sampled, [0.025, 0.975])],
        "positive_count": int(np.sum(data > 0)),
        "positive_fraction": float(np.mean(data > 0)),
        "wilcoxon_one_sided_greater_p": p_value,
    }


def holm_adjust(p_values: Sequence[float]) -> list[float]:
    values = [float(value) for value in p_values]
    if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in values):
        raise ValueError("p-values must be finite and in [0,1]")
    order = sorted(range(len(values)), key=values.__getitem__)
    adjusted = [1.0] * len(values)
    running = 0.0
    total = len(values)
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (total - rank) * values[index]))
        adjusted[index] = running
    return adjusted


def query_operating_point(native: Sequence[float], patched: Sequence[float]) -> dict[str, float]:
    native_array = np.asarray(native, dtype=np.float64)
    patched_array = np.asarray(patched, dtype=np.float64)
    if native_array.shape != patched_array.shape or native_array.ndim != 1:
        raise ValueError("Native and patched contribution vectors must have equal flat shape")
    denominator = float(np.dot(native_array, native_array))
    if denominator <= 0.0 or not np.isfinite(native_array).all() or not np.isfinite(patched_array).all():
        raise ValueError("Native contribution vector must have finite nonzero norm")
    return {
        "lambda_query_norm": float(np.linalg.norm(patched_array) / np.linalg.norm(native_array)),
        "lambda_query_proj": float(np.dot(patched_array, native_array) / denominator),
        "native_norm": float(np.linalg.norm(native_array)),
        "patched_norm": float(np.linalg.norm(patched_array)),
        "cosine": float(
            np.dot(patched_array, native_array)
            / (np.linalg.norm(patched_array) * np.linalg.norm(native_array))
        ) if np.linalg.norm(patched_array) > 0 else 0.0,
    }


__all__ = ["bootstrap_summary", "holm_adjust", "query_operating_point"]
