#!/usr/bin/env python3
"""Validate the real-model Stage 3B.8 representation/reconstruction smoke."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b8"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-dir", type=Path, required=True)
    args = parser.parse_args()
    result = read_json(args.smoke_dir / "result.json")
    rows = [json.loads(line) for line in (args.smoke_dir / "results.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != 1:
        raise RuntimeError("Representation smoke must contain exactly one base")
    row = rows[0]
    config = read_json(OUT / "config/stage3b8_config.json")
    environment = read_json(args.smoke_dir / "environment.json")
    target_checks = []
    for target, observed in zip(config["targets"], row["targets"], strict=True):
        arms = {arm["arm_id"]: arm for arm in observed["arms"]}
        captures = [audit for capture in observed["no_intervention"].values() for audit in capture["capture_audits"].values()]
        target_checks.append({
            "target_id": target["target_id"],
            "heads_exact": observed["heads"] == target["heads"],
            "layer_exact": int(observed["layer_index"]) == int(target["layer_index"]),
            "all_representation_dimensions_512": all(int(audit["flattened_representation_dimension"]) == 512 for audit in captures),
            "all_locations_pre_WO": all(audit["location"] == "selected logical query-head outputs before shared W_O" for audit in captures),
            "lambda0_native_exact": arms["lambda_0"]["native_endpoint_exact"] is True,
            "lambda1_stage3b7r_V_reproduced": arms["lambda_1"]["stage3b7r_v_reference_within_tolerance"] is True,
            "lambda1_stage3b7r_max_abs_D_error": arms["lambda_1"]["stage3b7r_v_reference_max_abs_D_error"],
            "all_self_conditions_exact": all(arm["all_self_restorations_exact"] for arm in arms.values()),
            "all_recipient_routing_and_native_roi_values_exact": all(arm["all_recipient_tensor_alignment_exact"] for arm in arms.values()),
            "all_nonselected_heads_unchanged": all(arm["all_query_head_selectivity_valid"] for arm in arms.values()),
            "candidate_representation_invariance_exact": observed["representation_vector_audit"]["candidate_invariance_exact"],
        })
    checks = {
        "one_base_smoke": result["base_problem_count"] == 1,
        "gpu_is_A5000": "A5000" in str(environment["gpu_name"]),
        "architecture_exact": environment["stage3b8_gqa_architecture"] == config["architecture_expected"],
        "four_condition_layout_and_roi_exact": row["mechanical_controls"]["all_layout_and_roi_mappings_exact"],
        "all_scoring_mechanics_passed": result["all_mechanical_controls_passed"],
        "determinism_public_result_exact": result["determinism_repeat"]["exact_public_result_match"],
        "determinism_vectors_exact": result["determinism_repeat"]["exact_vector_match"],
        "all_target_checks_passed": all(all(value for key, value in target.items() if key not in {"target_id", "lambda1_stage3b7r_max_abs_D_error"}) for target in target_checks),
    }
    payload = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "smoke_base_problem_id": row["base_problem_id"],
        "representation": config["representation"],
        "checks": checks,
        "targets": target_checks,
        "maximum_stage3b7r_V_endpoint_D_error": max(float(target["lambda1_stage3b7r_max_abs_D_error"]) for target in target_checks),
        "endpoint_tolerance": float(config["dose_response"]["endpoint_tolerance"]),
    }
    write_json(OUT / "audit/reconstruction_validation.json", payload)
    print(json.dumps(payload, indent=2))
    if payload["status"] != "PASS":
        raise SystemExit("Representation/reconstruction smoke failed; stop before Phase A cohort scoring")


if __name__ == "__main__":
    main()
