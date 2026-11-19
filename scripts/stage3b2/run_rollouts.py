#!/usr/bin/env python3
"""Run matched-seed Stage 3B.2 short behavioral source-switch rollouts."""

from __future__ import annotations

import argparse
import copy
import gc
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

from visual_reasoning.stage0.analysis import extract_answer
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage1.protocol import protocol_parameters, transformers_generation_kwargs
from visual_reasoning.stage3a.runtime import prepare_custom_image, short_rollout
from visual_reasoning.stage3b2.runtime import (
    capture_audit_valid,
    capture_context_visual_kv,
    classify_first_discriminative_token,
)
from visual_reasoning.stage3b2.switching import VisualSourceSwitch


ROOT = Path(__file__).resolve().parents[2]
SEED = 1_234
MAX_NEW_TOKENS = 64
CONDITIONS = ("original", "counterfactual", "sham")
ROLLOUT_LABELS = ("Ed_minus_16", "Ed_minus_4", "Ed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--schedule", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--required-gpu-class", choices=("A5000", "A6000"), default="A5000")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def rollout_audit_summary(audit: list[dict[str, Any]]) -> dict[str, Any]:
    absolute = [value for row in audit for value in row["switched_absolute_query_indices"]]
    return {
        "call_count": len(audit),
        "layers": sorted(set(int(row["layer_index"]) for row in audit)),
        "first_switched_absolute_query": audit[0]["first_switched_absolute_query"] if audit else None,
        "minimum_switched_absolute_query": min(absolute) if absolute else None,
        "maximum_switched_absolute_query": max(absolute) if absolute else None,
        "queries_before_switch_modified": sum(int(row["queries_before_switch_modified"]) for row in audit),
        "nonvisual_key_value_entries_replaced": sum(
            int(row["nonvisual_key_value_entries_replaced"]) for row in audit
        ),
    }


def classify_rollout(result: dict[str, Any], annotation: dict[str, Any]) -> dict[str, Any]:
    classification = classify_first_discriminative_token(
        result["generated_token_ids"],
        original_token_id=int(annotation["first_original_divergent_token_id"]),
        counterfactual_token_id=int(annotation["first_counterfactual_divergent_token_id"]),
    )
    return {
        **result,
        "first_discriminative_token_classification": classification,
        "first_generated_token_id": result["generated_token_ids"][0]
        if result["generated_token_ids"]
        else None,
        "extracted_final_answer": extract_answer(result["continuation_text"]),
    }


def switched_rollout(
    *,
    model: Any,
    processor: Any,
    prepared: dict[str, Any],
    context: list[int],
    source_layers: list[tuple[torch.Tensor, torch.Tensor]],
    visual_indices: list[int],
    switch_index: int,
    generation_kwargs: dict[str, Any],
) -> dict[str, Any]:
    prompt_length = int(prepared["input_ids"].shape[1])
    switch = VisualSourceSwitch(
        model=model,
        source_layers=source_layers,
        visual_indices=visual_indices,
        first_switched_absolute_query=prompt_length + int(switch_index) - 1,
    )
    with switch:
        result = short_rollout(
            model=model,
            processor=processor,
            prepared=prepared,
            prefix_token_ids=context,
            generation_kwargs=generation_kwargs,
            seed=SEED,
            max_new_tokens=MAX_NEW_TOKENS,
        )
    result["switch_audit"] = rollout_audit_summary(copy.deepcopy(switch.audit))
    return result


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    output_dir.relative_to((ROOT / "outputs/stage3b2/raw/rollouts").resolve())
    manifest = read_jsonl(args.manifest)
    annotations = {str(row["base_problem_id"]): row for row in read_jsonl(args.annotations)}
    schedules = {str(row["base_problem_id"]): row for row in read_jsonl(args.schedule)}
    bases = [str(row["base_problem_id"]) for row in manifest]
    signature = {
        "manifest": str(args.manifest.resolve()),
        "base_problem_ids": bases,
        "seed": SEED,
        "max_new_tokens": MAX_NEW_TOKENS,
        "labels": list(ROLLOUT_LABELS),
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

    data_rows = load_mathverse_rows(args.dataset_root)
    by_example = {str(row["sample_index"]): row for row in data_rows}
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    environment = runtime_environment(args.model_checkpoint, model, MAX_NEW_TOKENS)
    if args.required_gpu_class not in str(environment["gpu_name"]):
        raise RuntimeError(f"Expected {args.required_gpu_class}, observed {environment['gpu_name']}")
    write_json(output_dir / "environment.json", environment)
    generation_kwargs = transformers_generation_kwargs(
        protocol_parameters("official", MAX_NEW_TOKENS, SEED)
    )
    layer_count = int(model.config.text_config.num_hidden_layers)
    kv_heads = int(model.config.text_config.num_key_value_heads)
    head_dim = int(model.config.text_config.head_dim)
    all_rows = []
    peak_gpu_bytes = 0

    for item_index, item in enumerate(manifest):
        base = str(item["base_problem_id"])
        result_path = output_dir / "examples" / base / "result.json"
        if args.resume and result_path.is_file():
            all_rows.extend(json.loads(result_path.read_text(encoding="utf-8"))["rollouts"])
            print(f"[{item_index + 1}/{len(manifest)}] resumed base {base}", flush=True)
            continue
        ensure_directory(result_path.parent)
        annotation = annotations[base]
        context = [int(value) for value in annotation["history_before_ed_token_ids"]]
        source_row = by_example[str(item["example_id"])]
        prepared: dict[str, dict[str, Any]] = {}
        metadata: dict[str, dict[str, Any]] = {}
        captures: dict[str, dict[str, Any]] = {}
        for condition in CONDITIONS:
            prepared[condition], metadata[condition] = prepare_custom_image(
                processor, source_row, ROOT / item["conditions"][condition], device="cuda"
            )
        prompt_ids = [metadata[name]["prompt_token_ids"] for name in CONDITIONS]
        visual_sets = [metadata[name]["visual_token_indices"] for name in CONDITIONS]
        if not all(value == prompt_ids[0] for value in prompt_ids[1:]) or not all(
            value == visual_sets[0] for value in visual_sets[1:]
        ):
            raise RuntimeError(f"Rollout condition layout mismatch for base {base}")
        visual_indices = [int(value) for value in visual_sets[0]]
        for condition in CONDITIONS:
            captures[condition] = capture_context_visual_kv(
                model=model,
                prepared=prepared[condition],
                context_token_ids=context,
                visual_indices=visual_indices,
                seed=SEED,
            )
        capture_valid = all(
            capture_audit_valid(
                captures[name]["capture_audit"],
                visual_indices=visual_indices,
                layer_count=layer_count,
                kv_heads=kv_heads,
                head_dim=head_dim,
            )
            for name in CONDITIONS
        )
        if not capture_valid:
            raise RuntimeError(f"Rollout donor visual K/V capture failed for base {base}")

        no_switch = classify_rollout(
            short_rollout(
                model=model,
                processor=processor,
                prepared=prepared["original"],
                prefix_token_ids=context,
                generation_kwargs=generation_kwargs,
                seed=SEED,
                max_new_tokens=MAX_NEW_TOKENS,
            ),
            annotation,
        )
        checkpoints = []
        for label in ROLLOUT_LABELS:
            matching = [row for row in schedules[base]["checkpoints"] if label in row["labels"]]
            if not matching:
                continue
            checkpoint = matching[0]
            switch_index = int(checkpoint["switch_generated_index"])
            condition_results = {
                "O_history_O_vision": copy.deepcopy(no_switch),
                "O_history_C_vision": classify_rollout(
                    switched_rollout(
                        model=model,
                        processor=processor,
                        prepared=prepared["original"],
                        context=context,
                        source_layers=captures["counterfactual"]["source_layers"],
                        visual_indices=visual_indices,
                        switch_index=switch_index,
                        generation_kwargs=generation_kwargs,
                    ),
                    annotation,
                ),
                "O_history_sham_vision": classify_rollout(
                    switched_rollout(
                        model=model,
                        processor=processor,
                        prepared=prepared["original"],
                        context=context,
                        source_layers=captures["sham"]["source_layers"],
                        visual_indices=visual_indices,
                        switch_index=switch_index,
                        generation_kwargs=generation_kwargs,
                    ),
                    annotation,
                ),
                "C_history_O_vision": classify_rollout(
                    switched_rollout(
                        model=model,
                        processor=processor,
                        prepared=prepared["counterfactual"],
                        context=context,
                        source_layers=captures["original"]["source_layers"],
                        visual_indices=visual_indices,
                        switch_index=switch_index,
                        generation_kwargs=generation_kwargs,
                    ),
                    annotation,
                ),
            }
            sequences = {
                name: value["generated_token_ids"] for name, value in condition_results.items()
            }
            common_length = min((len(value) for value in sequences.values()), default=0)
            first_divergence = next(
                (
                    index
                    for index in range(common_length)
                    if len({values[index] for values in sequences.values()}) > 1
                ),
                None,
            )
            checkpoints.append(
                {
                    "base_problem_id": base,
                    "example_id": str(item["example_id"]),
                    "checkpoint_label": label,
                    "switch_generated_index": switch_index,
                    "ed_generated_index": int(annotation["ed_generated_index"]),
                    "first_cross_condition_token_divergence": first_divergence,
                    "conditions": condition_results,
                    "O_to_C_overrides_old_identity": condition_results["O_history_C_vision"][
                        "first_discriminative_token_classification"
                    ]
                    == "counterfactual",
                    "C_to_O_overrides_old_identity": condition_results["C_history_O_vision"][
                        "first_discriminative_token_classification"
                    ]
                    == "original",
                    "capture_all_layers_valid": capture_valid,
                }
            )
            peak_gpu_bytes = max(peak_gpu_bytes, int(torch.cuda.max_memory_allocated()))
        write_json(result_path, {"base_problem_id": base, "rollouts": checkpoints})
        all_rows.extend(checkpoints)
        print(f"[{item_index + 1}/{len(manifest)}] completed base {base} ({len(checkpoints)} rollout checkpoints)", flush=True)
        del prepared, captures, checkpoints
        gc.collect()
        torch.cuda.empty_cache()

    write_jsonl(output_dir / "rollout_results.jsonl", all_rows)
    write_json(
        output_dir / "result.json",
        {
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "base_problem_count": len({row["base_problem_id"] for row in all_rows}),
            "rollout_checkpoint_count": len(all_rows),
            "condition_rollout_count": 4 * len(all_rows),
            "all_capture_layers_valid": all(row["capture_all_layers_valid"] for row in all_rows),
            "peak_gpu_allocated_bytes": peak_gpu_bytes,
        },
    )


if __name__ == "__main__":
    main()
