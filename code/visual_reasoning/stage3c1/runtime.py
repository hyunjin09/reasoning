"""Transparent eager-Attention capture for Stage 3C.1."""

from __future__ import annotations

from contextlib import AbstractContextManager
from types import MethodType
from typing import Any, Mapping, Sequence

import torch

from visual_reasoning.stage3b6.heads import (
    _attention_module,
    _project_attention_output,
    _qwen_attention_parts,
)
from visual_reasoning.stage3c1.metrics import reconstruct_attention_rows


class MultiLayerAttentionCapture(AbstractContextManager["MultiLayerAttentionCapture"]):
    """Capture frozen query rows without changing the returned Attention output."""

    def __init__(
        self,
        *,
        model: Any,
        positions_by_layer: Mapping[int, Sequence[int]],
        heads_by_layer: Mapping[int, Sequence[int]],
    ) -> None:
        self.model = model
        self.positions_by_layer = {
            int(layer): sorted({int(position) for position in positions})
            for layer, positions in positions_by_layer.items()
        }
        self.heads_by_layer = {
            int(layer): sorted({int(head) for head in heads})
            for layer, heads in heads_by_layer.items()
        }
        if set(self.positions_by_layer) != set(self.heads_by_layer):
            raise ValueError("Capture layers must have both positions and heads")
        self.states: dict[int, dict[str, Any]] = {}
        self._original_forwards: dict[int, Any] = {}

    def _run(
        self,
        layer_index: int,
        module: torch.nn.Module,
        hidden_states: torch.Tensor,
        position_embeddings: tuple[torch.Tensor, torch.Tensor],
        attention_mask: torch.Tensor | None,
        past_key_values: Any | None = None,
        **kwargs: Any,
    ) -> tuple[torch.Tensor, torch.Tensor | None]:
        if layer_index in self.states:
            raise RuntimeError(f"Layer {layer_index} capture executed more than once")
        output, query, key, value, weights = _qwen_attention_parts(
            module,
            hidden_states,
            position_embeddings,
            attention_mask,
            past_key_values,
            kwargs,
        )
        if weights is None:
            raise RuntimeError("Stage 3C.1 requires eager Attention weights")
        sequence = int(query.shape[2])
        positions = self.positions_by_layer[layer_index]
        heads = self.heads_by_layer[layer_index]
        if not positions or positions[0] < 0 or positions[-1] >= sequence:
            raise ValueError(f"Layer {layer_index} query position outside sequence")
        if not heads or heads[0] < 0 or heads[-1] >= int(query.shape[1]):
            raise ValueError(f"Layer {layer_index} query head outside model")

        query_to_kv = [
            head // int(module.num_key_value_groups) for head in range(int(query.shape[1]))
        ]
        if max(query_to_kv) >= int(key.shape[1]):
            raise RuntimeError("GQA query-to-KV mapping is invalid")
        rows: dict[int, dict[str, torch.Tensor]] = {}
        reconstructed = reconstruct_attention_rows(
            query=query,
            key=key,
            value=value,
            attention_mask=attention_mask,
            scaling=float(module.scaling),
            num_key_value_groups=int(module.num_key_value_groups),
        )
        installed_output = output.transpose(1, 2)
        max_probability_error = float(
            (reconstructed["attention"] - weights).abs().max().item()
        )
        max_head_output_error = float(
            (reconstructed["head_output"] - installed_output).abs().max().item()
        )
        max_attention_sum_error = 0.0
        for position in positions:
            visible = position + 1
            installed_attention = weights[:, :, position : position + 1, :visible]
            max_attention_sum_error = max(
                max_attention_sum_error,
                float((installed_attention.float().sum(dim=-1) - 1.0).abs().max().item()),
            )
            head_index = torch.tensor(heads, device=query.device, dtype=torch.long)
            rows[position] = {
                "query": query[0, head_index, position, :].detach().float().cpu(),
                "raw_dot": reconstructed["raw_dot"][0, head_index, position, :visible].detach().float().cpu(),
                "scaled_logits": reconstructed["scaled_logits"][0, head_index, position, :visible].detach().float().cpu(),
                "final_logits": reconstructed["final_logits"][0, head_index, position, :visible].detach().float().cpu(),
                "attention": installed_attention[0, head_index, 0, :].detach().float().cpu(),
                "head_output": output[0, position, head_index, :].detach().float().cpu(),
            }

        projected = _project_attention_output(module, output, hidden_states)
        self.states[layer_index] = {
            "layer_index": layer_index,
            "positions": positions,
            "heads": heads,
            "rows": rows,
            "key": key[0, torch.tensor([query_to_kv[head] for head in heads], device=key.device), :, :]
            .detach()
            .float()
            .cpu(),
            "value": value[0, torch.tensor([query_to_kv[head] for head in heads], device=value.device), :, :]
            .detach()
            .float()
            .cpu(),
            "wo_weight": module.o_proj.weight.detach().float().cpu(),
            "wo_bias_present": module.o_proj.bias is not None,
            "scaling": float(module.scaling),
            "query_to_kv_group": query_to_kv,
            "tensor_shapes": {
                "residual_input": list(hidden_states.shape),
                "query": list(query.shape),
                "key": list(key.shape),
                "value": list(value.shape),
                "attention": list(weights.shape),
                "pre_wo_head_output": list(output.shape),
                "post_wo_output": list(projected.shape),
            },
            "reconstruction": {
                "maximum_probability_absolute_error": max_probability_error,
                "maximum_head_output_absolute_error": max_head_output_error,
                "maximum_attention_sum_absolute_error": max_attention_sum_error,
            },
        }
        return projected, weights

    def __enter__(self) -> "MultiLayerAttentionCapture":
        if self._original_forwards:
            raise RuntimeError("Attention capture is already active")
        for layer_index in sorted(self.positions_by_layer):
            module = _attention_module(self.model, layer_index)
            self._original_forwards[layer_index] = module.forward

            def forward(
                active_module: torch.nn.Module,
                hidden_states: torch.Tensor,
                position_embeddings: tuple[torch.Tensor, torch.Tensor],
                attention_mask: torch.Tensor | None,
                past_key_values: Any | None = None,
                *,
                _layer_index: int = layer_index,
                **kwargs: Any,
            ):
                return self._run(
                    _layer_index,
                    active_module,
                    hidden_states,
                    position_embeddings,
                    attention_mask,
                    past_key_values,
                    **kwargs,
                )

            module.forward = MethodType(forward, module)
        return self

    def close(self) -> None:
        for layer_index, original in self._original_forwards.items():
            _attention_module(self.model, layer_index).forward = original
        self._original_forwards.clear()

    def complete_states(self) -> dict[int, dict[str, Any]]:
        if set(self.states) != set(self.positions_by_layer):
            raise RuntimeError("Not every requested Attention layer executed exactly once")
        return self.states

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


__all__ = ["MultiLayerAttentionCapture"]
