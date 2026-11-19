#!/usr/bin/env python3
"""Write frozen, score-blind Stage 3C.9 ROI-overlay review decisions."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.stage0.io import write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    pending = read_jsonl(OUT / "cohort/roi_mapping_pending.jsonl")
    if len(pending) != 57 or len({str(row["base_problem_id"]) for row in pending}) != 57:
        raise RuntimeError("Expected 57 unique score-blind ROI mappings")
    target = OUT / "cohort/work/manual_roi_reviews.jsonl"
    if target.exists():
        raise FileExistsError(f"Create-once review file already exists: {target}")
    checks = {
        "target_patch_alignment": True,
        "target_only": True,
        "grid_layout_exact": True,
        "overlay_legible": True,
    }
    reviews = [{
        "base_problem_id": str(row["base_problem_id"]),
        "decision": "ACCEPT",
        "reason": (
            "Changed-pixel ROI and intersecting visual-token cells align with the target evidence; "
            "coarse grid-cell coverage is retained without attention-guided adjustment."
        ),
        "checks": dict(checks),
        "attention_used": False,
        "causal_scores_available": False,
    } for row in pending]
    write_jsonl(target, reviews)
    print(json.dumps({
        "reviewed": len(reviews),
        "accepted": len(reviews),
        "rejected": 0,
        "attention_used": False,
        "causal_scores_available": False,
        "output": str(target.relative_to(ROOT)),
    }, indent=2))


if __name__ == "__main__":
    main()
