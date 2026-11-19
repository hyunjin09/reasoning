#!/usr/bin/env python3
"""Freeze Stage 3C.7 config and unchanged cohorts before scoring."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c7"
SOURCE = ROOT / "outputs/stage3c6"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    frozen_at = datetime.now(timezone.utc).isoformat()
    source_config = read_json(SOURCE / "config/stage3c6_config.json")
    targets = read_json(SOURCE / "config/frozen_targets.json")
    p4 = list(range(16, 36))
    residuals = {
        "target_a": {"layer": 33, "boundary": "h_post_attn", "downstream_cache_layers": [34, 35]},
        "target_b": {"layer": 35, "boundary": "h_pre", "downstream_cache_layers": [35]},
    }
    config = {
        "created_at": frozen_at,
        "source_plan": "plan/stage3c7_plan.md",
        "source_plan_sha256": sha256(ROOT / "plan/stage3c7_plan.md"),
        "source_stage3c6_config": "outputs/stage3c6/config/stage3c6_config.json",
        "source_stage3c6_config_sha256": sha256(SOURCE / "config/stage3c6_config.json"),
        "model": source_config["model"],
        "model_checkpoint": source_config["model_checkpoint"],
        "dataset_root": source_config["dataset_root"],
        "seed": source_config["seed"],
        "architecture_expected": source_config["architecture_expected"],
        "residual_width_expected": source_config["residual_width_expected"],
        "targets": source_config["targets"],
        "validation_base_problem_ids": source_config["validation_base_problem_ids"],
        "primary_base_problem_ids": source_config["primary_base_problem_ids"],
        "validation_base_count": 7,
        "primary_base_count": 24,
        "minimum_valid_primary_bases": 20,
        "semantic_conditions": ["O", "C"],
        "sign_alignment": {"O": 1, "C": -1},
        "suppression_scope": source_config["suppression_scope"],
        "cache_scope": {"position": "t_pre only", "layers": p4, "modes": ["K", "V", "KV"], "native_kv_heads": 8},
        "residual_boundaries": residuals,
        "phase_a_arms": ["C0_native", "C1_suppressed", "C2_K", "C3_V", "C4_KV"],
        "phase_b_arms": ["J0_suppressed", "J1_residual", "J2_full_KV", "J3_downstream_KV", "J4_joint", "J5_full_KV_plus_residual"],
        "joint_kv_decomposition_gate": "J4 substantial separately per target",
        "optional_rollouts": {"run": False, "frozen_before_scoring": True, "reason": "teacher-forced evidence preference is primary; omit optional compute/storage"},
        "gpu": {"required_class": "A5000", "gpus": 2, "allocation_source": "project scheduler and Slurm"},
        "selection_used_attention": False,
        "cache_delta_used_for_layer_selection": False,
        "sink_manipulated": False,
        "token_type_scan": False,
        "stage4_authorized": False,
    }
    write_json(OUT / "config/stage3c7_config.json", config)
    write_json(OUT / "config/frozen_targets.json", {
        "frozen_at": frozen_at,
        "source": "outputs/stage3c6/config/frozen_targets.json",
        "source_sha256": sha256(SOURCE / "config/frozen_targets.json"),
        **{key: value for key, value in targets.items() if key != "frozen_at"},
        "residual_joint_boundaries": residuals,
    })
    write_json(OUT / "config/suppression_definition.json", {
        "frozen_at": frozen_at,
        "source": "outputs/stage3c6/config/suppression_definition.json",
        "source_sha256": sha256(SOURCE / "config/suppression_definition.json"),
        "recipient_deficit": source_config["suppression_scope"],
        "exact_stage3c6_reproduction_required": True,
    })
    write_json(OUT / "config/cache_scope.json", {
        "frozen_at": frozen_at,
        "cache_object": {"token": "t_pre=t*-1", "key": "post-RoPE", "value": "projected V", "layout": "[batch,8 KV heads,1 token,128 head_dim]"},
        "full_layers": p4,
        "downstream_by_target": {key: value["downstream_cache_layers"] for key, value in residuals.items()},
        "patch_modes": ["K", "V", "KV"],
        "forbidden_positions": ["all visual prompt positions", "current query t*", "all past reasoning positions except t_pre"],
        "layer_selection_used_cache_delta": False,
    })
    write_json(OUT / "config/residual_boundaries.json", {
        "frozen_at": frozen_at,
        "source": "Stage 3C.6 only; no Stage 3C.7 outcome used",
        "targets": residuals,
    })
    write_json(OUT / "config/joint_intervention_definition.json", {
        "frozen_at": frozen_at,
        "primary_joint": "J4 residual plus downstream K+V cache",
        "target_a_order": ["P4 suppression at t_pre L16-35", "native current state at L33 h_post_attn", "native t_pre K+V consulted at L34-35 Attention"],
        "target_b_order": ["P4 suppression at t_pre L16-35", "native current state at L35 h_pre", "native tpre K+V consulted at L35 Attention"],
        "J5_interpretation": "secondary practical total rescue; upstream cache effects may be overwritten by residual transplant",
    })
    test_ids = [
        "K_gt_0", "V_gt_0", "KV_gt_0", "KV_minus_K", "KV_minus_V",
        "residual_gt_0", "downstream_cache_gt_0", "joint_gt_0",
        "joint_minus_residual", "joint_minus_downstream_cache",
        "full_cache_minus_residual", "full_cache_plus_residual_gt_0",
    ]
    write_json(OUT / "config/primary_family.json", {
        "frozen_at": frozen_at,
        "frozen_before_scoring": True,
        "primary_unit": "base_problem_id",
        "test_ids": test_ids,
        "tests_per_target": len(test_ids),
        "multiplicity": "Holm separately within each target's fixed 12-test family",
        "primary_readout": "unnormalized sign-aligned rescue gain",
        "descriptive_readout": "unclipped RR",
        "robust_effect": {"holm_p_below": 0.05, "bootstrap_mean_gain_ci_lower_above": 0.0, "minimum_positive_fraction": 0.75},
        "strong_cache": "robust full K+V rescue and median RR>=0.50",
        "approaches_kv": "robust component median gain >=80% of K+V median gain",
        "substantial_joint": "robust J4 and median RR>=0.50",
        "near_complete_joint": "robust J4 and median RR>=0.80",
        "outcome_priority": ["O3_two_query_synergy", "O2_residual_cache_complementarity", "O4_residual_dominant", "O1_prior_cache_carrier", "O5_distributed_beyond_last_token_cache_and_residual"],
        "recommendation_rules": {
            "O1": "GO — Token-Type Carrier Atlas",
            "O2_or_O3_near_complete": "GO — Token-Type Carrier Atlas",
            "O2_or_O3_not_near_complete": "GO — Broader Recent-Cache Interaction",
            "O4": "GO — Residual Feature Mechanism",
            "O5_cache_nonzero": "GO — Broader Recent-Cache Interaction",
            "O5_cache_zero": "GO — Residual Feature Mechanism",
            "attention_sink": "ineligible while cache/residual ambiguity remains",
        },
        "bootstrap_seed": 20260904,
        "bootstrap_resamples": 10000,
    })
    for name in ("primary_manifest.jsonl", "validation_manifest.jsonl", "exclusions.jsonl"):
        destination = OUT / "cohort" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SOURCE / "cohort" / name, destination)
    for directory in (
        "audit", "phase_a_cache", "phase_b_joint", "controls", "secondary",
        "analysis/figures", "summaries", "raw/validation", "raw/primary",
    ):
        (OUT / directory).mkdir(parents=True, exist_ok=True)
    (OUT / "secondary/optional_rollouts.jsonl").write_text("", encoding="utf-8")
    print(json.dumps({"status": "frozen", "validation": 7, "primary": 24, "output": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
