#!/usr/bin/env python3
"""Run the bounded Stage 0 visual–reasoning instrumentation program."""

from __future__ import annotations

import argparse
import gc
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch

from visual_reasoning.stage0.analysis import correctness_summary, extract_answer
from visual_reasoning.stage0.attention import OnlineAttentionRecorder
from visual_reasoning.stage0.data import (
    dataset_inventory,
    load_mathverse_rows,
    resolve_image_path,
    select_stage0_subset,
)
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text
from visual_reasoning.stage0.modeling import (
    analyze_instrumented_generation,
    attention_modules,
    generate_once,
    load_runtime,
    prepare_example,
    runtime_environment,
)
from visual_reasoning.stage0.plotting import save_timeline_plots, save_visual_focus_snapshots
from visual_reasoning.stage0.reporting import (
    dataset_report_markdown,
    environment_markdown,
    instrumentation_markdown,
    model_report_markdown,
    stage0_summary_markdown,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("smoke", "full"), required=True)
    parser.add_argument("--num-examples", type=int, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-new-tokens", type=int, default=1024)
    parser.add_argument("--plot-examples", type=int, default=5)
    parser.add_argument("--selected-head-layers", default="0,1,18,35")
    parser.add_argument("--max-example-output-mb", type=float, default=128.0)
    parser.add_argument("--smoke-report", type=Path)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--summary-only", action="store_true")
    return parser.parse_args()


def parse_layers(value: str) -> list[int]:
    layers = [int(chunk.strip()) for chunk in value.split(",") if chunk.strip()]
    if not layers:
        raise ValueError("At least one selected head layer is required")
    return layers


def validate_output_root(output_dir: Path) -> Path:
    project_outputs = (Path.cwd() / "outputs").resolve()
    resolved = output_dir.resolve()
    try:
        resolved.relative_to(project_outputs)
    except ValueError as exc:
        raise ValueError(f"Stage 0 output directory must be under {project_outputs}: {resolved}") from exc
    return resolved


def directory_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def serializable_generation(generation: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in generation.items()
        if key not in {"token_rows", "attention_arrays"}
    }


def eos_token_ids(model: Any) -> list[int]:
    value = model.generation_config.eos_token_id
    if value is None:
        return []
    if isinstance(value, int):
        return [value]
    return [int(item) for item in value]


def qualitative_summary(results: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    stats = [result["descriptive_statistics"] for result in results]
    early = float(np.mean([item["early_quartile_visual_attention"] for item in stats]))
    late = float(np.mean([item["late_quartile_visual_attention"] for item in stats]))
    correlations = [item["visual_entropy_correlation"] for item in stats if item["visual_entropy_correlation"] is not None]
    correlation = float(np.mean(correlations)) if correlations else None
    repeated = sum(int(item["visual_peak_count"] >= 2) for item in stats)
    observations = [
        f"Mean descriptive visual-attention mass was {early:.4f} in the first generated-token quartile and {late:.4f} in the last quartile.",
        f"{repeated}/{len(results)} examples contained at least two within-trajectory visual-attention peaks under the provisional mean-plus-standard-deviation diagnostic.",
    ]
    if correlation is not None:
        observations.append(f"The example-mean token-level correlation between visual-attention mass and entropy was {correlation:.4f}.")
    hypotheses = [
        "Test whether early-versus-late descriptive differences survive causal visual-evidence interventions.",
        "Test whether repeated descriptive peaks align with changes in evidence demand rather than lexical visual-reference cues.",
    ]
    if correlation is not None:
        hypotheses.append("Disentangle predictive uncertainty from evidence demand with controlled causal comparisons.")
    return observations, hypotheses


def acceptance_criteria(
    mode: str,
    results: list[dict[str, Any]],
    inventory: dict[str, Any],
    smoke_report: dict[str, Any] | None,
    output_limit_bytes: int,
) -> tuple[list[dict[str, Any]], bool]:
    faithfulness = (
        all(bool(result.get("faithfulness", {}).get("passed")) for result in results)
        if mode == "smoke"
        else bool(smoke_report and smoke_report.get("smoke_gate_passed"))
    )
    visual_mapping = all(bool(result["validation"]["visual_mapping_passed"]) for result in results)
    alignment = all(all(bool(value) for value in result["alignment"].values()) for result in results)
    signals = all(bool(result["validation"]["required_signals_passed"]) for result in results)
    resource = all(int(result["output_bytes"]) <= output_limit_bytes for result in results)
    if mode == "full":
        resource = resource and 30 <= len(results) <= 50
    traceable = all(bool(result["validation"]["traceable_outputs_passed"]) for result in results)
    paired = int(inventory["complete_variant_group_count"]) == int(inventory["unique_problem_count"])
    plotted_examples = sum(bool(result.get("plot_files")) for result in results)
    plots = plotted_examples >= min(3, len(results)) and all(
        bool(result.get("visual_focus_files")) for result in results[: min(3, len(results))]
    )
    criteria = [
        {"id": 1, "name": "Deterministic faithfulness", "passed": faithfulness, "evidence": "exact generated-token and final-answer equality on smoke examples"},
        {"id": 2, "name": "Correct visual-token mapping", "passed": visual_mapping, "evidence": "placeholder count equals processor grid-derived merged token count"},
        {"id": 3, "name": "Token/span alignment works", "passed": alignment, "evidence": "token, score, attention, decode, and span-range checks"},
        {"id": 4, "name": "Required descriptive signals recorded", "passed": signals, "evidence": "modality mass, uncertainty, selected heads, and visual focus present"},
        {"id": 5, "name": "Resource use manageable", "passed": resource, "evidence": f"per-example output <= {output_limit_bytes} bytes and requested run completed"},
        {"id": 6, "name": "Outputs reproducible and traceable", "passed": traceable, "evidence": "structured per-example inputs, generations, tokens, spans, arrays, validation, and config"},
        {"id": 7, "name": "MathVerse paired variants accessible", "passed": paired, "evidence": f"{inventory['complete_variant_group_count']}/{inventory['unique_problem_count']} complete problem groups"},
        {"id": 8, "name": "Qualitative timelines inspectable", "passed": plots, "evidence": f"diagnostic plots for {plotted_examples} examples with spatial snapshots"},
    ]
    smoke_gate = faithfulness and visual_mapping and alignment and signals and resource and traceable and paired and plots
    return criteria, smoke_gate


def write_summary_artifacts(
    mode: str,
    output_dir: Path,
    expected_examples: int,
    results: list[dict[str, Any]],
    inventory: dict[str, Any],
    smoke_report: dict[str, Any] | None,
    output_limit_bytes: int,
) -> dict[str, Any]:
    criteria, smoke_gate_passed = acceptance_criteria(
        mode=mode,
        results=results,
        inventory=inventory,
        smoke_report=smoke_report,
        output_limit_bytes=output_limit_bytes,
    )
    observations, hypotheses = qualitative_summary(results)
    stage0_pass = mode == "full" and all(bool(item["passed"]) for item in criteria)
    summary = {
        "mode": mode,
        "examples_processed": len(results),
        "expected_examples": expected_examples,
        "smoke_gate_passed": smoke_gate_passed,
        "stage0_pass": stage0_pass,
        "stage1_started": False,
        "correctness_and_filtering": correctness_summary(results),
        "acceptance_criteria": criteria,
        "qualitative_observations": observations,
        "stage1_hypotheses": hypotheses,
        "known_limitations": [
            "Language eager attention is required for exact attention probabilities.",
            "Attention is descriptive and not causal evidence.",
            "Reasoning spans are provisional rule-based segments.",
            "A 2,048-token safety cap can truncate repetitive or non-terminating trajectories; these remain in raw logs and filtering statistics.",
        ],
        "result_files": [f"examples/{result['example_id']}/result.json" for result in results],
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    ensure_directory(output_dir / "summaries")
    write_json(output_dir / "summaries" / "stage0_summary.json", summary)
    write_text(output_dir / "summaries" / "stage0_summary.md", stage0_summary_markdown(summary))
    return summary


def main() -> None:
    args = parse_args()
    output_dir = validate_output_root(args.output_dir)
    selected_head_layers = parse_layers(args.selected_head_layers)
    if args.max_new_tokens < 64:
        raise ValueError("max-new-tokens must be at least 64 for Thinking-model smoke validation")
    if args.plot_examples < 3:
        raise ValueError("plot-examples must be at least 3")
    if not args.dataset_root.is_dir():
        raise FileNotFoundError(f"Dataset root not found: {args.dataset_root}")
    if not args.model_checkpoint.is_dir():
        raise FileNotFoundError(f"Model checkpoint not found: {args.model_checkpoint}")

    smoke_report: dict[str, Any] | None = None
    if args.mode == "full":
        if args.smoke_report is None or not args.smoke_report.is_file():
            raise ValueError("Full Stage 0 requires --smoke-report from a completed smoke run")
        smoke_report = json.loads(args.smoke_report.read_text(encoding="utf-8"))
        if not smoke_report.get("smoke_gate_passed"):
            raise RuntimeError("Smoke gate did not pass; refusing the full Stage 0 run")

    run_signature = {
        "mode": args.mode,
        "num_examples": args.num_examples,
        "dataset_root": str(args.dataset_root.resolve()),
        "model_checkpoint": str(args.model_checkpoint.resolve()),
        "max_new_tokens": args.max_new_tokens,
        "plot_examples": args.plot_examples,
        "selected_head_layers": selected_head_layers,
        "max_example_output_mb": args.max_example_output_mb,
        "smoke_report": str(args.smoke_report.resolve()) if args.smoke_report else None,
    }
    config_path = output_dir / "config.json"
    if output_dir.exists() and any(output_dir.iterdir()):
        if not args.resume:
            raise FileExistsError(f"Output directory is non-empty; use --resume after checking it: {output_dir}")
        if not config_path.is_file():
            raise RuntimeError("Cannot resume without config.json")
        existing = json.loads(config_path.read_text(encoding="utf-8"))
        if existing.get("run_signature") != run_signature:
            raise RuntimeError("Resume configuration does not match existing config.json")
    else:
        ensure_directory(output_dir)
        write_json(
            config_path,
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "run_signature": run_signature,
                "generation": {"do_sample": False, "decoding": "greedy", "use_cache": True},
                "attention": {
                    "language_implementation": "eager",
                    "vision_implementation": "sdpa",
                    "aggregation": "final query row; per-layer head mean; selected-layer per-head; all-layer/head visual focus",
                },
            },
        )

    rows = load_mathverse_rows(args.dataset_root)
    selected = select_stage0_subset(rows, count=args.num_examples, mode=args.mode)
    for row in selected:
        resolve_image_path(args.dataset_root, str(row["image"]))
    inventory = dataset_inventory(rows, selected)
    write_text(output_dir / "dataset_report.md", dataset_report_markdown(str(args.dataset_root.resolve()), inventory))
    write_json(output_dir / "dataset_inventory.json", inventory)

    output_limit_bytes = int(args.max_example_output_mb * 1024 * 1024)
    if args.summary_only:
        results = []
        for row in selected:
            result_path = output_dir / "examples" / str(row["sample_index"]) / "result.json"
            if not result_path.is_file():
                raise FileNotFoundError(f"Cannot rebuild summary; missing {result_path}")
            results.append(json.loads(result_path.read_text(encoding="utf-8")))
        summary = write_summary_artifacts(
            mode=args.mode,
            output_dir=output_dir,
            expected_examples=args.num_examples,
            results=results,
            inventory=inventory,
            smoke_report=smoke_report,
            output_limit_bytes=output_limit_bytes,
        )
        print(
            f"Stage 0 {args.mode} summary rebuilt: smoke_gate={summary['smoke_gate_passed']} "
            f"stage0_pass={summary['stage0_pass']}",
            flush=True,
        )
        return

    print(f"Loading {args.model_checkpoint} on CUDA for {args.mode} Stage 0", flush=True)
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, args.max_new_tokens)
    if environment["language_attention_implementation"] != "eager":
        raise RuntimeError(f"Language attention implementation is not eager: {environment['language_attention_implementation']}")
    if environment["vision_attention_implementation"] != "sdpa":
        raise RuntimeError(f"Vision attention implementation is not sdpa: {environment['vision_attention_implementation']}")
    if any(layer < 0 or layer >= environment["language_layers"] for layer in selected_head_layers):
        raise ValueError("A selected head layer lies outside the model")
    write_text(output_dir / "environment.md", environment_markdown(environment))
    write_text(output_dir / "model_report.md", model_report_markdown(environment))
    write_text(
        output_dir / "instrumentation.md",
        instrumentation_markdown({**environment, "selected_head_layers": selected_head_layers}),
    )

    results: list[dict[str, Any]] = []
    eos_ids = eos_token_ids(model)
    modules = attention_modules(model)
    for example_index, row in enumerate(selected):
        example_id = str(row["sample_index"])
        example_dir = output_dir / "examples" / example_id
        result_path = example_dir / "result.json"
        if args.resume and result_path.is_file():
            results.append(json.loads(result_path.read_text(encoding="utf-8")))
            print(f"[{example_index + 1}/{len(selected)}] resumed completed example {example_id}", flush=True)
            continue
        ensure_directory(example_dir)
        try:
            prepared, input_record, image_path = prepare_example(
                processor=processor,
                row=row,
                dataset_root=args.dataset_root,
                device="cuda",
            )
            write_json(example_dir / "input.json", input_record)
            baseline: dict[str, Any] | None = None
            faithfulness: dict[str, Any] | None = None
            if args.mode == "smoke":
                baseline = generate_once(
                    model=model,
                    processor=processor,
                    prepared_inputs=prepared,
                    max_new_tokens=args.max_new_tokens,
                    recorder=None,
                )
                write_json(
                    example_dir / "baseline_generation.json",
                    {
                        **serializable_generation(baseline),
                        "extracted_final_answer": extract_answer(baseline["full_generated_response"]),
                        "instrumentation_enabled": False,
                    },
                )

            recorder = OnlineAttentionRecorder(
                prompt_length=int(input_record["prompt_token_count"]),
                visual_indices=[int(value) for value in input_record["visual_token_indices"]],
                num_layers=int(environment["language_layers"]),
                selected_head_layers=selected_head_layers,
            )
            recorder.attach(modules)
            try:
                instrumented = generate_once(
                    model=model,
                    processor=processor,
                    prepared_inputs=prepared,
                    max_new_tokens=args.max_new_tokens,
                    recorder=recorder,
                )
            finally:
                recorder.close()
            attention_validation = recorder.validate(expected_steps=instrumented["generated_token_count"])
            if not attention_validation["passed"]:
                raise RuntimeError(f"Attention validation failed: {attention_validation}")

            generation_summary, spans = analyze_instrumented_generation(
                generation=instrumented,
                ground_truth=str(row["answer"]),
                max_new_tokens=args.max_new_tokens,
                eos_token_ids=eos_ids,
            )
            if baseline is not None:
                faithfulness = {
                    "generated_token_ids_match": baseline["generated_token_ids"] == instrumented["generated_token_ids"],
                    "final_answers_match": extract_answer(baseline["full_generated_response"])
                    == generation_summary["extracted_final_answer"],
                }
                faithfulness["passed"] = all(faithfulness.values())
                if not faithfulness["passed"]:
                    write_json(example_dir / "faithfulness.json", faithfulness)
                    raise RuntimeError(f"Mandatory deterministic faithfulness check failed: {faithfulness}")
                write_json(example_dir / "faithfulness.json", faithfulness)

            arrays = instrumented["attention_arrays"]
            write_json(
                example_dir / "generation.json",
                {
                    **generation_summary,
                    "raw_decoded_response": instrumented["raw_decoded_response"],
                    "instrumentation_enabled": True,
                    "attention_file": "attention_summary.npz",
                },
            )
            write_jsonl(example_dir / "tokens.jsonl", instrumented["token_rows"])
            write_json(example_dir / "spans.json", spans)
            np.savez_compressed(example_dir / "attention_summary.npz", **arrays)

            plot_files: list[Path] = []
            focus_files: list[Path] = []
            if example_index < args.plot_examples:
                plot_files = save_timeline_plots(instrumented["token_rows"], spans, example_dir / "plots")
                focus_files = save_visual_focus_snapshots(
                    image_path=image_path,
                    visual_focus=arrays["visual_focus"],
                    merged_grid_shape=input_record["visual_mapping"]["merged_grid_shape"],
                    token_rows=instrumented["token_rows"],
                    output_dir=example_dir / "visual_focus",
                )

            validation = {
                "visual_mapping_passed": len(input_record["visual_token_indices"])
                == int(input_record["visual_mapping"]["visual_token_count"]),
                "attention": attention_validation,
                "required_signals_passed": bool(
                    instrumented["token_rows"]
                    and arrays["modality_by_layer"].ndim == 3
                    and arrays["selected_head_mass"].ndim == 4
                    and arrays["visual_focus"].ndim == 2
                ),
                "traceable_outputs_passed": all(
                    (example_dir / name).is_file()
                    for name in ("input.json", "generation.json", "tokens.jsonl", "spans.json", "attention_summary.npz")
                ),
            }
            write_json(example_dir / "instrumentation_validation.json", validation)
            output_bytes = directory_bytes(example_dir)
            if output_bytes > output_limit_bytes:
                raise RuntimeError(
                    f"Example output {output_bytes} bytes exceeds configured bound {output_limit_bytes} bytes"
                )
            result = {
                "example_id": example_id,
                "problem_index": str(row["problem_index"]),
                "mathverse_variant": str(row["problem_version"]),
                "status": generation_summary["status"],
                "generated_token_count": generation_summary["generated_token_count"],
                "alignment": generation_summary["alignment"],
                "descriptive_statistics": generation_summary["descriptive_statistics"],
                "runtime": generation_summary["runtime"],
                "faithfulness": faithfulness,
                "validation": validation,
                "output_bytes": output_bytes,
                "plot_files": [str(path.relative_to(output_dir)) for path in plot_files],
                "visual_focus_files": [str(path.relative_to(output_dir)) for path in focus_files],
            }
            write_json(result_path, result)
            results.append(result)
            print(
                f"[{example_index + 1}/{len(selected)}] example {example_id}: "
                f"status={result['status']} tokens={result['generated_token_count']} bytes={output_bytes}",
                flush=True,
            )
            del prepared, instrumented, arrays
            if baseline is not None:
                del baseline
            gc.collect()
            torch.cuda.empty_cache()
        except Exception as exc:
            write_json(
                example_dir / "error.json",
                {"type": type(exc).__name__, "message": str(exc), "time": datetime.now(timezone.utc).isoformat()},
            )
            raise

    summary = write_summary_artifacts(
        mode=args.mode,
        output_dir=output_dir,
        expected_examples=args.num_examples,
        results=results,
        inventory=inventory,
        smoke_report=smoke_report,
        output_limit_bytes=output_limit_bytes,
    )
    print(
        f"Stage 0 {args.mode} complete: smoke_gate={summary['smoke_gate_passed']} "
        f"stage0_pass={summary['stage0_pass']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
