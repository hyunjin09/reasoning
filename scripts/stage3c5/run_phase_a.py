#!/usr/bin/env python3
"""Run Stage 3C.5 t_pre layer localization and frozen baselines."""

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
from visual_reasoning.stage3c5.runtime import (
    score_native_preference_with_readout,
    score_preference_with_tpre_readout,
)
from visual_reasoning.stage3c5.protocol import reduced_control_arms


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c5"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("validation", "phase_a", "controls"), required=True)
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


def deterministic_view(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: deterministic_view(item) for key, item in value.items() if key != "runtime_seconds"}
    if isinstance(value, list):
        return [deterministic_view(item) for item in value]
    return value


def original_path(base: str) -> Path:
    metadata = read_json(OUT.parent / "stage3b3_redesign/counterfactual_shams" / base / "edit_metadata.json")
    if metadata["manual_validation"]["status"] != "pass":
        raise RuntimeError(f"Four-condition validation failed for base {base}")
    return ROOT / metadata["paths"]["O"]


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


def source_groups(*, target: Sequence[int], mention: Sequence[int], irrelevant: Sequence[int]) -> dict[str, list[int]]:
    groups = {
        "T": sorted({int(value) for value in target}),
        "M": sorted({int(value) for value in mention}),
        "I": sorted({int(value) for value in irrelevant}),
    }
    sets = [set(groups[name]) for name in ("T", "M", "I")]
    if any(not values for values in sets) or any(
        sets[left] & sets[right] for left in range(3) for right in range(left + 1, 3)
    ):
        raise ValueError("T/M/I groups must be nonempty and disjoint")
    return groups


def arm_score(
    *, model: Any, prepared: dict[str, Any], event: dict[str, Any], current: int,
    queries: Sequence[int], layers: Sequence[int], sources: Sequence[int],
    all_heads: Sequence[int], readout_layer: int, seed: int, gain: float = 0.0,
) -> tuple[dict[str, Any], dict[str, torch.Tensor]]:
    prefix, bridge, original, counterfactual = evidence_sequences(event, current)
    return score_preference_with_tpre_readout(
        model=model, prepared=prepared, prefix_token_ids=prefix, bridge_token_ids=bridge,
        original_suffix_ids=original, counterfactual_suffix_ids=counterfactual,
        current_generated_index=current, intervention_generated_indices=queries,
        intervention_layers=layers, source_positions=sources, selected_heads=all_heads,
        gain=gain, readout_layer=readout_layer, seed=seed,
    )


def main() -> None:
    args = parse_args()
    config = read_json(OUT / "config/stage3c5_config.json")
    scopes = read_json(OUT / "config/tpre_layer_scopes.json")["scopes"]
    phase_b_gate = read_json(OUT / "analysis/phase_b_gate.json") if args.mode == "controls" else None
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
        "mode": args.mode, "manifest": str(args.manifest.resolve()),
        "shard_index": local_rank, "shard_count": world_size,
        "base_problem_ids": [str(row["base_problem_id"]) for row in manifest],
    })
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, 40_960)
    if "A5000" not in str(environment["gpu_name"]):
        raise RuntimeError(f"Stage 3C.5 requires A5000, observed {environment['gpu_name']}")
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
    torch.cuda.reset_peak_memory_stats()
    run_started = time.perf_counter()
    all_heads = list(range(observed["logical_query_heads"]))
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
        event, roi, mention = events[base], rois[base], mentions[base]
        prepared, metadata = prepare_custom_image(processor, data[str(item["example_id"])], original_path(base), device="cuda")
        if metadata["visual_token_indices"] != roi["absolute_source_groups"]["V_all"]:
            raise RuntimeError(f"Visual-token layout mismatch for base {base}")
        groups = source_groups(
            target=roi["absolute_source_groups"]["V_target"],
            mention=mention["mention_absolute_source_positions"],
            irrelevant=roi["absolute_source_groups"]["V_irrelevant"],
        )
        pair_by_target = {row["target_id"]: row for row in item["state_pairs"]}
        target_results: dict[str, Any] = {}
        state_tensors: dict[str, torch.Tensor] = {}
        for target_id in ("target_a", "target_b"):
            current = int(pair_by_target[target_id]["state_R"]["generated_index"])
            t_pre = current - 1
            if t_pre <= 0:
                raise RuntimeError(f"t_pre unavailable for base {base}/{target_id}")
            layer = int(config["targets"][target_id]["layer_index"])
            prefix, bridge, original, counterfactual = evidence_sequences(event, current)
            native, tensors = score_native_preference_with_readout(
                model=model, prepared=prepared, prefix_token_ids=prefix, bridge_token_ids=bridge,
                original_suffix_ids=original, counterfactual_suffix_ids=counterfactual,
                current_generated_index=current, readout_layer=layer, seed=int(config["seed"]),
            )
            for key, tensor in tensors.items():
                state_tensors[f"{target_id}.A0.{key}"] = tensor
            arms: dict[str, Any] = {}
            if args.mode == "controls":
                assert phase_b_gate is not None and phase_b_gate["pass"]
                selected_scope = str(phase_b_gate["selected_layer_scope"]["scope_id"])
                for spec in reduced_control_arms(scopes[selected_scope]):
                    label = str(spec["arm_id"])
                    score, tensors = arm_score(
                        model=model, prepared=prepared, event=event, current=current,
                        queries=[t_pre], layers=spec["layers"], sources=groups[str(spec["source"])],
                        all_heads=all_heads, readout_layer=layer, seed=int(config["seed"]),
                    )
                    arms[label] = score
                    for key, tensor in tensors.items():
                        state_tensors[f"{target_id}.{label}.{key}"] = tensor
            else:
                phase_scopes = list(scopes) if args.mode == "phase_a" else ["P0", "P5"]
                for label in phase_scopes:
                    score, tensors = arm_score(
                        model=model, prepared=prepared, event=event, current=current,
                        queries=[t_pre], layers=scopes[label], sources=groups["T"],
                        all_heads=all_heads, readout_layer=layer, seed=int(config["seed"]),
                    )
                    arms[label] = score
                    for key, tensor in tensors.items():
                        state_tensors[f"{target_id}.{label}.{key}"] = tensor
                for label, queries in (("A1_current", [current]), ("A3_joint", [t_pre, current])):
                    score, tensors = arm_score(
                        model=model, prepared=prepared, event=event, current=current,
                        queries=queries, layers=scopes["P5"], sources=groups["T"],
                        all_heads=all_heads, readout_layer=layer, seed=int(config["seed"]),
                    )
                    arms[label] = score
                    for key, tensor in tensors.items():
                        state_tensors[f"{target_id}.{label}.{key}"] = tensor
            identity = None
            repeat = None
            if args.mode == "validation" and item_index == 0:
                identity_score, _ = arm_score(
                    model=model, prepared=prepared, event=event, current=current,
                    queries=[t_pre], layers=scopes["P0"], sources=groups["T"],
                    all_heads=all_heads, readout_layer=layer, seed=int(config["seed"]), gain=1.0,
                )
                identity = {
                    "D_exact": float(identity_score["D"]) == float(native["D"]),
                    "original_token_log_probabilities_exact": identity_score["original_candidate"]["token_log_probabilities"] == native["original_candidate"]["token_log_probabilities"],
                    "counterfactual_token_log_probabilities_exact": identity_score["counterfactual_candidate"]["token_log_probabilities"] == native["counterfactual_candidate"]["token_log_probabilities"],
                }
                if args.repeat_first:
                    repeated, _ = arm_score(
                        model=model, prepared=prepared, event=event, current=current,
                        queries=[t_pre], layers=scopes["P5"], sources=groups["T"],
                        all_heads=all_heads, readout_layer=layer, seed=int(config["seed"]),
                    )
                    repeat = {
                        "exact": deterministic_view(repeated) == deterministic_view(arms["P5"]),
                        "D_max_abs_delta": abs(float(repeated["D"]) - float(arms["P5"]["D"])),
                    }
            target_results[target_id] = {
                "coordinate": config["targets"][target_id]["coordinate"],
                "t_star_generated_index": current,
                "t_pre_generated_index": t_pre,
                "native_A0": native,
                "arms": arms,
                "A2_tpre_alias": "P5" if args.mode != "controls" else None,
                "identity_audit": identity,
                "repeat_audit": repeat,
            }
        result_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(state_tensors, result_path.parent / "state_readouts.pt")
        write_json(result_path, {
            "base_problem_id": base, "example_id": str(item["example_id"]),
            "cohort_role": item["stage3c5_cohort_role"], "mode": args.mode,
            "condition": "O", "source_groups": groups, "target_results": target_results,
            "state_tensor_artifact": "state_readouts.pt",
            "runtime_seconds": time.perf_counter() - started,
            "selection_used_attention": False, "target_contribution_only": True,
            "teacher_forced_tokens_frozen": True, "downstream_recomputation_allowed": True,
            "sink_directly_intervened": False, "donor_state_patched": False,
        })
        completed += 1
        print(f"[{completed}/{len(manifest)}] {args.mode} base {base} seconds={time.perf_counter()-started:.1f}", flush=True)
        del prepared, metadata, target_results, state_tensors
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
