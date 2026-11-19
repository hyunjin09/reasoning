#!/usr/bin/env python3
"""Materialize a complete score-blind prefix of Stage 3C.9 semantic reviews."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_jsonl
from visual_reasoning.stage3c9.annotations import freeze_semantic_review


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--audit-output", type=Path, required=True)
    parser.add_argument("--accepted-output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.audit_output.exists() or args.accepted_output.exists():
        raise FileExistsError("Semantic materialization targets are create-once")
    proposals = read_jsonl(OUT / "cohort/candidate_proposals.jsonl")
    reviews = {str(row["base_problem_id"]): row for row in read_jsonl(args.reviews)}
    if not reviews:
        raise ValueError("At least one manual review is required")
    candidate_by_base = {
        str(row["base_problem_id"]): row
        for row in proposals
        if row["proposal_status"] == "manual_review_required"
    }
    unknown = sorted(set(reviews) - set(candidate_by_base), key=int)
    if unknown:
        raise RuntimeError(f"Reviews include non-candidates: {unknown}")
    cutoff = max(int(candidate_by_base[base]["screen_order"]) for base in reviews)
    expected = {
        base for base, row in candidate_by_base.items()
        if int(row["screen_order"]) <= cutoff
    }
    if set(reviews) != expected:
        missing = sorted(expected - set(reviews), key=int)
        raise RuntimeError(f"Manual reviews must cover the complete candidate prefix through order {cutoff}; missing={missing}")
    audit = []
    for proposal in proposals:
        if int(proposal["screen_order"]) > cutoff:
            continue
        base = str(proposal["base_problem_id"])
        if proposal["proposal_status"] != "manual_review_required":
            audit.append({
                "base_problem_id": base,
                "example_id": str(proposal["example_id"]),
                "screen_order": int(proposal["screen_order"]),
                "decision": "REJECT",
                "reason": proposal["proposal_status"],
                "attention_used": False,
                "causal_scores_available": False,
            })
        else:
            audit.append(freeze_semantic_review(proposal, reviews[base]))
    accepted = [row for row in audit if row["decision"] == "ACCEPT"]
    write_jsonl(args.audit_output, audit)
    write_jsonl(args.accepted_output, accepted)
    print(json.dumps({
        "cutoff_screen_order": cutoff,
        "screened_prefix_rows": len(audit),
        "manual_candidate_reviews": len(reviews),
        "accepted_for_edit_construction": len(accepted),
        "rejected": len(audit) - len(accepted),
        "attention_used": False,
        "causal_scores_available": False,
    }, indent=2))


if __name__ == "__main__":
    main()
