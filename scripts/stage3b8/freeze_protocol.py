#!/usr/bin/env python3
"""Freeze Stage 3B.8 targets, protected cohorts, and discovery rules."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b8"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    config_dir = OUT / "config"
    if config_dir.exists() and any(config_dir.iterdir()):
        raise FileExistsError(f"Stage 3B.8 protocol is already frozen: {config_dir}")
    ensure_directory(config_dir)
    plan = ROOT / "plan/stage3b8_plan.md"
    prior_config_path = ROOT / "outputs/stage3b7r/config/stage3b7r_config.json"
    prior_targets_path = ROOT / "outputs/stage3b7r/config/phase_b_targets.json"
    primary_path = ROOT / "outputs/stage3b6/config/primary_manifest.jsonl"
    old_validation_path = ROOT / "outputs/stage3b7/config/validation_manifest.jsonl"
    recent_validation_path = ROOT / "outputs/stage3b7r/validation_cohort/fresh_validation_manifest.jsonl"
    batch3_freeze_path = ROOT / "outputs/stage3b7r/config/batch3_edit_validation_freeze.json"
    batch3_manifest_path = ROOT / "outputs/stage3b7r/validation_cohort/edit_validation_batch3_v3/manual_valid_generation_manifest.jsonl"

    prior_config = read_json(prior_config_path)
    targets = read_json(prior_targets_path)["targets"]
    if [(row["coordinate"], row["layer_index"], row["heads"]) for row in targets] != [
        ("Ed", 29, [11, 6, 15, 12]),
        ("Ed_minus_1", 28, [16, 0, 3, 6]),
    ]:
        raise RuntimeError("Stage 3B.7-R frozen targets changed")
    primary = read_jsonl(primary_path)
    old_validation = read_jsonl(old_validation_path)
    recent_validation = read_jsonl(recent_validation_path)
    if len(primary) != 37 or len(old_validation) != 8 or len(recent_validation) != 13:
        raise RuntimeError("Protected cohort sizes changed")
    protected = {
        str(row["base_problem_id"])
        for rows in (primary, old_validation, recent_validation)
        for row in rows
    }
    batch3 = read_json(batch3_freeze_path)
    eligible = {str(value) for value in batch3["eligible_bases"]}
    candidate_rows = [
        row for row in read_jsonl(batch3_manifest_path)
        if str(row["base_problem_id"]) in eligible
    ]
    if len(candidate_rows) != 11 or len({str(row["base_problem_id"]) for row in candidate_rows}) != 11:
        raise RuntimeError("Expected exactly 11 unused manually edit-valid batch-3 candidates")
    if protected & {str(row["base_problem_id"]) for row in candidate_rows}:
        raise RuntimeError("Initial Stage 3B.8 candidates overlap a protected cohort")

    frozen_at = datetime.now(timezone.utc).isoformat()
    architecture = read_json(ROOT / "outputs/stage3b6/config/stage3b6_config.json")["architecture_expected"]
    protocol = {
        "frozen_at": frozen_at,
        "source_plan": str(plan.relative_to(ROOT)),
        "source_plan_sha256": sha256(plan),
        "source_stage3b7r_config": str(prior_config_path.relative_to(ROOT)),
        "source_stage3b7r_config_sha256": sha256(prior_config_path),
        "model": prior_config["model"],
        "model_checkpoint": prior_config["model_checkpoint"],
        "locked_generation_protocol": prior_config["locked_generation_protocol"],
        "architecture_expected": architecture,
        "targets": targets,
        "representation": {
            "name": "ROI-derived causal Value-content vector",
            "formula": "concat_h sum_{j in target ROI} alpha_recipient[h,j] * V_image[gqa(h),j]",
            "surface": "selected logical query-head outputs before shared W_O",
            "head_order": "exact frozen target head-list order",
            "dimension": len(targets[0]["heads"]) * int(architecture["head_dimension"]),
            "symmetric_delta": "0.5*((z(O;O)-z(O;C))+(z(C;O)-z(C;C)))",
            "semantic_direction": "counterfactual_to_original",
        },
        "dose_response": {
            "lambdas": [0.0, 0.25, 0.5, 0.75, 1.0],
            "endpoint_tolerance": 1e-6,
            "phase_b_gate": {
                "mechanical_endpoints_valid": True,
                "cohort_median_nondecreasing_tolerance": 0.05,
                "within_base_spearman_median_minimum": 0.50,
                "lambda1_semantic_effect_positive": True,
                "lambda1_semantic_exceeds_sham": True,
            },
        },
        "subspace": {
            "fit": "uncentered SVD of one symmetric semantic delta row per discovery base",
            "uncentered_reason": "causal deltas have a meaningful zero origin",
            "candidate_ranks": [1, 2, 4, 8, 16],
            "rank_rule": "smallest k with median projected/full >=0.80 and median complement/full <=0.30",
            "fallback": "maximize median projected/full minus median complement/full; prefer smaller rank on ties",
            "sham_delta": "0.5*((z(O;O)-z(O;O_sham))+(z(C;C)-z(C;C_sham)))",
            "random_subspaces": 100,
            "random_seed": 1234,
        },
        "selection_blinding": {
            "attention_used": False,
            "stage3b8_outcomes_used": False,
            "fit_quality_used": False,
        },
    }
    target_payload = {
        "frozen_at": frozen_at,
        "source": str(prior_targets_path.relative_to(ROOT)),
        "source_sha256": sha256(prior_targets_path),
        "targets": targets,
    }
    family = {
        "frozen_at": frozen_at,
        "primary_statistical_unit": "base_problem_id",
        "primary_confirmation_base_count": 37,
        "targets": [row["target_id"] for row in targets],
        "primary_conditions": ["native", "full_V", "learned_parallel", "orthogonal_complement"],
        "random_same_rank_subspace_count": 100,
        "attention_secondary_only": True,
    }
    split = {
        "frozen_at": frozen_at,
        "primary_confirmation": {
            "count": 37,
            "base_problem_ids": [str(row["base_problem_id"]) for row in primary],
            "manifest": str(primary_path.relative_to(ROOT)),
            "used_for_fit_or_rank_selection": False,
        },
        "protected_diagnostic": {
            "old_stage3b7_count": 8,
            "old_stage3b7_base_problem_ids": [str(row["base_problem_id"]) for row in old_validation],
            "stage3b7r_count": 13,
            "stage3b7r_base_problem_ids": [str(row["base_problem_id"]) for row in recent_validation],
        },
        "discovery": {
            "target_size": [16, 20],
            "minimum": 16,
            "initial_outcome_blind_edit_valid_candidates": [str(row["base_problem_id"]) for row in candidate_rows],
            "final_selection_rule": "ascending base_problem_id among completed-correct, edit-valid, strict-Ed-valid cases; freeze first 20 or all if 16-19",
        },
        "all_current_sets_disjoint": True,
    }
    write_json(config_dir / "stage3b8_config.json", protocol)
    write_json(config_dir / "primary_targets.json", target_payload)
    write_json(config_dir / "primary_family.json", family)
    write_json(config_dir / "discovery_confirmation_split.json", split)
    ensure_directory(OUT / "discovery_cohort")
    write_jsonl(OUT / "discovery_cohort/initial_generation_manifest.jsonl", candidate_rows)
    print(json.dumps({"primary": 37, "protected": len(protected), "initial_discovery_candidates": 11}, indent=2))


if __name__ == "__main__":
    main()
