#!/usr/bin/env python3
"""Run one uninstrumented Stage 1A.2 generation-protocol condition."""

from __future__ import annotations

import argparse
import gc
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text
from visual_reasoning.stage0.modeling import generate_once, load_runtime, prepare_example, runtime_environment
from visual_reasoning.stage0.reporting import model_report_markdown
from visual_reasoning.stage1.protocol import (
    OFFICIAL_QWEN_SOURCE,
    classify_protocol_generation,
    protocol_parameters,
    protocol_run_metrics,
    repetition_diagnostics,
    transformers_generation_kwargs,
)
from visual_reasoning.stage1.reporting import stage1_environment_markdown


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def directory_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def eos_token_ids(model: Any) -> list[int]:
    value = model.generation_config.eos_token_id
    if value is None:
        return []
    return [int(value)] if isinstance(value, int) else [int(item) for item in value]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--condition", choices=("greedy", "official"), required=True)
    parser.add_argument("--max-new-tokens", type=int, default=40_960)
    parser.add_argument("--seed", type=int, default=1_234)
    parser.add_argument("--max-example-output-mb", type=float, default=64.0)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    if args.max_new_tokens != 40_960:
        raise ValueError("Stage 1A.2 must use the prospective 40,960-token safety ceiling")
    output_dir = args.output_dir.resolve()
    allowed = (Path.cwd() / "outputs" / "stage1" / "protocol_pilot").resolve()
    try:
        output_dir.relative_to(allowed)
    except ValueError as exc:
        raise ValueError(f"Protocol output must be under {allowed}: {output_dir}") from exc
    manifest = read_jsonl(args.manifest)
    if not manifest:
        raise ValueError("Manifest is empty")
    parameters = protocol_parameters(args.condition, args.max_new_tokens, args.seed)
    generation_kwargs = transformers_generation_kwargs(parameters)
    signature = {
        "manifest": str(args.manifest.resolve()),
        "example_ids": [str(row["example_id"]) for row in manifest],
        "dataset_root": str(args.dataset_root.resolve()),
        "model_checkpoint": str(args.model_checkpoint.resolve()),
        "condition": args.condition,
        "parameters": parameters,
        "transformers_generation_kwargs": generation_kwargs,
        "instrumentation_enabled": False,
    }
    config_path = output_dir / "config.json"
    if output_dir.exists() and any(output_dir.iterdir()):
        if not args.resume or not config_path.is_file():
            raise FileExistsError(f"Non-empty output requires --resume and matching config: {output_dir}")
        if json.loads(config_path.read_text(encoding="utf-8")).get("run_signature") != signature:
            raise RuntimeError("Resume signature does not match existing protocol config")
    else:
        ensure_directory(output_dir)
        write_json(
            config_path,
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "run_signature": signature,
                "normal_stop": "EOS",
                "presence_penalty_mapping": "official value is 0.0; omitted as an exact no-op in Transformers",
                "official_source": OFFICIAL_QWEN_SOURCE if args.condition == "official" else None,
                "scientific_boundary": "protocol comparison only; no attention-based or causal claim",
            },
        )
        write_jsonl(output_dir / "manifest.jsonl", manifest)

    rows = load_mathverse_rows(args.dataset_root)
    by_id = {str(row["sample_index"]): row for row in rows}
    selected = [by_id[str(item["example_id"])] for item in manifest]
    for row in selected:
        resolve_image_path(args.dataset_root, str(row["image"]))
    print(f"Loading {args.model_checkpoint} for Stage 1A.2 {args.condition}", flush=True)
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, args.max_new_tokens)
    write_text(output_dir / "environment.md", stage1_environment_markdown(environment, args.condition, parameters))
    write_text(output_dir / "model_report.md", model_report_markdown(environment))
    eos_ids = eos_token_ids(model)
    output_limit = int(args.max_example_output_mb * 1024 * 1024)
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
        try:
            prepared, input_record, _ = prepare_example(processor, row, args.dataset_root, device="cuda")
            write_json(example_dir / "input.json", input_record)
            generation = generate_once(
                model,
                processor,
                prepared,
                args.max_new_tokens,
                recorder=None,
                generation_kwargs=generation_kwargs,
                seed=args.seed,
                collect_predictive_metrics=False,
            )
            classification = classify_protocol_generation(
                generation["generated_token_ids"],
                generation["full_generated_response"],
                str(row["answer"]),
                args.max_new_tokens,
                eos_ids,
            )
            repetition = repetition_diagnostics(generation["full_generated_response"])
            generation_record = {
                "full_generated_response": generation["full_generated_response"],
                "raw_decoded_response": generation["raw_decoded_response"],
                "generated_token_ids": generation["generated_token_ids"],
                "generated_token_count": generation["generated_token_count"],
                "ground_truth_answer": str(row["answer"]),
                **classification,
                "runtime": generation["runtime"],
                "generation_parameters": parameters,
                "instrumentation_enabled": False,
                "incremental_decode_alignment": generation["incremental_decode_alignment"],
            }
            write_json(example_dir / "generation.json", generation_record)
            write_jsonl(example_dir / "tokens.jsonl", generation["token_rows"])
            write_json(example_dir / "repetition_diagnostics.json", repetition)
            output_bytes = directory_bytes(example_dir)
            if output_bytes > output_limit:
                raise RuntimeError(f"Example output {output_bytes} exceeds bound {output_limit}")
            result = {
                "example_id": example_id,
                "problem_index": str(row["problem_index"]),
                "mathverse_variant": str(row["problem_version"]),
                "subject": str(row.get("metadata", {}).get("subject", "unknown")),
                **classification,
                "generated_token_count": generation["generated_token_count"],
                "runtime": generation["runtime"],
                "repetition": repetition,
                "output_bytes": output_bytes,
            }
            write_json(result_path, result)
            results.append(result)
            print(
                f"[{index + 1}/{len(selected)}] example {example_id}: status={result['status']} "
                f"termination={result['termination_reason']} tokens={result['generated_token_count']} "
                f"latency={result['runtime']['elapsed_seconds']:.1f}s loop_flag={repetition['any_pathology_flag']}",
                flush=True,
            )
            del prepared, generation
            gc.collect()
            torch.cuda.empty_cache()
        except Exception as exc:
            write_json(
                example_dir / "error.json",
                {"type": type(exc).__name__, "message": str(exc), "time": datetime.now(timezone.utc).isoformat()},
            )
            raise
    summary = protocol_run_metrics(results, args.max_new_tokens)
    summary.update(
        {
            "condition": args.condition,
            "parameters": parameters,
            "transformers_generation_kwargs": generation_kwargs,
            "instrumentation_enabled": False,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    write_json(output_dir / "run_summary.json", summary)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
