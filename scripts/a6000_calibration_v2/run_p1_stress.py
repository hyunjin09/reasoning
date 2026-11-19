#!/usr/bin/env python3
"""Run one frozen historical one-shot-cache A6000 memory stress case."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import torch

from visual_reasoning.a6000_calibration_v2.protocol import validate_stress_manifest
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import load_runtime, prepare_example, runtime_environment
from visual_reasoning.stage3b0.runtime import prefill_condition, score_preference_from_cache


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/a6000_calibration_v2"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def exact_score(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return bool(
        float(left["D"]) == float(right["D"])
        and left["original_candidate"]["token_log_probabilities"]
        == right["original_candidate"]["token_log_probabilities"]
        and left["counterfactual_candidate"]["token_log_probabilities"]
        == right["counterfactual_candidate"]["token_log_probabilities"]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest_path = OUT / "phase1_path_feasibility/stress_manifest.jsonl"
    manifest = read_jsonl(manifest_path)
    validate_stress_manifest(manifest)
    item = next((row for row in manifest if str(row["base_problem_id"]) == str(args.base)), None)
    if item is None:
        raise ValueError("Requested base is outside the frozen P1 stress manifest")
    output = args.output.resolve()
    output.relative_to(OUT.resolve())
    if output.exists():
        raise FileExistsError(output)

    environment = read_json(OUT / "config/environment_freeze.json")
    generation_path = ROOT / item["artifact_dir"] / "generation.json"
    if hashlib.sha256(generation_path.read_bytes()).hexdigest() != item["generation_sha256"]:
        raise RuntimeError("Frozen stress generation hash changed")
    generated = read_json(generation_path)["generated_token_ids"]
    prefix = [int(value) for value in generated[: int(item["stress_prefix_token_count"])]]
    if len(prefix) != int(item["stress_prefix_token_count"]):
        raise RuntimeError("Frozen stress prefix length mismatch")

    dataset = {
        str(row["sample_index"]): row
        for row in load_mathverse_rows(Path(environment["dataset_root"]))
    }
    row = dataset[str(item["example_id"])]
    processor, model = load_runtime(Path(environment["model_checkpoint"]), device="cuda")
    observed_environment = runtime_environment(Path(environment["model_checkpoint"]), model, 40_960)
    if "A6000" not in str(observed_environment["gpu_name"]):
        raise RuntimeError(f"Expected A6000, observed {observed_environment['gpu_name']}")
    if observed_environment["language_attention_implementation"] != "eager":
        raise RuntimeError("P1 stress requires eager language attention")
    prepared, input_record, _ = prepare_example(
        processor, row, Path(environment["dataset_root"]), device="cuda"
    )
    if input_record["image_grid_thw"] != item["image_grid_thw"]:
        raise RuntimeError("Frozen image-grid metadata changed")
    if len(input_record["visual_token_indices"]) != int(item["visual_token_count"]):
        raise RuntimeError("Frozen visual-token count changed")

    result: dict[str, Any] = {
        "base_problem_id": str(item["base_problem_id"]),
        "example_id": str(item["example_id"]),
        "path": "P1_historical_one_shot_cached",
        "stress_order": int(item["stress_order"]),
        "prefix_tokens": len(prefix),
        "reasoning_tokens": int(item["generated_token_count"]),
        "visual_tokens": int(item["visual_token_count"]),
        "candidate_length": int(item["candidate_length"]),
        "physical_vram_bytes": int(observed_environment["gpu_total_memory_bytes"]),
        "attention_backend": observed_environment["language_attention_implementation"],
        "backend_unchanged": observed_environment["language_attention_implementation"] == "eager",
        "silent_truncation": False,
        "mechanical_arms": {
            "native": "attempted",
            "W16": "not_available_without_frozen_target_ROI_and_event",
            "event_span_KV": "not_available_without_frozen_event_annotation",
        },
        "environment": observed_environment,
    }
    started = time.perf_counter()
    try:
        torch.cuda.reset_peak_memory_stats()
        cache, rope, prefill_audit = prefill_condition(model=model, prepared=prepared, seed=1234)
        first = score_preference_from_cache(
            model=model,
            prefill_cache=cache,
            rope_deltas=rope,
            prompt_length=int(prepared["input_ids"].shape[1]),
            visual_token_indices=input_record["visual_token_indices"],
            prefix_token_ids=prefix,
            candidate_original_ids=item["original_suffix_ids"],
            candidate_counterfactual_ids=item["counterfactual_suffix_ids"],
            seed=1234,
            cutoff_enabled=False,
        )
        second = score_preference_from_cache(
            model=model,
            prefill_cache=cache,
            rope_deltas=rope,
            prompt_length=int(prepared["input_ids"].shape[1]),
            visual_token_indices=input_record["visual_token_indices"],
            prefix_token_ids=prefix,
            candidate_original_ids=item["original_suffix_ids"],
            candidate_counterfactual_ids=item["counterfactual_suffix_ids"],
            seed=1234,
            cutoff_enabled=False,
        )
        result.update({
            "status": "PASS",
            "oom": False,
            "finite": bool(first["original_candidate"]["finite"] and first["counterfactual_candidate"]["finite"]),
            "deterministic": exact_score(first, second),
            "prefill_audit": prefill_audit,
            "first_score": first,
            "second_score": second,
        })
        del cache, first, second
    except torch.OutOfMemoryError as error:
        result.update({
            "status": "OOM",
            "oom": True,
            "finite": False,
            "deterministic": False,
            "error_type": type(error).__name__,
            "error": str(error),
        })
    finally:
        result.update({
            "wall_time_seconds": time.perf_counter() - started,
            "peak_allocated_vram_bytes": int(torch.cuda.max_memory_allocated()),
            "peak_reserved_vram_bytes": int(torch.cuda.max_memory_reserved()),
        })
        result["peak_reserved_vram_fraction"] = (
            result["peak_reserved_vram_bytes"] / result["physical_vram_bytes"]
        )
        write_json(output, result)
        del prepared, model, processor
        gc.collect()
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
