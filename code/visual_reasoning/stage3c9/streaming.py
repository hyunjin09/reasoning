"""Memory-bounded exact cached-prefix scoring for Stage 3C.9.

Long Stage 3C.9 prefixes cannot be evaluated as one dense eager-attention
matrix on the available GPUs. These helpers preserve eager attention and exact
generated-token coordinates while advancing a validated DynamicCache in
frozen, bounded query chunks.
"""

from __future__ import annotations

import copy
import time
from collections.abc import Mapping, Sequence
from contextlib import ExitStack
from dataclasses import dataclass
from typing import Any

import torch

from visual_reasoning.stage0.modeling import _reset_generation_state
from visual_reasoning.stage3a.runtime import summarize_candidate_log_probs
from visual_reasoning.stage3b0.cache import clone_cache
from visual_reasoning.stage3b0.runtime import suffix_position_ids
from visual_reasoning.stage3c4.runtime import SourceContributionWindowPatch
from visual_reasoning.stage3c7.runtime import CANDIDATES

from .runtime import absolute_reasoning_token_position


@dataclass
class StreamingPrefixState:
    cache: Any
    rope_deltas: torch.Tensor
    prompt_length: int
    generated_length: int
    last_logits: torch.Tensor


def _seed_without_clearing_rope(seed: int) -> None:
    torch.manual_seed(int(seed))
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(int(seed))


def release_cuda_allocator_cache(*, enabled: bool = False) -> None:
    """Release only unused CUDA allocator blocks at a fixed chunk boundary."""

    if enabled and torch.cuda.is_available():
        torch.cuda.empty_cache()


def fixed_chunk_ranges(
    *, start: int, end: int, chunk_size: int,
    mandatory_boundaries: Sequence[int] = (),
) -> list[tuple[int, int]]:
    """Build one condition-invariant query partition with optional patch barriers."""

    left, right, size = int(start), int(end), int(chunk_size)
    if left < 0 or right < left or size < 1:
        raise ValueError("Invalid fixed streaming range")
    barriers = sorted({int(value) for value in mandatory_boundaries})
    if any(value <= left or value >= right for value in barriers):
        raise ValueError("Mandatory chunk boundaries must lie strictly inside the range")
    ranges = []
    current = left
    while current < right:
        later_barriers = [value for value in barriers if value > current]
        boundary = min(right, current + size)
        if later_barriers and later_barriers[0] < boundary:
            boundary = later_barriers[0]
        ranges.append((current, boundary))
        current = boundary
    return ranges


@torch.inference_mode()
def prefill_streaming_state(
    *, model: Any, prepared: dict[str, Any], seed: int,
) -> tuple[StreamingPrefixState, dict[str, Any]]:
    """Run the unchanged multimodal prompt and retain its native cache/logit."""

    _reset_generation_state(model, seed=int(seed))
    started = time.perf_counter()
    output = model(**prepared, use_cache=True, return_dict=True, logits_to_keep=1)
    if output.past_key_values is None or output.rope_deltas is None:
        raise RuntimeError("Streaming prefill did not return cache and rope deltas")
    prompt_length = int(prepared["input_ids"].shape[1])
    if int(output.past_key_values.get_seq_length()) != prompt_length:
        raise RuntimeError("Streaming prefill cache length does not equal prompt length")
    state = StreamingPrefixState(
        cache=output.past_key_values,
        rope_deltas=output.rope_deltas.detach().clone(),
        prompt_length=prompt_length,
        generated_length=0,
        last_logits=output.logits[0, -1].detach().clone(),
    )
    audit = {
        "prompt_length": prompt_length,
        "cache_sequence_length": int(state.cache.get_seq_length()),
        "rope_deltas": state.rope_deltas.detach().cpu().tolist(),
        "runtime_seconds": time.perf_counter() - started,
        "prefix_execution": "native_multimodal_prefill",
    }
    del output
    return state, audit


def clone_streaming_state(state: StreamingPrefixState) -> StreamingPrefixState:
    return StreamingPrefixState(
        cache=clone_cache(state.cache),
        rope_deltas=state.rope_deltas.detach().clone(),
        prompt_length=int(state.prompt_length),
        generated_length=int(state.generated_length),
        last_logits=state.last_logits.detach().clone(),
    )


def _position_ids(
    *, state: StreamingPrefixState, length: int, device: torch.device,
) -> torch.Tensor:
    end = int(state.generated_length) + int(length)
    full = suffix_position_ids(
        prompt_length=int(state.prompt_length),
        suffix_length=end,
        rope_deltas=state.rope_deltas,
        device=device,
    )
    return full[:, :, int(state.generated_length):end]


@torch.inference_mode()
def advance_streaming_state(
    *, model: Any, state: StreamingPrefixState, token_ids: Sequence[int],
    seed: int, chunk_size: int = 128, release_allocator_cache: bool = False,
) -> StreamingPrefixState:
    """Advance one state in bounded eager-attention query chunks."""

    ids = [int(value) for value in token_ids]
    if int(chunk_size) < 1:
        raise ValueError("Streaming chunk size must be positive")
    device = state.cache.layers[0].keys.device
    _seed_without_clearing_rope(seed)
    for offset in range(0, len(ids), int(chunk_size)):
        chunk = ids[offset:offset + int(chunk_size)]
        input_ids = torch.tensor([chunk], dtype=torch.long, device=device)
        positions = _position_ids(state=state, length=len(chunk), device=device)
        attention_mask = torch.ones(
            (1, int(state.prompt_length) + int(state.generated_length) + len(chunk)),
            dtype=torch.long,
            device=device,
        )
        model.model.rope_deltas = state.rope_deltas.detach().clone().to(device)
        output = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            position_ids=positions,
            past_key_values=state.cache,
            use_cache=True,
            return_dict=True,
            logits_to_keep=1,
        )
        state.cache = output.past_key_values
        state.generated_length += len(chunk)
        state.last_logits = output.logits[0, -1].detach().clone()
        expected = int(state.prompt_length) + int(state.generated_length)
        if int(state.cache.get_seq_length()) != expected:
            raise RuntimeError("Streaming cache length drifted from generated-token coordinates")
        del output
        release_cuda_allocator_cache(enabled=release_allocator_cache)
    return state


def _cache_layers(cache: Any) -> list[tuple[torch.Tensor, torch.Tensor]]:
    layers = getattr(cache, "layers", None)
    if not isinstance(layers, list) or not layers:
        raise ValueError("Streaming state must expose a nonempty DynamicCache layer list")
    result = []
    for layer_index, layer in enumerate(layers):
        key, value = getattr(layer, "keys", None), getattr(layer, "values", None)
        if not isinstance(key, torch.Tensor) or not isinstance(value, torch.Tensor) or key.shape != value.shape:
            raise ValueError(f"Invalid streaming K/V cache at layer {layer_index}")
        result.append((key, value))
    return result


def snapshot_cache_positions(
    state: StreamingPrefixState, *, absolute_positions: Sequence[int],
) -> dict[int, tuple[torch.Tensor, torch.Tensor]]:
    selected = sorted({int(value) for value in absolute_positions})
    layers = _cache_layers(state.cache)
    if not selected or selected[0] < 0 or selected[-1] >= int(layers[0][0].shape[2]):
        raise ValueError("Snapshot positions are outside the streaming cache")
    return {
        layer: (
            key[:, :, selected, :].detach().clone(),
            value[:, :, selected, :].detach().clone(),
        )
        for layer, (key, value) in enumerate(layers)
    }


def patch_streaming_state(
    recipient: StreamingPrefixState, *, donor: StreamingPrefixState,
    generated_positions: Sequence[int], visual_positions: Sequence[int],
    selected_layers: Sequence[int] = (), mode: str = "KV",
) -> tuple[StreamingPrefixState, dict[str, Any]]:
    """Patch all-layer native-GQA K+V after a span has been computed."""

    generated = sorted({int(value) for value in generated_positions})
    if not generated or generated[0] < 0 or generated[-1] >= int(recipient.generated_length):
        raise ValueError("Patched generated positions must precede the next streaming query")
    absolute = [
        absolute_reasoning_token_position(
            prompt_length=int(recipient.prompt_length), token_index=index,
        )
        for index in generated
    ]
    if set(absolute) & {int(value) for value in visual_positions}:
        raise ValueError("Streaming checkpoint patches may not replace visual cache positions")
    target = clone_streaming_state(recipient)
    target_layers = _cache_layers(target.cache)
    donor_layers = _cache_layers(donor.cache)
    if len(target_layers) != len(donor_layers):
        raise ValueError("Streaming donor and recipient layer counts differ")
    if absolute[-1] >= int(donor_layers[0][0].shape[2]):
        raise ValueError("Streaming donor does not contain every patch position")
    normalized_mode = str(mode).upper()
    if normalized_mode not in {"K", "V", "KV"}:
        raise ValueError("Streaming cache patch mode must be K, V, or KV")
    selected = (
        set(range(len(target_layers)))
        if not selected_layers
        else {int(value) for value in selected_layers}
    )
    if not selected or not selected.issubset(set(range(len(target_layers)))):
        raise ValueError("Streaming cache patch selected an invalid layer")
    index = torch.tensor(absolute, dtype=torch.long, device=target_layers[0][0].device)
    layer_audits = []
    for layer_index, ((target_key, target_value), (donor_key, donor_value)) in enumerate(
        zip(target_layers, donor_layers)
    ):
        if layer_index not in selected:
            layer_audits.append({
                "layer_index": layer_index,
                "layer_selected": False,
                "mode": normalized_mode,
                "positions_replaced": [],
                "position_count": 0,
                "native_kv_head_count": int(target_key.shape[1]),
                "head_dimension": int(target_key.shape[-1]),
                "nonselected_key_max_abs_delta": 0.0,
                "nonselected_value_max_abs_delta": 0.0,
                "unselected_component_key_max_abs_delta": 0.0,
                "unselected_component_value_max_abs_delta": 0.0,
                "visual_positions_replaced": [],
                "current_query_position_replaced": False,
                "post_rope_key": True,
                "projected_value": True,
            })
            continue
        before_key = target_key.index_select(2, index).detach().clone()
        before_value = target_value.index_select(2, index).detach().clone()
        expected_key = donor_key.index_select(2, index).to(target_key.device, target_key.dtype)
        expected_value = donor_value.index_select(2, index).to(target_value.device, target_value.dtype)
        if normalized_mode in {"K", "KV"}:
            target_key[:, :, index, :] = expected_key
        if normalized_mode in {"V", "KV"}:
            target_value[:, :, index, :] = expected_value
        layer_audits.append({
            "layer_index": layer_index,
            "layer_selected": True,
            "mode": normalized_mode,
            "positions_replaced": absolute,
            "position_count": len(absolute),
            "native_kv_head_count": int(target_key.shape[1]),
            "head_dimension": int(target_key.shape[-1]),
            "recipient_key_exact_source_before_patch": bool(torch.equal(before_key, expected_key)),
            "recipient_value_exact_source_before_patch": bool(torch.equal(before_value, expected_value)),
            "selected_key_exact_expected": bool(torch.equal(
                target_key.index_select(2, index),
                expected_key if normalized_mode in {"K", "KV"} else before_key,
            )),
            "selected_value_exact_expected": bool(torch.equal(
                target_value.index_select(2, index),
                expected_value if normalized_mode in {"V", "KV"} else before_value,
            )),
            "nonselected_key_max_abs_delta": 0.0,
            "nonselected_value_max_abs_delta": 0.0,
            "unselected_component_key_max_abs_delta": 0.0 if normalized_mode == "V" else None,
            "unselected_component_value_max_abs_delta": 0.0 if normalized_mode == "K" else None,
            "visual_positions_replaced": [],
            "current_query_position_replaced": False,
            "post_rope_key": True,
            "projected_value": True,
            "first_patched_absolute_query": int(recipient.prompt_length) + int(recipient.generated_length),
        })
    return target, {
        "cache_mode": normalized_mode,
        "patch_generated_indices": generated,
        "patch_absolute_positions": absolute,
        "first_downstream_absolute_query": int(recipient.prompt_length) + int(recipient.generated_length),
        "layer_audits": layer_audits,
        "selected_layers": sorted(selected),
        "visual_kv_donor_patched": False,
        "non_event_cache_donor_patched": False,
    }


@torch.inference_mode()
def score_candidate_from_streaming_state(
    *, model: Any, state: StreamingPrefixState, candidate_token_ids: Sequence[int], seed: int,
) -> dict[str, Any]:
    candidate = [int(value) for value in candidate_token_ids]
    if not candidate:
        raise ValueError("Streaming evidence candidate must be nonempty")
    token_log_probabilities = []
    first_log_probs = torch.log_softmax(state.last_logits.float(), dim=-1)
    token_log_probabilities.append(float(first_log_probs[candidate[0]].item()))
    working = None
    if len(candidate) > 1:
        working = clone_streaming_state(state)
        for index, token in enumerate(candidate[:-1]):
            advance_streaming_state(
                model=model, state=working, token_ids=[token], seed=seed, chunk_size=1,
            )
            log_probs = torch.log_softmax(working.last_logits.float(), dim=-1)
            token_log_probabilities.append(float(log_probs[candidate[index + 1]].item()))
    summary = summarize_candidate_log_probs(token_log_probabilities)
    summary.update({
        "candidate_token_ids": candidate,
        "runtime_mode": "bounded_native_eager_cache",
        "finite": bool(all(torch.isfinite(torch.tensor(token_log_probabilities)).tolist())),
        "distribution_definition": "raw model next-token distribution; only divergent suffix rows are summarized",
    })
    if working is not None:
        del working
    return summary


@torch.inference_mode()
def score_preference_from_streaming_state(
    *, model: Any, state: StreamingPrefixState, original_suffix_ids: Sequence[int],
    counterfactual_suffix_ids: Sequence[int], seed: int,
) -> dict[str, Any]:
    candidates = {
        CANDIDATES[0]: score_candidate_from_streaming_state(
            model=model, state=state, candidate_token_ids=original_suffix_ids, seed=seed,
        ),
        CANDIDATES[1]: score_candidate_from_streaming_state(
            model=model, state=state, candidate_token_ids=counterfactual_suffix_ids, seed=seed,
        ),
    }
    original, counterfactual = candidates[CANDIDATES[0]], candidates[CANDIDATES[1]]
    return {
        "L_o": float(original["mean_log_probability"]),
        "L_c": float(counterfactual["mean_log_probability"]),
        "D": float(original["mean_log_probability"]) - float(counterfactual["mean_log_probability"]),
        "finite": bool(original["finite"] and counterfactual["finite"]),
        **candidates,
    }


@torch.inference_mode()
def roll_streaming_prefix(
    *, model: Any, prefill: StreamingPrefixState, prefix_token_ids: Sequence[int],
    end_generated_index: int, seed: int, layers: Sequence[int] = (),
    selected_heads: Sequence[int] = (), source_positions: Sequence[int] = (),
    suppressed_generated_indices: Sequence[int] = (), donor: StreamingPrefixState | None = None,
    patch_generated_indices: Sequence[int] = (), visual_positions: Sequence[int] = (),
    chunk_size: int = 128, release_allocator_cache: bool = False,
    forced_generated_boundaries: Sequence[int] = (),
    patch_selected_layers: Sequence[int] = (), patch_mode: str = "KV",
) -> tuple[StreamingPrefixState, dict[str, Any]]:
    """Roll one native/suppressed/rescue arm in causal generated-token order."""

    prefix = [int(value) for value in prefix_token_ids]
    end = int(end_generated_index)
    if end < int(prefill.generated_length) or end > len(prefix):
        raise ValueError("Streaming endpoint is outside the frozen prefix")
    suppressed = sorted({int(value) for value in suppressed_generated_indices})
    if suppressed and (
        not layers or not selected_heads or not source_positions
        or suppressed[0] < int(prefill.generated_length) or suppressed[-1] >= end
    ):
        raise ValueError("Invalid streaming source-suppression coordinates")
    patch_positions = sorted({int(value) for value in patch_generated_indices})
    patch_after = patch_positions[-1] + 1 if patch_positions else None
    if (donor is None) != (not patch_positions):
        raise ValueError("Streaming donor and patch positions must be supplied together")
    if patch_after is not None and (
        patch_positions[0] < int(prefill.generated_length) or patch_after >= end
    ):
        raise ValueError("Streaming patch must leave a downstream query before the readout")
    forced = sorted({int(value) for value in forced_generated_boundaries})
    if patch_after is not None and patch_after not in forced:
        raise ValueError("Every rescue arm must predeclare its patch boundary for all conditions")
    chunk_ranges = fixed_chunk_ranges(
        start=int(prefill.generated_length), end=end, chunk_size=int(chunk_size),
        mandatory_boundaries=forced,
    )
    state = clone_streaming_state(prefill)
    source_executions = []
    patch_audit = None
    suppressed_set = set(suppressed)
    executed_ranges = []
    for current, boundary in chunk_ranges:
        if int(state.generated_length) != current:
            raise RuntimeError("Streaming state left the frozen query partition")
        if patch_after is not None and current == patch_after:
            assert donor is not None
            state, patch_audit = patch_streaming_state(
                state, donor=donor, generated_positions=patch_positions,
                visual_positions=visual_positions,
                selected_layers=patch_selected_layers, mode=patch_mode,
            )
        active_queries = [position for position in range(current, boundary) if position in suppressed_set]
        patches = []
        if active_queries:
            absolute_queries = [
                absolute_reasoning_token_position(
                    prompt_length=int(state.prompt_length), token_index=index,
                )
                for index in active_queries
            ]
            patches = [
                SourceContributionWindowPatch(
                    model=model,
                    layer_index=int(layer),
                    query_positions=absolute_queries,
                    selected_heads=selected_heads,
                    source_positions=source_positions,
                    gain=0.0,
                )
                for layer in sorted({int(value) for value in layers})
            ]
        with ExitStack() as stack:
            for patch in patches:
                stack.enter_context(patch)
            advance_streaming_state(
                model=model,
                state=state,
                token_ids=prefix[current:boundary],
                seed=seed,
                chunk_size=max(1, boundary - current),
                release_allocator_cache=release_allocator_cache,
            )
        if patches:
            source_executions.append({
                "generated_query_indices": active_queries,
                "absolute_query_positions": [
                    absolute_reasoning_token_position(
                        prompt_length=int(state.prompt_length), token_index=index,
                    )
                    for index in active_queries
                ],
                "layer_audits": [patch.complete() for patch in patches],
            })
        executed_ranges.append([current, boundary])
    if patch_after is not None and patch_audit is None:
        raise RuntimeError("Streaming checkpoint patch was not executed")
    return state, {
        "runtime_mode": "bounded_native_eager_cache",
        "chunk_size": int(chunk_size),
        "forced_generated_boundaries": forced,
        "executed_chunk_ranges": executed_ranges,
        "condition_invariant_partition_required": True,
        "end_generated_index": end,
        "source_suppression_executions": source_executions,
        "source_suppressed_generated_indices": suppressed,
        "cache_patch": patch_audit,
        "patch_selected_layers": sorted({int(value) for value in patch_selected_layers}),
        "patch_mode": str(patch_mode).upper(),
    }


__all__ = [
    "StreamingPrefixState",
    "advance_streaming_state",
    "clone_streaming_state",
    "fixed_chunk_ranges",
    "patch_streaming_state",
    "prefill_streaming_state",
    "release_cuda_allocator_cache",
    "roll_streaming_prefix",
    "score_candidate_from_streaming_state",
    "score_preference_from_streaming_state",
    "snapshot_cache_positions",
]
