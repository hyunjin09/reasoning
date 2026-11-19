#!/usr/bin/env python3
"""Create a non-destructive Stage 3B.8 discovery outcome overlay."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl, write_text
from visual_reasoning.stage3b8.evaluation import evaluate_mathverse_response


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b8/discovery_cohort"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    roots = [OUT / "generation_raw/batch1", OUT / "generation_raw/batch2_active"]
    held = OUT / "generation_raw/batch2_held"
    if all((held / f"shard_{rank:02d}/result.json").is_file() for rank in range(2)):
        roots.append(held)
    rows = []
    for root in roots:
        for result_path in sorted(root.glob("shard_*/examples/*/result.json")):
            raw = read_json(result_path)
            generation_path = result_path.parent / "generation.json"
            generation_bytes = generation_path.read_bytes()
            generation = json.loads(generation_bytes)
            evaluation = evaluate_mathverse_response(
                str(generation["full_generated_response"]),
                str(raw["ground_truth_answer"]),
            )
            hit_cap = bool(raw["truncated"])
            effective_status = "truncated" if hit_cap else ("correct" if evaluation["correct"] else "wrong")
            rows.append({
                "base_problem_id": str(raw["base_problem_id"]),
                "example_id": str(raw["example_id"]),
                "raw_result_path": str(result_path.relative_to(ROOT)),
                "generation_path": str(generation_path.relative_to(ROOT)),
                "generation_sha256": hashlib.sha256(generation_bytes).hexdigest(),
                "legacy_evaluator": {
                    "status": raw["status"],
                    "extracted_final_answer": raw["extracted_final_answer"],
                },
                "stage3b8_evaluator": evaluation,
                "effective_status": effective_status,
                "effective_correct": effective_status == "correct",
                "generation_or_token_ids_modified": False,
            })
    rows.sort(key=lambda row: int(row["base_problem_id"]))
    write_jsonl(OUT / "outcome_reclassification.jsonl", rows)
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "count": len(rows),
        "correct": sum(row["effective_status"] == "correct" for row in rows),
        "wrong": sum(row["effective_status"] == "wrong" for row in rows),
        "truncated": sum(row["effective_status"] == "truncated" for row in rows),
        "legacy_status_changes": sum(row["effective_status"] != row["legacy_evaluator"]["status"] for row in rows),
        "evaluation_errors": sum(row["stage3b8_evaluator"]["evaluation_error"] is not None for row in rows),
        "raw_generations_modified": False,
    }
    write_json(OUT / "outcome_reclassification_summary.json", summary)
    write_text(
        OUT / "outcome_reclassification.md",
        "# Stage 3B.8 discovery outcome reclassification\n\n"
        "The locked Stage 0 evaluator is an A--E multiple-choice extractor. The prospective Stage 3B.8 "
        "screen includes free-response numeric MathVerse items, for which that extractor can return incidental "
        "letters (for example `C` from circumference). This overlay uses the last balanced `\\boxed{...}` "
        "expression and symbolic/numeric equivalence for free-response ground truth, while retaining the original "
        "A--E evaluator for choice items. It does not alter generated tokens, text, runtime records, or raw statuses.\n\n"
        f"- rows: {summary['count']}\n"
        f"- effective correct/wrong/truncated: {summary['correct']}/{summary['wrong']}/{summary['truncated']}\n"
        f"- legacy status changes: {summary['legacy_status_changes']}\n"
        f"- evaluation errors requiring manual review: {summary['evaluation_errors']}\n",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
