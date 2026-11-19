"""Restoration-controlled module metrics for Stage 3B.4."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
from scipy.stats import wilcoxon

from visual_reasoning.stage3b3_redesign.metrics import semantic_restoration_metrics


def bootstrap_summary(
    values: list[float], *, seed: int = 1234, resamples: int = 10_000
) -> dict[str, Any]:
    if not values:
        raise ValueError("At least one independent base value is required")
    array = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(array), size=(int(resamples), len(array)))
    medians = np.median(array[indices], axis=1)
    return {
        "N": int(len(array)),
        "mean": float(np.mean(array)),
        "median": float(np.median(array)),
        "bootstrap_95_CI": [
            float(np.quantile(medians, 0.025)),
            float(np.quantile(medians, 0.975)),
        ],
        "bootstrap_resamples": int(resamples),
        "bootstrap_seed": int(seed),
    }


def one_sided_wilcoxon_greater(values: list[float]) -> float:
    if not values or all(float(value) == 0.0 for value in values):
        return 1.0
    return float(wilcoxon(values, alternative="greater", zero_method="wilcox").pvalue)


def module_restoration_metrics(
    *,
    recipient_scores: Mapping[str, Mapping[str, float]],
    all_layer_bri: float,
) -> dict[str, Any]:
    """Apply the validated paired-semantic contrast to one module intervention."""
    if set(recipient_scores) != {"O", "C"}:
        raise ValueError("Module restoration requires O and C recipient histories")
    paired = semantic_restoration_metrics(
        original_history=recipient_scores["O"],
        counterfactual_history=recipient_scores["C"],
        all_layer_bri=all_layer_bri,
    )
    return {
        "R_O": paired["R_O"],
        "R_C": paired["R_C"],
        "BMR_O": paired["SRC_O"],
        "BMR_C": paired["SRC_C"],
        "BMR": paired["BSRC"],
        "BMR_normalized": paired["BSRC_normalized"],
        "A_render": paired["A_render"],
        "all_layer_BRI": paired["all_layer_BRI"],
        "activity_floor": paired["activity_floor"],
        "active": paired["active"],
        "render_to_semantic_ratio": paired["render_to_semantic_ratio"],
        "render_to_all_layer_ratio": paired["render_to_all_layer_ratio"],
        "O_restoration_source_consistent": paired["O_restoration_source_consistent"],
        "C_restoration_source_consistent": paired["C_restoration_source_consistent"],
        "bidirectionally_source_consistent": paired["bidirectionally_source_consistent"],
        "artifact_terms": {
            key: paired[key]
            for key in (
                "A_O_original_history",
                "A_C_original_history",
                "A_O_counterfactual_history",
                "A_C_counterfactual_history",
            )
        },
    }


def module_interaction_metrics(
    *, attention: float, mlp: float, joint: float, block: float
) -> dict[str, float | None]:
    """Return descriptive module/block ratios and the non-additive interaction."""
    denominator = float(block)
    return {
        "attention_to_block_ratio": None if denominator == 0.0 else float(attention) / denominator,
        "mlp_to_block_ratio": None if denominator == 0.0 else float(mlp) / denominator,
        "joint_to_block_ratio": None if denominator == 0.0 else float(joint) / denominator,
        "interaction": float(joint) - float(attention) - float(mlp),
    }
