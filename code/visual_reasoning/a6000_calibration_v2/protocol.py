"""Pure prospective path-selection rules for A6000 calibration v2."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import torch


def summarize_tensor_pair(left: torch.Tensor, right: torch.Tensor) -> dict[str, Any]:
    if left.shape != right.shape:
        raise ValueError("Diagnostic tensors must have matching shapes")
    delta = left.float() - right.float()
    return {
        "shape": list(left.shape),
        "exact": bool(torch.equal(left, right)),
        "max_abs_delta": float(delta.abs().max().item()) if delta.numel() else 0.0,
        "finite": bool(torch.isfinite(left).all().item() and torch.isfinite(right).all().item()),
    }


def validate_stress_manifest(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if len(rows) != 6:
        raise ValueError("P1 stress manifest must contain exactly six cases")
    bases = [str(row["base_problem_id"]) for row in rows]
    if len(set(bases)) != 6:
        raise ValueError("P1 stress cases must use six unique base problems")
    if any(bool(row.get("selection_used_attention")) for row in rows):
        raise ValueError("P1 stress selection may not use attention")
    if any(bool(row.get("selection_used_causal_effect")) for row in rows):
        raise ValueError("P1 stress selection may not use causal effects")
    if any(not bool(row.get("complete")) or not bool(row.get("normal_termination")) for row in rows):
        raise ValueError("P1 stress cases must be normally completed persisted trajectories")
    if any(int(row["candidate_length"]) < 1 for row in rows):
        raise ValueError("P1 candidates must be nonempty")
    if any(
        len(row["original_suffix_ids"]) != int(row["candidate_length"])
        or len(row["counterfactual_suffix_ids"]) != int(row["candidate_length"])
        for row in rows
    ):
        raise ValueError("P1 candidate lengths do not match the frozen manifest")
    return {
        "passed": True,
        "case_count": len(rows),
        "unique_base_count": len(set(bases)),
        "selection_used_attention": False,
        "selection_used_causal_effect": False,
        "longest_prefix_token_count": max(int(row["stress_prefix_token_count"]) for row in rows),
        "largest_visual_token_count": max(int(row["visual_token_count"]) for row in rows),
    }


def decide_p1(
    rows: Sequence[Mapping[str, Any]], *, expected_count: int, memory_fraction_max: float,
) -> dict[str, Any]:
    if expected_count < 1 or not 0 < memory_fraction_max < 1:
        raise ValueError("Invalid P1 decision parameters")
    failures = []
    for row in rows:
        fraction = row.get("peak_reserved_vram_fraction")
        reasons = []
        if bool(row.get("oom")):
            reasons.append("oom")
        if not bool(row.get("finite")):
            reasons.append("nonfinite")
        if not bool(row.get("deterministic")):
            reasons.append("nondeterministic")
        if not bool(row.get("backend_unchanged")):
            reasons.append("backend_changed")
        if bool(row.get("silent_truncation")):
            reasons.append("silent_truncation")
        if fraction is not None and float(fraction) > memory_fraction_max:
            reasons.append("reserved_vram_margin_exceeded")
        if reasons:
            failures.append({"base_problem_id": str(row["base_problem_id"]), "reasons": reasons})
    if failures:
        return {
            "status": "NOT_FEASIBLE",
            "selected_path": "P2_REQUIRED",
            "completed_case_count": len(rows),
            "expected_case_count": expected_count,
            "memory_fraction_max": float(memory_fraction_max),
            "failures": failures,
            "conclusive_early_failure": any("oom" in row["reasons"] for row in failures),
            "selection_used_scientific_effects": False,
        }
    if len(rows) != expected_count:
        return {
            "status": "INCOMPLETE",
            "selected_path": None,
            "completed_case_count": len(rows),
            "expected_case_count": expected_count,
            "memory_fraction_max": float(memory_fraction_max),
            "failures": [],
            "conclusive_early_failure": False,
            "selection_used_scientific_effects": False,
        }
    return {
        "status": "FEASIBLE",
        "selected_path": "P1",
        "completed_case_count": len(rows),
        "expected_case_count": expected_count,
        "memory_fraction_max": float(memory_fraction_max),
        "failures": [],
        "conclusive_early_failure": False,
        "selection_used_scientific_effects": False,
    }


def select_streaming_chunk(
    rows: Sequence[Mapping[str, Any]], *, candidates_descending: Sequence[int],
    expected_bases: set[str], memory_fraction_max: float,
) -> dict[str, Any]:
    candidates = [int(value) for value in candidates_descending]
    if not candidates or candidates != sorted(set(candidates), reverse=True):
        raise ValueError("Streaming chunk candidates must be unique and descending")
    if not expected_bases or not 0 < memory_fraction_max < 1:
        raise ValueError("Invalid streaming chunk decision parameters")
    grouped = {chunk: {} for chunk in candidates}
    for row in rows:
        chunk = int(row["chunk_size"])
        base = str(row["base_problem_id"])
        if chunk not in grouped or base not in expected_bases:
            raise ValueError("Streaming stress row is outside the frozen decision set")
        if base in grouped[chunk]:
            raise ValueError("Duplicate streaming stress row")
        grouped[chunk][base] = row
    diagnostics = []
    incomplete = False
    for chunk in candidates:
        selected = grouped[chunk]
        missing = sorted(expected_bases - set(selected))
        failed = []
        for base, row in selected.items():
            fraction = row.get("peak_reserved_vram_fraction")
            reasons = []
            if bool(row.get("oom")):
                reasons.append("oom")
            if not bool(row.get("finite")):
                reasons.append("nonfinite")
            if not bool(row.get("backend_unchanged")):
                reasons.append("backend_changed")
            if fraction is not None and float(fraction) > memory_fraction_max:
                reasons.append("reserved_vram_margin_exceeded")
            if reasons:
                failed.append({"base_problem_id": base, "reasons": reasons})
        diagnostics.append({
            "chunk_size": chunk,
            "completed_base_count": len(selected),
            "missing_bases": missing,
            "failures": failed,
        })
        if not missing and not failed:
            return {
                "status": "SELECTED",
                "selected_chunk_size": chunk,
                "memory_fraction_max": float(memory_fraction_max),
                "selection_uses_scientific_effects": False,
                "per_example_chunk_switching": False,
                "candidate_diagnostics": diagnostics,
            }
        incomplete |= bool(missing)
    return {
        "status": "INCOMPLETE" if incomplete else "NO_LISTED_CHUNK_FITS",
        "selected_chunk_size": None,
        "memory_fraction_max": float(memory_fraction_max),
        "selection_uses_scientific_effects": False,
        "per_example_chunk_switching": False,
        "candidate_diagnostics": diagnostics,
    }


def token_by_token_is_unlocked(
    rows: Sequence[Mapping[str, Any]], *, candidates_descending: Sequence[int],
    gate_base: str, memory_fraction_max: float,
) -> bool:
    """Return whether every frozen chunk is conclusively unsafe on one gate case."""

    candidates = [int(value) for value in candidates_descending]
    if not candidates or candidates != sorted(set(candidates), reverse=True):
        raise ValueError("Streaming chunk candidates must be unique and descending")
    if not 0 < memory_fraction_max < 1:
        raise ValueError("Invalid streaming memory threshold")
    by_chunk = {
        int(row["chunk_size"]): row
        for row in rows
        if str(row["base_problem_id"]) == str(gate_base)
    }
    for chunk in candidates:
        row = by_chunk.get(chunk)
        if row is None:
            return False
        fraction = row.get("peak_reserved_vram_fraction")
        failed = (
            bool(row.get("oom"))
            or not bool(row.get("finite"))
            or not bool(row.get("backend_unchanged"))
            or (fraction is not None and float(fraction) > memory_fraction_max)
        )
        if not failed:
            return False
    return True


__all__ = [
    "decide_p1",
    "select_streaming_chunk",
    "summarize_tensor_pair",
    "token_by_token_is_unlocked",
    "validate_stress_manifest",
]
