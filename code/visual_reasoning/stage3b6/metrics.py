"""Restoration-controlled Stage 3B.6 head and source-path metrics."""

from __future__ import annotations

import statistics
from collections import defaultdict
from collections.abc import Mapping
from collections.abc import Sequence
from typing import Any

from visual_reasoning.stage3b3_redesign.metrics import semantic_restoration_metrics


def head_restoration_metrics(
    *,
    recipient_scores: Mapping[str, Mapping[str, float]],
    stage3b5_attention_gain: float,
) -> dict[str, Any]:
    """Compute bidirectional semantic head restoration with paired shams."""

    paired = semantic_restoration_metrics(
        original_history=recipient_scores["O"],
        counterfactual_history=recipient_scores["C"],
        all_layer_bri=stage3b5_attention_gain,
    )
    gain = float(stage3b5_attention_gain)
    return {
        "BHR_O": float(paired["SRC_O"]),
        "BHR_C": float(paired["SRC_C"]),
        "BHR": float(paired["BSRC"]),
        "HRR": None if gain == 0.0 else float(paired["BSRC"]) / gain,
        "sham_effect": float(paired["A_render"]),
        "sham_to_semantic_ratio": paired["render_to_semantic_ratio"],
        "sham_to_attention_gain_ratio": paired["render_to_all_layer_ratio"],
        "bidirectionally_source_consistent": bool(
            paired["bidirectionally_source_consistent"]
        ),
        "artifact_terms": {
            key: float(paired[key])
            for key in (
                "A_O_original_history",
                "A_C_original_history",
                "A_O_counterfactual_history",
                "A_C_counterfactual_history",
            )
        },
    }


def path_restoration_metrics(
    *, recipient_scores: Mapping[str, Mapping[str, float]], all_source_bhr: float
) -> dict[str, Any]:
    """Compute BPR and its un-clipped ratio to the matching all-source head effect."""

    paired = semantic_restoration_metrics(
        original_history=recipient_scores["O"],
        counterfactual_history=recipient_scores["C"],
        all_layer_bri=all_source_bhr,
    )
    denominator = float(all_source_bhr)
    return {
        "BPR_O": float(paired["SRC_O"]),
        "BPR_C": float(paired["SRC_C"]),
        "BPR": float(paired["BSRC"]),
        "PRR": None if denominator == 0.0 else float(paired["BSRC"]) / denominator,
        "sham_effect": float(paired["A_render"]),
        "sham_to_semantic_ratio": paired["render_to_semantic_ratio"],
        "bidirectionally_source_consistent": bool(
            paired["bidirectionally_source_consistent"]
        ),
        "artifact_terms": {
            key: float(paired[key])
            for key in (
                "A_O_original_history",
                "A_C_original_history",
                "A_O_counterfactual_history",
                "A_C_counterfactual_history",
            )
        },
    }


def aggregate_base_medians(
    rows: Sequence[Mapping[str, Any]], *, value_keys: Sequence[str]
) -> list[dict[str, Any]]:
    """Collapse repeated cell/target moderators to one median row per base."""

    keys = tuple(str(key) for key in value_keys)
    if not keys:
        raise ValueError("At least one value key is required")
    grouped: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["base_problem_id"])].append(row)
    return [
        {
            "base_problem_id": base,
            **{
                key: float(statistics.median(float(row[key]) for row in base_rows))
                for key in keys
            },
            "aggregated_cell_count": len(base_rows),
        }
        for base, base_rows in sorted(grouped.items(), key=lambda item: item[0])
    ]


__all__ = [
    "aggregate_base_medians", "head_restoration_metrics", "path_restoration_metrics"
]
