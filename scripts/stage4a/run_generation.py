#!/usr/bin/env python3
"""Run one rank-disjoint Stage 4A prospective generation shard."""

from __future__ import annotations

import gc
import argparse
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
from visual_reasoning.stage3c8.protocol import distributed_process_info


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage4a"
ALLOWED = (OUT / "prospective_generation/raw").resolve()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def eos_token_ids(model: Any) -> list[int]:
    value = model.generation_config.eos_token_id
    if value is None:
        return []
    return [int(value)] if isinstance(value, int) else [int(item) for item in value]


def main() -> None:
    world_size, rank, device = distributed_process_info(os.environ, visible_device_count=torch.cuda.device_count())
    config = json.loads((OUT / "config/stage4a_config.json").read_text(encoding="utf-8"))
    expected_world_size = int(config["runtime"]["gpus"])
    if world_size != expected_world_size:
        raise RuntimeError(
            f"Frozen Stage 4A launch requires exactly {expected_world_size} ranks, observed {world_size}"
        )
    torch.cuda.set_device(device)
    parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int,default=800)
    args=parser.parse_args()
    if os.environ.get('SLURM_JOB_ID')!=config['runtime']['slurm_allocation']:
        raise RuntimeError('Must reuse existing user allocation')
    if args.limit not in [800,1200]:raise ValueError('Frozen screen tranche required')
    manifest_path=OUT/'cohort/prospective_screen_manifest.jsonl'
    full=read_jsonl(manifest_path)[:args.limit]
    pending=[r for r in full if r['native_reuse'] is None and (args.limit==800 or r['screen_order']>=800)]
    manifest=pending[rank::world_size]
    output_dir=(ALLOWED/f'shard_{rank:02d}' if args.limit==800 else ALLOWED/f'shard_ext_{rank:02d}').resolve()
    output_dir.relative_to(ALLOWED)

    frozen = config["locked_generation_protocol"]
    max_new_tokens = int(frozen["max_new_tokens"])
    seed = int(frozen["seed"])
    parameters = protocol_parameters("official", max_new_tokens, seed)
    if any(parameters[key] != frozen[key] for key in ("do_sample", "temperature", "top_p", "top_k", "presence_penalty", "max_new_tokens", "seed")):
        raise RuntimeError("Resolved generation protocol differs from frozen Stage 4A config")
    generation_kwargs = transformers_generation_kwargs(parameters)
    signature = {
        "manifest": str(manifest_path.resolve()),
        "example_ids": [str(row["example_id"]) for row in manifest],
        "base_problem_ids": [str(row["base_problem_id"]) for row in manifest],
        "dataset_root": config["dataset_root"],
        "model_checkpoint": config["model_checkpoint"],
        "protocol": parameters,
        "required_gpu_class": config["runtime"]["gpu_class"],
        "world_size": world_size,
        "rank": rank,
        "screen_limit": args.limit,
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "instrumentation": False,
        "selection_used_attention": False,
        "selection_used_generation_outcomes": False,
        "selection_used_carrier_outcomes": False,
    }
    config_path = output_dir / "config.json"
    if output_dir.exists() and any(output_dir.iterdir()):
        if not config_path.is_file():
            raise FileExistsError(f"Non-empty shard has no resumable config: {output_dir}")
        if json.loads(config_path.read_text(encoding="utf-8"))["run_signature"] != signature:
            raise RuntimeError(f"Resume signature mismatch for rank {rank}")
    else:
        ensure_directory(output_dir)
        write_json(config_path, {"created_at": datetime.now(timezone.utc).isoformat(), "run_signature": signature})
        write_jsonl(output_dir / "manifest.jsonl", manifest)

    dataset_root = Path(config["dataset_root"])
    by_id = {str(row["sample_index"]): row for row in load_mathverse_rows(dataset_root)}
    selected = [by_id[str(item["example_id"])] for item in manifest]
    processor, model = load_runtime(Path(config["model_checkpoint"]), device="cuda")
    environment = runtime_environment(Path(config["model_checkpoint"]), model, max_new_tokens)
    if config["runtime"]["gpu_class"] not in str(environment["gpu_name"]):
        raise RuntimeError(f"Expected {config['runtime']['gpu_class']}, observed {environment['gpu_name']}")
    environment.update({"world_size": world_size, "rank": rank, "local_cuda_device": device})
    write_json(output_dir / "environment.json", environment)
    eos_ids = eos_token_ids(model)

    results: list[dict[str, Any]] = []
    for index, (item, row) in enumerate(zip(manifest, selected)):
        if (OUT/'cohort/cohort_freeze_complete.json').exists():
            print('Frozen target cohort reached; stop before next trajectory',flush=True)
            break
        example_id = str(row["sample_index"])
        base = str(row["problem_index"])
        if base != str(item["base_problem_id"]):
            raise RuntimeError(f"Manifest/dataset base mismatch for example {example_id}")
        example_dir = output_dir / "examples" / example_id
        result_path = example_dir / "result.json"
        if result_path.is_file():
            result = json.loads(result_path.read_text(encoding="utf-8"))
            results.append(result)
            print(f"[rank {rank} {index + 1}/{len(manifest)}] resumed base={base}", flush=True)
            continue
        ensure_directory(example_dir)
        prepared, input_record, _ = prepare_example(processor, row, dataset_root, device="cuda")
        write_json(example_dir / "input.json", input_record)
        generation = generate_once(
            model, processor, prepared, max_new_tokens, recorder=None,
            generation_kwargs=generation_kwargs, seed=seed, collect_predictive_metrics=False,
        )
        legacy = classify_protocol_generation(
            generation["generated_token_ids"], generation["full_generated_response"],
            str(row["answer"]), max_new_tokens, eos_ids,
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
            "stage4a_generation_kind": "new_A6000_native",
            "base_problem_id": base,
            "screen_order": int(item["screen_order"]),
            "screen_phase": item["screen_phase"],
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
            f"[rank {rank} {index + 1}/{len(manifest)}] base={base} status={status} "
            f"tokens={result['generated_token_count']} seconds={result['runtime']['elapsed_seconds']:.1f}",
            flush=True,
        )
        del prepared, generation
        gc.collect()
        torch.cuda.empty_cache()

    summary = {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "rank": rank,
        "total": len(results),
        "correct": sum(row["status"] == "correct" for row in results),
        "wrong": sum(row["status"] == "wrong" for row in results),
        "truncated": sum(row["status"] == "truncated" for row in results),
        "invalid": sum(row["status"] == "invalid" for row in results),
        "all_raw_outcomes_preserved": len(results) == len(selected),
        "results": results,
    }
    write_json(output_dir / "result.json", summary)
    print(json.dumps({key: value for key, value in summary.items() if key != "results"}, indent=2), flush=True)


if __name__ == "__main__":
    main()
