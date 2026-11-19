#!/usr/bin/env python3
"""Run Stage 3B.0 generation-start cutoff and broad prompt-cache patching."""

from __future__ import annotations

import argparse
import copy
import gc
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage0.modeling import attention_modules, load_runtime, runtime_environment
from visual_reasoning.stage1.protocol import protocol_parameters, transformers_generation_kwargs
from visual_reasoning.stage3a.metrics import counterfactual_effect
from visual_reasoning.stage3a.runtime import prepare_custom_image, score_candidate, short_rollout
from visual_reasoning.stage3b0.cache import patch_cache_positions, validate_cache_layout
from visual_reasoning.stage3b0.intervention import GenerationStartVisualCutoff
from visual_reasoning.stage3b0.layout import build_token_groups
from visual_reasoning.stage3b0.metrics import directional_recovery, retention_ratio
from visual_reasoning.stage3b0.runtime import prefill_condition, score_preference_from_cache


ROOT = Path(__file__).resolve().parents[2]
SEED = 1_234
ROLLOUT_TOKENS = 128
GROUPS = ("P_post_image", "Q", "T", "Q_plus_T")
PATCH_PAIRS = (
    ("counterfactual", "original", "cross_original_to_counterfactual"),
    ("original", "counterfactual", "cross_counterfactual_to_original"),
    ("original", "original", "self_original"),
    ("counterfactual", "counterfactual", "self_counterfactual"),
    ("original", "sham", "sham_to_original"),
    ("sham", "original", "original_to_sham"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--stage3a-facts", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--mode", choices=("smoke", "cohort"), required=True)
    parser.add_argument("--required-gpu-class", choices=("A5000", "A6000"), default="A5000")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def prefix_hash(values: list[int]) -> str:
    payload = json.dumps([int(value) for value in values], separators=(",", ":")).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def score_full_preference(
    *,
    model: Any,
    prepared: dict[str, Any],
    prefix: list[int],
    candidate_o: list[int],
    candidate_c: list[int],
    visual: list[int],
    cutoff_enabled: bool | None,
) -> dict[str, Any]:
    hook = None
    if cutoff_enabled is not None:
        hook = GenerationStartVisualCutoff(
            prompt_length=int(prepared["input_ids"].shape[1]),
            visual_key_indices=visual,
            num_attention_heads=int(model.config.text_config.num_attention_heads),
            enabled=cutoff_enabled,
        ).attach(attention_modules(model))
    try:
        original = score_candidate(
            model=model,
            prepared=prepared,
            prefix_token_ids=prefix,
            candidate_token_ids=candidate_o,
            seed=SEED,
        )
        original_audit = copy.deepcopy(hook.audit) if hook is not None else None
        if hook is not None:
            hook.reset_audit()
        counterfactual = score_candidate(
            model=model,
            prepared=prepared,
            prefix_token_ids=prefix,
            candidate_token_ids=candidate_c,
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


def values_exact(observed: dict[str, Any], expected: dict[str, Any]) -> bool:
    for candidate in ("original_candidate", "counterfactual_candidate"):
        if observed[candidate]["token_log_probabilities"] != expected[candidate]["token_log_probabilities"]:
            return False
    return observed["L_o"] == expected["L_o"] and observed["L_c"] == expected["L_c"]


def rollout_with_cutoff(
    *, model: Any, processor: Any, prepared: dict[str, Any], prefix: list[int], visual: list[int], generation_kwargs: dict[str, Any]
) -> dict[str, Any]:
    hook = GenerationStartVisualCutoff(
        prompt_length=int(prepared["input_ids"].shape[1]),
        visual_key_indices=visual,
        num_attention_heads=int(model.config.text_config.num_attention_heads),
        enabled=True,
    ).attach(attention_modules(model))
    try:
        result = short_rollout(
            model=model,
            processor=processor,
            prepared=prepared,
            prefix_token_ids=prefix,
            generation_kwargs=generation_kwargs,
            seed=SEED,
            max_new_tokens=ROLLOUT_TOKENS,
        )
        result["cutoff_audit"] = copy.deepcopy(hook.audit)
    finally:
        hook.close()
    return result


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.relative_to((ROOT / "outputs/stage3b0/raw").resolve())
    manifest = read_jsonl(args.manifest)
    stage3a_rows = {str(row["base_problem_id"]): row for row in read_jsonl(args.stage3a_facts)}
    signature = {
        "mode": args.mode,
        "manifest": str(args.manifest.resolve()),
        "base_problem_ids": [str(row["base_problem_id"]) for row in manifest],
        "model_checkpoint": str(args.model_checkpoint.resolve()),
        "dataset_root": str(args.dataset_root.resolve()),
        "seed": SEED,
        "groups": list(GROUPS),
        "patch_pairs": [list(values) for values in PATCH_PAIRS],
        "cutoff": "all generated-token queries -> all visual prompt keys, all layers/heads",
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

    rows = load_mathverse_rows(args.dataset_root)
    by_id = {str(row["sample_index"]): row for row in rows}
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, 40_960)
    if args.required_gpu_class not in str(environment["gpu_name"]):
        raise RuntimeError(f"Expected {args.required_gpu_class}, observed {environment['gpu_name']}")
    write_json(output_dir / "environment.json", environment)
    generation_kwargs = transformers_generation_kwargs(protocol_parameters("official", 40_960, SEED))
    cutoff_rows: list[dict[str, Any]] = []
    patch_rows: list[dict[str, Any]] = []
    rollout_rows: list[dict[str, Any]] = []
    smoke_rows: list[dict[str, Any]] = []

    for item_index, item in enumerate(manifest):
        base = str(item["base_problem_id"])
        example = str(item["example_id"])
        example_dir = output_dir / "examples" / base
        result_path = example_dir / "result.json"
        if args.resume and result_path.is_file():
            result = json.loads(result_path.read_text(encoding="utf-8"))
            cutoff_rows.append(result["cutoff"])
            patch_rows.extend(result["patches"])
            rollout_rows.extend(result["rollouts"])
            if result.get("smoke") is not None:
                smoke_rows.append(result["smoke"])
            print(f"[{item_index + 1}/{len(manifest)}] resumed base {base}", flush=True)
            continue
        ensure_directory(example_dir)
        row = by_id[example]
        prepared: dict[str, dict[str, Any]] = {}
        metadata: dict[str, dict[str, Any]] = {}
        for condition in ("original", "counterfactual", "sham"):
            batch, meta = prepare_custom_image(
                processor, row, ROOT / item["conditions"][condition], device="cuda"
            )
            prepared[condition] = batch
            metadata[condition] = meta
        prompt_ids = [metadata[name]["prompt_token_ids"] for name in prepared]
        grids = [metadata[name]["image_grid_thw"] for name in prepared]
        if not all(values == prompt_ids[0] for values in prompt_ids[1:]) or not all(
            values == grids[0] for values in grids[1:]
        ):
            raise RuntimeError(f"Condition prompt/grid mismatch for base {base}")
        question = str(row.get("query_cot") or row.get("question") or "")
        question_ids = processor.tokenizer.encode(question, add_special_tokens=False)
        groups = build_token_groups(
            prompt_token_ids=prompt_ids[0],
            visual_token_indices=metadata["original"]["visual_token_indices"],
            question_token_ids=question_ids,
        )
        if any(not groups[name] for name in GROUPS):
            raise RuntimeError(f"Frozen token group is empty for base {base}")
        prefix = [int(value) for value in item["prefix_token_ids"]]
        if len(prefix) != int(item["event"]["e0_start_token"]) or prefix_hash(prefix) != item["prefix_sha256"]:
            raise RuntimeError(f"Strict Stage 3A prefix mismatch for base {base}")
        candidate_o = processor.tokenizer.encode(item["candidate_original"], add_special_tokens=False)
        candidate_c = processor.tokenizer.encode(item["candidate_counterfactual"], add_special_tokens=False)
        stage3a = stage3a_rows[base]
        if stage3a["prefix_sha256"] != item["prefix_sha256"]:
            raise RuntimeError(f"Stage 3A score/prefix mismatch for base {base}")

        caches: dict[str, Any] = {}
        rope: dict[str, torch.Tensor] = {}
        prefill_audits: dict[str, Any] = {}
        for condition in prepared:
            caches[condition], rope[condition], prefill_audits[condition] = prefill_condition(
                model=model, prepared=prepared[condition], seed=SEED
            )
        cache_diagnostic = validate_cache_layout(
            caches["original"],
            expected_layers=int(model.config.text_config.num_hidden_layers),
            expected_kv_heads=int(model.config.text_config.num_key_value_heads),
            expected_sequence_length=len(prompt_ids[0]),
            expected_head_dim=int(model.config.text_config.head_dim),
        )
        for condition in ("counterfactual", "sham"):
            validate_cache_layout(
                caches[condition],
                expected_layers=int(model.config.text_config.num_hidden_layers),
                expected_kv_heads=int(model.config.text_config.num_key_value_heads),
                expected_sequence_length=len(prompt_ids[0]),
                expected_head_dim=int(model.config.text_config.head_dim),
            )

        cached_cutoff_scores: dict[str, Any] = {}
        for condition in prepared:
            cached_cutoff_scores[condition] = score_preference_from_cache(
                model=model,
                prefill_cache=caches[condition],
                rope_deltas=rope[condition],
                prompt_length=len(prompt_ids[0]),
                visual_token_indices=groups["V"],
                prefix_token_ids=prefix,
                candidate_original_ids=candidate_o,
                candidate_counterfactual_ids=candidate_c,
                seed=SEED,
                cutoff_enabled=True,
            )
        # Primary cutoff effects retain Stage 3A's full-sequence computation.
        # Cached eager attention is deterministic but uses a slightly different
        # BF16 kernel path; it is the matched baseline only for cache patches.
        cutoff_scores: dict[str, Any] = {}
        for condition in prepared:
            cutoff_scores[condition] = score_full_preference(
                model=model,
                prepared=prepared[condition],
                prefix=prefix,
                candidate_o=candidate_o,
                candidate_c=candidate_c,
                visual=groups["V"],
                cutoff_enabled=True,
            )
        cutoff_effects = counterfactual_effect(
            original=cutoff_scores["original"],
            counterfactual=cutoff_scores["counterfactual"],
            sham=cutoff_scores["sham"],
        )
        cutoff_row = {
            "base_problem_id": base,
            "example_id": example,
            "evidence_type": item["edit_tier"],
            "prefix_sha256": item["prefix_sha256"],
            "prefix_token_count": len(prefix),
            "prompt_token_count": len(prompt_ids[0]),
            "condition_scores": cutoff_scores,
            "cached_condition_scores_for_patching": cached_cutoff_scores,
            **{f"{name}_cut": value for name, value in cutoff_effects.items()},
            "CE_full": float(stage3a["CE"]),
            "CE_full_controlled": float(stage3a["CE_controlled"]),
            "retention_ratio_raw": retention_ratio(ce_cut=cutoff_effects["CE"], ce_full=stage3a["CE"]),
            "retention_ratio_controlled_raw": retention_ratio(
                ce_cut=cutoff_effects["CE_controlled"], ce_full=stage3a["CE_controlled"]
            ),
            "selection_used_attention": False,
        }

        item_patches: list[dict[str, Any]] = []
        for group_name in GROUPS:
            for recipient, source, patch_type in PATCH_PAIRS:
                patched_cache, patch_audit = patch_cache_positions(caches[recipient], caches[source], groups[group_name])
                score = score_preference_from_cache(
                    model=model,
                    prefill_cache=patched_cache,
                    rope_deltas=rope[recipient],
                    prompt_length=len(prompt_ids[0]),
                    visual_token_indices=groups["V"],
                    prefix_token_ids=prefix,
                    candidate_original_ids=candidate_o,
                    candidate_counterfactual_ids=candidate_c,
                    seed=SEED,
                    cutoff_enabled=True,
                )
                baseline_recipient = float(cached_cutoff_scores[recipient]["D"])
                baseline_source = float(cached_cutoff_scores[source]["D"])
                shift = float(score["D"] - baseline_recipient)
                item_patches.append(
                    {
                        "base_problem_id": base,
                        "example_id": example,
                        "evidence_type": item["edit_tier"],
                        "group": group_name,
                        "patch_type": patch_type,
                        "recipient": recipient,
                        "source": source,
                        "recipient_D_no_patch": baseline_recipient,
                        "source_D_no_patch": baseline_source,
                        "patched_score": score,
                        "patched_D": float(score["D"]),
                        "D_shift": shift,
                        "directional_recovery_raw": directional_recovery(
                            recipient_preference=baseline_recipient,
                            source_preference=baseline_source,
                            patched_preference=float(score["D"]),
                        ),
                        "source_consistent_shift": bool(
                            (baseline_source - baseline_recipient) * shift > 0.0
                        ),
                        "patch_audit": patch_audit,
                        "selection_used_attention": False,
                    }
                )

        item_rollouts: list[dict[str, Any]] = []
        for condition in prepared:
            rollout = rollout_with_cutoff(
                model=model,
                processor=processor,
                prepared=prepared[condition],
                prefix=prefix,
                visual=groups["V"],
                generation_kwargs=generation_kwargs,
            )
            rollout.update(
                {
                    "base_problem_id": base,
                    "example_id": example,
                    "condition": condition,
                    "prefix_sha256": item["prefix_sha256"],
                    "original_fact": item["original_fact"],
                    "counterfactual_fact": item["counterfactual_fact"],
                }
            )
            item_rollouts.append(rollout)

        smoke = None
        if args.mode == "smoke":
            full_no_hook: dict[str, Any] = {}
            hooked_noop: dict[str, Any] = {}
            for condition in prepared:
                full_no_hook[condition] = score_full_preference(
                    model=model, prepared=prepared[condition], prefix=prefix, candidate_o=candidate_o,
                    candidate_c=candidate_c, visual=groups["V"], cutoff_enabled=None
                )
                hooked_noop[condition] = score_full_preference(
                    model=model, prepared=prepared[condition], prefix=prefix, candidate_o=candidate_o,
                    candidate_c=candidate_c, visual=groups["V"], cutoff_enabled=False
                )
            determinism = score_preference_from_cache(
                model=model,
                prefill_cache=caches["original"],
                rope_deltas=rope["original"],
                prompt_length=len(prompt_ids[0]),
                visual_token_indices=groups["V"],
                prefix_token_ids=prefix,
                candidate_original_ids=candidate_o,
                candidate_counterfactual_ids=candidate_c,
                seed=SEED,
                cutoff_enabled=True,
            )
            stage3a_exact = all(
                values_exact(full_no_hook[name], stage3a["condition_scores"][name]) for name in prepared
            )
            noop_exact = all(values_exact(hooked_noop[name], full_no_hook[name]) for name in prepared)
            cached_cutoff_max_abs = max(
                abs(cached_cutoff_scores[name][field] - cutoff_scores[name][field])
                for name in prepared
                for field in ("L_o", "L_c", "D")
            )
            self_patch_max_abs = max(
                abs(row_value["D_shift"])
                for row_value in item_patches
                if row_value["patch_type"].startswith("self_")
            )
            cutoff_audits = [
                cutoff_scores[name]["hook_audits"][candidate]
                for name in prepared
                for candidate in ("original_candidate", "counterfactual_candidate")
            ]
            cutoff_valid = all(
                not audit["prefill_modified"]
                and sorted(set(audit["layers_modified"])) == list(range(int(model.config.text_config.num_hidden_layers)))
                and min(audit["absolute_query_indices"]) == len(prompt_ids[0])
                for audit in cutoff_audits
            )
            smoke = {
                "base_problem_id": base,
                "stage3a_no_hook_exact": stage3a_exact,
                "hooked_noop_exact": noop_exact,
                "cutoff_all_layers_and_generated_start_only": cutoff_valid,
                "cached_vs_full_cutoff_max_abs_D_or_L": float(cached_cutoff_max_abs),
                "self_patch_max_abs_D_shift": float(self_patch_max_abs),
                "cached_deterministic_exact": values_exact(determinism, cached_cutoff_scores["original"]),
                "all_finite": all(
                    score["original_candidate"]["finite"] and score["counterfactual_candidate"]["finite"]
                    for score in cutoff_scores.values()
                ) and all(row_value["patched_score"]["original_candidate"]["finite"] and row_value["patched_score"]["counterfactual_candidate"]["finite"] for row_value in item_patches),
                "prefix_and_groups_aligned": True,
                "cache_diagnostic": cache_diagnostic,
                "full_no_hook": full_no_hook,
                "hooked_noop": hooked_noop,
                "full_sequence_cutoff": cutoff_scores,
                "cached_cutoff": cached_cutoff_scores,
            }

        record = {
            "base_problem_id": base,
            "layout": {
                "prompt_token_ids": prompt_ids[0],
                "question_token_ids": question_ids,
                "groups": groups,
                "condition_prompt_ids_exact": True,
                "condition_image_grids_exact": True,
                "condition_text_positions_exact": True,
            },
            "cache_diagnostic": cache_diagnostic,
            "prefill_audits": prefill_audits,
            "cutoff": cutoff_row,
            "patches": item_patches,
            "rollouts": item_rollouts,
            "smoke": smoke,
        }
        write_json(result_path, record)
        cutoff_rows.append(cutoff_row)
        patch_rows.extend(item_patches)
        rollout_rows.extend(item_rollouts)
        if smoke is not None:
            smoke_rows.append(smoke)
        print(f"[{item_index + 1}/{len(manifest)}] completed base {base}", flush=True)
        del prepared, caches, rope
        gc.collect()
        torch.cuda.empty_cache()

    write_jsonl(output_dir / "cutoff_results.jsonl", cutoff_rows)
    write_jsonl(output_dir / "patch_results.jsonl", patch_rows)
    write_jsonl(output_dir / "rollout_results.jsonl", rollout_rows)
    if smoke_rows:
        write_jsonl(output_dir / "smoke_results.jsonl", smoke_rows)
    write_json(
        output_dir / "result.json",
        {
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "mode": args.mode,
            "base_problem_count": len(cutoff_rows),
            "patch_row_count": len(patch_rows),
            "rollout_row_count": len(rollout_rows),
            "smoke_row_count": len(smoke_rows),
            "peak_gpu_allocated_bytes": int(torch.cuda.max_memory_allocated()),
        },
    )


if __name__ == "__main__":
    main()
