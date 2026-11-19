#!/usr/bin/env python3
"""Independently validate aggregated Stage 1A.2 protocol-comparison artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage0.analysis import extract_answer
from visual_reasoning.stage0.io import write_json
from visual_reasoning.stage1.protocol import protocol_run_metrics, repetition_diagnostics


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--condition-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.condition_root.resolve()
    summary = read_json(root / "run_summary.json")
    outcome_rows = read_jsonl(root / "raw_outcome_manifest.jsonl")
    failures: list[str] = []
    results: list[dict[str, Any]] = []
    require(len(outcome_rows) == 10, "Expected ten aggregate outcome rows", failures)
    require(len({str(row["example_id"]) for row in outcome_rows}) == len(outcome_rows), "Duplicate example IDs", failures)
    for outcome in outcome_rows:
        example_id = str(outcome["example_id"])
        example_dir = Path(outcome["artifact_dir"])
        for name in ("input.json", "generation.json", "tokens.jsonl", "repetition_diagnostics.json", "result.json"):
            require((example_dir / name).is_file(), f"{example_id}: missing {name}", failures)
        if failures and not (example_dir / "result.json").is_file():
            continue
        generation = read_json(example_dir / "generation.json")
        tokens = read_jsonl(example_dir / "tokens.jsonl")
        repetition = read_json(example_dir / "repetition_diagnostics.json")
        result = read_json(example_dir / "result.json")
        token_count = int(result["generated_token_count"])
        require(token_count == len(tokens), f"{example_id}: token row mismatch", failures)
        require(token_count == len(generation["generated_token_ids"]), f"{example_id}: token ID mismatch", failures)
        require("".join(str(row["decoded_token"]) for row in tokens) == generation["raw_decoded_response"], f"{example_id}: decode mismatch", failures)
        require(token_count <= 40_960, f"{example_id}: safety ceiling exceeded", failures)
        require(result["status"] == outcome["status"] == generation["status"], f"{example_id}: status mismatch", failures)
        require(bool(result["normal_termination"]) == (token_count < 40_960), f"{example_id}: termination mismatch", failures)
        if token_count == 40_960:
            require(result["status"] == "truncated", f"{example_id}: cap hit not truncated", failures)
        if result["status"] in {"correct", "wrong"}:
            require(extract_answer(generation["full_generated_response"]) is not None, f"{example_id}: completed answer absent", failures)
        recomputed_repetition = repetition_diagnostics(generation["full_generated_response"])
        require(repetition == recomputed_repetition, f"{example_id}: repetition diagnostics not reproducible", failures)
        require(bool(result["repetition"]["any_pathology_flag"]) == bool(repetition["any_pathology_flag"]), f"{example_id}: repetition flag mismatch", failures)
        results.append(result)
    recomputed = protocol_run_metrics(results, 40_960) if results else {}
    for name, value in recomputed.items():
        if name == "per_example":
            continue
        if isinstance(value, float):
            require(np.isclose(float(summary[name]), value), f"Summary mismatch: {name}", failures)
        else:
            require(summary[name] == value, f"Summary mismatch: {name}", failures)
    report = {
        "passed": not failures,
        "condition": summary.get("condition"),
        "validated_examples": len(results),
        "recomputed_metrics": recomputed,
        "failures": failures,
    }
    write_json(args.output.resolve(), report)
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
