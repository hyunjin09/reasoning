"""Logical query-head helpers for grouped-query Attention intervention."""

from __future__ import annotations

from contextlib import AbstractContextManager
from types import MethodType
from typing import Any, Sequence

import torch


def _attention_module(model: Any, layer_index: int) -> torch.nn.Module:
    layers = model.model.language_model.layers
    layer_index = int(layer_index)
    if layer_index < 0 or layer_index >= len(layers):
        raise ValueError("Attention layer is outside the language model")
    return layers[layer_index].self_attn


def _qwen_attention_parts(
    module: torch.nn.Module,
    hidden_states: torch.Tensor,
    position_embeddings: tuple[torch.Tensor, torch.Tensor],
    attention_mask: torch.Tensor | None,
    past_key_values: Any | None,
    kwargs: dict[str, Any],
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor | None]:
    """Reproduce the installed Qwen3-VL eager Attention computation pre-``W_O``."""

    from transformers.models.qwen3_vl import modeling_qwen3_vl as qwen_impl

    input_shape = hidden_states.shape[:-1]
    hidden_shape = (*input_shape, -1, int(module.head_dim))
    query = module.q_norm(module.q_proj(hidden_states).view(hidden_shape)).transpose(1, 2)
    key = module.k_norm(module.k_proj(hidden_states).view(hidden_shape)).transpose(1, 2)
    value = module.v_proj(hidden_states).view(hidden_shape).transpose(1, 2)
    cos, sin = position_embeddings
    query, key = qwen_impl.apply_rotary_pos_emb(query, key, cos, sin)
    if past_key_values is not None:
        key, value = past_key_values.update(key, value, int(module.layer_idx))
    attention_interface = qwen_impl.ALL_ATTENTION_FUNCTIONS.get_interface(
        module.config._attn_implementation, qwen_impl.eager_attention_forward
    )
    output, weights = attention_interface(
        module,
        query,
        key,
        value,
        attention_mask,
        dropout=0.0 if not module.training else module.attention_dropout,
        scaling=module.scaling,
        **kwargs,
    )
    return output, query, key, value, weights


def _project_attention_output(
    module: torch.nn.Module, output: torch.Tensor, hidden_states: torch.Tensor
) -> torch.Tensor:
    return module.o_proj(output.reshape(*hidden_states.shape[:-1], -1).contiguous())


def _attention_group_summary(
    weights: torch.Tensor | None,
    *,
    position: int,
    groups: dict[str, Sequence[int]] | None,
) -> dict[str, Any]:
    if weights is None:
        return {}
    current = weights[0, :, int(position), :].detach().float()
    summary: dict[str, Any] = {
        "current_weight_shape": list(current.shape),
        "per_head_total_mass": current.sum(dim=-1).cpu().tolist(),
    }
    for name, values in (groups or {}).items():
        indices = sorted({int(value) for value in values})
        if indices:
            mass = current[:, indices].sum(dim=-1)
            summary[f"{name}_mass_per_head"] = mass.cpu().tolist()
            summary[f"{name}_density_per_head"] = (mass / len(indices)).cpu().tolist()
    return summary


def gqa_query_to_kv_map(*, query_heads: int, kv_heads: int) -> list[int]:
    """Return the logical query-head to shared K/V-group mapping."""

    query_heads = int(query_heads)
    kv_heads = int(kv_heads)
    if query_heads <= 0 or kv_heads <= 0 or query_heads % kv_heads:
        raise ValueError("Query heads must be a positive multiple of K/V heads")
    group_size = query_heads // kv_heads
    return [head // group_size for head in range(query_heads)]


def _validate_head_output(
    tensor: torch.Tensor, *, position: int, selected_heads: Sequence[int]
) -> tuple[int, list[int]]:
    if tensor.ndim != 4:
        raise ValueError("Per-head Attention output must have [batch, sequence, head, dim]")
    position = int(position)
    head_count = int(tensor.shape[2])
    heads = sorted({int(head) for head in selected_heads})
    if position < 0 or position >= int(tensor.shape[1]):
        raise ValueError("Current position is outside the Attention output")
    if not heads or heads[0] < 0 or heads[-1] >= head_count:
        raise ValueError("Selected logical query head is outside the model")
    return position, heads


def splice_query_head_outputs(
    recipient_output: torch.Tensor,
    swapped_output: torch.Tensor,
    *,
    position: int,
    selected_heads: Sequence[int],
) -> tuple[torch.Tensor, dict[str, Any]]:
    """Splice selected logical heads at one sequence position before ``W_O``."""

    if recipient_output.shape != swapped_output.shape:
        raise ValueError("Recipient and swapped per-head outputs must have the same shape")
    position, heads = _validate_head_output(
        recipient_output, position=position, selected_heads=selected_heads
    )
    merged = recipient_output.clone()
    merged[:, position, heads, :] = swapped_output[:, position, heads, :]
    delta = merged - recipient_output
    per_head = delta.abs().amax(dim=(0, 1, 3))
    changed_heads = torch.nonzero(per_head > 0, as_tuple=False).flatten().tolist()
    per_position = delta.abs().amax(dim=(0, 2, 3))
    changed_positions = torch.nonzero(per_position > 0, as_tuple=False).flatten().tolist()
    nonselected = [head for head in range(int(delta.shape[2])) if head not in heads]
    nonselected_max = (
        float(delta[:, :, nonselected, :].abs().max().item()) if nonselected else 0.0
    )
    return merged, {
        "selected_query_heads": heads,
        "changed_query_heads": [int(value) for value in changed_heads],
        "changed_sequence_positions": [int(value) for value in changed_positions],
        "nonselected_head_max_abs_delta": nonselected_max,
        "selected_head_max_abs_delta": float(delta[:, position, heads, :].abs().max().item()),
        "pre_output_projection_shape": list(recipient_output.shape),
    }


def swap_kv_positions(
    recipient_key: torch.Tensor,
    recipient_value: torch.Tensor,
    source_key: torch.Tensor,
    source_value: torch.Tensor,
    *,
    positions: Sequence[int],
) -> tuple[torch.Tensor, torch.Tensor, dict[str, Any]]:
    """Swap post-RoPE K/V only at prospectively frozen sequence positions."""

    shape = recipient_key.shape
    if (
        recipient_key.ndim != 4
        or recipient_value.shape != shape
        or source_key.shape != shape
        or source_value.shape != shape
    ):
        raise ValueError("K/V tensors must share [batch, kv_head, sequence, head_dim]")
    selected = sorted({int(position) for position in positions})
    if not selected or selected[0] < 0 or selected[-1] >= int(shape[2]):
        raise ValueError("K/V source positions are empty or outside the sequence")
    key = recipient_key.clone()
    value = recipient_value.clone()
    key[:, :, selected, :] = source_key[:, :, selected, :]
    value[:, :, selected, :] = source_value[:, :, selected, :]
    complement = [index for index in range(int(shape[2])) if index not in selected]
    key_outside = (
        float((key[:, :, complement, :] - recipient_key[:, :, complement, :]).abs().max().item())
        if complement else 0.0
    )
    value_outside = (
        float((value[:, :, complement, :] - recipient_value[:, :, complement, :]).abs().max().item())
        if complement else 0.0
    )
    return key, value, {
        "assigned_positions": selected,
        "assigned_position_count": len(selected),
        "nonassigned_key_max_abs_delta": key_outside,
        "nonassigned_value_max_abs_delta": value_outside,
        "key_shape": list(shape),
        "value_shape": list(shape),
    }


class CaptureQwenHeadState(AbstractContextManager["CaptureQwenHeadState"]):
    """Transparently reconstruct one Qwen Attention layer and capture post-RoPE K/V."""

    def __init__(
        self,
        *,
        model: Any,
        layer_index: int,
        position: int,
        attention_groups: dict[str, Sequence[int]] | None = None,
    ) -> None:
        self.layer_index = int(layer_index)
        self.position = int(position)
        self.module = _attention_module(model, self.layer_index)
        self.attention_groups = attention_groups
        self.state: dict[str, Any] | None = None
        self.audit: list[dict[str, Any]] = []
        self._original_forward: Any | None = None

    def _run(
        self,
        module: torch.nn.Module,
        hidden_states: torch.Tensor,
        position_embeddings: tuple[torch.Tensor, torch.Tensor],
        attention_mask: torch.Tensor | None,
        past_key_values: Any | None = None,
        **kwargs: Any,
    ) -> tuple[torch.Tensor, torch.Tensor | None]:
        if self.state is not None:
            raise RuntimeError("Attention capture executed more than once")
        output, query, key, value, weights = _qwen_attention_parts(
            module,
            hidden_states,
            position_embeddings,
            attention_mask,
            past_key_values,
            kwargs,
        )
        if self.position < 0 or self.position >= int(output.shape[1]):
            raise ValueError("Attention capture position is outside the sequence")
        self.state = {
            "key": key.detach().clone(),
            "value": value.detach().clone(),
            "current_query": query[:, :, self.position, :].detach().clone(),
            "current_head_output": output[:, self.position, :, :].detach().clone(),
            "attention_summary": _attention_group_summary(
                weights, position=self.position, groups=self.attention_groups
            ),
        }
        self.audit.append({
            "layer_index": self.layer_index,
            "position": self.position,
            "query_shape": list(query.shape),
            "key_shape": list(key.shape),
            "value_shape": list(value.shape),
            "pre_output_projection_shape": list(output.shape),
            "query_heads": int(query.shape[1]),
            "kv_heads": int(key.shape[1]),
            "head_dimension": int(query.shape[-1]),
            "axis_order": {
                "query_key_value": ["batch", "head", "sequence", "head_dimension"],
                "pre_output_projection": ["batch", "sequence", "query_head", "head_dimension"],
            },
        })
        return _project_attention_output(module, output, hidden_states), weights

    def __enter__(self) -> "CaptureQwenHeadState":
        if self._original_forward is not None:
            raise RuntimeError("Attention capture context is already active")
        self._original_forward = self.module.forward

        def forward(
            module: torch.nn.Module,
            hidden_states: torch.Tensor,
            position_embeddings: tuple[torch.Tensor, torch.Tensor],
            attention_mask: torch.Tensor | None,
            past_key_values: Any | None = None,
            **kwargs: Any,
        ):
            return self._run(
                module,
                hidden_states,
                position_embeddings,
                attention_mask,
                past_key_values,
                **kwargs,
            )

        self.module.forward = MethodType(forward, self.module)
        return self

    def complete_state(self) -> dict[str, Any]:
        if self.state is None or len(self.audit) != 1:
            raise RuntimeError("Attention capture did not execute exactly once")
        return self.state

    def close(self) -> None:
        if self._original_forward is not None:
            self.module.forward = self._original_forward
            self._original_forward = None

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


class HybridQueryHeadIntervention(
    AbstractContextManager["HybridQueryHeadIntervention"]
):
    """Recompute source-conditioned K/V Attention and splice logical heads before ``W_O``."""

    def __init__(
        self,
        *,
        model: Any,
        layer_index: int,
        position: int,
        selected_heads: Sequence[int],
        source_key: torch.Tensor,
        source_value: torch.Tensor,
        source_positions: Sequence[int],
        attention_groups: dict[str, Sequence[int]] | None = None,
    ) -> None:
        self.layer_index = int(layer_index)
        self.position = int(position)
        self.selected_heads = sorted({int(head) for head in selected_heads})
        self.source_key = source_key
        self.source_value = source_value
        self.source_positions = sorted({int(value) for value in source_positions})
        self.attention_groups = attention_groups
        self.module = _attention_module(model, self.layer_index)
        self.audit: list[dict[str, Any]] = []
        self._original_forward: Any | None = None

    def _run(
        self,
        module: torch.nn.Module,
        hidden_states: torch.Tensor,
        position_embeddings: tuple[torch.Tensor, torch.Tensor],
        attention_mask: torch.Tensor | None,
        past_key_values: Any | None = None,
        **kwargs: Any,
    ) -> tuple[torch.Tensor, torch.Tensor | None]:
        if self.audit:
            raise RuntimeError("Head intervention executed more than once")
        native, query, recipient_key, recipient_value, native_weights = _qwen_attention_parts(
            module,
            hidden_states,
            position_embeddings,
            attention_mask,
            past_key_values,
            kwargs,
        )
        swapped_key, swapped_value, kv_audit = swap_kv_positions(
            recipient_key,
            recipient_value,
            self.source_key.to(device=recipient_key.device, dtype=recipient_key.dtype),
            self.source_value.to(device=recipient_value.device, dtype=recipient_value.dtype),
            positions=self.source_positions,
        )
        from transformers.models.qwen3_vl import modeling_qwen3_vl as qwen_impl

        attention_interface = qwen_impl.ALL_ATTENTION_FUNCTIONS.get_interface(
            module.config._attn_implementation, qwen_impl.eager_attention_forward
        )
        swapped, swapped_weights = attention_interface(
            module,
            query,
            swapped_key,
            swapped_value,
            attention_mask,
            dropout=0.0 if not module.training else module.attention_dropout,
            scaling=module.scaling,
            **kwargs,
        )
        merged, head_audit = splice_query_head_outputs(
            native,
            swapped,
            position=self.position,
            selected_heads=self.selected_heads,
        )
        query_heads = int(query.shape[1])
        kv_heads = int(recipient_key.shape[1])
        query_to_kv = gqa_query_to_kv_map(
            query_heads=query_heads, kv_heads=kv_heads
        )
        changed_heads = set(head_audit["changed_query_heads"])
        query_selective = bool(
            changed_heads.issubset(self.selected_heads)
            and head_audit["nonselected_head_max_abs_delta"] == 0.0
            and set(head_audit["changed_sequence_positions"]).issubset({self.position})
        )
        self.audit.append({
            "layer_index": self.layer_index,
            "position": self.position,
            **head_audit,
            "selected_kv_groups": sorted({query_to_kv[head] for head in self.selected_heads}),
            "query_to_kv_group": query_to_kv,
            "kv_swap": kv_audit,
            "query_head_selectivity_valid": query_selective,
            "source_group_isolation_valid": bool(
                kv_audit["nonassigned_key_max_abs_delta"] == 0.0
                and kv_audit["nonassigned_value_max_abs_delta"] == 0.0
            ),
            "recipient_query_retained": True,
            "intervention_surface": "post-RoPE source K/V -> per-query-head pre-W_O output",
            "recipient_attention_summary": _attention_group_summary(
                native_weights, position=self.position, groups=self.attention_groups
            ),
            "swapped_attention_summary": _attention_group_summary(
                swapped_weights, position=self.position, groups=self.attention_groups
            ),
        })
        return _project_attention_output(module, merged, hidden_states), native_weights

    def __enter__(self) -> "HybridQueryHeadIntervention":
        if self._original_forward is not None:
            raise RuntimeError("Head intervention context is already active")
        self._original_forward = self.module.forward

        def forward(
            module: torch.nn.Module,
            hidden_states: torch.Tensor,
            position_embeddings: tuple[torch.Tensor, torch.Tensor],
            attention_mask: torch.Tensor | None,
            past_key_values: Any | None = None,
            **kwargs: Any,
        ):
            return self._run(
                module,
                hidden_states,
                position_embeddings,
                attention_mask,
                past_key_values,
                **kwargs,
            )

        self.module.forward = MethodType(forward, self.module)
        return self

    def close(self) -> None:
        if self._original_forward is not None:
            self.module.forward = self._original_forward
            self._original_forward = None

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


__all__ = [
    "CaptureQwenHeadState", "HybridQueryHeadIntervention",
    "gqa_query_to_kv_map", "splice_query_head_outputs", "swap_kv_positions"
]
