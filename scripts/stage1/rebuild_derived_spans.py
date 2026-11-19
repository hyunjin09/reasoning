#!/usr/bin/env python3
"""Rebuild Stage 1 span-derived artifacts without rerunning model inference."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage0.io import write_json
from visual_reasoning.stage1.analysis import aggregate_spans, build_spans, candidate_visual_peaks


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument(
        "--reason",
        default=(
            "Apply the Stage 1 text-only semantic/segmentation rules uniformly: exclude generic "
            "'figure out'/'let's see' from VISUAL_READ, recognize standalone final option letters, "
            "and avoid splitting common abbreviations."
        ),
    )
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    manifest = read_jsonl(run_dir / "manifest.jsonl")
    rebuilt: list[dict[str, Any]] = []
    for manifest_row in manifest:
        example_id = str(manifest_row["example_id"])
        example_dir = run_dir / "examples" / example_id
        token_rows = read_jsonl(example_dir / "tokens.jsonl")
        spans = build_spans(token_rows)
        with np.load(example_dir / "attention_summary.npz") as stored:
            attention = {name: stored[name] for name in stored.files}
        span_arrays = aggregate_spans(spans, token_rows, attention)
        peaks = candidate_visual_peaks(spans)

        generation = read_json(example_dir / "generation.json")
        generation["candidate_visual_peaks"] = peaks
        result = read_json(example_dir / "result.json")
        original_span_count = int(result["span_count"])
        original_peak_count = int(result["candidate_visual_peak_count"])
        result["span_count"] = len(spans)
        result["candidate_visual_peak_count"] = int(peaks["peak_count"])
        validation = read_json(example_dir / "instrumentation_validation.json")
        validation["span_statistics_present"] = span_arrays["span_ranges"].shape[0] == len(spans)
        validation["passed"] = all(
            bool(validation[name])
            for name in (
                "visual_mapping_passed",
                "decoded_text_reconstructs",
                "alignment_passed",
                "normalized_source_statistics_present",
                "visual_focus_present",
                "uncertainty_present",
                "span_statistics_present",
            )
        ) and bool(validation["attention"]["passed"])
        result["validation"] = validation

        write_json(example_dir / "spans.json", spans)
        write_json(example_dir / "candidate_visual_peaks.json", peaks)
        np.savez_compressed(example_dir / "span_signals.npz", **span_arrays)
        write_json(example_dir / "generation.json", generation)
        write_json(example_dir / "instrumentation_validation.json", validation)
        write_json(example_dir / "result.json", result)
        rebuilt.append(
            {
                "example_id": example_id,
                "generated_token_count": len(token_rows),
                "original_span_count": original_span_count,
                "span_count": len(spans),
                "original_candidate_visual_peak_count": original_peak_count,
                "candidate_visual_peak_count": int(peaks["peak_count"]),
            }
        )
    write_json(
        run_dir / "derived_span_rebuild.json",
        {
            "reason": args.reason,
            "semantic_label_definition": "stage1_text_rules_v2",
            "candidate_peak_definition": "stage1_prominence_v2_token_midpoint",
            "candidate_peak_position_definition": "peak span token midpoint / total generated tokens",
            "inference_rerun": False,
            "raw_tokens_changed": False,
            "attention_arrays_changed": False,
            "generation_token_ids_changed": False,
            "statuses_changed": False,
            "rebuilt_examples": rebuilt,
        },
    )
    print(json.dumps({"rebuilt": len(rebuilt), "run_dir": str(run_dir)}, indent=2))


if __name__ == "__main__":
    main()
