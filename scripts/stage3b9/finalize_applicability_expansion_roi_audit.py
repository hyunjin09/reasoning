#!/usr/bin/env python3
"""Freeze manually reviewed ROI mappings and append them without altering v1 maps."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / "outputs/stage3b9"
OUT = STAGE / "roi_validation_applicability_expansion_v2"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    frozen_path = OUT / "roi_token_mapping.jsonl"
    combined_path = STAGE / "roi_validation/roi_token_mapping_all_fresh_v2.jsonl"
    phase_a_path = STAGE / "config/phase_a_scoring/phase_a_roi_mapping_all_fresh_v2.jsonl"
    if any(path.exists() for path in (frozen_path, combined_path, phase_a_path)):
        raise FileExistsError("Applicability-expansion ROI outputs are already frozen")
    rows = read_jsonl(OUT / "roi_token_mapping_draft.jsonl")
    if len(rows) != 7 or len({str(row["base_problem_id"]) for row in rows}) != 7:
        raise RuntimeError("Expected seven unique applicability-expansion mappings")
    reviewed_at = datetime.now(timezone.utc).isoformat()
    for row in rows:
        if not (row["target_token_count"] > 0 and row["target_complement_partition_exact"] and row["target_ring_irrelevant_disjoint"] and row["all_condition_layout_exact"] and row["edit_pixels_inside_declared_roi"]):
            raise RuntimeError(f"Mechanical ROI validation failed for base {row['base_problem_id']}")
        row["manual_overlay_validation"] = {
            "status": "pass", "reviewed_at": reviewed_at, "reviewer": "Codex primary agent",
            "review_material": row["overlay"],
            "review_note": "Changed-token cells cover the validated numeric edit; ring and matched irrelevant cells are aligned and disjoint. No attention or new-base causal outcome was used.",
            "attention_used": False, "generation_outcomes_used": False,
            "stage3b9_value_or_causal_scores_used": False,
        }
    write_jsonl(frozen_path, rows)
    initial = read_jsonl(STAGE / "roi_validation/roi_token_mapping_all_fresh.jsonl")
    combined = sorted([*initial, *rows], key=lambda row: int(row["base_problem_id"]))
    if len(initial) != 76 or len(combined) != 83 or len({str(row["base_problem_id"]) for row in combined}) != 83:
        raise RuntimeError("Combined fresh ROI mapping count/identity mismatch")
    write_jsonl(combined_path, combined)
    phase_a = []
    for row in combined:
        if row["phase"] == "phase_a":
            row["four_condition_layout_exact"] = bool(row["all_condition_layout_exact"])
            phase_a.append(row)
    if len(phase_a) != 61:
        raise RuntimeError(f"Expected 61 Phase-A mappings, found {len(phase_a)}")
    write_jsonl(phase_a_path, phase_a)
    write_json(OUT / "manual_roi_review.json", {
        "reviewed_at": reviewed_at, "reviewer": "Codex primary agent",
        "review_sheets": ["outputs/stage3b9/roi_validation_applicability_expansion_v2/review_sheet_00.png"],
        "reviewed": 7, "passed": 7, "rejected": 0,
        "attention_used": False, "generation_outcomes_used": False,
        "stage3b9_value_or_causal_scores_used": False,
        "combined_mapping": str(combined_path.relative_to(ROOT)),
        "combined_mapping_sha256": hashlib.sha256(combined_path.read_bytes()).hexdigest(),
    })
    write_text(OUT / "roi_mapping_report.md", "# Stage 3B.9 applicability-expansion ROI mapping\n\nAll seven edit-valid candidates passed manual overlay review before generation and new-base Value/projection scoring. Target/complement partitions and condition layouts are exact. Attention was not used.\n")
    print(json.dumps({"reviewed": 7, "combined_mappings": len(combined), "phase_a_mappings": len(phase_a)}, indent=2))


if __name__ == "__main__":
    main()
