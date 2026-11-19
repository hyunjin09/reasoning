#!/usr/bin/env python3
"""Freeze two balanced Stage 3B.9 generation shards before inference."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def main() -> None:
    phase_a = read_jsonl(OUT / "phase_a_shared/prospective_edit_manifest.jsonl")
    phase_b = read_jsonl(OUT / "phase_b_local/prospective_edit_manifest.jsonl")
    rows = []
    for row in [*phase_b, *phase_a]:
        rows.append({**row, "selected_for_prospective_generation": True})
    shards = [[], []]
    for index, row in enumerate(rows):
        shards[index % 2].append(row)
    target = OUT / "config/generation_shards"
    write_jsonl(target / "shard_00.jsonl", shards[0])
    write_jsonl(target / "shard_01.jsonl", shards[1])
    write_json(target / "freeze.json", {
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "phase_a_edit_valid": len(phase_a),
        "phase_b_edit_valid": len(phase_b),
        "total": len(rows),
        "shard_sizes": [len(shard) for shard in shards],
        "split_rule": "phase-B first then Phase-A; alternating assignment",
        "generation_outcomes_inspected": False,
        "stage3b9_value_or_causal_outcomes_inspected": False,
    })
    print(json.dumps({"total": len(rows), "shards": [len(shard) for shard in shards]}, indent=2))


if __name__ == "__main__":
    main()
