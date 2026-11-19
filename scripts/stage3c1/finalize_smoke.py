#!/usr/bin/env python3
"""Aggregate Stage 3C.1 smoke artifacts and enforce the full-run gate."""

from __future__ import annotations

import glob
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c1"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main() -> None:
    config = json.loads((OUT / "config/stage3c1_config.json").read_text())
    paths = sorted(glob.glob(str(OUT / "smoke_v3/shard_*/examples/*/result.json")))
    if len(paths) != 2:
        raise RuntimeError(f"Expected two v3 smoke results, found {len(paths)}")
    rows: list[dict[str, Any]] = [json.loads(Path(path).read_text()) for path in paths]
    audits = [
        {"base_problem_id": row["base_problem_id"], "condition": condition, **audit}
        for row in rows
        for condition, layer_rows in row["audits"].items()
        for audit in layer_rows.values()
    ]
    reconstruction = {
        "smoke_base_problem_ids": [row["base_problem_id"] for row in rows],
        "implementation": "installed full-shape Qwen3-VL eager Attention independently recomputed with the same Q/K/V, scale, full causal mask, BF16 cast, and matrix shapes",
        "frozen_reconstruction_tolerance": config["reconstruction_tolerance"],
        "bf16_source_mass_tolerance": config["source_mass_tolerance"],
        "maximum_probability_absolute_error": max(a["eager_reconstruction"]["maximum_probability_absolute_error"] for a in audits),
        "maximum_head_output_absolute_error": max(a["eager_reconstruction"]["maximum_head_output_absolute_error"] for a in audits),
        "maximum_installed_bf16_attention_sum_absolute_error": max(a["eager_reconstruction"]["maximum_attention_sum_absolute_error"] for a in audits),
        "maximum_source_mass_absolute_error": max(a["maximum_source_mass_absolute_error"] for a in audits),
        "maximum_alpha_v_partition_reconstruction_absolute_error": max(a["maximum_alpha_v_reconstruction_absolute_error"] for a in audits),
        "maximum_wo_partition_reconstruction_absolute_error": max(a["maximum_wo_reconstruction_absolute_error"] for a in audits),
        "all_values_finite": all(a["all_values_finite"] for a in audits),
    }
    reconstruction["probability_reconstruction_passed"] = (
        reconstruction["maximum_probability_absolute_error"] <= config["reconstruction_tolerance"]
    )
    reconstruction["head_output_reconstruction_passed"] = (
        reconstruction["maximum_head_output_absolute_error"] <= config["reconstruction_tolerance"]
    )
    reconstruction["source_mass_accounting_passed"] = (
        reconstruction["maximum_source_mass_absolute_error"] <= config["source_mass_tolerance"]
    )
    reconstruction["alpha_v_reconstruction_passed"] = (
        reconstruction["maximum_alpha_v_partition_reconstruction_absolute_error"] <= 1e-5
    )
    reconstruction["wo_reconstruction_passed"] = (
        reconstruction["maximum_wo_partition_reconstruction_absolute_error"] <= 1e-5
    )
    instrumentation = {
        "smoke_base_problem_ids": [row["base_problem_id"] for row in rows],
        "checks": [row["instrumentation_faithfulness"] for row in rows],
        "maximum_logit_absolute_error": max(row["instrumentation_faithfulness"]["maximum_logit_absolute_error"] for row in rows),
        "tolerance": config["instrumentation_logit_tolerance"],
        "all_passed": all(row["instrumentation_faithfulness"]["passed"] for row in rows),
        "deterministic_repeat_checks": [row["deterministic_repeat"] for row in rows],
        "all_repeats_bitwise_exact": all(row["deterministic_repeat"]["exact"] for row in rows),
    }
    mapping = audits[0]["query_to_kv_group"]
    gqa = {
        "logical_query_heads": 32,
        "kv_heads": 8,
        "query_heads_per_kv_group": 4,
        "logical_query_head_to_kv_head": mapping,
        "mapping_rule": "kv_head = logical_query_head // 4",
        "target_a": {"query_heads": [11, 6, 15, 12], "kv_heads": [mapping[h] for h in [11, 6, 15, 12]]},
        "target_b": {"query_heads": [16, 0, 3, 6], "kv_heads": [mapping[h] for h in [16, 0, 3, 6]]},
        "passed": mapping == [head // 4 for head in range(32)],
    }
    tensor_layout = {
        "axis_order": {
            "post_rope_query": ["batch", "logical_query_head", "sequence", "head_dimension"],
            "post_rope_key": ["batch", "kv_head", "sequence", "head_dimension"],
            "value": ["batch", "kv_head", "sequence", "head_dimension"],
            "attention_probability": ["batch", "logical_query_head", "query_position", "source_position"],
            "pre_wo_output": ["batch", "sequence", "logical_query_head", "head_dimension"],
            "wo_weight": ["residual_dimension", "logical_query_head_times_head_dimension"],
        },
        "observed_shapes": {
            f"base_{a['base_problem_id']}_{a['condition']}_layer_{a['layer_index']}": a["tensor_shapes"]
            for a in audits if a["condition"] == "O"
        },
        "raw_npz_granularity": audits[0]["raw_tensor_granularity"],
        "raw_npz_arrays": ["logical_heads", "offsets_from_E_d", "absolute_query_positions", "valid_source_lengths", "q_norm", "k_norm", "value_norm", "cosine", "raw_dot", "scaled_logits", "final_logits", "attention"],
    }
    gate_checks = {
        "eager_probability_reconstruction": reconstruction["probability_reconstruction_passed"],
        "eager_head_output_reconstruction": reconstruction["head_output_reconstruction_passed"],
        "source_mass_accounting": reconstruction["source_mass_accounting_passed"],
        "alpha_v_reconstruction": reconstruction["alpha_v_reconstruction_passed"],
        "wo_reconstruction": reconstruction["wo_reconstruction_passed"],
        "instrumentation_faithfulness": instrumentation["all_passed"],
        "deterministic_repeat": instrumentation["all_repeats_bitwise_exact"],
        "all_finite": reconstruction["all_values_finite"],
        "gqa_mapping": gqa["passed"],
        "condition_layout": all(row["condition_layout_exact"] for row in rows),
    }
    reconstruction["full_run_gate_checks"] = gate_checks
    reconstruction["full_run_gate_passed"] = all(gate_checks.values())
    write_json(OUT / "audit/reconstruction_check.json", reconstruction)
    write_json(OUT / "audit/instrumentation_faithfulness.json", instrumentation)
    write_json(OUT / "audit/gqa_mapping.json", gqa)
    write_json(OUT / "audit/tensor_layout.json", tensor_layout)
    print(json.dumps({"full_run_gate_passed": reconstruction["full_run_gate_passed"], **gate_checks}, indent=2))
    if not reconstruction["full_run_gate_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
