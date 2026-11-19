"""Stage 3B.8 bidirectional Value-restoration readouts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from visual_reasoning.stage3b3_redesign.metrics import semantic_restoration_metrics


def value_restoration_metrics(
    *, recipient_scores: Mapping[str, Mapping[str, float]]
) -> dict[str, Any]:
    """Label the established paired-semantic contrast as Value restoration."""

    paired = semantic_restoration_metrics(
        original_history=recipient_scores["O"],
        counterfactual_history=recipient_scores["C"],
        all_layer_bri=1.0,
    )
    return {
        "BVR_O": float(paired["SRC_O"]),
        "BVR_C": float(paired["SRC_C"]),
        "BVR": float(paired["BSRC"]),
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


__all__ = ["value_restoration_metrics"]
