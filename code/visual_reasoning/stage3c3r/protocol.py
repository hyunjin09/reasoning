"""Prospectively frozen decision helpers for Stage 3C.3-R."""

from __future__ import annotations

import math
import statistics
from collections.abc import Mapping
from typing import Any


def redundancy_gate(retained_by_base: Mapping[str, Mapping[str, float]]) -> dict[str, Any]:
    """Evaluate the frozen base-level Phase-B gate.

    Each independent base contributes once, as the arithmetic mean of its two
    frozen target-specific, unclipped retained-evidence ratios.
    """

    if not retained_by_base:
        raise ValueError("The redundancy gate requires at least one base")
    base_retained: dict[str, float] = {}
    for base, targets in retained_by_base.items():
        if set(targets) != {"target_a", "target_b"}:
            raise ValueError(f"Base {base} must contain both frozen targets")
        values = [float(targets[name]) for name in ("target_a", "target_b")]
        if not all(math.isfinite(value) for value in values):
            raise ValueError(f"Base {base} has a non-finite retained-evidence ratio")
        base_retained[str(base)] = sum(values) / 2.0
    values = list(base_retained.values())
    median = float(statistics.median(values))
    high_fraction = float(sum(value >= 0.80 for value in values) / len(values))
    return {
        "aggregation": "one independent value per base: mean of target_a and target_b E(0)/E(1); unclipped",
        "base_retained": base_retained,
        "N_unique_bases": len(values),
        "median_retained": median,
        "fraction_at_least_0_80": high_fraction,
        "median_rule": median >= 0.50,
        "high_fraction_rule": high_fraction >= 0.40,
        "passed": bool(median >= 0.50 or high_fraction >= 0.40),
    }


def approximate_monotonic_decrease(
    curve: Mapping[float, float], *, tolerance_fraction: float = 0.10
) -> bool:
    """Return whether evidence does not materially fall as gain increases.

    A local reversal is tolerated only up to 10% of the native evidence
    magnitude. This is a descriptive eligibility rule, not an inferential test.
    """

    if 1.0 not in curve or not curve:
        return False
    ordered = sorted((float(gain), float(value)) for gain, value in curve.items())
    if not all(math.isfinite(value) for _, value in ordered):
        return False
    tolerance = abs(float(curve[1.0])) * float(tolerance_fraction)
    return all(right + tolerance >= left for (_, left), (_, right) in zip(ordered, ordered[1:]))


def tested_thresholds(curve: Mapping[float, float]) -> dict[str, Any]:
    """Find tested (never interpolated) retained-evidence thresholds."""

    native = float(curve.get(1.0, math.nan))
    monotonic = approximate_monotonic_decrease(curve)
    if not monotonic or not math.isfinite(native) or native == 0.0:
        return {
            "approximately_monotonic": False,
            "lambda_80": None,
            "lambda_50": None,
            "interpolated": False,
        }
    retained = {float(gain): float(value) / native for gain, value in curve.items()}
    return {
        "approximately_monotonic": True,
        "lambda_80": min((gain for gain, value in retained.items() if value >= 0.80), default=None),
        "lambda_50": min((gain for gain, value in retained.items() if value >= 0.50), default=None),
        "interpolated": False,
    }


__all__ = ["approximate_monotonic_decrease", "redundancy_gate", "tested_thresholds"]

