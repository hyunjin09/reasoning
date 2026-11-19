#!/usr/bin/env python3
"""Freeze Stage 3B.5 cohorts, state boundaries, tests, gates, and decisions."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text
from visual_reasoning.stage3b5.boundaries import BOUNDARIES, EXPECTED_DOWNSTREAM
from visual_reasoning.stage3b5.protocol import build_primary_family


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b5"
STAGE3B4 = ROOT / "outputs/stage3b4"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    for path in (
        OUT / "config", OUT / "audit", OUT / "validation", OUT / "scoring",
        OUT / "analysis/figures", OUT / "summaries",
    ):
        ensure_directory(path)

    source_config = read_json(STAGE3B4 / "config/stage3b4_config.json")
    source_run = read_json(STAGE3B4 / "scoring/raw/primary_00/config.json")["run_signature"]
    target_by_window = source_config["target_by_window"]
    family = build_primary_family(target_by_window)
    cohort = read_jsonl(STAGE3B4 / "config/cohort_manifest.jsonl")
    validation = read_jsonl(STAGE3B4 / "validation/validation_manifest.jsonl")
    primary_numeric = [row for row in cohort if "structural" not in str(row["edit_tier"])]
    structural = [row for row in cohort if "structural" in str(row["edit_tier"])]
    validation_bases = {str(row["base_problem_id"]) for row in validation}
    primary_bases = {str(row["base_problem_id"]) for row in primary_numeric}
    if len(validation) != 8 or len(primary_numeric) != 37 or len(structural) != 4:
        raise RuntimeError("Stage 3B.5 requires the frozen 8 validation / 37 paired / 4 structural split")
    if validation_bases & primary_bases:
        raise RuntimeError("Stage 3B.5 validation and primary bases must remain disjoint")

    model_source = next(
        ROOT.glob(".venv/lib/python*/site-packages/transformers/models/qwen3_vl/modeling_qwen3_vl.py")
    )
    plan_path = ROOT / "plan/stage3b5_plan.md"
    frozen_at = datetime.now(timezone.utc).isoformat()
    config = {
        "frozen_at": frozen_at,
        "source_plan": "plan/stage3b5_plan.md",
        "source_plan_sha256": sha256(plan_path),
        "source_stage3b4_config": "outputs/stage3b4/config/stage3b4_config.json",
        "source_stage3b4_config_sha256": sha256(STAGE3B4 / "config/stage3b4_config.json"),
        "model_checkpoint": source_run["model_checkpoint"],
        "model": source_config["model"],
        "transformers_version": importlib.metadata.version("transformers"),
        "required_gpu_class": "A5000",
        "attention_implementation": "validated eager local override",
        "seed": int(source_config["seed"]),
        "coordinates": list(source_config["coordinates"]),
        "target_by_window": target_by_window,
        "boundaries": list(BOUNDARIES),
        "boundary_definitions": {
            "h_pre": "raw decoder-layer input before input RMSNorm",
            "pre_attn_norm": "input RMSNorm output presented to self-attention; raw residual remains recipient",
            "h_post_attn": "raw residual after attention addition and before post-attention RMSNorm",
            "pre_mlp_norm": "post-attention RMSNorm output presented to MLP; raw residual remains recipient",
            "h_post_block": "raw residual after MLP addition / decoder-layer output",
        },
        "expected_downstream_recompute": {
            key: list(value) for key, value in EXPECTED_DOWNSTREAM.items()
        },
        "conditions": ["O", "O_sham", "C", "C_sham"],
        "intervention_scope": "one frozen current evidence-decision position at one target layer/boundary",
        "two_layer_entry_recompute": {
            "implementation": "first-layer h_pre patch followed by natural recomputation through both retained layers",
            "physical_arm_is_primary_family_alias": True,
            "alias_count": 4,
            "duplicate_inference_test_added": False,
        },
        "primary_metric": "unnormalized paired semantic BMR",
        "normalized_metric": "BMR / abs(matching Stage 3B.2 all-layer BRI); unclipped",
        "primary_family_size": 40,
        "multiple_testing": "Holm across exactly 40 coordinate/window/layer-role/boundary tests",
        "validation": {
            "base_count": 8,
            "baseline_reproduction": "token-log-probability exact against Stage 3B.4 on A5000",
            "capture_audits": "all five states at every requested layer exactly once; exact post-attention residual sum",
            "patch_audits": "only current position replaced; exact source state; expected downstream modules execute in order",
            "self_restoration": "exact O and C score reproduction for every boundary arm",
            "finite_outputs": "all candidate scores finite",
            "determinism_anchor_base_problem_id": str(validation[0]["base_problem_id"]),
            "determinism": "repeat full anchor result with exact public output equality",
            "adjacent_interface_equivalence": "first-layer h_post_block and second-layer h_pre yield token-exact scores",
            "stage3b4_block_bridge": "second-layer h_post_block preserves a positive, source-consistent Stage 3B.4 Block tendency; exact score equality is not required because the frozen Stage 3B.4 arm patched both layer outputs",
            "full_block_gate": source_config["validation"]["full_block_gate"],
            "all_boundary_render_gate": {
                "definition": "median across bases of each base's median A_render/abs(all-layer BRI), pooled over all 40 fixed tests",
                "maximum": 0.05,
            },
        },
        "primary_inference": {
            "base_count": 37,
            "structural_manifest_only_base_count": 4,
            "one_sided_test": "Wilcoxon signed-rank BMR > 0",
            "alpha": 0.05,
            "robust_cell": {
                "holm_adjusted_p": "< 0.05",
                "median_bootstrap_CI_low": "> 0",
                "bidirectional_fraction": ">= 0.70",
                "median_render_to_semantic_ratio": "< 0.25",
                "all_self_restorations_exact": True,
            },
        },
        "decision_thresholds": {
            "minimum_category_cells": 2,
            "priority": [
                "upstream_residual_origin",
                "cross_layer_sequential",
                "attention_or_mlp_dominant_gain",
                "broader_residual_norm_redirect",
            ],
            "upstream": {
                "first_layer_h_pre_robust": True,
                "median_h_pre_to_final_block_ratio_min": 0.80,
            },
            "boundary_gain": {
                "boundary_after_state_robust": True,
                "median_gain_to_final_block_min": 0.25,
                "bootstrap_gain_CI_low": "> 0",
                "dominance_over_other_gain_in_final_block_units_min": 0.15,
            },
            "cross_layer_sequential": {
                "first_layer_h_pre_to_final_block_ratio_min": 0.70,
                "h_pre_recompute_gain_over_stage3b4_joint_in_final_block_units_min": 0.20,
                "h_pre_recompute_gain_over_second_layer_h_pre_in_final_block_units_min": 0.20,
                "bootstrap_gain_CI_low": "> 0",
                "upstream_0.80_rule_must_not_hold": True,
            },
        },
        "frozen_stage3b4_comparison": {
            "h_pre_recompute_vs": "joint",
            "h_post_attn_recompute_vs": "mlp",
            "source": "outputs/stage3b4/scoring/raw",
            "comparison_only_no_reselection": True,
        },
        "optional_readout_analysis": False,
        "optional_attention_analysis": False,
        "selection_used_attention": False,
        "prohibited": [
            "head/path localization", "ROI-specific paths", "Q/R carrier patching",
            "MLP feature/neuron analysis", "multi-evidence analysis", "failure analysis",
        ],
    }
    write_json(OUT / "config/stage3b5_config.json", config)
    write_json(OUT / "config/primary_family.json", {
        "frozen_at": frozen_at,
        "family_size": len(family),
        "correction": "Holm",
        "alpha": 0.05,
        "tests": family,
        "two_layer_entry_arms_are_aliases_not_additional_tests": True,
    })
    write_jsonl(OUT / "config/cohort_manifest.jsonl", [
        {**row, "stage3b5_role": "primary"} for row in primary_numeric
    ])
    write_jsonl(OUT / "config/structural_manifest_only.jsonl", [
        {**row, "stage3b5_role": "structural_manifest_only"} for row in structural
    ])
    write_jsonl(OUT / "validation/validation_manifest.jsonl", [
        {**row, "stage3b5_role": "validation"} for row in validation
    ])

    hook_locations = {
        "frozen_at": frozen_at,
        "transformers_version": config["transformers_version"],
        "source_file": str(model_source.relative_to(ROOT)),
        "source_sha256": sha256(model_source),
        "decoder_layer_class": "Qwen3VLTextDecoderLayer",
        "full_sequence_scoring": True,
        "use_cache": False,
        "hooks": {
            "h_pre": "decoder layer forward-pre input hidden_states",
            "pre_attn_norm": "input_layernorm forward output",
            "h_post_attn": "exact raw state after attention residual addition, implemented with an audited one-arm reconstruction of the frozen decoder forward so the MLP residual branch also receives the source state",
            "pre_mlp_norm": "post_attention_layernorm forward output",
            "h_post_block": "decoder layer forward output",
        },
        "targets": target_by_window,
        "hooks_frozen_before_validation_scores": True,
    }
    write_json(OUT / "audit/hook_locations.json", hook_locations)
    write_text(
        OUT / "audit/block_state_map.md",
        "# Stage 3B.5 Qwen3-VL block-state map\n\n"
        f"Frozen at `{frozen_at}` before validation scoring. Audited source: "
        f"`{hook_locations['source_file']}` (`transformers=={config['transformers_version']}`, "
        f"SHA-256 `{hook_locations['source_sha256']}`).\n\n"
        "The installed `Qwen3VLTextDecoderLayer` executes `h_pre -> input RMSNorm -> "
        "self-attention -> attention residual addition -> post-attention RMSNorm -> MLP -> "
        "MLP residual addition`. Stage 3B.5 captures and patches the current absolute token "
        "position only at `h_pre`, `pre_attn_norm`, `h_post_attn`, `pre_mlp_norm`, and "
        "`h_post_block`. For normalized-state arms the raw residual branch stays recipient. "
        "For `h_post_attn`, a one-arm reconstruction of the exact audited decoder forward patches "
        "the raw post-add residual directly before natural RMSNorm/MLP recomputation. This avoids "
        "both leaving the local residual branch unpatched and relying on non-bit-exact reduced-precision "
        "subtraction/addition.\n\n"
        "W4 is F28_29 (layers 28--29); W5 is F32_33 (layers 32--33). The first-layer "
        "`h_pre` arm is also the requested two-layer window-entry recompute arm, so it is "
        "reported in both analyses but not executed or tested twice.\n",
    )
    print(json.dumps({
        "validation_bases": len(validation),
        "primary_bases": len(primary_numeric),
        "structural_manifest_only": len(structural),
        "primary_tests": len(family),
        "targets": target_by_window,
    }, indent=2))


if __name__ == "__main__":
    main()
