#!/usr/bin/env python3
"""Freeze the manual four-image audit for Stage 3B.7R batch 1.

The decisions below were made from the four-image review sheets before any
prospective generation or causal score was produced.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
EDIT_ROOT = ROOT / "outputs/stage3b7r/validation_cohort/edit_validation"


PASS = {
    "183": "Isolated radius label is legible in all four conditions; circle geometry and all unrelated content are unchanged.",
    "184": "Isolated radius label is legible in all four conditions; bracket and unrelated task geometry remain intact.",
    "199": "Isolated chord-length label is legible in all four conditions; chord and unrelated geometry remain intact.",
    "208": "Isolated angle label is legible in all four conditions; angle geometry and unrelated content remain intact.",
    "214": "Isolated angle label is legible in all four conditions; surrounding line geometry and unrelated content remain intact.",
    "235": "Isolated angle label is legible in all four conditions; surrounding geometry and unrelated content remain intact.",
}


REJECT = {
    "162": "Edit ROI erases part of the slanted angle/line geometry, leaving a visible gap.",
    "173": "Edit ROI erases the radial line/angle geometry.",
    "190": "Edit ROI overlaps and erases the angle arc.",
    "201": "Edit ROI erases a segment of the circle boundary.",
    "202": "Edit ROI erases horizontal/diagonal line segments.",
    "204": "Original label 10 remains visible and the rendered value is a duplicate rather than a replacement.",
    "210": "Original label 5 remains visible and the rendered value is a duplicate rather than a replacement.",
    "216": "Original label 3 remains visible and the rendered value is a duplicate rather than a replacement.",
    "217": "Rendered conditions remove the explicit cm unit and leave a remnant, so semantic presentation is not matched.",
    "222": "Original label 32 remains visible and the rendered value overlaps as a duplicate.",
    "227": "A partial original digit remains, producing an ambiguous combined label.",
    "229": "Original label 54 remains visible and the rendered value is a duplicate rather than a replacement.",
    "233": "Edit ROI erases a triangle side and leaves part of the original label.",
    "234": "A partial original 10 remains, producing an ambiguous combined label.",
    "237": "Edit ROI overlaps the slanted line and leaves residual label content, producing malformed text.",
    "241": "Edit ROI overlaps the hypotenuse and leaves residual label content, producing malformed text.",
    "246": "Rendered conditions change the displayed unit from cm to m; the intervention is not target-value-only.",
    "252": "Original label 9 remains visible and the rendered value is displaced as a duplicate.",
}


def main() -> None:
    expected = {path.name for path in EDIT_ROOT.iterdir() if path.is_dir()}
    decided = set(PASS) | set(REJECT)
    if expected != decided:
        raise RuntimeError(f"Audit mismatch: missing={sorted(expected-decided)} extra={sorted(decided-expected)}")
    if set(PASS) & set(REJECT):
        raise RuntimeError("A base cannot both pass and fail")

    audited_at = datetime.now(timezone.utc).isoformat()
    records: list[dict] = []
    exclusions: list[dict] = []
    valid_generation: list[dict] = []
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
            "\n".join(
                [
                    f"# Four-image validation — base {base}",
                    "",
                    "Automatic pixel validation: **PASS**",
                    "",
                    f"Manual review: **{'PASS' if passed else 'REJECT'}**",
                    "",
                    rationale,
                    "",
                    "The decision was frozen before prospective generation and causal scoring; attention was not used.",
                    "",
                ]
            ),
        )
        record = {
            "base_problem_id": base,
            "example_id": metadata["example_id"],
            "manual_edit_status": "pass" if passed else "reject",
            "rationale": rationale,
            "audited_at": audited_at,
            "prospective_generation_inspected": False,
            "causal_scores_inspected": False,
            "selection_used_attention": False,
        }
        records.append(record)
        if passed:
            valid_generation.append(
                {
                    "base_problem_id": base,
                    "example_id": metadata["example_id"],
                    "edit_metadata": str(metadata_path.relative_to(ROOT)),
                    "selection_stage": "batch1_manual_edit_pass",
                }
            )
        else:
            exclusions.append({**record, "exclusion_stage": "manual_four_image_validation"})

    write_jsonl(EDIT_ROOT / "manual_validation_manifest.jsonl", records)
    write_jsonl(EDIT_ROOT / "manual_edit_exclusions.jsonl", exclusions)
    write_jsonl(EDIT_ROOT / "manual_valid_generation_manifest.jsonl", valid_generation)
    print(json.dumps({"audited": len(records), "pass": len(PASS), "reject": len(REJECT)}, indent=2))


if __name__ == "__main__":
    main()
