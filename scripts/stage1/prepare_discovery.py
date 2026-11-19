#!/usr/bin/env python3
"""Freeze the outcome-blind Stage 1B discovery cohort and GPU shards."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage1.data import VISUAL_VARIANTS, select_discovery_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-attempts", type=int, default=200)
    parser.add_argument("--shards", type=int, default=2)
    return parser.parse_args()


def manifest_row(order: int, row: dict[str, Any]) -> dict[str, Any]:
    image = str(row["image"])
    return {
        "order": order,
        "example_id": str(row["sample_index"]),
        "base_problem_id": str(row["problem_index"]),
        "problem_index": str(row["problem_index"]),
        "variant": str(row["problem_version"]),
        "subject": str(row.get("metadata", {}).get("subject", "unknown")),
        "subfield": str(row.get("metadata", {}).get("subfield", "unknown")),
        "question_id": str(row["sample_index"]),
        "image_id": image,
        "question_word_count": len(str(row.get("question", "")).split()),
        "selection_reason": (
            "prospective outcome-blind Stage 1B selection; paired Vision Intensive/Vision Dominant; "
            "subject round-robin; longer questions prioritized within subject"
        ),
    }


def main() -> None:
    args = parse_args()
    if args.shards <= 0:
        raise ValueError("shards must be positive")
    output_dir = args.output_dir.resolve()
    allowed = (Path.cwd() / "outputs" / "stage1" / "discovery").resolve()
    try:
        output_dir.relative_to(allowed)
    except ValueError as exc:
        raise ValueError(f"Discovery preparation must stay under {allowed}: {output_dir}") from exc
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Refusing to overwrite frozen discovery preparation: {output_dir}")

    rows = load_mathverse_rows(args.dataset_root)
    selected = select_discovery_rows(rows, max_attempts=args.max_attempts)
    manifest = [manifest_row(index, row) for index, row in enumerate(selected)]
    by_problem: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in manifest:
        by_problem[row["base_problem_id"]].append(row)
        resolve_image_path(args.dataset_root, row["image_id"])
    expected_variants = set(VISUAL_VARIANTS)
    if any({row["variant"] for row in pair} != expected_variants for pair in by_problem.values()):
        raise RuntimeError("Discovery manifest does not contain complete requested pairs")

    ensure_directory(output_dir / "manifests")
    write_jsonl(output_dir / "cohort_attempt_manifest.jsonl", manifest)
    shard_rows: list[list[dict[str, Any]]] = [[] for _ in range(args.shards)]
    ordered_pairs = sorted(by_problem.values(), key=lambda pair: min(int(row["order"]) for row in pair))
    for pair_index, pair in enumerate(ordered_pairs):
        shard_rows[pair_index % args.shards].extend(sorted(pair, key=lambda row: int(row["order"])))
    for shard_index, shard in enumerate(shard_rows):
        write_jsonl(output_dir / "manifests" / f"shard_{shard_index:02d}.jsonl", shard)

    config = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "selection_frozen_before_inference": True,
        "dataset_root": str(args.dataset_root.resolve()),
        "max_raw_attempts": args.max_attempts,
        "target_completed_correct": 100,
        "minimum_completed_correct": 80,
        "variants": list(VISUAL_VARIANTS),
        "pairing_key": "problem_index",
        "selection_uses_outcomes_or_attention": False,
        "selection_method": (
            "Complete Vision Intensive/Vision Dominant pairs; subject-balanced round-robin; "
            "descending question word count then problem_index within each subject."
        ),
        "protocol_lock": "outputs/stage1/protocol_pilot/protocol_40960_selection.json",
        "generation": {
            "protocol": "official",
            "do_sample": True,
            "temperature": 0.6,
            "top_p": 0.95,
            "top_k": 20,
            "repetition_penalty": 1.0,
            "presence_penalty": 0.0,
            "max_new_tokens": 40960,
            "seed": 1234,
            "normal_stop": "EOS",
            "hardware_scope": "NVIDIA RTX A5000",
        },
        "attempt_count": len(manifest),
        "base_problem_count": len(by_problem),
        "variant_counts": dict(sorted(Counter(row["variant"] for row in manifest).items())),
        "subject_counts": dict(sorted(Counter(row["subject"] for row in manifest).items())),
        "shards": [
            {
                "shard": index,
                "path": f"manifests/shard_{index:02d}.jsonl",
                "attempt_count": len(shard),
                "base_problem_count": len(shard) // 2,
            }
            for index, shard in enumerate(shard_rows)
        ],
        "scientific_boundary": "attention and candidate peaks are descriptive, not causal visual usage",
    }
    write_json(output_dir / "discovery_config.json", config)
    print(json.dumps(config, indent=2))


if __name__ == "__main__":
    main()
