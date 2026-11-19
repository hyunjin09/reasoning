#!/usr/bin/env python3
"""Diagnose full, one-shot-cache, and streaming-cache score-path parity."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from visual_reasoning.a6000_calibration.metrics import compare_scores
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.modeling import load_runtime, runtime_environment
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3b0.runtime import prefill_condition, score_preference_from_cache
from visual_reasoning.stage3c9.streaming import (
    prefill_streaming_state,
    roll_streaming_prefix,
    score_preference_from_streaming_state,
)


ROOT = Path(__file__).resolve().parents[2]
CALIBRATION = ROOT / "outputs/a6000_calibration"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def condition_paths(base: str) -> dict[str, Path]:
    metadata = read_json(
        ROOT / "outputs/stage3b3_redesign/counterfactual_shams" / base / "edit_metadata.json"
    )
    if metadata["manual_validation"]["status"] != "pass":
        raise RuntimeError(f"Image validation failed for base {base}")
    return {condition: ROOT / metadata["paths"][condition] for condition in ("O", "C")}


def evidence_sequences(event: dict[str, Any], state_index: int) -> tuple[list[int], list[int], list[int]]:
    context = [int(value) for value in event["history_before_ed_token_ids"]]
    ed = int(event["ed_generated_index"])
    if not 1 <= int(state_index) <= ed == len(context):
        raise ValueError("Frozen target state is outside evidence history")
    return (
        context,
        [int(value) for value in event["original_divergent_suffix_ids"]],
        [int(value) for value in event["counterfactual_divergent_suffix_ids"]],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="74")
    parser.add_argument("--smoke-result", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base = str(args.base)
    smoke = read_json(args.smoke_result)
    if str(smoke["base_problem_id"]) != base:
        raise ValueError("Smoke result and requested base differ")
    cohort = read_json(CALIBRATION / "config/calibration_cohort.json")
    cell = next(row for row in cohort["cells"] if str(row["base_problem_id"]) == base)
    c7 = read_json(ROOT / "outputs/stage3c7/config/stage3c7_config.json")
    tolerance = float(read_json(CALIBRATION / "config/tolerances.json")["aggregate_D_max_abs_delta"])
    manifests = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(ROOT / "outputs/stage3c7/cohort/primary_manifest.jsonl")
    }
    events = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl")
    }
    dataset = {
        str(row["sample_index"]): row for row in load_mathverse_rows(Path(c7["dataset_root"]))
    }
    item = manifests[base]
    pair = next(row for row in item["state_pairs"] if row["target_id"] == cell["target_id"])
    context, suffix_o, suffix_c = evidence_sequences(events[base], int(pair["state_R"]["generated_index"]))
    processor, model = load_runtime(Path(c7["model_checkpoint"]), device="cuda")
    environment = runtime_environment(Path(c7["model_checkpoint"]), model, 40_960)
    if "A6000" not in str(environment["gpu_name"]):
        raise RuntimeError(f"Expected A6000, observed {environment['gpu_name']}")

    results: dict[str, Any] = {
        "base_problem_id": base,
        "purpose": "single prospective diagnostic after the Layer-A full/cache parity failure",
        "tolerance": tolerance,
        "context_length": len(context),
        "conditions": {},
        "environment": environment,
    }
    for condition, image_path in condition_paths(base).items():
        prepared, metadata = prepare_custom_image(
            processor, dataset[str(item["example_id"])], image_path, device="cuda"
        )
        visual_positions = [int(value) for value in metadata["visual_token_indices"]]
        full = smoke["conditions"][condition]["full_scores"]["native"]

        cache, rope, prefill_audit = prefill_condition(
            model=model, prepared=prepared, seed=int(c7["seed"])
        )
        one_shot = score_preference_from_cache(
            model=model,
            prefill_cache=cache,
            rope_deltas=rope,
            prompt_length=int(prepared["input_ids"].shape[1]),
            visual_token_indices=visual_positions,
            prefix_token_ids=context,
            candidate_original_ids=suffix_o,
            candidate_counterfactual_ids=suffix_c,
            seed=int(c7["seed"]),
            cutoff_enabled=False,
        )

        streaming_scores = {}
        for chunk_size in (len(context), 1):
            stream_prefill, stream_prefill_audit = prefill_streaming_state(
                model=model, prepared=prepared, seed=int(c7["seed"])
            )
            state, stream_audit = roll_streaming_prefix(
                model=model,
                prefill=stream_prefill,
                prefix_token_ids=context,
                end_generated_index=len(context),
                seed=int(c7["seed"]),
                chunk_size=chunk_size,
            )
            score = score_preference_from_streaming_state(
                model=model,
                state=state,
                original_suffix_ids=suffix_o,
                counterfactual_suffix_ids=suffix_c,
                seed=int(c7["seed"]),
            )
            streaming_scores[str(chunk_size)] = {
                "score": score,
                "prefill_audit": stream_prefill_audit,
                "stream_audit": stream_audit,
                "versus_full": compare_scores(full, score, tolerance=tolerance),
                "versus_one_shot_cache": compare_scores(one_shot, score, tolerance=tolerance),
            }

        results["conditions"][condition] = {
            "full": full,
            "one_shot_cache": one_shot,
            "one_shot_prefill_audit": prefill_audit,
            "one_shot_versus_full": compare_scores(full, one_shot, tolerance=tolerance),
            "streaming": streaming_scores,
            "streaming_chunk_comparison": compare_scores(
                streaming_scores[str(len(context))]["score"],
                streaming_scores["1"]["score"],
                tolerance=tolerance,
            ),
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
