#!/usr/bin/env python3
"""Aggregate frozen Stage 3C.7 primary cache and joint rescue arms."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage3c4.analysis import holm_adjust, signed_summary
from visual_reasoning.stage3c7.protocol import rescue_effect, robust_effect, substantial


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c7"
TARGETS = ("target_a", "target_b")
CONDITIONS = ("O", "C")
ARM_TO_OUTPUT = {
    "C2_K": "phase_a_cache/k_only_results.jsonl",
    "C3_V": "phase_a_cache/v_only_results.jsonl",
    "C4_KV": "phase_a_cache/kv_results.jsonl",
    "J1_residual": "phase_b_joint/residual_only_results.jsonl",
    "J3_downstream_KV": "phase_b_joint/downstream_cache_only_results.jsonl",
    "J4_joint": "phase_b_joint/joint_results.jsonl",
    "J5_full_KV_plus_residual": "phase_b_joint/full_cache_plus_residual_results.jsonl",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, allow_nan=False) + "\n" for row in rows), encoding="utf-8")


def result_map(root: Path) -> dict[str, dict[str, Any]]:
    return {
        str(row["base_problem_id"]): row
        for path in sorted(root.glob("shard_*/examples/*/result.json"))
        for row in [read_json(path)]
    }


def aggregate_arm(base: str, target_id: str, source: dict[str, Any], arm: str) -> dict[str, Any]:
    conditions: dict[str, Any] = {}
    for condition in CONDITIONS:
        row = source[condition]
        conditions[condition] = rescue_effect(
            native_d=float(row["native"]["D"]), suppressed_d=float(row["suppressed"]["D"]),
            rescued_d=float(row["arms"][arm]["D"]), condition=condition,
        )
    loss = float(np.mean([conditions[c]["suppression_loss"] for c in CONDITIONS]))
    gain = float(np.mean([conditions[c]["rescue_gain"] for c in CONDITIONS]))
    return {
        "base_problem_id": base, "target_id": target_id, "arm": arm,
        "conditions": conditions,
        "sign_aligned": {
            "suppression_loss": loss, "rescue_gain": gain,
            "rescue_ratio": gain / loss if loss != 0 else None,
            "rescue_ratio_is_clipped": False,
        },
    }


def effect_summary(values: list[float], ratios: list[float] | None, seed: int) -> dict[str, Any]:
    summary = signed_summary(values, seed=seed)
    row = {
        "N": summary["N"], "mean_gain": summary["mean"], "median_gain": summary["median"],
        "gain_bootstrap_mean_ci95": summary["bootstrap_mean_ci95"],
        "positive_count": summary["positive_count"], "positive_fraction": summary["positive_fraction"],
        "wilcoxon_one_sided_greater_p": summary["wilcoxon_one_sided_greater_p"],
        "values": values,
    }
    if ratios is not None:
        row.update({"median_RR": float(np.median(ratios)), "mean_RR": float(np.mean(ratios)), "RR_values": ratios, "RR_is_clipped": False})
    return row


def main() -> None:
    config = read_json(OUT / "config/stage3c7_config.json")
    raw = result_map(OUT / "raw/primary")
    expected = [str(value) for value in config["primary_base_problem_ids"]]
    if set(raw) != set(expected):
        raise RuntimeError(f"Primary cohort mismatch: {sorted(raw)}")
    arm_rows = {arm: [] for arm in ARM_TO_OUTPUT}
    q_rows: list[dict[str, Any]] = []
    delta_rows: list[dict[str, Any]] = []
    reproduction_rows: list[dict[str, Any]] = []
    for base in expected:
        for target_id in TARGETS:
            source = raw[base]["target_results"][target_id]["conditions"]
            for arm in arm_rows:
                arm_rows[arm].append(aggregate_arm(base, target_id, source, arm))
            q_conditions = {
                condition: rescue_effect(
                    native_d=float(source[condition]["native"]["D"]),
                    suppressed_d=float(source[condition]["suppressed"]["D"]),
                    rescued_d=float(source[condition]["q_prompt_control"]["D"]),
                    condition=condition,
                ) for condition in CONDITIONS
            }
            q_rows.append({
                "base_problem_id": base, "target_id": target_id, "conditions": q_conditions,
                "mean_sign_aligned_gain": float(np.mean([q_conditions[c]["rescue_gain"] for c in CONDITIONS])),
                "exact_suppressed": all(float(source[c]["q_prompt_control"]["D"]) == float(source[c]["suppressed"]["D"]) for c in CONDITIONS),
            })
            for condition in CONDITIONS:
                reproduction_rows.append({
                    "base_problem_id": base, "target_id": target_id, "condition": condition,
                    **source[condition]["stage3c6_reproduction"],
                })
                for candidate, rows in source[condition]["cache_deltas"].items():
                    for row in rows:
                        delta_rows.append({"base_problem_id": base, "target_id": target_id, "condition": condition, "candidate": candidate, **row})
    for arm, relative in ARM_TO_OUTPUT.items():
        write_jsonl(OUT / relative, arm_rows[arm])
    write_jsonl(OUT / "controls/q_prompt_negative_control.jsonl", q_rows)
    write_json(OUT / "audit/residual_reproduction.json", {
        "rows": reproduction_rows,
        "all_native_exact": all(r["native_exact"] for r in reproduction_rows),
        "all_suppressed_exact": all(r["suppressed_exact"] for r in reproduction_rows),
        "all_residual_exact": all(r["residual_exact"] for r in reproduction_rows),
    })
    cache_delta_stats: dict[str, Any] = {"used_for_layer_or_scope_selection": False, "targets": {}}
    for target_id in TARGETS:
        target_rows = [r for r in delta_rows if r["target_id"] == target_id]
        by_layer = {}
        for layer in config["cache_scope"]["layers"]:
            current = [r for r in target_rows if int(r["layer"]) == int(layer)]
            by_layer[str(layer)] = {
                "N_condition_candidate_base_rows": len(current),
                "median_key_delta_l2": float(np.median([r["key_delta_l2"] for r in current])),
                "median_value_delta_l2": float(np.median([r["value_delta_l2"] for r in current])),
                "maximum_key_delta_l2": float(np.max([r["key_delta_l2"] for r in current])),
                "maximum_value_delta_l2": float(np.max([r["value_delta_l2"] for r in current])),
            }
        cache_delta_stats["targets"][target_id] = {"layers": by_layer}
    write_json(OUT / "phase_a_cache/cache_delta_statistics.json", cache_delta_stats)

    target_statistics: dict[str, Any] = {}
    test_ids = read_json(OUT / "config/primary_family.json")["test_ids"]
    for target_index, target_id in enumerate(TARGETS):
        lookup = {
            arm: [row for row in rows if row["target_id"] == target_id]
            for arm, rows in arm_rows.items()
        }
        gains = {arm: [r["sign_aligned"]["rescue_gain"] for r in rows] for arm, rows in lookup.items()}
        ratios = {arm: [r["sign_aligned"]["rescue_ratio"] for r in rows] for arm, rows in lookup.items()}
        vectors = {
            "K_gt_0": gains["C2_K"],
            "V_gt_0": gains["C3_V"],
            "KV_gt_0": gains["C4_KV"],
            "KV_minus_K": (np.asarray(gains["C4_KV"]) - np.asarray(gains["C2_K"])).tolist(),
            "KV_minus_V": (np.asarray(gains["C4_KV"]) - np.asarray(gains["C3_V"])).tolist(),
            "residual_gt_0": gains["J1_residual"],
            "downstream_cache_gt_0": gains["J3_downstream_KV"],
            "joint_gt_0": gains["J4_joint"],
            "joint_minus_residual": (np.asarray(gains["J4_joint"]) - np.asarray(gains["J1_residual"])).tolist(),
            "joint_minus_downstream_cache": (np.asarray(gains["J4_joint"]) - np.asarray(gains["J3_downstream_KV"])).tolist(),
            "full_cache_minus_residual": (np.asarray(gains["C4_KV"]) - np.asarray(gains["J1_residual"])).tolist(),
            "full_cache_plus_residual_gt_0": gains["J5_full_KV_plus_residual"],
        }
        ratio_map = {
            "K_gt_0": ratios["C2_K"], "V_gt_0": ratios["C3_V"], "KV_gt_0": ratios["C4_KV"],
            "residual_gt_0": ratios["J1_residual"], "downstream_cache_gt_0": ratios["J3_downstream_KV"],
            "joint_gt_0": ratios["J4_joint"], "full_cache_plus_residual_gt_0": ratios["J5_full_KV_plus_residual"],
        }
        tests = {
            test_id: effect_summary(vectors[test_id], ratio_map.get(test_id), 20267000 + 100 * target_index + i)
            for i, test_id in enumerate(test_ids)
        }
        adjusted = holm_adjust([float(tests[test_id]["wilcoxon_one_sided_greater_p"]) for test_id in test_ids])
        for test_id, p_value in zip(test_ids, adjusted):
            tests[test_id]["holm_adjusted_p"] = p_value
            tests[test_id]["robust_positive"] = robust_effect(tests[test_id])
        cache = tests["KV_gt_0"]
        k_approaches = bool(tests["K_gt_0"]["robust_positive"] and tests["K_gt_0"]["median_gain"] >= 0.8 * cache["median_gain"])
        v_approaches = bool(tests["V_gt_0"]["robust_positive"] and tests["V_gt_0"]["median_gain"] >= 0.8 * cache["median_gain"])
        if v_approaches and not k_approaches:
            cache_class = "C_Value"
        elif k_approaches and not v_approaches:
            cache_class = "C_Key"
        elif tests["KV_minus_K"]["robust_positive"] and tests["KV_minus_V"]["robust_positive"]:
            cache_class = "C_KV"
        elif substantial(cache):
            cache_class = "C_Strong_mixed"
        else:
            cache_class = "C_Weak"
        joint = tests["joint_gt_0"]
        target_statistics[target_id] = {
            "tests": tests, "cache_classification": cache_class,
            "K_approaches_KV": k_approaches, "V_approaches_KV": v_approaches,
            "full_cache_substantial": substantial(cache),
            "joint_substantial": substantial(joint),
            "joint_near_complete": substantial(joint, 0.80),
            "joint_interaction_median": float(np.median(
                np.asarray(gains["J4_joint"]) - np.asarray(gains["J1_residual"]) - np.asarray(gains["J3_downstream_KV"])
            )),
        }
    cache_output = {
        "primary_unit": "base_problem_id", "N_unique_bases": len(expected),
        "O_and_C_reported_separately": True, "unnormalized_gain_primary": True,
        "rescue_ratios_unclipped": True,
        "targets": {target: {key: value for key, value in target_statistics[target].items() if key in {"cache_classification", "K_approaches_KV", "V_approaches_KV", "full_cache_substantial"}} | {"tests": {key: target_statistics[target]["tests"][key] for key in ("K_gt_0", "V_gt_0", "KV_gt_0", "KV_minus_K", "KV_minus_V")}} for target in TARGETS},
    }
    joint_output = {
        "primary_unit": "base_problem_id", "N_unique_bases": len(expected),
        "O_and_C_reported_separately": True, "unnormalized_gain_primary": True,
        "rescue_ratios_unclipped": True,
        "targets": {target: {key: value for key, value in target_statistics[target].items() if key in {"joint_substantial", "joint_near_complete", "joint_interaction_median"}} | {"tests": {key: target_statistics[target]["tests"][key] for key in ("residual_gt_0", "downstream_cache_gt_0", "joint_gt_0", "joint_minus_residual", "joint_minus_downstream_cache", "full_cache_minus_residual", "full_cache_plus_residual_gt_0")}} for target in TARGETS},
    }
    write_json(OUT / "phase_a_cache/cache_rescue_statistics.json", cache_output)
    write_json(OUT / "phase_b_joint/joint_statistics.json", joint_output)
    gate = {
        "frozen_after_primary_J4_and_before_optional_decomposition": True,
        "rule": "J4 robust with median RR>=0.50 separately per target",
        "targets": {
            target: {"run": bool(target_statistics[target]["joint_substantial"]), "joint_substantial": bool(target_statistics[target]["joint_substantial"]), "median_RR_joint": float(target_statistics[target]["tests"]["joint_gt_0"]["median_RR"])}
            for target in TARGETS
        },
    }
    write_json(OUT / "phase_b_joint/joint_kv_decomposition_gate.json", gate)
    write_json(OUT / "analysis/primary_test_family.json", {"tests_per_target": 12, "targets": target_statistics})
    write_json(OUT / "analysis/prior_cache_mechanism.json", cache_output)
    write_json(OUT / "analysis/residual_cache_complementarity.json", joint_output)
    write_json(OUT / "analysis/target_heterogeneity.json", {
        "target_a": target_statistics["target_a"], "target_b": target_statistics["target_b"],
        "pooled_primary_inference": False,
    })
    # Validation-only self controls are copied into the required control table.
    validation = result_map(OUT / "raw/validation")
    self_rows = []
    for base, result in validation.items():
        for target_id, target in result["target_results"].items():
            for condition, row in target["conditions"].items():
                self_rows.append({
                    "base_problem_id": base, "target_id": target_id, "condition": condition,
                    "native_cache_exact": float(row["self_controls"]["native_cache"]["D"]) == float(row["native"]["D"]),
                    "suppressed_cache_exact": float(row["self_controls"]["suppressed_cache"]["D"]) == float(row["suppressed"]["D"]),
                    "native_residual_exact": float(row["self_controls"]["native_residual"]["D"]) == float(row["native"]["D"]),
                    "suppressed_residual_exact": float(row["self_controls"]["suppressed_residual"]["D"]) == float(row["suppressed"]["D"]),
                })
    write_jsonl(OUT / "controls/self_controls.jsonl", self_rows)
    write_json(OUT / "secondary/stage3c5_r_last1_comparison.json", {
        "stage3c5_pooled_median_CRR_R_last1": 0.0719,
        "stage3c7_within_condition_full_cache_median_RR": {target: target_statistics[target]["tests"]["KV_gt_0"]["median_RR"] for target in TARGETS},
        "comparison_is_descriptive": True,
    })
    write_json(OUT / "secondary/stage3c6_residual_comparison.json", {
        "stage3c6_exact_reproduction": all(r["native_exact"] and r["suppressed_exact"] and r["residual_exact"] for r in reproduction_rows),
        "targets": {target: {
            "residual_median_RR": target_statistics[target]["tests"]["residual_gt_0"]["median_RR"],
            "joint_median_RR": target_statistics[target]["tests"]["joint_gt_0"]["median_RR"],
            "joint_minus_residual_robust": target_statistics[target]["tests"]["joint_minus_residual"]["robust_positive"],
        } for target in TARGETS},
    })
    print(json.dumps({"N": len(expected), "gate": gate, "cache": {t: target_statistics[t]["cache_classification"] for t in TARGETS}}, indent=2))


if __name__ == "__main__":
    main()
