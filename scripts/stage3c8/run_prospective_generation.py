#!/usr/bin/env python3
"""Run one frozen Stage 3C.8 prospective baseline-generation shard."""

from __future__ import annotations

import argparse
import gc
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage0.modeling import generate_once, load_runtime, prepare_example, runtime_environment
from visual_reasoning.stage1.protocol import classify_protocol_generation, protocol_parameters, transformers_generation_kwargs
from visual_reasoning.stage3b8.evaluation import evaluate_mathverse_response
from visual_reasoning.stage3c8.protocol import local_cuda_device_index


ROOT = Path(__file__).resolve().parents[2]
ALLOWED = (ROOT / "outputs/stage3c8/prospective_generation/raw").resolve()
MAX_NEW_TOKENS = 40_960
SEED = 1_234


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def eos_token_ids(model: Any) -> list[int]:
    value = model.generation_config.eos_token_id
    if value is None:
        return []
    return [int(value)] if isinstance(value, int) else [int(item) for item in value]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--required-gpu-class", default="A5000")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cuda_device_index = local_cuda_device_index(
        os.environ, visible_device_count=torch.cuda.device_count()
    )
    torch.cuda.set_device(cuda_device_index)
    output_dir = args.output_dir.resolve()
    output_dir.relative_to(ALLOWED)
    manifest = read_jsonl(args.manifest)
    if not manifest:
        raise ValueError("Prospective-generation shard is empty")
    parameters = protocol_parameters("official", MAX_NEW_TOKENS, SEED)
    generation_kwargs = transformers_generation_kwargs(parameters)
    signature = {
        "manifest": str(args.manifest.resolve()),
        "example_ids": [str(row["example_id"]) for row in manifest],
        "base_problem_ids": [str(row["base_problem_id"]) for row in manifest],
        "dataset_root": str(args.dataset_root.resolve()),
        "model_checkpoint": str(args.model_checkpoint.resolve()),
        "protocol": parameters,
        "required_gpu_class": args.required_gpu_class,
        "instrumentation": False,
        "selection_used_attention": False,
        "selection_used_generation_outcomes": False,
        "selection_used_carrier_outcomes": False,
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

    by_id = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    selected = [by_id[str(item["example_id"])] for item in manifest]
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, MAX_NEW_TOKENS)
    if args.required_gpu_class not in str(environment["gpu_name"]):
        raise RuntimeError(f"Expected {args.required_gpu_class}, observed {environment['gpu_name']}")
    write_json(output_dir / "environment.json", environment)
    eos_ids = eos_token_ids(model)
    results: list[dict[str, Any]] = []
    for index, (item, row) in enumerate(zip(manifest, selected)):
        example_id = str(row["sample_index"])
        base = str(row["problem_index"])
        if base != str(item["base_problem_id"]):
            raise RuntimeError(f"Manifest/dataset base mismatch for example {example_id}")
        example_dir = output_dir / "examples" / example_id
        result_path = example_dir / "result.json"
        if args.resume and result_path.is_file():
            result = json.loads(result_path.read_text(encoding="utf-8"))
            results.append(result)
            print(f"[{index + 1}/{len(selected)}] resumed base {base}", flush=True)
            continue
        ensure_directory(example_dir)
        prepared, input_record, _ = prepare_example(processor, row, args.dataset_root, device="cuda")
        write_json(example_dir / "input.json", input_record)
        generation = generate_once(
            model, processor, prepared, MAX_NEW_TOKENS, recorder=None,
            generation_kwargs=generation_kwargs, seed=SEED, collect_predictive_metrics=False,
        )
        legacy = classify_protocol_generation(
            generation["generated_token_ids"], generation["full_generated_response"],
            str(row["answer"]), MAX_NEW_TOKENS, eos_ids,
        )
        evaluation = evaluate_mathverse_response(generation["full_generated_response"], str(row["answer"]))
        if legacy["truncated"]:
            status = "truncated"
        elif not legacy["complete"]:
            status = "invalid"
        else:
            status = "correct" if evaluation["correct"] else "wrong"
        generation_record = {
            **{key: value for key, value in generation.items() if key not in {"token_rows", "attention_arrays"}},
            **legacy,
            "legacy_status": legacy["status"],
            "numeric_mathverse_evaluation": evaluation,
            "status": status,
            "correct": status == "correct",
            "instrumentation_enabled": False,
        }
        write_json(example_dir / "generation.json", generation_record)
        write_jsonl(example_dir / "tokens.jsonl", generation["token_rows"])
        result = {
            "example_id": example_id,
            "base_problem_id": base,
            "screen_order": int(item["order"]),
            "variant": str(row["problem_version"]),
            "source": str(row["metadata"]["source"]),
            "ground_truth_answer": str(row["answer"]),
            "status": status,
            "correct": status == "correct",
            "complete": bool(legacy["complete"]),
            "truncated": bool(legacy["truncated"]),
            "normal_termination": bool(legacy["normal_termination"]),
            "termination_reason": legacy["termination_reason"],
            "ended_with_eos": bool(legacy["ended_with_eos"]),
            "extracted_final_answer": evaluation["predicted_answer"],
            "legacy_status": legacy["status"],
            "legacy_extracted_final_answer": legacy["extracted_final_answer"],
            "generated_token_count": int(generation["generated_token_count"]),
            "runtime": generation["runtime"],
            "artifact_dir": str(example_dir.relative_to(ROOT)),
            "selection_used_attention": False,
            "selection_used_carrier_outcome": False,
        }
        write_json(result_path, result)
        results.append(result)
        print(
            f"[{index + 1}/{len(selected)}] base={base}: {status} "
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
