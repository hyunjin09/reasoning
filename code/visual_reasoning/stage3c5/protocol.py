"""Prospectively frozen Stage 3C.5 scopes, gates, and metrics."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any


def frozen_tpre_layer_scopes(*, language_layers: int) -> dict[str, list[int]]:
    if int(language_layers) != 36:
        raise ValueError("Stage 3C.5 requires the frozen 36-layer architecture")
    return {
        "P0": [28, 29],
        "P1": [32, 33],
        "P2": list(range(28, 34)),
        "P3": list(range(24, 36)),
        "P4": list(range(16, 36)),
        "P5": list(range(36)),
    }


def evaluate_phase_b_gate(
    *,
    median_loss: float,
    positive_count: int,
    adjusted_p: float,
    n: int,
    historical_increment: float,
    minimum_historical_fraction: float,
) -> dict[str, Any]:
    values = (median_loss, adjusted_p, historical_increment, minimum_historical_fraction)
    if not all(math.isfinite(float(value)) for value in values) or int(n) <= 0:
        raise ValueError("Phase-B gate requires finite values and a positive cohort size")
    minimum_loss = float(historical_increment) * float(minimum_historical_fraction)
    minimum_positive = math.ceil(0.75 * int(n))
    checks = {
        "median_loss_at_least_minimum": float(median_loss) >= minimum_loss,
        "positive_count_at_least_75_percent": int(positive_count) >= minimum_positive,
        "holm_adjusted_p_below_0_05": float(adjusted_p) < 0.05,
    }
    return {
        "pass": all(checks.values()),
        "checks": checks,
        "median_loss": float(median_loss),
        "minimum_loss": minimum_loss,
        "positive_count": int(positive_count),
        "minimum_positive_count": minimum_positive,
        "N": int(n),
        "holm_adjusted_p": float(adjusted_p),
    }


def select_necessary_scope(
    scope_statistics: Mapping[str, Mapping[str, float]],
    *,
    n: int,
    fraction_of_p5: float = 0.80,
) -> dict[str, Any]:
    order = ("P0", "P1", "P2", "P3", "P4", "P5")
    if set(scope_statistics) != set(order):
        raise ValueError("Necessary-scope selection requires exactly P0--P5")
    p5_loss = float(scope_statistics["P5"]["median_loss"])
    threshold = float(fraction_of_p5) * p5_loss
    minimum_positive = math.ceil(0.75 * int(n))
    eligible = []
    for label in order:
        row = scope_statistics[label]
        passes = bool(
            float(row["median_loss"]) >= threshold
            and int(row["positive_count"]) >= minimum_positive
            and float(row["adjusted_p"]) < 0.05
        )
        if passes:
            eligible.append(label)
    chosen = eligible[0] if eligible else "P5"
    return {
        "scope_id": chosen,
        "threshold_fraction_of_p5": float(fraction_of_p5),
        "threshold_loss": threshold,
        "p5_median_loss": p5_loss,
        "eligible_scopes_in_plan_order": eligible,
        "fallback_to_p5": not bool(eligible),
    }


def carrier_restoration(
    *,
    native_o: float,
    native_c: float,
    donor_o_into_c: float,
    donor_c_into_o: float,
) -> dict[str, float]:
    values = tuple(map(float, (native_o, native_c, donor_o_into_c, donor_c_into_o)))
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Carrier restoration requires finite scores")
    o, c, o_into_c, c_into_o = values
    gap = o - c
    if gap == 0.0:
        raise ValueError("Carrier reference gap must be nonzero")
    shift_oc = o_into_c - c
    shift_co = o - c_into_o
    bcr = 0.5 * (shift_oc + shift_co)
    return {
        "native_O_D": o,
        "native_C_D": c,
        "reference_gap": gap,
        "donor_O_into_C_D": o_into_c,
        "donor_C_into_O_D": c_into_o,
        "o_into_c_shift": shift_oc,
        "c_into_o_shift": shift_co,
        "BCR": bcr,
        "CRR": bcr / gap,
    }


def classify_handoff(
    *, r_robust: bool, q_robust: bool, hpre_robust: bool, r_expands: bool
) -> str:
    count = sum(map(bool, (r_robust, q_robust, hpre_robust)))
    if count > 1:
        return "H5_mixed_carrier"
    if r_robust:
        return "H2_short_R_accumulation" if r_expands else "H1_immediate_R_carrier"
    if q_robust:
        return "H3_Q_carrier"
    if hpre_robust:
        return "H4_current_residual_carrier"
    return "H6_no_clean_carrier"


def reduced_control_arms(selected_layers: list[int]) -> list[dict[str, Any]]:
    layers = sorted({int(value) for value in selected_layers})
    if not layers:
        raise ValueError("Reduced controls require a nonempty frozen layer scope")
    return [
        {"arm_id": f"{source}_tpre", "source": source, "layers": layers}
        for source in ("T", "M", "I")
    ]


__all__ = [
    "carrier_restoration",
    "classify_handoff",
    "evaluate_phase_b_gate",
    "frozen_tpre_layer_scopes",
    "reduced_control_arms",
    "select_necessary_scope",
]
