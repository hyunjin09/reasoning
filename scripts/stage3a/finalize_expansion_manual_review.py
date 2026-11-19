#!/usr/bin/env python3
"""Record the lossless side-by-side manual review of expansion image edits."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a"

PASSES = {"2", "3", "5", "6", "9", "16", "20", "22", "24", "31", "32", "38", "40", "48", "53", "54", "55", "60", "67"}
REJECTIONS = {
    "1": "The target label lies between the triangle sides; the v2 mask still leaves visible line gaps.",
    "10": "The apex label overlaps both triangle sides; the v2 sham and target retain visible line gaps.",
    "14": "The corrected label ROI removes task-relevant radial/chord pixels inside the target angle.",
    "29": "The numeric label is too close to side AC; masking it removes a visible segment and leaves a spurious glyph.",
    "34": "The label overlaps the slanted geometry and the redraw leaves a visible line discontinuity.",
    "45": "The label overlaps the task-relevant chord near C, producing a visible discontinuity.",
    "56": "The target label overlaps the vertical diameter and triangle side; v2 removes both line segments.",
    "58": "The target label overlaps the top horizontal and diagonal lines; v2 visibly removes both.",
    "61": "The label sits immediately under the upper side; v2 still leaves a visible top-line gap.",
    "62": "The label overlays segment AB on a gray background; v2 removes a task-relevant portion of AB.",
    "65": "The source label/arrow overlaps the lower parallel line and nearby angle labels; the edit damages them.",
    "66": "The source label touches segment AB and point B; the edit removes task-relevant line/label pixels.",
}


def main() -> None:
    if PASSES & set(REJECTIONS):
        raise RuntimeError("Pass/reject decisions overlap")
    all_bases = PASSES | set(REJECTIONS)
    exclusions = []
    for base in sorted(all_bases, key=int):
        base_dir = OUT / "counterfactuals" / base
        metadata_path = base_dir / "edit_metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if base in PASSES:
            metadata["manual_validation"] = {
                "status": "pass",
                "reviewer": "Stage 3A primary-agent lossless side-by-side inspection",
                "checks": [
                    "target fact changed exactly as intended",
                    "sham retained the original fact",
                    "unrelated task-relevant content unchanged",
                    "replacement label legible",
                    "no accidental occlusion observed",
                    "dimensions unchanged",
                    "counterfactual remains logically interpretable",
                ],
            }
            outcome = "**PASS**"
            reason = "All seven manual edit checks passed. Generation eligibility and E0 annotation remain pending."
        else:
            reject_reason = REJECTIONS[base]
            metadata["manual_validation"] = {
                "status": "reject",
                "reviewer": "Stage 3A primary-agent lossless side-by-side inspection",
                "reason": reject_reason,
            }
            exclusions.append(
                {
                    "base_problem_id": base,
                    "example_id": metadata["example_id"],
                    "stage": "manual_edit_validation",
                    "reason": reject_reason,
                }
            )
            outcome = "**REJECT**"
            reason = reject_reason
        write_json(metadata_path, metadata)
        version = metadata.get("construction_version", 1)
        write_text(
            base_dir / "validation.md",
            f"# Edit Validation — base {base}, construction v{version}\n\n"
            "Automatic containment/dimension checks: **PASS**\n\n"
            f"Manual lossless side-by-side review: {outcome}\n\nReason: {reason}\n",
        )
    write_jsonl(OUT / "cohort/expansion_manual_edit_exclusions.jsonl", exclusions)
    print(json.dumps({"passed": len(PASSES), "rejected": len(REJECTIONS), "pass_bases": sorted(PASSES, key=int)}, indent=2))


if __name__ == "__main__":
    main()
