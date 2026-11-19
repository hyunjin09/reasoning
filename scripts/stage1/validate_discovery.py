#!/usr/bin/env python3
"""Independently validate final Stage 1B manifests, bundles, and reports."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage0.io import write_json
from visual_reasoning.stage1.analysis import build_spans, candidate_visual_peaks
from visual_reasoning.stage1.protocol import repetition_diagnostics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--discovery-dir", type=Path, required=True)
    parser.add_argument("--attempt-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> None:
    args = parse_args()
    root = args.discovery_dir.resolve()
    failures: list[str] = []
    attempts = read_jsonl(args.attempt_manifest)
    raw = read_jsonl(root / "raw_outcome_manifest.jsonl")
    cohort = read_jsonl(root / "cohort_manifest.jsonl")
    pairs = read_jsonl(root / "paired_variants" / "pairing_manifest.jsonl")
    expected_ids = {str(row["example_id"]) for row in attempts}
    raw_ids = {str(row["example_id"]) for row in raw}
    cohort_ids = {str(row["example_id"]) for row in cohort}
    require(len(attempts) == 200, f"expected 200 attempts, found {len(attempts)}", failures)
    require(len(raw) == len(attempts), "raw manifest count mismatch", failures)
    require(raw_ids == expected_ids, "raw manifest IDs differ from prospective attempts", failures)
    require(len(pairs) == len(raw), "pairing manifest count mismatch", failures)
    require(cohort_ids == {str(row["example_id"]) for row in raw if row["completed"] and row["correct"]}, "cohort eligibility mismatch", failures)

    shard_dirs = sorted((root / "shards_07").glob("shard_*"))
    require(len(shard_dirs) == 7, f"expected seven execution shards, found {len(shard_dirs)}", failures)
    for shard_dir in shard_dirs:
        config = read_json(shard_dir / "config.json")
        signature = config["run_signature"]
        parameters = signature["parameters"]
        require(signature["protocol"] == "official", f"{shard_dir.name}: protocol is not official", failures)
        require(parameters == {"do_sample": True, "temperature": 0.6, "top_p": 0.95, "top_k": 20, "repetition_penalty": 1.0, "presence_penalty": 0.0, "max_new_tokens": 40960, "seed": 1234}, f"{shard_dir.name}: locked generation parameters differ", failures)
        environment_text = (shard_dir / "environment.md").read_text(encoding="utf-8")
        require("protocol=`official`, sampling enabled" in environment_text, f"{shard_dir.name}: environment protocol line is incorrect", failures)
        rebuild = read_json(shard_dir / "derived_span_rebuild.json")
        require(rebuild.get("semantic_label_definition") == "stage1_text_rules_v2", f"{shard_dir.name}: derived span rebuild version mismatch", failures)
        require(rebuild.get("candidate_peak_definition") == "stage1_prominence_v2_token_midpoint", f"{shard_dir.name}: candidate-peak rebuild version mismatch", failures)

    by_problem: dict[str, set[str]] = defaultdict(set)
    for row in pairs:
        by_problem[str(row["base_problem_id"])].add(str(row["variant"]))
    require(len(by_problem) == 100, f"expected 100 paired base problems, found {len(by_problem)}", failures)
    require(all(variants == {"Vision Intensive", "Vision Dominant"} for variants in by_problem.values()), "incomplete variant pair", failures)

    validated = 0
    for row in raw:
        example_id = str(row["example_id"])
        artifact = Path(row["artifact_dir"])
        required = (
            "input.json",
            "generation.json",
            "tokens.jsonl",
            "spans.json",
            "attention_summary.npz",
            "uncertainty.npz",
            "span_signals.npz",
            "candidate_visual_peaks.json",
            "instrumentation_validation.json",
            "result.json",
        )
        for name in required:
            require((artifact / name).is_file(), f"{example_id}: missing {name}", failures)
        if any(not (artifact / name).is_file() for name in required):
            continue
        generation = read_json(artifact / "generation.json")
        result = read_json(artifact / "result.json")
        token_rows = read_jsonl(artifact / "tokens.jsonl")
        spans = read_json(artifact / "spans.json")
        peaks = read_json(artifact / "candidate_visual_peaks.json")
        instrumentation = read_json(artifact / "instrumentation_validation.json")
        attention = np.load(artifact / "attention_summary.npz", allow_pickle=False)
        uncertainty = np.load(artifact / "uncertainty.npz", allow_pickle=False)
        span_signals = np.load(artifact / "span_signals.npz", allow_pickle=False)
        token_count = int(result["generated_token_count"])
        visual_count = len(read_json(artifact / "input.json")["visual_token_indices"])
        require(token_count == int(generation["generated_token_count"]), f"{example_id}: result/generation length mismatch", failures)
        require(token_count == len(token_rows), f"{example_id}: token-row count mismatch", failures)
        require("".join(str(token["decoded_token"]) for token in token_rows) == generation["raw_decoded_response"], f"{example_id}: token text does not reconstruct response", failures)
        require(str(result["status"]) == str(row["status"]), f"{example_id}: raw/result status mismatch", failures)
        require(bool(instrumentation["passed"]), f"{example_id}: instrumentation validation failed", failures)
        require(attention["modality_by_layer"].shape[0] == token_count, f"{example_id}: attention/token mismatch", failures)
        require(attention["modality_density_by_layer"].shape == attention["modality_by_layer"].shape, f"{example_id}: density shape mismatch", failures)
        require(attention["source_token_counts"].shape == (token_count, 3), f"{example_id}: source-count shape mismatch", failures)
        require(attention["visual_focus"].shape == (token_count, visual_count), f"{example_id}: visual-focus shape mismatch", failures)
        require(uncertainty["entropy"].shape == (token_count,), f"{example_id}: entropy shape mismatch", failures)
        require(span_signals["span_ranges"].shape == (len(spans), 2), f"{example_id}: span-signal shape mismatch", failures)
        ranges = [(int(span["start_token"]), int(span["end_token"])) for span in spans]
        require(bool(ranges) and ranges[0][0] == 0 and ranges[-1][1] == token_count, f"{example_id}: span endpoints do not cover trace", failures)
        require(all(ranges[index][1] == ranges[index + 1][0] for index in range(len(ranges) - 1)), f"{example_id}: span coverage gap/overlap", failures)
        rebuilt = build_spans(token_rows)
        for key in ("span_id", "start_token", "end_token", "span_text", "semantic_label", "lexical_context"):
            require([span[key] for span in spans] == [span[key] for span in rebuilt], f"{example_id}: saved spans are not reproducible for {key}", failures)
        require(peaks == candidate_visual_peaks(spans), f"{example_id}: saved candidate peaks are not reproducible", failures)
        if token_count >= 40960:
            require(str(result["status"]) == "truncated", f"{example_id}: cap hit not classified truncated", failures)
        if str(result["status"]) == "truncated":
            require(token_count >= 40960, f"{example_id}: truncated below safety ceiling", failures)
            repetition_path = artifact / "repetition_diagnostics.json"
            require(repetition_path.is_file(), f"{example_id}: truncated trace lacks repetition diagnostics", failures)
            if repetition_path.is_file():
                require(
                    read_json(repetition_path)
                    == repetition_diagnostics(str(generation["full_generated_response"])),
                    f"{example_id}: repetition diagnostics are not reproducible",
                    failures,
                )
        if example_id in cohort_ids:
            require((artifact / "plots" / "span_timeline.png").is_file(), f"{example_id}: eligible timeline missing", failures)
            require((artifact / "plots" / "descriptive_timeline.json").is_file(), f"{example_id}: eligible timeline data missing", failures)
        validated += 1

    cohort_gate = read_json(root / "cohort_gate.json")
    statistics = read_json(root.parent / "summaries" / "stage1_statistics.json")
    representatives = read_json(root / "representative" / "representative_selection.json") if (root / "representative" / "representative_selection.json").is_file() else {"count": 0}
    manual = read_json(root / "manual_review" / "segmentation_review.json") if (root / "manual_review" / "segmentation_review.json").is_file() else {"reviewed_trajectory_count": 0}
    require(int(cohort_gate["completed_correct"]) == len(cohort), "cohort gate count mismatch", failures)
    require(len(cohort) >= 80, f"minimum discovery cohort not met: {len(cohort)}", failures)
    require(int(representatives.get("count", 0)) >= 10, "fewer than 10 representative trajectories", failures)
    require(int(manual.get("reviewed_trajectory_count", 0)) >= 20, "fewer than 20 manually reviewed segmentations", failures)
    require(bool(manual.get("typical_errors")), "manual segmentation error report is missing", failures)
    require(statistics.get("scientific_boundary") == "raw attention and candidate peaks are descriptive evidence, not causal visual usage", "statistics scientific boundary missing", failures)
    require((root.parent / "summaries" / "stage1_summary.md").is_file(), "stage1_summary.md missing", failures)
    require((root.parent / "summaries" / "candidate_hypotheses.md").is_file(), "candidate_hypotheses.md missing", failures)

    output = {
        "passed": not failures,
        "prospective_attempt_count": len(attempts),
        "raw_outcome_count": len(raw),
        "completed_correct_count": len(cohort),
        "outcome_counts": dict(sorted(Counter(str(row["status"]) for row in raw).items())),
        "validated_bundle_count": validated,
        "paired_base_problem_count": len(by_problem),
        "representative_count": int(representatives.get("count", 0)),
        "manual_segmentation_review_count": int(manual.get("reviewed_trajectory_count", 0)),
        "failures": failures,
    }
    write_json(args.output, output)
    print(json.dumps(output, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
