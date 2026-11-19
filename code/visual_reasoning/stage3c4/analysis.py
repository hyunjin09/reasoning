"""Base-level statistics for Stage 3C.4."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np
from scipy.stats import wilcoxon


def holm_adjust(p_values: Sequence[float]) -> list[float]:
    values = [float(value) for value in p_values]
    if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in values):
        raise ValueError("p-values must be finite and in [0,1]")
    order = sorted(range(len(values)), key=values.__getitem__)
    adjusted = [1.0] * len(values)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(values) - rank) * values[index]))
        adjusted[index] = running
    return adjusted


def _bootstrap_mean(
    values: np.ndarray, *, seed: int, resamples: int
) -> list[float]:
    rng = np.random.default_rng(int(seed))
    sampled = values[rng.integers(0, values.size, size=(int(resamples), values.size))].mean(axis=1)
    return [float(value) for value in np.quantile(sampled, [0.025, 0.975])]


def signed_summary(
    values: Sequence[float], *, seed: int = 20260904, resamples: int = 10_000
) -> dict[str, Any]:
    data = np.asarray(values, dtype=np.float64)
    if data.ndim != 1 or data.size == 0 or not np.isfinite(data).all():
        raise ValueError("Values must be a nonempty finite vector")
    if np.all(data == 0.0):
        p_value = 1.0
    else:
        try:
            p_value = float(wilcoxon(data, alternative="greater").pvalue)
        except ValueError:
            p_value = 1.0
        if not math.isfinite(p_value):
            p_value = 1.0
    return {
        "N": int(data.size),
        "mean": float(data.mean()),
        "median": float(np.median(data)),
        "bootstrap_mean_ci95": _bootstrap_mean(data, seed=seed, resamples=resamples),
        "positive_count": int(np.sum(data > 0)),
        "positive_fraction": float(np.mean(data > 0)),
        "wilcoxon_one_sided_greater_p": p_value,
    }


def retention_summary(
    native: Sequence[float],
    suppressed: Sequence[float],
    *,
    seed: int = 20260904,
    resamples: int = 10_000,
) -> dict[str, Any]:
    native_array = np.asarray(native, dtype=np.float64)
    suppressed_array = np.asarray(suppressed, dtype=np.float64)
    if (
        native_array.ndim != 1
        or native_array.size == 0
        or native_array.shape != suppressed_array.shape
        or not np.isfinite(native_array).all()
        or not np.isfinite(suppressed_array).all()
        or np.any(native_array == 0.0)
    ):
        raise ValueError("Native/suppressed evidence must be equal nonempty finite vectors with nonzero native values")
    loss = native_array - suppressed_array
    retained = suppressed_array / native_array
    return {
        "N": int(native_array.size),
        "primary_readout": "unnormalized evidence loss D_native - D_suppressed",
        "unnormalized_loss": loss.tolist(),
        "loss_summary": signed_summary(loss, seed=seed, resamples=resamples),
        "retained_evidence": retained.tolist(),
        "retained_evidence_is_clipped": False,
        "retained_mean": float(retained.mean()),
        "retained_median": float(np.median(retained)),
        "retained_bootstrap_mean_ci95": _bootstrap_mean(retained, seed=seed + 1, resamples=resamples),
        "fraction_retaining_at_least_0_80": float(np.mean(retained >= 0.80)),
        "fraction_retaining_at_least_0_50": float(np.mean(retained >= 0.50)),
    }


def tested_window_threshold(curve: dict[str, float], *, threshold: float) -> str | None:
    for label in ("T0", "T1", "T2", "T4", "T8", "T16"):
        if label in curve and float(curve[label]) < float(threshold):
            return label
    return None


__all__ = ["holm_adjust", "retention_summary", "signed_summary", "tested_window_threshold"]
