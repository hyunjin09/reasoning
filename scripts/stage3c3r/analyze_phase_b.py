#!/usr/bin/env python3
"""Aggregate the prospectively gated Stage 3C.3-R nested redundancy scopes."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage3c3r.analysis import bootstrap_summary, holm_adjust


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c3r"
TARGETS = ("target_a", "target_b")
SCOPES = ("R1", "R2", "R3")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, allow_nan=False) + "\n" for row in rows), encoding="utf-8")


def mechanics(rows: list[dict[str, Any]], phase_a: dict[tuple[str, str], float]) -> dict[str, Any]:
    maxima = {key: 0.0 for key in (
        "partition_max_abs_error", "selected_head_expected_max_abs_error",
        "query_max_abs_delta", "key_max_abs_delta", "value_max_abs_delta",
        "attention_max_abs_delta", "nonselected_head_max_abs_delta", "other_position_max_abs_delta",
        "lambda_one_D_vs_phase_a",
    )}
    flags: list[bool] = []
    baselines: list[bool] = []
    layers: set[int] = set()
    for row in rows:
        base = str(row["base_problem_id"])
        for target_id, target in row["target_results"].items():
            one_values = []
            for scope, arm in target["arms"].items():
                if scope not in SCOPES:
                    flags.append(False)
                layers.update(int(spec["layer_index"]) for spec in arm["layer_specs"])
                one_values.append(float(arm["lambda_results"]["1.0"]["D"]))
                if arm["baseline_audit"]:
                    baselines.extend(bool(value) for value in arm["baseline_audit"].values())
                for scored in arm["lambda_results"].values():
                    flags.append(bool(scored["finite"]))
                    for candidate_audits in scored["candidate_audits"].values():
                        for audit in candidate_audits:
                            flags.extend([
                                bool(audit["lambda_one_exact"]),
                                bool(audit["lambda_zero_exact"]),
                                bool(audit["all_outputs_finite"]),
                            ])
                            for key in maxima:
                                if key in audit:
                                    maxima[key] = max(maxima[key], abs(float(audit[key])))
            maxima["lambda_one_D_vs_phase_a"] = max(
                maxima["lambda_one_D_vs_phase_a"],
                *(abs(value - phase_a[(base, target_id)]) for value in one_values),
            )
    checks = {
        "all_finite_and_endpoint_flags": all(flags),
        "partition_within_tolerance": maxima["partition_max_abs_error"] <= 1e-6,
        "endpoint_arithmetic_exact": maxima["selected_head_expected_max_abs_error"] == 0.0,
        "qkv_attention_not_directly_modified": all(maxima[key] == 0.0 for key in (
            "query_max_abs_delta", "key_max_abs_delta", "value_max_abs_delta", "attention_max_abs_delta"
        )),
        "untargeted_heads_and_positions_exact_locally": (
            maxima["nonselected_head_max_abs_delta"] == 0.0
            and maxima["other_position_max_abs_delta"] == 0.0
        ),
        "lambda_one_phase_a_exact": maxima["lambda_one_D_vs_phase_a"] == 0.0,
        "sampled_uninstrumented_baselines_exact": bool(baselines) and all(baselines),
        "only_w4_layers_28_29": layers == {28, 29},
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "maxima": maxima,
        "layers_observed": sorted(layers),
        "multi_layer_attention_boundary": "At layer 29, upstream layer-28 interventions may naturally change the input and native local attention; the patch itself does not alter local Q/K/V/attention.",
    }


def main() -> None:
    gate = read_json(OUT / "phase_b_redundancy/redundancy_gate.json")
    if not gate["phase_b_authorized"]:
        raise RuntimeError("Phase B was not authorized")
    expected = {
        str(row["base_problem_id"])
        for row in read_jsonl(OUT / "cohort/primary_manifest.jsonl")
    }
    phase_a_rows = read_jsonl(OUT / "phase_a_gain/target_gain_results.jsonl")
    phase_a_native = {
        (str(row["base_problem_id"]), str(row["target_id"])): float(row["E"])
        for row in phase_a_rows if float(row["lambda"]) == 1.0
    }
    phase_a_zero = {
        (str(row["base_problem_id"]), str(row["target_id"])): float(row["E"])
        for row in phase_a_rows if float(row["lambda"]) == 0.0
    }
    paths = sorted((OUT / "raw/phase_b").glob("shard_*/examples/*/result.json"))
    rows = [read_json(path) for path in paths]
    observed = {str(row["base_problem_id"]) for row in rows}
    if len(rows) != 24 or observed != expected:
        raise RuntimeError(f"Incomplete Phase B: expected={sorted(expected)} observed={sorted(observed)}")
    audit = mechanics(rows, phase_a_native)
    write_json(OUT / "audit/phase_b_mechanics.json", audit)
    if audit["status"] != "PASS":
        raise RuntimeError("Phase B mechanics audit failed")

    by_scope: dict[str, list[dict[str, Any]]] = {scope: [] for scope in SCOPES}
    values: dict[tuple[str, str, str, float], float] = {}
    for row in sorted(rows, key=lambda item: int(item["base_problem_id"])):
        base = str(row["base_problem_id"])
        for target_id in TARGETS:
            native = phase_a_native[(base, target_id)]
            for scope in SCOPES:
                arm = row["target_results"][target_id]["arms"][scope]
                for gain_text, scored in arm["lambda_results"].items():
                    gain = float(gain_text)
                    evidence = float(scored["D"])
                    values[(base, target_id, scope, gain)] = evidence
                    by_scope[scope].append({
                        "base_problem_id": base,
                        "example_id": str(row["example_id"]),
                        "target_id": target_id,
                        "scope": scope,
                        "lambda": gain,
                        "E": evidence,
                        "native_D": native,
                        "ER_unclipped": evidence / native,
                        "evidence_loss_native_minus_lambda": native - evidence,
                        "layer_specs": arm["layer_specs"],
                    })
    for scope in SCOPES:
        write_jsonl(OUT / f"phase_b_redundancy/scope_{scope.lower()}_results.jsonl", by_scope[scope])

    analysis: dict[str, Any] = {
        "primary_unit": "base_problem_id",
        "N_unique_bases": len(expected),
        "phase_b_gate_passed": True,
        "scopes_frozen_before_phase_a": True,
        "targets": {},
    }
    phenotype: dict[str, Any] = {"targets": {}}
    phase_b_p: dict[tuple[str, str], float] = {}
    for target_id in TARGETS:
        target_result: dict[str, Any] = {"scopes": {}, "contrasts_vs_R0_lambda0": {}}
        r0_loss = {
            base: phase_a_native[(base, target_id)] - phase_a_zero[(base, target_id)]
            for base in expected
        }
        median_retained = {"R0": float(np.median([
            phase_a_zero[(base, target_id)] / phase_a_native[(base, target_id)] for base in expected
        ]))}
        for scope in SCOPES:
            losses = [
                phase_a_native[(base, target_id)] - values[(base, target_id, scope, 0.0)]
                for base in expected
            ]
            retained = [
                values[(base, target_id, scope, 0.0)] / phase_a_native[(base, target_id)]
                for base in expected
            ]
            contrast = [loss - r0_loss[base] for loss, base in zip(losses, expected)]
            target_result["scopes"][scope] = {
                "lambda0_loss": bootstrap_summary(losses),
                "lambda0_retained": bootstrap_summary(retained),
                "median_retained": float(np.median(retained)),
                "lambda0_positive_loss_fraction": float(np.mean(np.asarray(losses) > 0)),
                "lambda0_5_loss": bootstrap_summary([
                    phase_a_native[(base, target_id)] - values[(base, target_id, scope, 0.5)]
                    for base in expected
                ]),
            }
            target_result["contrasts_vs_R0_lambda0"][scope] = bootstrap_summary(contrast)
            phase_b_p[(target_id, scope)] = float(
                target_result["contrasts_vs_R0_lambda0"][scope]["wilcoxon_one_sided_greater_p"]
            )
            median_retained[scope] = float(np.median(retained))
        r0_weak = median_retained["R0"] >= 0.80
        r1_strong = median_retained["R1"] < 0.80
        r1_weak = median_retained["R1"] >= 0.80
        r2_or_r3_strong = median_retained["R2"] < 0.80 or median_retained["R3"] < 0.80
        broad_robust = median_retained["R3"] >= 0.80
        phenotype["targets"][target_id] = {
            "median_retained": median_retained,
            "R_Head_Parallel": bool(r0_weak and r1_strong),
            "R_Cross_Layer": bool(r0_weak and r1_weak and r2_or_r3_strong),
            "R_Broad_Robustness": bool(broad_robust),
            "threshold_is_descriptive": True,
        }
        analysis["targets"][target_id] = target_result
    write_json(OUT / "analysis/redundancy_scope_analysis.json", {**analysis, "phenotype": phenotype})

    # Frozen 26-test family: 10 Phase-A + 3 gated Phase-B tests per target.
    dose = read_json(OUT / "analysis/dose_response_statistics.json")
    specificity = read_json(OUT / "analysis/target_specificity_analysis.json")
    query = read_json(OUT / "analysis/query_patch_curve_comparison.json")
    hypothesis_rows = []
    for target_id in TARGETS:
        for gain in (0.75, 0.5, 0.25, 0.1, 0.0):
            stat = dose["targets"][target_id]["lambda_contrasts"][str(gain)]
            hypothesis_rows.append({"target_id": target_id, "test": f"T_{gain}_vs_1", "raw_p": stat["wilcoxon_one_sided_greater_p"]})
        hypothesis_rows.append({
            "target_id": target_id, "test": "monotonic_trend",
            "raw_p": dose["targets"][target_id]["monotonic_trend"]["wilcoxon_one_sided_greater_p"],
        })
        for key, label in (
            ("T_minus_M_loss", "T_vs_M_specificity"),
            ("T_minus_I_loss", "T_vs_I_specificity"),
            ("causal_minus_noncausal_T_loss", "causal_vs_noncausal_specificity"),
        ):
            hypothesis_rows.append({
                "target_id": target_id, "test": label,
                "raw_p": specificity["targets"][target_id][key]["wilcoxon_one_sided_greater_p"],
            })
        # Operating-point consistency is a descriptive frozen test; use p=1 when
        # a scalar per-base transition margin is unavailable for nonmonotonic curves.
        hypothesis_rows.append({
            "target_id": target_id,
            "test": "query_patch_operating_point_consistency",
            "raw_p": 1.0,
            "descriptive_result": query["targets"][target_id],
        })
        for scope in SCOPES:
            hypothesis_rows.append({
                "target_id": target_id,
                "test": f"{scope}_lambda0_vs_R0_lambda0",
                "raw_p": phase_b_p[(target_id, scope)],
            })
    adjusted = holm_adjust([float(row["raw_p"]) for row in hypothesis_rows])
    for row, value in zip(hypothesis_rows, adjusted):
        row["holm_adjusted_p"] = value
        row["holm_significant_0_05"] = value < 0.05
    write_json(OUT / "analysis/primary_family_statistics.json", {
        "family_size": len(hypothesis_rows),
        "multiplicity": "Holm across all 26 target-specific frozen tests",
        "rows": hypothesis_rows,
    })
    print(json.dumps({"mechanics": audit["status"], "analysis": analysis, "phenotype": phenotype}, indent=2))


if __name__ == "__main__":
    main()
