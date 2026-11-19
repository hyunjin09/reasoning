#!/usr/bin/env python3
"""Collect the seven frozen applicability-expansion generation outcomes."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage3b8.evaluation import evaluate_mathverse_response


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9/prospective_generation"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    frozen = []
    for path in sorted((ROOT / "outputs/stage3b9/config/generation_applicability_expansion_shards").glob("shard_*.jsonl")):
        frozen.extend(read_jsonl(path))
    by_base = {str(row["base_problem_id"]): row for row in frozen}
    paths = sorted((OUT / "raw").glob("applicability_expansion_*/examples/*/result.json"))
    if len(frozen) != 7 or len(paths) != 7:
        raise RuntimeError(f"Expansion generation is incomplete: frozen={len(frozen)}, results={len(paths)}")
    outcomes, overlays = [], []
    for path in paths:
        raw = read_json(path)
        base = str(raw["base_problem_id"])
        expected = by_base[base]
        if str(raw["example_id"]) != str(expected["example_id"]):
            raise RuntimeError(f"Identity mismatch for base {base}")
        generation_path = path.parent / "generation.json"
        generation_bytes = generation_path.read_bytes()
        generation = json.loads(generation_bytes)
        evaluation = evaluate_mathverse_response(str(generation["full_generated_response"]), str(raw["ground_truth_answer"]))
        status = "truncated" if raw["truncated"] else ("invalid" if not raw["complete"] else ("correct" if evaluation["correct"] else "wrong"))
        overlays.append({
            "base_problem_id": base, "example_id": str(raw["example_id"]),
            "raw_result_path": str(path.relative_to(ROOT)), "generation_path": str(generation_path.relative_to(ROOT)),
            "generation_sha256": hashlib.sha256(generation_bytes).hexdigest(),
            "legacy_evaluator": {"status": raw["status"], "extracted_final_answer": raw["extracted_final_answer"]},
            "mathverse_evaluator": evaluation, "effective_status": status,
            "generation_or_token_ids_modified": False,
        })
        outcomes.append({**raw, "cohort_source": "applicability_repair_expansion", "legacy_status": raw["status"],
            "legacy_extracted_final_answer": raw["extracted_final_answer"], "status": status,
            "correct": status == "correct", "extracted_final_answer": evaluation["predicted_answer"],
            "outcome_reclassification": "outputs/stage3b9/prospective_generation/applicability_expansion_reclassification.jsonl"})
    outcomes.sort(key=lambda row: int(row["base_problem_id"])); overlays.sort(key=lambda row: int(row["base_problem_id"]))
    write_jsonl(OUT / "applicability_expansion_reclassification.jsonl", overlays)
    write_jsonl(OUT / "applicability_expansion_raw_outcomes.jsonl", outcomes)
    correct = [row for row in outcomes if row["status"] == "correct"]
    write_jsonl(OUT / "applicability_expansion_completed_correct.jsonl", correct)
    counts = {status: sum(row["status"] == status for row in outcomes) for status in ("correct", "wrong", "truncated", "invalid")}
    summary = {"created_at": datetime.now(timezone.utc).isoformat(), "frozen_count": 7, "observed_count": len(outcomes),
        "counts": counts, "completed_correct_base_problem_ids": [str(row["base_problem_id"]) for row in correct],
        "all_raw_outcomes_preserved": True, "raw_generations_modified": False,
        "attention_used_for_selection": False, "new_base_value_or_projected_rank_outcomes_used_for_selection": False,
        "evaluation_errors": sum(row["mathverse_evaluator"]["evaluation_error"] is not None for row in overlays)}
    write_json(OUT / "applicability_expansion_summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
