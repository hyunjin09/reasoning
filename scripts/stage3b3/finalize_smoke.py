#!/usr/bin/env python3
"""Evaluate the prospectively frozen Stage 3B.3 three-base smoke gate."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json


ROOT = Path(__file__).resolve().parents[2]
ALL_LAYERS = set(range(36))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def ratio(sham: list[float], target: list[float]) -> float:
    denominator = statistics.median(abs(value) for value in target)
    return statistics.median(abs(value) for value in sham) / denominator if denominator else float("inf")


def evaluate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    coordinates = [point for row in rows for point in row["coordinates"]]
    sufficiency = [entry for point in coordinates for entry in point["coarse_sufficiency"]]
    necessity = [entry for point in coordinates for entry in point["coarse_necessity"]]
    cumulative = [entry for point in coordinates for entry in point["cumulative"]]
    residual = [entry for row in rows for entry in row["activation_patches"]]
    full_sham = [
        point["D_OO"] - point["full_all_layer"]["O_to_sham"]["D"] for point in coordinates
    ]
    full_target = [
        point["D_OO"] - point["full_all_layer"]["O_to_C"]["D"] for point in coordinates
    ]
    selective_ratio = ratio(
        [entry["sham_window_shift"] for entry in sufficiency],
        [entry["S_W_O_to_C"] for entry in sufficiency],
    )
    restoration_ratio = ratio(
        [entry["sham_restoration_shift"] for entry in necessity],
        [entry["N_W_O"] for entry in necessity],
    )
    all_layer_ratio = ratio(full_sham, full_target)

    restoration_complements_exact = all(
        set(entry["donor_layers"]) == ALL_LAYERS.difference(entry["layers"])
        for entry in necessity
    )
    indexing_exact = all(
        point["switch_generated_index"]
        == next(row["ed_generated_index"] for row in rows if point in row["coordinates"])
        - (1 if point["coordinate"] == "Ed_minus_1" else 0)
        for point in coordinates
    )
    target_direction_signs = all(
        point["stage3b2_all_layer_BRI"] > 0.0
        and point["D_OO"] - point["full_all_layer"]["O_to_C"]["D"] > 0.0
        and point["full_all_layer"]["C_to_O"]["D"] - point["D_CC"] > 0.0
        for point in coordinates
    )
    criteria = [
        ("three_numeric_label_bases", len(rows) == 3 and all(row["evidence_type"] == "tier1_local_numeric_label" for row in rows)),
        ("all_layer_switch_exactly_reproduces_stage3b2", bool(coordinates) and all(all(point["positive_control"][key] for key in ("O_to_C_exact_stage3b2", "C_to_O_exact_stage3b2", "O_to_sham_exact_stage3b2", "self_O_exact_stage3b2")) for point in coordinates)),
        ("no_switch_exactly_reproduces_stage3b2", bool(coordinates) and all(point["positive_control"]["no_switch_O_exact_stage3b2"] and point["positive_control"]["no_switch_C_exact_stage3b2"] for point in coordinates)),
        ("all_self_window_switches_transparent", bool(coordinates) and all(point["all_self_exact"] for point in coordinates)),
        ("sham_effects_small_at_frozen_ratio", all_layer_ratio <= 0.25 and selective_ratio <= 0.25 and restoration_ratio <= 0.25),
        ("only_selected_visual_kv_layers_replaced", bool(coordinates) and all(point["all_audits_valid"] for point in coordinates)),
        ("nonvisual_qpr_kv_unchanged", bool(coordinates) and all(point["all_audits_valid"] for point in coordinates)),
        ("visual_positions_and_condition_layout_exact", bool(rows) and all(row["condition_layout_exact"] and row["capture_all_layers_valid"] for row in rows)),
        ("ed_minus_1_and_ed_indexing_exact", indexing_exact),
        ("restoration_uses_exact_window_complement", restoration_complements_exact),
        ("current_position_residual_patch_is_surgical", bool(residual) and all(entry["all_audits_valid"] and entry["self_O_exact"] for entry in residual)),
        ("reciprocal_signs_finite_and_cross_run_deterministic", target_direction_signs and all(point["all_finite"] for point in coordinates) and all(entry["all_finite"] for entry in residual) and all(all(point["positive_control"].values()) for point in coordinates)),
    ]
    return {
        "status": "PASS" if all(value for _, value in criteria) else "FAIL",
        "base_problem_ids": [str(row["base_problem_id"]) for row in rows],
        "criterion_count": len(criteria),
        "criteria": [{"name": name, "status": "PASS" if value else "FAIL"} for name, value in criteria],
        "sham_to_target_ratios": {
            "all_layer": all_layer_ratio,
            "selective_coarse": selective_ratio,
            "restoration_coarse": restoration_ratio,
            "threshold": 0.25,
        },
        "counts": {
            "coordinate_rows": len(coordinates),
            "coarse_sufficiency_rows": len(sufficiency),
            "coarse_necessity_rows": len(necessity),
            "cumulative_rows": len(cumulative),
            "activation_patch_rows": len(residual),
        },
        "interpretation_boundary": "mechanical validation only; smoke target effects are not cohort evidence",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, required=True)
    args = parser.parse_args()
    raw_dir = args.raw_dir.resolve()
    raw_dir.relative_to((ROOT / "outputs/stage3b3/raw").resolve())
    rows = read_jsonl(raw_dir / "results.jsonl")
    result = evaluate(rows)
    smoke_dir = ROOT / "outputs/stage3b3/smoke"
    write_json(smoke_dir / "layer_switch_validation.json", result)
    activation = {
        "status": "PASS" if all(entry["all_audits_valid"] and entry["self_O_exact"] for row in rows for entry in row["activation_patches"]) else "FAIL",
        "definition": "replace only the current query-position residual after the named decoder layer",
        "boundaries_after_layers": [5, 11, 17, 23, 29, 35],
        "base_problem_ids": result["base_problem_ids"],
    }
    write_json(smoke_dir / "activation_patch_validation.json", activation)
    lines = [
        "# Stage 3B.3 layer-intervention smoke validation",
        "",
        f"Overall: **{result['status']}**",
        "",
        f"Bases: {', '.join(result['base_problem_ids'])}",
        "",
        "| Criterion | Status |",
        "|---|---|",
        *[f"| {entry['name']} | {entry['status']} |" for entry in result["criteria"]],
        "",
        "Sham/target ratios (frozen maximum 0.25):",
        "",
        f"- all-layer: {result['sham_to_target_ratios']['all_layer']:.6f}",
        f"- selective coarse: {result['sham_to_target_ratios']['selective_coarse']:.6f}",
        f"- restoration coarse: {result['sham_to_target_ratios']['restoration_coarse']:.6f}",
        "",
        "This gate validates intervention mechanics only. It is not a cohort-level scientific result.",
    ]
    (smoke_dir / "layer_switch_validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
