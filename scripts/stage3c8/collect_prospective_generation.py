#!/usr/bin/env python3
"""Validate and collect the frozen Stage 3C.8 prospective-generation outcomes."""

from __future__ import annotations

import hashlib
import json
import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c8"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-partial", action="store_true")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    args = parse_args()
    screen = read_jsonl(OUT / "cohort/prospective_screen_manifest.jsonl")
    expected = {str(row["base_problem_id"]): row for row in screen}
    if len(expected) != 240:
        raise RuntimeError(f"Expected 240 frozen screen bases, found {len(expected)}")
    result_paths = sorted((OUT / "prospective_generation/raw").glob("shard_*/examples/*/result.json"))
    if len(result_paths) != len(expected) and not args.allow_partial:
        raise RuntimeError(f"Prospective generation incomplete: {len(result_paths)}/{len(expected)} results")
    if len(result_paths) > len(expected):
        raise RuntimeError(f"Observed more results than frozen screen entries: {len(result_paths)}/{len(expected)}")
    outcomes = []
    for path in result_paths:
        row = read_json(path)
        base = str(row["base_problem_id"])
        if base not in expected:
            raise RuntimeError(f"Unfrozen generated base {base}")
        frozen = expected[base]
        if str(row["example_id"]) != str(frozen["example_id"]) or int(row["screen_order"]) != int(frozen["order"]):
            raise RuntimeError(f"Frozen identity mismatch for base {base}")
        generation_path = path.parent / "generation.json"
        tokens_path = path.parent / "tokens.jsonl"
        if not generation_path.is_file() or not tokens_path.is_file():
            raise RuntimeError(f"Incomplete raw bundle for base {base}")
        outcomes.append({
            **row,
            "generation_path": str(generation_path.relative_to(ROOT)),
            "generation_sha256": hashlib.sha256(generation_path.read_bytes()).hexdigest(),
            "tokens_path": str(tokens_path.relative_to(ROOT)),
            "tokens_sha256": hashlib.sha256(tokens_path.read_bytes()).hexdigest(),
            "raw_generation_modified": False,
        })
    outcomes.sort(key=lambda row: int(row["screen_order"]))
    if [int(row["screen_order"]) for row in outcomes] != sorted(int(row["screen_order"]) for row in outcomes):
        raise RuntimeError("Collected outcomes are not in frozen screen order")
    counts = Counter(str(row["status"]) for row in outcomes)
    correct = [row for row in outcomes if row["status"] == "correct"]
    write_jsonl(OUT / "prospective_generation/raw_outcome_manifest.jsonl", outcomes)
    write_jsonl(OUT / "prospective_generation/completed_correct_pool.jsonl", correct)
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "frozen": len(screen),
        "observed": len(outcomes),
        "unattempted": len(screen) - len(outcomes),
        "collection_status": "complete" if len(outcomes) == len(screen) else "partial",
        "status_counts": dict(sorted(counts.items())),
        "completed_correct": len(correct),
        "all_raw_outcomes_preserved": True,
        "raw_generations_modified": False,
        "selection_used_attention": False,
        "selection_used_carrier_outcome": False,
        "maximum_generated_tokens": max((int(row["generated_token_count"]) for row in outcomes), default=None),
        "maximum_peak_gpu_allocated_bytes": max((int(row["runtime"]["peak_gpu_allocated_bytes"]) for row in outcomes), default=None),
    }
    write_json(OUT / "prospective_generation/generation_summary.json", summary)
    accounting = read_json(OUT / "cohort/sample_accounting.json")
    accounting.update({
        "screened": len(outcomes),
        "unattempted": len(screen) - len(outcomes),
        "completed_correct": len(correct),
        "generation_status_counts": dict(sorted(counts.items())),
        "status": "edit_and_evidence_screen_pending",
    })
    write_json(OUT / "cohort/sample_accounting.json", accounting)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
