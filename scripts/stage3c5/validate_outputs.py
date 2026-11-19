#!/usr/bin/env python3
"""Independently validate Stage 3C.5 raw artifacts, metrics, and stop boundary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import torch

from visual_reasoning.stage3c5.protocol import carrier_restoration, frozen_tpre_layer_scopes


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c5"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def result_map(root: Path) -> dict[str, dict[str, Any]]:
    return {
        str(row["base_problem_id"]): row
        for path in sorted(root.glob("shard_*/examples/*/result.json"))
        for row in [read_json(path)]
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(left: float, right: float, tolerance: float = 1e-10) -> bool:
    return abs(float(left) - float(right)) <= tolerance


def base_carrier_values(rows: dict[str, dict[str, Any]], carrier: str) -> list[float]:
    values = []
    for base in rows:
        target_values = []
        for target in rows[base]["target_results"].values():
            pairs = target["carriers"][carrier]["pairs"]
            value = carrier_restoration(
                native_o=float(target["native"]["O"]["D"]),
                native_c=float(target["native"]["C"]["D"]),
                donor_o_into_c=float(pairs["semantic_O_into_C"]["score"]["D"]),
                donor_c_into_o=float(pairs["semantic_C_into_O"]["score"]["D"]),
            )["BCR"]
            target_values.append(value)
        values.append(float(np.mean(target_values)))
    return values


def main() -> None:
    config = read_json(OUT / "config/stage3c5_config.json")
    scopes = read_json(OUT / "config/tpre_layer_scopes.json")["scopes"]
    primary = read_jsonl(OUT / "cohort/primary_manifest.jsonl")
    validation = read_jsonl(OUT / "cohort/validation_manifest.jsonl")
    phase_a = result_map(OUT / "raw/phase_a")
    phase_b = result_map(OUT / "raw/phase_b")
    gated = result_map(OUT / "raw/phase_b_gated_r")
    controls = result_map(OUT / "raw/controls")
    expected = set(config["primary_base_problem_ids"])
    phase_a_stats = read_json(OUT / "phase_a_tpre_layer/tpre_layer_statistics.json")
    handoff_stats = read_json(OUT / "phase_b_handoff/handoff_statistics.json")
    gated_stats = read_json(OUT / "phase_b_handoff/gated_r_statistics.json")
    control_stats = read_json(OUT / "controls/target_specificity_statistics.json")
    acceptance = read_json(OUT / "summaries/stage3c5_acceptance.json")

    p4_losses = []
    p5_losses = []
    tpre_exact = True
    direct_mechanics = True
    for base, row in phase_a.items():
        p4_target = []
        p5_target = []
        for target in row["target_results"].values():
            native = float(target["native_A0"]["D"])
            p4_target.append(native - float(target["arms"]["P4"]["D"]))
            p5_target.append(native - float(target["arms"]["P5"]["D"]))
            tpre_exact &= int(target["t_pre_generated_index"]) == int(target["t_star_generated_index"]) - 1
            for score in target["arms"].values():
                for audits in score["candidate_audits"].values():
                    direct_mechanics &= all(
                        float(audit["query_max_abs_delta"]) == 0.0
                        and float(audit["key_max_abs_delta"]) == 0.0
                        and float(audit["value_max_abs_delta"]) == 0.0
                        and float(audit["attention_max_abs_delta"]) == 0.0
                        and float(audit["outside_window_max_abs_delta"]) == 0.0
                        and bool(audit["downstream_recomputation_allowed"])
                        for audit in audits
                    )
        p4_losses.append(float(np.mean(p4_target)))
        p5_losses.append(float(np.mean(p5_target)))

    carrier_medians = {
        carrier: float(np.median(base_carrier_values(phase_b, carrier)))
        for carrier in ("R_last1", "Q", "h_pre")
    }
    gated_medians = {
        carrier: float(np.median(base_carrier_values(gated, carrier)))
        for carrier in ("R_last2", "R_last4")
    }
    carrier_mechanics = True
    self_exact = True
    sham_complete = True
    for row in phase_b.values():
        visual = set(row["token_groups"]["V"])
        for target in row["target_results"].values():
            carrier_mechanics &= target["Q_positions"] == row["token_groups"]["Q"]
            carrier_mechanics &= not bool(set(target["Q_positions"]) & visual)
            carrier_mechanics &= target["R_positions"]["R_last1"] == [int(target["t_star_absolute_position"]) - 1]
            for carrier in ("R_last1", "Q", "h_pre"):
                pairs = target["carriers"][carrier]["pairs"]
                sham_complete &= set(pairs) == {
                    "self_O", "self_C", "semantic_O_into_C", "semantic_C_into_O",
                    "sham_Osham_into_O", "sham_O_into_Osham", "sham_Csham_into_C", "sham_C_into_Csham",
                }
                for self_name in ("self_O", "self_C"):
                    pair = pairs[self_name]
                    recipient = pair["recipient"]
                    self_exact &= pair["score"]["original_candidate"]["token_log_probabilities"] == target["native"][recipient]["original_candidate"]["token_log_probabilities"]
                    self_exact &= pair["score"]["counterfactual_candidate"]["token_log_probabilities"] == target["native"][recipient]["counterfactual_candidate"]["token_log_probabilities"]
                for pair in pairs.values():
                    score = pair["score"]
                    carrier_mechanics &= bool(score["finite"]) and not bool(score["visual_kv_patched"])
                    if carrier != "h_pre":
                        for audits in score["patch_audits"].values():
                            for audit in audits:
                                if audit["layer_selected"]:
                                    carrier_mechanics &= int(audit["visual_kv_entries_replaced"]) == 0
                                    carrier_mechanics &= not bool(audit["current_query_kv_replaced"])
                                    carrier_mechanics &= int(audit["queries_before_threshold_modified"]) == 0
                                    carrier_mechanics &= float(audit["nonselected_key_max_abs_delta"]) == 0.0
                                    carrier_mechanics &= float(audit["nonselected_value_max_abs_delta"]) == 0.0

    t_loss, m_loss, i_loss = [], [], []
    control_reproduction = True
    phase_a_by_base = {row["base_problem_id"]: row for row in read_jsonl(OUT / "phase_a_tpre_layer/per_problem_tpre_scope_results.jsonl")}
    for base, row in controls.items():
        aggregate = {source: [] for source in ("T", "M", "I")}
        for target_id, target in row["target_results"].items():
            native = float(target["native_A0"]["D"])
            for source in aggregate:
                aggregate[source].append(native - float(target["arms"][f"{source}_tpre"]["D"]))
            control_reproduction &= close(aggregate["T"][-1], phase_a_by_base[base]["targets"][target_id]["loss_by_scope"]["P4"])
        t_loss.append(float(np.mean(aggregate["T"])))
        m_loss.append(float(np.mean(aggregate["M"])))
        i_loss.append(float(np.mean(aggregate["I"])))

    required = [
        OUT / "analysis/necessary_window_analysis.json", OUT / "analysis/carrier_comparison.json",
        OUT / "analysis/target_heterogeneity.json", OUT / "analysis/handoff_classification.json",
        OUT / "secondary/retrieval_phenotype_overlap.json", OUT / "secondary/continuity_analysis.json",
        OUT / "summaries/stage3c5_summary.md", OUT / "summaries/next_stage_recommendation.md",
    ]
    resources = [read_json(path) for path in OUT.glob("raw/*/shard_*/resource_summary.json")]
    checks = [
        ("source_config_hash_exact", config["source_stage3c4_config_sha256"] == sha256(ROOT / config["source_stage3c4_config"])),
        ("exact_7_24_disjoint_split", len(validation) == 7 and len(primary) == 24 and not ({row["base_problem_id"] for row in validation} & {row["base_problem_id"] for row in primary})),
        ("no_primary_exclusions", read_jsonl(OUT / "cohort/exclusions.jsonl") == []),
        ("frozen_scopes_exact", scopes == frozen_tpre_layer_scopes(language_layers=36)),
        ("all_four_primary_raw_families_complete", all(set(rows) == expected for rows in (phase_a, phase_b, gated, controls))),
        ("tpre_indices_exact", tpre_exact),
        ("phase_a_direct_mechanics_valid", direct_mechanics),
        ("phase_a_validation_pass", read_json(OUT / "audit/phase_a_validation_summary.json")["status"] == "PASS"),
        ("phase_b_validation_pass", read_json(OUT / "audit/phase_b_validation_summary.json")["status"] == "PASS"),
        ("stage3c4_baselines_reproduce_exactly", read_json(OUT / "phase_a_tpre_layer/baseline_reproduction.json")["all_exact"]),
        ("P4_P5_metrics_recomputed", close(np.median(p4_losses), phase_a_stats["base_aggregated"]["P4"]["loss_summary"]["median"]) and close(np.median(p5_losses), phase_a_stats["base_aggregated"]["P5"]["loss_summary"]["median"])),
        ("carrier_metrics_recomputed", all(close(carrier_medians[name], handoff_stats["carriers"][name]["BCR"]["median"]) for name in carrier_medians)),
        ("gated_R_metrics_recomputed", all(close(gated_medians[name], gated_stats["carriers"][name]["BCR"]["median"]) for name in gated_medians)),
        ("carrier_patch_mechanics_valid", carrier_mechanics),
        ("self_patches_token_exact", self_exact),
        ("all_sham_pairs_present", sham_complete),
        ("controls_recomputed_and_reproduce", control_reproduction and close(np.median(t_loss), control_stats["median_loss"]["T"]) and close(np.median(m_loss), control_stats["median_loss"]["M"]) and close(np.median(i_loss), control_stats["median_loss"]["I"])),
        ("required_analysis_and_reports_exist", all(path.is_file() for path in required)),
        ("all_13_figures_valid", len(list((OUT / "analysis/figures").glob("*.png"))) == 13 and all(path.stat().st_size > 1000 for path in (OUT / "analysis/figures").glob("*.png"))),
        ("stop_boundary_and_single_recommendation", acceptance["all_criteria_pass"] and not acceptance["sink_manipulated"] and not acceptance["stage4_started"] and acceptance["recommendation"] == "GO — Current-Residual Mechanism" and all("A5000" in row["gpu_name"] for row in resources)),
    ]
    result = {
        "status": "PASS" if all(value for _, value in checks) else "FAIL",
        "checks": [{"id": index + 1, "name": name, "pass": bool(value)} for index, (name, value) in enumerate(checks)],
        "checks_passed": sum(bool(value) for _, value in checks), "checks_total": len(checks),
        "recomputed": {
            "P4_median_loss": float(np.median(p4_losses)), "P5_median_loss": float(np.median(p5_losses)),
            "carrier_BCR_medians": carrier_medians, "gated_R_BCR_medians": gated_medians,
            "control_median_losses": {"T": float(np.median(t_loss)), "M": float(np.median(m_loss)), "I": float(np.median(i_loss))},
        },
        "raw_counts": {"phase_a": len(phase_a), "phase_b": len(phase_b), "gated_r": len(gated), "controls": len(controls)},
        "maximum_peak_allocated_bytes": max(int(row["peak_allocated_bytes"]) for row in resources),
    }
    path = OUT / "audit/artifact_validation.json"
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
