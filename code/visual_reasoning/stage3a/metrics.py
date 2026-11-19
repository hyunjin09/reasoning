"""Prospectively defined Stage 3A causal scoring metrics."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np


def counterfactual_effect(
    *,
    original: Mapping[str, float],
    counterfactual: Mapping[str, float],
    sham: Mapping[str, float],
) -> dict[str, float]:
    """Compute evidence preference and the sham-controlled image effect."""

    d_original = float(original["L_o"] - original["L_c"])
    d_counterfactual = float(counterfactual["L_o"] - counterfactual["L_c"])
    d_sham = float(sham["L_o"] - sham["L_c"])
    effect = d_original - d_counterfactual
    sham_shift = d_original - d_sham
    return {
        "D_original": d_original,
        "D_counterfactual": d_counterfactual,
        "D_sham": d_sham,
        "CE": effect,
        "sham_shift": sham_shift,
        "CE_controlled": effect - sham_shift,
    }


def _softmax(logits: np.ndarray) -> np.ndarray:
    values = np.asarray(logits, dtype=np.float64)
    values = values - np.max(values)
    probabilities = np.exp(values)
    return probabilities / probabilities.sum()


def js_divergence_from_logits(left: Sequence[float], right: Sequence[float]) -> float:
    """Return Jensen-Shannon divergence in natural-log units."""

    p = _softmax(np.asarray(left))
    q = _softmax(np.asarray(right))
    if np.array_equal(p, q):
        return 0.0
    midpoint = 0.5 * (p + q)
    p_terms = np.where(p > 0, p * (np.log(p) - np.log(midpoint)), 0.0)
    q_terms = np.where(q > 0, q * (np.log(q) - np.log(midpoint)), 0.0)
    return float(0.5 * (p_terms.sum() + q_terms.sum()))


def pre_e0_checkpoints(e0_token: int) -> list[int]:
    """Return the frozen checkpoint schedule, all strictly before E0.

    A checkpoint value is the number of generated tokens retained in the
    evidence-neutral prefix. Zero is the earliest valid reasoning checkpoint.
    """

    e0 = int(e0_token)
    if e0 <= 0:
        raise ValueError("E0 must follow at least one evidence-neutral prefix token")
    # Values are prefix lengths, not token indices. A length of E0 ends at
    # token index E0-1 and therefore remains strictly before the E0 token.
    values = {0, e0, *(e0 - offset for offset in (64, 32, 16, 8) if e0 - offset >= 0)}
    return sorted(value for value in values if value <= e0)


def bootstrap_interval(
    values: Sequence[float],
    *,
    statistic: str = "mean",
    seed: int = 31_415,
    resamples: int = 20_000,
    confidence: float = 0.95,
) -> dict[str, float | int | str]:
    """Return a deterministic percentile bootstrap interval over base problems."""

    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or array.size == 0 or not np.isfinite(array).all():
        raise ValueError("Bootstrap values must be a nonempty finite one-dimensional sequence")
    if statistic not in {"mean", "median"}:
        raise ValueError(f"Unsupported bootstrap statistic: {statistic}")
    if resamples <= 0 or not 0.0 < confidence < 1.0:
        raise ValueError("Invalid bootstrap resample count or confidence")
    rng = np.random.default_rng(int(seed))
    samples = rng.choice(array, size=(int(resamples), array.size), replace=True)
    function = np.mean if statistic == "mean" else np.median
    estimates = function(samples, axis=1)
    alpha = (1.0 - float(confidence)) / 2.0
    return {
        "statistic": statistic,
        "estimate": float(function(array)),
        "ci_low": float(np.quantile(estimates, alpha)),
        "ci_high": float(np.quantile(estimates, 1.0 - alpha)),
        "confidence": float(confidence),
        "resamples": int(resamples),
        "seed": int(seed),
    }


def summarize_effect_values(
    values: Sequence[float],
    *,
    seed: int = 31_415,
    resamples: int = 20_000,
) -> dict[str, Any]:
    """Summarize one prospectively defined effect per independent base problem."""

    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or array.size == 0 or not np.isfinite(array).all():
        raise ValueError("Effect values must be a nonempty finite one-dimensional sequence")
    positive = int(np.count_nonzero(array > 0.0))
    return {
        "n": int(array.size),
        "expected_direction_definition": "effect > 0",
        "expected_direction_count": positive,
        "expected_direction_proportion": float(positive / array.size),
        "expected_direction_proportion_bootstrap_ci": bootstrap_interval(
            (array > 0.0).astype(np.float64), statistic="mean", seed=seed + 2, resamples=resamples
        ),
        "mean": float(np.mean(array)),
        "median": float(np.median(array)),
        "minimum": float(np.min(array)),
        "maximum": float(np.max(array)),
        "mean_bootstrap_ci": bootstrap_interval(array, statistic="mean", seed=seed, resamples=resamples),
        "median_bootstrap_ci": bootstrap_interval(array, statistic="median", seed=seed + 1, resamples=resamples),
    }
