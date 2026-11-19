#!/usr/bin/env python3
"""Aggregate Stage 3C.3-R Phase A and evaluate the frozen redundancy gate."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import spearmanr

from visual_reasoning.stage3c3r.analysis import bootstrap_summary, query_operating_point
from visual_reasoning.stage3c3r.protocol import redundancy_gate, tested_thresholds


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c3r"
TARGETS = ("target_a", "target_b")
GAINS = (1.0, 0.75, 0.5, 0.25, 0.1, 0.0)


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


def stage3c3_primary() -> dict[str, dict[str, Any]]:
    result = {}
    for path in OUT.parent.joinpath("stage3c3/phase_a_query/raw").glob(
        "shard_*/examples/*/result.json"
    ):
        row = read_json(path)
        result[str(row["base_problem_id"])] = row
    return result


def contribution_vector(routing: dict[str, Any]) -> list[float]:
    values: list[float] = []
    for head in sorted(routing["per_head"], key=lambda row: int(row["logical_query_head"])):
        values.extend(float(value) for value in head["groups"]["T"]["alpha_v_vector"])
    return values


def max_mechanics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    fields = (
        "partition_max_abs_error", "selected_head_expected_max_abs_error",
        "nonselected_head_max_abs_delta", "other_position_max_abs_delta",
        "query_max_abs_delta", "key_max_abs_delta", "value_max_abs_delta",
        "attention_max_abs_delta",
    )
    maxima = {field: 0.0 for field in fields}
    flags: list[bool] = []
    baseline: list[bool] = []
    repeats: list[bool] = []
    lambda_one_internal: list[float] = []
    for row in rows:
        for target in row["target_results"].values():
            one_scores = []
            for arm in target["arms"].values():
                one_scores.append(float(arm["lambda_results"]["1.0"]["D"]))
                if arm["baseline_audit"]:
                    baseline.extend(bool(value) for value in arm["baseline_audit"].values())
                if arm["repeat_audit"]:
                    repeats.extend([
                        bool(arm["repeat_audit"]["exact"]),
                        float(arm["repeat_audit"]["D_max_abs_delta"]) == 0.0,
                    ])
                for scored in arm["lambda_results"].values():
                    flags.append(bool(scored["finite"]))
                    for audits in scored["candidate_audits"].values():
                        for audit in audits:
                            for field in fields:
                                maxima[field] = max(maxima[field], abs(float(audit[field])))
                            flags.extend([
                                bool(audit["lambda_one_exact"]),
                                bool(audit["lambda_zero_exact"]),
                                bool(audit["all_outputs_finite"]),
                            ])
            lambda_one_internal.append(max(one_scores) - min(one_scores))
    checks = {
        "all_finite_and_endpoint_flags": all(flags),
        "partition_within_tolerance": maxima["partition_max_abs_error"] <= 1e-6,
        "endpoint_arithmetic_exact": maxima["selected_head_expected_max_abs_error"] == 0.0,
        "nonselected_heads_exact": maxima["nonselected_head_max_abs_delta"] == 0.0,
        "other_positions_exact": maxima["other_position_max_abs_delta"] == 0.0,
        "qkv_attention_exact": all(maxima[field] == 0.0 for field in (
            "query_max_abs_delta", "key_max_abs_delta", "value_max_abs_delta", "attention_max_abs_delta"
        )),
        "lambda_one_all_arms_D_exact": max(lambda_one_internal, default=math.inf) == 0.0,
        "sampled_uninstrumented_baselines_exact": bool(baseline) and all(baseline),
        "sampled_repeats_exact": len(repeats) >= 4 and all(repeats),
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "maxima": maxima}


def main() -> None:
    manifest = read_jsonl(OUT / "cohort/primary_manifest.jsonl")
    expected = {str(row["base_problem_id"]) for row in manifest}
    paths = sorted((OUT / "raw/phase_a").glob("shard_*/examples/*/result.json"))
    rows = [read_json(path) for path in paths]
    observed = {str(row["base_problem_id"]) for row in rows}
    if len(rows) != 24 or observed != expected:
        raise RuntimeError(f"Incomplete Phase A: expected={sorted(expected)} observed={sorted(observed)}")
    mechanics = max_mechanics(rows)
    if mechanics["status"] != "PASS":
        write_json(OUT / "audit/primary_mechanics.json", mechanics)
        raise RuntimeError("Primary mechanics audit failed")
    write_json(OUT / "audit/primary_mechanics.json", mechanics)

    gain_rows: list[dict[str, Any]] = []
    mention_rows: list[dict[str, Any]] = []
    irrelevant_rows: list[dict[str, Any]] = []
    noncausal_rows: list[dict[str, Any]] = []
    per_problem: list[dict[str, Any]] = []
    retained_by_base: dict[str, dict[str, float]] = {}
    curves: dict[tuple[str, str], dict[float, float]] = {}
    controls: dict[tuple[str, str, str], dict[float, float]] = {}

    for row in sorted(rows, key=lambda item: int(item["base_problem_id"])):
        base = str(row["base_problem_id"])
        retained_by_base[base] = {}
        problem = {"base_problem_id": base, "example_id": str(row["example_id"]), "targets": {}}
        for target_id in TARGETS:
            arms = row["target_results"][target_id]["arms"]
            target_arm = arms["target_causal"]["lambda_results"]
            native = float(target_arm["1.0"]["D"])
            if native == 0.0:
                raise RuntimeError(f"Native evidence preference is zero for {base}/{target_id}")
            curve = {gain: float(target_arm[str(gain)]["D"]) for gain in GAINS}
            curves[(base, target_id)] = curve
            retained_by_base[base][target_id] = curve[0.0] / native
            target_problem = {"native_D": native, "target_curve": {}, "controls": {}}
            for gain in GAINS:
                scored = target_arm[str(gain)]
                audit = scored["candidate_audits"]["original_candidate"][0]
                direct = audit["target_contribution"]
                out = {
                    "base_problem_id": base,
                    "example_id": str(row["example_id"]),
                    "target_id": target_id,
                    "lambda": gain,
                    "E": curve[gain],
                    "ER_unclipped": curve[gain] / native,
                    "native_D": native,
                    "evidence_loss_native_minus_lambda": native - curve[gain],
                    "target_contribution_native_concat_norm": float(direct["concatenated_native_norm"]),
                    "target_contribution_scaled_concat_norm": float(direct["concatenated_scaled_norm"]),
                    "post_wo_native_sum_norm": float(direct["head_set_post_wo_native_sum_norm"]),
                    "post_wo_scaled_sum_norm": float(direct["head_set_post_wo_scaled_sum_norm"]),
                    "unnormalized_evidence_primary": True,
                }
                gain_rows.append(out)
                target_problem["target_curve"][str(gain)] = out
            for arm_id, destination in (
                ("mention_causal", mention_rows),
                ("irrelevant_causal", irrelevant_rows),
                ("target_noncausal", noncausal_rows),
            ):
                control_curve = {
                    float(gain): float(scored["D"])
                    for gain, scored in arms[arm_id]["lambda_results"].items()
                }
                controls[(base, target_id, arm_id)] = control_curve
                packed = []
                for gain in (1.0, 0.5, 0.0):
                    packed.append({
                        "base_problem_id": base,
                        "example_id": str(row["example_id"]),
                        "target_id": target_id,
                        "arm_id": arm_id,
                        "lambda": gain,
                        "E": control_curve[gain],
                        "native_D": control_curve[1.0],
                        "ER_unclipped": control_curve[gain] / control_curve[1.0],
                        "evidence_loss_native_minus_lambda": control_curve[1.0] - control_curve[gain],
                    })
                destination.extend(packed)
                target_problem["controls"][arm_id] = {str(k): v for k, v in control_curve.items()}
            problem["targets"][target_id] = target_problem
        per_problem.append(problem)

    write_jsonl(OUT / "phase_a_gain/per_problem_lambda_results.jsonl", per_problem)
    write_jsonl(OUT / "phase_a_gain/target_gain_results.jsonl", gain_rows)
    write_jsonl(OUT / "phase_a_gain/mention_control_results.jsonl", mention_rows)
    write_jsonl(OUT / "phase_a_gain/irrelevant_control_results.jsonl", irrelevant_rows)
    write_jsonl(OUT / "phase_a_gain/noncausal_head_controls.jsonl", noncausal_rows)

    historical = stage3c3_primary()
    query_rows = []
    for base in sorted(expected, key=int):
        source = historical[base]
        for target_id in TARGETS:
            target = source["target_results"][target_id]["O"]
            native_routing = target["native"]["R"]["routing_by_candidate"]["original_candidate"]["causal"]
            patched_routing = target["forms"]["content_recipient_rope"]["causal"]["Q_R_to_Q_M"]["routing_by_candidate"]["original_candidate"]
            operating = query_operating_point(
                contribution_vector(native_routing), contribution_vector(patched_routing)
            )
            thresholds = tested_thresholds(curves[(base, target_id)])
            query_rows.append({
                "base_problem_id": base,
                "target_id": target_id,
                "stage3c3_direction": "Q_R_to_Q_M necessity arm",
                "comparable_state": "retrieval state R at the same frozen coordinate",
                **operating,
                **thresholds,
                "norm_operating_point_at_or_above_lambda_80": (
                    None if thresholds["lambda_80"] is None
                    else operating["lambda_query_norm"] >= float(thresholds["lambda_80"])
                ),
                "projection_operating_point_at_or_above_lambda_80": (
                    None if thresholds["lambda_80"] is None
                    else operating["lambda_query_proj"] >= float(thresholds["lambda_80"])
                ),
            })
    write_jsonl(OUT / "phase_a_gain/query_patch_operating_points.jsonl", query_rows)

    gate = redundancy_gate(retained_by_base)
    gate.update({
        "phase_b_authorized": bool(gate["passed"]),
        "evaluated_after_phase_a_complete": True,
        "nested_family_frozen_before_phase_a": True,
        "decision": "PROCEED_PHASE_B" if gate["passed"] else "STOP_AFTER_PHASE_A",
    })
    write_json(OUT / "phase_b_redundancy/redundancy_gate.json", gate)

    dose_stats: dict[str, Any] = {
        "primary_unit": "base_problem_id",
        "N_unique_bases": len(expected),
        "unnormalized_evidence_primary": True,
        "targets": {},
    }
    threshold_rows = []
    saturation: dict[str, Any] = {"classification_is_descriptive": True, "targets": {}}
    specificity: dict[str, Any] = {"primary_unit": "base_problem_id", "targets": {}}
    for target_id in TARGETS:
        target_stats: dict[str, Any] = {"lambda_contrasts": {}, "monotonic_trend": {}}
        for gain in GAINS[1:]:
            effects = [curves[(base, target_id)][1.0] - curves[(base, target_id)][gain] for base in expected]
            target_stats["lambda_contrasts"][str(gain)] = bootstrap_summary(effects)
        correlations = []
        for base in expected:
            ordered = sorted(curves[(base, target_id)])
            rho = float(spearmanr(ordered, [curves[(base, target_id)][gain] for gain in ordered]).statistic)
            correlations.append(rho)
            threshold_rows.append({
                "base_problem_id": base,
                "target_id": target_id,
                **tested_thresholds(curves[(base, target_id)]),
            })
        target_stats["monotonic_trend"] = bootstrap_summary(correlations)
        dose_stats["targets"][target_id] = target_stats
        median_er = {
            str(gain): float(np.median([
                curves[(base, target_id)][gain] / curves[(base, target_id)][1.0]
                for base in expected
            ]))
            for gain in GAINS
        }
        saturation["targets"][target_id] = {
            "median_ER_by_lambda": median_er,
            "median_lambda0_retained": median_er["0.0"],
            "plateau_through_lambda_0_25": median_er["0.25"] >= 0.80,
            "substantial_lambda0_loss": median_er["0.0"] < 0.80,
            "selected_path_not_necessary_by_target_median": median_er["0.0"] >= 0.50,
            "strong_saturation_signature": median_er["0.25"] >= 0.80 and median_er["0.0"] < 0.80,
        }
        target_loss = [curves[(base, target_id)][1.0] - curves[(base, target_id)][0.0] for base in expected]
        mention_loss = [
            controls[(base, target_id, "mention_causal")][1.0]
            - controls[(base, target_id, "mention_causal")][0.0]
            for base in expected
        ]
        irrelevant_loss = [
            controls[(base, target_id, "irrelevant_causal")][1.0]
            - controls[(base, target_id, "irrelevant_causal")][0.0]
            for base in expected
        ]
        noncausal_loss = [
            controls[(base, target_id, "target_noncausal")][1.0]
            - controls[(base, target_id, "target_noncausal")][0.0]
            for base in expected
        ]
        specificity["targets"][target_id] = {
            "T_loss": bootstrap_summary(target_loss),
            "M_loss": bootstrap_summary(mention_loss),
            "I_loss": bootstrap_summary(irrelevant_loss),
            "noncausal_T_loss": bootstrap_summary(noncausal_loss),
            "T_minus_M_loss": bootstrap_summary([a - b for a, b in zip(target_loss, mention_loss)]),
            "T_minus_I_loss": bootstrap_summary([a - b for a, b in zip(target_loss, irrelevant_loss)]),
            "causal_minus_noncausal_T_loss": bootstrap_summary([a - b for a, b in zip(target_loss, noncausal_loss)]),
        }
    write_json(OUT / "analysis/dose_response_statistics.json", dose_stats)
    write_json(OUT / "analysis/threshold_descriptives.json", {
        "definition": "smallest tested lambda retaining threshold; only approximately monotonic curves; no interpolation",
        "rows": threshold_rows,
    })
    write_json(OUT / "analysis/saturation_analysis.json", saturation)
    query_comparison = {
        "primary_unit": "base_problem_id",
        "necessity_operating_point_only": True,
        "targets": {},
    }
    for target_id in TARGETS:
        selected = [row for row in query_rows if row["target_id"] == target_id]
        eligible = [row for row in selected if row["lambda_80"] is not None]
        query_comparison["targets"][target_id] = {
            "N": len(selected),
            "norm_gain": bootstrap_summary([float(row["lambda_query_norm"]) for row in selected]),
            "projection_gain": bootstrap_summary([float(row["lambda_query_proj"]) for row in selected]),
            "N_with_lambda_80": len(eligible),
            "norm_at_or_above_lambda_80_fraction": (
                float(np.mean([row["norm_operating_point_at_or_above_lambda_80"] for row in eligible]))
                if eligible else None
            ),
            "projection_at_or_above_lambda_80_fraction": (
                float(np.mean([row["projection_operating_point_at_or_above_lambda_80"] for row in eligible]))
                if eligible else None
            ),
        }
    write_json(OUT / "analysis/query_patch_curve_comparison.json", query_comparison)
    write_json(OUT / "analysis/target_specificity_analysis.json", specificity)
    print(json.dumps({
        "mechanics": mechanics["status"],
        "N": len(expected),
        "gate": gate,
        "median_ER": {target: saturation["targets"][target]["median_ER_by_lambda"] for target in TARGETS},
    }, indent=2))


if __name__ == "__main__":
    main()
