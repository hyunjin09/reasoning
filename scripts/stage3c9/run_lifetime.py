#!/usr/bin/env python3
"""Score confirmed Stage 3C.9 checkpoints at downstream semantic readouts."""

from __future__ import annotations

import argparse
import gc
import json
import os
import time
from pathlib import Path
from typing import Any

import torch

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import ensure_directory, write_json
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3c8.protocol import distributed_process_info
from visual_reasoning.stage3c9.assay import SEMANTIC_CONDITIONS, exact_readout_sequences, source_window_indices
from visual_reasoning.stage3c9.protocol import canonical_streaming_kwargs, intervention_boundaries
from visual_reasoning.stage3c9.streaming import (
    prefill_streaming_state,
    roll_streaming_prefix,
    score_preference_from_streaming_state,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--classification", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = read_json(OUT / "config/stage3c9_config.json")
    streaming_kwargs = canonical_streaming_kwargs(config)
    classes = {
        str(row["base_problem_id"]): row
        for row in read_json(args.classification)["bases"]
    }
    world_size, rank, device = distributed_process_info(os.environ, visible_device_count=torch.cuda.device_count())
    torch.cuda.set_device(device)
    output = args.output_dir.resolve()
    output.relative_to(OUT.resolve())
    if world_size > 1:
        output = output / f"shard_{rank}"
    manifest = read_jsonl(args.manifest)[rank::world_size]
    dataset = {str(row["sample_index"]): row for row in load_mathverse_rows(Path(config["dataset_root"]))}
    processor, model = load_runtime(Path(config["model_checkpoint"]), device="cuda")
    environment = runtime_environment(Path(config["model_checkpoint"]), model, 40_960)
    if config["runtime"]["gpu_class"] not in str(environment["gpu_name"]):
        raise RuntimeError(f"Expected {config['runtime']['gpu_class']}, observed {environment['gpu_name']}")
    layers = list(range(int(model.config.text_config.num_hidden_layers)))
    heads = list(range(int(model.config.text_config.num_attention_heads)))
    ensure_directory(output)
    write_json(output / "environment.json", {**environment, "rank": rank, "world_size": world_size})
    write_json(output / "run_config.json", {
        "manifest": str(args.manifest.resolve()),
        "classification": str(args.classification.resolve()),
        "rank": rank,
        "world_size": world_size,
        "runtime_mode": "bounded_native_eager_cache",
        "query_chunk_size": streaming_kwargs["chunk_size"],
        "release_allocator_cache_between_chunks": streaming_kwargs["release_allocator_cache"],
        "condition_invariant_chunking": True,
        "only_independently_annotated_downstream_readouts": True,
        "pseudo_readouts_used": False,
        "base_problem_ids": [str(row["base_problem_id"]) for row in manifest],
    })
    torch.cuda.reset_peak_memory_stats()
    run_started = time.perf_counter()
    completed = 0
    for item in manifest:
        base = str(item["base_problem_id"])
        result_path = output / "examples" / base / "result.json"
        if result_path.is_file():
            if not args.resume:
                raise FileExistsError(result_path)
            completed += 1
            print(f"[{completed}/{len(manifest)}] resume skip base={base}", flush=True)
            continue
        started = time.perf_counter()
        class_events = {int(row["event_id"]): row for row in classes[base]["events"]}
        edit = read_json(ROOT / item["edit_metadata"])
        token_rows = read_jsonl(ROOT / item["tokens_path"])
        prepared, metadata, prefill = {}, {}, {}
        for condition in SEMANTIC_CONDITIONS:
            prepared[condition], metadata[condition] = prepare_custom_image(
                processor, dataset[str(item["example_id"])], ROOT / edit["paths"][condition], device="cuda"
            )
            prefill[condition], _ = prefill_streaming_state(
                model=model, prepared=prepared[condition], seed=int(config["runtime"]["seed"]),
            )
        if metadata["O"]["prompt_token_ids"] != metadata["C"]["prompt_token_ids"]:
            raise RuntimeError(f"O/C prompt layout mismatch for base {base}")
        visual_positions = [int(value) for value in metadata["O"]["visual_token_indices"]]
        target_positions = [int(value) for value in item["roi_mapping"]["absolute_source_groups"]["V_target"]]
        final_index = int(item["final_use_readout"]["token_index"])
        event_results = []
        ordered = sorted(item["events"], key=lambda row: int(row["span_start_token"]))
        for event_position, event in enumerate(ordered):
            classification = class_events[int(event["event_id"])]
            if classification["classification"] not in {"C2", "C3"}:
                continue
            downstream_events = [
                row for row in ordered[event_position + 1:]
                if int(row["local_use_readout"]["token_index"]) < final_index
            ]
            if not downstream_events:
                continue
            span = list(range(int(event["span_start_token"]), int(event["span_end_token"])))
            window_results = {}
            for window_name in classification["qualifying_windows"]:
                source_window = source_window_indices(
                    span_start_token=int(event["span_start_token"]), width=int(window_name[1:])
                )
                readout_results = []
                for downstream in downstream_events:
                    sequences = exact_readout_sequences(token_rows, downstream["local_use_readout"])
                    condition_results = {}
                    for condition in SEMANTIC_CONDITIONS:
                        prefix = sequences["prefix_token_ids"]
                        forced_boundaries = intervention_boundaries(
                            [span[-1]], end_generated_index=len(prefix)
                        )
                        native_state, native_audit = roll_streaming_prefix(
                            model=model, prefill=prefill[condition], prefix_token_ids=prefix,
                            end_generated_index=len(prefix), seed=int(config["runtime"]["seed"]),
                            forced_generated_boundaries=forced_boundaries, **streaming_kwargs,
                        )
                        native = score_preference_from_streaming_state(
                            model=model, state=native_state,
                            original_suffix_ids=sequences["original_suffix_ids"],
                            counterfactual_suffix_ids=sequences["counterfactual_suffix_ids"],
                            seed=int(config["runtime"]["seed"]),
                        )
                        native["streaming_audit"] = native_audit
                        suppressed_state, suppressed_audit = roll_streaming_prefix(
                            model=model, prefill=prefill[condition], prefix_token_ids=prefix,
                            end_generated_index=len(prefix), seed=int(config["runtime"]["seed"]),
                            layers=layers, selected_heads=heads, source_positions=target_positions,
                            suppressed_generated_indices=source_window,
                            forced_generated_boundaries=forced_boundaries, **streaming_kwargs,
                        )
                        suppressed = score_preference_from_streaming_state(
                            model=model, state=suppressed_state,
                            original_suffix_ids=sequences["original_suffix_ids"],
                            counterfactual_suffix_ids=sequences["counterfactual_suffix_ids"],
                            seed=int(config["runtime"]["seed"]),
                        )
                        suppressed["streaming_audit"] = suppressed_audit
                        del suppressed_state
                        rescue_state, rescue_audit = roll_streaming_prefix(
                            model=model, prefill=prefill[condition], prefix_token_ids=prefix,
                            end_generated_index=len(prefix), seed=int(config["runtime"]["seed"]),
                            layers=layers, selected_heads=heads, source_positions=target_positions,
                            suppressed_generated_indices=source_window,
                            donor=native_state, patch_generated_indices=span,
                            visual_positions=visual_positions,
                            forced_generated_boundaries=forced_boundaries, **streaming_kwargs,
                        )
                        rescue = score_preference_from_streaming_state(
                            model=model, state=rescue_state,
                            original_suffix_ids=sequences["original_suffix_ids"],
                            counterfactual_suffix_ids=sequences["counterfactual_suffix_ids"],
                            seed=int(config["runtime"]["seed"]),
                        )
                        rescue["streaming_audit"] = rescue_audit
                        condition_results[condition] = {
                            "native": native,
                            "suppressed": suppressed,
                            "event_span_rescue": rescue,
                        }
                        del native_state, rescue_state
                    readout_results.append({
                        "downstream_event_id": int(downstream["event_id"]),
                        "downstream_readout_generated_index": int(sequences["readout_generated_index"]),
                        "distance_from_checkpoint_end": int(sequences["readout_generated_index"]) - int(event["span_end_token"]),
                        "prefix_sha256": sequences["prefix_sha256"],
                        "conditions": condition_results,
                    })
                window_results[window_name] = readout_results
            event_results.append({
                "event_id": int(event["event_id"]),
                "classification": classification["classification"],
                "span_start_token": int(event["span_start_token"]),
                "span_end_token": int(event["span_end_token"]),
                "qualifying_windows": classification["qualifying_windows"],
                "windows": window_results,
            })
        result = {
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "events": event_results,
            "pseudo_readouts_used": False,
            "selection_used_attention": False,
            "runtime_seconds": time.perf_counter() - started,
        }
        write_json(result_path, result)
        completed += 1
        print(f"[{completed}/{len(manifest)}] base={base} lifetime_events={len(event_results)} seconds={result['runtime_seconds']:.1f}", flush=True)
        del prepared, prefill
        gc.collect()
        torch.cuda.empty_cache()
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    write_json(output / "run_summary.json", {
        "completed": completed,
        "expected": len(manifest),
        "runtime_seconds": time.perf_counter() - run_started,
        "peak_gpu_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "peak_gpu_reserved_bytes": int(torch.cuda.max_memory_reserved()),
    })


if __name__ == "__main__":
    main()
