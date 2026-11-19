#!/usr/bin/env python3
"""Run the frozen exhaustive recent-reasoning carrier atlas."""

from __future__ import annotations

import argparse
import gc
import json
import os
import time
from pathlib import Path
from typing import Any

import torch

from run_phase_a import CONDITIONS, ROOT, assets, coordinates, exact, read_json, read_jsonl, sequences, write_json
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3c8.runtime import (
    capture_native_or_window_suppressed_states,
    score_window_suppressed_with_cache_rescue,
)
from visual_reasoning.stage3c8.protocol import distributed_process_info


OUT = ROOT / "outputs/stage3c8"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--spans", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=("validation", "historical", "fresh"), required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--repeat-first", action="store_true")
    return parser.parse_args()


def selected_annotations(rows: list[dict[str, Any]], *, base: str, coordinate: str, recent: set[int]) -> list[dict[str, Any]]:
    result = [
        row for row in rows
        if str(row["base_problem_id"]) == base
        and str(row["coordinate"]) == coordinate
        and row["stream"] == "PREVIOUS_REASONING"
        and int(row["generated_index"]) in recent
    ]
    if {int(row["generated_index"]) for row in result} != recent:
        raise RuntimeError(f"Frozen recent-token annotations are incomplete for {base}/{coordinate}")
    return result


def main() -> None:
    args = parse_args()
    config = read_json(OUT / "config/stage3c8_config.json")
    family = read_json(OUT / "config/primary_family.json")
    world_size, rank, local_device = distributed_process_info(
        os.environ, visible_device_count=torch.cuda.device_count(),
    )
    torch.cuda.set_device(local_device)
    output = args.output_dir.resolve()
    output.relative_to(OUT.resolve())
    if world_size > 1:
        output = output / f"shard_{rank}"
    manifest = read_jsonl(args.manifest)[rank::world_size]
    annotations = read_jsonl(args.annotations)
    lexical_spans = read_jsonl(args.spans)
    old_events = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl")}
    old_rois = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl")}
    dataset = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, 40_960)
    if "A5000" not in str(environment["gpu_name"]):
        raise RuntimeError(f"Stage 3C8 requires A5000, observed {environment['gpu_name']}")
    layers = [int(value) for value in family["phase_b"]["all_layers"]]
    heads = list(range(int(model.config.text_config.num_attention_heads)))
    fixed_distances = [int(value) for value in family["phase_b"]["fixed_kv_distances"]]
    write_json(output / "environment.json", environment)
    write_json(output / "run_config.json", {
        "mode": args.mode,
        "manifest": str(args.manifest.resolve()),
        "rank": rank,
        "world_size": world_size,
        "layers": layers,
        "window": family["phase_b"]["window"],
        "fixed_kv_distances": fixed_distances,
        "base_problem_ids": [str(row["base_problem_id"]) for row in manifest],
    })
    torch.cuda.reset_peak_memory_stats()
    started_run = time.perf_counter()
    completed = 0
    for item_index, item in enumerate(manifest):
        base = str(item["base_problem_id"])
        result_path = output / "examples" / base / "result.json"
        if result_path.is_file():
            if not args.resume:
                raise FileExistsError(result_path)
            completed += 1
            print(f"[{completed}/{len(manifest)}] resume skip {base}", flush=True)
            continue
        started = time.perf_counter()
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
        target_positions = [int(value) for value in roi["absolute_source_groups"]["V_target"]]
        visual_positions = [int(value) for value in metadata["O"]["visual_token_indices"]]
        if visual_positions != [int(value) for value in roi["absolute_source_groups"]["V_all"]]:
            raise RuntimeError(f"Frozen ROI layout mismatch for base {base}")
        coordinate_results: dict[str, Any] = {}
        for coordinate, current in coordinates(item, event, args.mode):
            if current < 17:
                continue
            prefix, bridge, suffix_o, suffix_c = sequences(event, current)
            window = list(range(current - 16, current + 1))
            recent = list(range(current - 16, current))
            recent_set = set(recent)
            token_rows = selected_annotations(annotations, base=base, coordinate=coordinate, recent=recent_set)
            token_class = {int(row["generated_index"]): str(row["lexical_semantic_class"]) for row in token_rows}
            visual_class = {int(row["generated_index"]): str(row["visual_alignment"]) for row in token_rows}
            spans = [
                row for row in lexical_spans
                if str(row["base_problem_id"]) == base
                and str(row["coordinate"]) == coordinate
                and row["stream"] == "PREVIOUS_REASONING"
                and len(row["generated_indices"]) > 1
                and set(int(value) for value in row["generated_indices"]).issubset(recent_set)
            ]
            condition_results: dict[str, Any] = {}
            for condition in CONDITIONS:
                common = dict(
                    model=model,
                    prepared=prepared[condition],
                    prefix_token_ids=prefix,
                    bridge_token_ids=bridge,
                    original_suffix_ids=suffix_o,
                    counterfactual_suffix_ids=suffix_c,
                    window_generated_indices=window,
                    capture_generated_indices=recent,
                    cache_layers=layers,
                    source_positions=target_positions,
                    selected_heads=heads,
                    seed=int(config["runtime"]["seed"]),
                )
                native, native_states = capture_native_or_window_suppressed_states(
                    **common, suppression_enabled=False
                )
                suppressed, suppressed_states = capture_native_or_window_suppressed_states(
                    **common, suppression_enabled=True
                )
                rescue_common = dict(
                    model=model,
                    prepared=prepared[condition],
                    prefix_token_ids=prefix,
                    bridge_token_ids=bridge,
                    original_suffix_ids=suffix_o,
                    counterfactual_suffix_ids=suffix_c,
                    window_generated_indices=window,
                    suppression_layers=layers,
                    source_positions=target_positions,
                    selected_heads=heads,
                    donor_states=native_states,
                    visual_positions=visual_positions,
                    seed=int(config["runtime"]["seed"]),
                )
                all_recent = score_window_suppressed_with_cache_rescue(
                    **rescue_common, selected_generated_indices=recent, cache_mode="KV"
                )
                per_position = {
                    str(position): score_window_suppressed_with_cache_rescue(
                        **rescue_common, selected_generated_indices=[position], cache_mode="KV"
                    )
                    for position in recent
                }
                fixed = {}
                for distance in fixed_distances:
                    position = current - distance
                    if position not in recent_set:
                        continue
                    fixed[str(distance)] = {
                        "K": score_window_suppressed_with_cache_rescue(
                            **rescue_common, selected_generated_indices=[position], cache_mode="K"
                        ),
                        "V": score_window_suppressed_with_cache_rescue(
                            **rescue_common, selected_generated_indices=[position], cache_mode="V"
                        ),
                        "KV": per_position[str(position)],
                    }
                fixed_cumulative = {
                    "1": per_position[str(current - 1)],
                    "16": all_recent,
                    **{str(width): score_window_suppressed_with_cache_rescue(
                        **rescue_common,
                        selected_generated_indices=list(range(current - width, current)),
                        cache_mode="KV",
                    )
                    for width in (2, 4, 8)},
                }
                span_rescue = {
                    str(row["span_id"]): score_window_suppressed_with_cache_rescue(
                        **rescue_common,
                        selected_generated_indices=[int(value) for value in row["generated_indices"]],
                        cache_mode="KV",
                    )
                    for row in spans
                }
                type_groups = {}
                for token_type in sorted(set(token_class.values())):
                    positions = [position for position in recent if token_class[position] == token_type]
                    type_groups[f"lexical:{token_type}"] = score_window_suppressed_with_cache_rescue(
                        **rescue_common, selected_generated_indices=positions, cache_mode="KV"
                    )
                for alignment in sorted(set(visual_class.values())):
                    positions = [position for position in recent if visual_class[position] == alignment]
                    type_groups[f"visual_alignment:{alignment}"] = score_window_suppressed_with_cache_rescue(
                        **rescue_common, selected_generated_indices=positions, cache_mode="KV"
                    )
                controls = None
                repeat = None
                if args.mode == "validation":
                    native_self = score_window_suppressed_with_cache_rescue(
                        **rescue_common,
                        selected_generated_indices=recent,
                        cache_mode="KV",
                        suppression_enabled=False,
                    )
                    suppressed_self = score_window_suppressed_with_cache_rescue(
                        **{**rescue_common, "donor_states": suppressed_states},
                        selected_generated_indices=recent,
                        cache_mode="KV",
                    )
                    controls = {
                        "native_self": native_self,
                        "native_self_exact": exact(native_self, native),
                        "suppressed_self": suppressed_self,
                        "suppressed_self_exact": exact(suppressed_self, suppressed),
                    }
                    if args.repeat_first and item_index == 0:
                        repeated = score_window_suppressed_with_cache_rescue(
                            **rescue_common, selected_generated_indices=recent, cache_mode="KV"
                        )
                        repeat = {"arm": "all_recent", "exact": exact(repeated, all_recent)}
                condition_results[condition] = {
                    "native": native,
                    "suppressed": suppressed,
                    "capture_audits": {
                        "native": {
                            candidate: {
                                "cache": native_states[candidate]["cache_audit"],
                                "suppression": native_states[candidate]["suppression_audit"],
                            }
                            for candidate in native_states
                        },
                        "suppressed": {
                            candidate: {
                                "cache": suppressed_states[candidate]["cache_audit"],
                                "suppression": suppressed_states[candidate]["suppression_audit"],
                            }
                            for candidate in suppressed_states
                        },
                    },
                    "all_recent": all_recent,
                    "per_position": per_position,
                    "fixed_position_kv": fixed,
                    "fixed_recency_cumulative": fixed_cumulative,
                    "span_rescue": span_rescue,
                    "type_group_rescue": type_groups,
                    "self_controls": controls,
                    "repeat": repeat,
                }
                del native_states, suppressed_states
                gc.collect()
                torch.cuda.empty_cache()
            coordinate_results[coordinate] = {
                "current_generated_index": current,
                "window_generated_indices": window,
                "recent_generated_indices": recent,
                "token_classes": {str(key): value for key, value in token_class.items()},
                "visual_alignment_classes": {str(key): value for key, value in visual_class.items()},
                "multi_token_spans": spans,
                "conditions": condition_results,
            }
        if not coordinate_results:
            raise RuntimeError(f"No valid T16 coordinate for base {base}")
        result = {
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "cohort_role": args.mode,
            "coordinates": coordinate_results,
            "target_positions": target_positions,
            "visual_positions": visual_positions,
            "selection_used_attention": False,
            "runtime_seconds": time.perf_counter() - started,
        }
        write_json(result_path, result)
        completed += 1
        print(f"[{completed}/{len(manifest)}] base={base} seconds={result['runtime_seconds']:.1f}", flush=True)
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    write_json(output / "run_summary.json", {
        "mode": args.mode,
        "completed": completed,
        "expected": len(manifest),
        "runtime_seconds": time.perf_counter() - started_run,
        "peak_gpu_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "peak_gpu_reserved_bytes": int(torch.cuda.max_memory_reserved()),
    })


if __name__ == "__main__":
    main()
