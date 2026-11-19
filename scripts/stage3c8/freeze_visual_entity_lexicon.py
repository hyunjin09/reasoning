#!/usr/bin/env python3
"""Freeze manually reviewed visual-entity lexicons before token-cache scoring."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c8"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviews", type=Path, required=True)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    args = parse_args()
    destination = OUT / "annotations/visual_entity_lexicon.jsonl"
    if destination.exists():
        raise FileExistsError(destination)
    draft = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "annotations/visual_entity_lexicon_draft.jsonl")}
    reviews = {str(row["base_problem_id"]): row for row in read_jsonl(args.reviews)}
    if set(draft) != set(reviews):
        raise RuntimeError("Manual lexicon review must exactly cover the draft")
    frozen_at = datetime.now(timezone.utc).isoformat()
    frozen = []
    for base in sorted(draft, key=int):
        review = reviews[base]
        if review.get("manual_review_status") != "pass" or review.get("attention_used") is not False or review.get("causal_token_scores_available") is not False:
            raise RuntimeError(f"Invalid visual-entity review provenance for base {base}")
        visual = sorted({str(value).strip().lower() for value in review["visual_entities"] if str(value).strip()})
        target = sorted({str(value).strip().lower() for value in review["target_aligned_terms"] if str(value).strip()})
        mention = sorted({str(value).strip().lower() for value in review["mention_aligned_terms"] if str(value).strip()})
        if not target or not set(target).issubset(set(visual)) or not set(mention).issubset(set(visual)):
            raise RuntimeError(f"Target/mention terms must be nonempty subsets of visual entities for base {base}")
        frozen.append({
            "base_problem_id": base,
            "example_id": str(draft[base]["example_id"]),
            "visual_entities": visual,
            "target_aligned_terms": target,
            "mention_aligned_terms": mention,
            "manual_review_status": "pass",
            "reviewer": "primary research agent",
            "attention_used": False,
            "causal_token_scores_available": False,
            "frozen_at": frozen_at,
        })
    write_jsonl(destination, frozen)
    print(json.dumps({"frozen": len(frozen)}, indent=2))


if __name__ == "__main__":
    main()
