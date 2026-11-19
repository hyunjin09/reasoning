#!/usr/bin/env python3
"""Freeze the manual Stage 3B.7 ROI overlay review before causal scoring."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b7/roi_audit"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> None:
    mapping_path = OUT / "roi_token_mapping.jsonl"
    irrelevant_path = OUT / "irrelevant_roi_manifest.jsonl"
    rows = read_jsonl(mapping_path)
    controls = read_jsonl(irrelevant_path)
    if len(rows) != 45 or len(controls) != 45:
        raise RuntimeError("Manual audit requires all 45 validation+primary mappings")
    if any(row["manual_overlay_validation"]["status"] != "pending" for row in rows):
        raise RuntimeError("ROI audit was already finalized")
    reviewed_at = datetime.now(timezone.utc).isoformat()
    review = {
        "status": "pass",
        "reviewer": "primary research agent",
        "reviewed_at": reviewed_at,
        "review_scope": "all 45 validation+primary overlays across review_sheet_00 through review_sheet_04",
        "checks": {
            "target_tokens_cover_exact_edited_label_support": True,
            "fixed_ring_matches_grid_geometry": True,
            "irrelevant_tokens_are_disjoint_blank_or_low_ink_regions": True,
            "irrelevant_tokens_avoid_obvious_task_relevant_labels_or_marks": True,
            "target_complement_partition_is_exact": True,
            "four_condition_preprocessing_layout_is_exact": True,
        },
        "causal_scores_available": False,
        "selection_used_attention": False,
        "overrides_applied": False,
    }
    for row in rows:
        row["manual_overlay_validation"] = review
    for row in controls:
        row["manual_status"] = "pass"
        row["manual_reviewed_at"] = reviewed_at
        row["manual_review_note"] = (
            "Disjoint blank/low-ink matched control with no obvious task-relevant label or mark"
        )
        row["causal_scores_available"] = False
    write_jsonl(mapping_path, rows)
    write_jsonl(irrelevant_path, controls)
    (OUT / "roi_mapping_report.md").write_text(
        "# Stage 3B.7 ROI mapping audit\n\n"
        "Status: **PASS**.\n\n"
        "All 45 mappings (8 validation and 37 primary) reproduce identical four-condition "
        "processor layouts. `V_target` is the merged-token support of the union of exact "
        "Stage 3A edit pixels; `V_other` is its exact visual complement; the secondary ring "
        "uses a frozen one-cell Chebyshev radius. Every matched irrelevant region has the "
        "same token count as its target and is disjoint from target+ring.\n\n"
        "The primary research agent manually inspected review sheets 00--04 before any "
        "Stage 3B.7 causal score existed. Target overlays cover the edited labels, and "
        "irrelevant controls occupy blank/low-ink regions without another obvious "
        "task-relevant label or mark. No mapping override was applied.\n\n"
        "A localized pixel edit can influence nonlocal visual states through the vision "
        "encoder. These mappings localize LM-interface visual-token source positions, not "
        "raw-pixel information or a vision-encoder feature.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
