#!/usr/bin/env python3
"""Prepare deterministic Stage 3B.4 validation and paired-primary shards."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b4"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def round_robin(rows: list[dict[str, Any]], count: int) -> list[list[dict[str, Any]]]:
    shards = [[] for _ in range(count)]
    for index, row in enumerate(rows):
        shards[index % count].append(row)
    return shards


def main() -> None:
    validation = read_jsonl(OUT / "validation/validation_manifest.jsonl")
    cohort = read_jsonl(OUT / "config/cohort_manifest.jsonl")
    paired = [row for row in cohort if "structural" not in str(row["edit_tier"])]
    structural = [row for row in cohort if "structural" in str(row["edit_tier"])]
    if len(validation) != 8 or len(paired) != 37 or len(structural) != 4:
        raise RuntimeError("Frozen Stage 3B.4 split must be 8 validation / 37 paired / 4 structural")

    validation_dir = ensure_directory(OUT / "config/shards/validation")
    primary_dir = ensure_directory(OUT / "config/shards/primary")
    validation_shards = round_robin(validation, 8)
    primary_shards = round_robin(paired, 8)
    for index, rows in enumerate(validation_shards):
        write_jsonl(validation_dir / f"validation_{index:02d}.jsonl", rows)
    for index, rows in enumerate(primary_shards):
        write_jsonl(primary_dir / f"primary_{index:02d}.jsonl", rows)
    write_jsonl(OUT / "config/structural_manifest_only.jsonl", structural)
    write_json(OUT / "config/sharding_summary.json", {
        "validation_shards": [
            {"shard": index, "base_problem_ids": [str(row["base_problem_id"]) for row in rows]}
            for index, rows in enumerate(validation_shards)
        ],
        "primary_shards": [
            {"shard": index, "base_problem_ids": [str(row["base_problem_id"]) for row in rows]}
            for index, rows in enumerate(primary_shards)
        ],
        "structural_manifest_only": [str(row["base_problem_id"]) for row in structural],
        "structural_reason": "C_sham unavailable; excluded from paired module restoration without substitution",
    })


if __name__ == "__main__":
    main()
