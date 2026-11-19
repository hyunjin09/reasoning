"""Prospectively frozen Stage 3C.6 alignment, gates, and region selection."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any


def aligned_evidence_score(raw_d: float, condition: str) -> float:
    """Orient evidence preference toward the fact native to O or C."""

    value = float(raw_d)
    if not math.isfinite(value):
        raise ValueError("Evidence preference must be finite")
    if condition in {"O", "O_sham"}:
        return value
    if condition in {"C", "C_sham"}:
        return -value
    raise ValueError(f"Unsupported semantic condition: {condition}")


def rescue_effect(
    *, native_d: float, suppressed_d: float, rescued_d: float, condition: str
) -> dict[str, Any]:
    native = aligned_evidence_score(native_d, condition)
    suppressed = aligned_evidence_score(suppressed_d, condition)
    rescued = aligned_evidence_score(rescued_d, condition)
    loss = native - suppressed
    if loss == 0.0:
        raise ValueError("Rescue ratio is undefined for zero suppression loss")
    gain = rescued - suppressed
    return {
        "condition": condition,
        "aligned_native": native,
        "aligned_suppressed": suppressed,
        "aligned_rescued": rescued,
        "suppression_loss": loss,
        "rescue_gain": gain,
        "rescue_ratio": gain / loss,
        "rescue_ratio_is_clipped": False,
    }


def _robust_layer(row: Mapping[str, Any]) -> bool:
    ci = row["gain_bootstrap_mean_ci95"]
    return bool(
        float(row["holm_adjusted_p"]) < 0.05
        and float(ci[0]) > 0.0
        and int(row["positive_count"]) >= math.ceil(0.75 * int(row["N"]))
    )


def threshold_crossings(rows: Sequence[Mapping[str, Any]]) -> dict[str, int | None]:
    ordered = sorted(rows, key=lambda row: int(row["layer"]))
    result: dict[str, int | None] = {}
    for label, threshold in (("first_20", 0.20), ("first_50", 0.50), ("first_80", 0.80)):
        result[label] = next(
            (
                int(row["layer"])
                for row in ordered
                if float(row["median_RR"]) >= threshold and _robust_layer(row)
            ),
            None,
        )
    return result


def select_candidate_region(
    rows: Sequence[Mapping[str, Any]], *, layer_count: int = 36, window_size: int = 4
) -> dict[str, Any] | None:
    """Select a four-layer region without consulting within-block outcomes."""

    by_layer = {int(row["layer"]): row for row in rows}
    if set(by_layer) != set(range(int(layer_count))):
        raise ValueError("Candidate-region selection requires every frozen layer")
    if int(window_size) < 2 or int(window_size) > int(layer_count):
        raise ValueError("Invalid candidate-region window size")
    candidates: list[dict[str, Any]] = []
    for start in range(int(layer_count) - int(window_size) + 1):
        layers = list(range(start, start + int(window_size)))
        adjacent_significant = [
            [left, left + 1]
            for left in layers[:-1]
            if float(by_layer[left]["holm_adjusted_p"]) < 0.05
            and float(by_layer[left + 1]["holm_adjusted_p"]) < 0.05
            and float(by_layer[left]["median_gain"]) > 0.0
            and float(by_layer[left + 1]["median_gain"]) > 0.0
        ]
        slopes = [
            (float(by_layer[left + 1]["median_gain"]) - float(by_layer[left]["median_gain"]), left)
            for left in layers[:-1]
        ]
        best_slope, best_left = max(slopes, key=lambda item: (item[0], -item[1]))
        if adjacent_significant and best_slope > 0.0:
            candidates.append({
                "layers": layers,
                "largest_positive_slope": best_slope,
                "slope_transition": [best_left, best_left + 1],
                "adjacent_significant_pairs": adjacent_significant,
            })
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda row: (-float(row["largest_positive_slope"]), int(row["layers"][0])),
    )


__all__ = [
    "aligned_evidence_score",
    "rescue_effect",
    "select_candidate_region",
    "threshold_crossings",
]
