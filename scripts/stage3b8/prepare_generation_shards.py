#!/usr/bin/env python3
"""Create deterministic two-GPU shards for a frozen Stage 3B.8 manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from visual_reasoning.stage0.io import ensure_directory, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
ALLOWED = (ROOT / "outputs/stage3b8/discovery_cohort").resolve()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    output.relative_to(ALLOWED)
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Shard directory is nonempty: {output}")
    rows = [json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError("Cannot shard an empty manifest")
    ensure_directory(output)
    midpoint = (len(rows) + 1) // 2
    write_jsonl(output / "shard_00.jsonl", rows[:midpoint])
    write_jsonl(output / "shard_01.jsonl", rows[midpoint:])
    print(json.dumps({"total": len(rows), "shard_00": midpoint, "shard_01": len(rows) - midpoint}, indent=2))


if __name__ == "__main__":
    main()
