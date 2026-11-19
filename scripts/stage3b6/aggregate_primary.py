#!/usr/bin/env python3
"""Aggregate frozen Stage 3B.6 head confirmation and upstream-control results."""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage3b4.metrics import bootstrap_summary, one_sided_wilcoxon_greater
from visual_reasoning.stage3b4.protocol import holm_adjust
from visual_reasoning.stage3b6.protocol import primary_head_passes


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


def flatten(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "base_problem_id": str(base["base_problem_id"]),
            "example_id": str(base["example_id"]),
            "evidence_type": base["evidence_type"],
            **unit,
        }
        for base in rows
        for cell in base["cells"]
        for unit in cell["unit_results"]
    ]


def load_phase(phase: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    directories = sorted((OUT / "scoring/raw").glob(f"{phase}_*"))
    if len(directories) != 2:
        raise RuntimeError(f"Expected two {phase} shards, observed {len(directories)}")
    summaries = [read_json(path / "result.json") for path in directories]
    if not all(bool(row["all_mechanical_controls_passed"]) for row in summaries):
        raise RuntimeError(f"{phase} mechanical controls failed")
    rows = [row for path in directories for row in read_jsonl(path / "results.jsonl")]
    return rows, summaries


def summarize_unit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [float(row["BHR"]) for row in rows]
    hrr = [float(row["HRR"]) for row in rows if row["HRR"] is not None]
    sham_ratios = [
        float(row["sham_to_semantic_ratio"])
        for row in rows
        if row["sham_to_semantic_ratio"] is not None
    ]
    bootstrap = bootstrap_summary(values)
    return {
        "base_count": len(rows),
        "mean_BHR": bootstrap["mean"],
        "median_BHR": bootstrap["median"],
        "bootstrap_95_CI": bootstrap["bootstrap_95_CI"],
        "bootstrap_resamples": bootstrap["bootstrap_resamples"],
        "raw_p": one_sided_wilcoxon_greater(values),
        "bidirectional_count": sum(
            bool(row["bidirectionally_source_consistent"]) for row in rows
        ),
        "bidirectional_fraction": sum(
            bool(row["bidirectionally_source_consistent"]) for row in rows
        )
        / len(rows),
        "median_HRR": median(hrr),
        "median_sham_effect": median([float(row["sham_effect"]) for row in rows]),
        "median_sham_to_semantic_ratio": median(sham_ratios),
        "all_self_exact": all(bool(row["all_self_restorations_exact"]) for row in rows),
        "all_query_head_selectivity_valid": all(
            bool(row["mechanical_audit"]["all_query_head_selectivity_valid"])
            for row in rows
        ),
        "all_source_group_isolation_valid": all(
            bool(row["mechanical_audit"]["all_source_group_isolation_valid"])
            for row in rows
        ),
        "all_scores_finite": all(bool(row["all_scores_finite"]) for row in rows),
    }


def main() -> None:
    config = read_json(OUT / "config/stage3b6_config.json")
    split = read_json(OUT / "config/discovery_primary_split.json")
    freeze = read_json(OUT / "config/frozen_head_candidates.json")
    primary_bases, primary_shards = load_phase("primary")
    upstream_bases, upstream_shards = load_phase("upstream")
    expected = set(split["primary_base_problem_ids"])
    if {str(row["base_problem_id"]) for row in primary_bases} != expected:
        raise RuntimeError("Primary confirmation base set changed")
    if {str(row["base_problem_id"]) for row in upstream_bases} != expected:
        raise RuntimeError("Upstream-control base set changed")
    primary = flatten(primary_bases)
    upstream = flatten(upstream_bases)

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in primary:
        grouped[(row["cell_id"], row["unit_id"])].append(row)
    summaries: list[dict[str, Any]] = []
    p_values: dict[str, float] = {}
    for (cell_id, unit_id), rows in sorted(grouped.items()):
        if len(rows) != 37:
            raise RuntimeError(f"Primary {cell_id}/{unit_id} has {len(rows)} bases")
        summary = {
            "test_id": f"{cell_id}__{unit_id}",
            "cell_id": cell_id,
            "unit_id": unit_id,
            "unit_kind": rows[0]["unit_kind"],
            "heads": rows[0]["heads"],
            **summarize_unit(rows),
        }
        summaries.append(summary)
        p_values[summary["test_id"]] = float(summary["raw_p"])
    adjusted = holm_adjust(p_values)
    for summary in summaries:
        correction = adjusted[summary["test_id"]]
        summary["holm_adjusted_p"] = float(correction["adjusted_p"])
        summary["holm_rejected"] = bool(correction["rejected"])
        summary["confirmed"] = primary_head_passes(summary)

    upstream_grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in upstream:
        upstream_grouped[(str(row["origin_cell_id"]), row["unit_id"])].append(row)
    upstream_summaries = []
    for (origin, unit_id), rows in sorted(upstream_grouped.items()):
        if len(rows) != 37:
            raise RuntimeError(f"Upstream {origin}/{unit_id} has {len(rows)} bases")
        upstream_summaries.append({
            "origin_cell_id": origin,
            "control_cell_id": "Ed__W5",
            "unit_id": unit_id,
            "unit_kind": rows[0]["unit_kind"],
            "heads": rows[0]["heads"],
            **summarize_unit(rows),
        })

    singles = [row for row in primary if row["unit_kind"] == "single"]
    cumulative = [row for row in primary if row["unit_kind"] == "cumulative_set"]
    write_jsonl(OUT / "scoring/primary_head_results.jsonl", singles)
    write_jsonl(OUT / "scoring/cumulative_headset_results.jsonl", cumulative)
    write_jsonl(OUT / "scoring/upstream_control_results.jsonl", upstream)

    by_cell = defaultdict(list)
    for summary in summaries:
        by_cell[summary["cell_id"]].append(summary)
    classifications = []
    threshold = float(config["mechanism_classification"]["most_gain_HRR_threshold"])
    for cell_id, rows in sorted(by_cell.items()):
        confirmed = [row for row in rows if row["confirmed"]]
        set_lookup = {row["unit_id"]: row for row in rows}
        if not confirmed:
            category = "H-No-Head-Recovery"
        elif any(
            set_lookup.get(label, {}).get("confirmed", False)
            and float(set_lookup[label]["median_HRR"]) >= threshold
            for label in ("Top_1", "Top_2")
        ):
            category = "H-Sparse"
        elif (
            set_lookup.get("Top_4", {}).get("confirmed", False)
            and float(set_lookup["Top_4"]["median_HRR"]) >= threshold
        ):
            category = "H-Small-Ensemble"
        elif any(
            set_lookup.get(label, {}).get("confirmed", False)
            and float(set_lookup[label]["median_HRR"]) >= threshold
            for label in ("Top_8", "All_robust")
        ):
            category = "H-Distributed"
        else:
            category = "H-Partial-Recovery"
        classifications.append({
            "cell_id": cell_id,
            "category": category,
            "confirmed_unit_ids": [row["unit_id"] for row in confirmed],
            "threshold": threshold,
        })

    target_rows = []
    for cell_id, rows in sorted(by_cell.items()):
        confirmed = [row for row in rows if row["confirmed"]]
        singles_confirmed = [row for row in confirmed if row["unit_kind"] == "single"]
        if singles_confirmed:
            chosen = max(singles_confirmed, key=lambda row: float(row["median_BHR"]))
            reason = "strongest confirmed single head"
        else:
            cumulative_confirmed = [
                row for row in confirmed if row["unit_kind"] == "cumulative_set"
            ]
            if not cumulative_confirmed:
                continue
            order = {"Top_1": 1, "Top_2": 2, "Top_4": 4, "Top_8": 8, "All_robust": 10_000}
            chosen = min(
                cumulative_confirmed,
                key=lambda row: (len(row["heads"]), order.get(row["unit_id"], 20_000)),
            )
            reason = "smallest confirmed cumulative set"
        target_rows.append({
            "cell_id": cell_id,
            "unit_id": chosen["unit_id"],
            "heads": chosen["heads"],
            "unit_kind": chosen["unit_kind"],
            "selection_reason": reason,
            "primary_median_BHR": chosen["median_BHR"],
            "primary_median_HRR": chosen["median_HRR"],
        })
    source_gate = bool(target_rows)
    source_targets = {
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "gate_passed": source_gate,
        "gate_rule": config["source_path_gate"],
        "target_cell_ids": [row["cell_id"] for row in target_rows],
        "targets": target_rows,
        "selection_used_attention": False,
    }
    write_json(OUT / "analysis/source_path_targets.json", source_targets)
    if source_gate:
        primary_manifest = read_jsonl(OUT / "config/primary_manifest.jsonl")
        shards = [primary_manifest[::2], primary_manifest[1::2]]
        ensure_directory(OUT / "config/shards/source")
        for index, rows in enumerate(shards):
            write_jsonl(OUT / f"config/shards/source/source_{index:02d}.jsonl", rows)

    statistics_payload = {
        "primary_unit": "base_problem_id",
        "base_count": 37,
        "frozen_family_size": len(summaries),
        "holm_family": adjusted,
        "unit_statistics": summaries,
        "confirmed_unit_count": sum(bool(row["confirmed"]) for row in summaries),
        "source_path_gate_passed": source_gate,
        "source_path_target_count": len(target_rows),
        "all_primary_mechanical_controls_passed": all(
            bool(row["all_mechanical_controls_passed"]) for row in primary_shards
        ),
    }
    write_json(OUT / "analysis/head_restoration_statistics.json", statistics_payload)
    write_json(
        OUT / "analysis/sparse_vs_distributed_heads.json",
        {
            "classification_threshold": threshold,
            "cells": classifications,
            "ratios_are_unclipped": True,
            "ratios_are_not_unique_information_fractions": True,
        },
    )
    write_json(
        OUT / "analysis/upstream_control_statistics.json",
        {
            "control_cell_id": "Ed__W5",
            "role": "upstream-state control; not pooled with qualifying cells",
            "unit_statistics": upstream_summaries,
        },
    )

    ensure_directory(OUT / "analysis/figures")
    summary_lookup = {(row["cell_id"], row["unit_id"]): row for row in summaries}
    figure, axes = plt.subplots(1, 3, figsize=(15, 4))
    for axis, cell_id in zip(axes, sorted(by_cell)):
        rows = sorted(by_cell[cell_id], key=lambda row: (row["unit_kind"], row["unit_id"]))
        axis.bar(
            range(len(rows)),
            [float(row["median_BHR"]) for row in rows],
            color=["#d62728" if row["confirmed"] else "#4c78a8" for row in rows],
        )
        axis.set_xticks(range(len(rows)), [row["unit_id"] for row in rows], rotation=60, ha="right")
        axis.set_title(cell_id)
        axis.set_ylabel("primary median BHR")
    figure.tight_layout()
    figure.savefig(OUT / "analysis/figures/02_confirmatory_frozen_heads.png", dpi=180)
    plt.close(figure)

    figure, axes = plt.subplots(1, 3, figsize=(15, 4))
    labels = ("Top_1", "Top_2", "Top_4", "Top_8", "All_robust")
    for axis, cell_id in zip(axes, sorted(by_cell)):
        available = [label for label in labels if (cell_id, label) in summary_lookup]
        axis.plot(
            available,
            [float(summary_lookup[(cell_id, label)]["median_HRR"]) for label in available],
            marker="o",
        )
        axis.axhline(threshold, color="black", linestyle="--", linewidth=0.8)
        axis.set_title(cell_id)
        axis.set_ylabel("median HRR vs Stage 3B.5 gain")
        axis.tick_params(axis="x", rotation=45)
    figure.tight_layout()
    figure.savefig(OUT / "analysis/figures/03_cumulative_head_recovery.png", dpi=180)
    plt.close(figure)

    confirmed_rows = [row for row in summaries if row["confirmed"]]
    figure, axis = plt.subplots(figsize=(max(8, len(confirmed_rows) * 0.6), 4))
    axis.bar(
        range(len(confirmed_rows)),
        [float(row["median_BHR"]) for row in confirmed_rows],
        color="#59a14f",
    )
    axis.set_xticks(
        range(len(confirmed_rows)),
        [f"{row['cell_id']}\n{row['unit_id']}" for row in confirmed_rows],
        rotation=60,
        ha="right",
    )
    axis.set_ylabel("confirmed median BHR")
    figure.tight_layout()
    figure.savefig(OUT / "analysis/figures/04_head_effects_across_cells.png", dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(max(8, len(upstream_summaries) * 0.35), 4))
    axis.bar(
        range(len(upstream_summaries)),
        [float(row["median_BHR"]) for row in upstream_summaries],
        color="#f28e2b",
    )
    axis.set_xticks(
        range(len(upstream_summaries)),
        [f"{row['origin_cell_id']}\n{row['unit_id']}" for row in upstream_summaries],
        rotation=70,
        ha="right",
    )
    axis.set_ylabel("E_d/W5 control median BHR")
    figure.tight_layout()
    figure.savefig(OUT / "analysis/figures/05_upstream_control_heads.png", dpi=180)
    plt.close(figure)


if __name__ == "__main__":
    main()
