"""Calibration-local cache helpers built on the frozen DynamicCache layout."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import torch


def _maximum(tensor: torch.Tensor) -> float:
    return float(tensor.detach().float().abs().max().item()) if tensor.numel() else 0.0


def replace_selected_cache_positions(
    recipient_layers: Sequence[tuple[torch.Tensor, torch.Tensor]],
    donor_layers: Sequence[tuple[torch.Tensor, torch.Tensor]],
    *, absolute_positions: Sequence[int], selected_layers: Sequence[int],
    visual_positions: Sequence[int],
) -> list[dict[str, Any]]:
    """Replace K+V at exact layers/positions and return an invariance audit."""

    positions = sorted({int(value) for value in absolute_positions})
    selected = {int(value) for value in selected_layers}
    if not positions:
        raise ValueError("At least one cache position is required")
    if set(positions) & {int(value) for value in visual_positions}:
        raise ValueError("Calibration cache patch overlaps visual positions")
    if len(recipient_layers) != len(donor_layers):
        raise ValueError("Recipient and donor cache layer counts differ")
    audits = []
    for layer_index, ((target_key, target_value), (donor_key, donor_value)) in enumerate(
        zip(recipient_layers, donor_layers)
    ):
        if target_key.shape != donor_key.shape or target_value.shape != donor_value.shape:
            raise ValueError("Recipient and donor cache shapes differ")
        if positions[0] < 0 or positions[-1] >= int(target_key.shape[2]):
            raise ValueError("Calibration cache position is outside the sequence")
        before_key = target_key.detach().clone()
        before_value = target_value.detach().clone()
        index = torch.tensor(positions, dtype=torch.long, device=target_key.device)
        expected_key = donor_key.index_select(2, index).to(target_key.device, target_key.dtype)
        expected_value = donor_value.index_select(2, index).to(target_value.device, target_value.dtype)
        if layer_index in selected:
            target_key[:, :, index, :] = expected_key
            target_value[:, :, index, :] = expected_value
        keep = torch.ones(int(target_key.shape[2]), dtype=torch.bool, device=target_key.device)
        keep[index] = False
        audits.append({
            "layer_index": layer_index,
            "layer_selected": layer_index in selected,
            "mode": "KV",
            "positions_replaced": positions if layer_index in selected else [],
            "native_kv_head_count": int(target_key.shape[1]),
            "head_dimension": int(target_key.shape[-1]),
            "selected_key_exact_expected": bool(
                torch.equal(target_key.index_select(2, index), expected_key)
            ) if layer_index in selected else True,
            "selected_value_exact_expected": bool(
                torch.equal(target_value.index_select(2, index), expected_value)
            ) if layer_index in selected else True,
            "nonselected_key_max_abs_delta": _maximum(target_key[:, :, keep, :] - before_key[:, :, keep, :]),
            "nonselected_value_max_abs_delta": _maximum(target_value[:, :, keep, :] - before_value[:, :, keep, :]),
            "unselected_layer_key_max_abs_delta": _maximum(target_key - before_key) if layer_index not in selected else 0.0,
            "unselected_layer_value_max_abs_delta": _maximum(target_value - before_value) if layer_index not in selected else 0.0,
            "visual_positions_replaced": [],
            "post_rope_key": True,
            "projected_value": True,
        })
    if selected - set(range(len(recipient_layers))):
        raise ValueError("Selected cache layer is outside the model")
    return audits


def tensor_pair_max_abs_delta(
    left: Mapping[int, tuple[torch.Tensor, torch.Tensor]],
    right: Mapping[int, tuple[torch.Tensor, torch.Tensor]],
) -> dict[str, Any]:
    if set(left) != set(right):
        raise ValueError("Compared tensor layer sets differ")
    rows = []
    for layer in sorted(left):
        left_key, left_value = left[layer]
        right_key, right_value = right[layer]
        if left_key.shape != right_key.shape or left_value.shape != right_value.shape:
            raise ValueError("Compared tensor shapes differ")
        rows.append({
            "layer_index": int(layer),
            "key_max_abs_delta": _maximum(left_key - right_key),
            "value_max_abs_delta": _maximum(left_value - right_value),
            "key_shape": list(left_key.shape),
            "value_shape": list(left_value.shape),
        })
    key_max = max((row["key_max_abs_delta"] for row in rows), default=0.0)
    value_max = max((row["value_max_abs_delta"] for row in rows), default=0.0)
    return {
        "key_max_abs_delta": key_max,
        "value_max_abs_delta": value_max,
        "maximum_abs_delta": max(key_max, value_max),
        "layers": rows,
    }


__all__ = ["replace_selected_cache_positions", "tensor_pair_max_abs_delta"]
