"""Memory-safe online aggregation of Qwen3-VL language attention."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import torch


MODALITY_NAMES = ("visual", "prompt", "reasoning")


def visual_grid_metadata(grid_thw: list[int], merge_size: int, patch_size: int) -> dict[str, Any]:
    if len(grid_thw) != 3:
        raise ValueError(f"Expected [t, h, w], got {grid_thw}")
    temporal, grid_h, grid_w = (int(value) for value in grid_thw)
    if grid_h % merge_size or grid_w % merge_size:
        raise ValueError(f"Grid {grid_thw} is not divisible by merge_size={merge_size}")
    merged_h = grid_h // merge_size
    merged_w = grid_w // merge_size
    return {
        "patch_grid_shape": [temporal, grid_h, grid_w],
        "merged_grid_shape": [temporal, merged_h, merged_w],
        "visual_token_count": temporal * merged_h * merged_w,
        "patch_size": int(patch_size),
        "merge_size": int(merge_size),
        "resized_image_size": [grid_w * patch_size, grid_h * patch_size],
        "mapping_order": "temporal-major, then row-major over merged spatial grid",
    }


@dataclass
class _PendingLayer:
    modality_by_layer: torch.Tensor
    visual_focus: torch.Tensor
    selected_head_mass: torch.Tensor | None
    query_length: int
    key_length: int


class OnlineAttentionRecorder:
    """Aggregate exact eager-attention weights as each decoder layer returns.

    Only the final query row from each generation forward is retained. Full
    attention tensors remain owned by the model and are not stored by this
    recorder.
    """

    def __init__(
        self,
        prompt_length: int,
        visual_indices: list[int],
        num_layers: int,
        selected_head_layers: list[int] | tuple[int, ...],
    ) -> None:
        if prompt_length <= 0:
            raise ValueError("prompt_length must be positive")
        if not visual_indices:
            raise ValueError("At least one visual token index is required")
        if min(visual_indices) < 0 or max(visual_indices) >= prompt_length:
            raise ValueError("Visual indices must lie inside the initial prompt")
        self.prompt_length = int(prompt_length)
        self.visual_indices = sorted({int(index) for index in visual_indices})
        visual_set = set(self.visual_indices)
        self.prompt_indices = [index for index in range(prompt_length) if index not in visual_set]
        self.num_layers = int(num_layers)
        self.selected_head_layers = [int(layer) for layer in selected_head_layers]
        if any(layer < 0 or layer >= num_layers for layer in self.selected_head_layers):
            raise ValueError("selected_head_layers contains an invalid layer index")
        self._pending: dict[int, _PendingLayer] = {}
        self._handles: list[Any] = []
        self._modality_steps: list[np.ndarray] = []
        self._selected_head_steps: list[np.ndarray] = []
        self._focus_steps: list[np.ndarray] = []
        self._query_lengths: list[int] = []
        self._key_lengths: list[int] = []
        self._num_heads: int | None = None

    def attach(self, attention_modules: list[torch.nn.Module]) -> "OnlineAttentionRecorder":
        if len(attention_modules) != self.num_layers:
            raise ValueError(f"Expected {self.num_layers} attention modules, got {len(attention_modules)}")
        if self._handles:
            raise RuntimeError("Recorder is already attached")
        for layer_index, module in enumerate(attention_modules):
            self._handles.append(module.register_forward_hook(self._make_hook(layer_index)))
        return self

    def _make_hook(self, layer_index: int):
        def hook(_module, _inputs, output) -> None:
            if not isinstance(output, tuple) or len(output) < 2 or output[1] is None:
                raise RuntimeError(
                    "Language attention weights were unavailable; Stage 0 requires the eager attention implementation"
                )
            self.consume(layer_index, output[1])

        return hook

    def close(self) -> None:
        for handle in self._handles:
            handle.remove()
        self._handles.clear()

    def consume(self, layer_index: int, attention_weights: torch.Tensor) -> None:
        if attention_weights.ndim != 4 or attention_weights.shape[0] != 1:
            raise ValueError(f"Expected attention shape [1, heads, query, key], got {tuple(attention_weights.shape)}")
        if layer_index in self._pending:
            raise RuntimeError(f"Layer {layer_index} was recorded twice in one generation step")
        if not self._pending and layer_index != 0:
            raise RuntimeError(f"Generation step began at layer {layer_index}, expected layer 0")

        row = attention_weights[0, :, -1, :].detach().float()
        num_heads, key_length = row.shape
        query_length = int(attention_weights.shape[-2])
        if key_length < self.prompt_length:
            raise ValueError(f"Attention key length {key_length} is shorter than prompt length {self.prompt_length}")
        self._num_heads = self._num_heads or int(num_heads)
        if self._num_heads != int(num_heads):
            raise ValueError("Attention head count changed across layers")

        visual_index = torch.tensor(self.visual_indices, device=row.device, dtype=torch.long)
        prompt_index = torch.tensor(self.prompt_indices, device=row.device, dtype=torch.long)
        visual_by_head = row.index_select(-1, visual_index).sum(-1)
        prompt_by_head = row.index_select(-1, prompt_index).sum(-1)
        if key_length > self.prompt_length:
            reasoning_by_head = row[:, self.prompt_length :].sum(-1)
        else:
            reasoning_by_head = torch.zeros_like(visual_by_head)
        modality_by_head = torch.stack((visual_by_head, prompt_by_head, reasoning_by_head), dim=-1)

        pending = _PendingLayer(
            modality_by_layer=modality_by_head.mean(0),
            visual_focus=row.index_select(-1, visual_index).mean(0),
            selected_head_mass=modality_by_head if layer_index in self.selected_head_layers else None,
            query_length=query_length,
            key_length=int(key_length),
        )
        self._pending[layer_index] = pending
        if len(self._pending) == self.num_layers:
            self._finalize_step()

    def _finalize_step(self) -> None:
        expected = list(range(self.num_layers))
        if sorted(self._pending) != expected:
            raise RuntimeError(f"Incomplete attention step; observed layers {sorted(self._pending)}")
        ordered = [self._pending[layer] for layer in expected]
        key_lengths = {item.key_length for item in ordered}
        query_lengths = {item.query_length for item in ordered}
        if len(key_lengths) != 1 or len(query_lengths) != 1:
            raise RuntimeError("Attention shapes differ across language layers")

        modality = torch.stack([item.modality_by_layer for item in ordered]).cpu().numpy().astype(np.float32)
        focus = torch.stack([item.visual_focus for item in ordered]).mean(0).cpu().numpy().astype(np.float32)
        if self.selected_head_layers:
            selected = torch.stack(
                [self._pending[layer].selected_head_mass for layer in self.selected_head_layers]
            ).cpu().numpy().astype(np.float32)
        else:
            selected = np.empty((0, int(self._num_heads or 0), len(MODALITY_NAMES)), dtype=np.float32)

        self._modality_steps.append(modality)
        self._selected_head_steps.append(selected)
        self._focus_steps.append(focus)
        self._query_lengths.append(query_lengths.pop())
        self._key_lengths.append(key_lengths.pop())
        self._pending.clear()

    def as_arrays(self) -> dict[str, np.ndarray]:
        if self._pending:
            raise RuntimeError("Cannot export an incomplete attention step")
        if not self._modality_steps:
            return {
                "modality_by_layer": np.empty((0, self.num_layers, 3), dtype=np.float32),
                "selected_head_mass": np.empty((0, len(self.selected_head_layers), 0, 3), dtype=np.float32),
                "visual_focus": np.empty((0, len(self.visual_indices)), dtype=np.float32),
                "query_lengths": np.empty((0,), dtype=np.int32),
                "key_lengths": np.empty((0,), dtype=np.int32),
                "selected_head_layers": np.asarray(self.selected_head_layers, dtype=np.int32),
                "visual_indices": np.asarray(self.visual_indices, dtype=np.int32),
            }
        return {
            "modality_by_layer": np.stack(self._modality_steps),
            "selected_head_mass": np.stack(self._selected_head_steps),
            "visual_focus": np.stack(self._focus_steps),
            "query_lengths": np.asarray(self._query_lengths, dtype=np.int32),
            "key_lengths": np.asarray(self._key_lengths, dtype=np.int32),
            "selected_head_layers": np.asarray(self.selected_head_layers, dtype=np.int32),
            "visual_indices": np.asarray(self.visual_indices, dtype=np.int32),
            "modality_names": np.asarray(MODALITY_NAMES),
        }

    def validate(self, expected_steps: int) -> dict[str, Any]:
        arrays = self.as_arrays()
        modality = arrays["modality_by_layer"]
        finite = bool(np.isfinite(modality).all())
        mass_error = float(np.abs(modality.sum(axis=-1) - 1.0).max()) if modality.size else float("inf")
        expected_keys = np.arange(self.prompt_length, self.prompt_length + expected_steps, dtype=np.int32)
        key_alignment = bool(np.array_equal(arrays["key_lengths"], expected_keys))
        step_alignment = int(modality.shape[0]) == int(expected_steps)
        return {
            "passed": finite and mass_error <= 0.01 and key_alignment and step_alignment and not self._pending,
            "finite": finite,
            "maximum_modality_mass_error": mass_error,
            "key_length_alignment": key_alignment,
            "step_count_alignment": step_alignment,
            "recorded_steps": int(modality.shape[0]),
            "expected_steps": int(expected_steps),
        }

