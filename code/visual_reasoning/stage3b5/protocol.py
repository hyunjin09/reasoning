"""Prospectively frozen Stage 3B.5 hypothesis family and decision helper."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from visual_reasoning.stage3b4.protocol import holm_adjust
from visual_reasoning.stage3b5.boundaries import BOUNDARIES


COORDINATES = ("Ed_minus_1", "Ed")
WINDOWS = ("W4", "W5")


def build_primary_family(target_by_window: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    if set(target_by_window) != set(WINDOWS):
        raise ValueError("Primary family requires exactly W4 and W5")
    rows = []
    for coordinate in COORDINATES:
        for window in WINDOWS:
            target = target_by_window[window]
            layers = [int(value) for value in target["layers"]]
            if len(layers) != 2:
                raise ValueError("Each retained Stage 3B.5 window must contain two layers")
            for layer_role, layer_index in zip(("first", "second"), layers):
                for boundary in BOUNDARIES:
                    rows.append({
                        "test_id": f"{coordinate}__{window}__{layer_role}__{boundary}",
                        "coordinate": coordinate,
                        "window": window,
                        "fine_window": str(target["fine_window"]),
                        "layer_role": layer_role,
                        "layer_index": layer_index,
                        "boundary": boundary,
                        "primary_metric": "unnormalized paired semantic BMR",
                        "two_layer_entry_alias": bool(
                            layer_role == "first" and boundary == "h_pre"
                        ),
                    })
    if len(rows) != 40 or len({row["test_id"] for row in rows}) != 40:
        raise RuntimeError("Stage 3B.5 primary family must contain 40 unique tests")
    return rows


def evaluate_stage3b5_decision(
    cells: Sequence[Mapping[str, Any]], *, controls_pass: bool
) -> dict[str, Any]:
    """Apply the frozen hierarchy to the four coordinate/window cells."""
    if len(cells) != 4:
        raise ValueError("Stage 3B.5 decision requires four coordinate/window cells")
    if not controls_pass:
        return {
            "recommendation": "REDIRECT — Broader residual/norm interaction",
            "rationale": "One or more technical or paired-restoration controls failed.",
            "qualifying_cells": {},
        }

    upstream = [row for row in cells if bool(row["final_block"]["robust"]) and bool(row["first_h_pre"]["robust"]) and float(row["first_h_pre"]["final_block_ratio_median"]) >= 0.80]
    sequential = [row for row in cells if bool(row["two_layer_recompute"]["qualifies"])]
    attention = [row for row in cells if bool(row["attention_gain"]["qualifies"])]
    mlp = [row for row in cells if bool(row["mlp_gain"]["qualifies"])]

    def identity(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
        return [
            {"coordinate": str(row["coordinate"]), "window": str(row["window"])}
            for row in rows
        ]

    if len(upstream) >= 2:
        recommendation = "GO — Upstream residual-origin search"
        rationale = "First-layer h_pre restoration is robust and reaches at least 80% of final block restoration in at least two fixed cells."
    elif len(sequential) >= 2:
        recommendation = "GO — Cross-layer sequential mediation"
        rationale = "Two-layer entry-state recomputation meets the frozen block-closure and precomputed-output gain rule in at least two fixed cells."
    elif len(attention) >= 2 or len(mlp) >= 2:
        attention_strength = sum(float(row["attention_gain"].get("gain_to_final_block_median", 0.0)) for row in cells)
        mlp_strength = sum(float(row["mlp_gain"].get("gain_to_final_block_median", 0.0)) for row in cells)
        if len(attention) >= 2 and (len(mlp) < 2 or attention_strength >= mlp_strength):
            recommendation = "GO — Attention head/path localization"
            rationale = "The post-Attention boundary gain meets the frozen robust gain and dominance rule in at least two fixed cells."
        else:
            recommendation = "GO — MLP/residual mechanism localization"
            rationale = "The post-block boundary gain meets the frozen robust gain and dominance rule in at least two fixed cells."
    else:
        recommendation = "REDIRECT — Broader residual/norm interaction"
        rationale = "No predeclared boundary or two-layer recompute category explains the robust final-block effect in at least two fixed cells."
    return {
        "recommendation": recommendation,
        "rationale": rationale,
        "qualifying_cells": {
            "upstream": identity(upstream),
            "cross_layer_sequential": identity(sequential),
            "attention": identity(attention),
            "mlp": identity(mlp),
        },
        "category_cell_counts": {
            "upstream": len(upstream),
            "cross_layer_sequential": len(sequential),
            "attention": len(attention),
            "mlp": len(mlp),
        },
    }


__all__ = [
    "BOUNDARIES", "COORDINATES", "WINDOWS", "build_primary_family",
    "evaluate_stage3b5_decision", "holm_adjust",
]
