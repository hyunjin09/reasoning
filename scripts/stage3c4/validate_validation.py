#!/usr/bin/env python3
"""Validate the frozen seven-base Stage 3C.4 mechanics cohort."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c4"
TOLERANCE = 1e-6


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main() -> None:
    config = read_json(OUT / "config/stage3c4_config.json")
    paths = sorted((OUT / "raw/validation").glob("shard_*/examples/*/result.json"))
    rows = [read_json(path) for path in paths]
    observed_ids = {str(row["base_problem_id"]) for row in rows}
    expected_ids = set(config["validation_base_problem_ids"])
    all_audits = []
    layer_errors = []
    temporal_errors = []
    source_errors = []
    finite_errors = []
    for row in rows:
        base = str(row["base_problem_id"])
        for target_id, target in row["target_results"].items():
            expected_target_layer = int(config["targets"][target_id]["layer_index"])
            for arm_id, arm in target["arms"].items():
                if arm_id == "single_target_layer_current" and arm["layer_indices"] != [expected_target_layer]:
                    layer_errors.append(f"{base}/{target_id}/{arm_id}: wrong target layer")
                expected_layers = [int(value) for value in arm["layer_indices"]]
                expected_queries = [int(value) for value in arm["score"]["absolute_query_positions"]]
                expected_source = row["source_groups"][arm["source_group"]]
                for candidate, audits in arm["score"]["candidate_audits"].items():
                    if [int(audit["layer_index"]) for audit in audits] != expected_layers:
                        layer_errors.append(f"{base}/{target_id}/{arm_id}/{candidate}: layer enumeration")
                    for audit in audits:
                        all_audits.append(audit)
                        if audit["selected_heads"] != list(range(32)):
                            layer_errors.append(f"{base}/{target_id}/{arm_id}/{candidate}: head enumeration")
                        if audit["query_positions"] != expected_queries:
                            temporal_errors.append(f"{base}/{target_id}/{arm_id}/{candidate}: query positions")
                        if audit["source_positions"] != expected_source:
                            source_errors.append(f"{base}/{target_id}/{arm_id}/{candidate}: source positions")
                        if not audit["all_outputs_finite"]:
                            finite_errors.append(f"{base}/{target_id}/{arm_id}/{candidate}")

    identity = [
        target["identity_audit"]
        for row in rows
        for target in row["target_results"].values()
        if target["identity_audit"] is not None
    ]
    repeats = [
        target["repeat_audit"]
        for row in rows
        for target in row["target_results"].values()
        if target["repeat_audit"] is not None
    ]
    maxima = {
        name: max(float(audit[name]) for audit in all_audits)
        for name in (
            "partition_max_abs_error",
            "selected_head_expected_max_abs_error",
            "nonselected_head_max_abs_delta",
            "outside_window_max_abs_delta",
            "query_max_abs_delta",
            "key_max_abs_delta",
            "value_max_abs_delta",
            "attention_max_abs_delta",
        )
    }
    layer_scope = {
        "status": "PASS" if observed_ids == expected_ids and not layer_errors else "FAIL",
        "validation_bases": sorted(observed_ids),
        "expected_bases": sorted(expected_ids),
        "all_36_layers_enumerated_where_required": not layer_errors,
        "all_32_logical_heads_enumerated": not layer_errors,
        "errors": layer_errors,
    }
    temporal_scope = {
        "status": "PASS" if not temporal_errors and maxima["outside_window_max_abs_delta"] == 0.0 else "FAIL",
        "exact_query_windows": not temporal_errors,
        "queries_before_and_after_window_max_abs_delta": maxima["outside_window_max_abs_delta"],
        "downstream_recomputation_allowed": all(
            bool(audit["downstream_recomputation_allowed"]) for audit in all_audits
        ),
        "errors": temporal_errors,
    }
    source_isolation = {
        "status": "PASS" if not source_errors and all(
            maxima[name] == 0.0
            for name in (
                "selected_head_expected_max_abs_error",
                "nonselected_head_max_abs_delta",
                "outside_window_max_abs_delta",
                "query_max_abs_delta",
                "key_max_abs_delta",
                "value_max_abs_delta",
                "attention_max_abs_delta",
            )
        ) else "FAIL",
        "target_source_indices_exact": not source_errors,
        "maxima": maxima,
        "all_lambda_zero_exact": all(bool(audit["lambda_zero_exact"]) for audit in all_audits),
        "qkv_or_attention_directly_modified": any(
            bool(audit["qkv_directly_modified"] or audit["attention_directly_modified"])
            for audit in all_audits
        ),
        "errors": source_errors,
    }
    reconstruction = {
        "status": "PASS" if maxima["partition_max_abs_error"] <= TOLERANCE and all(
            audit["D_exact"]
            and audit["original_token_log_probabilities_exact"]
            and audit["counterfactual_token_log_probabilities_exact"]
            for audit in identity
        ) else "FAIL",
        "partition_compute_dtype": "float32",
        "max_partition_error": maxima["partition_max_abs_error"],
        "tolerance": TOLERANCE,
        "lambda_one_identity_audit_count": len(identity),
        "all_lambda_one_native_scores_exact": all(
            audit["D_exact"]
            and audit["original_token_log_probabilities_exact"]
            and audit["counterfactual_token_log_probabilities_exact"]
            for audit in identity
        ),
    }
    reproducibility = {
        "status": "PASS" if repeats and all(audit["exact"] for audit in repeats) else "FAIL",
        "repeat_count": len(repeats),
        "all_exact": bool(repeats) and all(audit["exact"] for audit in repeats),
        "maximum_D_delta": max((float(audit["D_max_abs_delta"]) for audit in repeats), default=None),
    }
    write_json(OUT / "audit/layer_scope_audit.json", layer_scope)
    write_json(OUT / "audit/temporal_scope_audit.json", temporal_scope)
    write_json(OUT / "audit/source_isolation.json", source_isolation)
    write_json(OUT / "audit/reconstruction_validation.json", reconstruction)
    write_json(OUT / "audit/reproducibility.json", reproducibility)
    checks = {
        "exact_7_base_cohort": observed_ids == expected_ids,
        "layer_scope": layer_scope["status"] == "PASS",
        "temporal_scope": temporal_scope["status"] == "PASS",
        "source_isolation": source_isolation["status"] == "PASS",
        "reconstruction": reconstruction["status"] == "PASS",
        "repeatability": reproducibility["status"] == "PASS",
        "finite_scores": not finite_errors,
        "no_donor_state": all(not bool(row["donor_state_patched"]) for row in rows),
        "no_sink_intervention": all(not bool(row["sink_directly_intervened"]) for row in rows),
    }
    summary = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "passed": sum(checks.values()),
        "total": len(checks),
        "finite_errors": finite_errors,
        "validation_base_problem_ids": sorted(observed_ids),
        "raw_result_paths": [str(path.relative_to(ROOT)) for path in paths],
    }
    write_json(OUT / "validation/validation_summary.json", summary)
    print(json.dumps(summary, indent=2))
    if summary["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
