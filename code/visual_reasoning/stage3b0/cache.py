"""Validated DynamicCache cloning and all-layer token-position patching."""

from __future__ import annotations

import copy
from typing import Any, Iterable

import torch


def _layer_tensors(cache: Any) -> list[tuple[torch.Tensor, torch.Tensor]]:
    layers = getattr(cache, "layers", None)
    if not isinstance(layers, list) or not layers:
        raise ValueError("Cache must expose a nonempty layers list")
    tensors: list[tuple[torch.Tensor, torch.Tensor]] = []
    for index, layer in enumerate(layers):
        keys = getattr(layer, "keys", None)
        values = getattr(layer, "values", None)
        if not isinstance(keys, torch.Tensor) or not isinstance(values, torch.Tensor):
            raise ValueError(f"Cache layer {index} does not expose tensor keys/values")
        if keys.shape != values.shape or keys.ndim != 4:
            raise ValueError(f"Cache layer {index} has invalid K/V shape")
        tensors.append((keys, values))
    return tensors


def validate_cache_layout(
    cache: Any,
    *,
    expected_layers: int,
    expected_kv_heads: int,
    expected_sequence_length: int,
    expected_head_dim: int,
) -> dict[str, Any]:
    tensors = _layer_tensors(cache)
    if len(tensors) != int(expected_layers):
        raise ValueError(f"Cache layer count mismatch: {len(tensors)} != {expected_layers}")
    expected = (1, int(expected_kv_heads), int(expected_sequence_length), int(expected_head_dim))
    shapes = [tuple(keys.shape) for keys, _ in tensors]
    if any(shape != expected for shape in shapes):
        raise ValueError(f"Cache tensor shape mismatch: expected {expected}, observed {shapes}")
    return {
        "layer_count": len(tensors),
        "tensor_shape": list(expected),
        "batch_axis": 0,
        "kv_head_axis": 1,
        "sequence_axis": 2,
        "head_dimension_axis": 3,
        "all_layers_same_shape": True,
    }


def clone_cache(cache: Any) -> Any:
    """Deep-clone a cache so suffix scoring cannot mutate the frozen prefill."""

    cloned = copy.deepcopy(cache)
    original_tensors = _layer_tensors(cache)
    cloned_tensors = _layer_tensors(cloned)
    if len(original_tensors) != len(cloned_tensors):
        raise ValueError("Cloned cache layer count changed")
    for (old_k, old_v), (new_k, new_v) in zip(original_tensors, cloned_tensors):
        if old_k.data_ptr() == new_k.data_ptr() or old_v.data_ptr() == new_v.data_ptr():
            raise RuntimeError("Cache clone aliases the source tensor storage")
    return cloned


def patch_cache_positions(recipient: Any, source: Any, positions: Iterable[int]) -> tuple[Any, dict[str, Any]]:
    """Return recipient cache with selected K/V sequence positions from source."""

    recipient_tensors = _layer_tensors(recipient)
    source_tensors = _layer_tensors(source)
    if len(recipient_tensors) != len(source_tensors):
        raise ValueError("Source and recipient cache shape/layer mismatch")
    if any(left[0].shape != right[0].shape for left, right in zip(recipient_tensors, source_tensors)):
        raise ValueError("Source and recipient cache tensor shape mismatch")
    indices = sorted({int(value) for value in positions})
    sequence_length = int(recipient_tensors[0][0].shape[2])
    if not indices or indices[0] < 0 or indices[-1] >= sequence_length:
        raise ValueError("Patch positions must be nonempty and inside the cache sequence")

    patched = clone_cache(recipient)
    patched_tensors = _layer_tensors(patched)
    index_tensor = torch.tensor(indices, dtype=torch.long, device=patched_tensors[0][0].device)
    layers_patched: list[int] = []
    for layer_index, ((target_k, target_v), (source_k, source_v)) in enumerate(
        zip(patched_tensors, source_tensors)
    ):
        target_k[:, :, index_tensor, :] = source_k[:, :, index_tensor, :]
        target_v[:, :, index_tensor, :] = source_v[:, :, index_tensor, :]
        layers_patched.append(layer_index)
    return patched, {
        "positions": indices,
        "position_count": len(indices),
        "layers_patched": layers_patched,
        "kv_tensors_patched_per_layer": 2,
        "sequence_axis": 2,
    }
