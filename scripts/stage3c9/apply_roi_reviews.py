#!/usr/bin/env python3
"""Apply score-blind manual review to Stage 3C.9 ROI-token mappings."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviews", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target = OUT / "cohort/roi_mapping.jsonl"
    rejection = OUT / "cohort/roi_rejections.jsonl"
    if target.exists() or rejection.exists():
        raise FileExistsError("Final ROI review outputs are create-once")
    pending = read_jsonl(OUT / "cohort/roi_mapping_pending.jsonl")
    reviews = {str(row["base_problem_id"]): row for row in read_jsonl(args.reviews)}
    expected = {str(row["base_problem_id"]) for row in pending}
    if set(reviews) != expected:
        raise RuntimeError(f"ROI reviews must exactly cover pending mappings; missing={sorted(expected-set(reviews), key=int)} extra={sorted(set(reviews)-expected, key=int)}")
    accepted, rejected = [], []
    for row in pending:
        base = str(row["base_problem_id"])
        review = reviews[base]
        if review.get("attention_used") is not False or review.get("causal_scores_available") is not False:
            raise RuntimeError(f"ROI review was not score-blind for base {base}")
        decision = str(review.get("decision", "")).upper()
        if decision == "ACCEPT":
            checks = review.get("checks", {})
            if not all(checks.get(key) is True for key in ("target_patch_alignment", "target_only", "grid_layout_exact", "overlay_legible")):
                raise RuntimeError(f"ROI checks failed for accepted base {base}")
            accepted.append({**row, "manual_overlay_validation": {"status": "pass", "review": review}})
        elif decision == "REJECT":
            rejected.append({**row, "manual_overlay_validation": {"status": "reject", "review": review}})
        else:
            raise ValueError(f"Unknown ROI decision for base {base}: {decision}")
    write_jsonl(target, accepted)
    write_jsonl(rejection, rejected)
    print(json.dumps({"reviewed": len(pending), "accepted": len(accepted), "rejected": len(rejected)}, indent=2))


if __name__ == "__main__":
    main()
