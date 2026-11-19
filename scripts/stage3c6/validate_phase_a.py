#!/usr/bin/env python3
"""Validate real-model Stage 3C.6 broad-scan mechanics before primary scoring."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import torch


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c6"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def result_map(root: Path) -> dict[str, dict[str, Any]]:
    return {
        str(row["base_problem_id"]): row
        for path in sorted(root.glob("shard_*/examples/*/result.json")) + sorted(root.glob("examples/*/result.json"))
        for row in [read_json(path)]
    }


def main() -> None:
    config = read_json(OUT / "config/stage3c6_config.json")
    rows = result_map(OUT / "raw/phase_a_validation")
    expected = set(config["validation_base_problem_ids"])
    if set(rows) != expected:
        raise RuntimeError(f"Validation cohort mismatch: {sorted(rows)}")
    checks: dict[str, bool] = {
        "exact_seven_disjoint_validation_bases": len(rows) == 7,
        "all_36_hpre_layers_scanned": True,
        "tpre_exact": True,
        "stage3c5_available_scores_reproduced": True,
        "suppression_direct_mechanics_valid": True,
        "rescue_current_position_only": True,
        "past_or_visual_kv_never_donor_patched": True,
        "self_native_exact_every_layer": True,
        "self_suppressed_exact_every_layer": True,
        "boundary_equivalence_exact": True,
        "candidate_specific_hpre_states_preserved": True,
        "deterministic_repeat_exact": True,
        "all_values_finite": True,
        "hpre_tensor_layout_exact": True,
    }
    maximum_partition_error = 0.0
    maximum_boundary_equivalence_error = 0.0
    tensor_rows = []
    patch_count = 0
    for base, row in rows.items():
        checks["past_or_visual_kv_never_donor_patched"] &= not row["past_token_kv_donor_patched"] and not row["visual_kv_donor_patched"]
        tensor_paths = list((OUT / "raw/phase_a_validation").glob(f"shard_*/examples/{base}/hpre_states.pt"))
        if not tensor_paths:
            tensor_paths = list((OUT / "raw/phase_a_validation").glob(f"examples/{base}/hpre_states.pt"))
        if len(tensor_paths) != 1:
            checks["hpre_tensor_layout_exact"] = False
        else:
            tensors = torch.load(tensor_paths[0], map_location="cpu", weights_only=True)
            checks["hpre_tensor_layout_exact"] &= len(tensors) == 576
            for key, tensor in tensors.items():
                valid = list(tensor.shape) == [1, int(config["residual_width_expected"])] and tensor.dtype == torch.float32 and bool(torch.isfinite(tensor).all())
                checks["hpre_tensor_layout_exact"] &= valid
                tensor_rows.append({"base_problem_id": base, "key": key, "shape": list(tensor.shape), "dtype": str(tensor.dtype), "finite": bool(torch.isfinite(tensor).all())})
        for target in row["target_results"].values():
            checks["tpre_exact"] &= int(target["t_pre_generated_index"]) == int(target["t_star_generated_index"]) - 1
            for condition, source in target["conditions"].items():
                checks["all_36_hpre_layers_scanned"] &= set(source["rescue_by_layer"]) == {str(value) for value in range(36)}
                checks["candidate_specific_hpre_states_preserved"] &= isinstance(source["candidate_hpre_states_exact"], bool)
                if condition == "O":
                    reproduction = source["stage3c5_reproduction"]
                    checks["stage3c5_available_scores_reproduced"] &= bool(reproduction["native_exact"])
                    if reproduction["P4_comparison_available"]:
                        checks["stage3c5_available_scores_reproduced"] &= bool(reproduction["P4_suppressed_exact"])
                for equivalence in source["native_boundary_equivalence"] + source["suppressed_boundary_equivalence"]:
                    checks["boundary_equivalence_exact"] &= bool(equivalence["exact"])
                    maximum_boundary_equivalence_error = max(maximum_boundary_equivalence_error, float(equivalence["max_abs_delta"]))
                for layer, result in source["rescue_by_layer"].items():
                    checks["self_native_exact_every_layer"] &= bool(result["self_native_exact"] and result["self_native_boundary_audit_valid"])
                    checks["self_suppressed_exact_every_layer"] &= bool(result["self_suppressed_exact"] and result["self_suppressed_boundary_audit_valid"])
                    rescue = result["rescue"]
                    checks["rescue_current_position_only"] &= bool(rescue["boundary_patch_audits_valid"] and rescue["current_position_only"])
                    checks["past_or_visual_kv_never_donor_patched"] &= not rescue["past_token_kv_donor_patched"] and not rescue["visual_kv_donor_patched"]
                    checks["all_values_finite"] &= bool(rescue["finite"])
                    for audit in rescue["boundary_patch_audits"].values():
                        checks["rescue_current_position_only"] &= len(audit) == 1 and int(audit[0]["noncurrent_positions_changed"]) == 0
                    for audits in rescue["suppression_audits"].values():
                        patch_count += len(audits)
                        checks["suppression_direct_mechanics_valid"] &= len(audits) == 20
                        for audit in audits:
                            maximum_partition_error = max(maximum_partition_error, float(audit["partition_max_abs_error"]))
                            checks["suppression_direct_mechanics_valid"] &= bool(
                                audit["query_positions"] == [int(rescue["suppression_absolute_position"])]
                                and audit["selected_heads"] == list(range(32))
                                and float(audit["query_max_abs_delta"]) == 0.0
                                and float(audit["key_max_abs_delta"]) == 0.0
                                and float(audit["value_max_abs_delta"]) == 0.0
                                and float(audit["attention_max_abs_delta"]) == 0.0
                                and float(audit["outside_window_max_abs_delta"]) == 0.0
                                and bool(audit["downstream_recomputation_allowed"])
                            )
                if source["repeat_audit"] is not None:
                    checks["deterministic_repeat_exact"] &= bool(source["repeat_audit"]["exact"])
    write_json(OUT / "audit/residual_tensor_layout.json", {
        "status": "PASS" if checks["hpre_tensor_layout_exact"] else "FAIL",
        "expected_per_base_tensor_count": 576,
        "expected_shape": [1, int(config["residual_width_expected"])], "expected_dtype": "torch.float32",
        "rows": tensor_rows,
    })
    write_json(OUT / "audit/boundary_equivalence.json", {
        "status": "PASS" if checks["boundary_equivalence_exact"] else "FAIL",
        "definition": "h_post_block(l) == h_pre(l+1)",
        "maximum_absolute_delta": maximum_boundary_equivalence_error,
    })
    write_json(OUT / "audit/current_position_selectivity.json", {
        "status": "PASS" if checks["rescue_current_position_only"] else "FAIL",
        "current_position_only": True, "noncurrent_positions_changed": 0,
    })
    write_json(OUT / "audit/past_cache_invariance.json", {
        "status": "PASS" if checks["past_or_visual_kv_never_donor_patched"] else "FAIL",
        "execution": "full-sequence use_cache=False; suppressed recipient states are recomputed natively",
        "donor_past_token_kv_patch_count": 0, "donor_visual_kv_patch_count": 0,
        "current_boundary_noncurrent_positions_changed": 0,
        "note": "A separate exact post-RoPE past-K/V replay audit is required before final acceptance.",
    })
    write_json(OUT / "audit/self_patch_validation.json", {
        "status": "PASS" if checks["self_native_exact_every_layer"] and checks["self_suppressed_exact_every_layer"] else "FAIL",
        "native_exact_every_layer": checks["self_native_exact_every_layer"],
        "suppressed_exact_every_layer": checks["self_suppressed_exact_every_layer"],
    })
    write_json(OUT / "audit/reproducibility.json", {
        "status": "PASS" if checks["deterministic_repeat_exact"] else "FAIL",
        "fixed_seed": int(config["seed"]), "repeat_exact": checks["deterministic_repeat_exact"],
    })
    result = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks, "checks_passed": sum(checks.values()), "checks_total": len(checks),
        "validation_base_count": len(rows), "suppression_patch_audit_count": patch_count,
        "maximum_partition_error": maximum_partition_error,
        "maximum_boundary_equivalence_error": maximum_boundary_equivalence_error,
    }
    write_json(OUT / "audit/phase_a_validation_summary.json", result)
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
