from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import torch
from transformers.models.qwen3_vl.modeling_qwen3_vl import apply_rotary_pos_emb, repeat_kv


@dataclass
class CapturedLayer:
    queries_by_event: dict[str, torch.Tensor] = field(default_factory=dict)
    visual_keys: torch.Tensor | None = None


@dataclass
class QueryKeyCaptureHook:
    selected_layers: list[int]
    target_positions: dict[str, int]
    visual_positions: torch.Tensor
    capture_visual_keys: bool
    captured: dict[int, CapturedLayer] = field(default_factory=dict)

    _modules: dict[int, Any] = field(default_factory=dict)
    _original_forwards: dict[int, Callable[..., Any]] = field(default_factory=dict)

    def attach(self, model: Any) -> None:
        if self._original_forwards:
            return
        for layer_idx in self.selected_layers:
            module = model.model.language_model.layers[layer_idx].self_attn
            self._modules[layer_idx] = module
            self._original_forwards[layer_idx] = module.forward
            module.forward = self._make_wrapped_forward(layer_idx, module)

    def detach(self) -> None:
        for layer_idx, module in self._modules.items():
            module.forward = self._original_forwards[layer_idx]
        self._modules.clear()
        self._original_forwards.clear()

    def _make_wrapped_forward(self, layer_idx: int, module: Any):
        hook = self
        original_forward = self._original_forwards[layer_idx]

        def wrapped_forward(hidden_states, position_embeddings, attention_mask, past_key_values=None, **kwargs):
            hook.capture_layer(layer_idx, module, hidden_states, position_embeddings)
            return original_forward(
                hidden_states,
                position_embeddings,
                attention_mask,
                past_key_values=past_key_values,
                **kwargs,
            )

        return wrapped_forward

    def capture_layer(self, layer_idx: int, module: Any, hidden_states: torch.Tensor, position_embeddings) -> None:
        with torch.no_grad():
            input_shape = hidden_states.shape[:-1]
            hidden_shape = (*input_shape, -1, module.head_dim)
            query_states = module.q_norm(module.q_proj(hidden_states).view(hidden_shape)).transpose(1, 2)
            key_states = module.k_norm(module.k_proj(hidden_states).view(hidden_shape)).transpose(1, 2)
            cos, sin = position_embeddings
            query_states, key_states = apply_rotary_pos_emb(query_states, key_states, cos, sin)
            if key_states.shape[1] != query_states.shape[1]:
                key_states = repeat_kv(key_states, module.num_key_value_groups)

            layer_capture = self.captured.setdefault(layer_idx, CapturedLayer())
            seq_len = query_states.shape[2]
            for event_name, position in self.target_positions.items():
                if 0 <= int(position) < seq_len:
                    layer_capture.queries_by_event[event_name] = (
                        query_states[0, :, int(position), :].detach().to("cpu", dtype=torch.float16)
                    )

            if self.capture_visual_keys:
                positions = self.visual_positions.to(key_states.device)
                layer_capture.visual_keys = key_states[0, :, positions, :].detach().to("cpu", dtype=torch.float16)


def stack_queries(captured: dict[int, CapturedLayer], event_name: str, selected_layers: list[int]) -> torch.Tensor:
    tensors = []
    for layer_idx in selected_layers:
        try:
            tensors.append(captured[layer_idx].queries_by_event[event_name])
        except KeyError as exc:
            raise KeyError(f"missing query capture for layer {layer_idx}, event {event_name}") from exc
    return torch.stack(tensors, dim=0)


def stack_visual_keys(captured: dict[int, CapturedLayer], selected_layers: list[int]) -> torch.Tensor:
    tensors = []
    for layer_idx in selected_layers:
        layer = captured.get(layer_idx)
        if layer is None or layer.visual_keys is None:
            raise KeyError(f"missing visual key capture for layer {layer_idx}")
        tensors.append(layer.visual_keys)
    return torch.stack(tensors, dim=0)

