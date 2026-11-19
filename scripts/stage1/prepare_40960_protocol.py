#!/usr/bin/env python3
"""Freeze the shared Stage 1A.2 40,960-token protocol-comparison inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl, write_text
from visual_reasoning.stage1.protocol import (
    GREEDY_PARAMETERS,
    OFFICIAL_QWEN_PARAMETERS,
    OFFICIAL_QWEN_SOURCE,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--historical-8192-manifest", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    historical = [
        json.loads(line)
        for line in args.historical_8192_manifest.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(historical) != 10:
        raise ValueError(f"Expected the exact ten-example 8,192 pilot manifest, found {len(historical)}")
    manifest = [
        {
            **row,
            "order": index,
            "selection_reason": "shared Stage 1A.2 cohort; " + str(row["selection_reason"]),
        }
        for index, row in enumerate(historical)
    ]
    output_dir = args.output_dir.resolve()
    manifest_path = output_dir / "pilot_40960_manifest.jsonl"
    greedy_path = output_dir / "config_40960_greedy.json"
    official_path = output_dir / "config_40960_official.json"
    source_path = output_dir / "official_generation_sources.md"
    for path in (manifest_path, greedy_path, official_path, source_path):
        if path.exists():
            raise FileExistsError(f"Prospective Stage 1A.2 file already exists: {path}")
    common = {
        "stage": "1A.2",
        "purpose": "natural-EOS generation-protocol comparison with a runaway safety ceiling",
        "model_checkpoint": str(args.model_checkpoint.resolve()),
        "dataset_root": str(args.dataset_root.resolve()),
        "manifest": str(manifest_path),
        "example_ids": [str(row["example_id"]) for row in manifest],
        "historical_8192_manifest": str(args.historical_8192_manifest.resolve()),
        "normal_stop": "EOS",
        "safety_ceiling_tokens": 40_960,
        "stage1b_gate": ">=90% normal termination preferred; 80-90% only with documented outlier/bias/resource justification; <80% stop",
        "faithfulness_gate": "3/3 exact generated-token match after selecting a protocol",
        "stage2_authorized": False,
    }
    write_jsonl(manifest_path, manifest)
    by_id = {str(row["example_id"]): row for row in manifest}
    shard_pairs = (("23", "8"), ("33", "14"), ("34", "24"), ("39", "44"), ("43", "48"))
    if set(by_id) != {sample_id for pair in shard_pairs for sample_id in pair}:
        raise ValueError("Historical 8,192 cohort does not match the prospective balanced shard definition")
    for shard_index, pair in enumerate(shard_pairs):
        write_jsonl(
            output_dir / "protocol_shards" / f"shard_{shard_index:02d}.jsonl",
            [{**by_id[sample_id], "shard_order": pair_index} for pair_index, sample_id in enumerate(pair)],
        )
    write_json(
        greedy_path,
        {
            **common,
            "condition": "greedy",
            "parameters": GREEDY_PARAMETERS,
            "configuration_source": "historical Stage 0/Stage 1 greedy pipeline; only safety ceiling changed",
        },
    )
    write_json(
        official_path,
        {
            **common,
            "condition": "official",
            "parameters": OFFICIAL_QWEN_PARAMETERS,
            "configuration_source": OFFICIAL_QWEN_SOURCE,
            "transformers_mapping": {
                "presence_penalty": "not passed because Transformers generate has no vLLM presence_penalty and the official value 0.0 is a no-op",
                "all_other_behavior_changing_parameters": "passed explicitly",
            },
        },
    )
    write_text(
        source_path,
        f"""# Qwen Thinking Generation Sources

## Selected official-style source

- QwenLM/Qwen3-VL official repository, Evaluation Reproduction, Thinking models: `{OFFICIAL_QWEN_SOURCE}`
- Parameters: seed 1234, sampling enabled, temperature 0.6, top-p 0.95, top-k 20, repetition penalty 1.0, presence penalty 0.0, output length 40960.

## Local checkpoint default

- `{args.model_checkpoint.resolve() / 'generation_config.json'}`
- The local released checkpoint instead records sampling enabled, temperature 1.0, top-p 0.95, top-k 20, and repetition penalty 1.0.

## Reconciliation

Condition B uses the explicit Qwen evaluation-reproduction recipe because this task compares intended evaluation-time Thinking behavior. The checkpoint default discrepancy is preserved rather than hidden. Presence penalty 0.0 is recorded but omitted from the Transformers call because it is an exact no-op and is not a Transformers generation argument.
""",
    )
    print(f"Prepared shared 40,960-token protocol cohort with {len(manifest)} examples in five balanced shards")


if __name__ == "__main__":
    main()
