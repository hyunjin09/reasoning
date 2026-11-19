#!/usr/bin/env python3
"""Draft attention-free visual-entity terms for required manual semantic review."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from run_phase_a import ROOT, assets, read_jsonl
from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import write_jsonl
from visual_reasoning.stage3c8.protocol import FUNCTION_WORDS


OUT = ROOT / "outputs/stage3c8"
UNIT_TERMS = {"cm", "mm", "m", "degree", "degrees"}
NON_ENTITY_TERMS = {"as", "choices", "find", "if", "then", "shown", "figure"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifests", type=Path, nargs="+", required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUT / "annotations/visual_entity_lexicon_draft.jsonl")
    return parser.parse_args()


def terms(text: str) -> set[str]:
    return {value.lower() for value in re.findall(r"[A-Za-z]+(?:_[A-Za-z]+)*|\d+(?:\.\d+)?", str(text))}


def main() -> None:
    args = parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    items = [row for path in args.manifests for row in read_jsonl(path)]
    if len({str(row["base_problem_id"]) for row in items}) != len(items):
        raise RuntimeError("Visual-entity lexicon manifests overlap")
    old_events = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl")
    }
    old_rois = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(ROOT / "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl")
    }
    dataset = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    rows = []
    for item in items:
        base = str(item["base_problem_id"])
        _, event, _ = assets(item, old_events, old_rois)
        mention_text = str(item.get("mention_entity") or item.get("target_evidence") or event.get("target_entity") or "")
        original = terms(event["original_fact"])
        counterfactual = terms(event["counterfactual_fact"])
        mention = terms(mention_text) - FUNCTION_WORDS - UNIT_TERMS
        target = ((original & counterfactual) | (original ^ counterfactual) | mention) - FUNCTION_WORDS - UNIT_TERMS
        question = str(dataset[str(item["example_id"])].get("query_cot") or dataset[str(item["example_id"])].get("question") or "")
        uppercase = {
            value.lower()
            for value in re.findall(r"\b(?:[A-Z]{1,4}|[A-Z][a-z]+)\b", question)
            if value.lower() not in NON_ENTITY_TERMS
        }
        rows.append({
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "question": question,
            "mention_source": mention_text,
            "suggested_visual_entities": sorted(uppercase | mention | target),
            "suggested_target_aligned_terms": sorted(target),
            "suggested_mention_aligned_terms": sorted(mention),
            "manual_review_status": "pending",
            "attention_used": False,
            "causal_token_scores_available": False,
        })
    write_jsonl(args.output, rows)
    print(json.dumps({"drafted": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
