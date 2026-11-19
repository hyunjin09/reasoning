#!/usr/bin/env python3
"""Aggregate completed Stage 1A.2 protocol shards without moving raw artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage1.protocol import protocol_run_metrics


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--condition-root", type=Path, required=True)
    parser.add_argument("--condition", choices=("greedy", "official"), required=True)
    args = parser.parse_args()
    manifest = read_jsonl(args.manifest)
    condition_root = args.condition_root.resolve()
    found: dict[str, tuple[dict[str, Any], Path]] = {}
    shard_summaries: list[dict[str, Any]] = []
    for shard_dir in sorted((condition_root / "shards").glob("shard_*")):
        summary_path = shard_dir / "run_summary.json"
        if not summary_path.is_file():
            raise FileNotFoundError(f"Incomplete protocol shard: {summary_path}")
        shard_summary = read_json(summary_path)
        if shard_summary["condition"] != args.condition:
            raise ValueError(f"Condition mismatch in {summary_path}")
        shard_summaries.append(shard_summary)
        for result_path in (shard_dir / "examples").glob("*/result.json"):
            result = read_json(result_path)
            example_id = str(result["example_id"])
            if example_id in found:
                raise ValueError(f"Duplicate protocol result for example {example_id}")
            found[example_id] = (result, result_path.parent)
    expected_ids = [str(row["example_id"]) for row in manifest]
    if set(found) != set(expected_ids):
        raise ValueError(f"Protocol results differ from manifest: expected={expected_ids}, found={sorted(found)}")
    results = [found[example_id][0] for example_id in expected_ids]
    summary = protocol_run_metrics(results, max_new_tokens=40_960)
    summary.update(
        {
            "condition": args.condition,
            "parameters": shard_summaries[0]["parameters"],
            "transformers_generation_kwargs": shard_summaries[0]["transformers_generation_kwargs"],
            "instrumentation_enabled": False,
            "shard_count": len(shard_summaries),
            "all_shards_complete": True,
        }
    )
    outcome_rows = []
    for manifest_row in manifest:
        example_id = str(manifest_row["example_id"])
        result, example_dir = found[example_id]
        outcome_rows.append(
            {
                "condition": args.condition,
                "example_id": example_id,
                "problem_index": result["problem_index"],
                "mathverse_variant": result["mathverse_variant"],
                "selection_reason": manifest_row["selection_reason"],
                "status": result["status"],
                "normal_termination": result["normal_termination"],
                "termination_reason": result["termination_reason"],
                "complete": result["complete"],
                "correct": result["correct"],
                "generated_token_count": result["generated_token_count"],
                "latency_seconds": result["runtime"]["elapsed_seconds"],
                "peak_gpu_allocated_bytes": result["runtime"]["peak_gpu_allocated_bytes"],
                "artifact_bytes": result["output_bytes"],
                "any_pathology_flag": result["repetition"]["any_pathology_flag"],
                "artifact_dir": str(example_dir.resolve()),
            }
        )
    write_json(condition_root / "run_summary.json", summary)
    write_jsonl(condition_root / "raw_outcome_manifest.jsonl", outcome_rows)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
