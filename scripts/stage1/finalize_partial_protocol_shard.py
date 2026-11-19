#!/usr/bin/env python3
"""Finalize a deliberately interrupted protocol shard from completed results only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json
from visual_reasoning.stage1.protocol import protocol_run_metrics


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard-dir", type=Path, required=True)
    args = parser.parse_args()
    shard_dir = args.shard_dir.resolve()
    config = read_json(shard_dir / "config.json")
    manifest = read_jsonl(shard_dir / "manifest.jsonl")
    results = [
        read_json(path)
        for path in sorted((shard_dir / "examples").glob("*/result.json"), key=lambda value: int(value.parent.name))
    ]
    if not results or len(results) >= len(manifest):
        raise ValueError("Partial finalization requires at least one result and fewer results than manifest rows")
    completed_ids = {str(row["example_id"]) for row in results}
    pending_ids = [str(row["example_id"]) for row in manifest if str(row["example_id"]) not in completed_ids]
    summary = protocol_run_metrics(results, max_new_tokens=40_960)
    signature = config["run_signature"]
    summary.update(
        {
            "condition": signature["condition"],
            "parameters": signature["parameters"],
            "transformers_generation_kwargs": signature["transformers_generation_kwargs"],
            "instrumentation_enabled": False,
            "partial_shard": True,
            "intended_example_count": len(manifest),
            "completed_example_count": len(results),
            "pending_example_ids_reassigned": pending_ids,
        }
    )
    write_json(shard_dir / "run_summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
