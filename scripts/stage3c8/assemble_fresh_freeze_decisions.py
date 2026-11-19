#!/usr/bin/env python3
"""Assemble final score-blind semantic/edit/ROI reviews for cohort freezing."""

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
    parser.add_argument("--roi-reviews", type=Path, required=True)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    args = parse_args()
    events = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(OUT / "cohort/fresh_semantic_events_pending.jsonl")
    }
    edits = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(OUT / "cohort/fresh_edit_manifest_reviewed.jsonl")
    }
    rois = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(OUT / "cohort/fresh_roi_mapping_pending.jsonl")
    }
    reviews = {str(row["base_problem_id"]): row for row in read_jsonl(args.roi_reviews)}
    if not set(edits).issubset(events):
        raise RuntimeError("Reviewed edits include a base without a frozen semantic event")
    if set(edits) != set(rois) or set(edits) != set(reviews):
        raise RuntimeError("Reviewed edits, ROI mappings, and manual ROI reviews must exactly match")
    decisions = []
    for base in sorted(edits, key=lambda value: int(events[value]["screen_order"])):
        event_row = events[base]
        edit_row = edits[base]
        edit = read_json(ROOT / edit_row["edit_metadata"])
        review = reviews[base]
        if review.get("attention_used") is not False or review.get("carrier_scores_available") is not False:
            raise RuntimeError(f"ROI review was not score-blind for base {base}")
        if str(review.get("decision", "")).upper() != "ACCEPT":
            raise RuntimeError(f"Only accepted ROI mappings may be frozen; base {base}")
        edit_checks = {
            name: bool(edit["manual_validation"][name])
            for name in ("full_image", "roi_crop", "target_semantics_exact", "unrelated_content_unchanged", "legible")
        }
        roi_checks = {
            "target_roi_exact": bool(review["target_roi_exact"]),
            "token_overlay_aligned": bool(review["token_overlay_aligned"]),
        }
        if not all(edit_checks.values()) or not all(roi_checks.values()):
            raise RuntimeError(f"Accepted freeze decision has a failed check for base {base}")
        decisions.append({
            "base_problem_id": base,
            "decision": "ACCEPT",
            "reason": str(review.get("reason", "semantic edit and visual-token ROI manually validated")),
            "target_evidence": event_row["target_evidence"],
            "evidence_type": event_row["evidence_type"],
            "event": event_row["event"],
            "edit_checks": edit_checks,
            "roi_checks": roi_checks,
            "attention_used": False,
            "carrier_scores_available": False,
        })
    output = OUT / "cohort/fresh_freeze_decisions.jsonl"
    write_jsonl(output, decisions)
    print(json.dumps({
        "freeze_decisions": len(decisions),
        "all_score_blind": True,
        "all_edit_checks_pass": True,
        "all_roi_checks_pass": True,
    }, indent=2))


if __name__ == "__main__":
    main()
