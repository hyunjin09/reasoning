#!/usr/bin/env python3
"""Create the conditional Stage 1A 8,192-token manifest from 4,096 results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage1.data import select_8192_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--stage0-dir", type=Path, required=True)
    parser.add_argument("--pilot-4096-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    args = parser.parse_args()
    results = []
    for result_path in sorted(
        (args.pilot_4096_dir / "examples").glob("*/result.json"), key=lambda path: int(path.parent.name)
    ):
        results.append(json.loads(result_path.read_text(encoding="utf-8")))
    if len(results) != 20:
        raise ValueError(f"Expected 20 completed 4,096 pilot results, found {len(results)}")
    truncation_rate = sum(result["status"] == "truncated" for result in results) / len(results)
    if truncation_rate <= 0.10:
        raise RuntimeError(f"4,096 truncation rate is {truncation_rate:.3f}; 8,192 pilot is not authorized")
    rows = load_mathverse_rows(args.dataset_root)
    manifest = select_8192_manifest(results, rows, args.stage0_dir.resolve(), minimum_examples=10)
    output_dir = args.output_dir.resolve()
    manifest_path = output_dir / "pilot_8192_manifest.jsonl"
    config_path = output_dir / "config_8192.json"
    if manifest_path.exists() or config_path.exists():
        raise FileExistsError("Prospective 8,192 pilot manifest/config already exists")
    write_jsonl(manifest_path, manifest)
    write_json(
        config_path,
        {
            "stage": "1A",
            "purpose": "conditional generation-cap pilot",
            "trigger_4096_truncation_rate": truncation_rate,
            "max_new_tokens": 8192,
            "model_checkpoint": str(args.model_checkpoint.resolve()),
            "dataset_root": str(args.dataset_root.resolve()),
            "decoding": {"do_sample": False, "strategy": "greedy", "use_cache": True},
            "sample_count": len(manifest),
            "sample_ids": [row["example_id"] for row in manifest],
            "selection_reasons": {row["example_id"]: row["selection_reason"] for row in manifest},
            "decision_gate": "lock 8192 only if truncation_rate <= 0.10; otherwise stop before Stage 1B",
        },
    )
    print(f"Prepared conditional 8,192 pilot: {len(manifest)} examples at {manifest_path}")


if __name__ == "__main__":
    main()

