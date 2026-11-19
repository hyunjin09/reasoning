#!/usr/bin/env python3
"""Run the frozen bidirectional prompt/question-token carrier atlas."""

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
    parser.add_argument("--spans", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=("validation", "historical", "fresh"), required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--repeat-first", action="store_true")
    return parser.parse_args()


def exact(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return bool(
        float(left["D"]) == float(right["D"])
        and left["original_candidate"]["token_log_probabilities"] == right["original_candidate"]["token_log_probabilities"]
        and left["counterfactual_candidate"]["token_log_probabilities"] == right["counterfactual_candidate"]["token_log_probabilities"]
    )


def main() -> None:
    args = parse_args()
    config = read_json(OUT / "config/stage3c8_config.json")
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
    seed = int(config["runtime"]["seed"])
    write_json(output / "environment.json", environment)
    write_json(output / "run_config.json", {
        "mode": args.mode,
        "manifest": str(args.manifest.resolve()),
        "rank": rank,
        "world_size": world_size,
        "bidirectional": True,
        "cache_mode": "KV",
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
        q_positions = [int(value) for value in groups["Q"]]
        eligible_positions = [int(value) for value in groups["P_post_image"]]
        visual_positions = [int(value) for value in groups["V"]]
        prompt_rows = [
            row for row in annotations
            if str(row["base_problem_id"]) == base
            and row["stream"] in {"PROMPT_QUESTION", "SPECIAL_CONTROL"}
        ]
        if {int(row["absolute_sequence_position"]) for row in prompt_rows} != set(eligible_positions):
            raise RuntimeError(f"Frozen prompt annotations do not match eligible positions for base {base}")
        spans = [
            row for row in lexical_spans
            if str(row["base_problem_id"]) == base and row["stream"] in {"PROMPT_QUESTION", "SPECIAL_CONTROL"}
        ]
        prefix = [int(value) for value in event["history_before_ed_token_ids"]]
        suffix_o = [int(value) for value in event["original_divergent_suffix_ids"]]
        suffix_c = [int(value) for value in event["counterfactual_divergent_suffix_ids"]]
        caches, rope, prefill_audits = {}, {}, {}
        baselines = {}
        for condition in CONDITIONS:
            caches[condition], rope[condition], prefill_audits[condition] = prefill_condition(
                model=model, prepared=prepared[condition], seed=seed
            )
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

        def score_patch(recipient: str, source: str, positions: list[int], mode: str = "KV") -> dict[str, Any]:
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
            return {
                "recipient": recipient,
                "source": source,
                "recipient_D": float(baselines[recipient]["D"]),
                "source_D": float(baselines[source]["D"]),
                "patched_score": score,
                "D_shift": float(score["D"] - baselines[recipient]["D"]),
                "patch_audit": audit,
            }

        full_q = {
            pair_name: score_patch(recipient, source, q_positions)
            for recipient, source, pair_name in PATCH_PAIRS
        }
        per_position = {
            str(position): {
                pair_name: score_patch(recipient, source, [position])
                for recipient, source, pair_name in PATCH_PAIRS
            }
            for position in eligible_positions
        }
        span_rescue = {
            str(row["span_id"]): {
                pair_name: score_patch(
                    recipient,
                    source,
                    [int(value) for value in row["absolute_positions"]],
                )
                for recipient, source, pair_name in PATCH_PAIRS
            }
            for row in spans
        }
        type_groups = {}
        for token_type in sorted({str(row["lexical_semantic_class"]) for row in prompt_rows}):
            positions = [
                int(row["absolute_sequence_position"])
                for row in prompt_rows
                if row["lexical_semantic_class"] == token_type
            ]
            type_groups[f"lexical:{token_type}"] = {
                pair_name: score_patch(recipient, source, positions)
                for recipient, source, pair_name in PATCH_PAIRS
            }
        for alignment in sorted({str(row["visual_alignment"]) for row in prompt_rows}):
            positions = [
                int(row["absolute_sequence_position"])
                for row in prompt_rows
                if row["visual_alignment"] == alignment
            ]
            type_groups[f"visual_alignment:{alignment}"] = {
                pair_name: score_patch(recipient, source, positions)
                for recipient, source, pair_name in PATCH_PAIRS
            }
        controls = None
        repeat = None
        if args.mode == "validation":
            controls = {}
            for condition in CONDITIONS:
                row = score_patch(condition, condition, q_positions)
                controls[condition] = {**row, "exact": exact(row["patched_score"], baselines[condition])}
            if args.repeat_first and item_index == 0:
                repeated = score_patch("C", "O", q_positions)
                repeat = {"arm": "full_q:O_to_C", "exact": exact(repeated["patched_score"], full_q["O_to_C"]["patched_score"])}
        result = {
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "cohort_role": args.mode,
            "prompt_token_count": len(prompt_ids),
            "question_positions": q_positions,
            "eligible_nonvisual_prompt_positions": eligible_positions,
            "visual_positions": visual_positions,
            "prefill_audits": prefill_audits,
            "baselines": baselines,
            "full_q": full_q,
            "per_prompt_position": per_position,
            "prompt_spans": spans,
            "prompt_span_rescue": span_rescue,
            "prompt_type_group_rescue": type_groups,
            "self_controls": controls,
            "repeat": repeat,
            "selection_used_attention": False,
            "runtime_seconds": time.perf_counter() - started,
        }
        write_json(result_path, result)
        completed += 1
        print(f"[{completed}/{len(manifest)}] base={base} q={len(q_positions)} seconds={result['runtime_seconds']:.1f}", flush=True)
        del caches
        gc.collect()
        torch.cuda.empty_cache()
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
