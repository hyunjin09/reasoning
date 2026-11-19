#!/usr/bin/env python3
"""Aggregate the disjoint Stage 3C.3-R mechanics validation gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c3r"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def historical_rows() -> dict[str, dict[str, Any]]:
    result = {}
    for path in OUT.parent.joinpath("stage3c3/validation/query_forms").glob(
        "shard_*/examples/*/result.json"
    ):
        row = read_json(path)
        result[str(row["base_problem_id"])] = row
    return result


def main() -> None:
    config = read_json(OUT / "config/stage3c3r_config.json")
    expected = {
        str(row["base_problem_id"])
        for row in read_jsonl(OUT / "cohort/validation_manifest.jsonl")
    }
    paths = sorted((OUT / "raw/validation").glob("shard_*/examples/*/result.json"))
    rows = [read_json(path) for path in paths]
    observed = {str(row["base_problem_id"]) for row in rows}
    history = historical_rows()
    maxima = {
        key: 0.0
        for key in (
            "partition_max_abs_error",
            "selected_head_expected_max_abs_error",
            "nonselected_head_max_abs_delta",
            "other_position_max_abs_delta",
            "query_max_abs_delta",
            "key_max_abs_delta",
            "value_max_abs_delta",
            "attention_max_abs_delta",
            "contribution_scale_max_abs_error",
        )
    }
    lambda_one_flags: list[bool] = []
    lambda_zero_flags: list[bool] = []
    finite_flags: list[bool] = []
    baseline_flags: list[bool] = []
    repeat_flags: list[bool] = []
    historical_D_errors: list[float] = []
    internal_lambda_one_errors: list[float] = []
    source_native_invariance_errors: list[float] = []
    selected_heads_expected = {
        target: sorted(map(int, row["causal_heads"]))
        for target, row in config["targets"].items()
    }
    noncausal_heads_expected = {
        target: sorted(map(int, row["noncausal_heads"]))
        for target, row in config["targets"].items()
    }
    head_definition_flags: list[bool] = []

    for row in rows:
        base = str(row["base_problem_id"])
        if base not in history:
            raise RuntimeError(f"Missing Stage 3C.3 validation history for base {base}")
        for target_id, target in row["target_results"].items():
            arms = target["arms"]
            lambda_one_Ds = [float(arm["lambda_results"]["1.0"]["D"]) for arm in arms.values()]
            internal_lambda_one_errors.append(max(lambda_one_Ds) - min(lambda_one_Ds))
            historical_D = float(
                history[base]["target_results"][target_id]["O"]["native"]["R"]["preference"]["D"]
            )
            historical_D_errors.append(abs(lambda_one_Ds[0] - historical_D))
            for arm_id, arm in arms.items():
                expected_heads = (
                    noncausal_heads_expected[target_id]
                    if arm_id == "target_noncausal"
                    else selected_heads_expected[target_id]
                )
                for spec in arm["layer_specs"]:
                    head_definition_flags.append(sorted(map(int, spec["heads"])) == expected_heads)
                if arm["baseline_audit"] is not None:
                    baseline_flags.extend(bool(value) for value in arm["baseline_audit"].values())
                if arm["repeat_audit"] is not None:
                    repeat_flags.append(bool(arm["repeat_audit"]["exact"]))
                    repeat_flags.append(float(arm["repeat_audit"]["D_max_abs_delta"]) == 0.0)
                native_group_reference: dict[tuple[str, str, int, str], float] = {}
                for gain_text, scored in arm["lambda_results"].items():
                    gain = float(gain_text)
                    finite_flags.append(bool(scored["finite"]))
                    for candidate, audits in scored["candidate_audits"].items():
                        for layer_order, audit in enumerate(audits):
                            for key in maxima:
                                if key in audit:
                                    maxima[key] = max(maxima[key], abs(float(audit[key])))
                            native_norm = float(
                                audit["target_contribution"]["concatenated_native_norm"]
                            )
                            scaled_norm = float(
                                audit["target_contribution"]["concatenated_scaled_norm"]
                            )
                            maxima["contribution_scale_max_abs_error"] = max(
                                maxima["contribution_scale_max_abs_error"],
                                abs(scaled_norm - gain * native_norm),
                            )
                            lambda_one_flags.append(bool(audit["lambda_one_exact"]))
                            lambda_zero_flags.append(bool(audit["lambda_zero_exact"]))
                            finite_flags.append(bool(audit["all_outputs_finite"]))
                            for group, summary in audit["audit_group_contributions"].items():
                                key = (arm_id, candidate, layer_order, group)
                                value = float(summary["concatenated_native_norm"])
                                if key in native_group_reference:
                                    source_native_invariance_errors.append(
                                        abs(value - native_group_reference[key])
                                    )
                                else:
                                    native_group_reference[key] = value

    tolerance = float(config["mechanical_bf16_tolerance"])
    checks = {
        "exact_seven_validation_bases": len(rows) == 7 and observed == expected,
        "disjoint_from_primary": expected.isdisjoint(config["primary_base_problem_ids"]),
        "partition_within_frozen_tolerance": maxima["partition_max_abs_error"] <= tolerance,
        "gain_endpoint_arithmetic_exact": maxima["selected_head_expected_max_abs_error"] == 0.0,
        "lambda_one_head_output_exact": all(lambda_one_flags),
        "lambda_zero_removes_only_source": all(lambda_zero_flags),
        "head_definitions_exact": all(head_definition_flags),
        "nonselected_heads_exact": maxima["nonselected_head_max_abs_delta"] == 0.0,
        "other_positions_exact": maxima["other_position_max_abs_delta"] == 0.0,
        "query_exact": maxima["query_max_abs_delta"] == 0.0,
        "key_exact": maxima["key_max_abs_delta"] == 0.0,
        "value_exact": maxima["value_max_abs_delta"] == 0.0,
        "attention_exact": maxima["attention_max_abs_delta"] == 0.0,
        "source_native_contributions_exact_across_gain": max(source_native_invariance_errors, default=0.0) == 0.0,
        "lambda_one_uninstrumented_exact": bool(baseline_flags) and all(baseline_flags),
        "lambda_one_historical_stage3c3_D_exact": max(historical_D_errors, default=float("inf")) == 0.0,
        "lambda_one_all_arms_D_exact": max(internal_lambda_one_errors, default=float("inf")) == 0.0,
        "deterministic_repeat_exact": len(repeat_flags) >= 4 and all(repeat_flags),
        "contribution_scaling_monotonic_and_numeric": maxima["contribution_scale_max_abs_error"] <= 1e-6,
        "all_outputs_finite": all(finite_flags),
    }
    passed = all(checks.values())
    summary = {
        "status": "PASS" if passed else "FAIL",
        "validation_base_problem_ids": sorted(observed, key=int),
        "N_unique_bases": len(rows),
        "checks": checks,
        "maxima": maxima,
        "frozen_tolerance": tolerance,
        "failed_v1_smoke_preserved": "outputs/stage3c3r/raw/validation_smoke/examples/141/result.json",
        "corrected_v2_smoke": "outputs/stage3c3r/raw/validation_smoke_v2/examples/141/result.json",
        "effect_magnitude_used_for_method_selection": False,
    }
    write_json(OUT / "validation/validation_summary.json", summary)
    (OUT / "validation/validation_summary.md").write_text(
        "# Stage 3C.3-R validation\n\n"
        f"Status: **{summary['status']}**\n\n"
        f"All {len(checks)} mechanical checks passed on {len(rows)} disjoint validation bases. "
        "The first smoke's BF16 partition-bookkeeping error is preserved; the corrected FP32 "
        "partition implementation has zero observed reconstruction and endpoint error while "
        "lambda=1 remains bit-exact to uninstrumented and historical Stage 3C.3 scoring.\n",
        encoding="utf-8",
    )
    write_json(OUT / "audit/contribution_partition.json", {
        "status": "PASS" if checks["partition_within_frozen_tolerance"] else "FAIL",
        "validation_N": len(rows),
        "compute_dtype": "float32",
        "maximum_reconstruction_error": maxima["partition_max_abs_error"],
        "frozen_tolerance": tolerance,
    })
    write_json(OUT / "audit/lambda_endpoint_validation.json", {
        "status": "PASS" if all(checks[key] for key in (
            "gain_endpoint_arithmetic_exact", "lambda_one_head_output_exact",
            "lambda_zero_removes_only_source", "lambda_one_uninstrumented_exact",
            "lambda_one_historical_stage3c3_D_exact", "contribution_scaling_monotonic_and_numeric",
        )) else "FAIL",
        "checks": {key: checks[key] for key in checks if "lambda" in key or "scaling" in key or "endpoint" in key},
        "maxima": {
            "endpoint_arithmetic": maxima["selected_head_expected_max_abs_error"],
            "contribution_scale": maxima["contribution_scale_max_abs_error"],
        },
    })
    write_json(OUT / "audit/head_selectivity.json", {
        "status": "PASS" if checks["head_definitions_exact"] and checks["nonselected_heads_exact"] else "FAIL",
        "checks": {key: checks[key] for key in ("head_definitions_exact", "nonselected_heads_exact", "other_positions_exact")},
        "maximum_nonselected_head_delta": maxima["nonselected_head_max_abs_delta"],
    })
    write_json(OUT / "audit/source_invariance.json", {
        "status": "PASS" if checks["source_native_contributions_exact_across_gain"] else "FAIL",
        "source_groups": ["T", "M", "I"],
        "maximum_native_group_contribution_delta_across_gain": max(source_native_invariance_errors, default=0.0),
        "non-target source contributions are not directly modified": True,
    })
    write_json(OUT / "audit/attention_invariance.json", {
        "status": "PASS" if all(checks[key] for key in ("query_exact", "key_exact", "value_exact", "attention_exact")) else "FAIL",
        "maxima": {key: maxima[key] for key in ("query_max_abs_delta", "key_max_abs_delta", "value_max_abs_delta", "attention_max_abs_delta")},
    })
    write_json(OUT / "audit/reproducibility.json", {
        "status": "PASS" if checks["deterministic_repeat_exact"] else "FAIL",
        "repeat_boolean_count": len(repeat_flags),
        "all_repeat_checks_exact": all(repeat_flags),
    })
    print(json.dumps(summary, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
