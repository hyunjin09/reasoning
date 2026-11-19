#!/usr/bin/env python3
"""Validate and collect every prospectively frozen Stage 3A expansion outcome."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage3a.cohort import merge_expansion_outcomes


ROOT = Path(__file__).resolve().parents[2]
EXPANSION = ROOT / "outputs/stage3a/cohort_expansion"
SCREEN = ROOT / "outputs/stage3a/cohort/expansion_generation_manifest.jsonl"
BACKUP_SCREEN = ROOT / "outputs/stage3a/cohort/backup_valid_generation_manifest.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    frozen = read_jsonl(SCREEN)
    if BACKUP_SCREEN.is_file():
        frozen.extend(read_jsonl(BACKUP_SCREEN))
    shard_results = []
    for shard_index in range(4):
        path = EXPANSION / f"shards/shard_{shard_index:02d}/result.json"
        if not path.is_file():
            raise FileNotFoundError(f"Expansion shard is incomplete: {path}")
        result = json.loads(path.read_text(encoding="utf-8"))
        if int(result["total"]) != len(result["results"]):
            raise RuntimeError(f"Shard summary/results count mismatch: {path}")
        shard_results.extend(result["results"])
    if BACKUP_SCREEN.is_file():
        backup_path = EXPANSION / "backup_round2/result.json"
        if not backup_path.is_file():
            raise FileNotFoundError(f"Backup expansion is incomplete: {backup_path}")
        backup = json.loads(backup_path.read_text(encoding="utf-8"))
        if int(backup["total"]) != len(backup["results"]):
            raise RuntimeError(f"Backup summary/results count mismatch: {backup_path}")
        shard_results.extend(backup["results"])
    merged = merge_expansion_outcomes(frozen, shard_results)
    write_jsonl(EXPANSION / "raw_outcome_manifest.jsonl", merged)
    eligible = []
    for row in merged:
        metadata_path = ROOT / f"outputs/stage3a/counterfactuals/{row['base_problem_id']}/edit_metadata.json"
        edit_status = "not_constructed"
        if metadata_path.is_file():
            edit_status = json.loads(metadata_path.read_text(encoding="utf-8"))["manual_validation"]["status"]
        if row["status"] == "correct" and edit_status == "pass":
            eligible.append({**row, "manual_edit_status": edit_status, "event_annotation_status": "pending"})
    write_jsonl(EXPANSION / "eligible_completed_correct_pending_event.jsonl", eligible)
    counts = Counter(str(row["status"]) for row in merged)
    summary = {
        "attempted": len(merged),
        "status_counts": dict(sorted(counts.items())),
        "all_raw_outcomes_preserved": len(merged) == len(frozen),
        "manually_valid_edit_and_completed_correct": len(eligible),
        "guaranteed_existing_completed_correct_manual_passes": 14,
        "projected_total_before_event_audit": 14 + len(eligible),
        "minimum_required": 30,
    }
    write_json(EXPANSION / "collection_summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
