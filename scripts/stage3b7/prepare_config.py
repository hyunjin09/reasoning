#!/usr/bin/env python3
"""Freeze Stage 3B.7 targets, cohorts, families, gates, and execution contract."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b7"


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
    plan_path = ROOT / "plan/stage3b7_plan.md"
    stage3b6_config_path = ROOT / "outputs/stage3b6/config/stage3b6_config.json"
    source_path_stats_path = ROOT / "outputs/stage3b6/analysis/source_path_statistics.json"
    split_path = ROOT / "outputs/stage3b6/config/discovery_primary_split.json"
    primary_manifest_path = ROOT / "outputs/stage3b6/config/primary_manifest.jsonl"
    validation_manifest_path = ROOT / "outputs/stage3b6/config/discovery_manifest.jsonl"
    for path in (
        plan_path,
        stage3b6_config_path,
        source_path_stats_path,
        split_path,
        primary_manifest_path,
        validation_manifest_path,
    ):
        if not path.is_file():
            raise FileNotFoundError(path)
    if (OUT / "config/stage3b7_config.json").exists():
        raise FileExistsError("Stage 3B.7 config is already frozen")

    stage3b6 = read_json(stage3b6_config_path)
    source_stats = read_json(source_path_stats_path)
    primary = read_jsonl(primary_manifest_path)
    validation = read_jsonl(validation_manifest_path)
    split = read_json(split_path)
    if len(primary) != 37 or len(validation) != 8:
        raise RuntimeError("Stage 3B.7 requires the exact 37/8 primary-validation split")
    primary_ids = [str(row["base_problem_id"]) for row in primary]
    validation_ids = [str(row["base_problem_id"]) for row in validation]
    if primary_ids != split["primary_base_problem_ids"] or validation_ids != split[
        "discovery_base_problem_ids"
    ]:
        raise RuntimeError("Stage 3B.6 cohort order changed")
    if set(primary_ids) & set(validation_ids):
        raise RuntimeError("Primary and validation bases are not disjoint")

    categories = {
        (row["cell_id"], row["unit_id"]): row
        for row in source_stats["source_categories"]
    }
    expected = {
        ("Ed__W4", "Top_4"): [11, 6, 15, 12],
        ("Ed_minus_1__W4", "Top_2"): [16, 0],
    }
    targets = []
    frozen_cells = {row["cell_id"]: row for row in stage3b6["frozen_cells"]}
    source_targets = read_json(ROOT / "outputs/stage3b6/analysis/source_path_targets.json")
    source_lookup = {
        (row["cell_id"], row["unit_id"]): row for row in source_targets["targets"]
    }
    for (cell_id, unit_id), heads in expected.items():
        if categories[(cell_id, unit_id)]["category"] != "V-dominant":
            raise RuntimeError(f"Primary target {cell_id}/{unit_id} is no longer V-dominant")
        if source_lookup[(cell_id, unit_id)]["heads"] != heads:
            raise RuntimeError(f"Frozen heads changed for {cell_id}/{unit_id}")
        targets.append({
            **frozen_cells[cell_id],
            "unit_id": unit_id,
            "heads": heads,
            "stage3b6_median_V_PRR": categories[(cell_id, unit_id)]["median_PRR"]["V"],
            "primary": True,
        })
    exploratory = {
        **frozen_cells["Ed_minus_1__W5"],
        "unit_id": "head_10",
        "heads": [10],
        "primary": False,
        "exploratory_only": True,
        "reason": "Stage 3B.6 V PRR was high but sham/semantic exceeded the frozen limit",
    }
    frozen_at = datetime.now(timezone.utc).isoformat()
    robust_rule = {
        "holm_adjusted_one_sided_p": "< 0.05",
        "median_bootstrap_95_CI_low": "> 0",
        "bidirectional_fraction": ">= 0.70",
        "median_sham_to_semantic_ratio": "< 0.25",
        "all_self_controls_exact": True,
        "all_mechanical_controls_pass": True,
    }
    config = {
        "frozen_at": frozen_at,
        "source_plan": "plan/stage3b7_plan.md",
        "source_plan_sha256": sha256(plan_path),
        "source_stage3b6_config": "outputs/stage3b6/config/stage3b6_config.json",
        "source_stage3b6_config_sha256": sha256(stage3b6_config_path),
        "source_stage3b6_path_statistics": "outputs/stage3b6/analysis/source_path_statistics.json",
        "source_stage3b6_path_statistics_sha256": sha256(source_path_stats_path),
        "model": stage3b6["model"],
        "model_checkpoint": stage3b6["model_checkpoint"],
        "seed": int(stage3b6["seed"]),
        "required_gpu_class": "A5000",
        "execution": {
            "tmux_session": "8",
            "slurm_job_id": "106936",
            "node": "node04",
            "gpus": 2,
            "new_slurm_submission": False,
        },
        "architecture_expected": stage3b6["architecture_expected"],
        "conditions": ["O", "O_sham", "C", "C_sham"],
        "primary_targets": targets,
        "exploratory_target": exploratory,
        "roi_mapping": {
            "source": "union of exact pixel differences O vs O_sham/C/C_sham inside the Stage 3A declared edit ROI",
            "grid": "processor-reproduced row-major merged visual-token grid",
            "ring": "Chebyshev radius 1 around V_target, clipped to image grid",
            "irrelevant": "translated target-token shape minimizing original-image cell darkness, disjoint from target+ring; deterministic fallback uses cardinality-matched minimum-darkness cells",
            "manual_overlay_audit_required": True,
            "selection_used_attention": False,
        },
        "phase_a": {
            "primary_arms": ["all_visual", "target_roi", "visual_complement", "irrelevant_roi"],
            "secondary_arms": ["target_ring"],
            "robust_rule": robust_rule,
            "holm_family_size": 8,
            "gate": {
                "target_robust": True,
                "target_minus_irrelevant_bootstrap_CI_low": "> 0",
                "target_greater_than_irrelevant_fraction": ">= 0.70",
                "max_median_PRR_target_or_ring": ">= 0.50",
            },
            "classification": {
                "ROI-Local": "target robust; target PRR >=0.75; complement PRR <0.50; irrelevant PRR <0.25",
                "ROI-Local-Plus-Context": "target robust; target PRR >=0.25; ring PRR >=0.75; ring-target PRR >=0.20",
                "Visual-Distributed": "all-V robust and complement PRR >=0.50 or max target/ring PRR <0.50",
                "ROI-Inconclusive": "target-minus-irrelevant gate fails",
            },
        },
        "phase_b": {
            "gated": True,
            "arms": ["K", "V", "KV"],
            "robust_rule": robust_rule,
            "holm_family": "three arms per Phase-A-qualified primary target",
            "kv_reproduces_phase_a_tolerance": 1e-6,
            "source_region_rule": (
                "use V_target when its median Phase-A PRR is >=0.50; otherwise "
                "use V_target_ring when that region meets the >=0.50 Phase-A gate"
            ),
            "classification": {
                "Value-Dominant": "V robust; median KVR_V >=0.75; median KVR_K <0.50",
                "Routing-Dominant": "K robust; median KVR_K >=0.75; median KVR_V <0.50",
                "Routing+Value-Interaction": "K and V robust; each median KVR >=0.25; bootstrap CI low of KV-max(K,V) >0",
                "Mechanism-Inconclusive": "no frozen class passes",
            },
        },
        "reproduction": {
            "all_visual_vs_stage3b6_max_abs_score_difference": 1e-6,
            "self_control_exact": True,
            "determinism_exact_public_result": True,
        },
        "secondary_only": [
            "raw Stage 2C ROI attention",
            "selected-head ROI attention",
            "Stage 3B.1 cutoff triangulation",
            "exploratory W5/head_10 after primary freeze",
        ],
        "prohibited": [
            "vision-encoder feature localization",
            "query/key feature analysis",
            "value-subspace analysis",
            "MLP feature/neuron analysis",
            "Q/R lifecycle analysis",
            "multi-evidence refresh",
            "failure analysis",
        ],
    }
    family = {
        "frozen_at": frozen_at,
        "primary_targets": targets,
        "phase_a_primary_arms": config["phase_a"]["primary_arms"],
        "phase_a_secondary_arms": config["phase_a"]["secondary_arms"],
        "phase_a_holm_test_ids": [
            f"{target['cell_id']}__{arm}"
            for target in targets
            for arm in config["phase_a"]["primary_arms"]
        ],
        "phase_b_conditional_arms": config["phase_b"]["arms"],
        "statistical_unit": "base_problem_id",
        "attention_used_for_selection": False,
    }
    for directory in (
        "config/shards/validation",
        "config/shards/primary",
        "roi_audit/overlays",
        "validation",
        "scoring/raw",
        "analysis/figures",
        "summaries",
    ):
        ensure_directory(OUT / directory)
    write_json(OUT / "config/stage3b7_config.json", config)
    write_json(OUT / "config/primary_family.json", family)
    write_jsonl(OUT / "config/cohort_manifest.jsonl", primary)
    write_jsonl(OUT / "config/validation_manifest.jsonl", validation)
    for role, rows in (("validation", validation), ("primary", primary)):
        for index, shard in enumerate(balanced_shards(rows, 2)):
            write_jsonl(
                OUT / f"config/shards/{role}/{role}_{index:02d}.jsonl", shard
            )
    write_json(
        OUT / "config/sharding_summary.json",
        {
            "frozen_at": frozen_at,
            "validation": [4, 4],
            "primary": [19, 18],
            "execution": "existing Slurm job 106936 via tmux 8, A5000 x2",
        },
    )


if __name__ == "__main__":
    main()
