"""Pure timing-curve summaries for Stage 3B.1."""

from __future__ import annotations

import math
from typing import Any, Sequence


THRESHOLDS = (0.50, 0.80, 0.90)
SCHEDULE_FIELDS = (
    "cutoff_generated_index",
    "labels",
    "requested_coordinates",
    "tokens_before_e0",
    "actual_progress",
    "strictly_pre_e0",
)


def schedule_matches_curve(
    schedule: Sequence[dict[str, Any]], curve: Sequence[dict[str, Any]]
) -> bool:
    """Return whether scored rows exactly preserve the frozen schedule metadata."""

    if len(schedule) != len(curve):
        return False
    return all(
        all(observed.get(field) == expected.get(field) for field in SCHEDULE_FIELDS)
        for expected, observed in zip(schedule, curve)
    )


def select_frozen_attention_event(
    candidates: Sequence[dict[str, Any]], *, frozen_pre_e0_density: float | None
) -> dict[str, Any] | None:
    """Resolve duplicate-E0 events using Stage 3A's already-frozen density match."""

    if len(candidates) == 1:
        return candidates[0]
    if not candidates or frozen_pre_e0_density is None:
        return None
    matching = [
        row
        for row in candidates
        if math.isclose(
            float(row["prediction_aligned_region_means"]["roi_per_token_density"]["PRE"]),
            float(frozen_pre_e0_density),
            rel_tol=1e-12,
            abs_tol=1e-15,
        )
    ]
    return matching[0] if len(matching) == 1 else None


def _ordered(curve: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = sorted(curve, key=lambda row: int(row["cutoff_generated_index"]))
    if not rows or len({int(row["cutoff_generated_index"]) for row in rows}) != len(rows):
        raise ValueError("Timing curve must contain nonempty unique cutoff indices")
    return rows


def _crossing_record(row: dict[str, Any], e0_start_token: int) -> dict[str, Any]:
    index = int(row["cutoff_generated_index"])
    return {
        "cutoff_generated_index": index,
        "tokens_before_e0": int(e0_start_token) - index,
        "normalized_progress": float(row["actual_progress"]),
        "retention_ratio_raw": float(row["retention_ratio_raw"]),
    }


def threshold_times(curve: Sequence[dict[str, Any]], *, e0_start_token: int) -> dict[str, Any]:
    """Report discrete first and stable crossings without smoothing."""

    rows = _ordered(curve)
    e0 = int(e0_start_token)
    result: dict[str, Any] = {}
    for threshold in THRESHOLDS:
        first_index = next(
            (index for index, row in enumerate(rows) if float(row["retention_ratio_raw"]) >= threshold),
            None,
        )
        stable_index = next(
            (
                index
                for index in range(len(rows))
                if all(float(row["retention_ratio_raw"]) >= threshold for row in rows[index:])
            ),
            None,
        )
        result[f"rho_{int(threshold * 100)}"] = {
            "threshold": threshold,
            "first": _crossing_record(rows[first_index], e0) if first_index is not None else None,
            "stable": _crossing_record(rows[stable_index], e0) if stable_index is not None else None,
        }
    return result


def monotonicity_audit(
    curve: Sequence[dict[str, Any]], *, control_noise_tolerance: float
) -> dict[str, Any]:
    """Retain all raw local decreases and separately flag control-sized noise."""

    rows = _ordered(curve)
    values = [float(row["retention_ratio_raw"]) for row in rows]
    downward = [max(0.0, left - right) for left, right in zip(values, values[1:])]
    decreases = [value for value in downward if value > 0.0]
    maximum = max(decreases, default=0.0)
    tolerance = float(control_noise_tolerance)
    return {
        "local_decrease_count": len(decreases),
        "maximum_downward_step": maximum,
        "total_downward_movement": sum(decreases),
        "monotonic_raw": not decreases,
        "control_noise_tolerance": tolerance,
        "deviation_exceeds_control_noise": maximum > tolerance,
        "material_complexity_threshold": 0.20,
        "material_non_monotonic": maximum > 0.20,
    }


def classify_timing_pattern(
    curve: Sequence[dict[str, Any]],
    *,
    thresholds: dict[str, Any],
    monotonicity: dict[str, Any],
) -> str:
    """Apply the prospectively documented descriptive S1--S6 rules."""

    rows = _ordered(curve)
    if bool(monotonicity["material_non_monotonic"]):
        return "S6_non_monotonic_complex"
    start = float(rows[0]["retention_ratio_raw"])
    if start >= 0.80:
        return "S1_prefill_sufficient"
    first_80 = thresholds["rho_80"]["first"]
    if first_80 is not None:
        progress = float(first_80["normalized_progress"])
        if progress <= 0.25:
            return "S2_early_postprefill_acquisition"
        if progress <= 0.75:
            return "S3_gradual_accumulation"
        return "S4_late_acquisition"
    if float(rows[-1]["retention_ratio_raw"]) < 0.50:
        return "S5_persistent_direct_vision_dependence"
    return "S3_gradual_accumulation"
