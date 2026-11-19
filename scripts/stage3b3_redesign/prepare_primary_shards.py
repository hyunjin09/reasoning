#!/usr/bin/env python3
"""Create eight balanced shards from the frozen 41-base primary manifest."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage3b3_redesign.primary import balanced_primary_shards


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "outputs/stage3b3_redesign/primary/primary_41_manifest.jsonl"
OUT = ROOT / "outputs/stage3b3_redesign/config/primary_shards"


def main() -> None:
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f"Refusing to overwrite frozen primary shards: {OUT}")
    ensure_directory(OUT)
    rows = [
        json.loads(line)
        for line in MANIFEST.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(rows) != 41 or len({str(row["base_problem_id"]) for row in rows}) != 41:
        raise RuntimeError("Primary manifest must contain exactly 41 unique base problems")

    shards = balanced_primary_shards(rows, shard_count=8)
    summary = []
    for index, shard in enumerate(shards):
        path = OUT / f"primary_{index:02d}.jsonl"
        write_jsonl(path, shard)
        numeric = sum("structural" not in str(row["edit_tier"]) for row in shard)
        structural = len(shard) - numeric
        summary.append({
            "shard": index,
            "base_problem_ids": [str(row["base_problem_id"]) for row in shard],
            "numeric_count": numeric,
            "structural_count": structural,
            "estimated_weight": numeric + 0.55 * structural,
            "manifest": str(path.relative_to(ROOT)),
        })
    write_json(OUT / "shard_summary.json", {"base_count": len(rows), "shards": summary})
    print(json.dumps({"base_count": len(rows), "shards": summary}, indent=2))


if __name__ == "__main__":
    main()
