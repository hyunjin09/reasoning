"""Query-head-selective routing-versus-value source composition."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import torch


KV_MODES = ("K", "V", "KV")


def compose_kv_sources(
    recipient_key: torch.Tensor,
    recipient_value: torch.Tensor,
    donor_key: torch.Tensor,
    donor_value: torch.Tensor,
    *,
    positions: Sequence[int],
    mode: str,
) -> tuple[torch.Tensor, torch.Tensor, dict[str, Any]]:
    """Compose donor K, donor V, or both at frozen source positions."""

    if mode not in KV_MODES:
        raise ValueError(f"Unknown K/V intervention mode: {mode}")
    shape = recipient_key.shape
    if (
        recipient_key.ndim != 4
        or recipient_value.shape != shape
        or donor_key.shape != shape
        or donor_value.shape != shape
    ):
        raise ValueError("K/V tensors must share [batch, kv_head, sequence, head_dim]")
    selected = sorted({int(position) for position in positions})
    if not selected or selected[0] < 0 or selected[-1] >= int(shape[2]):
        raise ValueError("K/V source positions are empty or outside the sequence")
    key = recipient_key.clone()
    value = recipient_value.clone()
    key_swapped = mode in {"K", "KV"}
    value_swapped = mode in {"V", "KV"}
    if key_swapped:
        key[:, :, selected, :] = donor_key[:, :, selected, :]
    if value_swapped:
        value[:, :, selected, :] = donor_value[:, :, selected, :]
    complement = [index for index in range(int(shape[2])) if index not in selected]
    return key, value, {
        "mode": mode,
        "key_swapped": key_swapped,
        "value_swapped": value_swapped,
        "assigned_positions": selected,
        "assigned_position_count": len(selected),
        "nonassigned_key_max_abs_delta": (
            float((key[:, :, complement] - recipient_key[:, :, complement]).abs().max().item())
            if complement else 0.0
        ),
        "nonassigned_value_max_abs_delta": (
            float((value[:, :, complement] - recipient_value[:, :, complement]).abs().max().item())
            if complement else 0.0
        ),
        "unswapped_key_max_abs_delta": (
            float((key - recipient_key).abs().max().item()) if not key_swapped else None
        ),
        "unswapped_value_max_abs_delta": (
            float((value - recipient_value).abs().max().item()) if not value_swapped else None
        ),
        "key_shape": list(shape),
        "value_shape": list(shape),
    }


__all__ = ["KV_MODES", "compose_kv_sources"]

