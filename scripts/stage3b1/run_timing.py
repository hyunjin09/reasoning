#!/usr/bin/env python3
"""Run frozen Stage 3B.1 full-sequence visual-sufficiency timing scores."""

from __future__ import annotations

import argparse
import copy
import gc
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage0.modeling import attention_modules, load_runtime, runtime_environment
from visual_reasoning.stage3a.metrics import counterfactual_effect
from visual_reasoning.stage3a.runtime import prepare_custom_image, score_candidate
from visual_reasoning.stage3b0.metrics import retention_ratio
from visual_reasoning.stage3b1.intervention import TimedVisualCutoff, valid_cutoff_audit


ROOT = Path(__file__).resolve().parents[2]
SEED = 1_234
CONDITIONS = ("original", "counterfactual", "sham")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--stage3a-facts", type=Path, required=True)
    parser.add_argument("--stage3b0-cutoff", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=("smoke", "cohort"), required=True)
    parser.add_argument("--required-gpu-class", choices=("A5000", "A6000"), default="A6000")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def token_hash(values: list[int]) -> str:
    payload = json.dumps([int(value) for value in values], separators=(",", ":")).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def scores_exact(observed: dict[str, Any], expected: dict[str, Any]) -> bool:
    for candidate in ("original_candidate", "counterfactual_candidate"):
        if observed[candidate]["token_log_probabilities"] != expected[candidate]["token_log_probabilities"]:
            return False
    return observed["L_o"] == expected["L_o"] and observed["L_c"] == expected["L_c"]


def score_preference(
    *,
    model: Any,
    prepared: dict[str, Any],
    prefix: list[int],
    candidate_original: list[int],
    candidate_counterfactual: list[int],
    visual_indices: list[int],
    cutoff_generated_index: int | None,
    hook_enabled: bool = True,
) -> dict[str, Any]:
    hook = None
    if cutoff_generated_index is not None:
        hook = TimedVisualCutoff(
            prompt_length=int(prepared["input_ids"].shape[1]),
            cutoff_generated_index=int(cutoff_generated_index),
            visual_key_indices=visual_indices,
            num_attention_heads=int(model.config.text_config.num_attention_heads),
            enabled=hook_enabled,
        ).attach(attention_modules(model))
    try:
        original = score_candidate(
            model=model,
            prepared=prepared,
            prefix_token_ids=prefix,
            candidate_token_ids=candidate_original,
            seed=SEED,
        )
        original_audit = copy.deepcopy(hook.audit) if hook is not None else None
        if hook is not None:
            hook.reset_audit()
        counterfactual = score_candidate(
            model=model,
            prepared=prepared,
            prefix_token_ids=prefix,
            candidate_token_ids=candidate_counterfactual,
            seed=SEED,
        )
        counterfactual_audit = copy.deepcopy(hook.audit) if hook is not None else None
    finally:
        if hook is not None:
            hook.close()
    return {
        "original_candidate": original,
        "counterfactual_candidate": counterfactual,
        "L_o": float(original["mean_log_probability"]),
        "L_c": float(counterfactual["mean_log_probability"]),
        "D": float(original["mean_log_probability"] - counterfactual["mean_log_probability"]),
        "hook_audits": {"original_candidate": original_audit, "counterfactual_candidate": counterfactual_audit},
    }


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.relative_to((ROOT / "outputs/stage3b1/raw").resolve())
    manifest = read_jsonl(args.manifest)
    schedules = {str(row["base_problem_id"]): row for row in read_jsonl(args.schedule)}
    stage3a = {str(row["base_problem_id"]): row for row in read_jsonl(args.stage3a_facts)}
    stage3b0 = {str(row["base_problem_id"]): row for row in read_jsonl(args.stage3b0_cutoff)}
    bases = [str(row["base_problem_id"]) for row in manifest]
    signature = {
        "mode": args.mode,
        "manifest": str(args.manifest.resolve()),
        "schedule": str(args.schedule.resolve()),
        "base_problem_ids": bases,
        "model_checkpoint": str(args.model_checkpoint.resolve()),
        "dataset_root": str(args.dataset_root.resolve()),
        "seed": SEED,
        "scoring_path": "full-sequence eager attention",
        "cutoff": "all generated-query->all visual-key edges at/after each frozen generated index",
        "required_gpu_class": args.required_gpu_class,
    }
    config_path = output_dir / "config.json"
    if output_dir.exists() and any(output_dir.iterdir()):
        if not args.resume or not config_path.is_file():
            raise FileExistsError(f"Non-empty output requires --resume: {output_dir}")
        if json.loads(config_path.read_text(encoding="utf-8"))["run_signature"] != signature:
            raise RuntimeError("Resume signature mismatch")
    else:
        ensure_directory(output_dir)
        write_json(config_path, {"created_at": datetime.now(timezone.utc).isoformat(), "run_signature": signature})
        write_jsonl(output_dir / "manifest.jsonl", manifest)

    data_rows = load_mathverse_rows(args.dataset_root)
    by_example = {str(row["sample_index"]): row for row in data_rows}
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, 40_960)
    if args.required_gpu_class not in str(environment["gpu_name"]):
        raise RuntimeError(f"Expected {args.required_gpu_class}, observed {environment['gpu_name']}")
    write_json(output_dir / "environment.json", environment)
    layer_count = int(model.config.text_config.num_hidden_layers)
    logical_heads = int(model.config.text_config.num_attention_heads)
    all_results: list[dict[str, Any]] = []
    smoke_rows: list[dict[str, Any]] = []
    peak_gpu_bytes = 0

    for item_index, item in enumerate(manifest):
        base = str(item["base_problem_id"])
        example = str(item["example_id"])
        result_path = output_dir / "examples" / base / "result.json"
        if args.resume and result_path.is_file():
            result = json.loads(result_path.read_text(encoding="utf-8"))
            all_results.append(result)
            if result.get("smoke") is not None:
                smoke_rows.append(result["smoke"])
            print(f"[{item_index + 1}/{len(manifest)}] resumed base {base}", flush=True)
            continue
        ensure_directory(result_path.parent)
        if base not in schedules or base not in stage3a or base not in stage3b0:
            raise RuntimeError(f"Missing frozen reference for base {base}")
        schedule = schedules[base]
        if schedule["prefix_sha256"] != item["prefix_sha256"]:
            raise RuntimeError(f"Schedule/prefix hash mismatch for base {base}")
        prefix = [int(value) for value in item["prefix_token_ids"]]
        e0 = int(item["event"]["e0_start_token"])
        if len(prefix) != e0 or token_hash(prefix) != item["prefix_sha256"]:
            raise RuntimeError(f"Strict Stage 3A prefix mismatch for base {base}")

        source_row = by_example[example]
        prepared: dict[str, dict[str, Any]] = {}
        metadata: dict[str, dict[str, Any]] = {}
        for condition in CONDITIONS:
            prepared[condition], metadata[condition] = prepare_custom_image(
                processor, source_row, ROOT / item["conditions"][condition], device="cuda"
            )
        prompt_ids = [metadata[name]["prompt_token_ids"] for name in CONDITIONS]
        grids = [metadata[name]["image_grid_thw"] for name in CONDITIONS]
        visual_sets = [metadata[name]["visual_token_indices"] for name in CONDITIONS]
        if not all(values == prompt_ids[0] for values in prompt_ids[1:]):
            raise RuntimeError(f"Condition prompt token mismatch for base {base}")
        if not all(values == grids[0] for values in grids[1:]) or not all(
            values == visual_sets[0] for values in visual_sets[1:]
        ):
            raise RuntimeError(f"Condition visual layout mismatch for base {base}")
        prompt_length = len(prompt_ids[0])
        visual_indices = [int(value) for value in visual_sets[0]]
        candidate_original = processor.tokenizer.encode(item["candidate_original"], add_special_tokens=False)
        candidate_counterfactual = processor.tokenizer.encode(item["candidate_counterfactual"], add_special_tokens=False)
        expected3a = stage3a[base]
        expected3b0 = stage3b0[base]
        if (
            candidate_original != expected3a["condition_scores"]["original"]["original_candidate"]["candidate_token_ids"]
            or candidate_counterfactual
            != expected3a["condition_scores"]["original"]["counterfactual_candidate"]["candidate_token_ids"]
        ):
            raise RuntimeError(f"Candidate tokenization changed for base {base}")

        no_cutoff: dict[str, Any] = {}
        for condition in CONDITIONS:
            no_cutoff[condition] = score_preference(
                model=model,
                prepared=prepared[condition],
                prefix=prefix,
                candidate_original=candidate_original,
                candidate_counterfactual=candidate_counterfactual,
                visual_indices=visual_indices,
                cutoff_generated_index=None,
            )
            peak_gpu_bytes = max(peak_gpu_bytes, int(torch.cuda.max_memory_allocated()))
        no_cutoff_effect = counterfactual_effect(
            original=no_cutoff["original"], counterfactual=no_cutoff["counterfactual"], sham=no_cutoff["sham"]
        )
        no_cutoff_exact = all(scores_exact(no_cutoff[name], expected3a["condition_scores"][name]) for name in CONDITIONS)

        timing_rows = []
        for checkpoint in schedule["checkpoints"]:
            cutoff_index = int(checkpoint["cutoff_generated_index"])
            condition_scores: dict[str, Any] = {}
            for condition in CONDITIONS:
                condition_scores[condition] = score_preference(
                    model=model,
                    prepared=prepared[condition],
                    prefix=prefix,
                    candidate_original=candidate_original,
                    candidate_counterfactual=candidate_counterfactual,
                    visual_indices=visual_indices,
                    cutoff_generated_index=cutoff_index,
                )
                peak_gpu_bytes = max(peak_gpu_bytes, int(torch.cuda.max_memory_allocated()))
            effects = counterfactual_effect(
                original=condition_scores["original"],
                counterfactual=condition_scores["counterfactual"],
                sham=condition_scores["sham"],
            )
            audits_valid = all(
                valid_cutoff_audit(
                    condition_scores[condition]["hook_audits"][candidate],
                    prompt_length=prompt_length,
                    prefix_token_count=len(prefix),
                    candidate_token_count=len(condition_scores[condition][candidate]["candidate_token_ids"]),
                    cutoff_generated_index=cutoff_index,
                    visual_indices=visual_indices,
                    layer_count=layer_count,
                    logical_heads=logical_heads,
                )
                for condition in CONDITIONS
                for candidate in ("original_candidate", "counterfactual_candidate")
            )
            timing_rows.append(
                {
                    **checkpoint,
                    "condition_scores": condition_scores,
                    **effects,
                    "retention_ratio_raw": retention_ratio(ce_cut=effects["CE"], ce_full=expected3a["CE"]),
                    "retention_ratio_controlled_raw": retention_ratio(
                        ce_cut=effects["CE_controlled"], ce_full=expected3a["CE_controlled"]
                    ),
                    "all_cutoff_audits_valid": audits_valid,
                }
            )
        start_row = next(row for row in timing_rows if row["cutoff_generated_index"] == 0)
        generation_start_exact = all(
            scores_exact(start_row["condition_scores"][name], expected3b0["condition_scores"][name])
            for name in CONDITIONS
        )

        smoke = None
        if args.mode == "smoke":
            no_op: dict[str, Any] = {}
            for condition in CONDITIONS:
                no_op[condition] = score_preference(
                    model=model,
                    prepared=prepared[condition],
                    prefix=prefix,
                    candidate_original=candidate_original,
                    candidate_counterfactual=candidate_counterfactual,
                    visual_indices=visual_indices,
                    cutoff_generated_index=0,
                    hook_enabled=False,
                )
                peak_gpu_bytes = max(peak_gpu_bytes, int(torch.cuda.max_memory_allocated()))
            duplicate_label_count = sum(max(0, len(row["labels"]) - 1) for row in timing_rows)
            smoke = {
                "base_problem_id": base,
                "e0_start_token": e0,
                "no_cutoff_stage3a_exact": no_cutoff_exact,
                "generation_start_stage3b0_exact": generation_start_exact,
                "hooked_noop_exact": all(scores_exact(no_op[name], no_cutoff[name]) for name in CONDITIONS),
                "all_timed_cutoff_audits_valid": all(row["all_cutoff_audits_valid"] for row in timing_rows),
                "duplicate_checkpoint_labels_share_single_score": duplicate_label_count > 0,
                "duplicate_label_count": duplicate_label_count,
                "checkpoint_count": len(timing_rows),
                "all_finite": all(
                    score[candidate]["finite"]
                    for row in timing_rows
                    for score in row["condition_scores"].values()
                    for candidate in ("original_candidate", "counterfactual_candidate")
                ),
                "scoring_path_fixed": "full-sequence eager attention",
            }
            smoke_rows.append(smoke)

        result = {
            "base_problem_id": base,
            "example_id": example,
            "evidence_type": item["edit_tier"],
            "prefix_sha256": item["prefix_sha256"],
            "e0_start_token": e0,
            "prompt_token_count": prompt_length,
            "visual_token_count": len(visual_indices),
            "visual_token_indices": visual_indices,
            "condition_layout_exact": True,
            "selection_used_attention": False,
            "no_cutoff_condition_scores": no_cutoff,
            "no_cutoff_effect": no_cutoff_effect,
            "no_cutoff_stage3a_exact": no_cutoff_exact,
            "generation_start_stage3b0_exact": generation_start_exact,
            "CE_full": float(expected3a["CE"]),
            "CE_full_controlled": float(expected3a["CE_controlled"]),
            "prefill_retention_stage3b0": float(expected3b0["retention_ratio_raw"]),
            "timing": timing_rows,
            "smoke": smoke,
        }
        write_json(result_path, result)
        all_results.append(result)
        print(f"[{item_index + 1}/{len(manifest)}] completed base {base} ({len(timing_rows)} checkpoints)", flush=True)
        del prepared, no_cutoff, timing_rows
        gc.collect()
        torch.cuda.empty_cache()

    write_jsonl(output_dir / "timing_results.jsonl", all_results)
    if smoke_rows:
        write_jsonl(output_dir / "smoke_results.jsonl", smoke_rows)
    write_json(
        output_dir / "result.json",
        {
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "mode": args.mode,
            "base_problem_count": len(all_results),
            "problem_checkpoint_count": sum(len(row["timing"]) for row in all_results),
            "smoke_row_count": len(smoke_rows),
            "peak_gpu_allocated_bytes": peak_gpu_bytes,
            "all_no_cutoff_stage3a_exact": all(row["no_cutoff_stage3a_exact"] for row in all_results),
            "all_generation_start_stage3b0_exact": all(
                row["generation_start_stage3b0_exact"] for row in all_results
            ),
            "all_cutoff_audits_valid": all(
                timing["all_cutoff_audits_valid"] for row in all_results for timing in row["timing"]
            ),
        },
    )


if __name__ == "__main__":
    main()
