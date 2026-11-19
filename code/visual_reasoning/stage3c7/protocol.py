"""Frozen Stage 3C.7 metrics and decision rules."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any


def aligned_evidence_score(raw_d: float, condition: str) -> float:
    value = float(raw_d)
    if not math.isfinite(value):
        raise ValueError("Evidence preference must be finite")
    if condition == "O":
        return value
    if condition == "C":
        return -value
    raise ValueError(f"Unsupported condition: {condition}")


def rescue_effect(*, native_d: float, suppressed_d: float, rescued_d: float, condition: str) -> dict[str, Any]:
    native = aligned_evidence_score(native_d, condition)
    suppressed = aligned_evidence_score(suppressed_d, condition)
    rescued = aligned_evidence_score(rescued_d, condition)
    loss = native - suppressed
    gain = rescued - suppressed
    return {
        "condition": condition,
        "aligned_native": native,
        "aligned_suppressed": suppressed,
        "aligned_rescued": rescued,
        "suppression_loss": loss,
        "rescue_gain": gain,
        "rescue_ratio": gain / loss if loss != 0.0 else None,
        "rescue_ratio_is_clipped": False,
    }


def robust_effect(row: Mapping[str, Any]) -> bool:
    ci = row["gain_bootstrap_mean_ci95"]
    return bool(
        float(row["holm_adjusted_p"]) < 0.05
        and float(ci[0]) > 0.0
        and int(row["positive_count"]) >= math.ceil(0.75 * int(row["N"]))
    )


def substantial(row: Mapping[str, Any], threshold: float = 0.50) -> bool:
    return bool(row.get("robust_positive", False) and float(row["median_RR"]) >= float(threshold))


def joint_outcome(
    *, full_cache: Mapping[str, Any], residual: Mapping[str, Any],
    downstream_cache: Mapping[str, Any], joint: Mapping[str, Any],
    joint_over_residual: Mapping[str, Any], joint_over_cache: Mapping[str, Any],
) -> str:
    joint_substantial = substantial(joint, 0.50)
    joint_near_complete = substantial(joint, 0.80)
    residual_substantial = substantial(residual, 0.50)
    downstream_substantial = substantial(downstream_cache, 0.50)
    cache_substantial = substantial(full_cache, 0.50)
    both_increments = bool(
        joint_over_residual.get("robust_positive", False)
        and joint_over_cache.get("robust_positive", False)
    )
    if joint_near_complete and not residual_substantial and not downstream_substantial:
        return "O3_two_query_synergy"
    if joint_substantial and both_increments:
        return "O2_residual_cache_complementarity"
    if residual_substantial and not bool(joint_over_residual.get("robust_positive", False)):
        return "O4_residual_dominant"
    if cache_substantial:
        return "O1_prior_cache_carrier"
    return "O5_distributed_beyond_last_token_cache_and_residual"


def recommendation_for_outcome(outcome: str, *, joint_near_complete: bool, cache_nonzero: bool) -> str:
    if outcome == "O1_prior_cache_carrier":
        return "GO — Token-Type Carrier Atlas"
    if outcome in {"O2_residual_cache_complementarity", "O3_two_query_synergy"}:
        return "GO — Token-Type Carrier Atlas" if joint_near_complete else "GO — Broader Recent-Cache Interaction"
    if outcome == "O4_residual_dominant":
        return "GO — Residual Feature Mechanism"
    if outcome == "O5_distributed_beyond_last_token_cache_and_residual" and cache_nonzero:
        return "GO — Broader Recent-Cache Interaction"
    return "GO — Residual Feature Mechanism"


__all__ = [
    "aligned_evidence_score", "joint_outcome", "recommendation_for_outcome",
    "rescue_effect", "robust_effect", "substantial",
]
