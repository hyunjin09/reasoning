#!/usr/bin/env python3
"""Create the prospective Stage 1A 4,096-token pilot manifest and config."""

from __future__ import annotations

import argparse
from pathlib import Path

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage1.data import build_pilot_manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--stage0-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    allowed = (Path.cwd() / "outputs" / "stage1").resolve()
    try:
        output_dir.relative_to(allowed)
    except ValueError as exc:
        raise ValueError(f"Pilot output must be under {allowed}: {output_dir}") from exc
    rows = load_mathverse_rows(args.dataset_root)
    manifest = build_pilot_manifest(rows, args.stage0_dir.resolve())
    manifest_path = output_dir / "pilot_4096_manifest.jsonl"
    config_path = output_dir / "config_4096.json"
    if manifest_path.exists() or config_path.exists():
        raise FileExistsError("Prospective 4,096 pilot manifest/config already exists")
    write_jsonl(manifest_path, manifest)
    write_json(
        config_path,
        {
            "stage": "1A",
            "purpose": "prospective generation-cap pilot",
            "max_new_tokens": 4096,
            "model_checkpoint": str(args.model_checkpoint.resolve()),
            "dataset_root": str(args.dataset_root.resolve()),
            "decoding": {"do_sample": False, "strategy": "greedy", "use_cache": True},
            "fixed_components": [
                "Stage 0 prompt template",
                "Stage 0 image preprocessing",
                "Stage 0 answer evaluator",
                "Stage 0 eager-language/SDPA-vision attention backends",
                "Stage 0 read-only hooks and online aggregation",
                "Stage 0 Unicode-aware token alignment",
                "Stage 0 visual-token mapping",
            ],
            "sample_count": len(manifest),
            "previously_truncated": sum(row["stage0_status"] == "truncated" for row in manifest),
            "previously_completed": sum(row["stage0_status"] == "correct" for row in manifest),
            "sample_ids": [row["example_id"] for row in manifest],
            "decision_gate": "lock 4096 only if truncation_rate <= 0.10; otherwise run conditional 8192 pilot",
        },
    )
    print(f"Prepared fixed 4,096 pilot: {len(manifest)} examples at {manifest_path}")


if __name__ == "__main__":
    main()

