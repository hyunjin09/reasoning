"""Pure tensor and source-accounting helpers for Stage 3C.1."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import torch


def build_source_partition(
    *,
    current_position: int,
    prompt_length: int,
    visual_positions: Sequence[int],
    question_positions: Sequence[int],
    special_prompt_positions: Sequence[int],
) -> dict[str, list[int]]:
    """Partition every causally visible position into four source classes.

    ``special_other`` contains non-question/nonvisual prompt control positions
    plus the current query token. This keeps ``previous_reasoning`` strictly
    prior to the active query while making source-mass accounting exhaustive.
    """

    current = int(current_position)
    prompt = int(prompt_length)
    if prompt <= 0 or current < prompt:
        raise ValueError("Current position must be a generated token after a nonempty prompt")
    visual = sorted({int(value) for value in visual_positions})
    question = sorted({int(value) for value in question_positions})
    special = sorted({int(value) for value in special_prompt_positions})
    declared = visual + question + special
    if any(value < 0 or value >= prompt for value in declared):
        raise ValueError("Declared prompt source position is outside the prompt")
    if len(declared) != len(set(declared)):
        raise ValueError("Declared prompt source groups must be disjoint")
    missing_prompt = sorted(set(range(prompt)) - set(declared))
    special = sorted([*special, *missing_prompt, current])
    partition = {
        "visual": visual,
        "prompt_question": question,
        "previous_reasoning": list(range(prompt, current)),
        "special_other": special,
    }
    flattened = [position for positions in partition.values() for position in positions]
    if len(flattened) != len(set(flattened)) or sorted(flattened) != list(range(current + 1)):
        raise ValueError("Source partition must be disjoint and exhaustive over the causal prefix")
    return partition


def _repeat_kv(hidden_states: torch.Tensor, repeats: int) -> torch.Tensor:
    batch, kv_heads, sequence, head_dimension = hidden_states.shape
    if repeats == 1:
        return hidden_states
    expanded = hidden_states[:, :, None, :, :].expand(
        batch, kv_heads, int(repeats), sequence, head_dimension
    )
    return expanded.reshape(batch, kv_heads * int(repeats), sequence, head_dimension)


def reconstruct_attention_rows(
    *,
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    attention_mask: torch.Tensor | None,
    scaling: float,
    num_key_value_groups: int,
) -> dict[str, torch.Tensor]:
    """Reconstruct installed eager-Attention rows from active post-RoPE Q/K/V."""

    if query.ndim != 4 or key.ndim != 4 or value.shape != key.shape:
        raise ValueError("Q/K/V tensors must use [batch, head, sequence, head_dimension]")
    repeated_key = _repeat_kv(key, num_key_value_groups)
    repeated_value = _repeat_kv(value, num_key_value_groups)
    if query.shape[:2] != repeated_key.shape[:2] or query.shape[-1] != repeated_key.shape[-1]:
        raise ValueError("Logical Q heads and expanded K/V heads do not align")
    raw_dot = torch.matmul(query, repeated_key.transpose(2, 3))
    scaled_logits = raw_dot * float(scaling)
    final_logits = scaled_logits if attention_mask is None else scaled_logits + attention_mask
    attention = torch.nn.functional.softmax(final_logits, dim=-1, dtype=torch.float32).to(query.dtype)
    head_output = torch.matmul(attention, repeated_value)
    return {
        "raw_dot": raw_dot,
        "scaled_logits": scaled_logits,
        "final_logits": final_logits,
        "attention": attention,
        "head_output": head_output,
        "expanded_key": repeated_key,
        "expanded_value": repeated_value,
    }


def _validated_indices(groups: Mapping[str, Sequence[int]], sequence: int) -> dict[str, list[int]]:
    result: dict[str, list[int]] = {}
    for name, values in groups.items():
        indices = sorted({int(value) for value in values})
        if any(index < 0 or index >= sequence for index in indices):
            raise ValueError(f"Source group {name!r} is outside the sequence")
        result[str(name)] = indices
    return result


def source_attention_statistics(
    attention: torch.Tensor, groups: Mapping[str, Sequence[int]]
) -> dict[str, list[dict[str, float | int]]]:
    """Return per-head mass and token-count-normalized density for each group."""

    if attention.ndim != 2:
        raise ValueError("Attention must have [logical_query_head, source_position]")
    validated = _validated_indices(groups, int(attention.shape[-1]))
    result: dict[str, list[dict[str, float | int]]] = {}
    for name, indices in validated.items():
        mass = attention[:, indices].float().sum(dim=-1) if indices else torch.zeros(
            attention.shape[0], dtype=torch.float32, device=attention.device
        )
        result[name] = [
            {
                "token_count": len(indices),
                "mass": float(value.item()),
                "density": float(value.item() / len(indices)) if indices else 0.0,
            }
            for value in mass
        ]
    return result


def source_value_contributions(
    attention: torch.Tensor,
    expanded_values: torch.Tensor,
    groups: Mapping[str, Sequence[int]],
) -> dict[str, list[dict[str, Any]]]:
    """Compute per-head alpha-V vectors and descriptive magnitude summaries."""

    if attention.ndim != 2 or expanded_values.ndim != 3:
        raise ValueError("Expected attention [head, source] and values [head, source, dim]")
    if attention.shape != expanded_values.shape[:2]:
        raise ValueError("Attention and expanded Value tensors do not align")
    validated = _validated_indices(groups, int(attention.shape[-1]))
    result: dict[str, list[dict[str, Any]]] = {}
    for name, indices in validated.items():
        if indices:
            vectors = torch.sum(
                attention[:, indices, None].to(expanded_values.dtype)
                * expanded_values[:, indices, :],
                dim=1,
            )
            masses = attention[:, indices].float().sum(dim=-1)
        else:
            vectors = torch.zeros(
                (attention.shape[0], expanded_values.shape[-1]),
                dtype=expanded_values.dtype,
                device=expanded_values.device,
            )
            masses = torch.zeros(attention.shape[0], dtype=torch.float32, device=attention.device)
        rows = []
        for head in range(int(attention.shape[0])):
            vector = vectors[head].detach().float().cpu()
            norm = float(vector.norm().item())
            mass = float(masses[head].item())
            rows.append(
                {
                    "token_count": len(indices),
                    "attention_mass": mass,
                    "vector": vector,
                    "norm": norm,
                    "norm_per_attention_mass": norm / mass if mass > 0 else None,
                }
            )
        result[name] = rows
    return result


def class_logsumexp(
    final_logits: torch.Tensor, groups: Mapping[str, Sequence[int]]
) -> dict[str, list[float | None]]:
    """Return per-head class log-sum-exp over final masked logits."""

    if final_logits.ndim != 2:
        raise ValueError("Final logits must have [logical_query_head, source_position]")
    validated = _validated_indices(groups, int(final_logits.shape[-1]))
    result: dict[str, list[float | None]] = {}
    for name, indices in validated.items():
        if not indices:
            result[name] = [None] * int(final_logits.shape[0])
        else:
            result[name] = [
                float(value)
                for value in torch.logsumexp(final_logits[:, indices].float(), dim=-1).cpu().tolist()
            ]
    return result


def wo_head_contributions(
    *,
    head_vectors: torch.Tensor,
    wo_weight: torch.Tensor,
    selected_heads: Sequence[int],
) -> dict[str, Any]:
    """Project individual logical-head vectors through their exact W_O slices."""

    if head_vectors.ndim != 2 or wo_weight.ndim != 2:
        raise ValueError("Expected head vectors [head, dim] and W_O weight [hidden, head*dim]")
    heads, head_dimension = int(head_vectors.shape[0]), int(head_vectors.shape[1])
    if int(wo_weight.shape[1]) != heads * head_dimension:
        raise ValueError("W_O input dimension does not match logical-head layout")
    selected = sorted({int(head) for head in selected_heads})
    if not selected or selected[0] < 0 or selected[-1] >= heads:
        raise ValueError("Selected logical head is outside W_O")
    per_head: dict[int, torch.Tensor] = {}
    for head in selected:
        start = head * head_dimension
        end = start + head_dimension
        per_head[head] = torch.nn.functional.linear(
            head_vectors[head].to(wo_weight.dtype), wo_weight[:, start:end]
        )
    selected_sum = torch.stack([per_head[head] for head in selected]).sum(dim=0)
    return {"per_head": per_head, "selected_sum": selected_sum}


__all__ = [
    "build_source_partition",
    "class_logsumexp",
    "reconstruct_attention_rows",
    "source_attention_statistics",
    "source_value_contributions",
    "wo_head_contributions",
]
