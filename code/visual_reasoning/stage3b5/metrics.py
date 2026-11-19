"""Stage 3B.5 paired restoration and sequential-boundary metrics."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from visual_reasoning.stage3b4.metrics import (
    bootstrap_summary,
    module_restoration_metrics,
    one_sided_wilcoxon_greater,
)


def boundary_restoration_metrics(
    *, recipient_scores: Mapping[str, Mapping[str, float]], all_layer_bri: float
) -> dict[str, Any]:
    """Reuse the exact validated Stage 3B.4 paired semantic metric."""
    return module_restoration_metrics(
        recipient_scores=recipient_scores,
        all_layer_bri=all_layer_bri,
    )


def boundary_increments(values: Mapping[str, float]) -> dict[str, float]:
    required = {
        "h_pre", "pre_attn_norm", "h_post_attn", "pre_mlp_norm", "h_post_block"
    }
    if set(values) != required:
        raise ValueError("Boundary increments require exactly the five frozen states")
    return {
        "G_input_norm": float(values["pre_attn_norm"]) - float(values["h_pre"]),
        "G_attn": float(values["h_post_attn"]) - float(values["h_pre"]),
        "G_post_attn_norm": float(values["pre_mlp_norm"]) - float(values["h_post_attn"]),
        "G_mlp": float(values["h_post_block"]) - float(values["h_post_attn"]),
    }


def recompute_contrasts(
    *,
    h_pre_recompute: float,
    h_post_attn_recompute: float,
    precomputed_joint: float,
    precomputed_mlp: float,
) -> dict[str, float]:
    return {
        "h_pre_vs_precomputed_joint": float(h_pre_recompute) - float(precomputed_joint),
        "h_post_attn_vs_precomputed_mlp": float(h_post_attn_recompute) - float(precomputed_mlp),
    }


__all__ = [
    "bootstrap_summary",
    "one_sided_wilcoxon_greater",
    "boundary_restoration_metrics",
    "boundary_increments",
    "recompute_contrasts",
]
