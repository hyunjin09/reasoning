#!/usr/bin/env python3
"""Run prospective W8/W16 Stage 3C.9 event-local source sensitivity."""

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
from visual_reasoning.stage3c3.runtime import score_evidence_suffix
from visual_reasoning.stage3c8.protocol import distributed_process_info
from visual_reasoning.stage3c9.assay import CONDITIONS, exact_readout_sequences, source_window_indices
from visual_reasoning.stage3c9.protocol import canonical_streaming_kwargs
from visual_reasoning.stage3c9.streaming import (
    StreamingPrefixState,
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
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=("validation", "primary"), required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--repeat-first", action="store_true")
    return parser.parse_args()


def exact_scores(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return bool(
        float(left["D"]) == float(right["D"])
        and left["original_candidate"]["token_log_probabilities"] == right["original_candidate"]["token_log_probabilities"]
        and left["counterfactual_candidate"]["token_log_probabilities"] == right["counterfactual_candidate"]["token_log_probabilities"]
    )


def full_prefix_native_score(
    *, model: Any, prepared: dict[str, Any], sequences: dict[str, Any], seed: int,
) -> dict[str, Any]:
    candidates = {
        name: score_evidence_suffix(
            model=model,
            prepared=prepared,
            prefix_token_ids=sequences["prefix_token_ids"],
            bridge_token_ids=[],
            suffix_token_ids=suffix,
            seed=seed,
        )
        for name, suffix in (
            ("original_candidate", sequences["original_suffix_ids"]),
            ("counterfactual_candidate", sequences["counterfactual_suffix_ids"]),
        )
    }
    lo = float(candidates["original_candidate"]["mean_log_probability"])
    lc = float(candidates["counterfactual_candidate"]["mean_log_probability"])
    return {"L_o": lo, "L_c": lc, "D": lo - lc, **candidates}


def score_readout(
    *, model: Any, prefill: StreamingPrefixState, sequences: dict[str, Any],
    event_start: int, layers: list[int], heads: list[int], source_positions: list[int],
    seed: int, repeat: bool, streaming_kwargs: dict[str, Any],
) -> dict[str, Any]:
    prefix = sequences["prefix_token_ids"]
    native_state, native_audit = roll_streaming_prefix(
        model=model, prefill=prefill, prefix_token_ids=prefix,
        end_generated_index=len(prefix), seed=seed, **streaming_kwargs,
    )
    native = score_preference_from_streaming_state(
        model=model, state=native_state,
        original_suffix_ids=sequences["original_suffix_ids"],
        counterfactual_suffix_ids=sequences["counterfactual_suffix_ids"], seed=seed,
    )
    native["streaming_audit"] = native_audit
    del native_state
    windows = {}
    for width in (8, 16):
        if int(event_start) < width:
            windows[f"W{width}"] = {"available": False, "reason": "event_precedes_full_window"}
            continue
        query_indices = source_window_indices(span_start_token=event_start, width=width)
        suppressed_state, suppression_audit = roll_streaming_prefix(
            model=model, prefill=prefill, prefix_token_ids=prefix,
            end_generated_index=len(prefix), seed=seed,
            layers=layers, selected_heads=heads, source_positions=source_positions,
            suppressed_generated_indices=query_indices, **streaming_kwargs,
        )
        suppressed = score_preference_from_streaming_state(
            model=model, state=suppressed_state,
            original_suffix_ids=sequences["original_suffix_ids"],
            counterfactual_suffix_ids=sequences["counterfactual_suffix_ids"], seed=seed,
        )
        executions = suppression_audit["source_suppression_executions"]
        layer_audits = [row for execution in executions for row in execution["layer_audits"]]
        suppressed.update({
            "candidate_audits": {
                "original_candidate": layer_audits,
                "counterfactual_candidate": layer_audits,
            },
            "query_generated_indices": query_indices,
            "absolute_query_positions": executions[0]["absolute_query_positions"] if len(executions) == 1 else [
                value for execution in executions for value in execution["absolute_query_positions"]
            ],
            "layer_indices": layers,
            "selected_heads": heads,
            "source_positions": source_positions,
            "gain": 0.0,
            "streaming_audit": suppression_audit,
        })
        del suppressed_state
        replay = None
        if repeat and width == 8:
            repeated_state, _ = roll_streaming_prefix(
                model=model, prefill=prefill, prefix_token_ids=prefix,
                end_generated_index=len(prefix), seed=seed,
                layers=layers, selected_heads=heads, source_positions=source_positions,
                suppressed_generated_indices=query_indices, **streaming_kwargs,
            )
            repeated = score_preference_from_streaming_state(
                model=model, state=repeated_state,
                original_suffix_ids=sequences["original_suffix_ids"],
                counterfactual_suffix_ids=sequences["counterfactual_suffix_ids"], seed=seed,
            )
            replay = {"exact": exact_scores(repeated, suppressed)}
        windows[f"W{width}"] = {
            "available": True,
            "query_generated_indices": query_indices,
            "native": native,
            "suppressed": suppressed,
            "deterministic_replay": replay,
        }
    return {
        "readout_generated_index": int(sequences["readout_generated_index"]),
        "prefix_sha256": sequences["prefix_sha256"],
        "prefix_hash_exact": True,
        "windows": windows,
    }


def main() -> None:
    args = parse_args()
    config = read_json(OUT / "config/stage3c9_config.json")
    streaming_kwargs = canonical_streaming_kwargs(config)
    world_size, rank, device = distributed_process_info(os.environ, visible_device_count=torch.cuda.device_count())
    torch.cuda.set_device(device)
    output = args.output_dir.resolve()
    output.relative_to(OUT.resolve())
    if world_size > 1:
        output = output / f"shard_{rank}"
    manifest = read_jsonl(args.manifest)[rank::world_size]
    if not manifest:
        raise ValueError("Rank-local source-sensitivity manifest is empty")
    dataset = {str(row["sample_index"]): row for row in load_mathverse_rows(Path(config["dataset_root"]))}
    processor, model = load_runtime(Path(config["model_checkpoint"]), device="cuda")
    environment = runtime_environment(Path(config["model_checkpoint"]), model, 40_960)
    if config["runtime"]["gpu_class"] not in str(environment["gpu_name"]):
        raise RuntimeError(f"Expected {config['runtime']['gpu_class']}, observed {environment['gpu_name']}")
    architecture = {
        "language_layers": int(model.config.text_config.num_hidden_layers),
        "logical_query_heads": int(model.config.text_config.num_attention_heads),
        "kv_heads": int(model.config.text_config.num_key_value_heads),
        "query_heads_per_kv_group": int(model.config.text_config.num_attention_heads // model.config.text_config.num_key_value_heads),
        "head_dimension": int(model.config.text_config.head_dim),
    }
    if architecture != config["architecture"]:
        raise RuntimeError(f"Architecture drift: {architecture}")
    layers = list(range(architecture["language_layers"]))
    heads = list(range(architecture["logical_query_heads"]))
    ensure_directory(output)
    write_json(output / "environment.json", {**environment, "rank": rank, "world_size": world_size, "architecture": architecture})
    write_json(output / "run_config.json", {
        "mode": args.mode,
        "manifest": str(args.manifest.resolve()),
        "rank": rank,
        "world_size": world_size,
        "runtime_mode": "bounded_native_eager_cache",
        "query_chunk_size": streaming_kwargs["chunk_size"],
        "release_allocator_cache_between_chunks": streaming_kwargs["release_allocator_cache"],
        "condition_invariant_chunking": True,
        "W8_and_W16_prospective": True,
        "layers": layers,
        "logical_heads": heads,
        "base_problem_ids": [str(row["base_problem_id"]) for row in manifest],
    })
    torch.cuda.reset_peak_memory_stats()
    run_started = time.perf_counter()
    completed = 0
    for item_index, item in enumerate(manifest):
        base = str(item["base_problem_id"])
        result_path = output / "examples" / base / "result.json"
        if result_path.is_file():
            if not args.resume:
                raise FileExistsError(result_path)
            completed += 1
            print(f"[{completed}/{len(manifest)}] resume skip base={base}", flush=True)
            continue
        started = time.perf_counter()
        edit = read_json(ROOT / item["edit_metadata"])
        if edit["manual_validation"]["status"] != "pass":
            raise RuntimeError(f"Edit validation not passed for base {base}")
        token_rows = read_jsonl(ROOT / item["tokens_path"])
        paths = {name: ROOT / edit["paths"][name] for name in CONDITIONS}
        prepared, metadata, prefill = {}, {}, {}
        for condition in CONDITIONS:
            prepared[condition], metadata[condition] = prepare_custom_image(
                processor, dataset[str(item["example_id"])], paths[condition], device="cuda"
            )
            prefill[condition], _ = prefill_streaming_state(
                model=model, prepared=prepared[condition], seed=int(config["runtime"]["seed"]),
            )
        prompt_ids = [metadata[name]["prompt_token_ids"] for name in CONDITIONS]
        grids = [metadata[name]["image_grid_thw"] for name in CONDITIONS]
        if not all(value == prompt_ids[0] for value in prompt_ids[1:]) or not all(value == grids[0] for value in grids[1:]):
            raise RuntimeError(f"Four-condition layout mismatch for base {base}")
        visual_positions = [int(value) for value in metadata["O"]["visual_token_indices"]]
        if visual_positions != [int(value) for value in item["roi_mapping"]["absolute_source_groups"]["V_all"]]:
            raise RuntimeError(f"Frozen ROI visual layout mismatch for base {base}")
        target_positions = [int(value) for value in item["roi_mapping"]["absolute_source_groups"]["V_target"]]
        final_sequences = exact_readout_sequences(token_rows, item["final_use_readout"])
        event_results = []
        for event_index, event in enumerate(item["events"]):
            local_sequences = exact_readout_sequences(token_rows, event["local_use_readout"])
            local_equals_final = local_sequences["prefix_sha256"] == final_sequences["prefix_sha256"]
            condition_results = {}
            for condition in CONDITIONS:
                local = score_readout(
                    model=model,
                    prefill=prefill[condition],
                    sequences=local_sequences,
                    event_start=int(event["span_start_token"]),
                    layers=layers,
                    heads=heads,
                    source_positions=target_positions,
                    seed=int(config["runtime"]["seed"]),
                    streaming_kwargs=streaming_kwargs,
                    repeat=bool(args.mode == "validation" and args.repeat_first and item_index == 0 and event_index == 0 and condition == "O"),
                )
                if args.mode == "validation" and item_index == 0 and event_index == 0 and condition == "O":
                    full = full_prefix_native_score(
                        model=model, prepared=prepared[condition], sequences=local_sequences,
                        seed=int(config["runtime"]["seed"]),
                    )
                    cached = local["windows"]["W8"]["native"]
                    local["streaming_full_prefix_parity"] = {
                        "exact": exact_scores(cached, full),
                        "streaming": cached,
                        "full_prefix": full,
                        "readout_generated_index": int(local_sequences["readout_generated_index"]),
                    }
                final = local if local_equals_final else score_readout(
                    model=model,
                    prefill=prefill[condition],
                    sequences=final_sequences,
                    event_start=int(event["span_start_token"]),
                    layers=layers,
                    heads=heads,
                    source_positions=target_positions,
                    seed=int(config["runtime"]["seed"]),
                    streaming_kwargs=streaming_kwargs,
                    repeat=False,
                )
                condition_results[condition] = {"local_use": local, "final_use": final}
            event_results.append({
                "event_id": int(event["event_id"]),
                "event_role": event["event_role"],
                "evidence_relation": event["evidence_relation"],
                "temporal_location": event["temporal_location"],
                "span_start_token": int(event["span_start_token"]),
                "span_end_token": int(event["span_end_token"]),
                "span_text": event["span_text"],
                "local_equals_final": local_equals_final,
                "conditions": condition_results,
            })
        result = {
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "cohort_role": args.mode,
            "events": event_results,
            "target_positions": target_positions,
            "visual_positions": visual_positions,
            "prompt_token_ids_exact_across_conditions": True,
            "image_grid_exact_across_conditions": True,
            "selection_used_attention": False,
            "runtime_seconds": time.perf_counter() - started,
        }
        write_json(result_path, result)
        completed += 1
        print(f"[{completed}/{len(manifest)}] base={base} events={len(event_results)} seconds={result['runtime_seconds']:.1f}", flush=True)
        del prepared, prefill
        gc.collect()
        torch.cuda.empty_cache()
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    write_json(output / "run_summary.json", {
        "mode": args.mode,
        "completed": completed,
        "expected": len(manifest),
        "runtime_seconds": time.perf_counter() - run_started,
        "peak_gpu_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "peak_gpu_reserved_bytes": int(torch.cuda.max_memory_reserved()),
    })


if __name__ == "__main__":
    main()
