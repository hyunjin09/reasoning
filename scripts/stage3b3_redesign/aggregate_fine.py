#!/usr/bin/env python3
"""Aggregate the prospectively gated Stage 3B.3-R two-layer refinement."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.stage3b3.aggregate_coarse import grouped_statistics
from visual_reasoning.stage0.io import write_json, write_jsonl


ROOT = PROJECT_ROOT
OUT = ROOT / "outputs/stage3b3_redesign"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def compact(row: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in row.items() if key != "controls"}


def main() -> None:
    gate = read_json(OUT / "analysis/fine_localization_gate.json")
    windows = gate["fine_windows"]
    if not windows:
        write_jsonl(OUT / "primary/fine_layer_results.jsonl", [])
        write_json(OUT / "analysis/fine_layer_statistics.json", {
            "status": "SKIPPED_NO_QUALIFYING_WINDOWS",
            "rows": [],
            "fine_windows": [],
        })
        write_json(OUT / "analysis/fine_aggregation_validation.json", {
            "status": "PASS",
            "reason": "The frozen primary-only fine gate selected no windows.",
            "fine_jobs_required": False,
        })
        print(json.dumps({"status": "SKIPPED_NO_QUALIFYING_WINDOWS"}, indent=2))
        return

    raw = OUT / "primary/raw/fine"
    result_paths = sorted(raw.glob("fine_*/examples/*/result.json"))
    results = [read_json(path) for path in result_paths]
    observed = [str(row["base_problem_id"]) for row in results]
    if len(results) != 41 or len(set(observed)) != 41:
        raise RuntimeError(f"Fine run incomplete: observed {len(results)} rows/{len(set(observed))} unique bases")
    shard_summaries = [read_json(path) for path in sorted(raw.glob("fine_*/result.json"))]
    if len(shard_summaries) != 8:
        raise RuntimeError(f"Expected eight fine shard summaries, observed {len(shard_summaries)}")

    by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for problem in results:
        metadata = {
            "base_problem_id": str(problem["base_problem_id"]),
            "example_id": str(problem["example_id"]),
            "evidence_type": problem["evidence_type"],
            "ed_alignment": problem["ed_alignment"],
            "paired_semantic_restoration_included": problem["paired_semantic_restoration_included"],
        }
        for point in problem["coordinates"]:
            for row in point["selective"]:
                key = (metadata["base_problem_id"], point["coordinate"], row["name"])
                by_key[key] = {
                    **metadata,
                    "coordinate": point["coordinate"],
                    "switch_generated_index": point["switch_generated_index"],
                    **compact(row),
                }
            for row in point["semantic_restoration"]:
                key = (metadata["base_problem_id"], point["coordinate"], row["name"])
                if key not in by_key:
                    raise RuntimeError(f"Fine restoration lacks matching selective row: {key}")
                by_key[key].update({
                    field: row[field]
                    for field in (
                        "SRC_O", "SRC_C", "BSRC", "BSRC_normalized", "A_render",
                        "active", "render_to_semantic_ratio", "render_to_all_layer_ratio",
                        "O_restoration_source_consistent", "C_restoration_source_consistent",
                    )
                })
                by_key[key]["restoration_bidirectionally_source_consistent"] = row[
                    "bidirectionally_source_consistent"
                ]

    rows = list(by_key.values())
    expected_rows = 41 * 2 * len(windows)
    if len(rows) != expected_rows:
        raise RuntimeError(f"Expected {expected_rows} fine rows, observed {len(rows)}")
    write_jsonl(OUT / "primary/fine_layer_results.jsonl", rows)

    sufficiency = grouped_statistics(
        rows,
        key_fields=("coordinate", "parent_window", "name"),
        metrics=("BWS", "BWS_normalized"),
    )
    restoration_rows = [row for row in rows if row["paired_semantic_restoration_included"]]
    expected_restoration_rows = 37 * 2 * len(windows)
    if len(restoration_rows) != expected_restoration_rows:
        raise RuntimeError(
            f"Expected {expected_restoration_rows} numeric fine-restoration rows, observed {len(restoration_rows)}"
        )
    restoration = grouped_statistics(
        restoration_rows,
        key_fields=("coordinate", "parent_window", "name"),
        metrics=("BSRC", "BSRC_normalized", "A_render"),
    )
    mechanical = {
        "eight_shards_complete": len(shard_summaries) == 8,
        "all_condition_layout_exact": all(row["all_condition_layout_exact"] for row in shard_summaries),
        "all_capture_layers_valid": all(row["all_capture_layers_valid"] for row in shard_summaries),
        "all_positive_controls_exact": all(row["all_positive_controls_exact"] for row in shard_summaries),
        "all_layer_switch_audits_valid": all(row["all_layer_switch_audits_valid"] for row in shard_summaries),
        "all_self_controls_exact": all(row["all_self_controls_exact"] for row in shard_summaries),
        "all_scores_finite": all(row["all_scores_finite"] for row in shard_summaries),
    }
    write_json(OUT / "analysis/fine_layer_statistics.json", {
        "status": "PASS" if all(mechanical.values()) else "FAIL",
        "fine_windows": windows,
        "sufficiency": sufficiency,
        "semantic_restoration": restoration,
    })
    write_json(OUT / "analysis/fine_aggregation_validation.json", {
        "status": "PASS" if all(mechanical.values()) else "FAIL",
        "base_problem_count": 41,
        "fine_window_count": len(windows),
        "row_count": len(rows),
        "expected_row_count": expected_rows,
        "numeric_restoration_row_count": len(restoration_rows),
        "expected_numeric_restoration_row_count": expected_restoration_rows,
        "mechanical_controls": mechanical,
        "selection_used_attention": False,
        "selection_used_validation_results": False,
    })
    print(json.dumps({
        "status": "PASS" if all(mechanical.values()) else "FAIL",
        "fine_windows": len(windows),
        "rows": len(rows),
    }, indent=2))


if __name__ == "__main__":
    main()
