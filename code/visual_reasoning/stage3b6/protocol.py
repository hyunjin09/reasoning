"""Frozen cells, ranking, and gates for Stage 3B.6."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def build_frozen_cells(
    *,
    target_by_window: Mapping[str, Mapping[str, Any]],
    qualifying: Mapping[str, Sequence[Mapping[str, str]]],
) -> list[dict[str, Any]]:
    """Resolve exact target layers from frozen Stage 3B.5 layer roles."""

    expected_attention = [
        ("Ed_minus_1", "W4", "first"),
        ("Ed_minus_1", "W5", "first"),
        ("Ed", "W4", "second"),
    ]
    observed = {
        (str(row["coordinate"]), str(row["window"]))
        for row in qualifying.get("attention", ())
    }
    if observed != {(coordinate, window) for coordinate, window, _ in expected_attention}:
        raise ValueError("Stage 3B.5 qualifying Attention cells changed")
    upstream = {
        (str(row["coordinate"]), str(row["window"]))
        for row in qualifying.get("upstream", ())
    }
    if upstream != {("Ed", "W5")}:
        raise ValueError("Stage 3B.5 upstream control changed")

    cells: list[dict[str, Any]] = []
    for coordinate, window, layer_role in expected_attention:
        layers = [int(value) for value in target_by_window[window]["layers"]]
        role_index = 0 if layer_role == "first" else 1
        cells.append({
            "cell_id": f"{coordinate}__{window}",
            "coordinate": coordinate,
            "window": window,
            "fine_window": str(target_by_window[window]["fine_window"]),
            "layer_role": layer_role,
            "layer_index": layers[role_index],
            "role": "qualifying_attention",
        })
    w5_layers = [int(value) for value in target_by_window["W5"]["layers"]]
    cells.append({
        "cell_id": "Ed__W5",
        "coordinate": "Ed",
        "window": "W5",
        "fine_window": str(target_by_window["W5"]["fine_window"]),
        "layer_role": "first",
        "layer_index": w5_layers[0],
        "role": "upstream_control",
    })
    return cells


def discovery_head_passes(summary: Mapping[str, Any]) -> bool:
    return bool(
        int(summary["base_count"]) == 8
        and float(summary["median_BHR"]) > 0.0
        and int(summary["bidirectional_count"]) >= 7
        and float(summary["median_sham_to_semantic_ratio"]) <= 0.25
        and bool(summary["all_self_exact"])
        and float(summary["median_HRR"]) >= 0.10
    )


def primary_head_passes(summary: Mapping[str, Any]) -> bool:
    return bool(
        float(summary["holm_adjusted_p"]) < 0.05
        and float(summary["bootstrap_95_CI"][0]) > 0.0
        and float(summary["bidirectional_fraction"]) >= 0.70
        and float(summary["median_sham_to_semantic_ratio"]) < 0.25
        and bool(summary["all_self_exact"])
        and float(summary["median_HRR"]) >= 0.25
    )


def freeze_ranked_head_sets(
    summaries: Sequence[Mapping[str, Any]], *, total_query_heads: int
) -> dict[str, Any]:
    if len(summaries) != int(total_query_heads):
        raise ValueError("Discovery ranking requires every logical query head exactly once")
    heads = [int(row["head_index"]) for row in summaries]
    if sorted(heads) != list(range(int(total_query_heads))):
        raise ValueError("Discovery head indices are incomplete or duplicated")
    ordered = sorted(
        summaries,
        key=lambda row: (-float(row["median_BHR"]), int(row["head_index"])),
    )
    ranking = [int(row["head_index"]) for row in ordered]
    robust = [
        int(row["head_index"])
        for row in ordered
        if bool(row.get("discovery_pass", False))
    ]
    sets: dict[str, list[int]] = {}
    for size in (1, 2, 4, 8):
        if total_query_heads >= size:
            sets[f"Top_{size}"] = ranking[:size]
    sets["All_robust"] = robust
    return {"ranking": ranking, "robust_heads": robust, "sets": sets}


__all__ = [
    "build_frozen_cells",
    "discovery_head_passes",
    "freeze_ranked_head_sets",
    "primary_head_passes",
]
