#!/usr/bin/env python3
"""Run an uninstrumented Stage 3A cohort-expansion shard on locked A5000."""

from __future__ import annotations

import argparse
import gc
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage0.modeling import generate_once, load_runtime, prepare_example, runtime_environment
from visual_reasoning.stage1.protocol import (
    classify_protocol_generation,
    protocol_parameters,
    transformers_generation_kwargs,
)


ROOT = Path(__file__).resolve().parents[2]
MAX_NEW_TOKENS = 40_960
SEED = 1_234


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def eos_token_ids(model: Any) -> list[int]:
    value = model.generation_config.eos_token_id
    if value is None:
        return []
    return [int(value)] if isinstance(value, int) else [int(item) for item in value]


def generation_record(generation: dict[str, Any], classification: dict[str, Any]) -> dict[str, Any]:
    keep = {key: value for key, value in generation.items() if key not in {"token_rows", "attention_arrays"}}
    return {**keep, **classification, "instrumentation_enabled": False}


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    allowed = (ROOT / "outputs/stage3a/cohort_expansion").resolve()
    output_dir.relative_to(allowed)
    manifest = read_jsonl(args.manifest)
    if not manifest:
        raise ValueError("Expansion manifest shard is empty")
    parameters = protocol_parameters("official", MAX_NEW_TOKENS, SEED)
    generation_kwargs = transformers_generation_kwargs(parameters)
    signature = {
        "manifest": str(args.manifest.resolve()),
        "example_ids": [str(row["example_id"]) for row in manifest],
        "dataset_root": str(args.dataset_root.resolve()),
        "model_checkpoint": str(args.model_checkpoint.resolve()),
        "protocol": parameters,
        "required_gpu_class": "NVIDIA RTX A5000",
        "instrumentation": False,
    }
    config_path = output_dir / "config.json"
    if output_dir.exists() and any(output_dir.iterdir()):
        if not args.resume or not config_path.is_file():
            raise FileExistsError(f"Non-empty output requires --resume: {output_dir}")
        if json.loads(config_path.read_text(encoding="utf-8"))["run_signature"] != signature:
            raise RuntimeError("Resume signature mismatch")
    else:
        ensure_directory(output_dir)
        write_json(config_path, {"created_at": datetime.now(timezone.utc).isoformat(), "run_signature": signature})
        write_jsonl(output_dir / "manifest.jsonl", manifest)

    rows = load_mathverse_rows(args.dataset_root)
    by_id = {str(row["sample_index"]): row for row in rows}
    selected = [by_id[str(item["example_id"])] for item in manifest]
    print(f"Loading locked checkpoint for {len(selected)} expansion examples", flush=True)
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, MAX_NEW_TOKENS)
    gpu_name = str(environment["gpu_name"])
    if "A5000" not in gpu_name:
        raise RuntimeError(f"Locked Stage 1 protocol requires A5000, observed {gpu_name}")
    write_json(output_dir / "environment.json", environment)
    eos_ids = eos_token_ids(model)
    results: list[dict[str, Any]] = []
    for index, row in enumerate(selected):
        example_id = str(row["sample_index"])
        example_dir = output_dir / "examples" / example_id
        result_path = example_dir / "result.json"
        if args.resume and result_path.is_file():
            results.append(json.loads(result_path.read_text(encoding="utf-8")))
            print(f"[{index + 1}/{len(selected)}] resumed {example_id}", flush=True)
            continue
        ensure_directory(example_dir)
        prepared, input_record, _ = prepare_example(processor, row, args.dataset_root, device="cuda")
        write_json(example_dir / "input.json", input_record)
        generation = generate_once(
            model,
            processor,
            prepared,
            MAX_NEW_TOKENS,
            recorder=None,
            generation_kwargs=generation_kwargs,
            seed=SEED,
            collect_predictive_metrics=False,
        )
        classification = classify_protocol_generation(
            generation["generated_token_ids"],
            generation["full_generated_response"],
            str(row["answer"]),
            MAX_NEW_TOKENS,
            eos_ids,
        )
        write_json(example_dir / "generation.json", generation_record(generation, classification))
        write_jsonl(example_dir / "tokens.jsonl", generation["token_rows"])
        result = {
            "example_id": example_id,
            "base_problem_id": str(row["problem_index"]),
            "variant": str(row["problem_version"]),
            "subject": str(row.get("metadata", {}).get("subject", "unknown")),
            "subfield": str(row.get("metadata", {}).get("subfield", "unknown")),
            **classification,
            "generated_token_count": int(generation["generated_token_count"]),
            "runtime": generation["runtime"],
            "artifact_dir": str(example_dir),
        }
        write_json(result_path, result)
        results.append(result)
        print(
            f"[{index + 1}/{len(selected)}] {example_id}: {result['status']} "
            f"tokens={result['generated_token_count']} seconds={result['runtime']['elapsed_seconds']:.1f}",
            flush=True,
        )
        del prepared, generation
        gc.collect()
        torch.cuda.empty_cache()
    summary = {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "correct": sum(row["status"] == "correct" for row in results),
        "wrong": sum(row["status"] == "wrong" for row in results),
        "truncated": sum(row["status"] == "truncated" for row in results),
        "invalid": sum(row["status"] == "invalid" for row in results),
        "all_raw_outcomes_preserved": len(results) == len(selected),
        "results": results,
    }
    write_json(output_dir / "result.json", summary)
    print(json.dumps({key: value for key, value in summary.items() if key != "results"}, indent=2))


if __name__ == "__main__":
    main()

