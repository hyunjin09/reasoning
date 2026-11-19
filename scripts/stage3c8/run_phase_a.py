#!/usr/bin/env python3
"""Run the frozen Stage 3C8 natural-t_pre carrier assay."""

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
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3c7.runtime import (
    CANDIDATES,
    capture_native_or_suppressed_states,
    score_suppressed_with_rescue,
)
from visual_reasoning.stage3c8.protocol import distributed_process_info


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c8"
CONDITIONS = ("O", "C")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=("validation", "historical", "fresh"), required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--repeat-first", action="store_true")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def exact(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return bool(
        float(left["D"]) == float(right["D"])
        and left[CANDIDATES[0]]["token_log_probabilities"] == right[CANDIDATES[0]]["token_log_probabilities"]
        and left[CANDIDATES[1]]["token_log_probabilities"] == right[CANDIDATES[1]]["token_log_probabilities"]
    )


def assets(item: dict[str, Any], old_events: dict[str, Any], old_rois: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    base = str(item["base_problem_id"])
    if item.get("edit_metadata"):
        edit = read_json(ROOT / item["edit_metadata"])
        event = item["event"]
        roi = item["roi_mapping"]
    else:
        edit = read_json(ROOT / "outputs/stage3b3_redesign/counterfactual_shams" / base / "edit_metadata.json")
        event = old_events[base]
        roi = old_rois[base]
    if edit["manual_validation"]["status"] != "pass":
        raise RuntimeError(f"Manual image validation failed for base {base}")
    return edit, event, roi


def coordinates(item: dict[str, Any], event: dict[str, Any], mode: str) -> list[tuple[str, int]]:
    if mode in {"validation", "historical"} and item.get("state_pairs"):
        return [
            (str(pair["target_id"]), int(pair["state_R"]["generated_index"]))
            for pair in item["state_pairs"]
        ]
    ed = int(event["ed_generated_index"])
    result = [("a_like", ed)]
    if ed >= 2:
        result.append(("b_like", ed - 1))
    return result


def sequences(event: dict[str, Any], current: int) -> tuple[list[int], list[int], list[int], list[int]]:
    context = [int(value) for value in event["history_before_ed_token_ids"]]
    ed = int(event["ed_generated_index"])
    if not 1 <= current <= ed == len(context):
        raise ValueError("Frozen coordinate lies outside strict E_d history")
    return (
        context[:current],
        context[current:ed],
        [int(value) for value in event["original_divergent_suffix_ids"]],
        [int(value) for value in event["counterfactual_divergent_suffix_ids"]],
    )


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
    old_events = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl")}
    old_rois = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl")}
    dataset = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, 40_960)
    if "A5000" not in str(environment["gpu_name"]):
        raise RuntimeError(f"Stage 3C8 requires A5000, observed {environment['gpu_name']}")
    layers = [int(value) for value in family["phase_a"]["layers"]]
    heads = list(range(int(model.config.text_config.num_attention_heads)))
    write_json(output / "environment.json", environment)
    write_json(output / "run_config.json", {
        "mode": args.mode,
        "manifest": str(args.manifest.resolve()),
        "rank": rank,
        "world_size": world_size,
        "layers": layers,
        "modes": family["phase_a"]["modes"],
        "base_problem_ids": [str(row["base_problem_id"]) for row in manifest],
    })
    started_run = time.perf_counter()
    completed = 0
    torch.cuda.reset_peak_memory_stats()
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
        condition_paths = {condition: ROOT / edit["paths"][condition] for condition in CONDITIONS}
        prepared, metadata = {}, {}
        for condition, path in condition_paths.items():
            prepared[condition], metadata[condition] = prepare_custom_image(
                processor, dataset[str(item["example_id"])], path, device="cuda"
            )
        if metadata["O"]["prompt_token_ids"] != metadata["C"]["prompt_token_ids"] or metadata["O"]["image_grid_thw"] != metadata["C"]["image_grid_thw"]:
            raise RuntimeError(f"Condition layout mismatch for base {base}")
        target_positions = [int(value) for value in roi["absolute_source_groups"]["V_target"]]
        visual_positions = [int(value) for value in metadata["O"]["visual_token_indices"]]
        if visual_positions != [int(value) for value in roi["absolute_source_groups"]["V_all"]]:
            raise RuntimeError(f"Frozen ROI layout mismatch for base {base}")
        coordinate_results: dict[str, Any] = {}
        for coordinate, current in coordinates(item, event, args.mode):
            prefix, bridge, suffix_o, suffix_c = sequences(event, current)
            tpre = current - 1
            condition_results: dict[str, Any] = {}
            for condition in CONDITIONS:
                common = dict(
                    model=model,
                    prepared=prepared[condition],
                    prefix_token_ids=prefix,
                    bridge_token_ids=bridge,
                    original_suffix_ids=suffix_o,
                    counterfactual_suffix_ids=suffix_c,
                    current_generated_index=current,
                    tpre_generated_index=tpre,
                    cache_layers=layers,
                    residual_layer=35,
                    suppression_layers=layers,
                    source_positions=target_positions,
                    selected_heads=heads,
                    seed=int(config["runtime"]["seed"]),
                )
                native, native_states = capture_native_or_suppressed_states(**common, suppression_enabled=False)
                suppressed, suppressed_states = capture_native_or_suppressed_states(**common, suppression_enabled=True)
                rescue_common = dict(
                    model=model,
                    prepared=prepared[condition],
                    prefix_token_ids=prefix,
                    bridge_token_ids=bridge,
                    original_suffix_ids=suffix_o,
                    counterfactual_suffix_ids=suffix_c,
                    current_generated_index=current,
                    tpre_generated_index=tpre,
                    suppression_layers=layers,
                    source_positions=target_positions,
                    selected_heads=heads,
                    native_states=native_states,
                    residual_layer=None,
                    residual_boundary=None,
                    visual_positions=visual_positions,
                    seed=int(config["runtime"]["seed"]),
                    suppression_enabled=True,
                )
                arms = {
                    mode: score_suppressed_with_rescue(
                        **rescue_common, cache_layers=layers, cache_mode=mode
                    )
                    for mode in family["phase_a"]["modes"]
                }
                controls = None
                repeat = None
                if args.mode == "validation":
                    controls = {
                        "native_self_KV": score_suppressed_with_rescue(
                            **{**rescue_common, "native_states": native_states, "suppression_enabled": False},
                            cache_layers=layers,
                            cache_mode="KV",
                        ),
                        "suppressed_self_KV": score_suppressed_with_rescue(
                            **{**rescue_common, "native_states": suppressed_states},
                            cache_layers=layers,
                            cache_mode="KV",
                        ),
                    }
                    if args.repeat_first and item_index == 0:
                        repeated = score_suppressed_with_rescue(
                            **rescue_common, cache_layers=layers, cache_mode="KV"
                        )
                        repeat = {"arm": "KV", "exact": exact(repeated, arms["KV"])}
                condition_results[condition] = {
                    "native": native,
                    "suppressed": suppressed,
                    "arms": arms,
                    "capture_audits": {
                        "native": {candidate: native_states[candidate]["cache_audit"] for candidate in native_states},
                        "suppressed": {candidate: suppressed_states[candidate]["cache_audit"] for candidate in suppressed_states},
                    },
                    "self_controls": controls,
                    "repeat": repeat,
                }
                del native_states, suppressed_states
                gc.collect()
                torch.cuda.empty_cache()
            coordinate_results[coordinate] = {
                "current_generated_index": current,
                "tpre_generated_index": tpre,
                "tpre_token_id": int(event["history_before_ed_token_ids"][tpre - 1]),
                "tpre_token_text": processor.tokenizer.decode([int(event["history_before_ed_token_ids"][tpre - 1])], skip_special_tokens=False),
                "conditions": condition_results,
            }
        result = {
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "cohort_role": args.mode,
            "coordinates": coordinate_results,
            "target_positions": target_positions,
            "visual_positions": visual_positions,
            "prompt_token_ids_exact": True,
            "image_grid_exact": True,
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
