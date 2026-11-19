#!/usr/bin/env python3
"""Validate saved Stage 0 outputs without loading the model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage0.io import write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    return parser.parse_args()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_example(example_dir: Path, mode: str) -> dict[str, Any]:
    required = [
        "input.json",
        "generation.json",
        "tokens.jsonl",
        "spans.json",
        "attention_summary.npz",
        "instrumentation_validation.json",
        "result.json",
    ]
    if mode == "smoke":
        required.extend(("baseline_generation.json", "faithfulness.json"))
    missing = [name for name in required if not (example_dir / name).is_file()]
    if missing:
        raise AssertionError(f"{example_dir.name}: missing {missing}")

    input_record = read_json(example_dir / "input.json")
    generation = read_json(example_dir / "generation.json")
    spans = read_json(example_dir / "spans.json")
    validation = read_json(example_dir / "instrumentation_validation.json")
    result = read_json(example_dir / "result.json")
    token_rows = [json.loads(line) for line in (example_dir / "tokens.jsonl").read_text(encoding="utf-8").splitlines()]
    arrays = np.load(example_dir / "attention_summary.npz", allow_pickle=False)

    token_count = int(generation["generated_token_count"])
    if len(token_rows) != token_count:
        raise AssertionError(f"{example_dir.name}: token row count mismatch")
    if "".join(str(row["decoded_token"]) for row in token_rows) != generation["raw_decoded_response"]:
        raise AssertionError(f"{example_dir.name}: decoded token text does not reconstruct the raw response")
    if arrays["modality_by_layer"].shape[0] != token_count:
        raise AssertionError(f"{example_dir.name}: modality step count mismatch")
    if arrays["visual_focus"].shape != (token_count, len(input_record["visual_token_indices"])):
        raise AssertionError(f"{example_dir.name}: visual focus shape mismatch")
    if arrays["modality_by_layer"].ndim != 3 or arrays["modality_by_layer"].shape[-1] != 3:
        raise AssertionError(f"{example_dir.name}: invalid modality array shape")
    if arrays["selected_head_mass"].ndim != 4 or arrays["selected_head_mass"].shape[-1] != 3:
        raise AssertionError(f"{example_dir.name}: invalid selected-head shape")
    if not np.isfinite(arrays["modality_by_layer"]).all():
        raise AssertionError(f"{example_dir.name}: non-finite attention mass")
    maximum_mass_error = float(np.abs(arrays["modality_by_layer"].sum(axis=-1) - 1.0).max())
    if maximum_mass_error > 0.01:
        raise AssertionError(f"{example_dir.name}: modality mass error {maximum_mass_error}")
    if not all(
        0 <= int(span["start_token"]) < int(span["end_token"]) <= token_count
        for span in spans
    ):
        raise AssertionError(f"{example_dir.name}: invalid span range")
    if not all(bool(value) for value in generation["alignment"].values()):
        raise AssertionError(f"{example_dir.name}: generation alignment failed")
    if not validation["attention"]["passed"]:
        raise AssertionError(f"{example_dir.name}: attention validation failed")
    if mode == "smoke" and not read_json(example_dir / "faithfulness.json")["passed"]:
        raise AssertionError(f"{example_dir.name}: faithfulness failed")
    return {
        "example_id": example_dir.name,
        "token_count": token_count,
        "span_count": len(spans),
        "maximum_modality_mass_error": maximum_mass_error,
        "status": result["status"],
    }


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    required_root = [
        "config.json",
        "environment.md",
        "dataset_report.md",
        "dataset_inventory.json",
        "model_report.md",
        "instrumentation.md",
        "summaries/stage0_summary.json",
        "summaries/stage0_summary.md",
    ]
    missing = [name for name in required_root if not (output_dir / name).is_file()]
    if missing:
        raise AssertionError(f"Missing root outputs: {missing}")
    config = read_json(output_dir / "config.json")
    summary = read_json(output_dir / "summaries" / "stage0_summary.json")
    mode = str(config["run_signature"]["mode"])
    example_dirs = sorted(
        [path for path in (output_dir / "examples").iterdir() if path.is_dir()],
        key=lambda path: int(path.name) if path.name.isdigit() else path.name,
    )
    expected = int(config["run_signature"]["num_examples"])
    if len(example_dirs) != expected:
        raise AssertionError(f"Expected {expected} example directories, found {len(example_dirs)}")
    examples = [validate_example(path, mode) for path in example_dirs]
    if int(summary["examples_processed"]) != expected:
        raise AssertionError("Summary example count mismatch")
    if summary.get("stage1_started") is not False:
        raise AssertionError("Stage 1 boundary was not preserved")
    if mode == "smoke" and not summary.get("smoke_gate_passed"):
        raise AssertionError("Smoke gate did not pass")
    if mode == "full":
        if not 30 <= expected <= 50:
            raise AssertionError("Full Stage 0 count is outside 30–50")
        if not summary.get("stage0_pass"):
            raise AssertionError("Full Stage 0 acceptance criteria did not pass")
        if not all(bool(item["passed"]) for item in summary["acceptance_criteria"]):
            raise AssertionError("At least one final acceptance criterion failed")

    report = {
        "passed": True,
        "mode": mode,
        "examples_validated": len(examples),
        "maximum_modality_mass_error": max(item["maximum_modality_mass_error"] for item in examples),
        "stage0_pass": bool(summary.get("stage0_pass")),
        "smoke_gate_passed": bool(summary.get("smoke_gate_passed")),
        "stage1_started": False,
        "examples": examples,
    }
    if args.report:
        write_json(args.report, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
