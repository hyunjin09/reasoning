#!/usr/bin/env python3
"""Freeze Stage 3C.5 cohorts, interventions, gates, and test family."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage3c5.protocol import frozen_tpre_layer_scopes


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c5"
SOURCE = ROOT / "outputs/stage3c4"


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
    created = datetime.now(timezone.utc).isoformat()
    source_config_path = SOURCE / "config/stage3c4_config.json"
    source_config = read_json(source_config_path)
    validation = read_jsonl(SOURCE / "cohort/validation_manifest.jsonl")
    primary = read_jsonl(SOURCE / "cohort/primary_manifest.jsonl")
    validation_ids = [str(row["base_problem_id"]) for row in validation]
    primary_ids = [str(row["base_problem_id"]) for row in primary]
    if len(validation_ids) != 7 or len(primary_ids) != 24 or set(validation_ids) & set(primary_ids):
        raise RuntimeError("Stage 3C.5 requires the exact disjoint Stage 3C.4 7/24 split")

    validation_rows = [
        {**row, "stage3c5_cohort_role": "validation", "reused_without_reselection": True}
        for row in validation
    ]
    primary_rows = [
        {**row, "stage3c5_cohort_role": "primary", "reused_without_reselection": True}
        for row in primary
    ]
    write_jsonl(OUT / "cohort/validation_manifest.jsonl", validation_rows)
    write_jsonl(OUT / "cohort/primary_manifest.jsonl", primary_rows)
    write_jsonl(OUT / "cohort/exclusions.jsonl", [])

    scopes = frozen_tpre_layer_scopes(language_layers=36)
    write_json(OUT / "config/tpre_layer_scopes.json", {
        "frozen_at": created,
        "frozen_before_phase_a_scoring": True,
        "query": "t_pre=t*-1 only",
        "all_heads": list(range(32)),
        "scopes": scopes,
        "descriptions": {
            "P0": "W4 only, layers 28-29",
            "P1": "W5 only, layers 32-33",
            "P2": "W4+W5, layers 28-33",
            "P3": "late layers 24-35",
            "P4": "mid+late layers 16-35",
            "P5": "all language layers 0-35",
        },
        "posthoc_scopes_allowed": False,
    })
    write_json(OUT / "config/carrier_family.json", {
        "frozen_at": created,
        "frozen_before_phase_a_scoring": True,
        "initial_carriers": ["R_last1", "Q", "h_pre"],
        "gated_recent_reasoning": ["R_last2", "R_last4"],
        "R_representation": "post-RoPE K/V cache entries for exact prior generated-token positions at the Phase-A-selected frozen layer family",
        "Q_representation": "post-RoPE K/V cache entries for the unique exact Stage-3B.0 question-content token span at the same frozen layer family",
        "h_pre_representation": "raw current-position decoder residual input at t* before the frozen historical target layer",
        "layer_family_selection_rule": "smallest P0--P5 scope with >=80% of P5 median loss, >=75% positive bases, and Holm p<0.05; otherwise P5",
        "h_pre_layers": {key: int(value["layer_index"]) for key, value in source_config["targets"].items()},
        "patch_components": ["post-RoPE K", "V"],
        "patch_pairs": [
            "O<-O", "C<-C", "C<-O", "O<-C",
            "O<-O_sham", "O_sham<-O", "C<-C_sham", "C_sham<-C",
        ],
        "recipient_image_and_unpatched_states_remain_native": True,
        "visual_kv_patched": False,
        "current_query_kv_patched": False,
        "exact_token_and_cache_position_alignment_required": True,
        "R_expansion_decision_rule": {
            "multiplicity": "Holm correction across R_last2-minus-R_last1 and R_last4-minus-R_last1 secondary contrasts",
            "minimum_positive_fraction": 0.75,
            "minimum_median_CRR_gain": 0.05,
            "holm_adjusted_p_max_exclusive": 0.05,
        },
    })
    tests = [
        "P0_vs_native", "P1_vs_native", "P2_vs_native", "P3_vs_native",
        "P4_vs_native", "P5_vs_native", "tpre_only_vs_current_only",
        "joint_vs_current_only", "monotonic_layer_scope_trend",
        "R_last1_semantic_restoration", "Q_semantic_restoration",
        "h_pre_semantic_restoration", "R_last1_vs_Q", "R_last1_vs_h_pre",
        "Q_vs_h_pre",
    ]
    write_json(OUT / "config/primary_family.json", {
        "frozen_at": created,
        "frozen_before_scoring": True,
        "primary_unit": "base_problem_id",
        "tests": tests,
        "test_count": len(tests),
        "secondary_gated_tests": ["R_last2_semantic_restoration", "R_last4_semantic_restoration"],
        "multiplicity": "Holm correction within the 15-test primary family; gated R_last2/R_last4 reported as secondary",
        "target_aggregation": "arithmetic mean of Target A and Target B within each base",
        "primary_readouts": {
            "phase_a": "unnormalized evidence loss D_native-D_intervention",
            "phase_b": "unnormalized bidirectional carrier restoration BCR",
        },
        "normalization": "retention/recovery are descriptive and unclipped",
        "bootstrap_seed": 20260904,
        "bootstrap_resamples": 10000,
        "phase_b_gate": {
            "historical_T0_to_T1_median_added_loss": 1.3069,
            "minimum_fraction": 0.20,
            "minimum_median_loss": 0.26138,
            "minimum_positive_fraction": 0.75,
            "holm_adjusted_p_max_exclusive": 0.05,
        },
        "carrier_robustness": {
            "minimum_positive_fraction": 0.75,
            "holm_adjusted_p_max_exclusive": 0.05,
            "minimum_median_CRR": 0.20,
            "minimum_semantic_to_sham_ratio": 2.0,
        },
        "r_expansion_gate": {
            "R_last1_holm_significant": True,
            "minimum_positive_fraction": 0.75,
            "maximum_median_CRR_exclusive": 0.80,
        },
    })
    targets = source_config["targets"]
    write_json(OUT / "config/frozen_targets.json", {
        "frozen_at": created,
        "source": "outputs/stage3c4/config/frozen_targets.json",
        "source_sha256": sha256(SOURCE / "config/frozen_targets.json"),
        "targets": targets,
        "t_star": "state_R.generated_index for each frozen target/base",
        "t_pre": "t_star-1 exactly",
        "target_roi": "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl:absolute_source_groups.V_target",
        "mention_roi": "outputs/stage3c2/annotations/mention_roi_annotations.jsonl:mention_absolute_source_positions",
        "irrelevant_roi": "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl:absolute_source_groups.V_irrelevant",
        "selection_used_attention": False,
    })
    config = {
        "created_at": created,
        "source_plan": "plan/stage3c5_plan.md",
        "source_plan_sha256": sha256(ROOT / "plan/stage3c5_plan.md"),
        "source_stage3c4_config": "outputs/stage3c4/config/stage3c4_config.json",
        "source_stage3c4_config_sha256": sha256(source_config_path),
        "model": source_config["model"],
        "model_checkpoint": source_config["model_checkpoint"],
        "dataset_root": source_config["dataset_root"],
        "seed": int(source_config["seed"]),
        "targets": targets,
        "architecture_expected": source_config["architecture_expected"],
        "validation_base_problem_ids": validation_ids,
        "primary_base_problem_ids": primary_ids,
        "validation_base_count": len(validation_ids),
        "primary_base_count": len(primary_ids),
        "phase_a_scopes": list(scopes),
        "phase_a_baselines": {
            "A0": "native",
            "A1": "all layers at t*",
            "A2": "all layers at t_pre only",
            "A3": "all layers at [t_pre,t*]",
        },
        "control_sources": ["M", "I"],
        "carrier_family": ["R_last1", "Q", "h_pre"],
        "gated_carriers": ["R_last2", "R_last4"],
        "gpu": {"required_class": "A5000", "gpus": 2, "slurm_job_id": "106936", "tmux_session": "8"},
        "selection_used_attention": False,
        "sink_manipulated": False,
        "stage4_authorized": False,
    }
    write_json(OUT / "config/stage3c5_config.json", config)
    write_json(OUT / "audit/contribution_definition.json", {
        "source": "code/visual_reasoning/stage3c4/runtime.py:SourceContributionWindowPatch",
        "definition": "c_T(t,l,h)=sum_j_in_T alpha(t,l,h,j)V(l,h,j), removed after Attention and before W_O",
        "partition_dtype": "float32",
        "tpre_only": True,
        "qkv_directly_modified": False,
        "attention_directly_modified": False,
        "non_target_source_directly_modified": False,
        "downstream_recomputation_allowed": True,
    })
    print(json.dumps({"validation": len(validation_rows), "primary": len(primary_rows), "scopes": list(scopes)}, indent=2))


if __name__ == "__main__":
    main()
