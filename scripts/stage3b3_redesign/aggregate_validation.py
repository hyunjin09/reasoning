#!/usr/bin/env python3
"""Aggregate the frozen Stage 3B.3-R method-validation shards and apply its gates."""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json, write_jsonl, write_text
from visual_reasoning.stage3b3_redesign.metrics import evaluate_restoration_gates


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b3_redesign"
RAW = OUT / "validation/raw/shards"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    expected = json.loads((OUT / "config/validation_split.json").read_text(encoding="utf-8"))[
        "validation_base_problem_ids"
    ]
    result_paths = sorted(RAW.glob("validation_*/examples/*/result.json"))
    results = [read_json(path) for path in result_paths]
    observed = [str(row["base_problem_id"]) for row in results]
    if len(results) != 8 or set(observed) != set(expected):
        raise RuntimeError(f"Validation is incomplete: expected {expected}, observed {observed}")
    shard_summaries = [read_json(path) for path in sorted(RAW.glob("validation_*/result.json"))]
    if len(shard_summaries) != 8:
        raise RuntimeError("Every validation shard must have a completed summary")

    restoration_rows = []
    render_rows = []
    selective_rows = []
    selective_gate_rows = []
    full_gate_rows = []
    for result in results:
        base = str(result["base_problem_id"])
        for point in result["coordinates"]:
            coordinate = point["coordinate"]
            bri = float(point["stage3b2_all_layer_BRI"])
            full_metric = point["full_paired_semantic_controls"]
            full_gate_rows.append({
                "base_problem_id": base,
                "coordinate": coordinate,
                "window": "all_layers",
                **full_metric,
            })
            for row in point["selective"]:
                paired = row["paired_semantic_controls"]
                public = {
                    "base_problem_id": base,
                    "coordinate": coordinate,
                    "window": row["name"],
                    "layers": row["layers"],
                    "stage3b2_all_layer_BRI": bri,
                    "BWS": float(row["BWS"]),
                    "BWS_normalized": row["BWS_normalized"],
                    "S_W_O_to_C": float(row["S_W_O_to_C"]),
                    "S_W_C_to_O": float(row["S_W_C_to_O"]),
                    "paired_semantic_controls": paired,
                    "self_O_exact": bool(row["self_O_exact"]),
                    "self_C_exact": bool(row["self_C_exact"]),
                    "all_audits_valid": bool(row["all_audits_valid"]),
                    "all_finite": bool(row["all_finite"]),
                    "raw_result": next(
                        str(path.relative_to(ROOT)) for path in result_paths if path.parent.name == base
                    ),
                }
                selective_rows.append(public)
                selective_gate_rows.append({
                    "base_problem_id": base,
                    "coordinate": coordinate,
                    "window": row["name"],
                    **paired,
                })
            for row in point["semantic_restoration"]:
                public = {
                    "base_problem_id": base,
                    "coordinate": coordinate,
                    "window": row["name"],
                    "layers": row["layers"],
                    **{
                        key: row[key] for key in (
                            "R_O", "R_C", "SRC_O", "SRC_C", "BSRC", "BSRC_normalized",
                            "A_O_original_history", "A_C_original_history",
                            "A_O_counterfactual_history", "A_C_counterfactual_history",
                            "A_render", "all_layer_BRI", "activity_floor", "active",
                            "render_to_semantic_ratio", "render_to_all_layer_ratio",
                            "O_restoration_source_consistent", "C_restoration_source_consistent",
                            "bidirectionally_source_consistent",
                        )
                    },
                    "all_audits_valid": bool(row["all_audits_valid"]),
                    "all_finite": bool(row["all_finite"]),
                    "raw_result": next(
                        str(path.relative_to(ROOT)) for path in result_paths if path.parent.name == base
                    ),
                }
                restoration_rows.append(public)
                render_rows.append({
                    key: public[key] for key in (
                        "base_problem_id", "coordinate", "window", "A_O_original_history",
                        "A_C_original_history", "A_O_counterfactual_history",
                        "A_C_counterfactual_history", "A_render", "BSRC", "all_layer_BRI",
                        "active", "render_to_semantic_ratio", "render_to_all_layer_ratio",
                    )
                })

    restoration_gates = evaluate_restoration_gates(restoration_rows)
    selective_gates = evaluate_restoration_gates(selective_gate_rows)
    full_gates = evaluate_restoration_gates(full_gate_rows)
    mechanics = {
        "eight_shards_complete": len(shard_summaries) == 8,
        "condition_layout_exact": all(row["all_condition_layout_exact"] for row in shard_summaries),
        "capture_layers_valid": all(row["all_capture_layers_valid"] for row in shard_summaries),
        "stage3b2_positive_controls_exact": all(row["all_positive_controls_exact"] for row in shard_summaries),
        "layer_switch_audits_valid": all(row["all_layer_switch_audits_valid"] for row in shard_summaries),
        "residual_patch_audits_valid": all(row["all_residual_patch_audits_valid"] for row in shard_summaries),
        "self_controls_exact": all(row["all_self_controls_exact"] for row in shard_summaries),
        "scores_finite": all(row["all_scores_finite"] for row in shard_summaries),
    }
    mechanics_pass = all(mechanics.values())
    paired_source_controls_pass = bool(
        selective_gates["all_gates_passed"] and full_gates["all_gates_passed"]
    )
    if not mechanics_pass or not paired_source_controls_pass:
        decision = "STOP_REDESIGN"
        primary_authorized = False
        restoration_in_primary = False
        rationale = (
            "Mechanical validity or paired all-layer/selective source controls failed; the reserved "
            "41-base primary cohort remains untouched."
        )
    elif restoration_gates["all_gates_passed"]:
        decision = "PASS"
        primary_authorized = True
        restoration_in_primary = True
        rationale = (
            "Mechanics, paired all-layer/selective controls, and redesigned restoration Gates A-D pass."
        )
    else:
        decision = "RESTORATION_DROP"
        primary_authorized = True
        restoration_in_primary = False
        rationale = (
            "Selective switching and residual mechanics remain valid, but redesigned restoration "
            "does not pass all Gates A-D; primary localization is authorized without restoration "
            "and without necessity claims."
        )
    completed_at = datetime.now(timezone.utc).isoformat()
    decision_payload = {
        "completed_at": completed_at,
        "decision": decision,
        "primary_41_authorized": primary_authorized,
        "restoration_in_primary": restoration_in_primary,
        "mechanical_controls": mechanics,
        "all_mechanical_controls_passed": mechanics_pass,
        "full_all_layer_paired_source_gates": full_gates,
        "selective_window_paired_source_gates": selective_gates,
        "restoration_gates": restoration_gates,
        "rationale": rationale,
        "validation_results_are_method_validation_not_primary_scientific_evidence": True,
        "remaining_41_were_unscored_at_decision_time": True,
    }
    write_jsonl(OUT / "validation/paired_semantic_restoration_results.jsonl", restoration_rows)
    write_jsonl(OUT / "validation/render_artifact_metrics.jsonl", render_rows)
    write_jsonl(OUT / "validation/selective_switch_validation.jsonl", selective_rows)
    write_json(OUT / "validation/validation_decision.json", decision_payload)
    median_bsrc = statistics.median(float(row["BSRC"]) for row in restoration_rows)
    active_count = sum(bool(row["active"]) for row in restoration_rows)
    write_text(
        OUT / "validation/validation_summary.md",
        "# Stage 3B.3-R method validation\n\n"
        f"Decision: **{decision}**\n\n"
        f"The frozen validation split contains 8 independent base problems and {len(restoration_rows)} "
        f"base/window/coordinate restoration rows. {active_count} rows meet the prospective 10% "
        f"activity floor; the pooled descriptive median BSRC is {median_bsrc:.6f}.\n\n"
        f"- Mechanical controls: {'PASS' if mechanics_pass else 'FAIL'}\n"
        f"- Paired all-layer source controls: {'PASS' if full_gates['all_gates_passed'] else 'FAIL'}\n"
        f"- Paired selective-window controls: {'PASS' if selective_gates['all_gates_passed'] else 'FAIL'}\n"
        f"- Revised restoration Gates A-D: {'PASS' if restoration_gates['all_gates_passed'] else 'FAIL'}\n\n"
        f"{rationale}\n\n"
        "The method-validation split is not used as primary localization evidence. Attention was not "
        "used for example or layer selection.\n",
    )
    print(json.dumps({
        "decision": decision,
        "mechanics_pass": mechanics_pass,
        "full_controls_pass": full_gates["all_gates_passed"],
        "selective_controls_pass": selective_gates["all_gates_passed"],
        "restoration_gates_pass": restoration_gates["all_gates_passed"],
        "primary_41_authorized": primary_authorized,
    }, indent=2))


if __name__ == "__main__":
    main()
