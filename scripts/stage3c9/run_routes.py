#!/usr/bin/env python3
"""Run gated direct/prior-history/joint Stage 3C.9 route interventions."""

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
from visual_reasoning.stage3c9.runtime import absolute_reasoning_token_position, validate_route_coordinates
from visual_reasoning.stage3c9.streaming import (
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
    parser.add_argument("--pair-manifest", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=("validation", "primary"), required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--repeat-first", action="store_true")
    return parser.parse_args()


def annotation_pair(item: dict[str, Any]) -> dict[str, Any]:
    events = sorted(item["events"], key=lambda row: int(row["span_start_token"]))
    for left_index, left in enumerate(events):
        for right in events[left_index + 1:]:
            if int(right["span_start_token"]) - int(left["span_start_token"]) >= 24:
                return {"event_a_id": int(left["event_id"]), "event_b_id": int(right["event_id"])}
    raise RuntimeError(f"No separated annotated route pair for base {item['base_problem_id']}")


def exact_scores(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return bool(
        float(left["D"]) == float(right["D"])
        and left["original_candidate"]["token_log_probabilities"] == right["original_candidate"]["token_log_probabilities"]
        and left["counterfactual_candidate"]["token_log_probabilities"] == right["counterfactual_candidate"]["token_log_probabilities"]
    )


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
    manifest_all = read_jsonl(args.manifest)
    pair_by_base = {
        str(row["base_problem_id"]): row["route_pair"]
        for row in read_jsonl(args.pair_manifest)
    } if args.pair_manifest else {}
    eligible = []
    for item in manifest_all:
        base = str(item["base_problem_id"])
        if args.mode == "validation":
            pair = annotation_pair(item)
        else:
            pair = pair_by_base.get(base)
            if pair is None:
                continue
        eligible.append((item, pair))
    if args.mode == "validation":
        eligible = eligible[:3]
    eligible = eligible[rank::world_size]
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
        "pair_manifest": None if args.pair_manifest is None else str(args.pair_manifest.resolve()),
        "rank": rank,
        "world_size": world_size,
        "runtime_mode": "bounded_native_eager_cache",
        "query_chunk_size": streaming_kwargs["chunk_size"],
        "release_allocator_cache_between_chunks": streaming_kwargs["release_allocator_cache"],
        "condition_invariant_chunking": True,
        "pair_selection": "first eligible by annotation order",
        "base_problem_ids": [str(item["base_problem_id"]) for item, _ in eligible],
    })
    torch.cuda.reset_peak_memory_stats()
    run_started = time.perf_counter()
    completed = 0
    for item_index, (item, pair) in enumerate(eligible):
        base = str(item["base_problem_id"])
        result_path = output / "examples" / base / "result.json"
        if result_path.is_file():
            if not args.resume:
                raise FileExistsError(result_path)
            completed += 1
            print(f"[{completed}/{len(eligible)}] resume skip base={base}", flush=True)
            continue
        started = time.perf_counter()
        events = {int(row["event_id"]): row for row in item["events"]}
        event_a = events[int(pair["event_a_id"])]
        event_b = events[int(pair["event_b_id"])]
        sequences = exact_readout_sequences(
            read_jsonl(ROOT / item["tokens_path"]), event_b["local_use_readout"]
        )
        coordinates = validate_route_coordinates(
            event_a_span=list(range(int(event_a["span_start_token"]), int(event_a["span_end_token"]))),
            event_b_span=list(range(int(event_b["span_start_token"]), int(event_b["span_end_token"]))),
            readout_generated_index=int(sequences["readout_generated_index"]),
        )
        edit = read_json(ROOT / item["edit_metadata"])
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
        condition_results = {}
        for condition in SEMANTIC_CONDITIONS:
            prefix = sequences["prefix_token_ids"]
            seed = int(config["runtime"]["seed"])
            a_window = source_window_indices(
                span_start_token=int(event_a["span_start_token"]), width=8
            )
            forced_boundaries = intervention_boundaries(
                [coordinates["prior_checkpoint_positions"][-1]],
                [coordinates["short_history_positions"][-1]],
                end_generated_index=len(prefix),
            )
            native_state, native_audit = roll_streaming_prefix(
                model=model, prefill=prefill[condition], prefix_token_ids=prefix,
                end_generated_index=len(prefix), seed=seed,
                forced_generated_boundaries=forced_boundaries, **streaming_kwargs,
            )
            a_suppressed_state, a_suppressed_audit = roll_streaming_prefix(
                model=model, prefill=prefill[condition], prefix_token_ids=prefix,
                end_generated_index=len(prefix), seed=seed,
                layers=layers, selected_heads=heads, source_positions=target_positions,
                suppressed_generated_indices=a_window,
                forced_generated_boundaries=forced_boundaries, **streaming_kwargs,
            )
            a_suppressed_score = score_preference_from_streaming_state(
                model=model, state=a_suppressed_state,
                original_suffix_ids=sequences["original_suffix_ids"],
                counterfactual_suffix_ids=sequences["counterfactual_suffix_ids"], seed=seed,
            )
            a_suppressed_score["streaming_audit"] = a_suppressed_audit

            def run_arm(*, direct_queries: list[int], donor, patch_positions: list[int]):
                state, audit = roll_streaming_prefix(
                    model=model, prefill=prefill[condition], prefix_token_ids=prefix,
                    end_generated_index=len(prefix), seed=seed,
                    layers=layers, selected_heads=heads, source_positions=target_positions,
                    suppressed_generated_indices=direct_queries,
                    donor=donor, patch_generated_indices=patch_positions,
                    visual_positions=visual_positions,
                    forced_generated_boundaries=forced_boundaries, **streaming_kwargs,
                )
                score = score_preference_from_streaming_state(
                    model=model, state=state,
                    original_suffix_ids=sequences["original_suffix_ids"],
                    counterfactual_suffix_ids=sequences["counterfactual_suffix_ids"], seed=seed,
                )
                patch = audit["cache_patch"]
                score.update({
                    "direct_suppression": bool(direct_queries),
                    "direct_source_window_generated_indices": direct_queries,
                    "direct_source_window_absolute_positions": [
                        absolute_reasoning_token_position(
                            prompt_length=int(prefill[condition].prompt_length), token_index=index,
                        ) for index in direct_queries
                    ],
                    "patch_generated_indices": patch_positions,
                    "patch_absolute_positions": [] if patch is None else patch["patch_absolute_positions"],
                    "target_capture_generated_indices": coordinates["event_b_span"],
                    "target_capture_absolute_positions": [
                        absolute_reasoning_token_position(
                            prompt_length=int(prefill[condition].prompt_length), token_index=index,
                        ) for index in coordinates["event_b_span"]
                    ],
                    "cache_mode": "KV",
                    "visual_cache_donor_patched": False,
                    "streaming_audit": audit,
                })
                return score, state, audit

            native = score_preference_from_streaming_state(
                model=model, state=native_state,
                original_suffix_ids=sequences["original_suffix_ids"],
                counterfactual_suffix_ids=sequences["counterfactual_suffix_ids"], seed=seed,
            )
            native["streaming_audit"] = native_audit
            b_absolute = [
                absolute_reasoning_token_position(
                    prompt_length=int(prefill[condition].prompt_length), token_index=index,
                ) for index in coordinates["event_b_span"]
            ]
            native_b = snapshot_cache_positions(native_state, absolute_positions=b_absolute)
            direct, direct_state, direct_audit = run_arm(
                direct_queries=coordinates["direct_w8_query_positions"], donor=None, patch_positions=[]
            )
            direct_b = snapshot_cache_positions(direct_state, absolute_positions=b_absolute)
            del direct_state
            prior, prior_state, prior_audit = run_arm(
                direct_queries=[], donor=a_suppressed_state,
                patch_positions=coordinates["prior_checkpoint_positions"],
            )
            prior_b = snapshot_cache_positions(prior_state, absolute_positions=b_absolute)
            del prior_state
            short, short_state, short_audit = run_arm(
                direct_queries=[], donor=a_suppressed_state,
                patch_positions=coordinates["short_history_positions"],
            )
            short_b = snapshot_cache_positions(short_state, absolute_positions=b_absolute)
            del short_state
            joint, joint_state, joint_audit = run_arm(
                direct_queries=coordinates["direct_w8_query_positions"], donor=a_suppressed_state,
                patch_positions=coordinates["short_history_positions"],
            )
            joint_b = snapshot_cache_positions(joint_state, absolute_positions=b_absolute)
            del joint_state
            snapshot_sets = {
                "direct": direct_b,
                "prior_checkpoint": prior_b,
                "short_history": short_b,
                "joint": joint_b,
            }
            state_divergence = {}
            for arm, snapshot in snapshot_sets.items():
                value = summarize_cache_state_difference(native_b, snapshot)
                state_divergence[arm] = {
                    "original_candidate": value,
                    "counterfactual_candidate": value,
                }
            arm_audits = {
                "direct": direct_audit,
                "prior_checkpoint": prior_audit,
                "short_history": short_audit,
                "joint": joint_audit,
            }
            native_self = None
            repeat = None
            if args.mode == "validation":
                native_self_score, native_self_state, _ = run_arm(
                    direct_queries=[], donor=native_state,
                    patch_positions=coordinates["prior_checkpoint_positions"],
                )
                native_self = {
                    "score": native_self_score,
                    "exact": exact_scores(native_self_score, native),
                }
                if args.repeat_first and item_index == 0 and condition == "O":
                    repeated, repeated_state, _ = run_arm(
                        direct_queries=coordinates["direct_w8_query_positions"],
                        donor=a_suppressed_state,
                        patch_positions=coordinates["short_history_positions"],
                    )
                    repeat = {"arm": "joint", "exact": exact_scores(repeated, joint)}
                    del repeated_state
                del native_self_state
            condition_results[condition] = {
                "native": native,
                "direct": direct,
                "prior_checkpoint": prior,
                "short_history": short,
                "joint": joint,
                "event_a_source_suppressed_score": a_suppressed_score,
                "checkpoint_b_state_divergence": state_divergence,
                "route_patch_audits": {
                    arm: {
                        candidate: (
                            [] if arm_audits[arm]["cache_patch"] is None
                            else arm_audits[arm]["cache_patch"]["layer_audits"]
                        )
                        for candidate in ("original_candidate", "counterfactual_candidate")
                    }
                    for arm in snapshot_sets
                },
                "direct_suppression_audits": {
                    arm: {
                        candidate: [
                            row for execution in arm_audits[arm]["source_suppression_executions"]
                            for row in execution["layer_audits"]
                        ]
                        for candidate in ("original_candidate", "counterfactual_candidate")
                    }
                    for arm in ("direct", "joint")
                },
                "native_self_control": native_self,
                "deterministic_replay": repeat,
            }
            del native_state, a_suppressed_state, native_b, direct_b, prior_b, short_b, joint_b
        result = {
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "cohort_role": args.mode,
            "event_a_id": int(event_a["event_id"]),
            "event_b_id": int(event_b["event_id"]),
            "coordinates": coordinates,
            "pair_selection": "first eligible pair by annotation order",
            "selection_used_effect_size": False,
            "selection_used_attention": False,
            "conditions": condition_results,
            "runtime_seconds": time.perf_counter() - started,
        }
        write_json(result_path, result)
        completed += 1
        print(f"[{completed}/{len(eligible)}] base={base} A={result['event_a_id']} B={result['event_b_id']} seconds={result['runtime_seconds']:.1f}", flush=True)
        del prepared, prefill
        gc.collect()
        torch.cuda.empty_cache()
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    write_json(output / "run_summary.json", {
        "mode": args.mode,
        "completed": completed,
        "expected": len(eligible),
        "runtime_seconds": time.perf_counter() - run_started,
        "peak_gpu_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "peak_gpu_reserved_bytes": int(torch.cuda.max_memory_reserved()),
    })


if __name__ == "__main__":
    main()
