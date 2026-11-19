"""Full-sequence eager scoring with captured or switched visual K/V."""

from __future__ import annotations

import copy
from typing import Any, Sequence

import torch

from visual_reasoning.stage0.modeling import _reset_generation_state
from visual_reasoning.stage3a.runtime import score_candidate
from visual_reasoning.stage2b.runtime import extend_prepared_inputs
from visual_reasoning.stage3b2.switching import (
    CaptureVisualKV,
    VisualSourceSwitch,
    valid_switch_audit,
)


def stage3a_divergent_tail_exact(
    observed: dict[str, Any],
    expected: dict[str, Any],
    *,
    common_prefix_token_count: int,
) -> bool:
    start = int(common_prefix_token_count)
    return bool(
        observed["candidate_token_ids"] == expected["candidate_token_ids"][start:]
        and observed["token_log_probabilities"] == expected["token_log_probabilities"][start:]
    )


def classify_first_discriminative_token(
    generated_token_ids: Sequence[int],
    *,
    original_token_id: int,
    counterfactual_token_id: int,
) -> str:
    if not generated_token_ids:
        return "no_token"
    first = int(generated_token_ids[0])
    if first == int(original_token_id):
        return "original"
    if first == int(counterfactual_token_id):
        return "counterfactual"
    return "other"


def capture_audit_valid(
    audit: Sequence[dict[str, Any]],
    *,
    visual_indices: Sequence[int],
    layer_count: int,
    kv_heads: int,
    head_dim: int,
) -> bool:
    visual = sorted({int(value) for value in visual_indices})
    expected_shape = [1, int(kv_heads), len(visual), int(head_dim)]
    return bool(
        len(audit) == int(layer_count)
        and sorted(int(row["layer_index"]) for row in audit) == list(range(int(layer_count)))
        and all(row["captured_visual_key_shape"] == expected_shape for row in audit)
        and all(row["visual_indices"] == visual for row in audit)
        and all(row["post_rope_key"] and row["value_projection"] for row in audit)
    )


def capture_candidate_visual_kv(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_token_ids: Sequence[int],
    visual_indices: Sequence[int],
    seed: int,
) -> dict[str, Any]:
    capture = CaptureVisualKV(model=model, visual_indices=visual_indices)
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
        "source_layers": capture.complete_layers(),
        "capture_audit": copy.deepcopy(capture.audit),
    }


@torch.inference_mode()
def capture_context_visual_kv(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    visual_indices: Sequence[int],
    seed: int,
) -> dict[str, Any]:
    """Capture donor visual K/V at the exact rollout-prefill sequence shape."""

    context = [int(value) for value in context_token_ids]
    if not context:
        raise ValueError("Rollout visual capture requires a nonempty generated context")
    batch = extend_prepared_inputs(prepared, context)
    capture = CaptureVisualKV(model=model, visual_indices=visual_indices)
    _reset_generation_state(model, seed=int(seed))
    with capture:
        output = model(**batch, use_cache=False, return_dict=True, logits_to_keep=1)
    layers = capture.complete_layers()
    audit = copy.deepcopy(capture.audit)
    del output, batch
    return {"source_layers": layers, "capture_audit": audit}


def capture_preference_visual_kv(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_original_ids: Sequence[int],
    candidate_counterfactual_ids: Sequence[int],
    visual_indices: Sequence[int],
    seed: int,
) -> dict[str, Any]:
    original = capture_candidate_visual_kv(
        model=model,
        prepared=prepared,
        context_token_ids=context_token_ids,
        candidate_token_ids=candidate_original_ids,
        visual_indices=visual_indices,
        seed=seed,
    )
    counterfactual = capture_candidate_visual_kv(
        model=model,
        prepared=prepared,
        context_token_ids=context_token_ids,
        candidate_token_ids=candidate_counterfactual_ids,
        visual_indices=visual_indices,
        seed=seed,
    )
    original_score = original["score"]
    counterfactual_score = counterfactual["score"]
    return {
        "original_candidate": original_score,
        "counterfactual_candidate": counterfactual_score,
        "L_o": float(original_score["mean_log_probability"]),
        "L_c": float(counterfactual_score["mean_log_probability"]),
        "D": float(
            original_score["mean_log_probability"]
            - counterfactual_score["mean_log_probability"]
        ),
        "source_layers": {
            "original_candidate": original["source_layers"],
            "counterfactual_candidate": counterfactual["source_layers"],
        },
        "capture_audits": {
            "original_candidate": original["capture_audit"],
            "counterfactual_candidate": counterfactual["capture_audit"],
        },
    }


def score_candidate_with_visual_source(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_token_ids: Sequence[int],
    source_layers: Sequence[tuple[Any, Any]],
    visual_indices: Sequence[int],
    switch_generated_index: int,
    seed: int,
) -> dict[str, Any]:
    prompt_length = int(prepared["input_ids"].shape[1])
    generated_length = len(context_token_ids) + len(candidate_token_ids)
    first_query = prompt_length + int(switch_generated_index) - 1
    switch = VisualSourceSwitch(
        model=model,
        source_layers=source_layers,
        visual_indices=visual_indices,
        first_switched_absolute_query=first_query,
    )
    with switch:
        score = score_candidate(
            model=model,
            prepared=prepared,
            prefix_token_ids=context_token_ids,
            candidate_token_ids=candidate_token_ids,
            seed=seed,
        )
    score["switch_audit"] = copy.deepcopy(switch.audit)
    score["switch_audit_valid"] = valid_switch_audit(
        switch.audit,
        prompt_length=prompt_length,
        generated_sequence_length=generated_length,
        switch_generated_index=int(switch_generated_index),
        visual_indices=visual_indices,
        layer_count=int(model.config.text_config.num_hidden_layers),
    )
    return score


def score_preference_with_visual_source(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_original_ids: Sequence[int],
    candidate_counterfactual_ids: Sequence[int],
    source_layers_by_candidate: dict[str, Sequence[tuple[Any, Any]]],
    visual_indices: Sequence[int],
    switch_generated_index: int,
    seed: int,
) -> dict[str, Any]:
    original = score_candidate_with_visual_source(
        model=model,
        prepared=prepared,
        context_token_ids=context_token_ids,
        candidate_token_ids=candidate_original_ids,
        source_layers=source_layers_by_candidate["original_candidate"],
        visual_indices=visual_indices,
        switch_generated_index=switch_generated_index,
        seed=seed,
    )
    counterfactual = score_candidate_with_visual_source(
        model=model,
        prepared=prepared,
        context_token_ids=context_token_ids,
        candidate_token_ids=candidate_counterfactual_ids,
        source_layers=source_layers_by_candidate["counterfactual_candidate"],
        visual_indices=visual_indices,
        switch_generated_index=switch_generated_index,
        seed=seed,
    )
    return {
        "original_candidate": original,
        "counterfactual_candidate": counterfactual,
        "L_o": float(original["mean_log_probability"]),
        "L_c": float(counterfactual["mean_log_probability"]),
        "D": float(original["mean_log_probability"] - counterfactual["mean_log_probability"]),
        "all_switch_audits_valid": bool(
            original["switch_audit_valid"] and counterfactual["switch_audit_valid"]
        ),
    }
