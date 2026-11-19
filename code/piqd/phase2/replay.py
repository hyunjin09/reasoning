from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

import torch

from piqd.model.qwen_loader import PreparedPrefill, build_prefill, prune_prefill


@dataclass(frozen=True)
class ConditionReplayInputs:
    condition: str
    prefill: PreparedPrefill
    prefix_start: int
    target_positions: dict[str, int]
    cache_context_id: str


def append_generated_tokens(inputs: dict[str, torch.Tensor], generated_token_ids: list[int]) -> dict[str, torch.Tensor]:
    if not generated_token_ids:
        raise ValueError("generated_token_ids must be non-empty")
    input_ids = inputs["input_ids"]
    token_tensor = torch.tensor([generated_token_ids], dtype=input_ids.dtype, device=input_ids.device)
    result = dict(inputs)
    result["input_ids"] = torch.cat([input_ids, token_tensor], dim=1)

    attention_mask = inputs.get("attention_mask")
    if attention_mask is not None:
        result["attention_mask"] = torch.cat([attention_mask, torch.ones_like(token_tensor)], dim=1)

    mm_token_type_ids = inputs.get("mm_token_type_ids")
    if mm_token_type_ids is not None:
        result["mm_token_type_ids"] = torch.cat([mm_token_type_ids, torch.zeros_like(token_tensor)], dim=1)
    return result


def build_condition_replay(
    *,
    model: Any,
    inputs: dict[str, torch.Tensor],
    generated_token_ids: list[int],
    events: list[Any],
    condition: str,
    retained_visual_indices: list[int] | None = None,
    sample_id: str,
) -> ConditionReplayInputs:
    full_prefill = build_prefill(model, inputs)
    return build_condition_replay_from_prefill(
        full_prefill=full_prefill,
        generated_token_ids=generated_token_ids,
        events=events,
        condition=condition,
        retained_visual_indices=retained_visual_indices,
        sample_id=sample_id,
    )


def build_condition_replay_from_prefill(
    *,
    full_prefill: PreparedPrefill,
    generated_token_ids: list[int],
    events: list[Any],
    condition: str,
    retained_visual_indices: list[int] | None = None,
    sample_id: str,
) -> ConditionReplayInputs:
    prefill = full_prefill
    visual_hash_items: list[int] | str = "full"
    if condition == "CQ":
        if retained_visual_indices is None:
            raise ValueError("CQ replay requires retained_visual_indices")
        prefill = prune_prefill(full_prefill, retained_visual_indices)
        visual_hash_items = retained_visual_indices
    elif condition != "CFQ":
        raise ValueError(f"unknown Phase 2 condition: {condition}")

    prefix_start = prefill.seq_len - len(generated_token_ids)
    target_positions = {
        event_key(event): prefix_start + int(event.generated_token_index)
        for event in events
    }
    for event in events:
        absolute_position = target_positions[event_key(event)]
        token_at_position = int(prefill.input_ids[0, absolute_position].item())
        if token_at_position != int(event.token_id):
            raise ValueError(
                f"{sample_id} {condition} event {event_key(event)} token mismatch: "
                f"position has {token_at_position}, expected {event.token_id}"
            )

    cache_context_id = make_cache_context_id(
        sample_id=sample_id,
        condition=condition,
        visual_items=visual_hash_items,
        prefix_hash=hash_token_ids(generated_token_ids),
    )
    return ConditionReplayInputs(
        condition=condition,
        prefill=prefill,
        prefix_start=prefix_start,
        target_positions=target_positions,
        cache_context_id=cache_context_id,
    )


def event_key(event: Any) -> str:
    return f"{event.event_type}::{int(event.generated_token_index)}"


def hash_token_ids(token_ids: list[int]) -> str:
    payload = json.dumps([int(token_id) for token_id in token_ids], separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def hash_indices(indices: list[int] | str) -> str:
    payload = json.dumps(indices, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def make_cache_context_id(sample_id: str, condition: str, visual_items: list[int] | str, prefix_hash: str) -> str:
    return "::".join([sample_id, condition, hash_indices(visual_items), prefix_hash])


def decoded_context(tokenizer: Any, token_ids: list[int], event_index: int, radius: int = 4) -> str:
    start = max(0, event_index - radius)
    end = min(len(token_ids), event_index + radius + 1)
    return tokenizer.decode(token_ids[start:end], skip_special_tokens=True)
