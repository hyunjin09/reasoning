#!/usr/bin/env python3
"""Split the frozen Stage 3A expansion manifest deterministically."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--shards", type=int, default=4)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.shards < 1 or args.shards > len(rows):
        raise ValueError("Shard count must be between one and the manifest size")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for shard in range(args.shards):
        path = args.output_dir / f"shard_{shard:02d}.jsonl"
        if path.exists():
            raise FileExistsError(path)
        selected = rows[shard :: args.shards]
        path.write_text("".join(json.dumps(row) + "\n" for row in selected), encoding="utf-8")
        print(f"{path}: {len(selected)}")


if __name__ == "__main__":
    main()

