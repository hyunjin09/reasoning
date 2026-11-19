#!/usr/bin/env python3
"""Mechanically split the frozen cohort using historical 8,192 termination only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--historical-run", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    by_id = {str(row["example_id"]): row for row in rows}
    historical = {}
    for result_path in (args.historical_run / "examples").glob("*/result.json"):
        result = json.loads(result_path.read_text(encoding="utf-8"))
        historical[str(result["example_id"])] = result
    if set(historical) != set(by_id):
        raise ValueError("Historical run and frozen 40,960 cohort differ")
    completed_ids = [sample_id for sample_id in by_id if historical[sample_id]["status"] != "truncated"]
    truncated_ids = [sample_id for sample_id in by_id if historical[sample_id]["status"] == "truncated"]
    output_dir = args.output_dir.resolve()
    write_jsonl(output_dir / "historically_completed.jsonl", [by_id[sample_id] for sample_id in completed_ids])
    for sample_id in truncated_ids:
        write_jsonl(output_dir / f"historically_truncated_{sample_id}.jsonl", [by_id[sample_id]])
    write_json(
        output_dir / "execution_split.json",
        {
            "scientific_manifest_unchanged": True,
            "split_basis": "historical 8,192 termination status only; used for resource-safe scheduling, not selection",
            "historically_completed_ids": completed_ids,
            "historically_truncated_ids": truncated_ids,
        },
    )
    print(f"Prepared one completed-control shard and {len(truncated_ids)} long-tail shards")


if __name__ == "__main__":
    main()
