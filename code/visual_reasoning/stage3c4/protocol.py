"""Frozen Stage 3C.4 scope and decision helpers."""

from __future__ import annotations

import math


def frozen_layer_scopes(*, language_layers: int) -> dict[str, list[int]]:
    """Return the exact nested layer family from the approved plan."""

    if int(language_layers) != 36:
        raise ValueError("Stage 3C.4 requires the frozen 36-layer architecture")
    return {
        "L0": [28, 29],
        "L1": list(range(28, 34)),
        "L2": list(range(24, 36)),
        "L3": list(range(16, 36)),
        "L4": list(range(36)),
    }


def temporal_query_indices(*, current_generated_index: int, backward: int) -> list[int]:
    """Return an inclusive exact generated-index window ending at the target query."""

    current = int(current_generated_index)
    lookback = int(backward)
    if current <= 0 or lookback < 0:
        raise ValueError("Generated indices must be positive and lookback nonnegative")
    start = current - lookback
    if start <= 0:
        raise ValueError("The exact temporal window is unavailable for this history")
    return list(range(start, current + 1))


def classify_spatiotemporal_outcome(
    *,
    layer_l4_retention: float,
    time_t16_retention: float,
    c_late4_retention: float,
    c_all4_retention: float,
    substantial_retention: float = 0.80,
) -> str:
    """Apply the frozen joint O1--O4 classification.

    O3 is reserved for a direct fixed-cell layer-by-time dissociation: the
    late-layer four-query cell remains robust while the matched all-layer cell
    does not. Otherwise a backward-expansion loss is classified as O2.
    """

    values = (
        float(layer_l4_retention),
        float(time_t16_retention),
        float(c_late4_retention),
        float(c_all4_retention),
        float(substantial_retention),
    )
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Outcome classification requires finite retention values")
    layer_l4, time_t16, c_late4, c_all4, threshold = values
    if layer_l4 < threshold:
        return "O1_layer_redundancy"
    if time_t16 >= threshold:
        return "O4_earlier_nonvisual_storage"
    if c_late4 >= threshold and c_all4 < threshold:
        return "O3_spatiotemporal_redundancy"
    return "O2_temporal_redundancy"


__all__ = [
    "classify_spatiotemporal_outcome",
    "frozen_layer_scopes",
    "temporal_query_indices",
]

