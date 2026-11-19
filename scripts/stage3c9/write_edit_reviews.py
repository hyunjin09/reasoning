#!/usr/bin/env python3
"""Write the frozen, score-blind Stage 3C.9 manual edit-review decisions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"


# Decisions were made from the full-image and enlarged-ROI review sheets before
# any Stage 3C.9 causal score existed. Three edit versions that still failed
# after the frozen v2 repair are listed explicitly alongside unrepaired rejects.
REJECTIONS: dict[str, str] = {
    "10": "The replacement duplicates the original target label instead of cleanly substituting it.",
    "14": "The replacement duplicates the original target label instead of cleanly substituting it.",
    "29": "The replacement overlaps the original target and adjacent diagram strokes.",
    "45": "The replacement duplicates the original target label instead of cleanly substituting it.",
    "56": "The replacement duplicates the original target label instead of cleanly substituting it.",
    "59": "The replacement duplicates the original target label instead of cleanly substituting it.",
    "61": "The replacement duplicates the original target label instead of cleanly substituting it.",
    "67": "The replacement duplicates the original target label instead of cleanly substituting it.",
    "73": "The replacement duplicates the original target label instead of cleanly substituting it.",
    "104": "The repaired target box remains vertically misaligned, leaving the original value visible.",
    "142": "The repaired target box leaves the original value visible beside the replacement.",
    "176": "The replacement duplicates the original target label instead of cleanly substituting it.",
    "423": "The replacement is misoriented and does not fully remove the original target label.",
    "762": "The repaired edit removes a substantial segment of a task-relevant rectangle edge.",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    pending = read_jsonl(OUT / "cohort/edit_manifest_pending.jsonl")
    bases = {str(row["base_problem_id"]) for row in pending}
    if len(pending) != 71 or len(bases) != 71:
        raise RuntimeError("Expected 71 unique pending edit quartets")
    if not set(REJECTIONS).issubset(bases):
        raise RuntimeError("Review rejection set contains a base outside the pending manifest")

    target = OUT / "cohort/work/manual_edit_reviews.jsonl"
    if target.exists():
        raise FileExistsError(f"Create-once review file already exists: {target}")

    required_checks = {
        "full_image": True,
        "roi_crop": True,
        "target_semantics_exact": True,
        "sham_semantics_exact": True,
        "unrelated_content_unchanged": True,
        "legible": True,
        "counterfactual_problem_valid": True,
    }
    reviews = []
    for item in pending:
        base = str(item["base_problem_id"])
        rejected = base in REJECTIONS
        reviews.append({
            "base_problem_id": base,
            "decision": "REJECT" if rejected else "ACCEPT",
            "reason": REJECTIONS.get(
                base,
                "Full image and enlarged ROI pass manual semantic, locality, legibility, and sham-control review.",
            ),
            "checks": {} if rejected else dict(required_checks),
            "attention_used": False,
            "causal_scores_available": False,
        })
    write_jsonl(target, reviews)
    print(json.dumps({
        "reviewed": len(reviews),
        "accepted": len(reviews) - len(REJECTIONS),
        "rejected": len(REJECTIONS),
        "attention_used": False,
        "causal_scores_available": False,
        "output": str(target.relative_to(ROOT)),
    }, indent=2))


if __name__ == "__main__":
    main()
