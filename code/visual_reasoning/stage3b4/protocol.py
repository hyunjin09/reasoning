"""Prospectively frozen Stage 3B.4 target and decision helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


MODULES = ("attention", "mlp", "joint", "block")
COORDINATES = ("Ed_minus_1", "Ed")
WINDOWS = ("W4", "W5")


def holm_adjust(
    p_values: Mapping[str, float], *, alpha: float = 0.05
) -> dict[str, dict[str, float | bool]]:
    """Holm-adjust one fixed family while preserving key identity."""
    ordered = sorted((float(value), str(key)) for key, value in p_values.items())
    running = 0.0
    adjusted: dict[str, dict[str, float | bool]] = {}
    family_size = len(ordered)
    for rank, (raw, key) in enumerate(ordered):
        running = max(running, min(1.0, raw * (family_size - rank)))
        adjusted[key] = {
            "raw_p": raw,
            "adjusted_p": running,
            "rejected": running <= float(alpha),
        }
    return adjusted


def retained_module_targets(
    *, decision: Mapping[str, Any], fine_rows: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    """Load exactly one retained fine window for each authorized W4/W5 cell."""
    authorized = {
        (str(row["coordinate"]), str(row["window"]))
        for row in decision["narrow_candidates"]
        if bool(row["fine_retains"])
    }
    expected = {(coordinate, window) for coordinate in COORDINATES for window in WINDOWS}
    if authorized != expected:
        raise ValueError("Stage 3B.4 requires the four frozen W4/W5 narrow candidates")

    targets = []
    for coordinate, window in sorted(expected):
        retained = [
            row
            for row in fine_rows
            if str(row["coordinate"]) == coordinate
            and str(row["parent_window"]) == window
            and max(float(row["BWS_median"]), float(row["BSRC_median"])) >= 0.15
        ]
        if len(retained) != 1:
            raise ValueError(
                f"Expected one retained fine window for {coordinate}/{window}, observed {len(retained)}"
            )
        row = retained[0]
        targets.append({
            "coordinate": coordinate,
            "window": window,
            "fine_window": str(row["name"]),
            "layers": [int(value) for value in row["layers"]],
            "source": "outputs/stage3b3_redesign/analysis/fine_layer_statistics.json",
        })
    return targets


def evaluate_module_decision(
    rows: Sequence[Mapping[str, Any]], *, controls_pass: bool
) -> dict[str, Any]:
    """Classify the fixed four cells using prospective module/block ratios."""
    if not controls_pass:
        return {
            "recommendation": "REDESIGN",
            "rationale": "One or more restoration or intervention-integrity controls failed.",
            "attention_cells": [],
            "mlp_cells": [],
            "cascade_cells": [],
            "block_robust_cells": [],
        }
    if len(rows) != 4:
        raise ValueError("The decision requires exactly four coordinate/window cells")

    attention_cells = []
    mlp_cells = []
    cascade_cells = []
    block_cells = []
    for row in rows:
        cell = {"coordinate": row["coordinate"], "window": row["window"]}
        if bool(row["block_robust"]):
            block_cells.append(cell)
        attention = row["attention"]
        mlp = row["mlp"]
        joint = row["joint"]
        attention_ratio = float(attention["block_ratio_median"])
        mlp_ratio = float(mlp["block_ratio_median"])
        joint_ratio = float(joint["block_ratio_median"])
        attention_modest = bool(attention["robust"]) and attention_ratio >= 0.20
        mlp_modest = bool(mlp["robust"]) and mlp_ratio >= 0.20
        joint_strong = bool(
            joint["robust"]
            and joint_ratio >= 0.70
            and float(joint["BMR_median"])
            >= max(float(attention["BMR_median"]), float(mlp["BMR_median"]))
        )
        if bool(row["block_robust"]) and attention_modest and mlp_modest and joint_strong:
            cascade_cells.append(cell)
        if bool(
            row["block_robust"]
            and attention["robust"]
            and attention_ratio >= 0.50
            and attention_ratio >= mlp_ratio + 0.20
        ):
            attention_cells.append(cell)
        if bool(
            row["block_robust"]
            and mlp["robust"]
            and mlp_ratio >= 0.50
            and mlp_ratio >= attention_ratio + 0.20
        ):
            mlp_cells.append(cell)

    if len(cascade_cells) >= 2:
        recommendation = "GO — Attention→MLP cascade analysis"
        rationale = "Both component restorations are robust in at least two cells and joint restoration is the strongest substantial block-relative effect."
    elif len(attention_cells) >= 2:
        recommendation = "GO — Attention-head/path localization"
        rationale = "Attention restoration is robust and contributes at least half of block restoration in at least two fixed cells while exceeding MLP restoration."
    elif len(mlp_cells) >= 2:
        recommendation = "GO — MLP mechanism localization"
        rationale = "MLP restoration is robust and contributes at least half of block restoration in at least two fixed cells while exceeding Attention restoration."
    elif len(block_cells) >= 2:
        recommendation = "REDIRECT — Distributed block computation"
        rationale = "Full-block restoration is robust in at least two cells, but no prespecified component attribution rule passes."
    else:
        recommendation = "REDESIGN"
        rationale = "The full-block bridge or restoration controls are insufficient for module attribution."
    return {
        "recommendation": recommendation,
        "rationale": rationale,
        "attention_cells": attention_cells,
        "mlp_cells": mlp_cells,
        "cascade_cells": cascade_cells,
        "block_robust_cells": block_cells,
        "category_cell_counts": {
            "attention": len(attention_cells),
            "mlp": len(mlp_cells),
            "cascade": len(cascade_cells),
            "block_robust": len(block_cells),
        },
    }
