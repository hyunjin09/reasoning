#!/usr/bin/env python3
"""Run gated Stage 3C.6 boundary, dose, or target-specificity rescue."""

from __future__ import annotations

import argparse
import gc
import json
import os
import time
from pathlib import Path
from typing import Any, Sequence

import torch

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3c6.runtime import (
    capture_preference_states,
    interpolate_residual,
    residual_delta_summaries,
    score_preference_with_residual_source,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c6"
CONDITIONS = ("O", "C")
BOUNDARIES = ("h_pre", "h_post_attn", "h_post_block")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("boundary", "dose", "controls"), required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-bases", type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def condition_paths(base: str) -> dict[str, Path]:
    metadata = read_json(ROOT / "outputs/stage3b3_redesign/counterfactual_shams" / base / "edit_metadata.json")
    if metadata["manual_validation"]["status"] != "pass":
        raise RuntimeError(f"Four-condition validation failed for base {base}")
    return {condition: ROOT / metadata["paths"][condition] for condition in CONDITIONS}


def evidence_sequences(event: dict[str, Any], state_index: int) -> tuple[list[int], list[int], list[int], list[int]]:
    context = [int(value) for value in event["history_before_ed_token_ids"]]
    ed = int(event["ed_generated_index"])
    index = int(state_index)
    if not 1 <= index <= ed == len(context):
        raise ValueError("Frozen target state is outside the evidence history")
    return context[:index], context[index:ed], [int(v) for v in event["original_divergent_suffix_ids"]], [int(v) for v in event["counterfactual_divergent_suffix_ids"]]


def score_exact(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return bool(
        float(left["D"]) == float(right["D"])
        and left["original_candidate"]["token_log_probabilities"] == right["original_candidate"]["token_log_probabilities"]
        and left["counterfactual_candidate"]["token_log_probabilities"] == right["counterfactual_candidate"]["token_log_probabilities"]
    )


def source_groups(target: Sequence[int], mention: Sequence[int], irrelevant: Sequence[int]) -> dict[str, list[int]]:
    groups = {"T": sorted(set(map(int, target))), "M": sorted(set(map(int, mention))), "I": sorted(set(map(int, irrelevant)))}
    sets = [set(groups[key]) for key in ("T", "M", "I")]
    if any(not value for value in sets) or any(sets[i] & sets[j] for i in range(3) for j in range(i + 1, 3)):
        raise ValueError("T/M/I must be nonempty and disjoint")
    return groups


def interpolated_states(
    native: dict[str, dict[str, dict[int, torch.Tensor]]],
    suppressed: dict[str, dict[str, dict[int, torch.Tensor]]],
    *, layer: int, boundary: str, gain: float,
) -> dict[str, dict[str, dict[int, torch.Tensor]]]:
    return {
        candidate: {
            boundary: {
                layer: interpolate_residual(
                    suppressed[candidate][boundary][layer], native[candidate][boundary][layer], gain
                )
            }
        }
        for candidate in ("original_candidate", "counterfactual_candidate")
    }


def main() -> None:
    args = parse_args()
    config = read_json(OUT / "config/stage3c6_config.json")
    region_freeze = read_json(OUT / "phase_a_hpre_scan/candidate_region_freeze.json")
    active_targets = {
        target: row["candidate_region"]["layers"]
        for target, row in region_freeze["targets"].items()
        if row["run_phase_b"]
    }
    if not active_targets:
        raise RuntimeError("Phase B is gated off for both targets")
    dose_freeze = read_json(OUT / "phase_c_optional_dose/dose_boundary_freeze.json") if args.mode == "dose" else None
    control_freeze = read_json(OUT / "phase_b_boundary/control_boundary_freeze.json") if args.mode == "controls" else None
    dose_lambdas = read_json(OUT / "config/primary_family.json")["dose_lambdas"] if args.mode == "dose" else []
    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    torch.cuda.set_device(local_rank if world_size > 1 else 0)
    output_dir = args.output_dir.resolve()
    output_dir.relative_to(OUT.resolve())
    if world_size > 1:
        output_dir = output_dir / f"shard_{local_rank}"
    manifest = read_jsonl(args.manifest)[local_rank::world_size]
    if args.max_bases:
        manifest = manifest[:args.max_bases]
    events = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl")}
    rois = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl")}
    mentions = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3c2/annotations/mention_roi_annotations.jsonl")}
    data = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "run_config.json", {
        "mode": args.mode, "manifest": str(args.manifest.resolve()), "shard_index": local_rank,
        "shard_count": world_size, "base_problem_ids": [str(row["base_problem_id"]) for row in manifest],
        "active_targets": active_targets, "boundaries": list(BOUNDARIES),
    })
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, 40_960)
    if "A5000" not in str(environment["gpu_name"]):
        raise RuntimeError(f"Stage 3C.6 requires A5000, observed {environment['gpu_name']}")
    observed = {
        "language_layers": int(model.config.text_config.num_hidden_layers),
        "logical_query_heads": int(model.config.text_config.num_attention_heads),
        "kv_heads": int(model.config.text_config.num_key_value_heads),
        "query_heads_per_kv_group": int(model.config.text_config.num_attention_heads // model.config.text_config.num_key_value_heads),
        "head_dimension": int(model.config.text_config.head_dim),
    }
    if observed != config["architecture_expected"]:
        raise RuntimeError(f"Architecture mismatch: {observed}")
    write_json(output_dir / "environment.json", {**environment, "architecture_observed": observed})
    suppression_layers = [int(value) for value in config["suppression_scope"]["layers"]]
    all_heads = list(range(observed["logical_query_heads"]))
    torch.cuda.reset_peak_memory_stats()
    run_started = time.perf_counter()
    completed = 0
    for item_index, item in enumerate(manifest):
        base = str(item["base_problem_id"])
        result_path = output_dir / "examples" / base / "result.json"
        if result_path.is_file():
            if not args.resume:
                raise FileExistsError(result_path)
            completed += 1
            print(f"[{completed}/{len(manifest)}] resume skip {base}", flush=True)
            continue
        started = time.perf_counter()
        prepared: dict[str, dict[str, Any]] = {}
        metadata: dict[str, dict[str, Any]] = {}
        for condition, path in condition_paths(base).items():
            prepared[condition], metadata[condition] = prepare_custom_image(processor, data[str(item["example_id"])], path, device="cuda")
        if metadata["O"]["prompt_token_ids"] != metadata["C"]["prompt_token_ids"] or metadata["O"]["image_grid_thw"] != metadata["C"]["image_grid_thw"]:
            raise RuntimeError(f"O/C prompt or grid mismatch for base {base}")
        roi, mention = rois[base], mentions[base]
        groups = source_groups(roi["absolute_source_groups"]["V_target"], mention["mention_absolute_source_positions"], roi["absolute_source_groups"]["V_irrelevant"])
        pair_by_target = {row["target_id"]: row for row in item["state_pairs"]}
        target_results: dict[str, Any] = {}
        for target_id, region in active_targets.items():
            current = int(pair_by_target[target_id]["state_R"]["generated_index"])
            tpre = current - 1
            prefix, bridge, suffix_o, suffix_c = evidence_sequences(events[base], current)
            condition_results: dict[str, Any] = {}
            for condition in CONDITIONS:
                if args.mode == "controls":
                    assert control_freeze is not None
                    spec = control_freeze["targets"][target_id]
                    layer, boundary = int(spec["layer"]), str(spec["boundary"])
                    control_results = {}
                    for source_name in ("M", "I"):
                        native, native_states = capture_preference_states(
                            model=model, prepared=prepared[condition], prefix_token_ids=prefix, bridge_token_ids=bridge,
                            original_suffix_ids=suffix_o, counterfactual_suffix_ids=suffix_c,
                            current_generated_index=current, capture_layers=[layer], suppression_generated_index=None,
                            suppression_layers=[], source_positions=groups[source_name], selected_heads=all_heads,
                            suppression_gain=1.0, seed=int(config["seed"]),
                        )
                        suppressed, suppressed_states = capture_preference_states(
                            model=model, prepared=prepared[condition], prefix_token_ids=prefix, bridge_token_ids=bridge,
                            original_suffix_ids=suffix_o, counterfactual_suffix_ids=suffix_c,
                            current_generated_index=current, capture_layers=[layer], suppression_generated_index=tpre,
                            suppression_layers=suppression_layers, source_positions=groups[source_name], selected_heads=all_heads,
                            suppression_gain=0.0, seed=int(config["seed"]),
                        )
                        rescue = score_preference_with_residual_source(
                            model=model, prepared=prepared[condition], prefix_token_ids=prefix, bridge_token_ids=bridge,
                            original_suffix_ids=suffix_o, counterfactual_suffix_ids=suffix_c,
                            current_generated_index=current, layer_index=layer, boundary=boundary,
                            source_states_by_candidate=native_states, suppression_generated_index=tpre,
                            suppression_layers=suppression_layers, source_positions=groups[source_name], selected_heads=all_heads,
                            suppression_gain=0.0, seed=int(config["seed"]),
                        )
                        control_results[source_name] = {"native": native, "suppressed": suppressed, "rescue": rescue, "layer": layer, "boundary": boundary}
                        del native_states, suppressed_states
                    condition_results[condition] = {"controls": control_results}
                    continue
                if args.mode == "dose":
                    assert dose_freeze is not None
                    spec = dose_freeze["targets"][target_id]
                    layer, boundary = int(spec["layer"]), str(spec["boundary"])
                    capture_layers = [layer]
                else:
                    layer, boundary = -1, ""
                    capture_layers = [int(value) for value in region]
                native, native_states = capture_preference_states(
                    model=model, prepared=prepared[condition], prefix_token_ids=prefix, bridge_token_ids=bridge,
                    original_suffix_ids=suffix_o, counterfactual_suffix_ids=suffix_c,
                    current_generated_index=current, capture_layers=capture_layers, suppression_generated_index=None,
                    suppression_layers=[], source_positions=groups["T"], selected_heads=all_heads,
                    suppression_gain=1.0, seed=int(config["seed"]),
                )
                suppressed, suppressed_states = capture_preference_states(
                    model=model, prepared=prepared[condition], prefix_token_ids=prefix, bridge_token_ids=bridge,
                    original_suffix_ids=suffix_o, counterfactual_suffix_ids=suffix_c,
                    current_generated_index=current, capture_layers=capture_layers, suppression_generated_index=tpre,
                    suppression_layers=suppression_layers, source_positions=groups["T"], selected_heads=all_heads,
                    suppression_gain=0.0, seed=int(config["seed"]),
                )
                if args.mode == "boundary":
                    scans: dict[str, Any] = {}
                    for scan_layer in capture_layers:
                        for scan_boundary in BOUNDARIES:
                            key = f"L{scan_layer}_{scan_boundary}"
                            rescue = score_preference_with_residual_source(
                                model=model, prepared=prepared[condition], prefix_token_ids=prefix, bridge_token_ids=bridge,
                                original_suffix_ids=suffix_o, counterfactual_suffix_ids=suffix_c,
                                current_generated_index=current, layer_index=scan_layer, boundary=scan_boundary,
                                source_states_by_candidate=native_states, suppression_generated_index=tpre,
                                suppression_layers=suppression_layers, source_positions=groups["T"], selected_heads=all_heads,
                                suppression_gain=0.0, seed=int(config["seed"]),
                            )
                            self_native = score_preference_with_residual_source(
                                model=model, prepared=prepared[condition], prefix_token_ids=prefix, bridge_token_ids=bridge,
                                original_suffix_ids=suffix_o, counterfactual_suffix_ids=suffix_c,
                                current_generated_index=current, layer_index=scan_layer, boundary=scan_boundary,
                                source_states_by_candidate=native_states, suppression_generated_index=None,
                                suppression_layers=[], source_positions=groups["T"], selected_heads=all_heads,
                                suppression_gain=1.0, seed=int(config["seed"]),
                            )
                            self_suppressed = score_preference_with_residual_source(
                                model=model, prepared=prepared[condition], prefix_token_ids=prefix, bridge_token_ids=bridge,
                                original_suffix_ids=suffix_o, counterfactual_suffix_ids=suffix_c,
                                current_generated_index=current, layer_index=scan_layer, boundary=scan_boundary,
                                source_states_by_candidate=suppressed_states, suppression_generated_index=tpre,
                                suppression_layers=suppression_layers, source_positions=groups["T"], selected_heads=all_heads,
                                suppression_gain=0.0, seed=int(config["seed"]),
                            )
                            scans[key] = {
                                "layer": scan_layer, "boundary": scan_boundary, "rescue": rescue,
                                "self_native_exact": score_exact(self_native, native),
                                "self_suppressed_exact": score_exact(self_suppressed, suppressed),
                            }
                    condition_results[condition] = {
                        "native": native, "suppressed": suppressed, "scans": scans,
                        "delta_summaries": {
                            b: residual_delta_summaries(native_states["original_candidate"], suppressed_states["original_candidate"], boundary=b)
                            for b in BOUNDARIES
                        },
                    }
                else:
                    dose_rows = {}
                    for gain in dose_lambdas:
                        source_states = interpolated_states(native_states, suppressed_states, layer=layer, boundary=boundary, gain=float(gain))
                        dose_rows[str(gain)] = score_preference_with_residual_source(
                            model=model, prepared=prepared[condition], prefix_token_ids=prefix, bridge_token_ids=bridge,
                            original_suffix_ids=suffix_o, counterfactual_suffix_ids=suffix_c,
                            current_generated_index=current, layer_index=layer, boundary=boundary,
                            source_states_by_candidate=source_states, suppression_generated_index=tpre,
                            suppression_layers=suppression_layers, source_positions=groups["T"], selected_heads=all_heads,
                            suppression_gain=0.0, seed=int(config["seed"]),
                        )
                    condition_results[condition] = {"native": native, "suppressed": suppressed, "dose": dose_rows, "layer": layer, "boundary": boundary}
                del native_states, suppressed_states
                gc.collect()
                torch.cuda.empty_cache()
            target_results[target_id] = {"coordinate": config["targets"][target_id]["coordinate"], "t_star_generated_index": current, "t_pre_generated_index": tpre, "conditions": condition_results}
        result_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(result_path, {
            "base_problem_id": base, "example_id": str(item["example_id"]), "mode": args.mode,
            "cohort_role": item["stage3c6_cohort_role"], "target_results": target_results,
            "runtime_seconds": time.perf_counter() - started, "current_position_only": True,
            "past_token_kv_donor_patched": False, "visual_kv_donor_patched": False,
            "selection_used_attention": False, "sink_directly_intervened": False,
        })
        completed += 1
        print(f"[{completed}/{len(manifest)}] {args.mode} base {base} seconds={time.perf_counter()-started:.1f}", flush=True)
        del prepared, metadata, target_results
        gc.collect()
        torch.cuda.empty_cache()
    write_json(output_dir / "resource_summary.json", {
        "mode": args.mode, "completed": completed, "requested": len(manifest),
        "wall_seconds_after_model_load": time.perf_counter() - run_started,
        "peak_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "peak_reserved_bytes": int(torch.cuda.max_memory_reserved()), "gpu_name": str(environment["gpu_name"]),
    })


if __name__ == "__main__":
    main()
