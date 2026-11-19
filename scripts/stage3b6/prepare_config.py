#!/usr/bin/env python3
"""Freeze Stage 3B.6 targets, cohorts, thresholds, source groups, and shards."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage3b6.protocol import build_frozen_cells


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b6"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def balanced_shards(rows: list[dict[str, Any]], count: int) -> list[list[dict[str, Any]]]:
    shards = [[] for _ in range(count)]
    for index, row in enumerate(rows):
        shards[index % count].append(row)
    return shards


def main() -> None:
    plan = ROOT / "plan/stage3b6_plan.md"
    stage3b5_config_path = ROOT / "outputs/stage3b5/config/stage3b5_config.json"
    decision_path = ROOT / "outputs/stage3b5/analysis/decision_rule_evaluation.json"
    validation_path = ROOT / "outputs/stage3b5/validation/validation_manifest.jsonl"
    primary_path = ROOT / "outputs/stage3b5/config/cohort_manifest.jsonl"
    token_groups_path = ROOT / "outputs/stage3b0/layout_audit/token_group_definition.json"
    for path in (
        plan,
        stage3b5_config_path,
        decision_path,
        validation_path,
        primary_path,
        token_groups_path,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)

    if (OUT / "config/stage3b6_config.json").exists():
        raise FileExistsError("Stage 3B.6 config is already frozen")
    stage3b5 = read_json(stage3b5_config_path)
    decision = read_json(decision_path)
    cells = build_frozen_cells(
        target_by_window=stage3b5["target_by_window"],
        qualifying=decision["qualifying_cells"],
    )
    discovery = read_jsonl(validation_path)
    primary = read_jsonl(primary_path)
    if len(discovery) != 8 or len(primary) != 37:
        raise RuntimeError("Frozen discovery/primary split must be exactly 8/37 bases")
    if {str(row["base_problem_id"]) for row in discovery} & {
        str(row["base_problem_id"]) for row in primary
    }:
        raise RuntimeError("Discovery and primary bases must be disjoint")

    frozen_at = datetime.now(timezone.utc).isoformat()
    config = {
        "frozen_at": frozen_at,
        "source_plan": "plan/stage3b6_plan.md",
        "source_plan_sha256": sha256(plan),
        "source_stage3b5_config": "outputs/stage3b5/config/stage3b5_config.json",
        "source_stage3b5_config_sha256": sha256(stage3b5_config_path),
        "source_stage3b5_decision": "outputs/stage3b5/analysis/decision_rule_evaluation.json",
        "source_stage3b5_decision_sha256": sha256(decision_path),
        "model": stage3b5["model"],
        "model_checkpoint": stage3b5["model_checkpoint"],
        "transformers_version": stage3b5["transformers_version"],
        "required_gpu_class": "A5000",
        "attention_implementation": "validated eager local override",
        "seed": int(stage3b5["seed"]),
        "architecture_expected": {
            "language_layers": 36,
            "logical_query_heads": 32,
            "kv_heads": 8,
            "query_heads_per_kv_group": 4,
            "head_dimension": 128,
        },
        "head_intervention": {
            "approach": "Preferred A — hybrid per-query-head recomputation",
            "recipient_query": "retained",
            "source_state": "post-RoPE K/V at frozen preceding source positions",
            "splice_surface": "selected logical query-head outputs before W_O at one current position",
            "downstream": "W_O, residual, MLP, and later layers recompute naturally",
            "selection_used_attention": False,
        },
        "conditions": ["O", "O_sham", "C", "C_sham"],
        "candidate_continuations": ["original_candidate", "counterfactual_candidate"],
        "frozen_cells": cells,
        "discovery": {
            "base_count": 8,
            "all_query_heads": list(range(32)),
            "ranking_metric": "median unnormalized BHR, descending; head index tie-break",
            "robust_rule": {
                "median_BHR": "> 0",
                "bidirectionally_consistent_bases": ">= 7/8",
                "median_sham_to_semantic_ratio": "<= 0.25",
                "all_self_controls_exact": True,
                "median_HRR": ">= 0.10",
            },
            "cumulative_sets": ["Top_1", "Top_2", "Top_4", "Top_8", "All_robust"],
        },
        "confirmation": {
            "base_count": 37,
            "statistical_unit": "base_problem_id",
            "one_sided_test": "Wilcoxon BHR > 0",
            "multiple_testing": "Holm within the prospectively frozen confirmatory units across the three qualifying cells",
            "robust_rule": {
                "holm_adjusted_p": "< 0.05",
                "median_bootstrap_CI_low": "> 0",
                "bidirectional_fraction": ">= 0.70",
                "median_sham_to_semantic_ratio": "< 0.25",
                "all_self_controls_exact": True,
                "median_HRR": ">= 0.25",
            },
        },
        "source_path_gate": {
            "required_confirmed_unit_count": 1,
            "path_target_per_cell": "strongest confirmed single head; otherwise smallest confirmed Top-k set",
            "groups": ["all", "V", "P", "R"],
            "P_definition": "Stage 3B.0 P_post_image eligible nonvisual prompt positions",
            "R_definition": "generated reasoning positions strictly before the recipient current query token",
            "current_token_excluded": True,
            "ROI_analysis": False,
        },
        "secondary_only": [
            "Stage 3B.1 cutoff triangulation",
            "raw/selected-head attention comparison after causal results freeze",
        ],
        "prohibited": [
            "ROI-specific path patching",
            "K-only/V-only/pattern-value decomposition",
            "MLP feature/neuron analysis",
            "Q/R long-term lifecycle tracing",
            "multi-evidence refresh",
            "failure analysis",
        ],
    }
    split = {
        "frozen_at": frozen_at,
        "discovery_source": "outputs/stage3b5/validation/validation_manifest.jsonl",
        "primary_source": "outputs/stage3b5/config/cohort_manifest.jsonl",
        "discovery_base_problem_ids": [str(row["base_problem_id"]) for row in discovery],
        "primary_base_problem_ids": [str(row["base_problem_id"]) for row in primary],
        "disjoint": True,
        "selection_used_attention": False,
    }
    qualifying = {
        "frozen_at": frozen_at,
        "source": "outputs/stage3b5/analysis/decision_rule_evaluation.json",
        "cells": cells,
        "layer_search_reopened": False,
    }
    ensure_directory(OUT / "config/shards/discovery")
    for directory in (
        "audit", "discovery", "validation", "scoring", "analysis/figures", "summaries"
    ):
        ensure_directory(OUT / directory)
    write_json(OUT / "config/stage3b6_config.json", config)
    write_json(OUT / "config/qualifying_cells.json", qualifying)
    write_json(OUT / "config/discovery_primary_split.json", split)
    write_jsonl(OUT / "config/discovery_manifest.jsonl", discovery)
    write_jsonl(OUT / "config/primary_manifest.jsonl", primary)
    write_json(
        OUT / "audit/source_token_groups.json",
        {
            **read_json(token_groups_path),
            "stage3b6_primary_groups": {
                "V": "all visual-token positions",
                "P": "Stage 3B.0 P_post_image",
                "R": "all generated positions strictly before the current query token",
                "all": "V union P union R",
            },
            "current_query_position_excluded": True,
            "selection_used_attention": False,
            "frozen_at": frozen_at,
        },
    )
    shards = balanced_shards(discovery, 2)
    for index, rows in enumerate(shards):
        write_jsonl(OUT / f"config/shards/discovery/discovery_{index:02d}.jsonl", rows)
    write_json(
        OUT / "config/sharding_summary.json",
        {
            "discovery": [
                {"shard": index, "base_count": len(rows)}
                for index, rows in enumerate(shards)
            ],
            "primary_shards_deferred_until_candidate_freeze": True,
            "requested_execution": "existing Slurm allocation in tmux session 8, A5000 x2",
        },
    )


if __name__ == "__main__":
    main()
