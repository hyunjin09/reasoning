#!/usr/bin/env python3
"""Run frozen event-span, constituent-token, and neighbor checkpoint rescue."""

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
from visual_reasoning.stage3c8.runtime import summarize_cache_state_difference
from visual_reasoning.stage3c9.runtime import absolute_reasoning_token_position
from visual_reasoning.stage3c9.streaming import (
    StreamingPrefixState,
    prefill_streaming_state,
    roll_streaming_prefix,
    score_preference_from_streaming_state,
    snapshot_cache_positions,
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
    parser.add_argument("--source-classification", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=("validation", "primary"), required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--repeat-first", action="store_true")
    parser.add_argument("--force-all-windows", action="store_true")
    parser.add_argument("--max-scored-events-per-base", type=int, default=0)
    return parser.parse_args()


def exact_scores(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return bool(
        float(left["D"]) == float(right["D"])
        and left["original_candidate"]["token_log_probabilities"] == right["original_candidate"]["token_log_probabilities"]
        and left["counterfactual_candidate"]["token_log_probabilities"] == right["counterfactual_candidate"]["token_log_probabilities"]
    )


def score_readout(
    *, model: Any, prefill: StreamingPrefixState, sequences: dict[str, Any], event: dict[str, Any],
    windows: list[str], layers: list[int], heads: list[int], target_positions: list[int],
    visual_positions: list[int], seed: int, full_local_controls: bool, validate_controls: bool,
    repeat: bool, streaming_kwargs: dict[str, Any],
) -> dict[str, Any]:
    span = list(range(int(event["span_start_token"]), int(event["span_end_token"])))
    neighbor_row = event["matched_neighbor_span"]
    neighbor = list(range(int(neighbor_row["start_token"]), int(neighbor_row["end_token"])))
    available = [name for name in windows if int(event["span_start_token"]) >= int(name[1:])]
    if not available:
        return {"available": False, "reason": "no_selected_source_window_available"}
    prefix = sequences["prefix_token_ids"]
    forced_boundaries = intervention_boundaries(
        span, neighbor, end_generated_index=len(prefix)
    )
    native_state, native_stream = roll_streaming_prefix(
        model=model, prefill=prefill, prefix_token_ids=prefix,
        end_generated_index=len(prefix), seed=seed,
        forced_generated_boundaries=forced_boundaries, **streaming_kwargs,
    )
    native = score_preference_from_streaming_state(
        model=model, state=native_state,
        original_suffix_ids=sequences["original_suffix_ids"],
        counterfactual_suffix_ids=sequences["counterfactual_suffix_ids"], seed=seed,
    )
    native["streaming_audit"] = native_stream
    prompt_length = int(prefill.prompt_length)
    capture_generated = sorted(set(span + neighbor))
    capture_absolute = [
        absolute_reasoning_token_position(prompt_length=prompt_length, token_index=index)
        for index in capture_generated
    ]
    native_snapshot = snapshot_cache_positions(native_state, absolute_positions=capture_absolute)

    def capture_audit(snapshot: dict[int, tuple[torch.Tensor, torch.Tensor]]) -> list[dict[str, Any]]:
        return [{
            "layer_index": int(layer),
            "layer_selected": True,
            "positions": capture_absolute,
            "post_rope_key": True,
            "value_projection": True,
            "key_shape": list(key.shape),
            "value_shape": list(value.shape),
        } for layer, (key, value) in sorted(snapshot.items())]

    def rescue_arm(
        *, source_window: list[int], patch_positions: list[int], donor: StreamingPrefixState,
        suppression_enabled: bool,
    ) -> dict[str, Any]:
        state, stream = roll_streaming_prefix(
            model=model, prefill=prefill, prefix_token_ids=prefix,
            end_generated_index=len(prefix), seed=seed,
            layers=layers, selected_heads=heads, source_positions=target_positions,
            suppressed_generated_indices=source_window if suppression_enabled else [],
            donor=donor, patch_generated_indices=patch_positions,
            visual_positions=visual_positions,
            forced_generated_boundaries=forced_boundaries, **streaming_kwargs,
        )
        score = score_preference_from_streaming_state(
            model=model, state=state,
            original_suffix_ids=sequences["original_suffix_ids"],
            counterfactual_suffix_ids=sequences["counterfactual_suffix_ids"], seed=seed,
        )
        patch = stream["cache_patch"]
        suppression_rows = [
            row for execution in stream["source_suppression_executions"]
            for row in execution["layer_audits"]
        ]
        score.update({
            "patch_generated_indices": patch["patch_generated_indices"],
            "patch_absolute_positions": patch["patch_absolute_positions"],
            "first_downstream_absolute_query": patch["first_downstream_absolute_query"],
            "cache_mode": "KV",
            "cache_patch_audits": {
                "original_candidate": patch["layer_audits"],
                "counterfactual_candidate": patch["layer_audits"],
            },
            "suppression_audits": {
                "original_candidate": suppression_rows,
                "counterfactual_candidate": suppression_rows,
            },
            "suppression_enabled": suppression_enabled,
            "visual_kv_donor_patched": False,
            "non_event_cache_donor_patched": patch_positions != span,
            "streaming_audit": stream,
        })
        return score

    arms = {}
    for window_name in available:
        source_window = source_window_indices(
            span_start_token=int(event["span_start_token"]), width=int(window_name[1:])
        )
        suppressed_state, suppressed_stream = roll_streaming_prefix(
            model=model, prefill=prefill, prefix_token_ids=prefix,
            end_generated_index=len(prefix), seed=seed,
            layers=layers, selected_heads=heads, source_positions=target_positions,
            suppressed_generated_indices=source_window,
            forced_generated_boundaries=forced_boundaries, **streaming_kwargs,
        )
        suppressed = score_preference_from_streaming_state(
            model=model, state=suppressed_state,
            original_suffix_ids=sequences["original_suffix_ids"],
            counterfactual_suffix_ids=sequences["counterfactual_suffix_ids"], seed=seed,
        )
        suppressed["streaming_audit"] = suppressed_stream
        suppressed_snapshot = snapshot_cache_positions(suppressed_state, absolute_positions=capture_absolute)
        if not validate_controls:
            del suppressed_state
            suppressed_state = None
        event_span = rescue_arm(
            source_window=source_window, patch_positions=span, donor=native_state,
            suppression_enabled=True,
        )
        constituent = {}
        neighbor_score = None
        if full_local_controls:
            constituent = {
                str(position): rescue_arm(
                    source_window=source_window, patch_positions=[position], donor=native_state,
                    suppression_enabled=True,
                )
                for position in span
            }
            neighbor_score = rescue_arm(
                source_window=source_window, patch_positions=neighbor, donor=native_state,
                suppression_enabled=True,
            )
        self_controls = None
        if validate_controls:
            assert suppressed_state is not None
            native_self = rescue_arm(
                source_window=source_window, patch_positions=span, donor=native_state,
                suppression_enabled=False,
            )
            suppressed_self = rescue_arm(
                source_window=source_window, patch_positions=span, donor=suppressed_state,
                suppression_enabled=True,
            )
            self_controls = {
                "native_to_native": native_self,
                "native_to_native_exact": exact_scores(native_self, native),
                "suppressed_to_suppressed": suppressed_self,
                "suppressed_to_suppressed_exact": exact_scores(suppressed_self, suppressed),
            }
        replay = None
        if repeat and window_name == available[0]:
            repeated = rescue_arm(
                source_window=source_window, patch_positions=span, donor=native_state,
                suppression_enabled=True,
            )
            replay = {"exact": exact_scores(repeated, event_span), "arm": "event_span_KV"}
        divergence = summarize_cache_state_difference(native_snapshot, suppressed_snapshot)
        state_divergence = {
            "original_candidate": divergence,
            "counterfactual_candidate": divergence,
        }
        suppression_rows = [
            row for execution in suppressed_stream["source_suppression_executions"]
            for row in execution["layer_audits"]
        ]
        arms[window_name] = {
            "source_window_generated_indices": source_window,
            "native": native,
            "suppressed": suppressed,
            "event_span_rescue": event_span,
            "constituent_token_rescue": constituent,
            "matched_neighbor_rescue": neighbor_score,
            "matched_neighbor_generated_indices": neighbor,
            "cache_state_divergence": state_divergence,
            "capture_audits": {
                "native": {
                    candidate: {
                        "cache": capture_audit(native_snapshot),
                        "suppression": [],
                    }
                    for candidate in ("original_candidate", "counterfactual_candidate")
                },
                "suppressed": {
                    candidate: {
                        "cache": capture_audit(suppressed_snapshot),
                        "suppression": suppression_rows,
                    }
                    for candidate in ("original_candidate", "counterfactual_candidate")
                },
            },
            "self_controls": self_controls,
            "deterministic_replay": replay,
        }
        if suppressed_state is not None:
            del suppressed_state
        del suppressed_snapshot
    del native_state, native_snapshot
    return {
        "available": True,
        "readout_generated_index": int(sequences["readout_generated_index"]),
        "prefix_sha256": sequences["prefix_sha256"],
        "prefix_hash_exact": True,
        "span_generated_indices": span,
        "neighbor_generated_indices": neighbor,
        "windows": arms,
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
    source_rows = {
        (str(row["base_problem_id"]), int(row["event_id"])): row
        for row in read_jsonl(args.source_classification)
    }
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
        "mode": args.mode,
        "manifest": str(args.manifest.resolve()),
        "source_classification": str(args.source_classification.resolve()),
        "rank": rank,
        "world_size": world_size,
        "runtime_mode": "bounded_native_eager_cache",
        "query_chunk_size": streaming_kwargs["chunk_size"],
        "release_allocator_cache_between_chunks": streaming_kwargs["release_allocator_cache"],
        "condition_invariant_chunking": True,
        "force_all_windows": bool(args.force_all_windows),
        "max_scored_events_per_base": int(args.max_scored_events_per_base),
        "layers": layers,
        "logical_heads": heads,
        "cache_mode": "KV",
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
        token_rows = read_jsonl(ROOT / item["tokens_path"])
        prepared, metadata, prefill = {}, {}, {}
        for condition in SEMANTIC_CONDITIONS:
            prepared[condition], metadata[condition] = prepare_custom_image(
                processor,
                dataset[str(item["example_id"])],
                ROOT / edit["paths"][condition],
                device="cuda",
            )
            prefill[condition], _ = prefill_streaming_state(
                model=model, prepared=prepared[condition], seed=int(config["runtime"]["seed"]),
            )
        if metadata["O"]["prompt_token_ids"] != metadata["C"]["prompt_token_ids"] or metadata["O"]["image_grid_thw"] != metadata["C"]["image_grid_thw"]:
            raise RuntimeError(f"O/C layout mismatch for base {base}")
        visual_positions = [int(value) for value in metadata["O"]["visual_token_indices"]]
        target_positions = [int(value) for value in item["roi_mapping"]["absolute_source_groups"]["V_target"]]
        if visual_positions != [int(value) for value in item["roi_mapping"]["absolute_source_groups"]["V_all"]]:
            raise RuntimeError(f"Frozen ROI visual layout mismatch for base {base}")
        final_sequences = exact_readout_sequences(token_rows, item["final_use_readout"])
        event_results = []
        for event_index, event in enumerate(item["events"]):
            selected = source_rows[(base, int(event["event_id"]))]
            within_limit = not args.max_scored_events_per_base or event_index < args.max_scored_events_per_base
            windows = (["W8", "W16"] if args.force_all_windows else list(selected["source_sensitive_windows"])) if within_limit else []
            local_sequences = exact_readout_sequences(token_rows, event["local_use_readout"])
            condition_results = {}
            for condition in SEMANTIC_CONDITIONS:
                local = score_readout(
                    model=model,
                    prefill=prefill[condition],
                    sequences=local_sequences,
                    event=event,
                    windows=windows,
                    layers=layers,
                    heads=heads,
                    target_positions=target_positions,
                    visual_positions=visual_positions,
                    seed=int(config["runtime"]["seed"]),
                    full_local_controls=True,
                    validate_controls=args.mode == "validation",
                    repeat=bool(args.mode == "validation" and args.repeat_first and item_index == 0 and event_index == 0 and condition == "O"),
                    streaming_kwargs=streaming_kwargs,
                )
                if local_sequences["prefix_sha256"] == final_sequences["prefix_sha256"]:
                    final = local
                else:
                    final = score_readout(
                        model=model,
                        prefill=prefill[condition],
                        sequences=final_sequences,
                        event=event,
                        windows=windows,
                        layers=layers,
                        heads=heads,
                        target_positions=target_positions,
                        visual_positions=visual_positions,
                        seed=int(config["runtime"]["seed"]),
                        full_local_controls=False,
                        validate_controls=False,
                        repeat=False,
                        streaming_kwargs=streaming_kwargs,
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
                "source_sensitive_windows": list(selected["source_sensitive_windows"]),
                "scored_windows": windows,
                "conditions": condition_results,
            })
        result = {
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "cohort_role": args.mode,
            "events": event_results,
            "target_positions": target_positions,
            "visual_positions": visual_positions,
            "cache_mode": "KV",
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
