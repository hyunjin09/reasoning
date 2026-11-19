#!/usr/bin/env python3
"""Independent raw-artifact and acceptance validation for Stage 3C.7."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import torch
from scipy.stats import wilcoxon


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c7"
CONDITIONS = ("O", "C")
TARGETS = ("target_a", "target_b")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def results(root: Path) -> dict[str, dict[str, Any]]:
    return {str(row["base_problem_id"]): row for path in sorted(root.glob("shard_*/examples/*/result.json")) for row in [read_json(path)]}


def aligned(value: float, condition: str) -> float:
    return float(value) if condition == "O" else -float(value)


def exact(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return bool(float(left["D"]) == float(right["D"]) and left["original_candidate"]["token_log_probabilities"] == right["original_candidate"]["token_log_probabilities"] and left["counterfactual_candidate"]["token_log_probabilities"] == right["counterfactual_candidate"]["token_log_probabilities"])


def one_sided(values: list[float]) -> float:
    array = np.asarray(values, dtype=np.float64)
    if np.all(array == 0):
        return 1.0
    value = float(wilcoxon(array, alternative="greater").pvalue)
    return value if math.isfinite(value) else 1.0


def holm(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=values.__getitem__)
    result = [1.0] * len(values)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(values) - rank) * values[index]))
        result[index] = running
    return result


def main() -> None:
    config = read_json(OUT / "config/stage3c7_config.json")
    primary = results(OUT / "raw/primary")
    validation = results(OUT / "raw/validation")
    expected_primary = set(config["primary_base_problem_ids"])
    expected_validation = set(config["validation_base_problem_ids"])
    family = read_json(OUT / "analysis/primary_test_family.json")
    test_ids = read_json(OUT / "config/primary_family.json")["test_ids"]
    arm = {
        "K_gt_0": "C2_K", "V_gt_0": "C3_V", "KV_gt_0": "C4_KV",
        "residual_gt_0": "J1_residual", "downstream_cache_gt_0": "J3_downstream_KV",
        "joint_gt_0": "J4_joint", "full_cache_plus_residual_gt_0": "J5_full_KV_plus_residual",
    }
    recomputed = {}
    full_exact = q_exact = j5_exact = 0
    mechanics = []
    reproduction = []
    tensor_layout = []
    for target in TARGETS:
        gains = {name: [] for name in arm}
        ratios = {name: [] for name in arm}
        for base in config["primary_base_problem_ids"]:
            conditions = primary[base]["target_results"][target]["conditions"]
            condition_values = {name: [] for name in arm}
            losses = []
            for condition in CONDITIONS:
                row = conditions[condition]
                loss = aligned(row["native"]["D"], condition) - aligned(row["suppressed"]["D"], condition)
                losses.append(loss)
                reproduction.append(all(row["stage3c6_reproduction"][key] for key in ("native_exact", "suppressed_exact", "residual_exact")))
                for name, raw_arm in arm.items():
                    gain = aligned(row["arms"][raw_arm]["D"], condition) - aligned(row["suppressed"]["D"], condition)
                    condition_values[name].append(gain)
                full_exact += int(exact(row["arms"]["C4_KV"], row["native"]))
                j5_exact += int(exact(row["arms"]["J5_full_KV_plus_residual"], row["native"]))
                q_exact += int(exact(row["q_prompt_control"], row["suppressed"]))
                for raw_arm in ("C2_K", "C3_V", "C4_KV", "J3_downstream_KV", "J4_joint", "J5_full_KV_plus_residual"):
                    current = row["arms"][raw_arm]
                    for candidate in ("original_candidate", "counterfactual_candidate"):
                        selected = [a for a in current["cache_patch_audits"][candidate] if a.get("layer_selected")]
                        mechanics.append(bool(
                            selected and all(a["positions_replaced"] == [current["tpre_absolute_position"]] for a in selected)
                            and all(a["non_tpre_key_max_abs_delta"] == 0 and a["non_tpre_value_max_abs_delta"] == 0 for a in selected)
                            and all(a["visual_positions_replaced"] == [] and not a["current_query_position_replaced"] and a["query_vectors_replaced"] == 0 for a in selected)
                        ))
            mean_loss = float(np.mean(losses))
            for name in arm:
                value = float(np.mean(condition_values[name])); gains[name].append(value); ratios[name].append(value / mean_loss)
        vectors = {
            **{name: gains[name] for name in arm},
            "KV_minus_K": (np.asarray(gains["KV_gt_0"]) - np.asarray(gains["K_gt_0"])).tolist(),
            "KV_minus_V": (np.asarray(gains["KV_gt_0"]) - np.asarray(gains["V_gt_0"])).tolist(),
            "joint_minus_residual": (np.asarray(gains["joint_gt_0"]) - np.asarray(gains["residual_gt_0"])).tolist(),
            "joint_minus_downstream_cache": (np.asarray(gains["joint_gt_0"]) - np.asarray(gains["downstream_cache_gt_0"])).tolist(),
            "full_cache_minus_residual": (np.asarray(gains["KV_gt_0"]) - np.asarray(gains["residual_gt_0"])).tolist(),
        }
        p_values = [one_sided(vectors[name]) for name in test_ids]
        adjusted = holm(p_values)
        recomputed[target] = {}
        for name, p, adj in zip(test_ids, p_values, adjusted):
            stored = family["targets"][target]["tests"][name]
            row = {
                "median_gain": float(np.median(vectors[name])), "positive_count": int(np.sum(np.asarray(vectors[name]) > 0)),
                "wilcoxon": p, "holm": adj,
            }
            if name in ratios:
                row["median_RR"] = float(np.median(ratios[name]))
            row["matches_stored"] = bool(
                abs(row["median_gain"] - stored["median_gain"]) < 1e-12
                and row["positive_count"] == stored["positive_count"]
                and abs(row["wilcoxon"] - stored["wilcoxon_one_sided_greater_p"]) < 1e-12
                and abs(row["holm"] - stored["holm_adjusted_p"]) < 1e-12
                and ("median_RR" not in row or abs(row["median_RR"] - stored["median_RR"]) < 1e-12)
            )
            recomputed[target][name] = row
    for result in primary.values():
        tensor_path = next(path for path in (OUT / "raw/primary").glob(f"shard_*/examples/{result['base_problem_id']}/{result['state_tensor_artifact']}"))
        values = torch.load(tensor_path, map_location="cpu", weights_only=True)
        tensor_layout.append(bool(values and all(torch.isfinite(v).all() and (v.ndim != 4 or tuple(v.shape[1:]) == (8, 1, 128)) for v in values.values())))
    self_controls = read_json(OUT / "audit/mechanical_validation_summary.json")["checks"]
    config_files = ["stage3c7_config.json", "frozen_targets.json", "suppression_definition.json", "cache_scope.json", "residual_boundaries.json", "joint_intervention_definition.json", "primary_family.json"]
    required_files = [
        "phase_a_cache/k_only_results.jsonl", "phase_a_cache/v_only_results.jsonl", "phase_a_cache/kv_results.jsonl",
        "phase_a_cache/cache_rescue_statistics.json", "phase_a_cache/cache_delta_statistics.json",
        "phase_b_joint/residual_only_results.jsonl", "phase_b_joint/downstream_cache_only_results.jsonl",
        "phase_b_joint/joint_results.jsonl", "phase_b_joint/full_cache_plus_residual_results.jsonl",
        "phase_b_joint/joint_statistics.json", "phase_b_joint/optional_joint_kv_decomposition.jsonl",
        "controls/q_prompt_negative_control.jsonl", "controls/self_controls.jsonl",
        "analysis/prior_cache_mechanism.json", "analysis/residual_cache_complementarity.json",
        "analysis/target_heterogeneity.json", "analysis/two_query_classification.json",
        "summaries/stage3c7_summary.md", "summaries/stage3c7_acceptance.json", "summaries/next_stage_recommendation.md",
    ]
    report = read_json(OUT / "summaries/stage3c7_acceptance.json")
    classification = read_json(OUT / "analysis/two_query_classification.json")
    checks = {
        "01_exact_targets": sha(OUT / "cohort/primary_manifest.jsonl") == sha(ROOT / "outputs/stage3c6/cohort/primary_manifest.jsonl"),
        "02_exact_p4_reproduction": bool(reproduction) and all(reproduction),
        "03_within_condition": all(set(primary[b]["target_results"][t]["conditions"]) == {"O", "C"} for b in primary for t in TARGETS),
        "04_tpre_position_frozen": self_controls["position"],
        "05_native_gqa_layout": all(tensor_layout),
        "06_visual_never_patched": self_controls["visual_invariance"],
        "07_current_query_never_cache_patched": self_controls["current_invariance"],
        "08_non_tpre_cache_native": bool(mechanics) and all(mechanics),
        "09_components_isolated": self_controls["selectivity"] and read_json(OUT / "audit/joint_kv_decomposition_primary_validation.json")["checks"]["K_V_KV_isolated"],
        "10_residual_reproduction": all(reproduction),
        "11_boundaries_pre_frozen": (OUT / "config/residual_boundaries.json").is_file(),
        "12_downstream_scope_semantic": read_json(OUT / "config/cache_scope.json")["downstream_by_target"] == {"target_a": [34, 35], "target_b": [35]},
        "13_joint_order": self_controls["joint_order"],
        "14_self_patches": self_controls["self_controls"],
        "15_targets_separate": set(classification["targets"]) == set(TARGETS),
        "16_unnormalized_primary": read_json(OUT / "config/primary_family.json")["primary_readout"].startswith("unnormalized"),
        "17_ratios_unclipped": all(family["targets"][t]["tests"][name].get("RR_is_clipped") is False for t in TARGETS for name in arm),
        "18_no_token_sink": not config["token_type_scan"] and not config["sink_manipulated"],
        "19_no_stage4_failure": not config["stage4_authorized"] and all(not row["stage4_started"] for row in primary.values()),
        "20_one_recommendation": classification["single_review_only_recommendation"] == "GO — Token-Type Carrier Atlas" and classification["recommendation_agrees_across_targets"],
        "cohort_cardinality": set(primary) == expected_primary and set(validation) == expected_validation and len(primary) == 24 and len(validation) == 7,
        "config_files": all((OUT / "config" / name).is_file() for name in config_files),
        "required_files": all((OUT / name).is_file() for name in required_files),
        "figures": len(list((OUT / "analysis/figures").glob("*.png"))) == 14 and all(path.stat().st_size > 0 for path in (OUT / "analysis/figures").glob("*.png")),
        "metrics_recomputed": all(row["matches_stored"] for target in recomputed.values() for row in target.values()),
        "exact_endpoints": full_exact == 96 and j5_exact == 96 and q_exact == 96,
        "acceptance_report": report["status"] == "PASS" and report["passed"] == 20 and report["total"] == 20,
        "failed_smoke_excluded": (OUT / "raw/validation_smoke_failed_v1").is_dir() and "failed_v1" not in " ".join(str(path) for path in (OUT / "phase_a_cache").glob("*")),
    }
    output = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "passed": sum(checks.values()), "total": len(checks), "checks": checks,
        "raw_counts": {"validation": len(validation), "primary": len(primary)},
        "recomputed_primary_tests": recomputed,
        "exact_endpoint_counts": {"full_KV_native": full_exact, "J5_native": j5_exact, "Q_suppressed": q_exact},
    }
    path = OUT / "audit/artifact_validation.json"
    path.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({k: output[k] for k in ("status", "passed", "total", "raw_counts", "exact_endpoint_counts")}, indent=2))
    if output["status"] != "PASS":
        print(json.dumps({k: v for k, v in checks.items() if not v}, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
