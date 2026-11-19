"""Pure CPU helpers for Stage 2A paired descriptive analysis."""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np
from scipy.stats import rankdata, wilcoxon


def normalized_token_bins(values: np.ndarray, bin_count: int = 20) -> np.ndarray:
    """Average a token-aligned array into equal normalized-progress bins."""

    array = np.asarray(values, dtype=np.float64)
    if array.ndim == 0:
        raise ValueError("values must have a token dimension")
    if array.shape[0] < bin_count:
        raise ValueError(f"need at least {bin_count} tokens, found {array.shape[0]}")
    if bin_count <= 0:
        raise ValueError("bin_count must be positive")
    edges = np.linspace(0, array.shape[0], bin_count + 1, dtype=np.int64)
    return np.stack([array[edges[index] : edges[index + 1]].mean(axis=0) for index in range(bin_count)])


def progress_window_mean(values: np.ndarray, start: float, end: float) -> np.ndarray:
    """Average token values whose normalized positions lie in [start, end)."""

    array = np.asarray(values, dtype=np.float64)
    if not 0.0 <= start < end <= 1.0:
        raise ValueError("progress bounds must satisfy 0 <= start < end <= 1")
    count = array.shape[0]
    left = min(count - 1, int(math.floor(start * count)))
    right = count if end == 1.0 else max(left + 1, int(math.floor(end * count)))
    return array[left:right].mean(axis=0)


def bootstrap_mean_ci(
    differences: Iterable[float],
    *,
    samples: int = 10_000,
    seed: int = 20260826,
) -> list[float] | None:
    values = np.asarray(list(differences), dtype=np.float64)
    if not values.size:
        return None
    rng = np.random.default_rng(seed)
    draws = rng.choice(values, size=(samples, values.size), replace=True).mean(axis=1)
    return [float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))]


def bootstrap_median_ci(
    differences: Iterable[float],
    *,
    samples: int = 10_000,
    seed: int = 20260826,
) -> list[float] | None:
    values = np.asarray(list(differences), dtype=np.float64)
    if not values.size:
        return None
    rng = np.random.default_rng(seed)
    draws = np.median(rng.choice(values, size=(samples, values.size), replace=True), axis=1)
    return [float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))]


def paired_effect(left: Iterable[float], right: Iterable[float]) -> dict[str, object]:
    """Summarize paired right-minus-left differences.

    `left` is Vision Intensive and `right` is Vision Dominant throughout Stage
    2A, making every reported difference VD - VI.
    """

    vi = np.asarray(list(left), dtype=np.float64)
    vd = np.asarray(list(right), dtype=np.float64)
    if vi.shape != vd.shape or vi.ndim != 1:
        raise ValueError("paired inputs must be equal-length one-dimensional arrays")
    if not vi.size:
        raise ValueError("at least one pair is required")
    if not np.isfinite(vi).all() or not np.isfinite(vd).all():
        raise ValueError("paired inputs must be finite")
    diff = vd - vi
    standard_deviation = float(diff.std(ddof=1)) if diff.size > 1 else 0.0
    cohen_dz = float(diff.mean() / standard_deviation) if standard_deviation > 0 else None
    nonzero = diff[diff != 0]
    if nonzero.size:
        ranks = rankdata(np.abs(nonzero))
        positive = float(ranks[nonzero > 0].sum())
        negative = float(ranks[nonzero < 0].sum())
        rank_biserial = (positive - negative) / (positive + negative)
        test = wilcoxon(nonzero, zero_method="wilcox", alternative="two-sided", method="auto")
        statistic = float(test.statistic)
        p_value = float(test.pvalue)
    else:
        rank_biserial = 0.0
        statistic = 0.0
        p_value = 1.0
    return {
        "n_pairs": int(diff.size),
        "difference_definition": "Vision Dominant minus Vision Intensive",
        "vi_mean": float(vi.mean()),
        "vd_mean": float(vd.mean()),
        "paired_mean_difference": float(diff.mean()),
        "paired_median_difference": float(np.median(diff)),
        "paired_difference_bootstrap_mean_95ci": bootstrap_mean_ci(diff),
        "paired_difference_bootstrap_median_95ci": bootstrap_median_ci(diff),
        "cohen_dz": cohen_dz,
        "matched_rank_biserial": float(rank_biserial),
        "wilcoxon_statistic": statistic,
        "wilcoxon_p_value": p_value,
        "zero_difference_pairs": int((diff == 0).sum()),
        "differences": diff.tolist(),
    }


def holm_adjust(p_values: dict[str, float]) -> dict[str, float]:
    """Holm family-wise adjusted p-values keyed like the input."""

    ordered = sorted(p_values.items(), key=lambda item: item[1])
    count = len(ordered)
    adjusted: dict[str, float] = {}
    running = 0.0
    for rank, (name, value) in enumerate(ordered):
        candidate = min(1.0, float(value) * (count - rank))
        running = max(running, candidate)
        adjusted[name] = running
    return adjusted


def token_weighted_semantic_means(
    spans: list[dict[str, object]],
    token_values: np.ndarray,
) -> dict[str, np.ndarray]:
    """Aggregate token-aligned signals by saved coarse semantic label."""

    values = np.asarray(token_values, dtype=np.float64)
    by_label: dict[str, list[np.ndarray]] = {}
    for span in spans:
        start, end = int(span["start_token"]), int(span["end_token"])
        if not 0 <= start < end <= values.shape[0]:
            raise ValueError("span range is outside token values")
        by_label.setdefault(str(span["semantic_label"]), []).append(values[start:end])
    return {label: np.concatenate(rows, axis=0).mean(axis=0) for label, rows in by_label.items()}
