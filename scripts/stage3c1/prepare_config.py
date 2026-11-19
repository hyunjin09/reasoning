#!/usr/bin/env python3
"""Freeze the prospective Stage 3C.1 measurement protocol."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c1"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    plan = ROOT / "plan/stage3c1_plan.md"
    manifest = ROOT / "outputs/stage3b6/config/primary_manifest.jsonl"
    annotations = ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl"
    roi_mapping = ROOT / "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl"
    checkpoint = Path(
        "/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/"
        "snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e"
    )
    targets = {
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "selection_used_stage3c1_attention": False,
        "source": "outputs/stage3b7r/config/stage3b7r_config.json",
        "targets": [
            {
                "target_id": "target_a",
                "coordinate": "E_d",
                "window": "W4",
                "layer_index": 29,
                "causal_heads": [11, 6, 15, 12],
            },
            {
                "target_id": "target_b",
                "coordinate": "E_d-1",
                "window": "W4",
                "layer_index": 28,
                "causal_heads": [16, 0, 3, 6],
            },
        ],
        "upstream_state_control": {
            "target_id": "target_a_w5_upstream",
            "coordinate": "E_d",
            "window": "W5",
            "layer_index": 32,
            "heads": [11, 6, 15, 12],
            "role": "upstream-state control only",
        },
        "secondary_w5_comparator": {
            "target_id": "target_b_w5_head10",
            "coordinate": "E_d-1",
            "window": "W5",
            "layer_index": 32,
            "heads": [10],
            "role": "secondary comparator only; no source-claim upgrade",
        },
    }
    temporal = {
        "offsets_from_E_d": [-16, -8, -4, -2, -1, 0],
        "absolute_generated_index_rule": "E_d + offset",
        "absolute_sequence_position_rule": "prompt_length + generated_index - 1",
        "missing_history_rule": "omit checkpoint when E_d + offset < 1",
        "post_divergence_checkpoints": [],
        "selection_used_stage3c1_attention": False,
    }
    controls = {
        "freeze_rule": "lowest logical query-head indices absent from each frozen causal set",
        "selection_used_stage3c1_attention": False,
        "target_a_layer29": [0, 1, 2, 3],
        "target_b_layer28": [1, 2, 4, 5],
        "matched_size": True,
    }
    sources = {
        "partition": {
            "visual": "all image placeholder positions",
            "prompt_question": "unique exact question-content span in the chat-template prompt",
            "previous_reasoning": "generated positions after prompt and strictly before active query",
            "special_other": "all remaining prompt/control positions plus active query token",
        },
        "roi_overlays": {
            "target_roi": "frozen Stage 3B.7 absolute_source_groups.V_target",
            "matched_irrelevant_roi": "frozen Stage 3B.7 absolute_source_groups.V_irrelevant",
            "visual_complement": "frozen Stage 3B.7 absolute_source_groups.V_other",
            "all_visual": "frozen Stage 3B.7 absolute_source_groups.V_all",
        },
        "sink_candidate_rules": {
            "first_prompt_token": "absolute prompt position 0",
            "template_control_and_active_query": "the exhaustive special_other source partition: all nonvisual, non-question chat-template prompt positions plus the active query token",
            "newline_formatting": "decoded token contains a newline or carriage return",
            "image_boundary_neighbor": "nonvisual prompt position immediately adjacent to the visual placeholder block",
            "active_query_token": "the current query position",
        },
        "sink_analysis_is_descriptive": True,
    }
    config = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_plan": str(plan.relative_to(ROOT)),
        "source_plan_sha256": sha256(plan),
        "model": "Qwen3-VL-4B-Thinking",
        "model_checkpoint": str(checkpoint),
        "dataset_root": "/data/dataset/MathVerse",
        "manifest": str(manifest.relative_to(ROOT)),
        "annotations": str(annotations.relative_to(ROOT)),
        "roi_mapping": str(roi_mapping.relative_to(ROOT)),
        "paired_image_root": "outputs/stage3b3_redesign/counterfactual_shams",
        "conditions": ["O", "O_sham", "C", "C_sham"],
        "base_problem_count": sum(1 for line in manifest.read_text().splitlines() if line.strip()),
        "seed": 1234,
        "architecture_expected": {
            "language_layers": 36,
            "logical_query_heads": 32,
            "kv_heads": 8,
            "query_heads_per_kv_group": 4,
            "head_dimension": 128,
        },
        "capture_heads_by_layer": {
            "28": sorted({16, 0, 3, 6, 1, 2, 4, 5}),
            "29": sorted({11, 6, 15, 12, 0, 1, 2, 3}),
            "32": sorted({11, 6, 15, 12, 10}),
        },
        "reconstruction_tolerance": 0.0,
        "instrumentation_logit_tolerance": 1e-5,
        "source_mass_tolerance": 0.005,
        "source_mass_tolerance_basis": "BF16 probabilities are summed in FP32 after the installed softmax casts to BF16; 0.005 bounds representation-rounding drift observed during the pre-cohort smoke audit",
        "deterministic_repeat_tolerance": 0.0,
        "gpu": {
            "required_class": "A5000",
            "gpus": 2,
            "slurm_job_id": "106936",
            "tmux_session": "8",
        },
        "attention_is_descriptive_not_causal": True,
        "attention_is_never_manipulated": True,
        "selection_used_stage3c1_attention": False,
    }
    for name, value in (
        ("stage3c1_config.json", config),
        ("frozen_targets.json", targets),
        ("temporal_grid.json", temporal),
        ("control_heads.json", controls),
        ("source_classes.json", sources),
    ):
        write_json(OUT / "config" / name, value)

    equations = "# Exact eager-Attention equations\n\n"
    equations += "Stage 3C.1 transparently reproduces the installed Qwen3-VL eager Attention path. "
    equations += "For residual input `h`, the module applies its installed Q/K norms after the Q/K projections, "
    equations += "then the installed multimodal RoPE to obtain the active post-RoPE `Q` and `K`; `V` is the direct V projection.\n\n"
    equations += "```text\nQ = RoPE(q_norm(W_Q h))\nK = RoPE(k_norm(W_K h))\nV = W_V h\n"
    equations += "K_rep, V_rep = repeat_kv(K, V, num_key_value_groups=4)\n"
    equations += "z_ij = (q_i dot k_j) / sqrt(128) + causal_mask_ij\n"
    equations += "alpha_i = softmax_float32(z_i), cast_to_query_dtype\n"
    equations += "o_i,h = sum_j alpha_i,h,j V_rep_h,j\n"
    equations += "Attention(h)_i = W_O concat_h(o_i,h)\n```\n\n"
    equations += "The capture returns that same projected tensor to the model. All probability, αV, and W_O checks "
    equations += "are passive reconstructions. No attention, Q, K, V, source state, or output is changed.\n"
    (OUT / "audit").mkdir(parents=True, exist_ok=True)
    (OUT / "audit/attention_equations.md").write_text(equations, encoding="utf-8")
    print(json.dumps({"prepared": True, "base_problem_count": config["base_problem_count"]}, indent=2))


if __name__ == "__main__":
    main()
