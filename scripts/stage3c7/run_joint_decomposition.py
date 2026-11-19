#!/usr/bin/env python3
"""Run gated residual-plus-downstream K/V decomposition for passing targets."""

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
from visual_reasoning.stage3c7.runtime import capture_native_or_suppressed_states, score_suppressed_with_rescue


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c7"
CONDITIONS = ("O", "C")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=("validation", "primary"), required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--dataset-root", type=Path, required=True)
    p.add_argument("--model-checkpoint", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--resume", action="store_true")
    return p.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def condition_paths(base: str) -> dict[str, Path]:
    metadata = read_json(ROOT / "outputs/stage3b3_redesign/counterfactual_shams" / base / "edit_metadata.json")
    return {condition: ROOT / metadata["paths"][condition] for condition in CONDITIONS}


def evidence_sequences(event: dict[str, Any], state_index: int) -> tuple[list[int], list[int], list[int], list[int]]:
    history = [int(value) for value in event["history_before_ed_token_ids"]]
    ed = int(event["ed_generated_index"])
    return history[:state_index], history[state_index:ed], [int(v) for v in event["original_divergent_suffix_ids"]], [int(v) for v in event["counterfactual_divergent_suffix_ids"]]


def prior_result(base: str, family: str) -> dict[str, Any]:
    paths = sorted((OUT / "raw" / family).glob(f"shard_*/examples/{base}/result.json"))
    if len(paths) != 1:
        raise RuntimeError(f"Expected one prior result for {base}/{family}")
    return read_json(paths[0])


def score_exact(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return bool(float(left["D"]) == float(right["D"]) and left["original_candidate"]["token_log_probabilities"] == right["original_candidate"]["token_log_probabilities"] and left["counterfactual_candidate"]["token_log_probabilities"] == right["counterfactual_candidate"]["token_log_probabilities"])


def main() -> None:
    args = parse_args()
    config = read_json(OUT / "config/stage3c7_config.json")
    gate = read_json(OUT / "phase_b_joint/joint_kv_decomposition_gate.json")
    active = [target for target, row in gate["targets"].items() if row["run"]]
    if not active:
        raise RuntimeError("Joint K/V decomposition is gated off")
    world_size = int(os.environ.get("WORLD_SIZE", "1"))
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))
    torch.cuda.set_device(local_rank if world_size > 1 else 0)
    output_dir = args.output_dir.resolve()
    output_dir.relative_to(OUT.resolve())
    if world_size > 1:
        output_dir = output_dir / f"shard_{local_rank}"
    manifest = read_jsonl(args.manifest)[local_rank::world_size]
    events = {str(r["base_problem_id"]): r for r in read_jsonl(ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl")}
    rois = {str(r["base_problem_id"]): r for r in read_jsonl(ROOT / "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl")}
    data = {str(r["sample_index"]): r for r in load_mathverse_rows(args.dataset_root)}
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "run_config.json", {"mode": args.mode, "active_targets": active, "shard_index": local_rank, "shard_count": world_size})
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, 40_960)
    if "A5000" not in str(environment["gpu_name"]):
        raise RuntimeError(f"A5000 required, observed {environment['gpu_name']}")
    write_json(output_dir / "environment.json", environment)
    full_layers = config["cache_scope"]["layers"]
    all_heads = list(range(config["architecture_expected"]["logical_query_heads"]))
    torch.cuda.reset_peak_memory_stats()
    run_started = time.perf_counter()
    completed = 0
    for item in manifest:
        base = str(item["base_problem_id"])
        result_path = output_dir / "examples" / base / "result.json"
        if result_path.is_file():
            if not args.resume:
                raise FileExistsError(result_path)
            completed += 1
            continue
        started = time.perf_counter()
        prepared, metadata = {}, {}
        for condition, path in condition_paths(base).items():
            prepared[condition], metadata[condition] = prepare_custom_image(processor, data[str(item["example_id"])], path, device="cuda")
        target_positions = rois[base]["absolute_source_groups"]["V_target"]
        visual_positions = metadata["O"]["visual_token_indices"]
        pairs = {row["target_id"]: row for row in item["state_pairs"]}
        target_results = {}
        for target_id in active:
            spec = config["residual_boundaries"][target_id]
            current = int(pairs[target_id]["state_R"]["generated_index"])
            tpre = current - 1
            prefix, bridge, suffix_o, suffix_c = evidence_sequences(events[base], current)
            conditions = {}
            for condition in CONDITIONS:
                native, native_states = capture_native_or_suppressed_states(
                    model=model, prepared=prepared[condition], prefix_token_ids=prefix, bridge_token_ids=bridge,
                    original_suffix_ids=suffix_o, counterfactual_suffix_ids=suffix_c,
                    current_generated_index=current, tpre_generated_index=tpre,
                    cache_layers=full_layers, residual_layer=int(spec["layer"]), suppression_enabled=False,
                    suppression_layers=full_layers, source_positions=target_positions,
                    selected_heads=all_heads, seed=int(config["seed"]),
                )
                common = dict(
                    model=model, prepared=prepared[condition], prefix_token_ids=prefix, bridge_token_ids=bridge,
                    original_suffix_ids=suffix_o, counterfactual_suffix_ids=suffix_c,
                    current_generated_index=current, tpre_generated_index=tpre,
                    suppression_layers=full_layers, source_positions=target_positions,
                    selected_heads=all_heads, native_states=native_states,
                    cache_layers=spec["downstream_cache_layers"], residual_layer=int(spec["layer"]),
                    residual_boundary=str(spec["boundary"]), visual_positions=visual_positions,
                    seed=int(config["seed"]), suppression_enabled=True,
                )
                arms = {mode: score_suppressed_with_rescue(**common, cache_mode=mode) for mode in ("K", "V", "KV")}
                prior = prior_result(base, args.mode)["target_results"][target_id]["conditions"][condition]
                conditions[condition] = {
                    "native": native, "arms": arms,
                    "KV_exact_prior_J4": score_exact(arms["KV"], prior["arms"]["J4_joint"]),
                }
                del native_states
                gc.collect(); torch.cuda.empty_cache()
            target_results[target_id] = {"conditions": conditions, "residual_boundary": spec}
        write_json(result_path, {"base_problem_id": base, "example_id": str(item["example_id"]), "cohort_role": args.mode, "active_targets": active, "target_results": target_results, "runtime_seconds": time.perf_counter() - started})
        completed += 1
        print(f"[{completed}/{len(manifest)}] base={base} seconds={time.perf_counter()-started:.1f}", flush=True)
    write_json(output_dir / "run_summary.json", {"completed": completed, "expected": len(manifest), "runtime_seconds": time.perf_counter()-run_started, "peak_gpu_allocated_bytes": int(torch.cuda.max_memory_allocated()), "peak_gpu_reserved_bytes": int(torch.cuda.max_memory_reserved())})


if __name__ == "__main__":
    main()
