#!/usr/bin/env python3
"""Deterministically shard the frozen 49-base Stage 3B.0 cohort."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "outputs/stage3b0/config/cohort_manifest.jsonl"
OUTPUT = ROOT / "outputs/stage3b0/config/shards"
SHARD_COUNT = 7


def main() -> None:
    rows = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) != 49 or len({str(row["base_problem_id"]) for row in rows}) != 49:
        raise RuntimeError("Expected the frozen 49-base cohort")
    ensure_directory(OUTPUT)
    summary = []
    for shard_index in range(SHARD_COUNT):
        shard = rows[shard_index::SHARD_COUNT]
        path = OUTPUT / f"cohort_{shard_index:02d}.jsonl"
        write_jsonl(path, shard)
        summary.append(
            {
                "shard": shard_index,
                "path": str(path.relative_to(ROOT)),
                "count": len(shard),
                "base_problem_ids": [str(row["base_problem_id"]) for row in shard],
            }
        )
    write_json(OUTPUT / "sharding_summary.json", {"shard_count": SHARD_COUNT, "total": 49, "shards": summary})
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
