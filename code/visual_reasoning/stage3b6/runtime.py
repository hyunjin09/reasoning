"""Full-sequence Stage 3B.6 source-conditioned logical-head scoring."""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

from visual_reasoning.stage3a.runtime import score_candidate
from visual_reasoning.stage3b4.runtime import absolute_intervention_position
from visual_reasoning.stage3b6.heads import (
    CaptureQwenHeadState,
    HybridQueryHeadIntervention,
)


CANDIDATES = ("original_candidate", "counterfactual_candidate")


def capture_candidate_head_state(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_token_ids: Sequence[int],
    intervention_generated_index: int,
    layer_index: int,
    attention_groups: dict[str, Sequence[int]],
    seed: int,
) -> dict[str, Any]:
    position = absolute_intervention_position(
        prompt_length=int(prepared["input_ids"].shape[1]),
        intervention_generated_index=intervention_generated_index,
    )
    capture = CaptureQwenHeadState(
        model=model,
        layer_index=layer_index,
        position=position,
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


def capture_preference_head_states(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_original_ids: Sequence[int],
    candidate_counterfactual_ids: Sequence[int],
    intervention_generated_index: int,
    layer_index: int,
    attention_groups: dict[str, Sequence[int]],
    seed: int,
) -> dict[str, Any]:
    rows = {
        "original_candidate": capture_candidate_head_state(
            model=model,
            prepared=prepared,
            context_token_ids=context_token_ids,
            candidate_token_ids=candidate_original_ids,
            intervention_generated_index=intervention_generated_index,
            layer_index=layer_index,
            attention_groups=attention_groups,
            seed=seed,
        ),
        "counterfactual_candidate": capture_candidate_head_state(
            model=model,
            prepared=prepared,
            context_token_ids=context_token_ids,
            candidate_token_ids=candidate_counterfactual_ids,
            intervention_generated_index=intervention_generated_index,
            layer_index=layer_index,
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
        "current_absolute_position": rows["original_candidate"][
            "current_absolute_position"
        ],
    }


def score_candidate_with_hybrid_heads(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_token_ids: Sequence[int],
    intervention_generated_index: int,
    layer_index: int,
    selected_heads: Sequence[int],
    source_state: dict[str, Any],
    source_positions: Sequence[int],
    attention_groups: dict[str, Sequence[int]],
    seed: int,
) -> dict[str, Any]:
    position = absolute_intervention_position(
        prompt_length=int(prepared["input_ids"].shape[1]),
        intervention_generated_index=intervention_generated_index,
    )
    patch = HybridQueryHeadIntervention(
        model=model,
        layer_index=layer_index,
        position=position,
        selected_heads=selected_heads,
        source_key=source_state["key"],
        source_value=source_state["value"],
        source_positions=source_positions,
        attention_groups=attention_groups,
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
        raise RuntimeError("Hybrid head intervention did not execute exactly once")
    score["head_patch_audit"] = copy.deepcopy(patch.audit[0])
    return score


def score_preference_with_hybrid_heads(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_original_ids: Sequence[int],
    candidate_counterfactual_ids: Sequence[int],
    intervention_generated_index: int,
    layer_index: int,
    selected_heads: Sequence[int],
    source_states_by_candidate: dict[str, dict[str, Any]],
    source_positions: Sequence[int],
    attention_groups: dict[str, Sequence[int]],
    seed: int,
) -> dict[str, Any]:
    original = score_candidate_with_hybrid_heads(
        model=model,
        prepared=prepared,
        context_token_ids=context_token_ids,
        candidate_token_ids=candidate_original_ids,
        intervention_generated_index=intervention_generated_index,
        layer_index=layer_index,
        selected_heads=selected_heads,
        source_state=source_states_by_candidate["original_candidate"],
        source_positions=source_positions,
        attention_groups=attention_groups,
        seed=seed,
    )
    counterfactual = score_candidate_with_hybrid_heads(
        model=model,
        prepared=prepared,
        context_token_ids=context_token_ids,
        candidate_token_ids=candidate_counterfactual_ids,
        intervention_generated_index=intervention_generated_index,
        layer_index=layer_index,
        selected_heads=selected_heads,
        source_state=source_states_by_candidate["counterfactual_candidate"],
        source_positions=source_positions,
        attention_groups=attention_groups,
        seed=seed,
    )
    return {
        "original_candidate": original,
        "counterfactual_candidate": counterfactual,
        "L_o": float(original["mean_log_probability"]),
        "L_c": float(counterfactual["mean_log_probability"]),
        "D": float(original["mean_log_probability"] - counterfactual["mean_log_probability"]),
        "all_query_head_selectivity_valid": bool(
            original["head_patch_audit"]["query_head_selectivity_valid"]
            and counterfactual["head_patch_audit"]["query_head_selectivity_valid"]
        ),
        "all_source_group_isolation_valid": bool(
            original["head_patch_audit"]["source_group_isolation_valid"]
            and counterfactual["head_patch_audit"]["source_group_isolation_valid"]
        ),
    }


__all__ = [
    "CANDIDATES", "capture_candidate_head_state", "capture_preference_head_states",
    "score_candidate_with_hybrid_heads", "score_preference_with_hybrid_heads",
]
