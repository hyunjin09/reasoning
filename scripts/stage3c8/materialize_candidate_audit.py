#!/usr/bin/env python3
"""Materialize score-blind manual fresh screens into edit and event inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_jsonl
from visual_reasoning.stage3c8.fresh import materialize_manual_candidate


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c8"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposals", type=Path, required=True)
    parser.add_argument("--reviews", type=Path, required=True)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    args = parse_args()
    proposals = read_jsonl(args.proposals)
    reviews = {str(row["base_problem_id"]): row for row in read_jsonl(args.reviews)}
    expected = {str(row["base_problem_id"]) for row in proposals}
    if set(reviews) != expected:
        missing = sorted(expected - set(reviews), key=int)
        extra = sorted(set(reviews) - expected, key=int)
        raise RuntimeError(f"Manual screen must exactly cover proposals; missing={missing}, extra={extra}")
    materialized = [
        materialize_manual_candidate(proposal, reviews[str(proposal["base_problem_id"])])
        for proposal in proposals
    ]
    accepted = [row for row in materialized if row["decision"] == "ACCEPT"]
    write_jsonl(OUT / "cohort/fresh_candidate_audit.jsonl", materialized)
    write_jsonl(OUT / "cohort/fresh_semantic_events_pending.jsonl", [
        {key: value for key, value in row.items() if key != "edit_spec"}
        for row in accepted
    ])
    write_jsonl(OUT / "cohort/fresh_edit_specs.jsonl", [row["edit_spec"] for row in accepted])
    print(json.dumps({
        "reviewed": len(materialized),
        "accepted_for_edit_construction": len(accepted),
        "rejected": len(materialized) - len(accepted),
        "carrier_scores_available": False,
    }, indent=2))


if __name__ == "__main__":
    main()
