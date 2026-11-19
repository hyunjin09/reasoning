"""Full-sequence preference scoring with exact block-boundary restoration."""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

from visual_reasoning.stage3a.runtime import score_candidate
from visual_reasoning.stage3b4.runtime import absolute_intervention_position
from visual_reasoning.stage3b5.boundaries import (
    BOUNDARIES,
    EXPECTED_DOWNSTREAM,
    CaptureCurrentBlockBoundaries,
    CurrentPositionBoundaryPatch,
    valid_boundary_capture_audit,
    valid_boundary_patch_audit,
)


CANDIDATES = ("original_candidate", "counterfactual_candidate")


def capture_candidate_boundaries(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_token_ids: Sequence[int],
    intervention_generated_index: int,
    layer_indices: Sequence[int],
    seed: int,
) -> dict[str, Any]:
    position = absolute_intervention_position(
        prompt_length=int(prepared["input_ids"].shape[1]),
        intervention_generated_index=intervention_generated_index,
    )
    if intervention_generated_index > len(context_token_ids):
        raise ValueError("Boundary intervention lies after the frozen context")
    capture = CaptureCurrentBlockBoundaries(
        model=model,
        position=position,
        layer_indices=layer_indices,
    )
    with capture:
        score = score_candidate(
            model=model,
            prepared=prepared,
            prefix_token_ids=context_token_ids,
            candidate_token_ids=candidate_token_ids,
            seed=seed,
        )
    states = capture.complete_states()
    return {
        "score": score,
        "states": states,
        "capture_audit": copy.deepcopy(capture.audit),
        "residual_addition_audit": copy.deepcopy(capture.residual_addition_audit),
        "capture_audit_valid": valid_boundary_capture_audit(
            capture.audit,
            layer_indices=layer_indices,
            position=position,
        ),
        "current_absolute_position": position,
    }


def capture_preference_boundaries(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_original_ids: Sequence[int],
    candidate_counterfactual_ids: Sequence[int],
    intervention_generated_index: int,
    layer_indices: Sequence[int],
    seed: int,
) -> dict[str, Any]:
    captures = {
        "original_candidate": capture_candidate_boundaries(
            model=model,
            prepared=prepared,
            context_token_ids=context_token_ids,
            candidate_token_ids=candidate_original_ids,
            intervention_generated_index=intervention_generated_index,
            layer_indices=layer_indices,
            seed=seed,
        ),
        "counterfactual_candidate": capture_candidate_boundaries(
            model=model,
            prepared=prepared,
            context_token_ids=context_token_ids,
            candidate_token_ids=candidate_counterfactual_ids,
            intervention_generated_index=intervention_generated_index,
            layer_indices=layer_indices,
            seed=seed,
        ),
    }
    original = captures["original_candidate"]["score"]
    counterfactual = captures["counterfactual_candidate"]["score"]
    return {
        "original_candidate": original,
        "counterfactual_candidate": counterfactual,
        "L_o": float(original["mean_log_probability"]),
        "L_c": float(counterfactual["mean_log_probability"]),
        "D": float(original["mean_log_probability"] - counterfactual["mean_log_probability"]),
        "states": {
            candidate: captures[candidate]["states"] for candidate in CANDIDATES
        },
        "capture_audits": {
            candidate: captures[candidate]["capture_audit"] for candidate in CANDIDATES
        },
        "residual_addition_audits": {
            candidate: captures[candidate]["residual_addition_audit"]
            for candidate in CANDIDATES
        },
        "all_boundary_capture_audits_valid": all(
            bool(captures[candidate]["capture_audit_valid"])
            for candidate in CANDIDATES
        ),
        "current_absolute_position": captures["original_candidate"]["current_absolute_position"],
    }


def score_candidate_with_boundary(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_token_ids: Sequence[int],
    intervention_generated_index: int,
    layer_index: int,
    boundary: str,
    source_state: Any,
    seed: int,
) -> dict[str, Any]:
    position = absolute_intervention_position(
        prompt_length=int(prepared["input_ids"].shape[1]),
        intervention_generated_index=intervention_generated_index,
    )
    patch = CurrentPositionBoundaryPatch(
        model=model,
        position=position,
        layer_index=layer_index,
        boundary=boundary,
        source_state=source_state,
    )
    with patch:
        score = score_candidate(
            model=model,
            prepared=prepared,
            prefix_token_ids=context_token_ids,
            candidate_token_ids=candidate_token_ids,
            seed=seed,
        )
    audit = copy.deepcopy(patch.audit)
    score["boundary_patch_audit"] = audit
    score["boundary_patch_audit_valid"] = valid_boundary_patch_audit(
        audit,
        layer_index=layer_index,
        boundary=boundary,
        position=position,
        expected_downstream=EXPECTED_DOWNSTREAM[boundary],
    )
    return score


def score_preference_with_boundary(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_original_ids: Sequence[int],
    candidate_counterfactual_ids: Sequence[int],
    intervention_generated_index: int,
    layer_index: int,
    boundary: str,
    source_states_by_candidate: dict[str, dict[str, dict[int, Any]]],
    seed: int,
) -> dict[str, Any]:
    original = score_candidate_with_boundary(
        model=model,
        prepared=prepared,
        context_token_ids=context_token_ids,
        candidate_token_ids=candidate_original_ids,
        intervention_generated_index=intervention_generated_index,
        layer_index=layer_index,
        boundary=boundary,
        source_state=source_states_by_candidate["original_candidate"][boundary][layer_index],
        seed=seed,
    )
    counterfactual = score_candidate_with_boundary(
        model=model,
        prepared=prepared,
        context_token_ids=context_token_ids,
        candidate_token_ids=candidate_counterfactual_ids,
        intervention_generated_index=intervention_generated_index,
        layer_index=layer_index,
        boundary=boundary,
        source_state=source_states_by_candidate["counterfactual_candidate"][boundary][layer_index],
        seed=seed,
    )
    return {
        "original_candidate": original,
        "counterfactual_candidate": counterfactual,
        "L_o": float(original["mean_log_probability"]),
        "L_c": float(counterfactual["mean_log_probability"]),
        "D": float(original["mean_log_probability"] - counterfactual["mean_log_probability"]),
        "all_boundary_patch_audits_valid": bool(
            original["boundary_patch_audit_valid"]
            and counterfactual["boundary_patch_audit_valid"]
        ),
    }


__all__ = [
    "BOUNDARIES", "CANDIDATES", "capture_candidate_boundaries",
    "capture_preference_boundaries", "score_candidate_with_boundary",
    "score_preference_with_boundary", "absolute_intervention_position",
]
