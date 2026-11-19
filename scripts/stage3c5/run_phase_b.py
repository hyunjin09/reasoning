#!/usr/bin/env python3
"""Run frozen Stage 3C.5 bidirectional R/Q/h_pre carrier patches."""

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
from visual_reasoning.stage3b0.layout import build_token_groups
from visual_reasoning.stage3c5.carriers import (
    capture_preference_carrier_states,
    score_preference_with_hpre_source,
    score_preference_with_token_source,
)
from visual_reasoning.stage3c5.runtime import summarize_state


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c5"
CONDITIONS = ("O", "O_sham", "C", "C_sham")
PAIRS = (
    ("O", "O", "self_O"),
    ("C", "C", "self_C"),
    ("C", "O", "semantic_O_into_C"),
    ("O", "C", "semantic_C_into_O"),
    ("O", "O_sham", "sham_Osham_into_O"),
    ("O_sham", "O", "sham_O_into_Osham"),
    ("C", "C_sham", "sham_Csham_into_C"),
    ("C_sham", "C", "sham_C_into_Csham"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("validation", "primary", "gated_r"), required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--carriers", default="R_last1,Q,h_pre")
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


def capture_summary(states: dict[str, dict[str, Any]], selected_layers: list[int]) -> dict[str, Any]:
    result = {}
    for candidate, state in states.items():
        result[candidate] = {
            "h_pre": state["h_pre_summary"],
            "kv_capture_audit": state["kv_audit"],
            "h_pre_boundary_audit": state["boundary_audit"],
            "selected_layer_tensor_summaries": {
                str(layer): {
                    "key": summarize_state(state["kv_layers"][layer][0]),
                    "value": summarize_state(state["kv_layers"][layer][1]),
                }
                for layer in selected_layers
            },
        }
    return result


def main() -> None:
    args = parse_args()
    config = read_json(OUT / "config/stage3c5_config.json")
    gate = read_json(OUT / "analysis/phase_b_gate.json")
    if not gate["pass"]:
        raise RuntimeError("Phase B is prohibited because the isolated t_pre gate did not pass")
    scopes = read_json(OUT / "config/tpre_layer_scopes.json")["scopes"]
    selected_scope = str(gate["selected_layer_scope"]["scope_id"])
    selected_layers = [int(value) for value in scopes[selected_scope]]
    carriers = [value.strip() for value in args.carriers.split(",") if value.strip()]
    allowed = {"R_last1", "R_last2", "R_last4", "Q", "h_pre"}
    if not carriers or not set(carriers) <= allowed:
        raise ValueError(f"Unsupported carriers: {carriers}")
    if args.mode == "gated_r" and not set(carriers) <= {"R_last2", "R_last4"}:
        raise ValueError("gated_r mode may contain only R_last2/R_last4")
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
    data = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "run_config.json", {
        "mode": args.mode, "manifest": str(args.manifest.resolve()),
        "shard_index": local_rank, "shard_count": world_size,
        "base_problem_ids": [str(row["base_problem_id"]) for row in manifest],
        "selected_scope": selected_scope, "selected_layers": selected_layers,
        "carriers": carriers, "pairs": [list(value) for value in PAIRS],
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
        row = data[str(item["example_id"])]
        prepared: dict[str, dict[str, Any]] = {}
        metadata: dict[str, dict[str, Any]] = {}
        for condition, path in condition_paths(base).items():
            prepared[condition], metadata[condition] = prepare_custom_image(processor, row, path, device="cuda")
        prompt_ids = [metadata[condition]["prompt_token_ids"] for condition in CONDITIONS]
        grids = [metadata[condition]["image_grid_thw"] for condition in CONDITIONS]
        if not all(value == prompt_ids[0] for value in prompt_ids[1:]) or not all(value == grids[0] for value in grids[1:]):
            raise RuntimeError(f"Condition token/grid alignment failed for base {base}")
        question = str(row.get("query_cot") or row.get("question") or "")
        question_ids = processor.tokenizer.encode(question, add_special_tokens=False)
        token_groups = build_token_groups(
            prompt_token_ids=prompt_ids[0],
            visual_token_indices=metadata["O"]["visual_token_indices"],
            question_token_ids=question_ids,
        )
        pair_by_target = {value["target_id"]: value for value in item["state_pairs"]}
        target_results: dict[str, Any] = {}
        persisted_hpre: dict[str, torch.Tensor] = {}
        for target_id in ("target_a", "target_b"):
            current = int(pair_by_target[target_id]["state_R"]["generated_index"])
            tpre = current - 1
            prefix, bridge, suffix_o, suffix_c = evidence_sequences(events[base], current)
            prompt_length = len(prompt_ids[0])
            current_absolute = prompt_length + current - 1
            r_positions = {
                "R_last1": [prompt_length + index - 1 for index in range(current - 1, current)],
                "R_last2": [prompt_length + index - 1 for index in range(current - 2, current)],
                "R_last4": [prompt_length + index - 1 for index in range(current - 4, current)],
            }
            if any(position < prompt_length for position in r_positions["R_last4"]):
                raise RuntimeError(f"Insufficient generated history for base {base}/{target_id}")
            capture_positions = sorted(set(token_groups["Q"]) | set(r_positions["R_last4"]))
            hpre_layer = int(config["targets"][target_id]["layer_index"])
            native: dict[str, Any] = {}
            states: dict[str, dict[str, dict[str, Any]]] = {}
            capture_audits: dict[str, Any] = {}
            for condition in CONDITIONS:
                native[condition], states[condition] = capture_preference_carrier_states(
                    model=model, prepared=prepared[condition], prefix_token_ids=prefix,
                    bridge_token_ids=bridge, original_suffix_ids=suffix_o,
                    counterfactual_suffix_ids=suffix_c, capture_positions=capture_positions,
                    selected_layers=selected_layers, current_absolute_position=current_absolute,
                    hpre_layer=hpre_layer, seed=int(config["seed"]),
                )
                capture_audits[condition] = capture_summary(states[condition], selected_layers)
                for candidate in ("original_candidate", "counterfactual_candidate"):
                    persisted_hpre[f"{target_id}.{condition}.{candidate}"] = states[condition][candidate]["h_pre"].detach().float().cpu()
            carrier_results: dict[str, Any] = {}
            for carrier in carriers:
                source_positions = token_groups["Q"] if carrier == "Q" else r_positions.get(carrier)
                pair_results: dict[str, Any] = {}
                for recipient, donor, pair_name in PAIRS:
                    if carrier == "h_pre":
                        score = score_preference_with_hpre_source(
                            model=model, prepared=prepared[recipient], prefix_token_ids=prefix,
                            bridge_token_ids=bridge, original_suffix_ids=suffix_o,
                            counterfactual_suffix_ids=suffix_c, donor_states=states[donor],
                            current_absolute_position=current_absolute, hpre_layer=hpre_layer,
                            seed=int(config["seed"]),
                        )
                    else:
                        assert source_positions is not None
                        score = score_preference_with_token_source(
                            model=model, prepared=prepared[recipient], prefix_token_ids=prefix,
                            bridge_token_ids=bridge, original_suffix_ids=suffix_o,
                            counterfactual_suffix_ids=suffix_c, donor_states=states[donor],
                            captured_positions=capture_positions, source_positions=source_positions,
                            selected_layers=selected_layers, current_absolute_position=current_absolute,
                            visual_positions=token_groups["V"], seed=int(config["seed"]),
                        )
                    pair_results[pair_name] = {"recipient": recipient, "donor": donor, "score": score}
                repeat = None
                if args.repeat_first and item_index == 0:
                    recipient, donor = "C", "O"
                    if carrier == "h_pre":
                        repeated = score_preference_with_hpre_source(
                            model=model, prepared=prepared[recipient], prefix_token_ids=prefix,
                            bridge_token_ids=bridge, original_suffix_ids=suffix_o,
                            counterfactual_suffix_ids=suffix_c, donor_states=states[donor],
                            current_absolute_position=current_absolute, hpre_layer=hpre_layer,
                            seed=int(config["seed"]),
                        )
                    else:
                        assert source_positions is not None
                        repeated = score_preference_with_token_source(
                            model=model, prepared=prepared[recipient], prefix_token_ids=prefix,
                            bridge_token_ids=bridge, original_suffix_ids=suffix_o,
                            counterfactual_suffix_ids=suffix_c, donor_states=states[donor],
                            captured_positions=capture_positions, source_positions=source_positions,
                            selected_layers=selected_layers, current_absolute_position=current_absolute,
                            visual_positions=token_groups["V"], seed=int(config["seed"]),
                        )
                    reference = pair_results["semantic_O_into_C"]["score"]
                    repeat = {
                        "exact": deterministic_view(repeated) == deterministic_view(reference),
                        "D_max_abs_delta": abs(float(repeated["D"]) - float(reference["D"])),
                    }
                carrier_results[carrier] = {
                    "source_positions": source_positions if source_positions is not None else [current_absolute],
                    "selected_layers": selected_layers if carrier != "h_pre" else [hpre_layer],
                    "pairs": pair_results, "repeat_audit": repeat,
                }
            target_results[target_id] = {
                "coordinate": config["targets"][target_id]["coordinate"],
                "t_star_generated_index": current, "t_pre_generated_index": tpre,
                "t_star_absolute_position": current_absolute,
                "Q_positions": token_groups["Q"], "R_positions": r_positions,
                "capture_positions": capture_positions, "selected_scope": selected_scope,
                "selected_layers": selected_layers, "h_pre_layer": hpre_layer,
                "native": native, "capture_audits": capture_audits,
                "carriers": carrier_results,
            }
            del states
            gc.collect()
            torch.cuda.empty_cache()
        result_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(persisted_hpre, result_path.parent / "hpre_states.pt")
        write_json(result_path, {
            "base_problem_id": base, "example_id": str(item["example_id"]),
            "cohort_role": item["stage3c5_cohort_role"], "mode": args.mode,
            "condition_prompt_ids_exact": True, "condition_image_grids_exact": True,
            "token_groups": token_groups, "target_results": target_results,
            "hpre_tensor_artifact": "hpre_states.pt",
            "runtime_seconds": time.perf_counter() - started,
            "visual_kv_donor_patch": False, "sink_directly_intervened": False,
            "teacher_forced_tokens_frozen": True, "selection_used_attention": False,
        })
        completed += 1
        print(f"[{completed}/{len(manifest)}] {args.mode} base {base} seconds={time.perf_counter()-started:.1f}", flush=True)
        del prepared, metadata, target_results, persisted_hpre
        gc.collect()
        torch.cuda.empty_cache()
    write_json(output_dir / "resource_summary.json", {
        "mode": args.mode, "carriers": carriers, "completed": completed, "requested": len(manifest),
        "wall_seconds_after_model_load": time.perf_counter() - run_started,
        "peak_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "peak_reserved_bytes": int(torch.cuda.max_memory_reserved()),
        "gpu_name": str(environment["gpu_name"]),
    })


if __name__ == "__main__":
    main()
