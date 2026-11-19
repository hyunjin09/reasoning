#!/usr/bin/env python3
"""Independently validate Stage 3C.6 raw artifacts, metrics, and stop boundary."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import torch

from visual_reasoning.stage3c6.protocol import threshold_crossings


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c6"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def result_paths(root: Path) -> list[Path]:
    return sorted(root.glob("shard_*/examples/*/result.json"))


def iter_results(root: Path) -> Iterator[tuple[Path, dict[str, Any]]]:
    for path in result_paths(root):
        yield path, read_json(path)


def close(left: float, right: float, tolerance: float = 1e-10) -> bool:
    return abs(float(left) - float(right)) <= tolerance


def main() -> None:
    config = read_json(OUT / "config/stage3c6_config.json")
    prior = read_json(ROOT / config["source_stage3c5_config"])
    primary = read_jsonl(OUT / "cohort/primary_manifest.jsonl")
    validation = read_jsonl(OUT / "cohort/validation_manifest.jsonl")
    expected = set(config["primary_base_problem_ids"])
    expected_validation = set(config["validation_base_problem_ids"])
    layers = set(range(36))
    phase_a_paths = result_paths(OUT / "raw/phase_a")
    phase_a_bases = {path.parent.name for path in phase_a_paths}
    phase_a_mechanics = True
    current_only = True
    caches_native = True
    self_exact = True
    conditions_exact = True
    tpre_exact = True
    all_36 = True
    tensor_layout = True
    for path, row in iter_results(OUT / "raw/phase_a"):
        base = str(row["base_problem_id"])
        conditions_exact &= bool(row["condition_prompt_ids_exact"] and row["condition_image_grids_exact"])
        caches_native &= not bool(row["past_token_kv_donor_patched"] or row["visual_kv_donor_patched"])
        tensor_path = path.parent / "hpre_states.pt"
        if not tensor_path.is_file():
            tensor_layout = False
        else:
            tensors = torch.load(tensor_path, map_location="cpu", weights_only=True)
            tensor_layout &= len(tensors) == 576 and all(
                list(value.shape) == [1, int(config["residual_width_expected"])]
                and value.dtype == torch.float32
                and bool(torch.isfinite(value).all())
                for value in tensors.values()
            )
            del tensors
        for target in row["target_results"].values():
            tpre_exact &= int(target["t_pre_generated_index"]) == int(target["t_star_generated_index"]) - 1
            for source in target["conditions"].values():
                all_36 &= set(map(int, source["rescue_by_layer"])) == layers
                for rescue_row in source["rescue_by_layer"].values():
                    self_exact &= bool(rescue_row["self_native_exact"] and rescue_row["self_suppressed_exact"])
                    rescue = rescue_row["rescue"]
                    current_only &= bool(rescue["current_position_only"] and rescue["boundary_patch_audits_valid"])
                    caches_native &= not bool(rescue["past_token_kv_donor_patched"] or rescue["visual_kv_donor_patched"])
                    for audits in rescue["boundary_patch_audits"].values():
                        current_only &= len(audits) == 1 and int(audits[0]["noncurrent_positions_changed"]) == 0
                    for audits in rescue["suppression_audits"].values():
                        phase_a_mechanics &= len(audits) == 20
                        for audit in audits:
                            phase_a_mechanics &= bool(
                                audit["selected_heads"] == list(range(32))
                                and float(audit["query_max_abs_delta"]) == 0.0
                                and float(audit["key_max_abs_delta"]) == 0.0
                                and float(audit["value_max_abs_delta"]) == 0.0
                                and float(audit["attention_max_abs_delta"]) == 0.0
                                and float(audit["outside_window_max_abs_delta"]) == 0.0
                            )

    reproduction = read_json(OUT / "audit/suppression_reproduction.json")
    validation_a = read_json(OUT / "audit/phase_a_validation_summary.json")
    past_cache = read_json(OUT / "audit/past_cache_invariance.json")
    boundary_equivalence = read_json(OUT / "audit/boundary_equivalence.json")
    crossings = read_json(OUT / "phase_a_hpre_scan/threshold_crossings.json")
    regions = read_json(OUT / "phase_a_hpre_scan/candidate_region_freeze.json")
    per_a = read_jsonl(OUT / "phase_a_hpre_scan/per_problem_layer_rescue.jsonl")
    statistics_exact = True
    thresholds_exact = True
    for target in ("target_a", "target_b"):
        stats = read_json(OUT / f"phase_a_hpre_scan/{target}_layer_statistics.json")
        for row in stats["sign_aligned_layers"]:
            layer = str(row["layer"])
            values = [item["targets"][target]["sign_aligned"]["layers"][layer]["rescue_gain"] for item in per_a]
            ratios = [item["targets"][target]["sign_aligned"]["layers"][layer]["rescue_ratio"] for item in per_a]
            statistics_exact &= close(np.median(values), row["median_gain"]) and close(np.median(ratios), row["median_RR"])
        recomputed_crossings = threshold_crossings(stats["sign_aligned_layers"])
        thresholds_exact &= all(recomputed_crossings[key] == crossings[target][key] for key in ("first_20", "first_50", "first_80"))

    active = {target for target, row in regions["targets"].items() if row["run_phase_b"]}
    phase_b_paths = result_paths(OUT / "raw/phase_b_boundary")
    phase_b_bases = {path.parent.name for path in phase_b_paths}
    phase_b_target_gate = True
    phase_b_mechanics = True
    for _, row in iter_results(OUT / "raw/phase_b_boundary"):
        phase_b_target_gate &= set(row["target_results"]) == active
        phase_b_mechanics &= bool(row["current_position_only"] and not row["past_token_kv_donor_patched"] and not row["visual_kv_donor_patched"])
        for target_id, target in row["target_results"].items():
            region = regions["targets"][target_id]["candidate_region"]["layers"]
            expected_cells = {f"L{layer}_{boundary}" for layer in region for boundary in ("h_pre", "h_post_attn", "h_post_block")}
            for source in target["conditions"].values():
                phase_b_mechanics &= set(source["scans"]) == expected_cells
                phase_b_mechanics &= all(
                    bool(value["self_native_exact"] and value["self_suppressed_exact"])
                    and bool(value["rescue"]["current_position_only"])
                    and not bool(value["rescue"]["past_token_kv_donor_patched"] or value["rescue"]["visual_kv_donor_patched"])
                    for value in source["scans"].values()
                )
    validation_b = read_json(OUT / "audit/phase_b_validation_summary.json")
    boundary = read_json(OUT / "phase_b_boundary/boundary_statistics.json")
    dose = read_json(OUT / "phase_c_optional_dose/dose_statistics.json")
    controls = read_json(OUT / "controls/control_statistics.json")
    dose_bases = {path.parent.name for path in result_paths(OUT / "raw/phase_c_dose")}
    control_bases = {path.parent.name for path in result_paths(OUT / "raw/controls")}
    followups_valid = bool(
        set(boundary["targets"]) == active
        and set(dose["targets"]) == active
        and set(controls["targets"]) == active
        and all(row["lambda_zero_exact_suppressed"] for row in dose["targets"].values())
        and read_jsonl(OUT / "controls/optional_sham_rescue.jsonl") == []
    )

    required = [
        OUT / "analysis/suppression_deficit_analysis.json",
        OUT / "analysis/residual_rescue_analysis.json",
        OUT / "analysis/target_heterogeneity.json",
        OUT / "analysis/current_residual_classification.json",
        OUT / "secondary/stage3c5_semantic_patch_comparison.json",
        OUT / "secondary/retrieval_phenotype_overlap.json",
        OUT / "summaries/stage3c6_summary.md",
        OUT / "summaries/next_stage_recommendation.md",
    ]
    acceptance = read_json(OUT / "summaries/stage3c6_acceptance.json")
    classification = read_json(OUT / "analysis/current_residual_classification.json")
    resources = [read_json(path) for path in OUT.glob("raw/*/shard_*/resource_summary.json")]
    recommendation_text = (OUT / "summaries/next_stage_recommendation.md").read_text(encoding="utf-8")
    checks = [
        ("source_configs_and_targets_exact", config["source_stage3c5_config_sha256"] == sha256(ROOT / config["source_stage3c5_config"]) and config["targets"] == prior["targets"]),
        ("exact_7_24_disjoint_frozen_cohorts", len(validation) == 7 and len(primary) == 24 and {str(row["base_problem_id"]) for row in validation} == expected_validation and {str(row["base_problem_id"]) for row in primary} == expected and not expected_validation & expected),
        ("no_primary_exclusions", read_jsonl(OUT / "cohort/exclusions.jsonl") == []),
        ("P4_suppression_definition_exact", config["suppression_scope"]["query"] == "t_pre=t*-1" and config["suppression_scope"]["layers"] == list(range(16, 36)) and config["suppression_scope"]["heads"] == list(range(32)) and config["suppression_scope"]["source"] == "T" and config["suppression_scope"]["gain"] == 0.0),
        ("phase_a_primary_complete", phase_a_bases == expected and len(phase_a_paths) == 24),
        ("phase_a_validation_pass", validation_a["status"] == "PASS" and validation_a["validation_base_count"] == 7),
        ("stage3c5_P4_reproduced_exactly", reproduction["all_exact"] and reproduction["N_target_base_cells"] == 48),
        ("native_suppressed_semantic_conditions_matched", conditions_exact and tpre_exact),
        ("all_36_hpre_layers_scanned", all_36),
        ("suppression_and_current_rescue_mechanics_valid", phase_a_mechanics and current_only and caches_native),
        ("primary_residual_tensor_layout_valid", tensor_layout),
        ("past_cache_and_visual_cache_recipient_native", past_cache["status"] == "PASS" and past_cache["all_past_post_rope_KV_exact"] and past_cache["maximum_absolute_delta"] == 0.0 and past_cache["visual_positions_included_in_exact_comparison"]),
        ("boundary_equivalence_and_self_patches_exact", boundary_equivalence["status"] == "PASS" and boundary_equivalence["maximum_absolute_delta"] == 0.0 and self_exact),
        ("phase_a_metrics_and_thresholds_recomputed", statistics_exact and thresholds_exact),
        ("phase_b_gate_and_frozen_regions_respected", phase_b_bases == expected and phase_b_target_gate and regions["frozen_before_within_block_scoring"] and not regions["selection_used_boundary_outcomes"]),
        ("phase_b_validation_and_mechanics_pass", validation_b["status"] == "PASS" and phase_b_mechanics),
        ("dose_and_target_specificity_controls_complete", dose_bases == expected and control_bases == expected and followups_valid),
        ("required_analyses_reports_and_14_figures_exist", all(path.is_file() for path in required) and len(list((OUT / "analysis/figures").glob("*.png"))) == 14 and all(path.stat().st_size > 1000 for path in (OUT / "analysis/figures").glob("*.png"))),
        ("A5000_compute_and_primary_unit_valid", resources and all("A5000" in row["gpu_name"] for row in resources) and all(read_json(path)["primary_unit"] == "base_problem_id" for path in (OUT / "analysis/suppression_deficit_analysis.json", OUT / "analysis/residual_rescue_analysis.json", OUT / "analysis/target_heterogeneity.json"))),
        ("stop_boundary_and_single_recommendation", acceptance["all_criteria_pass"] and len(acceptance["criteria"]) == 20 and classification["recommendation"] in recommendation_text and recommendation_text.count("## Recommendation") == 1 and not acceptance["token_type_scan_started"] and not acceptance["sink_manipulated"] and not acceptance["stage4_started"]),
    ]
    result = {
        "status": "PASS" if all(value for _, value in checks) else "FAIL",
        "checks": [{"id": index + 1, "name": name, "pass": bool(value)} for index, (name, value) in enumerate(checks)],
        "checks_passed": sum(bool(value) for _, value in checks),
        "checks_total": len(checks),
        "raw_counts": {"phase_a": len(phase_a_paths), "phase_b_boundary": len(phase_b_paths), "dose": len(result_paths(OUT / "raw/phase_c_dose")), "controls": len(result_paths(OUT / "raw/controls"))},
        "active_phase_b_targets": sorted(active),
        "maximum_peak_allocated_bytes": max(int(row["peak_allocated_bytes"]) for row in resources),
    }
    path = OUT / "audit/artifact_validation.json"
    path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
