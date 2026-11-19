#!/usr/bin/env python3
"""Create score-blind numeric evidence/E_d proposals for manual fresh review."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from transformers import AutoTokenizer

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import write_jsonl
from visual_reasoning.stage3c8.fresh import (
    exact_numeric_candidate,
    infer_missing_numeric_facts,
    numeric_surface_matches,
    propose_counterfactual_numeric_value,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c8"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pool", type=Path, default=OUT / "prospective_generation/completed_correct_pool.jsonl")
    parser.add_argument("--allow-partial-raw", action="store_true")
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--model-checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUT / "cohort/fresh_evidence_proposals.jsonl")
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def numeric_variants(value: str) -> set[str]:
    result = {str(value)}
    try:
        number = float(value)
    except ValueError:
        return result
    if number.is_integer():
        result.add(str(int(number)))
        result.add(f"{number:.1f}")
    return result


def token_offsets(tokens: list[dict[str, Any]]) -> tuple[str, list[tuple[int, int]]]:
    pieces = [str(row["decoded_token"]) for row in tokens]
    bounds, cursor = [], 0
    for piece in pieces:
        bounds.append((cursor, cursor + len(piece)))
        cursor += len(piece)
    return "".join(pieces), bounds


def token_at(bounds: list[tuple[int, int]], character: int) -> int:
    for index, (start, end) in enumerate(bounds):
        if start <= character < end:
            return index
    return len(bounds) - 1


def main() -> None:
    args = parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    if args.pool.is_file():
        pool = read_jsonl(args.pool)
    elif args.allow_partial_raw:
        pool = [
            read_json(path)
            for path in sorted((OUT / "prospective_generation/raw").glob("shard_*/examples/*/result.json"))
            if read_json(path)["status"] == "correct"
        ]
    else:
        raise FileNotFoundError(args.pool)
    rows = load_mathverse_rows(args.dataset_root)
    by_base: dict[str, dict[str, dict[str, Any]]] = {}
    for row in rows:
        by_base.setdefault(str(row["problem_index"]), {})[str(row["problem_version"])] = row
    tokenizer = AutoTokenizer.from_pretrained(args.model_checkpoint, local_files_only=True)
    proposals = []
    for item in sorted(pool, key=lambda row: int(row["screen_order"])):
        base = str(item["base_problem_id"])
        variants = by_base[base]
        dominant = variants["Vision Dominant"]
        text_variant = variants.get("Text Dominant") or variants.get("Text Lite")
        if text_variant is None:
            facts = []
        else:
            facts = infer_missing_numeric_facts(
                str(text_variant.get("question_for_eval") or text_variant.get("question") or ""),
                str(dominant.get("question_for_eval") or dominant.get("question") or ""),
            )
        artifact = ROOT / item["artifact_dir"]
        generation = read_json(artifact / "generation.json")
        tokens = read_jsonl(artifact / "tokens.jsonl")
        text, bounds = token_offsets(tokens)
        fact_rows = []
        for fact_index, fact in enumerate(facts):
            matches = numeric_surface_matches(text, numeric_variants(fact["original_value"]))
            if not matches:
                fact_rows.append({**fact, "proposal_status": "reject_no_trace_value", "trace_mentions": []})
                continue
            match = min(matches, key=lambda value: value.start())
            sentence_breaks = list(re.finditer(r"(?:[.!?](?:\s+|$)|\n+)", text[:match.start()]))
            e0_char = sentence_breaks[-1].end() if sentence_breaks else 0
            e0 = token_at(bounds, e0_char)
            counterfactual = propose_counterfactual_numeric_value(
                fact["original_value"], fact["context"]
            )
            candidate = exact_numeric_candidate(
                tokens=tokens,
                match_start=match.start(),
                match_end=match.end(),
                counterfactual_value=counterfactual,
                tokenizer=tokenizer,
            )
            fact_rows.append({
                **fact,
                "fact_index": fact_index,
                "counterfactual_value": counterfactual,
                "proposal_status": "manual_review_required",
                "e0_start_token_proposed": e0,
                "ed_generated_index_proposed": candidate["ed_generated_index"],
                **{key: value for key, value in candidate.items() if key != "ed_generated_index"},
                "trace_context": text[max(0, match.start() - 260):min(len(text), match.end() + 320)].replace("\n", "\\n"),
                "trace_value_character_start": match.start(),
                "trace_value_surface": match.group(0),
                "prefix_is_strictly_before_value": True,
            })
        proposals.append({
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "screen_order": int(item["screen_order"]),
            "source": item["source"],
            "generation_path": str((artifact / "generation.json").relative_to(ROOT)),
            "generated_token_count": int(generation["generated_token_count"]),
            "vision_dominant_question": str(dominant.get("question_for_eval") or dominant.get("question") or ""),
            "text_dominant_question": None if text_variant is None else str(text_variant.get("question_for_eval") or text_variant.get("question") or ""),
            "numeric_fact_proposals": fact_rows,
            "selection_used_attention": False,
            "carrier_scores_available": False,
        })
    write_jsonl(args.output, proposals)
    print(json.dumps({
        "completed_correct": len(pool),
        "with_missing_numeric_fact": sum(bool(row["numeric_fact_proposals"]) for row in proposals),
        "with_trace_aligned_fact": sum(any(fact["proposal_status"] == "manual_review_required" for fact in row["numeric_fact_proposals"]) for row in proposals),
    }, indent=2))


if __name__ == "__main__":
    main()
