#!/usr/bin/env python3
"""Collect and validate all Stage 3B.7R prospective generation outcomes."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b7r/validation_cohort"
RAW = OUT / "generation_raw"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    expected = read_jsonl(OUT / "prospective_generation_eligible.jsonl")
    expected_by_base = {str(row["base_problem_id"]): row for row in expected}
    if len(expected) != 16 or len(expected_by_base) != 16:
        raise RuntimeError("Frozen prospective set is not exactly 16 unique bases")
    results = []
    for shard in (RAW / "shard_00", RAW / "shard_01"):
        summary = read_json(shard / "result.json")
        config = read_json(shard / "config.json")["run_signature"]
        expected_protocol = {
            "do_sample": True,
            "temperature": 0.6,
            "top_p": 0.95,
            "top_k": 20,
            "repetition_penalty": 1.0,
            "presence_penalty": 0.0,
            "max_new_tokens": 40960,
            "seed": 1234,
        }
        if config["protocol"] != expected_protocol or config["required_gpu_class"] != "NVIDIA RTX A5000":
            raise RuntimeError(f"Locked protocol mismatch in {shard}")
        if summary["total"] != len(summary["results"]) or not summary["all_raw_outcomes_preserved"]:
            raise RuntimeError(f"Incomplete raw outcomes in {shard}")
        results.extend(summary["results"])
    results.sort(key=lambda row: int(row["base_problem_id"]))
    observed = {str(row["base_problem_id"]) for row in results}
    if len(results) != 16 or observed != set(expected_by_base):
        raise RuntimeError(f"Observed generation set mismatch: rows={len(results)}")
    for row in results:
        expected_row = expected_by_base[str(row["base_problem_id"])]
        if str(row["example_id"]) != str(expected_row["example_id"]):
            raise RuntimeError(f"Example mismatch for base {row['base_problem_id']}")
    completed_correct = [row for row in results if row["status"] == "correct"]
    summary = {
        "total": len(results),
        "correct": sum(row["status"] == "correct" for row in results),
        "wrong": sum(row["status"] == "wrong" for row in results),
        "truncated": sum(row["status"] == "truncated" for row in results),
        "invalid": sum(row["status"] == "invalid" for row in results),
        "completed_correct_pending_strict_E_d": len(completed_correct),
        "minimum_validation_size": 12,
        "minimum_generation_yield_met": len(completed_correct) >= 12,
        "all_raw_outcomes_preserved": len(results) == 16,
        "attention_used_for_selection": False,
        "causal_scores_exist_or_were_inspected": False,
    }
    write_jsonl(OUT / "raw_outcome_manifest.jsonl", results)
    write_jsonl(OUT / "completed_correct_pending_strict_ed.jsonl", completed_correct)
    write_json(OUT / "generation_collection_summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
