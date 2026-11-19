#!/usr/bin/env python3
"""Run Stage 3A fact-preference, temporal, and short-rollout scoring."""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage1.protocol import protocol_parameters, transformers_generation_kwargs
from visual_reasoning.stage3a.metrics import counterfactual_effect, js_divergence_from_logits, pre_e0_checkpoints
from visual_reasoning.stage3a.runtime import next_token_logits, prepare_custom_image, score_candidate, short_rollout


ROOT = Path(__file__).resolve().parents[2]
SEED = 1_234
ROLLOUT_TOKENS = 128


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--required-gpu-class",
        choices=("A5000", "A6000"),
        default="A5000",
        help="Expected NVIDIA GPU class; recorded in the immutable run signature.",
    )
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def prefix_hash(token_ids: list[int]) -> str:
    payload = json.dumps([int(value) for value in token_ids], separators=(",", ":")).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def condition_paths(item: dict[str, Any]) -> dict[str, Path]:
    return {name: ROOT / item["conditions"][name] for name in ("original", "counterfactual", "sham")}


def score_at_checkpoint(
    *,
    model: Any,
    prepared_by_condition: dict[str, dict[str, Any]],
    prefix: list[int],
    candidate_original_ids: list[int],
    candidate_counterfactual_ids: list[int],
) -> dict[str, Any]:
    condition_scores: dict[str, dict[str, Any]] = {}
    logits: dict[str, torch.Tensor] = {}
    for condition, prepared in prepared_by_condition.items():
        original_score = score_candidate(
            model=model,
            prepared=prepared,
            prefix_token_ids=prefix,
            candidate_token_ids=candidate_original_ids,
            seed=SEED,
        )
        counterfactual_score = score_candidate(
            model=model,
            prepared=prepared,
            prefix_token_ids=prefix,
            candidate_token_ids=candidate_counterfactual_ids,
            seed=SEED,
        )
        condition_scores[condition] = {
            "original_candidate": original_score,
            "counterfactual_candidate": counterfactual_score,
            "L_o": original_score["mean_log_probability"],
            "L_c": counterfactual_score["mean_log_probability"],
        }
        logits[condition] = next_token_logits(model=model, prepared=prepared, prefix_token_ids=prefix, seed=SEED)
    effects = counterfactual_effect(
        original=condition_scores["original"],
        counterfactual=condition_scores["counterfactual"],
        sham=condition_scores["sham"],
    )
    result = {
        "prefix_token_count": len(prefix),
        "prefix_sha256": prefix_hash(prefix),
        "condition_scores": condition_scores,
        **effects,
        "js_original_counterfactual": js_divergence_from_logits(
            logits["original"].numpy(), logits["counterfactual"].numpy()
        ),
        "js_original_sham": js_divergence_from_logits(logits["original"].numpy(), logits["sham"].numpy()),
    }
    del logits
    return result


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.relative_to((ROOT / "outputs/stage3a/scoring/shards").resolve())
    manifest = read_jsonl(args.manifest)
    if not manifest:
        raise ValueError("Scoring manifest is empty")
    signature = {
        "manifest": str(args.manifest.resolve()),
        "base_problem_ids": [str(row["base_problem_id"]) for row in manifest],
        "dataset_root": str(args.dataset_root.resolve()),
        "model_checkpoint": str(args.model_checkpoint.resolve()),
        "gpu_class": f"NVIDIA RTX {args.required_gpu_class}",
        "seed": SEED,
        "rollout_tokens": ROLLOUT_TOKENS,
        "candidate_metric": "per-token normalized raw-model log probability",
        "temporal_schedule": "prefix lengths 0, E0-64, E0-32, E0-16, E0-8, E0 (last included token is E0-1)",
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

    dataset_rows = load_mathverse_rows(args.dataset_root)
    by_id = {str(row["sample_index"]): row for row in dataset_rows}
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, 40_960)
    if args.required_gpu_class not in str(environment["gpu_name"]):
        raise RuntimeError(
            f"Stage 3A requires {args.required_gpu_class} for this recorded run, "
            f"observed {environment['gpu_name']}"
        )
    write_json(output_dir / "environment.json", environment)
    generation_kwargs = transformers_generation_kwargs(protocol_parameters("official", 40_960, SEED))
    facts: list[dict[str, Any]] = []
    temporal: list[dict[str, Any]] = []
    rollouts: list[dict[str, Any]] = []
    for index, item in enumerate(manifest):
        base = str(item["base_problem_id"])
        example = str(item["example_id"])
        example_dir = output_dir / "examples" / base
        result_path = example_dir / "result.json"
        if args.resume and result_path.is_file():
            cached = json.loads(result_path.read_text(encoding="utf-8"))
            facts.append(cached["primary"])
            temporal.extend(cached["temporal"])
            rollouts.extend(cached["rollouts"])
            print(f"[{index + 1}/{len(manifest)}] resumed base {base}", flush=True)
            continue
        ensure_directory(example_dir)
        row = by_id[example]
        prepared_by_condition: dict[str, dict[str, Any]] = {}
        input_metadata: dict[str, dict[str, Any]] = {}
        for condition, path in condition_paths(item).items():
            prepared, metadata = prepare_custom_image(processor, row, path, device="cuda")
            prepared_by_condition[condition] = prepared
            input_metadata[condition] = metadata
        prompt_ids = [metadata["prompt_token_ids"] for metadata in input_metadata.values()]
        grid_values = [metadata["image_grid_thw"] for metadata in input_metadata.values()]
        if not all(ids == prompt_ids[0] for ids in prompt_ids[1:]):
            raise RuntimeError(f"Condition prompt token IDs differ for base {base}")
        if not all(grid == grid_values[0] for grid in grid_values[1:]):
            raise RuntimeError(f"Condition image grids differ for base {base}")
        clean_prefix = [int(value) for value in item["prefix_token_ids"]]
        e0 = int(item["event"]["e0_start_token"])
        if len(clean_prefix) != e0:
            raise RuntimeError(f"Frozen prefix is not y_<E0 for base {base}")
        candidate_o_ids = processor.tokenizer.encode(str(item["candidate_original"]), add_special_tokens=False)
        candidate_c_ids = processor.tokenizer.encode(str(item["candidate_counterfactual"]), add_special_tokens=False)
        if not candidate_o_ids or not candidate_c_ids:
            raise RuntimeError(f"Empty candidate tokenization for base {base}")
        write_json(
            example_dir / "input_validation.json",
            {
                "condition_prompt_ids_exact": True,
                "condition_image_grids_exact": True,
                "prefix_is_exact_y_before_e0": True,
                "prefix_token_count": len(clean_prefix),
                "prefix_sha256": prefix_hash(clean_prefix),
                "candidate_original_ids": candidate_o_ids,
                "candidate_counterfactual_ids": candidate_c_ids,
                "condition_metadata": input_metadata,
            },
        )

        rows_for_item: list[dict[str, Any]] = []
        for prefix_length in pre_e0_checkpoints(e0):
            scored = score_at_checkpoint(
                model=model,
                prepared_by_condition=prepared_by_condition,
                prefix=clean_prefix[:prefix_length],
                candidate_original_ids=candidate_o_ids,
                candidate_counterfactual_ids=candidate_c_ids,
            )
            scored.update(
                {
                    "base_problem_id": base,
                    "example_id": example,
                    "phase": "pre_e0",
                    "relative_to_e0_tokens": int(prefix_length - e0),
                    "strictly_pre_e0": True,
                }
            )
            rows_for_item.append(scored)
            print(f"[{index + 1}/{len(manifest)}] base {base} prefix={prefix_length}/{e0}", flush=True)

        primary = next(row for row in rows_for_item if row["prefix_token_count"] == e0)
        primary = {
            **primary,
            "original_fact": item["original_fact"],
            "counterfactual_fact": item["counterfactual_fact"],
            "candidate_original": item["candidate_original"],
            "candidate_counterfactual": item["candidate_counterfactual"],
            "evidence_type": item["edit_tier"],
            "counterfactual_expected_answer": item.get("counterfactual_expected_answer"),
            "manual_validation_status": item["manual_validation"]["status"],
            "selection_used_attention": False,
            "stage2c_attention_category": item.get("stage2c_attention_category"),
        }

        post_rows: list[dict[str, Any]] = []
        full_ids = [int(value) for value in item["full_generated_token_ids"]]
        post_points = {
            "after_e1": int(item["event"]["e1_completion_token"]) + 1,
            "at_e2": item["event"].get("e2_start_token"),
        }
        for label, prefix_length_value in post_points.items():
            if prefix_length_value is None:
                continue
            prefix_length = int(prefix_length_value)
            if not (e0 < prefix_length <= len(full_ids)):
                continue
            scored = score_at_checkpoint(
                model=model,
                prepared_by_condition=prepared_by_condition,
                prefix=full_ids[:prefix_length],
                candidate_original_ids=candidate_o_ids,
                candidate_counterfactual_ids=candidate_c_ids,
            )
            scored.update(
                {
                    "base_problem_id": base,
                    "example_id": example,
                    "phase": label,
                    "relative_to_e0_tokens": int(prefix_length - e0),
                    "strictly_pre_e0": False,
                }
            )
            post_rows.append(scored)

        rollout_rows: list[dict[str, Any]] = []
        for condition, prepared in prepared_by_condition.items():
            rollout = short_rollout(
                model=model,
                processor=processor,
                prepared=prepared,
                prefix_token_ids=clean_prefix,
                generation_kwargs=generation_kwargs,
                seed=SEED,
                max_new_tokens=ROLLOUT_TOKENS,
            )
            rollout.update(
                {
                    "base_problem_id": base,
                    "example_id": example,
                    "condition": condition,
                    "prefix_sha256": prefix_hash(clean_prefix),
                    "original_fact": item["original_fact"],
                    "counterfactual_fact": item["counterfactual_fact"],
                }
            )
            rollout_rows.append(rollout)
        record = {"primary": primary, "temporal": rows_for_item + post_rows, "rollouts": rollout_rows}
        write_json(result_path, record)
        facts.append(primary)
        temporal.extend(rows_for_item + post_rows)
        rollouts.extend(rollout_rows)
        del prepared_by_condition
        gc.collect()
        torch.cuda.empty_cache()
    write_jsonl(output_dir / "fact_preference.jsonl", facts)
    write_jsonl(output_dir / "temporal_sensitivity.jsonl", temporal)
    write_jsonl(output_dir / "rollout_results.jsonl", rollouts)
    summary = {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "base_problem_count": len(facts),
        "temporal_row_count": len(temporal),
        "rollout_count": len(rollouts),
        "all_condition_prefixes_identical_by_construction": True,
        "result_files": ["fact_preference.jsonl", "temporal_sensitivity.jsonl", "rollout_results.jsonl"],
    }
    write_json(output_dir / "result.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
