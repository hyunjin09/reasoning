"""Stage 3C.5 state readouts and carrier interventions."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from contextlib import ExitStack
from typing import Any

import torch

from visual_reasoning.stage3b4.runtime import absolute_intervention_position
from visual_reasoning.stage3b5.boundaries import CaptureCurrentBlockBoundaries
from visual_reasoning.stage3c3.runtime import score_evidence_suffix
from visual_reasoning.stage3c4.runtime import SourceContributionWindowPatch


def summarize_state(state: torch.Tensor) -> dict[str, Any]:
    value = state.detach().float().cpu().contiguous()
    return {
        "shape": list(value.shape),
        "dtype": "float32",
        "l2_norm": float(torch.linalg.vector_norm(value).item()),
        "mean": float(value.mean().item()),
        "finite": bool(torch.isfinite(value).all().item()),
        "sha256_float32": hashlib.sha256(value.numpy().tobytes()).hexdigest(),
    }


def _preference(original: Mapping[str, Any], counterfactual: Mapping[str, Any]) -> dict[str, Any]:
    lo = float(original["mean_log_probability"])
    lc = float(counterfactual["mean_log_probability"])
    return {"L_o": lo, "L_c": lc, "D": lo - lc, "finite": bool(original["finite"] and counterfactual["finite"])}


@torch.inference_mode()
def score_preference_with_tpre_readout(
    *,
    model: Any,
    prepared: dict[str, Any],
    prefix_token_ids: Sequence[int],
    bridge_token_ids: Sequence[int],
    original_suffix_ids: Sequence[int],
    counterfactual_suffix_ids: Sequence[int],
    current_generated_index: int,
    intervention_generated_indices: Sequence[int],
    intervention_layers: Sequence[int],
    source_positions: Sequence[int],
    selected_heads: Sequence[int],
    gain: float,
    readout_layer: int,
    seed: int,
) -> tuple[dict[str, Any], dict[str, torch.Tensor]]:
    """Score one arm while retaining raw h_pre/h_post_attn at ``t*``."""

    prompt_length = int(prepared["input_ids"].shape[1])
    current_position = absolute_intervention_position(
        prompt_length=prompt_length,
        intervention_generated_index=int(current_generated_index),
    )
    query_positions = [
        absolute_intervention_position(
            prompt_length=prompt_length,
            intervention_generated_index=int(index),
        )
        for index in sorted({int(value) for value in intervention_generated_indices})
    ]
    layers = sorted({int(value) for value in intervention_layers})
    candidates: dict[str, Any] = {}
    candidate_audits: dict[str, list[dict[str, Any]]] = {}
    state_summaries: dict[str, Any] = {}
    tensors: dict[str, torch.Tensor] = {}
    for candidate_name, suffix in (
        ("original_candidate", original_suffix_ids),
        ("counterfactual_candidate", counterfactual_suffix_ids),
    ):
        patches = [
            SourceContributionWindowPatch(
                model=model,
                layer_index=layer,
                query_positions=query_positions,
                selected_heads=selected_heads,
                source_positions=source_positions,
                gain=float(gain),
            )
            for layer in layers
        ]
        capture = CaptureCurrentBlockBoundaries(
            model=model,
            position=current_position,
            layer_indices=[int(readout_layer)],
        )
        with ExitStack() as stack:
            stack.enter_context(capture)
            for patch in patches:
                stack.enter_context(patch)
            candidates[candidate_name] = score_evidence_suffix(
                model=model,
                prepared=prepared,
                prefix_token_ids=prefix_token_ids,
                bridge_token_ids=bridge_token_ids,
                suffix_token_ids=suffix,
                seed=seed,
            )
        candidate_audits[candidate_name] = [patch.complete() for patch in patches]
        states = capture.complete_states()
        state_summaries[candidate_name] = {}
        for boundary in ("h_pre", "h_post_attn"):
            tensor = states[boundary][int(readout_layer)].detach().float().cpu()
            tensors[f"{candidate_name}.{boundary}"] = tensor
            state_summaries[candidate_name][boundary] = summarize_state(tensor)
        state_summaries[candidate_name]["candidate_log_probability_readout"] = {
            "first_token_log_probability": float(candidates[candidate_name]["token_log_probabilities"][0]),
            "mean_log_probability": float(candidates[candidate_name]["mean_log_probability"]),
        }
    return {
        **_preference(candidates["original_candidate"], candidates["counterfactual_candidate"]),
        "original_candidate": candidates["original_candidate"],
        "counterfactual_candidate": candidates["counterfactual_candidate"],
        "candidate_audits": candidate_audits,
        "state_readouts": state_summaries,
        "current_generated_index": int(current_generated_index),
        "current_absolute_position": current_position,
        "intervention_generated_indices": sorted({int(value) for value in intervention_generated_indices}),
        "absolute_query_positions": query_positions,
        "layer_indices": layers,
        "readout_layer": int(readout_layer),
        "source_positions": sorted({int(value) for value in source_positions}),
        "selected_heads": sorted({int(value) for value in selected_heads}),
        "gain": float(gain),
    }, tensors


@torch.inference_mode()
def score_native_preference_with_readout(
    *,
    model: Any,
    prepared: dict[str, Any],
    prefix_token_ids: Sequence[int],
    bridge_token_ids: Sequence[int],
    original_suffix_ids: Sequence[int],
    counterfactual_suffix_ids: Sequence[int],
    current_generated_index: int,
    readout_layer: int,
    seed: int,
) -> tuple[dict[str, Any], dict[str, torch.Tensor]]:
    prompt_length = int(prepared["input_ids"].shape[1])
    current_position = absolute_intervention_position(
        prompt_length=prompt_length,
        intervention_generated_index=int(current_generated_index),
    )
    candidates: dict[str, Any] = {}
    summaries: dict[str, Any] = {}
    tensors: dict[str, torch.Tensor] = {}
    for candidate_name, suffix in (
        ("original_candidate", original_suffix_ids),
        ("counterfactual_candidate", counterfactual_suffix_ids),
    ):
        capture = CaptureCurrentBlockBoundaries(
            model=model, position=current_position, layer_indices=[int(readout_layer)]
        )
        with capture:
            candidates[candidate_name] = score_evidence_suffix(
                model=model,
                prepared=prepared,
                prefix_token_ids=prefix_token_ids,
                bridge_token_ids=bridge_token_ids,
                suffix_token_ids=suffix,
                seed=seed,
            )
        states = capture.complete_states()
        summaries[candidate_name] = {}
        for boundary in ("h_pre", "h_post_attn"):
            tensor = states[boundary][int(readout_layer)].detach().float().cpu()
            tensors[f"{candidate_name}.{boundary}"] = tensor
            summaries[candidate_name][boundary] = summarize_state(tensor)
        summaries[candidate_name]["candidate_log_probability_readout"] = {
            "first_token_log_probability": float(candidates[candidate_name]["token_log_probabilities"][0]),
            "mean_log_probability": float(candidates[candidate_name]["mean_log_probability"]),
        }
    return {
        **_preference(candidates["original_candidate"], candidates["counterfactual_candidate"]),
        "original_candidate": candidates["original_candidate"],
        "counterfactual_candidate": candidates["counterfactual_candidate"],
        "state_readouts": summaries,
        "current_generated_index": int(current_generated_index),
        "current_absolute_position": current_position,
        "readout_layer": int(readout_layer),
    }, tensors


__all__ = [
    "score_native_preference_with_readout",
    "score_preference_with_tpre_readout",
    "summarize_state",
]
