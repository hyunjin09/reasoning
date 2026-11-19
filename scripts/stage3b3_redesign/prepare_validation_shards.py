#!/usr/bin/env python3
"""Write one-base validation shards without changing the frozen split."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b3_redesign/config/validation_shards"
MANIFEST = ROOT / "outputs/stage3b3_redesign/config/validation_manifest.jsonl"


def main() -> None:
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError(f"Refusing to overwrite validation shards: {OUT}")
    ensure_directory(OUT)
    rows = [
        json.loads(line) for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    summary = []
    for index, row in enumerate(rows):
        path = OUT / f"validation_{index:02d}.jsonl"
        write_jsonl(path, [row])
        summary.append({
            "shard": index,
            "base_problem_ids": [str(row["base_problem_id"])],
            "manifest": str(path.relative_to(ROOT)),
        })
    write_json(OUT / "shard_summary.json", {"shards": summary})
    print(json.dumps({"shard_count": len(summary), "bases": [row["base_problem_ids"][0] for row in summary]}, indent=2))


if __name__ == "__main__":
    main()
