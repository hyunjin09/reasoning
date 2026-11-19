#!/usr/bin/env python3
"""Freeze the Stage 3B.1 cohort, checkpoint schedules, and analysis rules."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage3b1.checkpoints import (
    E0_RELATIVE_OFFSETS,
    NORMALIZED_PROGRESS,
    build_checkpoint_schedule,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "outputs/stage3a/cohort/primary_manifest.jsonl"
OUTPUT = ROOT / "outputs/stage3b1"
SMOKE_BASES = ("118", "148", "113")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    rows = read_jsonl(SOURCE)
    bases = [str(row["base_problem_id"]) for row in rows]
    if len(rows) != 49 or len(set(bases)) != 49:
        raise RuntimeError("Stage 3B.1 requires the frozen 49-unique-base Stage 3A manifest")
    if any(len(row["prefix_token_ids"]) != int(row["event"]["e0_start_token"]) for row in rows):
        raise RuntimeError("Every frozen prefix must equal y_<E0")
    smoke = [row for base in SMOKE_BASES for row in rows if str(row["base_problem_id"]) == base]
    if len(smoke) != 3 or any(row["edit_tier"] != "tier1_local_numeric_label" for row in smoke):
        raise RuntimeError("Smoke bases must be three numeric-label examples")
    if [int(row["event"]["e0_start_token"]) for row in smoke] != [6, 72, 908]:
        raise RuntimeError("Smoke examples no longer span the frozen short/medium/long E0 lengths")

    schedules = []
    for row in rows:
        e0 = int(row["event"]["e0_start_token"])
        checkpoints = build_checkpoint_schedule(e0)
        schedules.append(
            {
                "base_problem_id": str(row["base_problem_id"]),
                "example_id": str(row["example_id"]),
                "prefix_sha256": row["prefix_sha256"],
                "e0_start_token": e0,
                "checkpoint_count": len(checkpoints),
                "checkpoints": checkpoints,
            }
        )
    total = sum(row["checkpoint_count"] for row in schedules)
    if total != 489:
        raise RuntimeError(f"Frozen schedule changed: expected 489 unique problem-checkpoints, observed {total}")

    for directory in (
        "config/shards",
        "smoke",
        "scoring",
        "analysis/figures",
        "summaries",
        "raw/smoke",
        "raw/shards",
    ):
        ensure_directory(OUTPUT / directory)
    write_jsonl(OUTPUT / "config/cohort_manifest.jsonl", rows)
    write_jsonl(OUTPUT / "config/smoke_manifest.jsonl", smoke)
    write_jsonl(OUTPUT / "config/checkpoint_schedule.jsonl", schedules)
    write_json(
        OUTPUT / "config/stage3b1_config.json",
        {
            "frozen_at": datetime.now(timezone.utc).isoformat(),
            "source_manifest": str(SOURCE.relative_to(ROOT)),
            "primary_unit": "base_problem_id",
            "base_problem_count": 49,
            "evidence_strata": {"tier1_local_numeric_label": 45, "tier3_structural_visual_edit": 4},
            "selection_used_attention": False,
            "model_protocol": "Qwen3-VL-4B-Thinking locked Stage 1 official-style protocol",
            "seed": 1234,
            "strict_prefix": "exact Stage 3A y_<E0 token IDs; E0 excluded",
            "cutoff_semantics": {
                "cutoff_generated_index_c": "queries y_0 through y_(c-1) retain vision; y_c is the first blocked generated query",
                "generation_start": "c=0, exactly the Stage 3B.0 boundary",
                "blocked_edges": "all generated-query to all visual-prompt-key edges at and after c",
                "prefill": "unmodified",
                "layers": 36,
                "logical_query_heads": 32,
            },
            "checkpoint_coordinates": {
                "e0_relative_offsets": list(E0_RELATIVE_OFFSETS),
                "normalized_progress": list(NORMALIZED_PROGRESS),
                "normalized_mapping": "floor(requested_progress * E0)",
                "deduplication": "score each exact cutoff index once and retain every associated label",
                "unique_problem_checkpoint_pairs": total,
            },
            "scoring_path": "full-sequence eager attention for no-cutoff and every timed-cutoff score",
            "thresholds_secondary": [0.5, 0.8, 0.9],
            "monotonicity": {
                "primary_curve": "raw unsmoothed retention",
                "control_noise_tolerance": 1e-6,
                "material_complexity_threshold": 0.20,
            },
            "timing_category_rules": {
                "S6": "maximum raw downward step >0.20",
                "S1": "generation-start retention >=0.80 after excluding S6",
                "S2": "first rho>=0.80 crossing at progress <=0.25",
                "S3": "first rho>=0.80 at progress (0.25,0.75], or partial late retention >=0.50",
                "S4": "first rho>=0.80 after progress 0.75",
                "S5": "no rho>=0.80 crossing and final retention <0.50",
            },
            "decision_rules": {
                "GO": "at least 50% have a stable rho>=0.80 crossing, median E0-1 retention >=0.80, and median maximum post-prefill gain >=0.50",
                "CONDITIONAL_GO": "GO fails, but at least 50% have a first rho>=0.80 crossing and median maximum post-prefill gain >=0.30",
                "REDIRECT": "neither GO nor CONDITIONAL_GO conditions hold",
            },
            "attention_role": "secondary exact-event overlap only after timing scores are frozen",
            "smoke_base_problem_ids": list(SMOKE_BASES),
            "optional_rollouts": "not run prospectively because Stage 3B.0 128-token rollouts rarely reached the fact; teacher-forced evidence preference is primary",
            "prohibited": ["Q/R patching", "layer/module/head/path analysis", "Stage 3B.2"],
            "stage3b2_started": False,
        },
    )
    print(json.dumps({"cohort": len(rows), "smoke_bases": list(SMOKE_BASES), "unique_checkpoints": total}, indent=2))


if __name__ == "__main__":
    main()
