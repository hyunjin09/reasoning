"""Full-sequence scoring for Stage 3B.8 ROI-derived Value interventions."""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

import torch

from visual_reasoning.stage3a.runtime import score_candidate
from visual_reasoning.stage3b4.runtime import absolute_intervention_position
from visual_reasoning.stage3b8.heads import (
    CaptureQwenROIValueState,
    ROIValueDeltaIntervention,
)


CANDIDATES = ("original_candidate", "counterfactual_candidate")


def capture_candidate_value_state(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_token_ids: Sequence[int],
    intervention_generated_index: int,
    layer_index: int,
    selected_query_heads: Sequence[int],
    roi_positions: Sequence[int],
    attention_groups: dict[str, Sequence[int]],
    seed: int,
) -> dict[str, Any]:
    position = absolute_intervention_position(
        prompt_length=int(prepared["input_ids"].shape[1]),
        intervention_generated_index=intervention_generated_index,
    )
    capture = CaptureQwenROIValueState(
        model=model,
        layer_index=layer_index,
        position=position,
        selected_query_heads=selected_query_heads,
        roi_positions=roi_positions,
        attention_groups=attention_groups,
    )
    with capture:
        score = score_candidate(
            model=model,
            prepared=prepared,
            prefix_token_ids=context_token_ids,
            candidate_token_ids=candidate_token_ids,
            seed=seed,
        )
    return {
        "score": score,
        "state": capture.complete_state(),
        "capture_audit": copy.deepcopy(capture.audit[0]),
        "current_absolute_position": position,
    }


def capture_preference_value_states(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_original_ids: Sequence[int],
    candidate_counterfactual_ids: Sequence[int],
    intervention_generated_index: int,
    layer_index: int,
    selected_query_heads: Sequence[int],
    roi_positions: Sequence[int],
    attention_groups: dict[str, Sequence[int]],
    seed: int,
) -> dict[str, Any]:
    rows = {
        "original_candidate": capture_candidate_value_state(
            model=model,
            prepared=prepared,
            context_token_ids=context_token_ids,
            candidate_token_ids=candidate_original_ids,
            intervention_generated_index=intervention_generated_index,
            layer_index=layer_index,
            selected_query_heads=selected_query_heads,
            roi_positions=roi_positions,
            attention_groups=attention_groups,
            seed=seed,
        ),
        "counterfactual_candidate": capture_candidate_value_state(
            model=model,
            prepared=prepared,
            context_token_ids=context_token_ids,
            candidate_token_ids=candidate_counterfactual_ids,
            intervention_generated_index=intervention_generated_index,
            layer_index=layer_index,
            selected_query_heads=selected_query_heads,
            roi_positions=roi_positions,
            attention_groups=attention_groups,
            seed=seed,
        ),
    }
    original = rows["original_candidate"]["score"]
    counterfactual = rows["counterfactual_candidate"]["score"]
    return {
        "original_candidate": original,
        "counterfactual_candidate": counterfactual,
        "L_o": float(original["mean_log_probability"]),
        "L_c": float(counterfactual["mean_log_probability"]),
        "D": float(original["mean_log_probability"] - counterfactual["mean_log_probability"]),
        "states": {candidate: rows[candidate]["state"] for candidate in CANDIDATES},
        "capture_audits": {
            candidate: rows[candidate]["capture_audit"] for candidate in CANDIDATES
        },
        "current_absolute_position": rows["original_candidate"]["current_absolute_position"],
    }


def score_candidate_with_value_delta(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_token_ids: Sequence[int],
    intervention_generated_index: int,
    layer_index: int,
    selected_query_heads: Sequence[int],
    recipient_state: dict[str, torch.Tensor],
    donor_state: dict[str, torch.Tensor],
    roi_positions: Sequence[int],
    dose: float,
    projector_basis: torch.Tensor | None,
    seed: int,
    projector_complement: bool = False,
) -> dict[str, Any]:
    position = absolute_intervention_position(
        prompt_length=int(prepared["input_ids"].shape[1]),
        intervention_generated_index=intervention_generated_index,
    )
    patch = ROIValueDeltaIntervention(
        model=model,
        layer_index=layer_index,
        position=position,
        selected_query_heads=selected_query_heads,
        dose=dose,
        expected_recipient_state=recipient_state,
        donor_state=donor_state,
        roi_positions=roi_positions,
        projector_basis=projector_basis,
        projector_complement=projector_complement,
    )
    with patch:
        score = score_candidate(
            model=model,
            prepared=prepared,
            prefix_token_ids=context_token_ids,
            candidate_token_ids=candidate_token_ids,
            seed=seed,
        )
    if len(patch.audit) != 1:
        raise RuntimeError("ROI Value intervention did not execute exactly once")
    score["value_patch_audit"] = copy.deepcopy(patch.audit[0])
    if patch.full_delta is None or patch.applied_delta is None:
        raise RuntimeError("ROI Value intervention did not retain its exact delta")
    score["_full_delta"] = patch.full_delta
    score["_applied_delta"] = patch.applied_delta
    return score


def score_preference_with_value_delta(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_original_ids: Sequence[int],
    candidate_counterfactual_ids: Sequence[int],
    intervention_generated_index: int,
    layer_index: int,
    selected_query_heads: Sequence[int],
    recipient_states_by_candidate: dict[str, dict[str, torch.Tensor]],
    donor_states_by_candidate: dict[str, dict[str, torch.Tensor]],
    roi_positions: Sequence[int],
    dose: float,
    projector_basis: torch.Tensor | None,
    seed: int,
    projector_complement: bool = False,
    return_vectors: bool = False,
) -> dict[str, Any]:
    original = score_candidate_with_value_delta(
        model=model,
        prepared=prepared,
        context_token_ids=context_token_ids,
        candidate_token_ids=candidate_original_ids,
        intervention_generated_index=intervention_generated_index,
        layer_index=layer_index,
        selected_query_heads=selected_query_heads,
        recipient_state=recipient_states_by_candidate["original_candidate"],
        donor_state=donor_states_by_candidate["original_candidate"],
        roi_positions=roi_positions,
        dose=dose,
        projector_basis=projector_basis,
        projector_complement=projector_complement,
        seed=seed,
    )
    counterfactual = score_candidate_with_value_delta(
        model=model,
        prepared=prepared,
        context_token_ids=context_token_ids,
        candidate_token_ids=candidate_counterfactual_ids,
        intervention_generated_index=intervention_generated_index,
        layer_index=layer_index,
        selected_query_heads=selected_query_heads,
        recipient_state=recipient_states_by_candidate["counterfactual_candidate"],
        donor_state=donor_states_by_candidate["counterfactual_candidate"],
        roi_positions=roi_positions,
        dose=dose,
        projector_basis=projector_basis,
        projector_complement=projector_complement,
        seed=seed,
    )
    audits = [original["value_patch_audit"], counterfactual["value_patch_audit"]]
    full_vectors = {
        "original_candidate": original.pop("_full_delta"),
        "counterfactual_candidate": counterfactual.pop("_full_delta"),
    }
    applied_vectors = {
        "original_candidate": original.pop("_applied_delta"),
        "counterfactual_candidate": counterfactual.pop("_applied_delta"),
    }
    result = {
        "original_candidate": original,
        "counterfactual_candidate": counterfactual,
        "L_o": float(original["mean_log_probability"]),
        "L_c": float(counterfactual["mean_log_probability"]),
        "D": float(original["mean_log_probability"] - counterfactual["mean_log_probability"]),
        "all_query_head_selectivity_valid": all(
            set(audit["changed_query_heads"]).issubset(set(audit["selected_query_heads"]))
            and audit["nonselected_head_max_abs_delta"] == 0.0
            for audit in audits
        ),
        "all_recipient_tensor_alignment_exact": all(
            audit["recipient_attention_exact"] and audit["recipient_roi_value_exact"]
            for audit in audits
        ),
    }
    if return_vectors:
        result["_full_delta_by_candidate"] = full_vectors
        result["_applied_delta_by_candidate"] = applied_vectors
    return result


__all__ = [
    "CANDIDATES",
    "capture_candidate_value_state",
    "capture_preference_value_states",
    "score_candidate_with_value_delta",
    "score_preference_with_value_delta",
]
