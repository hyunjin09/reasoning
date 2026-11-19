#!/usr/bin/env python3
"""Deterministically cost-balance the frozen Stage 3B.1 cohort."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
COHORT = ROOT / "outputs/stage3b1/config/cohort_manifest.jsonl"
SCHEDULE = ROOT / "outputs/stage3b1/config/checkpoint_schedule.jsonl"
OUTPUT = ROOT / "outputs/stage3b1/config/shards"
SHARD_COUNT = 7


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    cohort = read_jsonl(COHORT)
    schedules = {str(row["base_problem_id"]): row for row in read_jsonl(SCHEDULE)}
    if len(cohort) != 49 or len(schedules) != 49:
        raise RuntimeError("Expected the frozen 49-base cohort and schedule")
    shards: list[list[dict]] = [[] for _ in range(SHARD_COUNT)]
    costs = [0 for _ in range(SHARD_COUNT)]
    ordered = sorted(
        cohort,
        key=lambda row: (
            -int(row["event"]["e0_start_token"]) * schedules[str(row["base_problem_id"])]["checkpoint_count"],
            int(row["base_problem_id"]),
        ),
    )
    for row in ordered:
        base = str(row["base_problem_id"])
        cost = int(row["event"]["e0_start_token"]) * int(schedules[base]["checkpoint_count"])
        target = min(range(SHARD_COUNT), key=lambda index: (costs[index], index))
        shards[target].append(row)
        costs[target] += cost
    ensure_directory(OUTPUT)
    summary = []
    for index, rows in enumerate(shards):
        rows.sort(key=lambda row: int(row["base_problem_id"]))
        path = OUTPUT / f"cohort_{index:02d}.jsonl"
        write_jsonl(path, rows)
        summary.append(
            {
                "shard": index,
                "path": str(path.relative_to(ROOT)),
                "count": len(rows),
                "estimated_cost": costs[index],
                "base_problem_ids": [str(row["base_problem_id"]) for row in rows],
            }
        )
    if sum(row["count"] for row in summary) != 49:
        raise RuntimeError("Sharding lost a frozen base")
    write_json(OUTPUT / "sharding_summary.json", {"shard_count": SHARD_COUNT, "total": 49, "shards": summary})
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
