#!/usr/bin/env python3
"""Prepare (but do not launch) the four prospectively held batch-2 examples."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b8/discovery_cohort"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    all_rows = read_jsonl(OUT / "edit_validation/batch2_v4/manual_valid_generation_manifest.jsonl")
    active = {str(row["base_problem_id"]) for row in read_jsonl(OUT / "active_generation_manifest_batch2.jsonl")}
    held = [row for row in all_rows if str(row["base_problem_id"]) not in active]
    if [str(row["base_problem_id"]) for row in held] != ["394", "395", "396", "397"]:
        raise RuntimeError("Held batch-2 set changed from the prospectively frozen four bases")
    write_jsonl(OUT / "held_generation_manifest_batch2.jsonl", held)
    shard_dir = OUT / "generation_shards/batch2_held"
    ensure_directory(shard_dir)
    write_jsonl(shard_dir / "shard_00.jsonl", held[::2])
    write_jsonl(shard_dir / "shard_01.jsonl", held[1::2])
    write_json(ROOT / "outputs/stage3b8/config/discovery_batch2_held.json", {
        "status": "prepared_not_launched",
        "activation_rule": "launch only if batch1 plus batch2_active cannot yield at least 16 completed-correct strict-Ed-valid discovery bases",
        "base_problem_ids": [str(row["base_problem_id"]) for row in held],
        "selection_used_attention": False,
        "selection_used_generation_or_stage3b8_causal_outcomes": False,
    })
    print(json.dumps({"held": len(held), "base_problem_ids": [str(row["base_problem_id"]) for row in held]}, indent=2))


if __name__ == "__main__":
    main()
