#!/usr/bin/env python3
"""Freeze the prospective Stage 3B.3 cohort, windows, rules, and shards."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage3b3.windows import coarse_layer_windows, cumulative_layer_windows


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b3"
SOURCE = ROOT / "outputs/stage3b2"
SMOKE_BASES = ("118", "148", "113")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def balanced_shards(
    manifest: list[dict[str, Any]],
    costs: dict[str, int],
    count: int,
) -> list[list[dict[str, Any]]]:
    shards: list[list[dict[str, Any]]] = [[] for _ in range(count)]
    loads = [0] * count
    for row in sorted(manifest, key=lambda value: costs[str(value["base_problem_id"])], reverse=True):
        target = min(range(count), key=lambda index: (loads[index], len(shards[index]), index))
        shards[target].append(row)
        loads[target] += costs[str(row["base_problem_id"])]
    return shards


def main() -> None:
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f"Refusing to overwrite existing Stage 3B.3 output tree: {OUT}")
    ensure_directory(OUT / "config/shards")
    for relative in ("smoke", "scoring", "analysis/figures", "summaries", "raw/coarse", "raw/fine"):
        ensure_directory(OUT / relative)

    manifest = read_jsonl(SOURCE / "config/cohort_manifest.jsonl")
    annotations = read_jsonl(SOURCE / "annotations/discriminative_event_annotations.jsonl")
    stage3b2_results = read_jsonl(SOURCE / "scoring/per_problem_switch_results.jsonl")
    if len(manifest) != 49 or len({str(row["base_problem_id"]) for row in manifest}) != 49:
        raise RuntimeError("Stage 3B.3 requires the exact 49-base Stage 3B.2 cohort")
    annotation_by_base = {str(row["base_problem_id"]): row for row in annotations}
    result_by_base = {str(row["base_problem_id"]): row for row in stage3b2_results}
    frozen_at = datetime.now(timezone.utc).isoformat()
    coarse = coarse_layer_windows()
    cumulative = cumulative_layer_windows()
    activation_boundaries = [5, 11, 17, 23, 29, 35]

    windows_payload = {
        "frozen_at": frozen_at,
        "language_layer_count": 36,
        "coarse_windows": coarse,
        "cumulative_windows": cumulative,
        "activation_patch_boundaries_after_layers": activation_boundaries,
        "primary_coordinates": ["Ed_minus_1", "Ed"],
        "selection_used_attention": False,
    }
    fine_rule = {
        "frozen_at": frozen_at,
        "cohort_scale_results_inspected_before_freeze": False,
        "qualify_coarse_window_if_at_either_primary_coordinate": [
            "median normalized BWS >= 0.20",
            "median normalized BWN >= 0.20",
            "the 95% bootstrap CI for median normalized BWS or BWN is wholly above the corresponding intervals of at least two nonadjacent coarse windows",
        ],
        "ci_separation_definition": "candidate ci_low > comparator ci_high at the same coordinate and metric",
        "boundary_rule": "fine-scan each qualifying coarse window and its immediate coarse neighbors",
        "fine_windows": "nonoverlapping 2-layer windows inside the rule-selected coarse regions",
        "single_layer_refinement": "not run in Stage 3B.3",
        "attention_used": False,
    }
    decision_rules = {
        "GO_module_path_localization": (
            "a coarse window has median normalized BWS and BWN >=0.20 at a primary coordinate, "
            "both median bootstrap CIs exclude zero, both sufficiency and necessity are bidirectionally "
            "consistent in >=70% of bases, sham/target <0.25, and a 2-layer refinement within the "
            "qualifying/adjacent region retains normalized BWS or BWN >=0.15"
        ),
        "GO_distributed_layer_mechanism": (
            "controls pass and no narrow-hotspot rule passes, but at least three coarse windows have "
            "median normalized BWS or BWN >=0.10, or cumulative curves show a multi-boundary increase "
            "without one qualifying 2-layer concentration"
        ),
        "REDIRECT_current_state_representation": (
            "source-switch effects do not meet hotspot/distributed rules, while coarse BAP has an adjacent-boundary "
            "increase >=0.30, post-boundary median normalized BAP >=0.50, and its median CI excludes zero"
        ),
        "REDESIGN": "all-layer reproduction or self/sham/audit controls fail",
    }
    config = {
        "frozen_at": frozen_at,
        "source_stage": "outputs/stage3b2",
        "primary_unit": "base_problem_id",
        "base_problem_count": 49,
        "evidence_types": {"tier1_local_numeric_label": 45, "tier3_structural_visual_edit": 4},
        "annotation_alignment": {"exact_baseline_tokens": 12, "semantic_teacher_forced_lead": 37},
        "model": "Qwen3-VL-4B-Thinking",
        "required_gpu_class": "A5000",
        "attention_implementation": "validated eager path",
        "seed": 1234,
        "primary_coordinates": ["Ed_minus_1", "Ed"],
        "primary_metrics": ["unnormalized BWS", "unnormalized BWN", "unnormalized BAP"],
        "secondary_normalization": "divide by matching Stage 3B.2 all-layer BRI; no clipping",
        "coarse_window_count": 6,
        "cumulative_set_count": 12,
        "activation_boundary_count": 6,
        "fine_localization_rule": "outputs/stage3b3/config/fine_localization_rule.json",
        "decision_rules": decision_rules,
        "smoke_base_problem_ids": list(SMOKE_BASES),
        "selection_used_attention": False,
        "optional_layer_readout": "skipped unless causal analyses pass and an already validated readout is available; no probe training",
        "prohibited": [
            "attention-vs-MLP decomposition",
            "head/path analysis",
            "ROI-specific source switching",
            "Q/R long-term carrier tracing",
            "multi-evidence refresh",
            "failure analysis",
        ],
    }
    write_json(OUT / "config/stage3b3_config.json", config)
    write_json(OUT / "config/coarse_layer_windows.json", windows_payload)
    write_json(OUT / "config/fine_localization_rule.json", fine_rule)
    write_jsonl(OUT / "config/cohort_manifest.jsonl", manifest)
    smoke = [row for base in SMOKE_BASES for row in manifest if str(row["base_problem_id"]) == base]
    if len(smoke) != 3:
        raise RuntimeError("Smoke bases are missing from the frozen cohort")
    write_jsonl(OUT / "config/smoke_manifest.jsonl", smoke)

    costs = {
        base: int(annotation_by_base[base]["ed_generated_index"])
        + int(result_by_base[base]["prompt_token_count"])
        + len(annotation_by_base[base]["original_divergent_suffix_ids"])
        + len(annotation_by_base[base]["counterfactual_divergent_suffix_ids"])
        for base in annotation_by_base
    }
    shards = balanced_shards(manifest, costs, 7)
    shard_summary = []
    for index, rows in enumerate(shards):
        path = OUT / f"config/shards/cohort_{index:02d}.jsonl"
        write_jsonl(path, rows)
        shard_summary.append(
            {
                "shard": index,
                "base_problem_ids": [str(row["base_problem_id"]) for row in rows],
                "base_count": len(rows),
                "estimated_sequence_cost": sum(costs[str(row["base_problem_id"])] for row in rows),
            }
        )
    write_json(OUT / "config/shard_summary.json", {"shards": shard_summary})
    print(json.dumps({"frozen_at": frozen_at, "bases": len(manifest), "shards": shard_summary}, indent=2))


if __name__ == "__main__":
    main()
