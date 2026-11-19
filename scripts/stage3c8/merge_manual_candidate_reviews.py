#!/usr/bin/env python3
"""Merge audited review batches in frozen screen order before materialization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c8"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposals", type=Path, required=True)
    parser.add_argument("--reviews", type=Path, nargs="+", required=True)
    parser.add_argument(
        "--output", type=Path,
        default=OUT / "cohort/fresh_candidate_reviews.jsonl",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    args = parse_args()
    proposals = read_jsonl(args.proposals)
    order = {str(row["base_problem_id"]): int(row["screen_order"]) for row in proposals}
    reviews: dict[str, dict[str, Any]] = {}
    for path in args.reviews:
        for row in read_jsonl(path):
            base = str(row["base_problem_id"])
            if base in reviews:
                raise RuntimeError(f"Duplicate manual candidate review for base {base}")
            reviews[base] = row
    if set(reviews) != set(order):
        missing = sorted(set(order) - set(reviews), key=int)
        extra = sorted(set(reviews) - set(order), key=int)
        raise RuntimeError(f"Review coverage mismatch; missing={missing}, extra={extra}")
    rows = sorted(reviews.values(), key=lambda row: order[str(row["base_problem_id"])])
    if any(row.get("attention_used") is not False or row.get("carrier_scores_available") is not False for row in rows):
        raise RuntimeError("Every manual review must be attention-free and pre-score")
    write_jsonl(args.output, rows)
    print(json.dumps({
        "merged": len(rows),
        "accepted": sum(str(row["decision"]).upper() == "ACCEPT" for row in rows),
        "rejected": sum(str(row["decision"]).upper() == "REJECT" for row in rows),
    }, indent=2))


if __name__ == "__main__":
    main()
