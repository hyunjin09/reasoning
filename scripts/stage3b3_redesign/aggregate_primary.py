#!/usr/bin/env python3
"""Aggregate the frozen 41-base Stage 3B.3-R primary coarse run."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.stage3b3.aggregate_coarse import grouped_statistics, summary
from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage3b3_redesign.primary import apply_redesign_fine_rule


ROOT = PROJECT_ROOT
OUT = ROOT / "outputs/stage3b3_redesign"
RAW = OUT / "primary/raw/shards"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def compact(row: dict[str, Any], *, drop: tuple[str, ...] = ("controls",)) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key not in drop}


def metric_rows(
    rows: list[dict[str, Any]], *, metrics: tuple[str, ...], key_fields: tuple[str, ...]
) -> list[dict[str, Any]]:
    return grouped_statistics(rows, key_fields=key_fields, metrics=metrics)


def main() -> None:
    manifest = read_jsonl(OUT / "primary/primary_41_manifest.jsonl")
    expected = {str(row["base_problem_id"]) for row in manifest}
    result_paths = sorted(RAW.glob("primary_*/examples/*/result.json"))
    results = [read_json(path) for path in result_paths]
    observed = [str(row["base_problem_id"]) for row in results]
    if len(results) != 41 or set(observed) != expected or len(set(observed)) != 41:
        raise RuntimeError(f"Primary run incomplete: expected 41 unique bases, observed {len(results)}/{len(set(observed))}")
    shard_summaries = [read_json(path) for path in sorted(RAW.glob("primary_*/result.json"))]
    if len(shard_summaries) != 8:
        raise RuntimeError(f"Expected eight completed shard summaries, observed {len(shard_summaries)}")

    path_by_base = {path.parent.name: str(path.relative_to(ROOT)) for path in result_paths}
    switch_rows: list[dict[str, Any]] = []
    restoration_rows: list[dict[str, Any]] = []
    cumulative_rows: list[dict[str, Any]] = []
    activation_rows: list[dict[str, Any]] = []
    positive_rows: list[dict[str, Any]] = []
    render_rows: list[dict[str, Any]] = []

    for problem in results:
        base = str(problem["base_problem_id"])
        metadata = {
            "base_problem_id": base,
            "example_id": str(problem["example_id"]),
            "evidence_type": problem["evidence_type"],
            "ed_alignment": problem["ed_alignment"],
            "paired_semantic_restoration_included": bool(problem["paired_semantic_restoration_included"]),
            "raw_result": path_by_base[base],
        }
        for point in problem["coordinates"]:
            point_meta = {
                **metadata,
                "coordinate": point["coordinate"],
                "switch_generated_index": point["switch_generated_index"],
                "stage3b2_all_layer_BRI": point["stage3b2_all_layer_BRI"],
            }
            positive_rows.append({
                **point_meta,
                **point["positive_control"],
                "all_switch_audits_valid": point["all_switch_audits_valid"],
                "all_scores_finite": point["all_scores_finite"],
            })
            full_paired = point.get("full_paired_semantic_controls")
            if full_paired is not None:
                render_rows.append({**point_meta, "arm": "all_layer", "window": "all_layers", **full_paired})
            for row in point["selective"]:
                public = {**point_meta, **compact(row)}
                switch_rows.append(public)
                paired = row.get("paired_semantic_controls")
                if paired is not None:
                    render_rows.append({
                        **point_meta,
                        "arm": "selective",
                        "window": row["name"],
                        **paired,
                    })
            for row in point["semantic_restoration"]:
                public = {**point_meta, **compact(row)}
                restoration_rows.append(public)
                render_rows.append({
                    **point_meta,
                    "arm": "restoration",
                    "window": row["name"],
                    **{
                        key: row[key] for key in (
                            "A_O_original_history", "A_C_original_history",
                            "A_O_counterfactual_history", "A_C_counterfactual_history",
                            "A_render", "BSRC", "BSRC_normalized", "active",
                            "render_to_semantic_ratio", "render_to_all_layer_ratio",
                        )
                    },
                })
            cumulative_rows.extend({**point_meta, **compact(row)} for row in point["cumulative"])
        activation_rows.extend(
            {**metadata, "coordinate": "Ed", **compact(row)} for row in problem["activation_patches"]
        )

    primary = OUT / "primary"
    write_jsonl(primary / "coarse_window_switch_results.jsonl", switch_rows)
    write_jsonl(primary / "semantic_restoration_results.jsonl", restoration_rows)
    write_jsonl(primary / "cumulative_layer_results.jsonl", cumulative_rows)
    write_jsonl(primary / "activation_patch_results.jsonl", activation_rows)
    write_jsonl(primary / "positive_control_results.jsonl", positive_rows)
    write_jsonl(primary / "render_control_results.jsonl", render_rows)

    sufficiency = metric_rows(
        switch_rows,
        key_fields=("coordinate", "name"),
        metrics=("S_W_O_to_C", "S_W_C_to_O", "BWS", "BWS_normalized"),
    )
    restoration = metric_rows(
        restoration_rows,
        key_fields=("coordinate", "name"),
        metrics=("SRC_O", "SRC_C", "BSRC", "BSRC_normalized", "A_render"),
    )
    cumulative = metric_rows(
        cumulative_rows,
        key_fields=("coordinate", "family", "name"),
        metrics=("BWS", "BWS_normalized"),
    )
    activation = metric_rows(
        activation_rows,
        key_fields=("after_layer",),
        metrics=("A_O_receive_C", "A_C_receive_O", "BAP", "BAP_normalized"),
    )

    for stat in sufficiency:
        subset = [row for row in switch_rows if row["coordinate"] == stat["coordinate"] and row["name"] == stat["name"]]
        stat["bidirectional_consistency_fraction"] = sum(bool(row["bidirectionally_source_consistent"]) for row in subset) / len(subset)
        stat["sham_window_shift"] = summary([float(row["sham_window_shift"]) for row in subset])
    for stat in restoration:
        subset = [row for row in restoration_rows if row["coordinate"] == stat["coordinate"] and row["name"] == stat["name"]]
        stat["bidirectional_consistency_fraction"] = sum(bool(row["bidirectionally_source_consistent"]) for row in subset) / len(subset)
        stat["active_fraction"] = sum(bool(row["active"]) for row in subset) / len(subset)
        stat["render_to_semantic_ratio"] = summary([float(row["render_to_semantic_ratio"]) for row in subset if row["render_to_semantic_ratio"] is not None])
        stat["render_to_all_layer_ratio"] = summary([float(row["render_to_all_layer_ratio"]) for row in subset if row["render_to_all_layer_ratio"] is not None])

    restoration_map = {(row["coordinate"], row["name"]): row for row in restoration}
    fine_input = []
    for row in sufficiency:
        key = (row["coordinate"], row["name"])
        if key not in restoration_map:
            raise RuntimeError(f"Missing numeric restoration statistics for {key}")
        fine_input.append({
            "coordinate": row["coordinate"],
            "name": row["name"],
            "statistics": {
                "BWS_normalized": row["statistics"]["BWS_normalized"],
                "BSRC_normalized": restoration_map[key]["statistics"]["BSRC_normalized"],
            },
        })
    fine_gate = apply_redesign_fine_rule(fine_input)

    render_statistics = metric_rows(
        render_rows,
        key_fields=("arm", "coordinate", "window"),
        metrics=("A_render", "BSRC", "BSRC_normalized", "render_to_semantic_ratio", "render_to_all_layer_ratio"),
    )
    analysis = OUT / "analysis"
    write_json(analysis / "layer_statistics.json", {
        "primary_base_problem_count": 41,
        "numeric_restoration_base_count": 37,
        "sufficiency": sufficiency,
        "semantic_restoration": restoration,
        "cumulative": cumulative,
        "activation": activation,
    })
    write_json(analysis / "semantic_restoration_statistics.json", {
        "independent_unit": "base_problem_id",
        "N": 37,
        "rows": restoration,
    })
    write_json(analysis / "render_control_statistics.json", {"rows": render_statistics})
    write_json(analysis / "fine_localization_gate.json", fine_gate)
    write_json(OUT / "config/fine_layer_windows.json", {
        "source_rule": "outputs/stage3b3/config/fine_localization_rule.json",
        "redesign_application": "outputs/stage3b3_redesign/config/redesign_fine_rule_application.json",
        "primary_coarse_results_frozen_before_application": True,
        **fine_gate,
    })

    exact_primary = {str(row["base_problem_id"]) for row in results if row["ed_alignment"] == "exact_baseline_tokens"}
    exact_switch = [row for row in switch_rows if row["base_problem_id"] in exact_primary]
    exact_restoration = [row for row in restoration_rows if row["base_problem_id"] in exact_primary]
    validation_switch = read_jsonl(OUT / "validation/selective_switch_validation.jsonl")
    validation_restoration = read_jsonl(OUT / "validation/paired_semantic_restoration_results.jsonl")
    validation_results = [
        read_json(path)
        for path in sorted((OUT / "validation/raw/shards").glob("validation_*/examples/*/result.json"))
    ]
    validation_exact = {
        str(row["base_problem_id"])
        for row in validation_results
        if row["ed_alignment"] == "exact_baseline_tokens"
    }
    pooled_switch = [
        {**row, "window": row["name"]} for row in exact_switch
    ] + [row for row in validation_switch if row["base_problem_id"] in validation_exact]
    pooled_restoration = [
        {**row, "window": row["name"]} for row in exact_restoration
    ] + [row for row in validation_restoration if row["base_problem_id"] in validation_exact]
    write_json(analysis / "exact_baseline_robustness.json", {
        "fine_selection_frozen_before_pooling_validation_cases": True,
        "primary": {
            "N": len(exact_primary),
            "base_problem_ids": sorted(exact_primary, key=int),
            "sufficiency": metric_rows(exact_switch, key_fields=("coordinate", "name"), metrics=("BWS", "BWS_normalized")),
            "semantic_restoration": metric_rows(exact_restoration, key_fields=("coordinate", "name"), metrics=("BSRC", "BSRC_normalized")),
        },
        "pooled_secondary": {
            "N": len(exact_primary | validation_exact),
            "base_problem_ids": sorted(exact_primary | validation_exact, key=int),
            "sufficiency": metric_rows(pooled_switch, key_fields=("coordinate", "window"), metrics=("BWS", "BWS_normalized")),
            "semantic_restoration": metric_rows(pooled_restoration, key_fields=("coordinate", "window"), metrics=("BSRC", "BSRC_normalized")),
        },
    })

    row_counts = {
        "coarse_switch": len(switch_rows),
        "semantic_restoration": len(restoration_rows),
        "cumulative": len(cumulative_rows),
        "activation": len(activation_rows),
        "positive_control": len(positive_rows),
    }
    expected_row_counts = {
        "coarse_switch": 41 * 2 * 6,
        "semantic_restoration": 37 * 2 * 6,
        "cumulative": 41 * 2 * 12,
        "activation": 41 * 6,
        "positive_control": 41 * 2,
    }
    mechanical = {
        "eight_shards_complete": len(shard_summaries) == 8,
        "all_expected_rows_present": row_counts == expected_row_counts,
        "all_condition_layout_exact": all(row["all_condition_layout_exact"] for row in shard_summaries),
        "all_capture_layers_valid": all(row["all_capture_layers_valid"] for row in shard_summaries),
        "all_positive_controls_exact": all(row["all_positive_controls_exact"] for row in shard_summaries),
        "all_layer_switch_audits_valid": all(row["all_layer_switch_audits_valid"] for row in shard_summaries),
        "all_residual_patch_audits_valid": all(row["all_residual_patch_audits_valid"] for row in shard_summaries),
        "all_self_controls_exact": all(row["all_self_controls_exact"] for row in shard_summaries),
        "all_scores_finite": all(row["all_scores_finite"] for row in shard_summaries),
    }
    write_json(analysis / "primary_aggregation_validation.json", {
        "status": "PASS" if all(mechanical.values()) else "FAIL",
        "base_problem_count": len(results),
        "unique_base_problem_count": len(set(observed)),
        "numeric_restoration_base_count": sum(row["paired_semantic_restoration_included"] for row in results),
        "evidence_type_counts": dict(Counter(row["evidence_type"] for row in results)),
        "alignment_counts": dict(Counter(row["ed_alignment"] for row in results)),
        "row_counts": row_counts,
        "expected_row_counts": expected_row_counts,
        "mechanical_controls": mechanical,
        "selection_used_attention": False,
    })
    print(json.dumps({
        "bases": len(results),
        "fine_qualifying_union": fine_gate["qualifying_union"],
        "fine_window_count": len(fine_gate["fine_windows"]),
        "mechanics_pass": all(mechanical.values()),
    }, indent=2))


if __name__ == "__main__":
    main()
