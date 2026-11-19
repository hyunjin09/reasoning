#!/usr/bin/env python3
"""Collect every outcome from the frozen Stage 3A round-3 generation shards."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage3a.cohort import merge_expansion_outcomes


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a"
FROZEN = OUT / "cohort/round3_valid_generation_manifest.jsonl"
SHARDS = OUT / "cohort_expansion/round3/shards"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    frozen = read_jsonl(FROZEN)
    outcomes: list[dict] = []
    for shard_dir in sorted(SHARDS.glob("shard_*")):
        result_path = shard_dir / "result.json"
        if not result_path.is_file():
            raise FileNotFoundError(f"Round-3 shard is incomplete: {result_path}")
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if int(result["total"]) != len(result["results"]):
            raise RuntimeError(f"Shard summary/results mismatch: {result_path}")
        outcomes.extend(result["results"])
    merged = merge_expansion_outcomes(frozen, outcomes)
    counts = Counter(str(row["status"]) for row in merged)
    completed_correct = [row for row in merged if row["status"] == "correct" and row["complete"]]
    output = OUT / "cohort_expansion/round3/raw_outcome_manifest.jsonl"
    write_jsonl(output, merged)
    write_jsonl(OUT / "cohort_expansion/round3/completed_correct_pending_e0.jsonl", completed_correct)
    summary = {
        "attempted": len(merged),
        "status_counts": dict(sorted(counts.items())),
        "completed_correct_pending_strict_pre_e0_audit": len(completed_correct),
        "all_raw_outcomes_preserved": len(merged) == len(frozen),
        "selection_and_edits_frozen_before_outcomes": True,
        "selection_used_attention": False,
    }
    write_json(OUT / "cohort_expansion/round3/collection_summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
