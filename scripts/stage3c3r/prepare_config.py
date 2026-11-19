#!/usr/bin/env python3
"""Freeze Stage 3C.3-R cohorts, interventions, gate, and test family."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c3r"
SOURCE = ROOT / "outputs/stage3c3"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, allow_nan=False) + "\n" for row in rows), encoding="utf-8"
    )


def main() -> None:
    created = datetime.now(timezone.utc).isoformat()
    source_config_path = SOURCE / "config/stage3c3_config.json"
    source_config = read_json(source_config_path)
    validation_source = SOURCE / "cohort/validation_manifest.jsonl"
    primary_source = SOURCE / "cohort/primary_manifest.jsonl"
    validation = read_jsonl(validation_source)
    primary = read_jsonl(primary_source)
    validation_ids = [str(row["base_problem_id"]) for row in validation]
    primary_ids = [str(row["base_problem_id"]) for row in primary]
    if len(validation_ids) != 7 or len(primary_ids) != 24:
        raise RuntimeError("Stage 3C.3-R requires the exact 7/24 Stage 3C.3 split")
    if set(validation_ids) & set(primary_ids):
        raise RuntimeError("Validation and primary cohorts must be disjoint")

    targets = source_config["targets"]
    if targets != {
        "target_a": {
            "coordinate": "E_d",
            "layer_index": 29,
            "causal_heads": [11, 6, 15, 12],
            "noncausal_heads": [0, 1, 2, 3],
        },
        "target_b": {
            "coordinate": "E_d-1",
            "layer_index": 28,
            "causal_heads": [16, 0, 3, 6],
            "noncausal_heads": [1, 2, 4, 5],
        },
    }:
        raise RuntimeError("Frozen Stage 3C.3 target definitions changed unexpectedly")

    reused_validation = [
        {**row, "stage3c3r_cohort_role": "validation", "reused_without_reselection": True}
        for row in validation
    ]
    reused_primary = [
        {**row, "stage3c3r_cohort_role": "primary", "reused_without_reselection": True}
        for row in primary
    ]
    write_jsonl(OUT / "cohort/validation_manifest.jsonl", reused_validation)
    write_jsonl(OUT / "cohort/primary_manifest.jsonl", reused_primary)
    write_jsonl(OUT / "cohort/exclusions.jsonl", [])

    frozen_targets = {
        "frozen_at": created,
        "source": str(source_config_path.relative_to(ROOT)),
        "source_sha256": sha256(source_config_path),
        "targets": targets,
        "target_roi_definition": {
            "per_base_source": "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl:absolute_source_groups.V_target",
            "source_sha256": sha256(ROOT / "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl"),
            "selection_used_attention": False,
        },
        "mention_roi_definition": {
            "per_base_source": "outputs/stage3c2/annotations/mention_roi_annotations.jsonl:mention_absolute_source_positions",
            "source_sha256": sha256(ROOT / "outputs/stage3c2/annotations/mention_roi_annotations.jsonl"),
            "selection_used_attention": False,
        },
        "irrelevant_roi_definition": {
            "per_base_source": "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl:absolute_source_groups.V_irrelevant",
            "selection_used_attention": False,
        },
    }
    write_json(OUT / "config/frozen_targets.json", frozen_targets)

    lambda_grid = {
        "frozen_at": created,
        "phase_a_target": [1.0, 0.75, 0.5, 0.25, 0.1, 0.0],
        "phase_a_controls": [1.0, 0.5, 0.0],
        "phase_b_nested_scopes": [1.0, 0.5, 0.0],
        "optional_strengthening": {"values": [1.25, 1.5], "run": False},
        "tuned_on_validation_effect_magnitude": False,
    }
    write_json(OUT / "config/lambda_grid.json", lambda_grid)

    nested = {
        "frozen_at": created,
        "frozen_before_phase_a_scoring": True,
        "logical_query_head_count": 32,
        "allowed_layers": [28, 29],
        "scopes": {
            "R0": {
                "description": "selected causal heads at the frozen target's current layer",
                "target_a": [{"layer_index": 29, "heads": [11, 6, 15, 12]}],
                "target_b": [{"layer_index": 28, "heads": [16, 0, 3, 6]}],
            },
            "R1": {
                "description": "all logical query heads at the frozen target's current layer",
                "target_a": [{"layer_index": 29, "heads": list(range(32))}],
                "target_b": [{"layer_index": 28, "heads": list(range(32))}],
            },
            "R2": {
                "description": "the target's frozen causal head identities at both W4 layers",
                "target_a": [
                    {"layer_index": 28, "heads": [11, 6, 15, 12]},
                    {"layer_index": 29, "heads": [11, 6, 15, 12]},
                ],
                "target_b": [
                    {"layer_index": 28, "heads": [16, 0, 3, 6]},
                    {"layer_index": 29, "heads": [16, 0, 3, 6]},
                ],
            },
            "R3": {
                "description": "all logical query heads at both W4 layers",
                "target_a": [
                    {"layer_index": 28, "heads": list(range(32))},
                    {"layer_index": 29, "heads": list(range(32))},
                ],
                "target_b": [
                    {"layer_index": 28, "heads": list(range(32))},
                    {"layer_index": 29, "heads": list(range(32))},
                ],
            },
        },
        "r2_head_identity_rule": "reuse each target's frozen logical causal-head IDs independently at layers 28 and 29",
        "scope_expansion_after_outcomes_allowed": False,
    }
    write_json(OUT / "config/nested_scope_family.json", nested)

    phase_a = [
        "T lambda=.75 vs 1 evidence change",
        "T lambda=.50 vs 1 evidence change",
        "T lambda=.25 vs 1 evidence change",
        "T lambda=.10 vs 1 evidence change",
        "T lambda=0 vs 1 evidence change",
        "monotonic trend",
        "T vs M attenuation specificity",
        "T vs I attenuation specificity",
        "causal-head vs noncausal-head attenuation specificity",
        "Stage 3C.3 query-patch operating-point consistency with dose curve",
    ]
    phase_b = [
        "R1 lambda=0 vs R0 lambda=0",
        "R2 lambda=0 vs R0 lambda=0",
        "R3 lambda=0 vs R0 lambda=0",
    ]
    primary_family = {
        "frozen_at": created,
        "primary_unit": "base_problem_id",
        "phase_a_tests": phase_a,
        "phase_b_gated_tests": phase_b,
        "target_specific_hypothesis_count": 2 * (len(phase_a) + len(phase_b)),
        "multiplicity": "Holm correction across 26 target-specific hypotheses; gated-unrun Phase-B p-values are 1.0",
        "primary_readout": "unnormalized evidence preference D = L_o - L_c",
        "retained_evidence": "descriptive E(lambda)/E(1), unclipped",
        "phase_b_gate": {
            "per_target": "E(0)/E(1), unclipped",
            "per_base": "arithmetic mean of target_a and target_b retained evidence",
            "pass_if": "median >= 0.50 OR fraction >= 0.80 is at least 0.40",
        },
        "bootstrap_seed": 20260904,
        "bootstrap_resamples": 10000,
    }
    write_json(OUT / "config/primary_family.json", primary_family)

    config = {
        "created_at": created,
        "source_plan": "plan/stage3c3r_plan.md",
        "source_plan_sha256": sha256(ROOT / "plan/stage3c3r_plan.md"),
        "source_stage3c3_config": str(source_config_path.relative_to(ROOT)),
        "source_stage3c3_config_sha256": sha256(source_config_path),
        "model": source_config["model"],
        "model_checkpoint": source_config["model_checkpoint"],
        "dataset_root": source_config["dataset_root"],
        "seed": source_config["seed"],
        "validation_base_count": len(validation_ids),
        "primary_base_count": len(primary_ids),
        "validation_base_problem_ids": validation_ids,
        "primary_base_problem_ids": primary_ids,
        "condition": "O",
        "targets": targets,
        "architecture_expected": source_config["architecture_expected"],
        "mechanical_bf16_tolerance": 1e-6,
        "mechanical_tolerance_frozen_after_validation_smoke": True,
        "mechanical_tolerance_basis": "FP32 contribution partition arithmetic; lambda=1 and isolation endpoints remain exact",
        "phase_a_target_source": "T",
        "phase_a_controls": ["M", "I", "noncausal_T"],
        "phase_b_is_gated": True,
        "optional_evidence_direction_projection": {
            "run": False,
            "reason": "not required to distinguish magnitude saturation from nested W4 redundancy",
        },
        "gpu": source_config["gpu"],
        "selection_used_attention": False,
        "sink_manipulated": False,
        "query_or_hpre_intervention_added": False,
        "broader_than_w4_allowed": False,
        "stage3c4_authorized": False,
        "stage4_authorized": False,
    }
    write_json(OUT / "config/stage3c3r_config.json", config)
    print(json.dumps({
        "validation": validation_ids,
        "primary": primary_ids,
        "frozen_targets": targets,
        "phase_a_lambda": lambda_grid["phase_a_target"],
        "nested_scopes": list(nested["scopes"]),
    }, indent=2))


if __name__ == "__main__":
    main()
