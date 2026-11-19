"""Pure tensor operations for the frozen Stage 3B.8 Value representation."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import torch

from visual_reasoning.stage3b6.heads import gqa_query_to_kv_map


def roi_value_contribution(
    *,
    attention_weights: torch.Tensor,
    values: torch.Tensor,
    current_position: int,
    selected_query_heads: Sequence[int],
    roi_positions: Sequence[int],
) -> torch.Tensor:
    """Return selected-head ``sum_j alpha[h,j] V[gqa(h),j]`` before ``W_O``.

    Attention is ``[batch, query_head, query_position, source_position]`` and
    Value is ``[batch, kv_head, source_position, head_dimension]``.  The return
    value retains ``[batch, selected_query_head, head_dimension]`` so callers
    can either concatenate it or splice its per-head components.
    """

    if attention_weights.ndim != 4 or values.ndim != 4:
        raise ValueError("Attention and Value tensors must both be rank four")
    if int(attention_weights.shape[0]) != int(values.shape[0]):
        raise ValueError("Attention and Value batch dimensions differ")
    if int(attention_weights.shape[-1]) != int(values.shape[2]):
        raise ValueError("Attention source and Value sequence dimensions differ")
    position = int(current_position)
    heads = [int(head) for head in selected_query_heads]
    roi = sorted({int(index) for index in roi_positions})
    if not heads or len(set(heads)) != len(heads):
        raise ValueError("Selected query heads must be nonempty and unique")
    if not roi:
        raise ValueError("ROI positions must be nonempty")
    if position < 0 or position >= int(attention_weights.shape[2]):
        raise ValueError("Current position is outside the Attention tensor")
    if min(heads) < 0 or max(heads) >= int(attention_weights.shape[1]):
        raise ValueError("Selected query head is outside the Attention tensor")
    if min(roi) < 0 or max(roi) >= int(values.shape[2]):
        raise ValueError("ROI position is outside the Value tensor")

    query_to_kv = gqa_query_to_kv_map(
        query_heads=int(attention_weights.shape[1]),
        kv_heads=int(values.shape[1]),
    )
    contributions = []
    for head in heads:
        alpha = attention_weights[:, head, position, roi]
        value = values[:, query_to_kv[head], roi, :]
        contributions.append(torch.matmul(alpha.unsqueeze(1), value).squeeze(1))
    return torch.stack(contributions, dim=1)


def roi_value_contribution_from_current(
    *,
    current_attention_weights: torch.Tensor,
    values: torch.Tensor,
    selected_query_heads: Sequence[int],
    roi_positions: Sequence[int],
) -> torch.Tensor:
    """Current-row variant avoiding retention of a quadratic Attention tensor."""

    if current_attention_weights.ndim != 3:
        raise ValueError("Current Attention weights must be [batch, query_head, source]")
    return roi_value_contribution(
        attention_weights=current_attention_weights.unsqueeze(2),
        values=values,
        current_position=0,
        selected_query_heads=selected_query_heads,
        roi_positions=roi_positions,
    )


def flatten_head_vectors(tensor: torch.Tensor) -> torch.Tensor:
    """Concatenate selected logical-head vectors in their frozen order."""

    if tensor.ndim < 2:
        raise ValueError("Head tensor must have at least head and feature axes")
    return tensor.reshape(*tensor.shape[:-2], int(tensor.shape[-2] * tensor.shape[-1]))


def unflatten_head_vectors(tensor: torch.Tensor, *, head_count: int) -> torch.Tensor:
    """Inverse of :func:`flatten_head_vectors` for a frozen head count."""

    count = int(head_count)
    if count <= 0 or int(tensor.shape[-1]) % count:
        raise ValueError("Vector dimension must be divisible by head count")
    return tensor.reshape(*tensor.shape[:-1], count, int(tensor.shape[-1]) // count)


def symmetric_semantic_delta(
    *, z_oo: torch.Tensor, z_oc: torch.Tensor, z_co: torch.Tensor, z_cc: torch.Tensor
) -> torch.Tensor:
    """Compute the prospectively frozen counterfactual-to-original delta."""

    if not (z_oo.shape == z_oc.shape == z_co.shape == z_cc.shape):
        raise ValueError("All semantic representation tensors must align exactly")
    return 0.5 * ((z_oo - z_oc) + (z_co - z_cc))


def interpolate_head_delta(
    native_output: torch.Tensor,
    head_delta: torch.Tensor,
    *,
    current_position: int,
    selected_query_heads: Sequence[int],
    dose: float,
) -> tuple[torch.Tensor, dict[str, Any]]:
    """Add a scaled ROI-derived delta to selected pre-``W_O`` head outputs."""

    if native_output.ndim != 4:
        raise ValueError("Native head output must be [batch, sequence, head, dim]")
    position = int(current_position)
    heads = [int(head) for head in selected_query_heads]
    expected = (int(native_output.shape[0]), len(heads), int(native_output.shape[3]))
    if tuple(head_delta.shape) != expected:
        raise ValueError(f"Head delta shape {tuple(head_delta.shape)} != {expected}")
    if position < 0 or position >= int(native_output.shape[1]):
        raise ValueError("Current position is outside the head output")
    if not heads or len(set(heads)) != len(heads):
        raise ValueError("Selected query heads must be nonempty and unique")
    if min(heads) < 0 or max(heads) >= int(native_output.shape[2]):
        raise ValueError("Selected query head is outside the head output")
    merged = native_output.clone()
    scaled = head_delta.to(device=merged.device, dtype=merged.dtype) * float(dose)
    merged[:, position, heads, :] = merged[:, position, heads, :] + scaled
    delta = merged - native_output
    changed_heads = torch.nonzero(delta.abs().amax(dim=(0, 1, 3)) > 0, as_tuple=False).flatten().tolist()
    changed_positions = torch.nonzero(delta.abs().amax(dim=(0, 2, 3)) > 0, as_tuple=False).flatten().tolist()
    nonselected = [head for head in range(int(delta.shape[2])) if head not in heads]
    return merged, {
        "dose": float(dose),
        "selected_query_heads": heads,
        "changed_query_heads": [int(value) for value in changed_heads],
        "changed_sequence_positions": [int(value) for value in changed_positions],
        "nonselected_head_max_abs_delta": (
            float(delta[:, :, nonselected, :].abs().max().item()) if nonselected else 0.0
        ),
        "selected_head_max_abs_delta": float(delta[:, position, heads, :].abs().max().item()),
        "pre_output_projection_shape": list(native_output.shape),
    }


def fit_right_singular_subspace(rows: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """Fit an uncentered right-singular basis to causal delta rows.

    Deltas have a meaningful zero origin, so Stage 3B.8 prospectively uses
    uncentered SVD instead of subtracting the discovery mean.
    """

    if rows.ndim != 2 or min(rows.shape) < 1:
        raise ValueError("Discovery delta matrix must be nonempty and rank two")
    _, singular_values, vh = torch.linalg.svd(rows.to(torch.float64), full_matrices=False)
    return vh.transpose(0, 1).contiguous(), singular_values


def project_rows(rows: torch.Tensor, basis: torch.Tensor) -> torch.Tensor:
    """Orthogonally project row vectors onto the columns of ``basis``."""

    if rows.ndim < 1 or basis.ndim != 2 or int(rows.shape[-1]) != int(basis.shape[0]):
        raise ValueError("Rows and projector basis do not align")
    typed = basis.to(device=rows.device, dtype=rows.dtype)
    return (rows @ typed) @ typed.transpose(0, 1)


def random_orthonormal_basis(*, dimension: int, rank: int, seed: int) -> torch.Tensor:
    """Return a deterministic Haar-distributed orthonormal column basis."""

    width = int(dimension)
    count = int(rank)
    if width < 1 or count < 1 or count > width:
        raise ValueError("Random-subspace dimension/rank are invalid")
    generator = torch.Generator(device="cpu")
    generator.manual_seed(int(seed))
    matrix = torch.randn(width, count, generator=generator, dtype=torch.float64)
    q, r = torch.linalg.qr(matrix, mode="reduced")
    signs = torch.where(torch.diag(r) < 0, -torch.ones(count), torch.ones(count))
    return q * signs


def select_discovery_rank(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    """Apply the frozen discovery-only rank rule and deterministic fallback."""

    ordered = sorted(rows, key=lambda row: int(row["rank"]))
    passing = [
        row
        for row in ordered
        if float(row["median_projected_ratio"]) >= 0.80
        and float(row["median_complement_ratio"]) <= 0.30
    ]
    if passing:
        return {
            "rank": int(passing[0]["rank"]),
            "rule_satisfied": True,
            "selection_reason": "smallest rank meeting projected>=0.80 and complement<=0.30",
        }
    if not ordered:
        raise ValueError("No discovery rank results were supplied")
    # Prospectively defined partial-result fallback: maximize recovered semantic
    # effect minus residual complement, then prefer the smaller rank on ties.
    best = max(
        ordered,
        key=lambda row: (
            float(row["median_projected_ratio"])
            - float(row["median_complement_ratio"]),
            -int(row["rank"]),
        ),
    )
    return {
        "rank": int(best["rank"]),
        "rule_satisfied": False,
        "selection_reason": "best discovery tradeoff: maximize projected ratio minus complement ratio",
    }


__all__ = [
    "fit_right_singular_subspace",
    "flatten_head_vectors",
    "interpolate_head_delta",
    "project_rows",
    "random_orthonormal_basis",
    "roi_value_contribution",
    "roi_value_contribution_from_current",
    "select_discovery_rank",
    "symmetric_semantic_delta",
    "unflatten_head_vectors",
]
