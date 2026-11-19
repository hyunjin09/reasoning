#!/usr/bin/env python3
"""Run one frozen fixed-chunk streaming A6000 memory stress case."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import torch

from visual_reasoning.a6000_calibration_v2.protocol import (
    token_by_token_is_unlocked,
    validate_stress_manifest,
)
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import load_runtime, prepare_example, runtime_environment
from visual_reasoning.stage3c9.streaming import (
    prefill_streaming_state,
    roll_streaming_prefix,
    score_preference_from_streaming_state,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/a6000_calibration_v2"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--chunk-size", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device-index", type=int, default=0)
    parser.add_argument("--release-allocator-cache", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.device_index < 0 or args.device_index >= torch.cuda.device_count():
        raise ValueError("Device index is outside the Slurm-assigned CUDA device pool")
    torch.cuda.set_device(int(args.device_index))
    device = f"cuda:{int(args.device_index)}"
    chunking = read_json(OUT / "config/canonical_chunking.json")
    candidates = [int(value) for value in chunking["candidate_chunk_sizes_descending"]]
    if int(args.chunk_size) not in candidates:
        prior_rows = [
            read_json(path)
            for path in sorted((OUT / "phase1_path_feasibility").glob("p2_chunk*_base*.json"))
        ]
        fallback_allowed = (
            int(args.chunk_size) == 1
            and bool(chunking["token_by_token_allowed_only_if_all_listed_candidates_fail"])
            and token_by_token_is_unlocked(
                prior_rows,
                candidates_descending=candidates,
                gate_base="351",
                memory_fraction_max=0.90,
            )
        )
        if not fallback_allowed:
            raise ValueError("Chunk size is outside the prospectively frozen ladder")
    manifest = read_jsonl(OUT / "phase1_path_feasibility/stress_manifest.jsonl")
    validate_stress_manifest(manifest)
    item = next((row for row in manifest if str(row["base_problem_id"]) == str(args.base)), None)
    if item is None:
        raise ValueError("Requested base is outside the frozen P2 stress manifest")
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
    dataset = {
        str(row["sample_index"]): row
        for row in load_mathverse_rows(Path(environment["dataset_root"]))
    }
    processor, model = load_runtime(Path(environment["model_checkpoint"]), device=device)
    observed_environment = runtime_environment(Path(environment["model_checkpoint"]), model, 40_960)
    observed_environment.update({
        "selected_cuda_device_index": int(args.device_index),
        "release_allocator_cache_between_chunks": bool(args.release_allocator_cache),
        "selected_cuda_device_name": torch.cuda.get_device_name(int(args.device_index)),
        "selected_cuda_total_memory_bytes": int(
            torch.cuda.get_device_properties(int(args.device_index)).total_memory
        ),
    })
    if "A6000" not in str(observed_environment["gpu_name"]):
        raise RuntimeError(f"Expected A6000, observed {observed_environment['gpu_name']}")
    if observed_environment["language_attention_implementation"] != "eager":
        raise RuntimeError("P2 stress requires eager language attention")
    prepared, input_record, _ = prepare_example(
        processor,
        dataset[str(item["example_id"])],
        Path(environment["dataset_root"]),
        device=device,
    )
    if input_record["image_grid_thw"] != item["image_grid_thw"]:
        raise RuntimeError("Frozen image-grid metadata changed")
    if len(input_record["visual_token_indices"]) != int(item["visual_token_count"]):
        raise RuntimeError("Frozen visual-token count changed")

    result: dict[str, Any] = {
        "base_problem_id": str(item["base_problem_id"]),
        "example_id": str(item["example_id"]),
        "path": "P2_fixed_streaming_cached",
        "chunk_size": int(args.chunk_size),
        "stress_order": int(item["stress_order"]),
        "prefix_tokens": len(prefix),
        "reasoning_tokens": int(item["generated_token_count"]),
        "visual_tokens": int(item["visual_token_count"]),
        "candidate_length": int(item["candidate_length"]),
        "physical_vram_bytes": int(observed_environment["selected_cuda_total_memory_bytes"]),
        "selected_cuda_device_index": int(args.device_index),
        "attention_backend": observed_environment["language_attention_implementation"],
        "backend_unchanged": observed_environment["language_attention_implementation"] == "eager",
        "silent_truncation": False,
        "environment": observed_environment,
    }
    started = time.perf_counter()
    try:
        torch.cuda.reset_peak_memory_stats()
        prefill, prefill_audit = prefill_streaming_state(model=model, prepared=prepared, seed=1234)
        state, streaming_audit = roll_streaming_prefix(
            model=model,
            prefill=prefill,
            prefix_token_ids=prefix,
            end_generated_index=len(prefix),
            seed=1234,
            chunk_size=int(args.chunk_size),
            release_allocator_cache=bool(args.release_allocator_cache),
        )
        score = score_preference_from_streaming_state(
            model=model,
            state=state,
            original_suffix_ids=item["original_suffix_ids"],
            counterfactual_suffix_ids=item["counterfactual_suffix_ids"],
            seed=1234,
        )
        result.update({
            "status": "PASS",
            "oom": False,
            "finite": bool(score["finite"]),
            "prefill_audit": prefill_audit,
            "streaming_audit": streaming_audit,
            "score": score,
        })
        del prefill, state, score
    except torch.OutOfMemoryError as error:
        result.update({
            "status": "OOM",
            "oom": True,
            "finite": False,
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
