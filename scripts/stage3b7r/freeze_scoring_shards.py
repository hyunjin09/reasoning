#!/usr/bin/env python3
"""Freeze balanced two-GPU shards from an already frozen Stage 3B.7-R manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--expected-count", type=int, required=True)
    args = parser.parse_args()
    rows = read_jsonl(args.manifest)
    bases = [str(row["base_problem_id"]) for row in rows]
    if len(rows) != args.expected_count or len(set(bases)) != len(rows):
        raise RuntimeError(f"Expected {args.expected_count} unique bases, observed {len(rows)}/{len(set(bases))}")
    paths = [args.output_dir / f"{args.prefix}_{rank:02d}.jsonl" for rank in range(2)]
    if any(path.exists() for path in paths):
        raise FileExistsError("Scoring shards are already frozen")
    ensure_directory(args.output_dir)
    shards = [rows[0::2], rows[1::2]]
    for path, shard in zip(paths, shards, strict=True):
        write_jsonl(path, shard)
    write_json(args.output_dir / f"{args.prefix}_summary.json", {
        "source_manifest": str(args.manifest),
        "base_problem_ids": bases,
        "shard_counts": [len(shard) for shard in shards],
        "selection_used_attention": False,
        "causal_scores_inspected_before_freeze": False,
    })


if __name__ == "__main__":
    main()
