#!/usr/bin/env python3
"""Create deterministic Stage 3B.2 cohort shards."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "outputs/stage3b2/config"
SHARD_COUNT = 7


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    rows = read_jsonl(CONFIG / "cohort_manifest.jsonl")
    schedules = {str(row["base_problem_id"]): row for row in read_jsonl(CONFIG / "switch_checkpoint_schedule.jsonl")}
    # Longest E_d first, greedy balance by frozen checkpoint count then E_d.
    ordered = sorted(
        rows,
        key=lambda row: (
            int(schedules[str(row["base_problem_id"])]["checkpoint_count"]),
            int(schedules[str(row["base_problem_id"])]["ed_generated_index"]),
        ),
        reverse=True,
    )
    shards: list[list[dict]] = [[] for _ in range(SHARD_COUNT)]
    loads = [0] * SHARD_COUNT
    for row in ordered:
        base = str(row["base_problem_id"])
        target = min(range(SHARD_COUNT), key=lambda index: (loads[index], len(shards[index]), index))
        shards[target].append(row)
        loads[target] += int(schedules[base]["checkpoint_count"])
    ensure_directory(CONFIG / "shards")
    for index, shard in enumerate(shards):
        write_jsonl(CONFIG / "shards" / f"cohort_{index:02d}.jsonl", shard)
    write_json(
        CONFIG / "shards/sharding_summary.json",
        {
            "shard_count": SHARD_COUNT,
            "base_counts": [len(shard) for shard in shards],
            "checkpoint_loads": loads,
            "base_problem_ids": [[str(row["base_problem_id"]) for row in shard] for shard in shards],
        },
    )
    print(json.dumps({"base_counts": [len(shard) for shard in shards], "checkpoint_loads": loads}, indent=2))


if __name__ == "__main__":
    main()
