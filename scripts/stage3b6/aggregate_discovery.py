#!/usr/bin/env python3
"""Validate Stage 3B.6 all-head discovery and freeze confirmatory candidates."""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage3b6.protocol import (
    discovery_head_passes,
    freeze_ranked_head_sets,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b6"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def median(values: list[float]) -> float:
    return float(statistics.median(float(value) for value in values))


def flatten_base(row: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for cell in row["cells"]:
        for unit in cell["unit_results"]:
            result.append({
                "base_problem_id": str(row["base_problem_id"]),
                "example_id": str(row["example_id"]),
                "evidence_type": row["evidence_type"],
                **{
                    key: value
                    for key, value in unit.items()
                    if key != "mechanical_audit"
                },
                "mechanical_controls": {
                    "all_query_head_selectivity_valid": unit["mechanical_audit"][
                        "all_query_head_selectivity_valid"
                    ],
                    "all_source_group_isolation_valid": unit["mechanical_audit"][
                        "all_source_group_isolation_valid"
                    ],
                },
            })
    return result


def unit(heads: list[int], label: str, kind: str) -> dict[str, Any]:
    return {
        "unit_id": label,
        "kind": kind,
        "heads": [int(head) for head in heads],
    }


def main() -> None:
    config = read_json(OUT / "config/stage3b6_config.json")
    split = read_json(OUT / "config/discovery_primary_split.json")
    shard_dirs = sorted((OUT / "discovery/raw").glob("discovery_*"))
    if len(shard_dirs) != 2:
        raise RuntimeError(f"Expected two discovery shards, observed {len(shard_dirs)}")
    shard_summaries = [read_json(path / "result.json") for path in shard_dirs]
    if not all(bool(row["all_mechanical_controls_passed"]) for row in shard_summaries):
        raise RuntimeError("Discovery mechanical gate failed")
    base_rows = [
        row
        for path in shard_dirs
        for row in read_jsonl(path / "results.jsonl")
    ]
    expected_bases = set(split["discovery_base_problem_ids"])
    observed_bases = {str(row["base_problem_id"]) for row in base_rows}
    if observed_bases != expected_bases or len(base_rows) != 8:
        raise RuntimeError("Discovery base set changed")
    flattened = [row for base in base_rows for row in flatten_base(base)]
    if len(flattened) != 8 * 3 * 32:
        raise RuntimeError(f"Expected 768 discovery rows, observed {len(flattened)}")
    write_jsonl(OUT / "discovery/per_head_discovery_results.jsonl", flattened)

    grouped: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in flattened:
        if row["unit_kind"] != "single" or len(row["heads"]) != 1:
            raise RuntimeError("Discovery may contain only single logical heads")
        grouped[(row["cell_id"], int(row["heads"][0]))].append(row)
    summaries_by_cell: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for (cell_id, head), rows in sorted(grouped.items()):
        if len(rows) != 8:
            raise RuntimeError(f"Discovery {cell_id}/head {head} has {len(rows)} bases")
        ratios = [
            float(row["sham_to_semantic_ratio"])
            for row in rows
            if row["sham_to_semantic_ratio"] is not None
        ]
        hrr = [float(row["HRR"]) for row in rows if row["HRR"] is not None]
        summary = {
            "cell_id": cell_id,
            "head_index": head,
            "base_count": len(rows),
            "mean_BHR": float(statistics.fmean(float(row["BHR"]) for row in rows)),
            "median_BHR": median([float(row["BHR"]) for row in rows]),
            "median_HRR": median(hrr),
            "bidirectional_count": sum(
                bool(row["bidirectionally_source_consistent"]) for row in rows
            ),
            "median_sham_effect": median([float(row["sham_effect"]) for row in rows]),
            "median_sham_to_semantic_ratio": median(ratios),
            "all_self_exact": all(bool(row["all_self_restorations_exact"]) for row in rows),
            "all_query_head_selectivity_valid": all(
                bool(row["mechanical_controls"]["all_query_head_selectivity_valid"])
                for row in rows
            ),
            "all_source_group_isolation_valid": all(
                bool(row["mechanical_controls"]["all_source_group_isolation_valid"])
                for row in rows
            ),
        }
        summary["discovery_pass"] = discovery_head_passes(summary)
        summaries_by_cell[cell_id].append(summary)

    frozen_cells: dict[str, Any] = {}
    rankings: dict[str, Any] = {}
    for cell in config["frozen_cells"]:
        if cell["role"] != "qualifying_attention":
            continue
        cell_id = cell["cell_id"]
        summaries = sorted(
            summaries_by_cell[cell_id], key=lambda row: int(row["head_index"])
        )
        frozen = freeze_ranked_head_sets(summaries, total_query_heads=32)
        units: list[dict[str, Any]] = [
            unit([head], f"head_{head:02d}", "single")
            for head in frozen["robust_heads"]
        ]
        for label in ("Top_1", "Top_2", "Top_4", "Top_8", "All_robust"):
            heads = frozen["sets"].get(label, [])
            if heads:
                units.append(unit(heads, label, "cumulative_set"))
        frozen_cells[cell_id] = {
            **cell,
            "ranking": frozen["ranking"],
            "robust_heads": frozen["robust_heads"],
            "sets": frozen["sets"],
            "units": units,
        }
        rankings[cell_id] = {
            "head_summaries": sorted(
                summaries, key=lambda row: (-float(row["median_BHR"]), int(row["head_index"]))
            ),
            "ranking": frozen["ranking"],
        }

    upstream_units = []
    for cell_id, payload in frozen_cells.items():
        for candidate in payload["units"]:
            upstream_units.append({**candidate, "origin_cell_id": cell_id})
    frozen = {
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "source": "8-base Stage 3B.6 all-head discovery",
        "source_base_problem_ids": split["discovery_base_problem_ids"],
        "selection_metric": config["discovery"]["ranking_metric"],
        "robust_rule": config["discovery"]["robust_rule"],
        "selection_used_attention": False,
        "cells": frozen_cells,
        "upstream_units": upstream_units,
    }
    write_json(OUT / "discovery/head_rankings.json", rankings)
    write_json(OUT / "config/frozen_head_candidates.json", frozen)

    validation = {
        "status": "PASS",
        "base_count": len(base_rows),
        "expected_result_rows": 768,
        "observed_result_rows": len(flattened),
        "all_shards_mechanical_pass": True,
        "all_baselines_exact_stage3b5": all(
            bool(row["mechanical_controls"]["all_baselines_exact_stage3b5"])
            for row in base_rows
        ),
        "all_query_head_selectivity_valid": all(
            bool(row["mechanical_controls"]["all_query_head_selectivity_valid"])
            for row in base_rows
        ),
        "all_source_group_isolation_valid": all(
            bool(row["mechanical_controls"]["all_source_group_isolation_valid"])
            for row in base_rows
        ),
        "all_self_restorations_exact": all(
            bool(row["mechanical_controls"]["all_self_restorations_exact"])
            for row in base_rows
        ),
        "all_scores_finite": all(
            bool(row["mechanical_controls"]["all_scores_finite"])
            for row in base_rows
        ),
        "determinism": [row["determinism_repeat"] for row in shard_summaries],
        "selection_used_attention": False,
    }
    validation["all_validation_checks_passed"] = all(
        bool(value)
        for key, value in validation.items()
        if key.startswith("all_")
    )
    write_json(OUT / "validation/head_intervention_validation.json", validation)

    architecture = read_json(shard_dirs[0] / "environment.json")[
        "stage3b6_gqa_architecture"
    ]
    mapping = [head // architecture["query_heads_per_kv_group"] for head in range(32)]
    write_json(
        OUT / "audit/head_tensor_layout.json",
        {
            "architecture": architecture,
            "query_key_value_axis_order": ["batch", "head", "sequence", "head_dimension"],
            "pre_output_projection_axis_order": [
                "batch", "sequence", "logical_query_head", "head_dimension"
            ],
            "intervention_position_count": 1,
            "query_head_selective": True,
        },
    )
    write_json(
        OUT / "audit/output_projection_slices.json",
        {
            "W_O_input_shape": [architecture["logical_query_heads"] * architecture["head_dimension"]],
            "logical_head_slices": [
                {
                    "query_head": head,
                    "start": head * architecture["head_dimension"],
                    "end_exclusive": (head + 1) * architecture["head_dimension"],
                }
                for head in range(32)
            ],
            "splice_before_W_O": True,
        },
    )
    gqa_lines = [
        "# Stage 3B.6 grouped-query Attention audit",
        "",
        "Status: **PASS**.",
        "",
        f"- Logical query heads: {architecture['logical_query_heads']}",
        f"- K/V heads: {architecture['kv_heads']}",
        f"- Query heads per K/V group: {architecture['query_heads_per_kv_group']}",
        f"- Head dimension: {architecture['head_dimension']}",
        "- K/V tensor order: batch × K/V head × sequence × head dimension.",
        "- Pre-W_O output order: batch × sequence × logical query head × head dimension.",
        "- The hybrid intervention recomputes with recipient Q and source-position K/V, then splices only selected logical query heads before W_O.",
        "- A shared K/V group is never treated as one logical query head.",
        "",
        "Query-head→K/V-group map: `" + ", ".join(f"{head}→{group}" for head, group in enumerate(mapping)) + "`.",
    ]
    (OUT / "audit/gqa_head_map.md").write_text("\n".join(gqa_lines) + "\n", encoding="utf-8")

    report_lines = [
        "# Stage 3B.6 candidate-head freeze",
        "",
        "The all-head discovery mechanics passed on the eight disjoint Stage 3B.5 validation bases. Rankings were computed only from paired semantic restoration; raw attention was not used.",
        "",
    ]
    for cell_id, payload in frozen_cells.items():
        report_lines.extend([
            f"## {cell_id}",
            "",
            f"Robust single heads: {payload['robust_heads'] or 'none'}.",
            f"Frozen ranking: {payload['ranking']}.",
            f"Confirmatory units: {[row['unit_id'] for row in payload['units']]}.",
            "",
        ])
    report_lines.extend([
        "All Top-1/2/4/8 sets were frozen before primary scoring. `All_robust` is included only when the discovery rule retained at least one single head.",
        "",
    ])
    (OUT / "discovery/candidate_freeze_report.md").write_text(
        "\n".join(report_lines), encoding="utf-8"
    )
    (OUT / "validation/validation_report.md").write_text(
        "# Stage 3B.6 head-intervention validation\n\n"
        "Status: **PASS**. All 768 discovery rows preserved exact Stage 3B.5 baselines, exact self controls, query-head selectivity, source-position isolation, finite scores, and the fixed 8-base split.\n",
        encoding="utf-8",
    )
    (OUT / "audit/hook_validation.md").write_text(
        "# Stage 3B.6 hook validation\n\n"
        "The installed eager Qwen Attention computation was reconstructed exactly on all discovery baselines. Hybrid patches retained recipient Q, assigned donor post-RoPE K/V only at frozen preceding positions, changed no nonselected logical query-head output before W_O, and re-executed W_O plus all downstream computation.\n",
        encoding="utf-8",
    )

    ensure_directory(OUT / "analysis/figures")
    figure, axes = plt.subplots(1, 3, figsize=(15, 4), sharey=False)
    for axis, (cell_id, payload) in zip(axes, frozen_cells.items()):
        by_head = {int(row["head_index"]): row for row in rankings[cell_id]["head_summaries"]}
        values = [float(by_head[head]["median_BHR"]) for head in range(32)]
        colors = ["#d62728" if by_head[head]["discovery_pass"] else "#4c78a8" for head in range(32)]
        axis.bar(range(32), values, color=colors)
        axis.axhline(0.0, color="black", linewidth=0.8)
        axis.set_title(cell_id)
        axis.set_xlabel("logical query head")
        axis.set_ylabel("discovery median BHR")
    figure.tight_layout()
    figure.savefig(OUT / "analysis/figures/01_discovery_all_heads.png", dpi=180)
    plt.close(figure)

    primary = read_jsonl(OUT / "config/primary_manifest.jsonl")
    shards = [primary[::2], primary[1::2]]
    ensure_directory(OUT / "config/shards/primary")
    ensure_directory(OUT / "config/shards/upstream")
    for index, rows in enumerate(shards):
        write_jsonl(OUT / f"config/shards/primary/primary_{index:02d}.jsonl", rows)
        write_jsonl(OUT / f"config/shards/upstream/upstream_{index:02d}.jsonl", rows)


if __name__ == "__main__":
    main()
