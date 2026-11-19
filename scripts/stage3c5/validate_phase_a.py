#!/usr/bin/env python3
"""Validate disjoint Stage 3C.5 Phase-A mechanics before primary scoring."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import torch


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c5"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def result_map(root: Path) -> dict[str, dict[str, Any]]:
    return {
        str(row["base_problem_id"]): row
        for path in sorted(root.glob("shard_*/examples/*/result.json"))
        for row in [read_json(path)]
    }


def main() -> None:
    config = read_json(OUT / "config/stage3c5_config.json")
    scopes = read_json(OUT / "config/tpre_layer_scopes.json")["scopes"]
    rows = result_map(OUT / "raw/phase_a_validation")
    expected = set(config["validation_base_problem_ids"])
    if set(rows) != expected:
        raise RuntimeError(f"Validation cohort mismatch: {sorted(rows)}")
    query_rows = []
    scope_rows = []
    all_audits = []
    identities = []
    repeats = []
    state_rows = []
    for base, row in rows.items():
        tensor_path = next((OUT / "raw/phase_a_validation").glob(f"shard_*/examples/{base}/state_readouts.pt"))
        states = torch.load(tensor_path, weights_only=True)
        state_rows.append({
            "base_problem_id": base,
            "tensor_count": len(states),
            "all_float32": all(value.dtype == torch.float32 for value in states.values()),
            "all_finite": all(bool(torch.isfinite(value).all().item()) for value in states.values()),
        })
        for target_id, target in row["target_results"].items():
            current = int(target["t_star_generated_index"])
            tpre = int(target["t_pre_generated_index"])
            query_rows.append({
                "base_problem_id": base, "target_id": target_id,
                "t_star": current, "t_pre": tpre,
                "tpre_equals_tstar_minus_one": tpre == current - 1,
                "positive_tpre": tpre > 0,
            })
            for arm_id, score in target["arms"].items():
                expected_queries = [current] if arm_id == "A1_current" else ([tpre, current] if arm_id == "A3_joint" else [tpre])
                expected_layers = scopes[arm_id] if arm_id in scopes else scopes["P5"]
                scope_rows.append({
                    "base_problem_id": base, "target_id": target_id, "arm_id": arm_id,
                    "queries_exact": score["intervention_generated_indices"] == expected_queries,
                    "layers_exact": score["layer_indices"] == expected_layers,
                    "finite": bool(score["finite"]),
                })
                for candidate_audits in score["candidate_audits"].values():
                    all_audits.extend(candidate_audits)
            if target["identity_audit"] is not None:
                identities.append(target["identity_audit"])
            if target["repeat_audit"] is not None:
                repeats.append(target["repeat_audit"])
    max_partition = max(float(row["partition_max_abs_error"]) for row in all_audits)
    mechanics = {
        "validation_base_count": len(rows),
        "target_count": len(query_rows),
        "audit_call_count": len(all_audits),
        "tpre_exact_all": all(row["tpre_equals_tstar_minus_one"] and row["positive_tpre"] for row in query_rows),
        "scope_and_query_exact_all": all(row["queries_exact"] and row["layers_exact"] for row in scope_rows),
        "finite_scores_all": all(row["finite"] for row in scope_rows),
        "identity_exact_all": bool(identities) and all(all(row.values()) for row in identities),
        "repeat_exact_all": bool(repeats) and all(row["exact"] and row["D_max_abs_delta"] == 0 for row in repeats),
        "qkv_direct_delta_zero_all": all(
            float(row["query_max_abs_delta"]) == 0.0
            and float(row["key_max_abs_delta"]) == 0.0
            and float(row["value_max_abs_delta"]) == 0.0
            for row in all_audits
        ),
        "attention_direct_delta_zero_all": all(float(row["attention_max_abs_delta"]) == 0.0 for row in all_audits),
        "outside_window_delta_zero_all": all(float(row["outside_window_max_abs_delta"]) == 0.0 for row in all_audits),
        "nonselected_head_delta_zero_all": all(float(row["nonselected_head_max_abs_delta"]) == 0.0 for row in all_audits),
        "downstream_recomputation_all": all(bool(row["downstream_recomputation_allowed"]) for row in all_audits),
        "maximum_partition_abs_error": max_partition,
        "partition_tolerance": 1e-6,
        "partition_within_tolerance": max_partition <= 1e-6,
        "states_float32_finite_all": all(row["all_float32"] and row["all_finite"] for row in state_rows),
    }
    checks = [
        ("exact_seven_disjoint_validation_bases", len(rows) == 7),
        ("tpre_equals_tstar_minus_one", mechanics["tpre_exact_all"]),
        ("layer_and_query_schedules_exact", mechanics["scope_and_query_exact_all"]),
        ("scores_finite", mechanics["finite_scores_all"]),
        ("lambda_one_native_transparency", mechanics["identity_exact_all"]),
        ("bitwise_repeatability", mechanics["repeat_exact_all"]),
        ("direct_qkv_unchanged", mechanics["qkv_direct_delta_zero_all"]),
        ("direct_attention_unchanged", mechanics["attention_direct_delta_zero_all"]),
        ("queries_outside_tpre_unchanged", mechanics["outside_window_delta_zero_all"]),
        ("fp32_partition_valid", mechanics["partition_within_tolerance"]),
        ("downstream_recomputation_allowed", mechanics["downstream_recomputation_all"]),
        ("state_readouts_finite", mechanics["states_float32_finite_all"]),
    ]
    summary = {
        "status": "PASS" if all(value for _, value in checks) else "FAIL",
        "checks": [{"id": index + 1, "name": name, "pass": value} for index, (name, value) in enumerate(checks)],
        "mechanics": mechanics,
    }
    write_json(OUT / "audit/tpre_query_index_audit.json", {"rows": query_rows, "all_pass": mechanics["tpre_exact_all"]})
    write_json(OUT / "audit/layer_scope_audit.json", {"rows": scope_rows, "all_pass": mechanics["scope_and_query_exact_all"]})
    write_json(OUT / "audit/reconstruction_validation.json", mechanics)
    write_json(OUT / "audit/phase_a_validation_summary.json", summary)
    print(json.dumps({"status": summary["status"], "checks_passed": sum(value for _, value in checks), "checks_total": len(checks), "max_partition": max_partition}, indent=2))
    if summary["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
