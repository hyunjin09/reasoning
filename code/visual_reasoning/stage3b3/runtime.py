"""Full-sequence scoring for Stage 3B.3 layer and residual interventions."""

from __future__ import annotations

import copy
from typing import Any, Sequence

from visual_reasoning.stage3a.runtime import score_candidate
from visual_reasoning.stage3b3.residual import (
    CaptureCurrentResiduals,
    CurrentPositionResidualPatch,
    valid_residual_patch_audit,
)
from visual_reasoning.stage3b3.switching import (
    LayerVisualSourceSwitch,
    valid_layer_switch_audit,
)


def score_candidate_with_layer_visual_source(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_token_ids: Sequence[int],
    source_layers: Sequence[tuple[Any, Any]],
    visual_indices: Sequence[int],
    switch_generated_index: int,
    selected_layers: Sequence[int],
    seed: int,
) -> dict[str, Any]:
    prompt_length = int(prepared["input_ids"].shape[1])
    generated_length = len(context_token_ids) + len(candidate_token_ids)
    intervention = LayerVisualSourceSwitch(
        model=model,
        source_layers=source_layers,
        visual_indices=visual_indices,
        first_switched_absolute_query=prompt_length + int(switch_generated_index) - 1,
        selected_layers=selected_layers,
    )
    with intervention:
        score = score_candidate(
            model=model,
            prepared=prepared,
            prefix_token_ids=context_token_ids,
            candidate_token_ids=candidate_token_ids,
            seed=seed,
        )
    score["layer_switch_audit"] = copy.deepcopy(intervention.audit)
    score["layer_switch_audit_valid"] = valid_layer_switch_audit(
        intervention.audit,
        prompt_length=prompt_length,
        generated_sequence_length=generated_length,
        switch_generated_index=int(switch_generated_index),
        visual_indices=visual_indices,
        layer_count=int(model.config.text_config.num_hidden_layers),
        selected_layers=selected_layers,
    )
    return score


def score_preference_with_layer_visual_source(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_original_ids: Sequence[int],
    candidate_counterfactual_ids: Sequence[int],
    source_layers_by_candidate: dict[str, Sequence[tuple[Any, Any]]],
    visual_indices: Sequence[int],
    switch_generated_index: int,
    selected_layers: Sequence[int],
    seed: int,
) -> dict[str, Any]:
    original = score_candidate_with_layer_visual_source(
        model=model,
        prepared=prepared,
        context_token_ids=context_token_ids,
        candidate_token_ids=candidate_original_ids,
        source_layers=source_layers_by_candidate["original_candidate"],
        visual_indices=visual_indices,
        switch_generated_index=switch_generated_index,
        selected_layers=selected_layers,
        seed=seed,
    )
    counterfactual = score_candidate_with_layer_visual_source(
        model=model,
        prepared=prepared,
        context_token_ids=context_token_ids,
        candidate_token_ids=candidate_counterfactual_ids,
        source_layers=source_layers_by_candidate["counterfactual_candidate"],
        visual_indices=visual_indices,
        switch_generated_index=switch_generated_index,
        selected_layers=selected_layers,
        seed=seed,
    )
    return {
        "original_candidate": original,
        "counterfactual_candidate": counterfactual,
        "L_o": float(original["mean_log_probability"]),
        "L_c": float(counterfactual["mean_log_probability"]),
        "D": float(original["mean_log_probability"] - counterfactual["mean_log_probability"]),
        "all_layer_switch_audits_valid": bool(
            original["layer_switch_audit_valid"] and counterfactual["layer_switch_audit_valid"]
        ),
    }


def capture_candidate_current_residuals(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_token_ids: Sequence[int],
    layer_indices: Sequence[int],
    seed: int,
) -> dict[str, Any]:
    prompt_length = int(prepared["input_ids"].shape[1])
    current_position = prompt_length + len(context_token_ids) - 1
    capture = CaptureCurrentResiduals(
        model=model,
        position=current_position,
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
    return {
        "score": score,
        "states": capture.complete_states(),
        "capture_audit": copy.deepcopy(capture.audit),
        "current_absolute_position": current_position,
    }


def capture_preference_current_residuals(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_original_ids: Sequence[int],
    candidate_counterfactual_ids: Sequence[int],
    layer_indices: Sequence[int],
    seed: int,
) -> dict[str, Any]:
    original = capture_candidate_current_residuals(
        model=model,
        prepared=prepared,
        context_token_ids=context_token_ids,
        candidate_token_ids=candidate_original_ids,
        layer_indices=layer_indices,
        seed=seed,
    )
    counterfactual = capture_candidate_current_residuals(
        model=model,
        prepared=prepared,
        context_token_ids=context_token_ids,
        candidate_token_ids=candidate_counterfactual_ids,
        layer_indices=layer_indices,
        seed=seed,
    )
    return {
        "original_candidate": original["score"],
        "counterfactual_candidate": counterfactual["score"],
        "L_o": float(original["score"]["mean_log_probability"]),
        "L_c": float(counterfactual["score"]["mean_log_probability"]),
        "D": float(
            original["score"]["mean_log_probability"]
            - counterfactual["score"]["mean_log_probability"]
        ),
        "states": {
            "original_candidate": original["states"],
            "counterfactual_candidate": counterfactual["states"],
        },
        "capture_audits": {
            "original_candidate": original["capture_audit"],
            "counterfactual_candidate": counterfactual["capture_audit"],
        },
        "current_absolute_position": original["current_absolute_position"],
    }


def score_candidate_with_current_residual(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_token_ids: Sequence[int],
    layer_index: int,
    source_state: Any,
    seed: int,
) -> dict[str, Any]:
    current_position = int(prepared["input_ids"].shape[1]) + len(context_token_ids) - 1
    patch = CurrentPositionResidualPatch(
        model=model,
        layer_index=layer_index,
        position=current_position,
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
    score["residual_patch_audit"] = copy.deepcopy(patch.audit)
    score["residual_patch_audit_valid"] = valid_residual_patch_audit(
        patch.audit,
        layer_index=layer_index,
        position=current_position,
    )
    return score


def score_preference_with_current_residual(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_original_ids: Sequence[int],
    candidate_counterfactual_ids: Sequence[int],
    layer_index: int,
    source_states_by_candidate: dict[str, Any],
    seed: int,
) -> dict[str, Any]:
    original = score_candidate_with_current_residual(
        model=model,
        prepared=prepared,
        context_token_ids=context_token_ids,
        candidate_token_ids=candidate_original_ids,
        layer_index=layer_index,
        source_state=source_states_by_candidate["original_candidate"],
        seed=seed,
    )
    counterfactual = score_candidate_with_current_residual(
        model=model,
        prepared=prepared,
        context_token_ids=context_token_ids,
        candidate_token_ids=candidate_counterfactual_ids,
        layer_index=layer_index,
        source_state=source_states_by_candidate["counterfactual_candidate"],
        seed=seed,
    )
    return {
        "original_candidate": original,
        "counterfactual_candidate": counterfactual,
        "L_o": float(original["mean_log_probability"]),
        "L_c": float(counterfactual["mean_log_probability"]),
        "D": float(original["mean_log_probability"] - counterfactual["mean_log_probability"]),
        "all_residual_patch_audits_valid": bool(
            original["residual_patch_audit_valid"] and counterfactual["residual_patch_audit_valid"]
        ),
    }
