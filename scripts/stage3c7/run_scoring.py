#!/usr/bin/env python3
"""Run frozen Stage 3C.7 cache, residual, joint, and control arms."""

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
from visual_reasoning.stage3b0.layout import build_token_groups
from visual_reasoning.stage3c5.carriers import select_captured_positions
from visual_reasoning.stage3c7.runtime import (
    CANDIDATES,
    cache_delta_summaries,
    capture_native_or_suppressed_states,
    score_suppressed_with_prompt_cache_control,
    score_suppressed_with_rescue,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c7"
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


def score_exact(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return bool(
        float(left["D"]) == float(right["D"])
        and left[CANDIDATES[0]]["token_log_probabilities"] == right[CANDIDATES[0]]["token_log_probabilities"]
        and left[CANDIDATES[1]]["token_log_probabilities"] == right[CANDIDATES[1]]["token_log_probabilities"]
    )


def condition_paths(base: str) -> dict[str, Path]:
    metadata = read_json(ROOT / "outputs/stage3b3_redesign/counterfactual_shams" / base / "edit_metadata.json")
    if metadata["manual_validation"]["status"] != "pass":
        raise RuntimeError(f"Image validation failed for base {base}")
    return {condition: ROOT / metadata["paths"][condition] for condition in CONDITIONS}


def evidence_sequences(event: dict[str, Any], state_index: int) -> tuple[list[int], list[int], list[int], list[int]]:
    context = [int(value) for value in event["history_before_ed_token_ids"]]
    ed = int(event["ed_generated_index"])
    index = int(state_index)
    if not 1 <= index <= ed == len(context):
        raise ValueError("Frozen target state is outside evidence history")
    return (
        context[:index], context[index:ed],
        [int(value) for value in event["original_divergent_suffix_ids"]],
        [int(value) for value in event["counterfactual_divergent_suffix_ids"]],
    )


def prior_stage3c6(base: str, family: str) -> dict[str, Any]:
    roots = {
        "phase_a": ("phase_a", "phase_a_validation"),
        "phase_b": ("phase_b_boundary", "phase_b_validation"),
    }[family]
    matches = [
        path for root in roots
        for path in (ROOT / "outputs/stage3c6/raw" / root).glob(f"shard_*/examples/{base}/result.json")
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one Stage 3C.6 {family} result for base {base}; got {matches}")
    return read_json(matches[0])


def historical_reproduction(
    *, base: str, target_id: str, condition: str,
    native: dict[str, Any], suppressed: dict[str, Any], residual: dict[str, Any],
) -> dict[str, Any]:
    old_a = prior_stage3c6(base, "phase_a")["target_results"][target_id]["conditions"][condition]
    if target_id == "target_a":
        old_b = prior_stage3c6(base, "phase_b")["target_results"][target_id]["conditions"][condition]
        old_residual = old_b["scans"]["L33_h_post_attn"]["rescue"]
    else:
        old_residual = old_a["rescue_by_layer"]["35"]["rescue"]
    return {
        "native_exact": score_exact(native, old_a["native"]),
        "suppressed_exact": score_exact(suppressed, old_a["suppressed"]),
        "residual_exact": score_exact(residual, old_residual),
        "native_D_delta": float(native["D"]) - float(old_a["native"]["D"]),
        "suppressed_D_delta": float(suppressed["D"]) - float(old_a["suppressed"]["D"]),
        "residual_D_delta": float(residual["D"]) - float(old_residual["D"]),
    }


def state_tensor_artifact(
    *, native: dict[str, dict[str, Any]], suppressed: dict[str, dict[str, Any]],
    tpre_absolute: int, residual_layer: int, residual_boundary: str,
) -> dict[str, torch.Tensor]:
    result: dict[str, torch.Tensor] = {}
    for state_name, states in (("native", native), ("suppressed", suppressed)):
        for candidate in CANDIDATES:
            cache = select_captured_positions(
                states[candidate]["cache"],
                captured_positions=states[candidate]["cache_positions"],
                selected_positions=[tpre_absolute],
            )
            for layer, (key, value) in cache.items():
                result[f"{state_name}.{candidate}.L{layer}.K"] = key.detach().cpu()
                result[f"{state_name}.{candidate}.L{layer}.V"] = value.detach().cpu()
            result[f"{state_name}.{candidate}.L{residual_layer}.{residual_boundary}"] = (
                states[candidate]["residual"][residual_boundary][residual_layer].detach().cpu()
            )
    return result


def main() -> None:
    args = parse_args()
    config = read_json(OUT / "config/stage3c7_config.json")
    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    torch.cuda.set_device(local_rank if world_size > 1 else 0)
    output_dir = args.output_dir.resolve()
    output_dir.relative_to(OUT.resolve())
    if world_size > 1:
        output_dir = output_dir / f"shard_{local_rank}"
    manifest = read_jsonl(args.manifest)[local_rank::world_size]
    if args.max_bases:
        manifest = manifest[: args.max_bases]
    events = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl")}
    rois = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl")}
    data = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "run_config.json", {
        "mode": args.mode, "manifest": str(args.manifest.resolve()),
        "shard_index": local_rank, "shard_count": world_size,
        "base_problem_ids": [str(row["base_problem_id"]) for row in manifest],
        "phase_a_arms": config["phase_a_arms"], "phase_b_arms": config["phase_b_arms"],
        "self_controls": args.mode == "validation", "q_prompt_control": True,
    })
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, 40_960)
    if "A5000" not in str(environment["gpu_name"]):
        raise RuntimeError(f"Stage 3C.7 requires A5000, observed {environment['gpu_name']}")
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
    all_heads = list(range(observed["logical_query_heads"]))
    full_layers = [int(value) for value in config["cache_scope"]["layers"]]
    torch.cuda.reset_peak_memory_stats()
    started_run = time.perf_counter()
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
            prepared[condition], metadata[condition] = prepare_custom_image(
                processor, data[str(item["example_id"])], path, device="cuda"
            )
        if metadata["O"]["prompt_token_ids"] != metadata["C"]["prompt_token_ids"] or metadata["O"]["image_grid_thw"] != metadata["C"]["image_grid_thw"]:
            raise RuntimeError(f"O/C prompt or grid mismatch for base {base}")
        question = str(data[str(item["example_id"])].get("query_cot") or data[str(item["example_id"])].get("question") or "")
        groups = build_token_groups(
            prompt_token_ids=metadata["O"]["prompt_token_ids"],
            visual_token_indices=metadata["O"]["visual_token_indices"],
            question_token_ids=processor.tokenizer.encode(question, add_special_tokens=False),
        )
        target_positions = [int(value) for value in rois[base]["absolute_source_groups"]["V_target"]]
        visual_positions = [int(value) for value in metadata["O"]["visual_token_indices"]]
        if visual_positions != rois[base]["absolute_source_groups"]["V_all"]:
            raise RuntimeError(f"Visual-token layout mismatch for base {base}")
        pairs = {row["target_id"]: row for row in item["state_pairs"]}
        target_results: dict[str, Any] = {}
        tensors: dict[str, torch.Tensor] = {}
        for target_id in ("target_a", "target_b"):
            spec = config["residual_boundaries"][target_id]
            current = int(pairs[target_id]["state_R"]["generated_index"])
            tpre = current - 1
            prefix, bridge, suffix_o, suffix_c = evidence_sequences(events[base], current)
            condition_results: dict[str, Any] = {}
            for condition in CONDITIONS:
                common = dict(
                    model=model, prepared=prepared[condition], prefix_token_ids=prefix,
                    bridge_token_ids=bridge, original_suffix_ids=suffix_o,
                    counterfactual_suffix_ids=suffix_c, current_generated_index=current,
                    tpre_generated_index=tpre, cache_layers=full_layers,
                    residual_layer=int(spec["layer"]), suppression_layers=full_layers,
                    source_positions=target_positions, selected_heads=all_heads,
                    seed=int(config["seed"]), additional_cache_positions=groups["Q"],
                )
                native, native_states = capture_native_or_suppressed_states(**common, suppression_enabled=False)
                suppressed, suppressed_states = capture_native_or_suppressed_states(**common, suppression_enabled=True)
                rescue_common = dict(
                    model=model, prepared=prepared[condition], prefix_token_ids=prefix,
                    bridge_token_ids=bridge, original_suffix_ids=suffix_o,
                    counterfactual_suffix_ids=suffix_c, current_generated_index=current,
                    tpre_generated_index=tpre, suppression_layers=full_layers,
                    source_positions=target_positions, selected_heads=all_heads,
                    visual_positions=visual_positions, seed=int(config["seed"]),
                    suppression_enabled=True,
                )
                arms = {
                    "C2_K": score_suppressed_with_rescue(**rescue_common, native_states=native_states, cache_layers=full_layers, cache_mode="K", residual_layer=None, residual_boundary=None),
                    "C3_V": score_suppressed_with_rescue(**rescue_common, native_states=native_states, cache_layers=full_layers, cache_mode="V", residual_layer=None, residual_boundary=None),
                    "C4_KV": score_suppressed_with_rescue(**rescue_common, native_states=native_states, cache_layers=full_layers, cache_mode="KV", residual_layer=None, residual_boundary=None),
                    "J1_residual": score_suppressed_with_rescue(**rescue_common, native_states=native_states, cache_layers=[], cache_mode=None, residual_layer=int(spec["layer"]), residual_boundary=str(spec["boundary"])),
                    "J3_downstream_KV": score_suppressed_with_rescue(**rescue_common, native_states=native_states, cache_layers=spec["downstream_cache_layers"], cache_mode="KV", residual_layer=None, residual_boundary=None),
                    "J4_joint": score_suppressed_with_rescue(**rescue_common, native_states=native_states, cache_layers=spec["downstream_cache_layers"], cache_mode="KV", residual_layer=int(spec["layer"]), residual_boundary=str(spec["boundary"])),
                    "J5_full_KV_plus_residual": score_suppressed_with_rescue(**rescue_common, native_states=native_states, cache_layers=full_layers, cache_mode="KV", residual_layer=int(spec["layer"]), residual_boundary=str(spec["boundary"])),
                }
                q_control = score_suppressed_with_prompt_cache_control(
                    model=model, prepared=prepared[condition], prefix_token_ids=prefix,
                    bridge_token_ids=bridge, original_suffix_ids=suffix_o,
                    counterfactual_suffix_ids=suffix_c, current_generated_index=current,
                    tpre_generated_index=tpre, suppression_layers=full_layers,
                    source_positions=target_positions, selected_heads=all_heads,
                    native_states=native_states, prompt_positions=groups["Q"],
                    visual_positions=visual_positions, seed=int(config["seed"]),
                )
                self_controls = None
                if args.mode == "validation":
                    native_common = {**rescue_common, "suppression_enabled": False}
                    self_controls = {
                        "native_cache": score_suppressed_with_rescue(**native_common, native_states=native_states, cache_layers=full_layers, cache_mode="KV", residual_layer=None, residual_boundary=None),
                        "suppressed_cache": score_suppressed_with_rescue(**rescue_common, native_states=suppressed_states, cache_layers=full_layers, cache_mode="KV", residual_layer=None, residual_boundary=None),
                        "native_residual": score_suppressed_with_rescue(**native_common, native_states=native_states, cache_layers=[], cache_mode=None, residual_layer=int(spec["layer"]), residual_boundary=str(spec["boundary"])),
                        "suppressed_residual": score_suppressed_with_rescue(**rescue_common, native_states=suppressed_states, cache_layers=[], cache_mode=None, residual_layer=int(spec["layer"]), residual_boundary=str(spec["boundary"])),
                    }
                repeated = None
                if args.repeat_first and item_index == 0:
                    repeated_score = score_suppressed_with_rescue(
                        **rescue_common, native_states=native_states,
                        cache_layers=spec["downstream_cache_layers"], cache_mode="KV",
                        residual_layer=int(spec["layer"]), residual_boundary=str(spec["boundary"]),
                    )
                    repeated = {"arm": "J4_joint", "exact": score_exact(repeated_score, arms["J4_joint"])}
                reproduction = historical_reproduction(
                    base=base, target_id=target_id, condition=condition,
                    native=native, suppressed=suppressed, residual=arms["J1_residual"],
                )
                cache_deltas = {
                    candidate: cache_delta_summaries(
                        select_captured_positions(native_states[candidate]["cache"], captured_positions=native_states[candidate]["cache_positions"], selected_positions=[native["tpre_absolute_position"]]),
                        select_captured_positions(suppressed_states[candidate]["cache"], captured_positions=suppressed_states[candidate]["cache_positions"], selected_positions=[suppressed["tpre_absolute_position"]]),
                    ) for candidate in CANDIDATES
                }
                condition_results[condition] = {
                    "native": native, "suppressed": suppressed, "arms": arms,
                    "q_prompt_control": q_control, "self_controls": self_controls,
                    "stage3c6_reproduction": reproduction, "cache_deltas": cache_deltas,
                    "cache_capture_audits": {
                        "native": {candidate: native_states[candidate]["cache_audit"] for candidate in CANDIDATES},
                        "suppressed": {candidate: suppressed_states[candidate]["cache_audit"] for candidate in CANDIDATES},
                    },
                    "repeat": repeated,
                }
                prefix_name = f"{target_id}.{condition}"
                for key, value in state_tensor_artifact(
                    native=native_states, suppressed=suppressed_states,
                    tpre_absolute=native["tpre_absolute_position"], residual_layer=int(spec["layer"]),
                    residual_boundary=str(spec["boundary"]),
                ).items():
                    tensors[f"{prefix_name}.{key}"] = value
                del native_states, suppressed_states
                gc.collect()
                torch.cuda.empty_cache()
            context = events[base]["history_before_ed_token_ids"]
            target_results[target_id] = {
                "current_generated_index": current, "tpre_generated_index": tpre,
                "tpre_token_id": int(context[tpre - 1]),
                "tpre_token_text": processor.tokenizer.decode([int(context[tpre - 1])], skip_special_tokens=False),
                "residual_boundary": spec, "conditions": condition_results,
            }
        result_path.parent.mkdir(parents=True, exist_ok=True)
        tensor_path = result_path.parent / "native_suppressed_states.pt"
        torch.save(tensors, tensor_path)
        result = {
            "base_problem_id": base, "example_id": str(item["example_id"]),
            "cohort_role": args.mode, "target_results": target_results,
            "prompt_token_ids_exact": metadata["O"]["prompt_token_ids"] == metadata["C"]["prompt_token_ids"],
            "image_grid_exact": metadata["O"]["image_grid_thw"] == metadata["C"]["image_grid_thw"],
            "visual_positions": visual_positions, "question_positions": groups["Q"],
            "target_positions": target_positions, "state_tensor_artifact": tensor_path.name,
            "runtime_seconds": time.perf_counter() - started,
            "selection_used_attention": False, "cache_delta_used_for_selection": False,
            "sink_directly_intervened": False, "stage4_started": False,
        }
        write_json(result_path, result)
        completed += 1
        print(f"[{completed}/{len(manifest)}] base={base} seconds={result['runtime_seconds']:.1f}", flush=True)
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    write_json(output_dir / "run_summary.json", {
        "mode": args.mode, "completed": completed, "expected": len(manifest),
        "runtime_seconds": time.perf_counter() - started_run,
        "peak_gpu_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "peak_gpu_reserved_bytes": int(torch.cuda.max_memory_reserved()),
    })


if __name__ == "__main__":
    main()
