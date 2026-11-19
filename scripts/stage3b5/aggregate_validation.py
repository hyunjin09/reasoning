#!/usr/bin/env python3
"""Apply the prospectively frozen Stage 3B.5 independent validation gate."""

from __future__ import annotations

import json
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json, write_text
from visual_reasoning.stage3b3_redesign.metrics import evaluate_restoration_gates


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b5"
RAW = OUT / "validation/raw"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def gate_row(row: dict[str, Any], *, base: str) -> dict[str, Any]:
    return {
        "base_problem_id": base,
        "BSRC": float(row["BMR"]),
        "SRC_O": float(row["BMR_O"]),
        "SRC_C": float(row["BMR_C"]),
        "A_render": float(row["A_render"]),
        "all_layer_BRI": float(row["all_layer_BRI"]),
        "active": bool(row["active"]),
        "render_to_semantic_ratio": row["render_to_semantic_ratio"],
        "render_to_all_layer_ratio": row["render_to_all_layer_ratio"],
    }


def main() -> None:
    expected = {
        str(json.loads(line)["base_problem_id"])
        for line in (OUT / "validation/validation_manifest.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    paths = sorted(RAW.glob("validation_*/examples/*/result.json"))
    results = [read_json(path) for path in paths]
    observed = [str(row["base_problem_id"]) for row in results]
    summaries = [read_json(path) for path in sorted(RAW.glob("validation_*/result.json"))]
    if len(results) != 8 or set(observed) != expected or len(set(observed)) != 8:
        raise RuntimeError(f"Validation incomplete: {len(results)} results, {len(set(observed))} unique")
    if len(summaries) != 8:
        raise RuntimeError(f"Expected eight validation summaries, observed {len(summaries)}")

    rows = []
    for result in results:
        for point in result["coordinates"]:
            for row in point["boundary_restoration"]:
                rows.append({
                    "base_problem_id": str(result["base_problem_id"]),
                    "coordinate": point["coordinate"],
                    **{key: value for key, value in row.items() if key != "controls"},
                })
    if len(rows) != 8 * 40:
        raise RuntimeError(f"Expected 320 validation rows, observed {len(rows)}")

    final_post_block = [
        row for row in rows
        if row["layer_role"] == "second" and row["boundary"] == "h_post_block"
    ]
    final_post_block_gates = evaluate_restoration_gates([
        gate_row(row, base=str(row["base_problem_id"])) for row in final_post_block
    ])
    base_render_ratios = []
    for base in sorted(expected, key=int):
        values = [
            float(row["render_to_all_layer_ratio"])
            for row in rows
            if row["base_problem_id"] == base and row["render_to_all_layer_ratio"] is not None
        ]
        base_render_ratios.append(statistics.median(values))
    all_boundary_render_median = statistics.median(base_render_ratios)
    all_boundary_render_pass = all_boundary_render_median <= 0.05

    repeat_paths = sorted(RAW.glob("validation_*/determinism_repeat.json"))
    determinism = bool(
        len(repeat_paths) == 1 and read_json(repeat_paths[0])["exact_public_result_match"]
    )
    mechanics = {
        "eight_shards_complete": len(summaries) == 8,
        "condition_layout_exact": all(row["all_condition_layout_exact"] for row in summaries),
        "capture_hooks_exact": all(row["all_capture_audits_valid"] for row in summaries),
        "post_attention_residual_additions_exact": all(
            all(
                audit["post_attn_sum_exact"]
                for candidate_rows in point["no_switch"].values()
                for audits in candidate_rows["residual_addition_audits"].values()
                for audit in audits
            )
            for result in results for point in result["coordinates"]
        ),
        "baseline_exact_stage3b4": all(row["all_baselines_exact_stage3b4"] for row in summaries),
        "patch_hooks_current_position_only": all(row["all_patch_audits_valid"] for row in summaries),
        "downstream_recompute_verified": all(row["all_downstream_recompute_verified"] for row in summaries),
        "self_restoration_exact": all(row["all_self_restorations_exact"] for row in summaries),
        "adjacent_interface_scores_exact": all(row["all_adjacent_interface_scores_exact"] for row in summaries),
        "adjacent_interface_captured_states_exact": all(row["all_adjacent_interface_captured_states_exact"] for row in summaries),
        "finite_outputs": all(row["all_scores_finite"] for row in summaries),
        "deterministic_replication": determinism,
    }
    mechanics_pass = all(mechanics.values())
    passed = bool(
        mechanics_pass
        and all_boundary_render_pass
        and final_post_block_gates["all_gates_passed"]
    )
    result = {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "decision": "PASS" if passed else "STOP_REDESIGN",
        "primary_authorized": passed,
        "independent_base_count": len(expected),
        "boundary_row_count": len(rows),
        "mechanical_controls": mechanics,
        "all_mechanical_controls_passed": mechanics_pass,
        "all_boundary_sham_render_gate": {
            "passed": all_boundary_render_pass,
            "median_base_render_to_all_layer_ratio": all_boundary_render_median,
            "maximum": 0.05,
        },
        "final_layer_post_block_restoration_gates": final_post_block_gates,
        "stage3b4_block_tendency_definition": "the final single-layer post-block reference must pass the same base-aggregated positive/source-consistent Gates A-D; exact equality to Stage 3B.4 is not expected because Stage 3B.4 patched both layer outputs",
        "validation_results_are_method_validation_not_primary_scientific_evidence": True,
    }
    write_json(OUT / "validation/validation_results.json", result)

    first = results[0]
    audit_rows = []
    patch_rows = []
    for point in first["coordinates"]:
        for condition, capture in point["no_switch"].items():
            for candidate, audits in capture["capture_audit_summaries"].items():
                audit_rows.extend({
                    "base_problem_id": str(first["base_problem_id"]),
                    "coordinate": point["coordinate"],
                    "condition": condition,
                    "candidate": candidate,
                    **audit,
                } for audit in audits)
        for row in point["boundary_restoration"]:
            candidate = row["controls"]["O"]["C"]["original_candidate"]
            patch_rows.append({
                "coordinate": point["coordinate"],
                "window": row["window"],
                "layer_role": row["layer_role"],
                "boundary": row["boundary"],
                **candidate["boundary_patch_audit_summary"],
            })
    write_json(OUT / "audit/tensor_shape_diagnostics.json", {
        "source": "first frozen validation base",
        "capture_rows": audit_rows,
        "patch_rows": patch_rows,
        "captured_boundaries": sorted({row["boundary"] for row in audit_rows}),
        "captured_layers": sorted({int(row["layer_index"]) for row in audit_rows}),
        "captured_state_shapes": sorted({tuple(row["state_shape"]) for row in audit_rows}),
        "hidden_last_dimensions": sorted({int(row["hidden_shape"][-1]) for row in audit_rows}),
        "all_patch_rows_current_position_only": all(
            row["positions_replaced"] == [row["position"]]
            and row["noncurrent_positions_changed"] == 0
            for row in patch_rows
        ),
    })
    write_text(
        OUT / "validation/validation_report.md",
        "# Stage 3B.5 independent method validation\n\n"
        f"Decision: **{result['decision']}**\n\n"
        f"Eight disjoint paired numeric bases produced {len(rows)} fixed boundary rows. "
        f"Mechanical controls {'passed' if mechanics_pass else 'failed'}; the final-layer "
        f"post-block bridge Gates A–D {'passed' if final_post_block_gates['all_gates_passed'] else 'failed'}; "
        f"the pooled boundary sham/all-layer ratio was {all_boundary_render_median:.6f} "
        "against the frozen 0.05 maximum.\n\n"
        "The validation split is technical method evidence only. Early/normalized boundary arms "
        "were not required to be scientifically positive. Attention magnitude was not used.\n",
    )
    print(json.dumps({
        "decision": result["decision"],
        "mechanics_pass": mechanics_pass,
        "final_post_block_gates_pass": final_post_block_gates["all_gates_passed"],
        "all_boundary_render_pass": all_boundary_render_pass,
    }, indent=2))


if __name__ == "__main__":
    main()
