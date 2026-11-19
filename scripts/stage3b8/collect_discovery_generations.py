#!/usr/bin/env python3
"""Collect all completed Stage 3B.8 discovery-generation batches."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b8/discovery_cohort"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    batches = {
        "batch1": OUT / "generation_raw/batch1",
        "batch2_active": OUT / "generation_raw/batch2_active",
    }
    held_root = OUT / "generation_raw/batch2_held"
    if all((held_root / f"shard_{rank:02d}/result.json").is_file() for rank in range(2)):
        batches["batch2_held"] = held_root
    overlay_path = OUT / "outcome_reclassification.jsonl"
    if not overlay_path.is_file():
        raise FileNotFoundError("Run reclassify_discovery_outcomes.py before collection")
    overlay = {
        str(row["base_problem_id"]): row
        for row in [json.loads(line) for line in overlay_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    }
    results = []
    batch_summaries = {}
    for name, root in batches.items():
        summaries = [read_json(root / f"shard_{rank:02d}/result.json") for rank in range(2)]
        batch_rows = [row for summary in summaries for row in summary["results"]]
        if any(not summary["all_raw_outcomes_preserved"] for summary in summaries):
            raise RuntimeError(f"Raw outcomes are incomplete for {name}")
        for row in batch_rows:
            row["generation_batch"] = name
            audit = overlay.get(str(row["base_problem_id"]))
            if audit is None:
                raise RuntimeError(f"Missing outcome reclassification for base {row['base_problem_id']}")
            row["legacy_status"] = row["status"]
            row["legacy_extracted_final_answer"] = row["extracted_final_answer"]
            row["status"] = audit["effective_status"]
            row["correct"] = audit["effective_correct"]
            row["extracted_final_answer"] = audit["stage3b8_evaluator"]["predicted_answer"]
            row["outcome_reclassification"] = str(overlay_path.relative_to(ROOT))
        results.extend(batch_rows)
        batch_summaries[name] = {
            "total": len(batch_rows),
            "correct": sum(row["status"] == "correct" for row in batch_rows),
            "wrong": sum(row["status"] == "wrong" for row in batch_rows),
            "truncated": sum(row["status"] == "truncated" for row in batch_rows),
            "invalid": sum(row["status"] == "invalid" for row in batch_rows),
        }
    results.sort(key=lambda row: int(row["base_problem_id"]))
    if len({str(row["base_problem_id"]) for row in results}) != len(results):
        raise RuntimeError("Discovery generation contains duplicate base problems")
    completed_correct = [row for row in results if row["status"] == "correct"]
    summary = {
        "total": len(results),
        "correct": len(completed_correct),
        "wrong": sum(row["status"] == "wrong" for row in results),
        "truncated": sum(row["status"] == "truncated" for row in results),
        "invalid": sum(row["status"] == "invalid" for row in results),
        "completed_correct_pending_strict_ed": len(completed_correct),
        "all_raw_outcomes_preserved": True,
        "attention_used_for_selection": False,
        "stage3b8_causal_or_fit_outcomes_exist_or_were_inspected": False,
        "batches": batch_summaries,
    }
    write_jsonl(OUT / "raw_outcome_manifest.jsonl", results)
    write_jsonl(OUT / "completed_correct_pool.jsonl", completed_correct)
    write_json(OUT / "generation_collection_summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
