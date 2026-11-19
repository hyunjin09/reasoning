#!/usr/bin/env python3
"""Freeze the manually reviewed Stage 3B.9 fresh ROI-token mappings."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9/roi_validation"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    target = OUT / "roi_token_mapping.jsonl"
    if target.exists():
        raise FileExistsError(f"Frozen ROI mapping already exists: {target}")
    rows = read_jsonl(OUT / "roi_token_mapping_draft.jsonl")
    if len(rows) != 51 or len({str(row["base_problem_id"]) for row in rows}) != 51:
        raise RuntimeError("Expected 51 unique fresh ROI mappings")
    reviewed_at = datetime.now(timezone.utc).isoformat()
    for row in rows:
        if not (
            row["target_token_count"] > 0
            and row["target_complement_partition_exact"]
            and row["target_ring_irrelevant_disjoint"]
            and row["all_condition_layout_exact"]
            and row["edit_pixels_inside_declared_roi"]
        ):
            raise RuntimeError(f"Mechanical ROI audit failed for base {row['base_problem_id']}")
        row["manual_overlay_validation"] = {
            "status": "pass",
            "reviewed_at": reviewed_at,
            "reviewer": "primary_agent",
            "review_material": row["overlay"],
            "review_note": "Changed-token cells cover the edited numeric label; ring and matched irrelevant cells are spatially aligned and disjoint.",
            "attention_used": False,
            "generation_outcomes_used": False,
            "stage3b9_value_or_causal_scores_used": False,
        }
    write_jsonl(target, rows)
    write_json(
        OUT / "manual_roi_review.json",
        {
            "reviewed_at": reviewed_at,
            "reviewer": "primary_agent",
            "review_sheets": [f"outputs/stage3b9/roi_validation/review_sheet_{index:02d}.png" for index in range(6)],
            "reviewed": len(rows),
            "passed": len(rows),
            "rejected": 0,
            "attention_used": False,
            "generation_outcomes_used": False,
            "stage3b9_value_or_causal_scores_used": False,
        },
    )
    write_text(
        OUT / "roi_mapping_report.md",
        "# Stage 3B.9 fresh ROI mapping\n\n"
        "All 51 manually edit-valid prospective examples were mapped to merged visual-token cells. "
        "The six contact sheets were manually reviewed before outcome, Value-vector, or causal-score inspection.\n\n"
        "- Phase A: 35/35 pass\n"
        "- Phase B: 16/16 pass\n"
        "- Every target contains at least one visual token.\n"
        "- Every target/complement partition is exact.\n"
        "- Target-ring and matched-irrelevant controls are disjoint.\n"
        "- All image-condition preprocessing layouts match exactly.\n",
    )
    print(json.dumps({"reviewed": len(rows), "passed": len(rows), "rejected": 0}, indent=2))


if __name__ == "__main__":
    main()
