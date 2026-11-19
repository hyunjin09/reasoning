#!/usr/bin/env python3
"""Run only the prospectively gated prompt type-group K/V decomposition."""

from __future__ import annotations

import argparse
import gc
import json
import os
import time
from pathlib import Path
from typing import Any

import torch

from run_phase_a import ROOT, assets, read_json, read_jsonl, write_json
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3b0.layout import build_token_groups
from visual_reasoning.stage3b0.runtime import prefill_condition, score_preference_from_cache
from visual_reasoning.stage3c8.protocol import distributed_process_info
from visual_reasoning.stage3c8.runtime import patch_prefill_cache_positions


OUT = ROOT / "outputs/stage3c8"
CONDITIONS = ("O", "C")
PATCH_PAIRS = (("C", "O", "O_to_C"), ("O", "C", "C_to_O"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    gate = read_json(OUT / "config/phase_c_kv_gate.json")
    gated_classes = [str(value) for value in gate["gated_token_classes"]]
    world_size, rank, local_device = distributed_process_info(
        os.environ, visible_device_count=torch.cuda.device_count(),
    )
    output = args.output_dir.resolve()
    output.relative_to(OUT.resolve())
    if world_size > 1:
        output = output / f"shard_{rank}"
    output.mkdir(parents=True, exist_ok=True)
    manifest = read_jsonl(args.manifest)[rank::world_size]
    if not gate["run"]:
        write_json(output / "run_summary.json", {
            "status": "gated_off",
            "rank": rank,
            "world_size": world_size,
            "gated_token_classes": [],
            "completed": 0,
        })
        return

    torch.cuda.set_device(local_device)
    config = read_json(OUT / "config/stage3c8_config.json")
    annotations = read_jsonl(args.annotations)
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
    write_json(output / "environment.json", environment)
    write_json(output / "run_config.json", {
        "manifest": str(args.manifest.resolve()),
        "rank": rank,
        "world_size": world_size,
        "gated_token_classes": gated_classes,
        "modes": ["K", "V", "KV"],
        "gate_frozen_before_scores": True,
        "base_problem_ids": [str(row["base_problem_id"]) for row in manifest],
    })
    seed = int(config["runtime"]["seed"])
    completed = 0
    started_run = time.perf_counter()
    torch.cuda.reset_peak_memory_stats()
    for item in manifest:
        base = str(item["base_problem_id"])
        result_path = output / "examples" / base / "result.json"
        if result_path.is_file():
            if not args.resume:
                raise FileExistsError(result_path)
            completed += 1
            continue
        edit, event, _ = assets(item, old_events, old_rois)
        prepared, metadata = {}, {}
        for condition in CONDITIONS:
            prepared[condition], metadata[condition] = prepare_custom_image(
                processor,
                dataset[str(item["example_id"])],
                ROOT / edit["paths"][condition],
                device="cuda",
            )
        prompt_ids = metadata["O"]["prompt_token_ids"]
        if prompt_ids != metadata["C"]["prompt_token_ids"] or metadata["O"]["image_grid_thw"] != metadata["C"]["image_grid_thw"]:
            raise RuntimeError(f"Condition layout mismatch for base {base}")
        question = str(dataset[str(item["example_id"])].get("query_cot") or dataset[str(item["example_id"])].get("question") or "")
        groups = build_token_groups(
            prompt_token_ids=prompt_ids,
            visual_token_indices=metadata["O"]["visual_token_indices"],
            question_token_ids=processor.tokenizer.encode(question, add_special_tokens=False),
        )
        eligible = {int(value) for value in groups["P_post_image"]}
        visual_positions = [int(value) for value in groups["V"]]
        prompt_rows = [
            row for row in annotations
            if str(row["base_problem_id"]) == base
            and row["stream"] in {"PROMPT_QUESTION", "SPECIAL_CONTROL"}
        ]
        prefix = [int(value) for value in event["history_before_ed_token_ids"]]
        suffix_o = [int(value) for value in event["original_divergent_suffix_ids"]]
        suffix_c = [int(value) for value in event["counterfactual_divergent_suffix_ids"]]
        caches, rope, baselines = {}, {}, {}
        for condition in CONDITIONS:
            caches[condition], rope[condition], _ = prefill_condition(model=model, prepared=prepared[condition], seed=seed)
            baselines[condition] = score_preference_from_cache(
                model=model,
                prefill_cache=caches[condition],
                rope_deltas=rope[condition],
                prompt_length=len(prompt_ids),
                visual_token_indices=visual_positions,
                prefix_token_ids=prefix,
                candidate_original_ids=suffix_o,
                candidate_counterfactual_ids=suffix_c,
                seed=seed,
                cutoff_enabled=True,
            )
        class_results: dict[str, Any] = {}
        for token_class in gated_classes:
            if not token_class.startswith("lexical:"):
                raise RuntimeError(f"Phase-C K/V gate contains a non-lexical class: {token_class}")
            lexical_class = token_class.removeprefix("lexical:")
            positions = sorted({
                int(row["absolute_sequence_position"])
                for row in prompt_rows
                if row["lexical_semantic_class"] == lexical_class
            })
            if not positions:
                continue
            if not set(positions).issubset(eligible):
                raise RuntimeError(f"Gated class positions escape eligible prompt positions for base {base}")
            modes: dict[str, Any] = {}
            for mode in ("K", "V", "KV"):
                pairs = {}
                for recipient, source, pair_name in PATCH_PAIRS:
                    patched, audit = patch_prefill_cache_positions(
                        caches[recipient], caches[source], positions=positions, mode=mode,
                        forbidden_positions=visual_positions,
                    )
                    score = score_preference_from_cache(
                        model=model,
                        prefill_cache=patched,
                        rope_deltas=rope[recipient],
                        prompt_length=len(prompt_ids),
                        visual_token_indices=visual_positions,
                        prefix_token_ids=prefix,
                        candidate_original_ids=suffix_o,
                        candidate_counterfactual_ids=suffix_c,
                        seed=seed,
                        cutoff_enabled=True,
                    )
                    pairs[pair_name] = {
                        "recipient": recipient,
                        "source": source,
                        "recipient_D": float(baselines[recipient]["D"]),
                        "source_D": float(baselines[source]["D"]),
                        "patched_score": score,
                        "D_shift": float(score["D"] - baselines[recipient]["D"]),
                        "patch_audit": audit,
                    }
                modes[mode] = pairs
            class_results[token_class] = {"positions": positions, "modes": modes}
        write_json(result_path, {
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "cohort_role": "fresh",
            "gated_token_classes": gated_classes,
            "class_results": class_results,
            "selection_used_attention": False,
            "gate_frozen_before_scores": True,
        })
        completed += 1
        del caches
        gc.collect()
        torch.cuda.empty_cache()
        print(f"[{completed}/{len(manifest)}] base={base} classes={len(class_results)}", flush=True)
    write_json(output / "run_summary.json", {
        "status": "complete",
        "completed": completed,
        "expected": len(manifest),
        "rank": rank,
        "world_size": world_size,
        "gated_token_classes": gated_classes,
        "runtime_seconds": time.perf_counter() - started_run,
        "peak_gpu_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        "peak_gpu_reserved_bytes": int(torch.cuda.max_memory_reserved()),
    })


if __name__ == "__main__":
    main()
