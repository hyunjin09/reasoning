#!/usr/bin/env python3
"""Four-token GPU smoke for seeded sampling and memory-safe instrumentation."""

from __future__ import annotations

import argparse
from pathlib import Path

from visual_reasoning.stage0.attention import OnlineAttentionRecorder
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import write_json
from visual_reasoning.stage0.modeling import attention_modules, generate_once, load_runtime, prepare_example
from visual_reasoning.stage1.protocol import protocol_parameters, transformers_generation_kwargs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    row = next(row for row in load_mathverse_rows(args.dataset_root) if str(row["sample_index"]) == "8")
    processor, model = load_runtime(args.model_checkpoint, device="cuda")
    prepared, input_record, _ = prepare_example(processor, row, args.dataset_root, device="cuda")
    parameters = protocol_parameters("official", max_new_tokens=4, seed=1234)
    generation_kwargs = transformers_generation_kwargs(parameters)
    first = generate_once(
        model,
        processor,
        prepared,
        4,
        recorder=None,
        generation_kwargs=generation_kwargs,
        seed=1234,
        collect_predictive_metrics=False,
    )
    second = generate_once(
        model,
        processor,
        prepared,
        4,
        recorder=None,
        generation_kwargs=generation_kwargs,
        seed=1234,
        collect_predictive_metrics=False,
    )
    attention = OnlineAttentionRecorder(
        prompt_length=int(input_record["prompt_token_count"]),
        visual_indices=[int(value) for value in input_record["visual_token_indices"]],
        num_layers=int(model.config.text_config.num_hidden_layers),
        selected_head_layers=[0, 1, 18, 35],
    ).attach(attention_modules(model))
    try:
        instrumented = generate_once(
            model,
            processor,
            prepared,
            4,
            recorder=attention,
            generation_kwargs=generation_kwargs,
            seed=1234,
            collect_predictive_metrics=True,
            memory_safe_scores=True,
        )
    finally:
        attention.close()
    validation = attention.validate(4)
    report = {
        "passed": (
            first["generated_token_ids"] == second["generated_token_ids"] == instrumented["generated_token_ids"]
            and validation["passed"]
            and len(instrumented["token_rows"]) == 4
            and all("next_token_entropy" in row for row in instrumented["token_rows"])
        ),
        "purpose": "runtime API smoke only; not the selected-protocol faithfulness gate",
        "full_pilot_safety_ceiling": 40_960,
        "smoke_generated_tokens": 4,
        "parameters": parameters,
        "first_ids": first["generated_token_ids"],
        "second_ids": second["generated_token_ids"],
        "instrumented_ids": instrumented["generated_token_ids"],
        "attention_validation": validation,
    }
    write_json(args.output.resolve(), report)
    print(report)
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
