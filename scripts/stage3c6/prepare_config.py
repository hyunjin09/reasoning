#!/usr/bin/env python3
"""Freeze Stage 3C.6 configuration and the inherited 7/24 cohort split."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c6"
SOURCE = ROOT / "outputs/stage3c5"


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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    destination = OUT / "config/stage3c6_config.json"
    if destination.exists():
        raise FileExistsError(f"Frozen Stage 3C.6 config already exists: {destination}")
    source_config_path = SOURCE / "config/stage3c5_config.json"
    source_config = read_json(source_config_path)
    plan_path = ROOT / "plan/stage3c6_plan.md"
    frozen_at = datetime.now(timezone.utc).isoformat()
    primary = read_jsonl(SOURCE / "cohort/primary_manifest.jsonl")
    validation = read_jsonl(SOURCE / "cohort/validation_manifest.jsonl")
    primary_ids = [str(row["base_problem_id"]) for row in primary]
    validation_ids = [str(row["base_problem_id"]) for row in validation]
    if len(primary_ids) != 24 or len(validation_ids) != 7 or set(primary_ids) & set(validation_ids):
        raise RuntimeError("Stage 3C.6 requires the exact disjoint Stage 3C.5 7/24 split")
    for role, rows in (("primary", primary), ("validation", validation)):
        for row in rows:
            row["stage3c6_cohort_role"] = role
            row["stage3c6_reused_without_reselection"] = True
    targets = read_json(SOURCE / "config/frozen_targets.json")
    config = {
        "created_at": frozen_at,
        "source_plan": "plan/stage3c6_plan.md",
        "source_plan_sha256": sha256(plan_path),
        "source_stage3c5_config": "outputs/stage3c5/config/stage3c5_config.json",
        "source_stage3c5_config_sha256": sha256(source_config_path),
        "model": source_config["model"],
        "model_checkpoint": source_config["model_checkpoint"],
        "dataset_root": source_config["dataset_root"],
        "seed": int(source_config["seed"]),
        "architecture_expected": source_config["architecture_expected"],
        "residual_width_expected": 2560,
        "targets": source_config["targets"],
        "validation_base_problem_ids": validation_ids,
        "primary_base_problem_ids": primary_ids,
        "validation_base_count": 7,
        "primary_base_count": 24,
        "semantic_conditions": ["O", "C"],
        "sign_alignment": {"O": 1, "C": -1},
        "suppression_scope": {"query": "t_pre=t*-1", "layers": list(range(16, 36)), "heads": list(range(32)), "source": "T", "gain": 0.0},
        "hpre_scan_layers": list(range(36)),
        "boundary_scan": ["h_pre", "h_post_attn", "h_post_block"],
        "optional_dose_enabled_if_gated": True,
        "optional_sham_enabled": False,
        "gpu": source_config["gpu"],
        "selection_used_attention": False,
        "sink_manipulated": False,
        "token_type_carrier_scan": False,
        "stage4_authorized": False,
    }
    write_json(destination, config)
    write_json(OUT / "config/frozen_targets.json", {
        "frozen_at": frozen_at,
        "source": "outputs/stage3c5/config/frozen_targets.json",
        "source_sha256": sha256(SOURCE / "config/frozen_targets.json"),
        **{key: value for key, value in targets.items() if key != "frozen_at"},
    })
    write_json(OUT / "config/suppression_definition.json", {
        "frozen_at": frozen_at,
        "source_implementation": "code/visual_reasoning/stage3c4/runtime.py:SourceContributionWindowPatch",
        "recipient_deficit": config["suppression_scope"],
        "semantics": "FP32 removal of target-ROI alphaV contribution after Attention and before W_O at t_pre only",
        "direct_qkv_modified": False,
        "attention_probabilities_modified": False,
        "downstream_recomputation": True,
    })
    write_json(OUT / "config/residual_boundaries.json", {
        "frozen_at": frozen_at,
        "broad_scan_boundary": "h_pre",
        "broad_scan_layers": list(range(36)),
        "gated_boundaries": ["h_pre", "h_post_attn", "h_post_block"],
        "current_position_only": True,
        "past_token_kv_donor_patch": False,
        "visual_kv_donor_patch": False,
        "candidate_region_rule": "Among contiguous four-layer windows containing an adjacent pair of Holm-significant positive layers, maximize the positive adjacent-layer median unnormalized-gain slope; earliest start breaks ties.",
        "candidate_region_width": 4,
    })
    write_json(OUT / "config/primary_family.json", {
        "frozen_at": frozen_at,
        "frozen_before_scoring": True,
        "primary_unit": "base_problem_id",
        "condition_reporting": "O and C separately, then sign-aligned arithmetic mean within base",
        "primary_readout": "unnormalized rescue gain G=D_rescue-D_supp after semantic sign alignment",
        "descriptive_readout": "unclipped RR=G/(D_native-D_supp)",
        "phase_a": {"families": {"target_a": 36, "target_b": 36}, "multiplicity": "Holm separately within each target's fixed 36-layer family"},
        "robust_layer": {"minimum_positive_fraction": 0.75, "bootstrap_mean_ci_lower_exclusive": 0.0, "holm_adjusted_p_max_exclusive": 0.05},
        "thresholds": {"first_20": 0.20, "first_50": 0.50, "first_80": 0.80},
        "broad_outcome_rules": {
            "R4_transient": "a robust peak has median RR>=0.20 and layer-35 median RR is both <0.20 and <50% of the peak",
            "R1_early": "otherwise first_20 is in layers 0--11",
            "R2_mid_late": "otherwise first_20 is in layers 12--27",
            "R3_late_only": "otherwise first_20 is in layers 28--35",
            "R5_none": "no robust first_20 crossing"
        },
        "phase_b_gate": "at least one robust h_pre layer with median RR>=0.20, separately per target",
        "phase_b": {"window_width": 4, "boundaries": ["h_pre", "h_post_attn", "h_post_block"], "rescue_tests_per_gated_target": 12, "rescue_multiplicity": "Holm separately within each gated target's fixed layer-by-boundary family", "transition_tests_per_gated_target": 8, "transition_multiplicity": "secondary Holm family across four Attention and four MLP increments per target"},
        "dose_lambdas": [0.0, 0.25, 0.5, 0.75, 1.0],
        "recommendation_rule": {
            "strong_residual": "at least one target has a robust first_50 crossing",
            "broad_residual": "a strong target has at least eight robust layers with median RR>=0.50",
            "GO_Residual_Feature_Subspace": "strong and broad residual rescue",
            "GO_Token_Type_Carrier_Atlas": "strong but not broad residual rescue, with prior token-cache effects remaining weak",
            "GO_Prior_Cache_Two_Query": "no strong rescue or transient rescue",
            "GO_Attention_Sink": "not selected while a more fundamental residual/cache ambiguity remains"
        },
        "bootstrap_seed": 20260904,
        "bootstrap_resamples": 10000,
    })
    write_jsonl(OUT / "cohort/primary_manifest.jsonl", primary)
    write_jsonl(OUT / "cohort/validation_manifest.jsonl", validation)
    write_jsonl(OUT / "cohort/exclusions.jsonl", [])
    for directory in (
        "audit", "phase_a_hpre_scan", "phase_b_boundary", "phase_c_optional_dose",
        "controls", "secondary", "analysis/figures", "summaries", "raw",
    ):
        (OUT / directory).mkdir(parents=True, exist_ok=True)
    print(json.dumps({"status": "frozen", "primary": len(primary), "validation": len(validation), "path": str(destination)}, indent=2))


if __name__ == "__main__":
    main()
