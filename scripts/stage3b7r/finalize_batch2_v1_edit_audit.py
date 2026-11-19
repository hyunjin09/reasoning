#!/usr/bin/env python3
"""Freeze the manual four-image audit for Stage 3B.7R batch 2 v1."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
EDIT_ROOT = ROOT / "outputs/stage3b7r/validation_cohort/edit_validation_batch2"

PASS = {
    "265": "The complete angle expression is replaced cleanly; all line and angle geometry remains intact.",
    "267": "The isolated arc label is replaced cleanly; circle, chords, and all unrelated content remain intact.",
}

REJECT = {
    "255": "ROI undercoverage leaves residual original label content; expanding it would risk the adjacent slanted segment.",
    "257": "ROI undercoverage leaves the original 5 visible beside the rerendered label; eligible for a geometry-safe v2 ROI.",
    "261": "ROI intersects the rhombus side and leaves a line-end artifact before the rerendered label.",
    "262": "ROI erases a task-relevant segment of the upper trapezoid base.",
    "264": "ROI includes and erases part of the angle arc; eligible for a lower, text-only v2 ROI.",
    "268": "ROI is shifted right of the original digit, leaving the old 5 visible; eligible for a text-only v2 ROI.",
    "271": "ROI alters the callout-arrow endpoint and leaves a visual artifact before the expression.",
    "277": "ROI intersects the radius segment and leaves a line-end artifact before the label.",
    "278": "ROI is shifted right of the original digit, leaving the old 8 visible; eligible for a text-only v2 ROI.",
    "280": "ROI leaves the original x visible and intersects the nearby diagonal.",
    "282": "ROI begins inside the original 14, leaving a residual digit; eligible for a text-only v2 ROI.",
    "283": "ROI begins inside the original 24, leaving a residual digit; eligible for a text-only v2 ROI.",
    "284": "ROI targets the equality ticks rather than the expression digit; a wider repair would overlap line geometry.",
    "287": "ROI begins inside the original 52-degree label, leaving a residual digit; eligible for a text-only v2 ROI.",
    "288": "ROI leaves the semantic angle-number label 3 attached to the rerender and intersects the diagonal endpoint.",
    "289": "ROI erases a segment of side PT beneath the label.",
    "290": "ROI begins inside the original 123-degree label; a safe expansion is blocked by the adjacent transversal.",
    "292": "ROI begins inside the original 70-degree label, leaving it visible; eligible for a text-only v2 ROI.",
    "293": "ROI leaves the original 7 visible and creates a mismatched rectangular background over the filled rhombus.",
    "294": "ROI leaves the original 30-degree label visible and intersects the diagonal.",
    "296": "ROI begins inside the original 11, leaving a residual digit; eligible for a text-only v2 ROI.",
    "297": "ROI begins inside the original 123-degree label, leaving a residual digit; eligible for a text-only v2 ROI.",
    "299": "ROI begins inside the original 20, leaving a residual digit; eligible for a text-only v2 ROI.",
}


def main() -> None:
    expected = {path.name for path in EDIT_ROOT.iterdir() if path.is_dir()}
    decided = set(PASS) | set(REJECT)
    if expected != decided:
        raise RuntimeError(f"Audit mismatch: missing={sorted(expected-decided)} extra={sorted(decided-expected)}")
    audited_at = datetime.now(timezone.utc).isoformat()
    records, exclusions, valid = [], [], []
    for base in sorted(decided, key=int):
        metadata_path = EDIT_ROOT / base / "edit_metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        passed = base in PASS
        rationale = (PASS if passed else REJECT)[base]
        metadata["manual_validation"] = {
            "status": "pass" if passed else "reject",
            "reviewer": "primary_agent_visual_audit",
            "audited_at": audited_at,
            "rationale": rationale,
            "audit_blinding": {
                "prospective_generation_inspected": False,
                "causal_scores_inspected": False,
                "attention_used": False,
            },
        }
        write_json(metadata_path, metadata)
        write_text(
            EDIT_ROOT / base / "validation.md",
            f"# Four-image validation — base {base} (batch 2 v1)\n\n"
            "Automatic pixel validation: **PASS**\n\n"
            f"Manual review: **{'PASS' if passed else 'REJECT'}**\n\n{rationale}\n\n"
            "The decision was frozen before prospective generation and causal scoring; attention was not used.\n",
        )
        record = {
            "base_problem_id": base,
            "example_id": metadata["example_id"],
            "edit_version": "batch2_v1",
            "manual_edit_status": "pass" if passed else "reject",
            "rationale": rationale,
            "audited_at": audited_at,
            "prospective_generation_inspected": False,
            "causal_scores_inspected": False,
            "selection_used_attention": False,
        }
        records.append(record)
        if passed:
            valid.append({
                "base_problem_id": base,
                "example_id": metadata["example_id"],
                "edit_metadata": str(metadata_path.relative_to(ROOT)),
                "selection_stage": "batch2_v1_manual_edit_pass",
            })
        else:
            exclusions.append({**record, "exclusion_stage": "manual_four_image_validation"})
    write_jsonl(EDIT_ROOT / "manual_validation_manifest.jsonl", records)
    write_jsonl(EDIT_ROOT / "manual_edit_exclusions.jsonl", exclusions)
    write_jsonl(EDIT_ROOT / "manual_valid_generation_manifest.jsonl", valid)
    print(json.dumps({"audited": len(records), "pass": len(PASS), "reject": len(REJECT)}, indent=2))


if __name__ == "__main__":
    main()
