"""Prospectively defined Stage 2B effect summaries."""

from __future__ import annotations

import re
from typing import Any, Sequence


MATERIAL_EFFECT_NATS = 0.05
SPECIFICITY_MARGIN_NATS = 0.05


def first_token_divergence(baseline: Sequence[int], condition: Sequence[int]) -> int | None:
    for index, (left, right) in enumerate(zip(baseline, condition)):
        if int(left) != int(right):
            return index
    if len(baseline) != len(condition):
        return min(len(baseline), len(condition))
    return None


def first_semantic_divergence(baseline_text: str, condition_text: str) -> dict[str, Any]:
    """Return the first differing sentence/newline segment as a lightweight audit aid."""

    split = lambda text: [
        re.sub(r"\s+", " ", segment).strip()
        for segment in re.split(r"(?<=[.!?])\s+|\n+", text)
        if segment.strip()
    ]
    baseline_segments = split(baseline_text)
    condition_segments = split(condition_text)
    for index, (left, right) in enumerate(zip(baseline_segments, condition_segments)):
        if left != right:
            return {"segment_index": index, "baseline_segment": left, "condition_segment": right}
    if len(baseline_segments) != len(condition_segments):
        index = min(len(baseline_segments), len(condition_segments))
        return {
            "segment_index": index,
            "baseline_segment": baseline_segments[index] if index < len(baseline_segments) else None,
            "condition_segment": condition_segments[index] if index < len(condition_segments) else None,
        }
    return {"segment_index": None, "baseline_segment": None, "condition_segment": None}


def classify_local_effects(effects: dict[str, dict[str, float]]) -> dict[str, Any]:
    """Assign one P1--P6 category from local clean-token NLL changes.

    The 0.05-nat materiality and specificity margins are fixed before causal
    outputs are inspected. Raw effects remain primary for this five-item pilot.
    """

    a = effects["A"]
    b = effects["B"]
    all_values = [float(value) for window in (a, b) for value in window.values()]
    a_specific = (
        float(a["A_roi"]) >= MATERIAL_EFFECT_NATS
        and float(a["A_roi"]) - max(float(a["B_roi"]), float(a["irrelevant_roi"])) >= SPECIFICITY_MARGIN_NATS
    )
    b_specific = (
        float(b["B_roi"]) >= MATERIAL_EFFECT_NATS
        and float(b["B_roi"]) - max(float(b["A_roi"]), float(b["irrelevant_roi"])) >= SPECIFICITY_MARGIN_NATS
    )
    persistent_a = (
        float(a["A_roi"]) - max(float(a["B_roi"]), float(a["irrelevant_roi"])) >= SPECIFICITY_MARGIN_NATS
        and float(b["A_roi"]) - max(float(b["B_roi"]), float(b["irrelevant_roi"])) >= SPECIFICITY_MARGIN_NATS
    )
    persistent_b = (
        float(a["B_roi"]) - max(float(a["A_roi"]), float(a["irrelevant_roi"])) >= SPECIFICITY_MARGIN_NATS
        and float(b["B_roi"]) - max(float(b["A_roi"]), float(b["irrelevant_roi"])) >= SPECIFICITY_MARGIN_NATS
    )
    general_fragility = all(
        max(float(window[key]) for key in ("A_roi", "B_roi", "irrelevant_roi"))
        - min(float(window[key]) for key in ("A_roi", "B_roi", "irrelevant_roi"))
        < SPECIFICITY_MARGIN_NATS
        for window in (a, b)
    ) and max(all_values) >= MATERIAL_EFFECT_NATS

    if max(abs(value) for value in all_values) < MATERIAL_EFFECT_NATS:
        category, label = "P5", "No detectable ROI-level causal dependence"
    elif a_specific and b_specific:
        category, label = "P1", "Strong evidence-specific crossover"
    elif persistent_a or persistent_b:
        category, label = "P4", "Persistent evidence dependence"
    elif a_specific or b_specific:
        category, label = "P2", "Partial evidence specificity"
    elif general_fragility:
        category, label = "P3", "General visual fragility"
    else:
        category, label = "P6", "Uninterpretable or ambiguous local pattern"

    return {
        "category": category,
        "label": label,
        "A_window_specific": bool(a_specific),
        "B_window_specific": bool(b_specific),
        "persistent_A": bool(persistent_a),
        "persistent_B": bool(persistent_b),
        "material_effect_threshold_nats_per_token": MATERIAL_EFFECT_NATS,
        "specificity_margin_nats_per_token": SPECIFICITY_MARGIN_NATS,
        "crossover_score": (
            float(a["A_roi"]) - float(a["B_roi"]) + float(b["B_roi"]) - float(b["A_roi"])
        ),
    }
