"""Primary Stage 3B.0 cutoff-retention and patch-recovery metrics."""

from __future__ import annotations


def retention_ratio(*, ce_cut: float, ce_full: float) -> float | None:
    denominator = float(ce_full)
    return None if denominator == 0.0 else float(ce_cut) / denominator


def directional_recovery(
    *, recipient_preference: float, source_preference: float, patched_preference: float
) -> float | None:
    denominator = float(source_preference) - float(recipient_preference)
    if denominator == 0.0:
        return None
    return (float(patched_preference) - float(recipient_preference)) / denominator
