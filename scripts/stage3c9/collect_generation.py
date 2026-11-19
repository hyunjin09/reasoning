#!/usr/bin/env python3
"""Collect resumable Stage 3C.9 generation outcomes and update screening counts."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    manifest = {
        str(row["example_id"]): row
        for row in (
            json.loads(line)
            for line in (OUT / "cohort/prospective_screen_manifest.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }
    rows = []
    for path in sorted((OUT / "prospective_generation/raw").glob("shard_*/examples/*/result.json")):
        row = read_json(path)
        expected = manifest.get(str(row["example_id"]))
        if expected is None or str(row["base_problem_id"]) != str(expected["base_problem_id"]):
            raise RuntimeError(f"Result is outside frozen screen: {path}")
        rows.append(row)
    rows.sort(key=lambda row: int(row["screen_order"]))
    if len({str(row["example_id"]) for row in rows}) != len(rows):
        raise RuntimeError("Duplicate generated example results")
    write_jsonl(OUT / "cohort/raw_outcome_manifest.jsonl", rows)
    write_jsonl(OUT / "prospective_generation/completed_correct_pool.jsonl", [row for row in rows if row["status"] == "correct"])
    status = Counter(str(row["status"]) for row in rows)
    normal = sum(bool(row["normal_termination"]) for row in rows)
    counts = {
        "attempted": len(rows),
        "completed": normal,
        "correct": status["correct"],
        "wrong": status["wrong"],
        "truncated": status["truncated"],
        "invalid": status["invalid"],
        "correct_with_at_least_160_total_generated_tokens": sum(row["status"] == "correct" and int(row["generated_token_count"]) >= 160 for row in rows),
        "long_enough": 0,
        "multi_segment": 0,
        "multi_event": 0,
        "edit_valid": 0,
        "ROI_valid": 0,
        "retained": 0,
        "initial_budget": 600,
        "maximum_budget": 1_000,
        "status": "initial_generation_complete" if len(rows) == 600 else "initial_generation_in_progress",
    }
    write_json(OUT / "cohort/screening_accounting.json", counts)
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
