#!/usr/bin/env python3
"""Prepare deterministic Stage 3B.5 validation and primary shards."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b5"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def round_robin(rows: list[dict[str, Any]], count: int) -> list[list[dict[str, Any]]]:
    shards = [[] for _ in range(count)]
    for index, row in enumerate(rows):
        shards[index % count].append(row)
    return shards


def main() -> None:
    validation = read_jsonl(OUT / "validation/validation_manifest.jsonl")
    primary = read_jsonl(OUT / "config/cohort_manifest.jsonl")
    if len(validation) != 8 or len(primary) != 37:
        raise RuntimeError("Frozen Stage 3B.5 split must be 8 validation / 37 paired")
    validation_shards = round_robin(validation, 8)
    primary_shards = round_robin(primary, 8)
    for phase, shards in (("validation", validation_shards), ("primary", primary_shards)):
        directory = ensure_directory(OUT / f"config/shards/{phase}")
        for index, rows in enumerate(shards):
            write_jsonl(directory / f"{phase}_{index:02d}.jsonl", rows)
    write_json(OUT / "config/sharding_summary.json", {
        "validation_shards": [
            {"shard": index, "base_problem_ids": [str(row["base_problem_id"]) for row in rows]}
            for index, rows in enumerate(validation_shards)
        ],
        "primary_shards": [
            {"shard": index, "base_problem_ids": [str(row["base_problem_id"]) for row in rows]}
            for index, rows in enumerate(primary_shards)
        ],
    })


if __name__ == "__main__":
    main()
