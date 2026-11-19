#!/usr/bin/env python3
"""Split the frozen Stage 3A primary manifest into deterministic scoring shards."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--shards", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.relative_to((ROOT / "outputs/stage3a/scoring").resolve())
    if args.shards <= 0:
        raise ValueError("--shards must be positive")
    rows = [json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(rows) < args.shards:
        raise ValueError("Cannot create more scoring shards than primary rows")
    if len({str(row["base_problem_id"]) for row in rows}) != len(rows):
        raise RuntimeError("Primary manifest contains duplicate base_problem_id")
    ensure_directory(output)
    sizes = []
    for index in range(args.shards):
        shard = rows[index:: args.shards]
        path = output / f"primary_{index:02d}.jsonl"
        if path.exists():
            raise FileExistsError(path)
        write_jsonl(path, shard)
        sizes.append(len(shard))
    summary = {
        "source_manifest": str(args.manifest.resolve()),
        "primary_count": len(rows),
        "shard_count": args.shards,
        "shard_sizes": sizes,
        "assignment": "round-robin in frozen primary-manifest order",
    }
    write_json(output / "sharding_summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
