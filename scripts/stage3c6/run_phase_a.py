#!/usr/bin/env python3
"""Run the frozen 36-layer Stage 3C.6 h_pre suppression-rescue scan."""

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
    boundary_equivalence,
    capture_preference_states,
    residual_delta_summaries,
    score_preference_with_residual_source,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c6"
CONDITIONS = ("O", "C")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("validation", "primary"), required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-bases", type=int, default=0)
    parser.add_argument("--repeat-first", action="store_true")
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
    return (
        context[:index], context[index:ed],
        [int(value) for value in event["original_divergent_suffix_ids"]],
        [int(value) for value in event["counterfactual_divergent_suffix_ids"]],
    )


def score_exact(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return bool(
        float(left["D"]) == float(right["D"])
        and left["original_candidate"]["token_log_probabilities"] == right["original_candidate"]["token_log_probabilities"]
        and left["counterfactual_candidate"]["token_log_probabilities"] == right["counterfactual_candidate"]["token_log_probabilities"]
    )


def prior_stage3c5(base: str) -> dict[str, Any]:
    raw = ROOT / "outputs/stage3c5/raw"
    matches = [
        path
        for family in ("phase_a", "phase_a_validation")
        for path in (raw / family).glob(f"shard_*/examples/{base}/result.json")
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one Stage 3C.5 Phase-A result for base {base}")
    return read_json(matches[0])


def reproduction_record(
    native: dict[str, Any], suppressed: dict[str, Any], old: dict[str, Any]
) -> dict[str, Any]:
    prior_p4 = old["arms"].get("P4")
    return {
        "native_exact": score_exact(native, old["native_A0"]),
        "P4_comparison_available": prior_p4 is not None,
        "P4_suppressed_exact": score_exact(suppressed, prior_p4) if prior_p4 is not None else None,
        "native_D_delta": float(native["D"]) - float(old["native_A0"]["D"]),
        "P4_D_delta": float(suppressed["D"]) - float(prior_p4["D"]) if prior_p4 is not None else None,
    }


def main() -> None:
    args = parse_args()
    config = read_json(OUT / "config/stage3c6_config.json")
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
    data = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "run_config.json", {
        "mode": args.mode, "manifest": str(args.manifest.resolve()),
        "shard_index": local_rank, "shard_count": world_size,
        "base_problem_ids": [str(row["base_problem_id"]) for row in manifest],
        "conditions": list(CONDITIONS), "layers": config["hpre_scan_layers"],
        "self_controls_at_every_layer": True,
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
    layers = [int(value) for value in config["hpre_scan_layers"]]
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
        event, roi = events[base], rois[base]
        prepared: dict[str, dict[str, Any]] = {}
        metadata: dict[str, dict[str, Any]] = {}
        for condition, path in condition_paths(base).items():
            prepared[condition], metadata[condition] = prepare_custom_image(
                processor, data[str(item["example_id"])], path, device="cuda"
            )
        prompt_ids = [metadata[condition]["prompt_token_ids"] for condition in CONDITIONS]
        grids = [metadata[condition]["image_grid_thw"] for condition in CONDITIONS]
        if not all(value == prompt_ids[0] for value in prompt_ids[1:]) or not all(value == grids[0] for value in grids[1:]):
            raise RuntimeError(f"Condition token/grid alignment failed for base {base}")
        target_positions = [int(value) for value in roi["absolute_source_groups"]["V_target"]]
        if metadata["O"]["visual_token_indices"] != roi["absolute_source_groups"]["V_all"]:
            raise RuntimeError(f"Visual-token layout mismatch for base {base}")
        pair_by_target = {row["target_id"]: row for row in item["state_pairs"]}
        prior = prior_stage3c5(base)
        target_results: dict[str, Any] = {}
        persisted_hpre: dict[str, torch.Tensor] = {}
        for target_id in ("target_a", "target_b"):
            current = int(pair_by_target[target_id]["state_R"]["generated_index"])
            tpre = current - 1
            prefix, bridge, suffix_o, suffix_c = evidence_sequences(event, current)
            condition_results: dict[str, Any] = {}
            for condition in CONDITIONS:
                native, native_states = capture_preference_states(
                    model=model, prepared=prepared[condition], prefix_token_ids=prefix,
                    bridge_token_ids=bridge, original_suffix_ids=suffix_o,
                    counterfactual_suffix_ids=suffix_c, current_generated_index=current,
                    capture_layers=layers, suppression_generated_index=None,
                    suppression_layers=[], source_positions=target_positions,
                    selected_heads=all_heads, suppression_gain=1.0, seed=int(config["seed"]),
                )
                suppressed, suppressed_states = capture_preference_states(
                    model=model, prepared=prepared[condition], prefix_token_ids=prefix,
                    bridge_token_ids=bridge, original_suffix_ids=suffix_o,
                    counterfactual_suffix_ids=suffix_c, current_generated_index=current,
                    capture_layers=layers, suppression_generated_index=tpre,
                    suppression_layers=suppression_layers, source_positions=target_positions,
                    selected_heads=all_heads, suppression_gain=0.0, seed=int(config["seed"]),
                )
                candidate_state_exact = all(
                    torch.equal(native_states["original_candidate"]["h_pre"][layer], native_states["counterfactual_candidate"]["h_pre"][layer])
                    and torch.equal(suppressed_states["original_candidate"]["h_pre"][layer], suppressed_states["counterfactual_candidate"]["h_pre"][layer])
                    for layer in layers
                )
                for state_name, states in (("native", native_states), ("suppressed", suppressed_states)):
                    for candidate in ("original_candidate", "counterfactual_candidate"):
                        for layer in layers:
                            persisted_hpre[f"{target_id}.{condition}.{state_name}.{candidate}.h_pre.{layer}"] = states[candidate]["h_pre"][layer].detach().float().cpu()
                rescue_by_layer: dict[str, Any] = {}
                for layer in layers:
                    rescued = score_preference_with_residual_source(
                        model=model, prepared=prepared[condition], prefix_token_ids=prefix,
                        bridge_token_ids=bridge, original_suffix_ids=suffix_o,
                        counterfactual_suffix_ids=suffix_c, current_generated_index=current,
                        layer_index=layer, boundary="h_pre", source_states_by_candidate=native_states,
                        suppression_generated_index=tpre, suppression_layers=suppression_layers,
                        source_positions=target_positions, selected_heads=all_heads,
                        suppression_gain=0.0, seed=int(config["seed"]),
                    )
                    self_native = score_preference_with_residual_source(
                        model=model, prepared=prepared[condition], prefix_token_ids=prefix,
                        bridge_token_ids=bridge, original_suffix_ids=suffix_o,
                        counterfactual_suffix_ids=suffix_c, current_generated_index=current,
                        layer_index=layer, boundary="h_pre", source_states_by_candidate=native_states,
                        suppression_generated_index=None, suppression_layers=[],
                        source_positions=target_positions, selected_heads=all_heads,
                        suppression_gain=1.0, seed=int(config["seed"]),
                    )
                    self_suppressed = score_preference_with_residual_source(
                        model=model, prepared=prepared[condition], prefix_token_ids=prefix,
                        bridge_token_ids=bridge, original_suffix_ids=suffix_o,
                        counterfactual_suffix_ids=suffix_c, current_generated_index=current,
                        layer_index=layer, boundary="h_pre", source_states_by_candidate=suppressed_states,
                        suppression_generated_index=tpre, suppression_layers=suppression_layers,
                        source_positions=target_positions, selected_heads=all_heads,
                        suppression_gain=0.0, seed=int(config["seed"]),
                    )
                    rescue_by_layer[str(layer)] = {
                        "rescue": rescued,
                        "self_native_exact": score_exact(self_native, native),
                        "self_suppressed_exact": score_exact(self_suppressed, suppressed),
                        "self_native_boundary_audit_valid": self_native["boundary_patch_audits_valid"],
                        "self_suppressed_boundary_audit_valid": self_suppressed["boundary_patch_audits_valid"],
                    }
                repeat = None
                if args.repeat_first and item_index == 0 and target_id == "target_a" and condition == "O":
                    layer = 29
                    repeated = score_preference_with_residual_source(
                        model=model, prepared=prepared[condition], prefix_token_ids=prefix,
                        bridge_token_ids=bridge, original_suffix_ids=suffix_o,
                        counterfactual_suffix_ids=suffix_c, current_generated_index=current,
                        layer_index=layer, boundary="h_pre", source_states_by_candidate=native_states,
                        suppression_generated_index=tpre, suppression_layers=suppression_layers,
                        source_positions=target_positions, selected_heads=all_heads,
                        suppression_gain=0.0, seed=int(config["seed"]),
                    )
                    repeat = {"layer": layer, "exact": score_exact(repeated, rescue_by_layer[str(layer)]["rescue"])}
                reproduction = None
                if condition == "O":
                    old = prior["target_results"][target_id]
                    reproduction = reproduction_record(native, suppressed, old)
                condition_results[condition] = {
                    "native": native,
                    "suppressed": suppressed,
                    "rescue_by_layer": rescue_by_layer,
                    "hpre_delta_summaries": {
                        candidate: residual_delta_summaries(
                            native_states[candidate], suppressed_states[candidate], boundary="h_pre"
                        )
                        for candidate in ("original_candidate", "counterfactual_candidate")
                    },
                    "native_boundary_equivalence": boundary_equivalence(native_states["original_candidate"]),
                    "suppressed_boundary_equivalence": boundary_equivalence(suppressed_states["original_candidate"]),
                    "candidate_hpre_states_exact": candidate_state_exact,
                    "stage3c5_reproduction": reproduction,
                    "repeat_audit": repeat,
                }
                del native_states, suppressed_states
                gc.collect()
                torch.cuda.empty_cache()
            target_results[target_id] = {
                "coordinate": config["targets"][target_id]["coordinate"],
                "t_star_generated_index": current,
                "t_pre_generated_index": tpre,
                "conditions": condition_results,
            }
        result_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(persisted_hpre, result_path.parent / "hpre_states.pt")
        write_json(result_path, {
            "base_problem_id": base, "example_id": str(item["example_id"]),
            "cohort_role": item["stage3c6_cohort_role"], "mode": args.mode,
            "conditions": list(CONDITIONS), "condition_prompt_ids_exact": True,
            "condition_image_grids_exact": True, "target_positions": target_positions,
            "target_results": target_results, "hpre_tensor_artifact": "hpre_states.pt",
            "runtime_seconds": time.perf_counter() - started,
            "current_position_only": True, "past_token_kv_donor_patched": False,
            "visual_kv_donor_patched": False, "selection_used_attention": False,
            "teacher_forced_tokens_frozen": True, "sink_directly_intervened": False,
        })
        completed += 1
        print(f"[{completed}/{len(manifest)}] {args.mode} base {base} seconds={time.perf_counter()-started:.1f}", flush=True)
        del prepared, metadata, target_results, persisted_hpre
        gc.collect()
        torch.cuda.empty_cache()
    write_json(output_dir / "resource_summary.json", {
        "mode": args.mode, "completed": completed, "requested": len(manifest),
        "wall_seconds_after_model_load": time.perf_counter() - run_started,
        "peak_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "peak_reserved_bytes": int(torch.cuda.max_memory_reserved()),
        "gpu_name": str(environment["gpu_name"]),
    })


if __name__ == "__main__":
    main()
