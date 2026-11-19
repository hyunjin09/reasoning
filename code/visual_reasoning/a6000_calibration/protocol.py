"""Frozen cell mappings and historical-reference extraction."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def target_cell_id(target_id: str) -> str:
    mapping = {"target_a": "Ed__W4", "target_b": "Ed_minus_1__W4"}
    try:
        return mapping[str(target_id)]
    except KeyError as error:
        raise ValueError(f"Unknown calibration target: {target_id}") from error


def extract_a5000_reference(
    cell: Mapping[str, Any], *, kv_row: Mapping[str, Any],
    residual_row: Mapping[str, Any], target_roi_row: Mapping[str, Any],
    irrelevant_roi_row: Mapping[str, Any],
) -> dict[str, Any]:
    base = str(cell["base_problem_id"])
    target = str(cell["target_id"])
    cell_id = target_cell_id(target)
    identities = [
        str(kv_row.get("base_problem_id")) == base and str(kv_row.get("target_id")) == target,
        str(residual_row.get("base_problem_id")) == base and str(residual_row.get("target_id")) == target,
        str(target_roi_row.get("base_problem_id")) == base and str(target_roi_row.get("cell_id")) == cell_id,
        str(irrelevant_roi_row.get("base_problem_id")) == base and str(irrelevant_roi_row.get("cell_id")) == cell_id,
    ]
    if not all(identities):
        raise ValueError("Historical reference rows do not match the frozen calibration cell")
    aligned_o = float(kv_row["conditions"]["O"]["aligned_native"])
    aligned_c = float(kv_row["conditions"]["C"]["aligned_native"])
    target_effect = float(target_roi_row["BPR"])
    irrelevant_effect = float(irrelevant_roi_row["BPR"])
    return {
        "base_problem_id": base,
        "target_id": target,
        "cell_id": cell_id,
        "stratum": str(cell["effect_stratum"]),
        "visual_content_effect": aligned_o + aligned_c,
        "target_roi_effect": target_effect,
        "irrelevant_roi_effect": irrelevant_effect,
        "target_minus_irrelevant_roi": target_effect - irrelevant_effect,
        "suppression_loss": float(kv_row["sign_aligned"]["suppression_loss"]),
        "kv_rescue_gain": float(kv_row["sign_aligned"]["rescue_gain"]),
        "current_residual_rescue_gain": float(residual_row["sign_aligned"]["rescue_gain"]),
        "archived_anchor_effect": float(cell.get("archived_anchor_effect", kv_row["sign_aligned"]["suppression_loss"])),
        "reference_sources": {
            "content_and_kv": "outputs/stage3c7/phase_a_cache/kv_results.jsonl",
            "residual": "outputs/stage3c7/phase_b_joint/residual_only_results.jsonl",
            "target_roi": "outputs/stage3b7r/scoring/target_roi_results.jsonl",
            "irrelevant_roi": "outputs/stage3b7r/scoring/irrelevant_roi_results.jsonl",
        },
    }


__all__ = ["extract_a5000_reference", "target_cell_id"]
