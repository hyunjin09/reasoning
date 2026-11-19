#!/usr/bin/env python3
"""One-example diagnostic for full-sequence versus cached scoring parity."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import write_json
from visual_reasoning.stage0.modeling import load_runtime
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3b0.layout import build_token_groups
from visual_reasoning.stage3b0.runtime import prefill_condition, score_preference_from_cache

from run_interventions import SEED, score_full_preference


ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    item = json.loads(next(line for line in args.manifest.read_text(encoding="utf-8").splitlines() if line.strip()))
    rows = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    row = rows[str(item["example_id"])]
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    prepared, metadata = prepare_custom_image(
        processor, row, ROOT / item["conditions"]["original"], device="cuda"
    )
    question = str(row.get("query_cot") or row.get("question") or "")
    groups = build_token_groups(
        prompt_token_ids=metadata["prompt_token_ids"],
        visual_token_indices=metadata["visual_token_indices"],
        question_token_ids=processor.tokenizer.encode(question, add_special_tokens=False),
    )
    prefix = [int(value) for value in item["prefix_token_ids"]]
    candidate_o = processor.tokenizer.encode(item["candidate_original"], add_special_tokens=False)
    candidate_c = processor.tokenizer.encode(item["candidate_counterfactual"], add_special_tokens=False)
    cache, rope, prefill = prefill_condition(model=model, prepared=prepared, seed=SEED)
    results = {}
    for label, full_hook, cached_cutoff in (
        ("no_cutoff", None, False),
        ("visual_cutoff", True, True),
    ):
        full = score_full_preference(
            model=model,
            prepared=prepared,
            prefix=prefix,
            candidate_o=candidate_o,
            candidate_c=candidate_c,
            visual=groups["V"],
            cutoff_enabled=full_hook,
        )
        cached = score_preference_from_cache(
            model=model,
            prefill_cache=cache,
            rope_deltas=rope,
            prompt_length=len(metadata["prompt_token_ids"]),
            visual_token_indices=groups["V"],
            prefix_token_ids=prefix,
            candidate_original_ids=candidate_o,
            candidate_counterfactual_ids=candidate_c,
            seed=SEED,
            cutoff_enabled=cached_cutoff,
        )
        results[label] = {
            "full": {key: full[key] for key in ("L_o", "L_c", "D")},
            "cached": {key: cached[key] for key in ("L_o", "L_c", "D")},
            "absolute_differences": {key: abs(full[key] - cached[key]) for key in ("L_o", "L_c", "D")},
        }
    write_json(
        args.output,
        {
            "base_problem_id": str(item["base_problem_id"]),
            "diagnostic_question": "Is cached/full discrepancy specific to the cutoff or a general deterministic kernel-path difference?",
            "prefill": prefill,
            "results": results,
        },
    )
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
