#!/usr/bin/env python3
"""Split a frozen Stage 1B manifest without separating modality pairs."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--shards", type=int, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.shards <= 0:
        raise ValueError("shards must be positive")
    output_dir = args.output_dir.resolve()
    allowed = (Path.cwd() / "outputs" / "stage1" / "discovery").resolve()
    try:
        output_dir.relative_to(allowed)
    except ValueError as exc:
        raise ValueError(f"Execution manifests must stay under {allowed}: {output_dir}") from exc
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Refusing to overwrite execution manifests: {output_dir}")

    rows = [json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines()]
    by_problem: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_problem[str(row["base_problem_id"])].append(row)
    ordered_pairs = sorted(by_problem.values(), key=lambda pair: min(int(row["order"]) for row in pair))
    if any(len(pair) != 2 for pair in ordered_pairs):
        raise RuntimeError("Every frozen base problem must have exactly two selected variants")
    shards: list[list[dict[str, Any]]] = [[] for _ in range(args.shards)]
    for pair_index, pair in enumerate(ordered_pairs):
        shards[pair_index % args.shards].extend(sorted(pair, key=lambda row: int(row["order"])))
    ensure_directory(output_dir)
    for index, shard in enumerate(shards):
        write_jsonl(output_dir / f"shard_{index:02d}.jsonl", shard)
    write_json(
        output_dir / "execution_shards.json",
        {
            "source_manifest": str(args.manifest.resolve()),
            "selection_changed": False,
            "pair_preserving": True,
            "shard_count": args.shards,
            "shards": [
                {
                    "shard": index,
                    "path": f"shard_{index:02d}.jsonl",
                    "attempt_count": len(shard),
                    "base_problem_count": len(shard) // 2,
                }
                for index, shard in enumerate(shards)
            ],
        },
    )


if __name__ == "__main__":
    main()
