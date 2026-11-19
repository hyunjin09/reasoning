#!/usr/bin/env python3
"""Reclassify and collect the frozen Stage 3B.9 prospective generations."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text
from visual_reasoning.stage3b8.evaluation import evaluate_mathverse_response


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9/prospective_generation"
RAW = OUT / "raw"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    frozen = []
    for path in sorted((ROOT / "outputs/stage3b9/config/generation_shards").glob("shard_*.jsonl")):
        frozen.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    if len(frozen) != 51 or len({str(row["base_problem_id"]) for row in frozen}) != 51:
        raise RuntimeError("Expected the frozen 51-example generation cohort")
    by_base = {str(row["base_problem_id"]): row for row in frozen}
    result_paths = sorted(RAW.glob("shard_*/examples/*/result.json"))
    if len(result_paths) != len(frozen):
        raise RuntimeError(f"Prospective generation is incomplete: {len(result_paths)}/{len(frozen)} examples")
    overlays, outcomes = [], []
    for result_path in result_paths:
        raw = read_json(result_path)
        base = str(raw["base_problem_id"])
        if base not in by_base:
            raise RuntimeError(f"Unfrozen generation base: {base}")
        generation_path = result_path.parent / "generation.json"
        generation_bytes = generation_path.read_bytes()
        generation = json.loads(generation_bytes)
        evaluation = evaluate_mathverse_response(
            str(generation["full_generated_response"]), str(raw["ground_truth_answer"])
        )
        if raw["truncated"]:
            status = "truncated"
        elif not raw["complete"]:
            status = "invalid"
        else:
            status = "correct" if evaluation["correct"] else "wrong"
        overlay = {
            "base_problem_id": base,
            "example_id": str(raw["example_id"]),
            "phase": raw["phase"],
            "raw_result_path": str(result_path.relative_to(ROOT)),
            "generation_path": str(generation_path.relative_to(ROOT)),
            "generation_sha256": hashlib.sha256(generation_bytes).hexdigest(),
            "legacy_evaluator": {
                "status": raw["status"],
                "extracted_final_answer": raw["extracted_final_answer"],
            },
            "numeric_mathverse_evaluator": evaluation,
            "effective_status": status,
            "effective_correct": status == "correct",
            "generation_or_token_ids_modified": False,
        }
        overlays.append(overlay)
        outcomes.append({
            **raw,
            "legacy_status": raw["status"],
            "legacy_extracted_final_answer": raw["extracted_final_answer"],
            "status": status,
            "correct": status == "correct",
            "extracted_final_answer": evaluation["predicted_answer"],
            "outcome_reclassification": "outputs/stage3b9/prospective_generation/outcome_reclassification.jsonl",
        })
    overlays.sort(key=lambda row: int(row["base_problem_id"]))
    outcomes.sort(key=lambda row: int(row["base_problem_id"]))
    if len({str(row["base_problem_id"]) for row in outcomes}) != 51:
        raise RuntimeError("Duplicate or missing Stage 3B.9 prospective result")
    ensure_directory(OUT)
    write_jsonl(OUT / "outcome_reclassification.jsonl", overlays)
    write_jsonl(OUT / "raw_outcome_manifest.jsonl", outcomes)
    for phase in ("phase_a", "phase_b"):
        phase_rows = [row for row in outcomes if row["phase"] == phase and row["status"] == "correct"]
        write_jsonl(OUT / f"{phase}_completed_correct_pool.jsonl", phase_rows)
    counts = {
        phase: {
            status: sum(row["phase"] == phase and row["status"] == status for row in outcomes)
            for status in ("correct", "wrong", "truncated", "invalid")
        }
        for phase in ("phase_a", "phase_b")
    }
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "frozen_count": 51,
        "observed_count": len(outcomes),
        "counts_by_phase": counts,
        "all_raw_outcomes_preserved": True,
        "raw_generations_modified": False,
        "attention_used_for_selection": False,
        "value_vectors_or_causal_scores_used_for_selection": False,
        "numeric_evaluation_errors": sum(row["numeric_mathverse_evaluator"]["evaluation_error"] is not None for row in overlays),
    }
    write_json(OUT / "generation_collection_summary.json", summary)
    write_text(
        OUT / "outcome_reclassification.md",
        "# Stage 3B.9 prospective outcome reclassification\n\n"
        "The raw runner retains the historical A--E extractor. This non-destructive overlay applies the "
        "Stage 3B.8 free-response MathVerse numeric/symbolic evaluator, preserving every raw generation, "
        "token ID, runtime, and legacy status.\n\n"
        f"- Phase A correct/wrong/truncated/invalid: {counts['phase_a']['correct']}/"
        f"{counts['phase_a']['wrong']}/{counts['phase_a']['truncated']}/{counts['phase_a']['invalid']}\n"
        f"- Phase B correct/wrong/truncated/invalid: {counts['phase_b']['correct']}/"
        f"{counts['phase_b']['wrong']}/{counts['phase_b']['truncated']}/{counts['phase_b']['invalid']}\n",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
