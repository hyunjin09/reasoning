#!/usr/bin/env python3
"""Repair token text after normal multibyte tokenizer prefix rewrites."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from transformers import AutoProcessor

from visual_reasoning.stage0.analysis import aggregate_span_signals, build_reasoning_spans
from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage0.modeling import _incremental_decode_pieces


SIGNAL_NAMES = (
    "visual_attention_mass",
    "prompt_attention_mass",
    "reasoning_attention_mass",
    "next_token_entropy",
    "top1_probability",
    "top1_top2_margin",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    allowed_root = (Path.cwd() / "outputs").resolve()
    try:
        output_dir.relative_to(allowed_root)
    except ValueError as exc:
        raise ValueError(f"Output directory must be under {allowed_root}: {output_dir}") from exc
    processor = AutoProcessor.from_pretrained(args.model_checkpoint.resolve(), local_files_only=True)
    repaired: list[str] = []
    unchanged: list[str] = []
    for example_dir in sorted(
        (path for path in (output_dir / "examples").iterdir() if path.is_dir()),
        key=lambda path: int(path.name),
    ):
        generation_path = example_dir / "generation.json"
        result_path = example_dir / "result.json"
        token_path = example_dir / "tokens.jsonl"
        generation = read_json(generation_path)
        result = read_json(result_path)
        token_rows = read_jsonl(token_path)
        token_ids = [int(value) for value in generation["generated_token_ids"]]
        pieces, raw_decoded, aligned = _incremental_decode_pieces(processor.tokenizer, token_ids)
        if not aligned or len(pieces) != len(token_rows):
            raise RuntimeError(f"Could not reconstruct aligned token text for example {example_dir.name}")
        changed = not bool(generation["alignment"].get("incremental_decode_alignment")) or any(
            str(row.get("decoded_token", "")) != piece for row, piece in zip(token_rows, pieces)
        )
        if not changed:
            unchanged.append(example_dir.name)
            continue
        for row, piece in zip(token_rows, pieces):
            row["decoded_token"] = piece
        spans = build_reasoning_spans(token_rows)
        aggregate_span_signals(spans, token_rows, signal_names=SIGNAL_NAMES)
        with np.load(example_dir / "attention_summary.npz", allow_pickle=False) as arrays:
            visual_focus = arrays["visual_focus"]
            for span in spans:
                start, end = int(span["start_token"]), int(span["end_token"])
                span["visual_focus"] = visual_focus[start:end].mean(axis=0).astype(float).tolist()
        generation["raw_decoded_response"] = raw_decoded
        generation["alignment"]["incremental_decode_alignment"] = True
        generation["alignment"]["span_ranges_valid"] = all(
            0 <= int(span["start_token"]) < int(span["end_token"]) <= len(token_rows) for span in spans
        )
        result["alignment"] = dict(generation["alignment"])
        write_jsonl(token_path, token_rows)
        write_json(example_dir / "spans.json", spans)
        write_json(generation_path, generation)
        write_json(result_path, result)
        repaired.append(example_dir.name)
    report = {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "cause": "normal multibyte tokenizer prefix rewrites were misclassified as token misalignment",
        "scope": "token display text, reasoning spans, and alignment metadata only; token IDs, scores, attention, and generation outputs unchanged",
        "repaired_examples": repaired,
        "unchanged_examples": unchanged,
    }
    write_json(output_dir / "summaries" / "decode_alignment_repair.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
