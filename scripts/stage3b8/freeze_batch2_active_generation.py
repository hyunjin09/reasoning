#!/usr/bin/env python3
"""Activate the first 16 frozen batch-2 edits under the ascending-base rule."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b8/discovery_cohort"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    target = OUT / "active_generation_manifest_batch2.jsonl"
    shard_dir = OUT / "generation_shards/batch2_active"
    if target.exists() or (shard_dir.exists() and any(shard_dir.iterdir())):
        raise FileExistsError("Batch-2 active generation set is already frozen")
    rows = sorted(
        read_jsonl(OUT / "edit_validation/batch2_v4/manual_valid_generation_manifest.jsonl"),
        key=lambda row: int(row["base_problem_id"]),
    )
    if len(rows) != 20:
        raise RuntimeError("Expected 20 manually valid batch-2 contingency edits")
    active, held = rows[:16], rows[16:]
    write_jsonl(target, active)
    ensure_directory(shard_dir)
    write_jsonl(shard_dir / "shard_00.jsonl", active[:8])
    write_jsonl(shard_dir / "shard_01.jsonl", active[8:])
    write_json(ROOT / "outputs/stage3b8/config/discovery_batch2_activation.json", {
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "active_count": len(active),
        "active_bases": [row["base_problem_id"] for row in active],
        "held_clean_contingency_count": len(held),
        "held_bases": [row["base_problem_id"] for row in held],
        "rule": "ascending base_problem_id among the already frozen/manual-valid batch-2 edits",
        "attention_used": False,
        "stage3b8_causal_or_fit_outcomes_exist_or_were_inspected": False,
        "reason": "Add a bounded 16-base generation batch; retain four redundant circle-label edits only if yield after strict Ed audit remains below 16.",
    })
    print(json.dumps({"active": len(active), "held": len(held)}, indent=2))


if __name__ == "__main__":
    main()
