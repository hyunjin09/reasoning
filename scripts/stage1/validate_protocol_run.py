#!/usr/bin/env python3
"""Independently validate a completed Stage 1 protocol-run artifact tree."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage0.io import write_json


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def validate_example(example_dir: Path, expected_id: str, cap: int) -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    required = (
        "input.json",
        "generation.json",
        "tokens.jsonl",
        "spans.json",
        "candidate_visual_peaks.json",
        "attention_summary.npz",
        "uncertainty.npz",
        "span_signals.npz",
        "instrumentation_validation.json",
        "result.json",
    )
    for name in required:
        require((example_dir / name).is_file(), f"{expected_id}: missing {name}", failures)
    if failures:
        return {}, failures

    input_record = read_json(example_dir / "input.json")
    generation = read_json(example_dir / "generation.json")
    tokens = read_jsonl(example_dir / "tokens.jsonl")
    spans = read_json(example_dir / "spans.json")
    peaks = read_json(example_dir / "candidate_visual_peaks.json")
    validation = read_json(example_dir / "instrumentation_validation.json")
    result = read_json(example_dir / "result.json")
    token_count = int(generation["generated_token_count"])
    visual_count = len(input_record["visual_token_indices"])

    require(str(result["example_id"]) == expected_id, f"{expected_id}: result ID mismatch", failures)
    require(str(input_record["example_id"]) == expected_id, f"{expected_id}: input ID mismatch", failures)
    require(token_count == len(tokens), f"{expected_id}: token-row count mismatch", failures)
    require(token_count == len(generation["generated_token_ids"]), f"{expected_id}: token-ID count mismatch", failures)
    require(token_count == int(result["generated_token_count"]), f"{expected_id}: result token count mismatch", failures)
    require(token_count <= cap, f"{expected_id}: generation exceeds cap", failures)
    require(generation["status"] == result["status"], f"{expected_id}: status mismatch", failures)
    require(bool(generation["complete"]) == bool(result["complete"]), f"{expected_id}: completion mismatch", failures)
    require(bool(generation["correct"]) == bool(result["correct"]), f"{expected_id}: correctness mismatch", failures)
    require(bool(validation["passed"]), f"{expected_id}: instrumentation validation failed", failures)
    require(bool(result["validation"]["passed"]), f"{expected_id}: copied validation failed", failures)
    require(
        "".join(str(row["decoded_token"]) for row in tokens) == generation["raw_decoded_response"],
        f"{expected_id}: decoded-token reconstruction mismatch",
        failures,
    )

    if token_count == cap:
        require(generation["status"] == "truncated", f"{expected_id}: cap hit not classified truncated", failures)
        require(not bool(generation["complete"]), f"{expected_id}: cap hit classified complete", failures)
    if bool(generation["complete"]):
        require(token_count < cap, f"{expected_id}: complete trace did not terminate before cap", failures)
        require(generation["status"] in {"correct", "wrong"}, f"{expected_id}: invalid complete status", failures)
        require(generation["extracted_final_answer"] is not None, f"{expected_id}: complete trace lacks answer", failures)

    expected_start = 0
    for index, span in enumerate(spans):
        require(int(span["span_id"]) == index, f"{expected_id}: nonsequential span ID", failures)
        require(int(span["start_token"]) == expected_start, f"{expected_id}: span coverage gap/overlap", failures)
        require(int(span["end_token"]) > int(span["start_token"]), f"{expected_id}: empty span", failures)
        require(
            span["semantic_label"]
            in {"VISUAL_READ", "COMPUTE", "RELATION_INFERENCE", "VERIFY", "PLAN", "ANSWER_SELECTION", "OTHER"},
            f"{expected_id}: unknown semantic label",
            failures,
        )
        expected_start = int(span["end_token"])
    require(expected_start == token_count, f"{expected_id}: spans do not cover token sequence", failures)
    require(len(spans) == int(result["span_count"]), f"{expected_id}: span count mismatch", failures)
    require(int(peaks["span_count"]) == len(spans), f"{expected_id}: peak span count mismatch", failures)
    require(int(peaks["peak_count"]) == len(peaks["peaks"]), f"{expected_id}: peak count malformed", failures)
    require(int(peaks["peak_count"]) == int(result["candidate_visual_peak_count"]), f"{expected_id}: result peak count mismatch", failures)

    with np.load(example_dir / "attention_summary.npz") as attention:
        require(attention["modality_by_layer"].shape[0] == token_count, f"{expected_id}: attention token axis mismatch", failures)
        require(attention["modality_by_layer"].shape[-1] == 3, f"{expected_id}: attention source axis mismatch", failures)
        require(attention["modality_density_by_layer"].shape == attention["modality_by_layer"].shape, f"{expected_id}: density shape mismatch", failures)
        require(attention["source_token_counts"].shape == (token_count, 3), f"{expected_id}: source-count shape mismatch", failures)
        require(attention["visual_focus"].shape == (token_count, visual_count), f"{expected_id}: visual-focus shape mismatch", failures)
        require(np.isfinite(attention["modality_by_layer"]).all(), f"{expected_id}: nonfinite attention mass", failures)
        require(np.isfinite(attention["modality_density_by_layer"]).all(), f"{expected_id}: nonfinite attention density", failures)
    with np.load(example_dir / "uncertainty.npz") as uncertainty:
        for name in ("entropy", "top1_probability", "top1_top2_margin"):
            require(uncertainty[name].shape == (token_count,), f"{expected_id}: {name} shape mismatch", failures)
            require(np.isfinite(uncertainty[name]).all(), f"{expected_id}: nonfinite {name}", failures)
    with np.load(example_dir / "span_signals.npz") as span_signals:
        require(span_signals["span_ranges"].shape == (len(spans), 2), f"{expected_id}: span-range shape mismatch", failures)
        require(span_signals["modality_mass_by_span_layer"].shape[0] == len(spans), f"{expected_id}: span mass count mismatch", failures)
        require(span_signals["modality_density_by_span_layer"].shape == span_signals["modality_mass_by_span_layer"].shape, f"{expected_id}: span density shape mismatch", failures)
        require(span_signals["visual_focus_distribution"].shape == (len(spans), visual_count), f"{expected_id}: span focus shape mismatch", failures)
        require(span_signals["uncertainty_by_span"].shape == (len(spans), 3, 3), f"{expected_id}: span uncertainty shape mismatch", failures)
    return result, failures


def recompute_summary(results: list[dict[str, Any]], cap: int) -> dict[str, Any]:
    lengths = np.asarray([int(item["generated_token_count"]) for item in results], dtype=np.int64)
    latencies = np.asarray([float(item["runtime"]["elapsed_seconds"]) for item in results], dtype=np.float64)
    completed = [item for item in results if bool(item["complete"])]
    truncated = [item for item in results if item["status"] == "truncated"]
    return {
        "max_new_tokens": cap,
        "total": len(results),
        "completed": len(completed),
        "completion_rate": len(completed) / len(results),
        "truncated": len(truncated),
        "truncation_rate": len(truncated) / len(results),
        "correct": sum(item["status"] == "correct" for item in results),
        "wrong": sum(item["status"] == "wrong" for item in results),
        "invalid": sum(item["status"] == "invalid" for item in results),
        "correctness_among_completed": sum(item["status"] == "correct" for item in completed) / len(completed) if completed else 0.0,
        "median_generation_length": float(np.median(lengths)),
        "p90_generation_length": float(np.percentile(lengths, 90)),
        "maximum_generation_length": int(lengths.max()),
        "median_latency_seconds": float(np.median(latencies)),
        "p90_latency_seconds": float(np.percentile(latencies, 90)),
        "peak_gpu_allocated_bytes": max(int(item["runtime"]["peak_gpu_allocated_bytes"]) for item in results),
        "maximum_artifact_bytes": max(int(item["output_bytes"]) for item in results),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    manifest = read_jsonl(run_dir / "manifest.jsonl")
    summary = read_json(run_dir / "run_summary.json")
    cap = int(summary["max_new_tokens"])
    failures: list[str] = []
    results: list[dict[str, Any]] = []
    expected_ids = [str(item["example_id"]) for item in manifest]
    actual_ids = sorted(path.name for path in (run_dir / "examples").iterdir() if path.is_dir())
    require(set(actual_ids) == set(expected_ids), "Example-directory IDs do not match manifest", failures)
    for example_id in expected_ids:
        result, example_failures = validate_example(run_dir / "examples" / example_id, example_id, cap)
        failures.extend(example_failures)
        if result:
            results.append(result)
    recomputed = recompute_summary(results, cap) if results else {}
    for name, value in recomputed.items():
        if name in {"completion_rate", "truncation_rate", "correctness_among_completed", "median_generation_length", "p90_generation_length", "median_latency_seconds", "p90_latency_seconds"}:
            require(np.isclose(float(summary[name]), float(value)), f"Summary mismatch: {name}", failures)
        else:
            require(summary[name] == value, f"Summary mismatch: {name}", failures)
    require(bool(summary["all_instrumentation_valid"]), "Run summary says instrumentation is invalid", failures)
    report = {
        "passed": not failures,
        "run_dir": str(run_dir),
        "manifest_count": len(manifest),
        "validated_example_count": len(results),
        "recomputed_metrics": recomputed,
        "failures": failures,
    }
    write_json(args.output.resolve(), report)
    print(json.dumps(report, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
