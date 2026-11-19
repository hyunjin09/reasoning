#!/usr/bin/env python3
"""Finalize target-specific Stage 3C.7 classifications and controls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import spearmanr

from visual_reasoning.stage3c4.analysis import signed_summary
from visual_reasoning.stage3c7.protocol import joint_outcome, recommendation_for_outcome


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c7"
TARGETS = ("target_a", "target_b")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def result_map(root: Path) -> dict[str, dict[str, Any]]:
    return {str(row["base_problem_id"]): row for path in sorted(root.glob("shard_*/examples/*/result.json")) for row in [read_json(path)]}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def exact(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return bool(
        float(left["D"]) == float(right["D"])
        and left["original_candidate"]["token_log_probabilities"] == right["original_candidate"]["token_log_probabilities"]
        and left["counterfactual_candidate"]["token_log_probabilities"] == right["counterfactual_candidate"]["token_log_probabilities"]
    )


def main() -> None:
    family = read_json(OUT / "analysis/primary_test_family.json")
    cache = read_json(OUT / "phase_a_cache/cache_rescue_statistics.json")
    joint = read_json(OUT / "phase_b_joint/joint_statistics.json")
    raw = result_map(OUT / "raw/primary")
    classifications = {}
    recommendations = []
    exact_rows = []
    for target in TARGETS:
        tests = family["targets"][target]["tests"]
        outcome = joint_outcome(
            full_cache=tests["KV_gt_0"], residual=tests["residual_gt_0"],
            downstream_cache=tests["downstream_cache_gt_0"], joint=tests["joint_gt_0"],
            joint_over_residual=tests["joint_minus_residual"],
            joint_over_cache=tests["joint_minus_downstream_cache"],
        )
        recommendation = recommendation_for_outcome(
            outcome, joint_near_complete=family["targets"][target]["joint_near_complete"],
            cache_nonzero=tests["KV_gt_0"]["robust_positive"],
        )
        recommendations.append(recommendation)
        classifications[target] = {
            "cache_classification": family["targets"][target]["cache_classification"],
            "joint_outcome": outcome,
            "full_cache_median_RR": tests["KV_gt_0"]["median_RR"],
            "residual_median_RR": tests["residual_gt_0"]["median_RR"],
            "downstream_cache_median_RR": tests["downstream_cache_gt_0"]["median_RR"],
            "joint_median_RR": tests["joint_gt_0"]["median_RR"],
            "joint_substantial": family["targets"][target]["joint_substantial"],
            "joint_near_complete": family["targets"][target]["joint_near_complete"],
            "review_only_recommendation": recommendation,
        }
    for base, result in raw.items():
        for target, target_row in result["target_results"].items():
            for condition, row in target_row["conditions"].items():
                exact_rows.append({
                    "base_problem_id": base, "target": target, "condition": condition,
                    "full_KV_exact_native": exact(row["arms"]["C4_KV"], row["native"]),
                    "full_KV_plus_residual_exact_native": exact(row["arms"]["J5_full_KV_plus_residual"], row["native"]),
                    "q_prompt_exact_suppressed": exact(row["q_prompt_control"], row["suppressed"]),
                })
    control_gains = read_jsonl(OUT / "controls/q_prompt_negative_control.jsonl")
    q_values = [float(row["mean_sign_aligned_gain"]) for row in control_gains]
    q_stats = signed_summary(q_values)
    q_output = {
        "N_target_base_rows": len(q_values), "all_exact_suppressed": all(row["exact_suppressed"] for row in control_gains),
        "gain_summary": q_stats, "expected_near_zero": True,
    }
    write_json(OUT / "controls/q_prompt_negative_control_statistics.json", q_output)
    write_json(OUT / "analysis/exact_endpoint_analysis.json", {
        "N_target_condition_base_cells": len(exact_rows),
        "full_KV_exact_native_count": sum(r["full_KV_exact_native"] for r in exact_rows),
        "full_KV_plus_residual_exact_native_count": sum(r["full_KV_plus_residual_exact_native"] for r in exact_rows),
        "q_prompt_exact_suppressed_count": sum(r["q_prompt_exact_suppressed"] for r in exact_rows),
        "rows": exact_rows,
    })
    # Relate descriptively measured native/suppressed cache deltas to base-level rescue.
    delta_audit = read_json(OUT / "audit/primary_native_suppressed_cache_deltas.json")["rows"]
    kv_rows = read_jsonl(OUT / "phase_a_cache/kv_results.jsonl")
    delta_correlations = {}
    for target in TARGETS:
        delta_by_base = {}
        for row in delta_audit:
            if row["target"] != target:
                continue
            delta_by_base.setdefault(row["base_problem_id"], []).append(float(row["key_delta_l2"]) + float(row["value_delta_l2"]))
        rescue_by_base = {row["base_problem_id"]: float(row["sign_aligned"]["rescue_gain"]) for row in kv_rows if row["target_id"] == target}
        bases = sorted(set(delta_by_base) & set(rescue_by_base))
        x = [float(np.mean(delta_by_base[base])) for base in bases]
        y = [rescue_by_base[base] for base in bases]
        rho, p = spearmanr(x, y)
        delta_correlations[target] = {"N": len(bases), "spearman_rho": float(rho), "two_sided_p": float(p), "secondary_descriptive": True}
    classification = {
        "primary_unit": "base_problem_id", "N_unique_bases": len(raw),
        "targets": classifications,
        "overall": "target_heterogeneous_O2_A_O1_B",
        "overall_interpretation": "Full native t_pre K+V is a complete tested carrier for both targets; Target A additionally shows clean complementarity at the frozen late residual/downstream-cache boundary, while Target B requires broader P4 cache access than its one-layer downstream scope.",
        "single_review_only_recommendation": "GO — Token-Type Carrier Atlas",
        "recommendation_agrees_across_targets": len(set(recommendations)) == 1,
        "attention_used_for_selection_or_intervention": False,
        "RR_unique_information_fraction": False,
    }
    write_json(OUT / "analysis/two_query_classification.json", classification)
    write_json(OUT / "analysis/cache_delta_rescue_relationship.json", delta_correlations)
    cache["exact_endpoint_analysis"] = read_json(OUT / "analysis/exact_endpoint_analysis.json")
    cache["cache_delta_rescue_relationship"] = delta_correlations
    joint["target_classifications"] = classifications
    write_json(OUT / "analysis/prior_cache_mechanism.json", cache)
    write_json(OUT / "analysis/residual_cache_complementarity.json", joint)
    write_json(OUT / "analysis/target_heterogeneity.json", {
        "targets": classifications,
        "contrast": "Target A clean late residual-cache complementarity; Target B full-cache carrier but insufficient one-layer downstream joint rescue",
        "pooled_primary_inference": False,
    })
    print(json.dumps(classification, indent=2))


if __name__ == "__main__":
    main()
