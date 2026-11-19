"""Full-sequence scoring for Stage 3B.7 spatial and K/V interventions."""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

from visual_reasoning.stage3a.runtime import score_candidate
from visual_reasoning.stage3b4.runtime import absolute_intervention_position
from visual_reasoning.stage3b7.heads import HybridQueryHeadKVIntervention


CANDIDATES = ("original_candidate", "counterfactual_candidate")


def score_candidate_with_kv_intervention(
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
    mode: str,
    attention_groups: dict[str, Sequence[int]],
    seed: int,
) -> dict[str, Any]:
    position = absolute_intervention_position(
        prompt_length=int(prepared["input_ids"].shape[1]),
        intervention_generated_index=intervention_generated_index,
    )
    patch = HybridQueryHeadKVIntervention(
        model=model,
        layer_index=layer_index,
        position=position,
        selected_heads=selected_heads,
        source_key=source_state["key"],
        source_value=source_state["value"],
        source_positions=source_positions,
        mode=mode,
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
        raise RuntimeError("K/V intervention did not execute exactly once")
    score["kv_patch_audit"] = copy.deepcopy(patch.audit[0])
    return score


def score_preference_with_kv_intervention(
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
    mode: str,
    attention_groups: dict[str, Sequence[int]],
    seed: int,
) -> dict[str, Any]:
    original = score_candidate_with_kv_intervention(
        model=model,
        prepared=prepared,
        context_token_ids=context_token_ids,
        candidate_token_ids=candidate_original_ids,
        intervention_generated_index=intervention_generated_index,
        layer_index=layer_index,
        selected_heads=selected_heads,
        source_state=source_states_by_candidate["original_candidate"],
        source_positions=source_positions,
        mode=mode,
        attention_groups=attention_groups,
        seed=seed,
    )
    counterfactual = score_candidate_with_kv_intervention(
        model=model,
        prepared=prepared,
        context_token_ids=context_token_ids,
        candidate_token_ids=candidate_counterfactual_ids,
        intervention_generated_index=intervention_generated_index,
        layer_index=layer_index,
        selected_heads=selected_heads,
        source_state=source_states_by_candidate["counterfactual_candidate"],
        source_positions=source_positions,
        mode=mode,
        attention_groups=attention_groups,
        seed=seed,
    )
    return {
        "original_candidate": original,
        "counterfactual_candidate": counterfactual,
        "L_o": float(original["mean_log_probability"]),
        "L_c": float(counterfactual["mean_log_probability"]),
        "D": float(
            original["mean_log_probability"]
            - counterfactual["mean_log_probability"]
        ),
        "all_query_head_selectivity_valid": bool(
            original["kv_patch_audit"]["query_head_selectivity_valid"]
            and counterfactual["kv_patch_audit"]["query_head_selectivity_valid"]
        ),
        "all_source_group_isolation_valid": bool(
            original["kv_patch_audit"]["source_group_isolation_valid"]
            and counterfactual["kv_patch_audit"]["source_group_isolation_valid"]
        ),
    }


__all__ = [
    "CANDIDATES",
    "score_candidate_with_kv_intervention",
    "score_preference_with_kv_intervention",
]
