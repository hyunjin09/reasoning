#!/usr/bin/env python3
"""Run frozen Phase-D local acquisition and downstream landmark-cache rescue."""

from __future__ import annotations

import argparse
import gc
import json
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import torch

from run_phase_a import ROOT, assets, read_json, read_jsonl, write_json
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3c8.protocol import distributed_process_info
from visual_reasoning.stage3c8.runtime import (
    capture_landmark_cache_states,
    score_landmark_cache_patch,
    summarize_cache_state_difference,
)


OUT = ROOT / "outputs/stage3c8"
CONDITIONS = ("O", "C")
CANDIDATES = ("original_candidate", "counterfactual_candidate")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--landmarks", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    world_size, rank, local_device = distributed_process_info(
        os.environ, visible_device_count=torch.cuda.device_count(),
    )
    output = args.output_dir.resolve()
    output.relative_to(OUT.resolve())
    if world_size > 1:
        output = output / f"shard_{rank}"
    output.mkdir(parents=True, exist_ok=True)
    manifest = read_jsonl(args.manifest)[rank::world_size]
    all_landmarks = read_jsonl(args.landmarks)
    by_base: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in all_landmarks:
        by_base[str(row["base_problem_id"])].append(row)
    if not manifest:
        write_json(output / "run_summary.json", {"status": "gated_off_or_empty", "completed": 0, "rank": rank, "world_size": world_size})
        return
    torch.cuda.set_device(local_device)
    config = read_json(OUT / "config/stage3c8_config.json")
    old_events = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl")
    }
    old_rois = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(ROOT / "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl")
    }
    dataset = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, 40_960)
    if "A5000" not in str(environment["gpu_name"]):
        raise RuntimeError(f"Stage 3C8 requires A5000, observed {environment['gpu_name']}")
    layers = list(range(int(model.config.text_config.num_hidden_layers)))
    heads = list(range(int(model.config.text_config.num_attention_heads)))
    seed = int(config["runtime"]["seed"])
    write_json(output / "environment.json", environment)
    write_json(output / "run_config.json", {
        "manifest": str(args.manifest.resolve()),
        "landmarks": str(args.landmarks.resolve()),
        "rank": rank,
        "world_size": world_size,
        "layers": layers,
        "local_window_width": 4,
        "base_problem_ids": [str(row["base_problem_id"]) for row in manifest],
        "selection_used_attention": False,
        "landmarks_frozen_before_phase_d_scores": True,
    })
    torch.cuda.reset_peak_memory_stats()
    started_run = time.perf_counter()
    completed = 0
    for item in manifest:
        base = str(item["base_problem_id"])
        result_path = output / "examples" / base / "result.json"
        if result_path.is_file():
            if not args.resume:
                raise FileExistsError(result_path)
            completed += 1
            continue
        edit, event, roi = assets(item, old_events, old_rois)
        prepared, metadata = {}, {}
        for condition in CONDITIONS:
            prepared[condition], metadata[condition] = prepare_custom_image(
                processor,
                dataset[str(item["example_id"])],
                ROOT / edit["paths"][condition],
                device="cuda",
            )
        if metadata["O"]["prompt_token_ids"] != metadata["C"]["prompt_token_ids"] or metadata["O"]["image_grid_thw"] != metadata["C"]["image_grid_thw"]:
            raise RuntimeError(f"Condition layout mismatch for base {base}")
        visual_positions = [int(value) for value in metadata["O"]["visual_token_indices"]]
        if visual_positions != [int(value) for value in roi["absolute_source_groups"]["V_all"]]:
            raise RuntimeError(f"Frozen ROI layout mismatch for base {base}")
        target_positions = [int(value) for value in roi["absolute_source_groups"]["V_target"]]
        history = [int(value) for value in event["history_before_ed_token_ids"]]
        suffix_o = [int(value) for value in event["original_divergent_suffix_ids"]]
        suffix_c = [int(value) for value in event["counterfactual_divergent_suffix_ids"]]
        landmark_results = []
        for landmark in sorted(by_base[base], key=lambda row: int(row["landmark_generated_index"])):
            position = int(landmark["landmark_generated_index"])
            window = [int(value) for value in landmark["local_suppression_generated_indices"]]
            condition_results = {}
            for condition in CONDITIONS:
                common = dict(
                    model=model,
                    prepared=prepared[condition],
                    history_before_readout_ids=history,
                    original_suffix_ids=suffix_o,
                    counterfactual_suffix_ids=suffix_c,
                    landmark_generated_index=position,
                    local_suppression_generated_indices=window,
                    cache_layers=layers,
                    source_positions=target_positions,
                    selected_heads=heads,
                    seed=seed,
                )
                native, native_states = capture_landmark_cache_states(**common, suppression_enabled=False)
                suppressed, suppressed_states = capture_landmark_cache_states(**common, suppression_enabled=True)
                state_difference = {
                    candidate: summarize_cache_state_difference(
                        native_states[candidate]["cache"], suppressed_states[candidate]["cache"]
                    )
                    for candidate in CANDIDATES
                }
                rescue = score_landmark_cache_patch(
                    model=model,
                    prepared=prepared[condition],
                    history_before_readout_ids=history,
                    original_suffix_ids=suffix_o,
                    counterfactual_suffix_ids=suffix_c,
                    landmark_generated_index=position,
                    local_suppression_generated_indices=window,
                    suppression_layers=layers,
                    source_positions=target_positions,
                    selected_heads=heads,
                    donor_states=native_states,
                    visual_positions=visual_positions,
                    seed=seed,
                    suppression_enabled=True,
                )
                condition_results[condition] = {
                    "native": native,
                    "suppressed": suppressed,
                    "rescue": rescue,
                    "state_difference": state_difference,
                    "native_capture_audit": {candidate: native_states[candidate]["cache_audit"] for candidate in CANDIDATES},
                    "suppressed_capture_audit": {candidate: suppressed_states[candidate]["cache_audit"] for candidate in CANDIDATES},
                }
                del native_states, suppressed_states
                gc.collect()
                torch.cuda.empty_cache()
            landmark_results.append({"annotation": landmark, "conditions": condition_results})
        write_json(result_path, {
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "cohort_role": "fresh_long_horizon",
            "target_positions": target_positions,
            "visual_positions": visual_positions,
            "landmarks": landmark_results,
            "selection_used_attention": False,
            "landmarks_frozen_before_phase_d_scores": True,
        })
        completed += 1
        print(f"[{completed}/{len(manifest)}] base={base} landmarks={len(landmark_results)}", flush=True)
    write_json(output / "run_summary.json", {
        "status": "complete",
        "completed": completed,
        "expected": len(manifest),
        "rank": rank,
        "world_size": world_size,
        "runtime_seconds": time.perf_counter() - started_run,
        "peak_gpu_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "peak_gpu_reserved_bytes": int(torch.cuda.max_memory_reserved()),
    })


if __name__ == "__main__":
    main()
