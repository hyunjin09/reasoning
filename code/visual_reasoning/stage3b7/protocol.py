"""Prospectively frozen Stage 3B.7 gates and mechanism categories."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def phase_a_gate_passes(
    *,
    target_summary: Mapping[str, Any],
    ring_summary: Mapping[str, Any],
    target_minus_irrelevant: Mapping[str, Any],
) -> bool:
    return bool(
        target_summary["robust"]
        and float(target_minus_irrelevant["bootstrap_95_CI"][0]) > 0.0
        and float(target_minus_irrelevant["target_greater_fraction"]) >= 0.70
        and max(
            float(target_summary["median_PRR"]),
            float(ring_summary["median_PRR"]),
        )
        >= 0.50
    )


def classify_kv_mechanism(
    *,
    k: Mapping[str, Any],
    v: Mapping[str, Any],
    interaction: Mapping[str, Any],
) -> str:
    k_ratio = float(k["median_KVR"])
    v_ratio = float(v["median_KVR"])
    if bool(v["robust"]) and v_ratio >= 0.75 and k_ratio < 0.50:
        return "Value-Dominant"
    if bool(k["robust"]) and k_ratio >= 0.75 and v_ratio < 0.50:
        return "Routing-Dominant"
    if (
        bool(k["robust"])
        and bool(v["robust"])
        and k_ratio >= 0.25
        and v_ratio >= 0.25
        and float(interaction["bootstrap_95_CI"][0]) > 0.0
    ):
        return "Routing+Value-Interaction"
    return "Mechanism-Inconclusive"


__all__ = ["classify_kv_mechanism", "phase_a_gate_passes"]
