#!/usr/bin/env python3
"""Run a manifest-defined Stage 1 instrumented or faithfulness generation shard."""

from __future__ import annotations

import argparse
import gc
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch

from visual_reasoning.stage0.analysis import extract_answer
from visual_reasoning.stage0.attention import OnlineAttentionRecorder
from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text
from visual_reasoning.stage0.modeling import attention_modules, generate_once, load_runtime, prepare_example, runtime_environment
from visual_reasoning.stage0.reporting import instrumentation_markdown, model_report_markdown
from visual_reasoning.stage1.analysis import add_source_densities, analyze_generation
from visual_reasoning.stage1.protocol import protocol_parameters, transformers_generation_kwargs
from visual_reasoning.stage1.reporting import stage1_environment_markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-new-tokens", type=int, required=True)
    parser.add_argument("--mode", choices=("instrumented", "faithfulness"), default="instrumented")
    parser.add_argument("--protocol", choices=("greedy", "official"), default="greedy")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--selected-head-layers", default="0,1,18,35")
    parser.add_argument("--max-example-output-mb", type=float, default=256.0)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def serializable_generation(generation: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in generation.items() if key not in {"token_rows", "attention_arrays"}}


def directory_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def eos_token_ids(model: Any) -> list[int]:
    value = model.generation_config.eos_token_id
    if value is None:
        return []
    return [int(value)] if isinstance(value, int) else [int(item) for item in value]


def run_metrics(results: list[dict[str, Any]], cap: int) -> dict[str, Any]:
    lengths = np.asarray([int(result["generated_token_count"]) for result in results], dtype=np.int32)
    latencies = np.asarray([float(result["runtime"]["elapsed_seconds"]) for result in results], dtype=np.float64)
    completed = [result for result in results if bool(result["complete"])]
    truncated = [result for result in results if result["status"] == "truncated"]
    return {
        "max_new_tokens": int(cap),
        "total": len(results),
        "completed": len(completed),
        "completion_rate": len(completed) / len(results) if results else 0.0,
        "truncated": len(truncated),
        "truncation_rate": len(truncated) / len(results) if results else 0.0,
        "correct": sum(result["status"] == "correct" for result in results),
        "wrong": sum(result["status"] == "wrong" for result in results),
        "invalid": sum(result["status"] == "invalid" for result in results),
        "correctness_among_completed": sum(result["status"] == "correct" for result in completed) / len(completed) if completed else 0.0,
        "median_generation_length": float(np.median(lengths)) if lengths.size else 0.0,
        "p90_generation_length": float(np.percentile(lengths, 90)) if lengths.size else 0.0,
        "maximum_generation_length": int(lengths.max()) if lengths.size else 0,
        "median_latency_seconds": float(np.median(latencies)) if latencies.size else 0.0,
        "p90_latency_seconds": float(np.percentile(latencies, 90)) if latencies.size else 0.0,
        "peak_gpu_allocated_bytes": max((int(result["runtime"]["peak_gpu_allocated_bytes"]) for result in results), default=0),
        "maximum_artifact_bytes": max((int(result["output_bytes"]) for result in results), default=0),
        "per_example": [
            {
                "example_id": result["example_id"],
                "status": result["status"],
                "complete": result["complete"],
                "generated_token_count": result["generated_token_count"],
                "latency_seconds": result["runtime"]["elapsed_seconds"],
                "peak_gpu_allocated_bytes": result["runtime"]["peak_gpu_allocated_bytes"],
                "artifact_bytes": result["output_bytes"],
            }
            for result in results
        ],
    }


def main() -> None:
    args = parse_args()
    if args.max_new_tokens not in (4096, 8192, 40960):
        raise ValueError("Stage 1 generation cap must be 4096, 8192, or the approved 40960 safety ceiling")
    output_dir = args.output_dir.resolve()
    allowed = (Path.cwd() / "outputs" / "stage1").resolve()
    try:
        output_dir.relative_to(allowed)
    except ValueError as exc:
        raise ValueError(f"Stage 1 output must be under {allowed}: {output_dir}") from exc
    manifest = read_jsonl(args.manifest)
    if not manifest:
        raise ValueError("Manifest is empty")
    selected_head_layers = [int(value) for value in args.selected_head_layers.split(",") if value.strip()]
    parameters = protocol_parameters(args.protocol, args.max_new_tokens, args.seed)
    generation_kwargs = transformers_generation_kwargs(parameters)
    signature = {
        "manifest": str(args.manifest.resolve()),
        "example_ids": [str(row["example_id"]) for row in manifest],
        "dataset_root": str(args.dataset_root.resolve()),
        "model_checkpoint": str(args.model_checkpoint.resolve()),
        "max_new_tokens": int(args.max_new_tokens),
        "mode": args.mode,
        "protocol": args.protocol,
        "parameters": parameters,
        "transformers_generation_kwargs": generation_kwargs,
        "selected_head_layers": selected_head_layers,
        "max_example_output_mb": float(args.max_example_output_mb),
    }
    config_path = output_dir / "config.json"
    if output_dir.exists() and any(output_dir.iterdir()):
        if not args.resume or not config_path.is_file():
            raise FileExistsError(f"Non-empty output requires --resume and matching config: {output_dir}")
        existing = json.loads(config_path.read_text(encoding="utf-8"))
        if existing.get("run_signature") != signature:
            raise RuntimeError("Resume signature does not match existing config")
    else:
        ensure_directory(output_dir)
        write_json(
            config_path,
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "run_signature": signature,
                "generation": {**parameters, "transformers_generation_kwargs": generation_kwargs, "use_cache": True},
                "presence_penalty_mapping": "official value is 0.0; omitted as an exact no-op in Transformers",
                "scientific_boundary": "attention and candidate peaks are descriptive, not causal visual usage",
            },
        )
        write_jsonl(output_dir / "manifest.jsonl", manifest)

    rows = load_mathverse_rows(args.dataset_root)
    by_id = {str(row["sample_index"]): row for row in rows}
    selected = [by_id[str(item["example_id"])] for item in manifest]
    for row in selected:
        resolve_image_path(args.dataset_root, str(row["image"]))
    print(f"Loading {args.model_checkpoint} on CUDA for Stage 1 {args.mode} run", flush=True)
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, args.max_new_tokens)
    if environment["language_attention_implementation"] != "eager" or environment["vision_attention_implementation"] != "sdpa":
        raise RuntimeError(f"Unexpected attention backends: {environment}")
    if any(layer < 0 or layer >= int(environment["language_layers"]) for layer in selected_head_layers):
        raise ValueError("Selected head layer is outside the language model")
    write_text(output_dir / "environment.md", stage1_environment_markdown(environment, args.protocol, parameters))
    write_text(output_dir / "model_report.md", model_report_markdown(environment))
    write_text(output_dir / "instrumentation.md", instrumentation_markdown({**environment, "selected_head_layers": selected_head_layers}))

    results: list[dict[str, Any]] = []
    modules = attention_modules(model)
    eos_ids = eos_token_ids(model)
    output_limit = int(args.max_example_output_mb * 1024 * 1024)
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
            prepared, input_record, _image_path = prepare_example(processor, row, args.dataset_root, device="cuda")
            write_json(example_dir / "input.json", input_record)
            baseline = None
            faithfulness = None
            if args.mode == "faithfulness":
                baseline = generate_once(
                    model,
                    processor,
                    prepared,
                    args.max_new_tokens,
                    recorder=None,
                    generation_kwargs=generation_kwargs,
                    seed=args.seed,
                    memory_safe_scores=args.max_new_tokens == 40960,
                )
                write_json(
                    example_dir / "baseline_generation.json",
                    {**serializable_generation(baseline), "extracted_final_answer": extract_answer(baseline["full_generated_response"]), "instrumentation_enabled": False},
                )
            recorder = OnlineAttentionRecorder(
                prompt_length=int(input_record["prompt_token_count"]),
                visual_indices=[int(value) for value in input_record["visual_token_indices"]],
                num_layers=int(environment["language_layers"]),
                selected_head_layers=selected_head_layers,
            ).attach(modules)
            try:
                instrumented = generate_once(
                    model,
                    processor,
                    prepared,
                    args.max_new_tokens,
                    recorder=recorder,
                    generation_kwargs=generation_kwargs,
                    seed=args.seed,
                    memory_safe_scores=args.max_new_tokens == 40960,
                )
            finally:
                recorder.close()
            attention_validation = recorder.validate(instrumented["generated_token_count"])
            if not attention_validation["passed"]:
                raise RuntimeError(f"Attention validation failed: {attention_validation}")
            instrumented["attention_arrays"] = add_source_densities(
                instrumented["token_rows"],
                instrumented["attention_arrays"],
                prompt_length=int(input_record["prompt_token_count"]),
                visual_count=len(input_record["visual_token_indices"]),
            )
            generation_summary, spans, span_arrays, peaks = analyze_generation(
                instrumented, str(row["answer"]), args.max_new_tokens, eos_ids
            )
            if baseline is not None:
                faithfulness = {
                    "generated_token_ids_match": baseline["generated_token_ids"] == instrumented["generated_token_ids"],
                    "final_answers_match": extract_answer(baseline["full_generated_response"]) == generation_summary["extracted_final_answer"],
                }
                faithfulness["passed"] = all(faithfulness.values())
                write_json(example_dir / "faithfulness.json", faithfulness)
                if not faithfulness["passed"]:
                    raise RuntimeError(f"Exact faithfulness failed: {faithfulness}")
            arrays = instrumented["attention_arrays"]
            write_json(
                example_dir / "generation.json",
                {**generation_summary, "raw_decoded_response": instrumented["raw_decoded_response"], "instrumentation_enabled": True, "attention_file": "attention_summary.npz"},
            )
            write_jsonl(example_dir / "tokens.jsonl", instrumented["token_rows"])
            write_json(example_dir / "spans.json", spans)
            write_json(example_dir / "candidate_visual_peaks.json", peaks)
            np.savez_compressed(example_dir / "attention_summary.npz", **arrays)
            np.savez_compressed(
                example_dir / "uncertainty.npz",
                entropy=np.asarray([row["next_token_entropy"] for row in instrumented["token_rows"]], dtype=np.float32),
                top1_probability=np.asarray([row["top1_probability"] for row in instrumented["token_rows"]], dtype=np.float32),
                top1_top2_margin=np.asarray([row["top1_top2_margin"] for row in instrumented["token_rows"]], dtype=np.float32),
            )
            np.savez_compressed(example_dir / "span_signals.npz", **span_arrays)
            decoded_reconstructs = "".join(str(row["decoded_token"]) for row in instrumented["token_rows"]) == instrumented["raw_decoded_response"]
            validation = {
                "visual_mapping_passed": len(input_record["visual_token_indices"]) == int(input_record["visual_mapping"]["visual_token_count"]),
                "attention": attention_validation,
                "decoded_text_reconstructs": decoded_reconstructs,
                "alignment_passed": all(bool(value) for value in generation_summary["alignment"].values()),
                "normalized_source_statistics_present": arrays["modality_density_by_layer"].shape == arrays["modality_by_layer"].shape,
                "visual_focus_present": arrays["visual_focus"].shape[0] == generation_summary["generated_token_count"],
                "uncertainty_present": bool(instrumented["token_rows"]),
                "span_statistics_present": span_arrays["span_ranges"].shape[0] == len(spans),
            }
            validation["passed"] = all(
                (
                    validation["visual_mapping_passed"],
                    attention_validation["passed"],
                    decoded_reconstructs,
                    validation["alignment_passed"],
                    validation["normalized_source_statistics_present"],
                    validation["visual_focus_present"],
                    validation["uncertainty_present"],
                    validation["span_statistics_present"],
                )
            )
            write_json(example_dir / "instrumentation_validation.json", validation)
            if not validation["passed"]:
                raise RuntimeError(f"Stage 1 validation failed: {validation}")
            output_bytes = directory_bytes(example_dir)
            if output_bytes > output_limit:
                raise RuntimeError(f"Example output {output_bytes} exceeds bound {output_limit}")
            result = {
                "example_id": example_id,
                "problem_index": str(row["problem_index"]),
                "mathverse_variant": str(row["problem_version"]),
                "subject": str(row.get("metadata", {}).get("subject", "unknown")),
                "status": generation_summary["status"],
                "complete": generation_summary["complete"],
                "correct": generation_summary["correct"],
                "generated_token_count": generation_summary["generated_token_count"],
                "span_count": len(spans),
                "candidate_visual_peak_count": int(peaks["peak_count"]),
                "alignment": generation_summary["alignment"],
                "runtime": generation_summary["runtime"],
                "faithfulness": faithfulness,
                "validation": validation,
                "output_bytes": output_bytes,
            }
            write_json(result_path, result)
            results.append(result)
            print(
                f"[{index + 1}/{len(selected)}] example {example_id}: status={result['status']} "
                f"tokens={result['generated_token_count']} latency={result['runtime']['elapsed_seconds']:.1f}s bytes={output_bytes}",
                flush=True,
            )
            del prepared, instrumented, arrays, span_arrays
            if baseline is not None:
                del baseline
            gc.collect()
            torch.cuda.empty_cache()
        except Exception as exc:
            write_json(example_dir / "error.json", {"type": type(exc).__name__, "message": str(exc), "time": datetime.now(timezone.utc).isoformat()})
            raise
    summary = run_metrics(results, args.max_new_tokens)
    summary.update(
        {
            "mode": args.mode,
            "protocol": args.protocol,
            "parameters": parameters,
            "all_instrumentation_valid": all(bool(result["validation"]["passed"]) for result in results),
            "faithfulness_passed": args.mode == "faithfulness" and len(results) >= 3 and all(bool(result["faithfulness"]["passed"]) for result in results),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    write_json(output_dir / "run_summary.json", summary)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
