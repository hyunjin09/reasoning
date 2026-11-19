"""Frozen event/base classification rules for Stage 3C.9."""

from __future__ import annotations

import statistics
from collections.abc import Mapping, Sequence
from typing import Any


def aligned_preference(value: float, condition: str) -> float:
    """Orient D so positive always favors the fact depicted by the condition."""

    name = str(condition)
    if name in {"O", "O_sham"}:
        return float(value)
    if name in {"C", "C_sham"}:
        return -float(value)
    raise ValueError(f"Unknown semantic condition: {condition}")


def source_and_rescue_effects(
    *, condition: str, native_D: float, suppressed_D: float,
    rescue_D: float | None = None,
) -> dict[str, float | None]:
    """Return sign-aligned unnormalized source loss and unclipped rescue ratio."""

    native = aligned_preference(native_D, condition)
    suppressed = aligned_preference(suppressed_D, condition)
    source_loss = native - suppressed
    rescue = None if rescue_D is None else aligned_preference(rescue_D, condition)
    gain = None if rescue is None else rescue - suppressed
    ratio = None if gain is None or source_loss == 0.0 else gain / source_loss
    return {
        "aligned_native_D": native,
        "aligned_suppressed_D": suppressed,
        "aligned_rescue_D": rescue,
        "source_loss": source_loss,
        "rescue_gain": gain,
        "rescue_ratio": ratio,
    }


def summarize_source_window(
    condition_scores: Mapping[str, Mapping[str, float]], *, effect_floor: float = 0.05,
) -> dict[str, Any]:
    """Apply the frozen semantic-direction and matched-sham source gate."""

    required = {"O", "C", "O_sham", "C_sham"}
    if set(condition_scores) != required:
        raise ValueError(f"Source summary requires exactly {sorted(required)}")
    details = {
        condition: source_and_rescue_effects(
            condition=condition,
            native_D=float(scores["native_D"]),
            suppressed_D=float(scores["suppressed_D"]),
        )
        for condition, scores in condition_scores.items()
    }
    source_losses = {condition: float(details[condition]["source_loss"]) for condition in ("O", "C")}
    sham_effects = {condition: float(details[condition]["source_loss"]) for condition in ("O_sham", "C_sham")}
    classification = classify_checkpoint(
        source_losses=source_losses,
        sham_source_effects=sham_effects,
        rescue_gains={},
        rescue_ratios={},
        neighbor_gains={},
        effect_floor=effect_floor,
    )
    return {
        "source_losses": source_losses,
        "sham_source_effects": sham_effects,
        "condition_metrics": details,
        "source_loss_mean": classification["source_loss_mean"],
        "sham_source_effect_mean_abs": classification["sham_source_effect_mean_abs"],
        "source_sensitive": classification["source_sensitive"],
        "source_classification": "C1" if classification["source_sensitive"] else "C0",
        "effect_floor": float(effect_floor),
    }


def _mean(values: Mapping[str, float] | None) -> float | None:
    if not values:
        return None
    return statistics.fmean(float(value) for value in values.values())


def classify_checkpoint(
    *, source_losses: Mapping[str, float], sham_source_effects: Mapping[str, float],
    rescue_gains: Mapping[str, float], rescue_ratios: Mapping[str, float],
    neighbor_gains: Mapping[str, float], final_rescue_gains: Mapping[str, float] | None = None,
    effect_floor: float = 0.05, rescue_ratio_floor: float = 0.25,
) -> dict[str, Any]:
    """Apply the prospectively frozen C0--C3 event rule."""

    source_mean = float(_mean(source_losses) or 0.0)
    sham_mean_abs = statistics.fmean(abs(float(value)) for value in sham_source_effects.values()) if sham_source_effects else 0.0
    rescue_mean = float(_mean(rescue_gains) or 0.0)
    neighbor_mean = float(_mean(neighbor_gains) or 0.0)
    rescue_ratio_median = (
        statistics.median(float(value) for value in rescue_ratios.values())
        if rescue_ratios else None
    )
    source_sensitive = (
        bool(source_losses)
        and all(float(value) >= 0.0 for value in source_losses.values())
        and source_mean >= float(effect_floor)
        and source_mean > sham_mean_abs
    )
    functional = (
        source_sensitive
        and bool(rescue_gains)
        and set(rescue_ratios) == set(rescue_gains)
        and all(float(value) > 0.0 for value in rescue_gains.values())
        and rescue_mean >= float(effect_floor)
        and rescue_ratio_median is not None
        and rescue_ratio_median >= float(rescue_ratio_floor)
        and rescue_mean > neighbor_mean
    )
    final_mean = _mean(final_rescue_gains)
    persistent = (
        functional
        and final_rescue_gains is not None
        and bool(final_rescue_gains)
        and all(float(value) > 0.0 for value in final_rescue_gains.values())
        and float(final_mean or 0.0) >= float(effect_floor)
    )
    classification = "C3" if persistent else "C2" if functional else "C1" if source_sensitive else "C0"
    return {
        "classification": classification,
        "source_sensitive": source_sensitive,
        "functional_span_rescue": functional,
        "persistent_checkpoint": persistent,
        "source_loss_mean": source_mean,
        "sham_source_effect_mean_abs": sham_mean_abs,
        "rescue_gain_mean": rescue_mean,
        "neighbor_gain_mean": neighbor_mean,
        "median_unclipped_rescue_ratio": rescue_ratio_median,
        "final_rescue_gain_mean": final_mean,
        "effect_floor": float(effect_floor),
        "rescue_ratio_floor": float(rescue_ratio_floor),
    }


def repeated_checkpoint_status(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    qualified = [
        (index, event) for index, event in enumerate(events)
        if str(event.get("classification")) in {"C2", "C3"}
    ]
    pairs = []
    for left_index, (left_original, left) in enumerate(qualified):
        for right_original, right in qualified[left_index + 1:]:
            left_start, left_end = int(left["span_start_token"]), int(left["span_end_token"])
            right_start, right_end = int(right["span_start_token"]), int(right["span_end_token"])
            nonoverlap = left_end <= right_start or right_end <= left_start
            if nonoverlap and abs(right_start - left_start) >= 24:
                pairs.append([left_original, right_original])
    return {
        "repeated_checkpoint": bool(pairs),
        "checkpoint_count": len(qualified),
        "checkpoint_event_indices": [index for index, _ in qualified],
        "qualifying_pairs": pairs,
        "minimum_separation": 24,
    }


def lifetime_phenotype(
    *, local_gain: float, downstream: Sequence[tuple[int, float]],
    final_gain: float | None, effect_floor: float = 0.05,
) -> str:
    """Classify persistence at frozen semantic readouts without pseudo-readouts."""

    if float(local_gain) < float(effect_floor):
        return "NOT_APPLICABLE"
    meaningful = [(int(distance), float(gain)) for distance, gain in downstream if float(gain) >= effect_floor]
    if final_gain is not None and float(final_gain) >= effect_floor:
        return "L-Persistent"
    if any(distance >= 65 for distance, _ in meaningful):
        return "L-Persistent"
    if any(33 <= distance <= 64 for distance, _ in meaningful):
        return "L-Medium"
    return "L-Short"


def route_phenotype(
    *, direct_deficit: float, short_history_deficit: float,
    joint_deficit: float, effect_floor: float = 0.05,
) -> str:
    """Classify fixed direct/prior-history/joint route deficits without fractions."""

    direct = float(direct_deficit) >= float(effect_floor)
    inherited = float(short_history_deficit) >= float(effect_floor)
    joint = float(joint_deficit) >= float(effect_floor)
    if direct and inherited:
        return "R-Mixed"
    if direct:
        return "R-Direct"
    if inherited:
        return "R-Inherited"
    if joint:
        return "R-Redundant"
    return "R-Unresolved"


def enrichment_match_key(
    focal: Mapping[str, Any], candidate: Mapping[str, Any],
) -> tuple[float, float, float, float, float, int]:
    """Rank a non-checkpoint control on every predeclared structure covariate."""

    return (
        float(bool(candidate["boundary_position"]) != bool(focal["boundary_position"])),
        abs(float(candidate["distance_to_local_use_readout"]) - float(focal["distance_to_local_use_readout"])),
        abs(float(candidate["normalized_reasoning_progress"]) - float(focal["normalized_reasoning_progress"])),
        abs(float(candidate["span_length"]) - float(focal["span_length"])),
        abs(float(candidate["local_token_density"]) - float(focal["local_token_density"])),
        int(candidate["event_id"]),
    )
