#!/usr/bin/env python3
"""Archive failed expansion-edit v1 renderings and build one prespecified v2 repair."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl, write_text
from visual_reasoning.stage3a.edits import build_text_conditions, validate_edit_conditions


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a"

# These corrections address only v1 box placement observed in side-by-side image
# review. They were fixed before expansion generation outcomes were available.
REPAIRS = {
    "1": {"roi": [151, 68, 198, 92], "font": 22, "reason": "v1 ROI erased small portions of both triangle sides"},
    "9": {"roi": [175, 225, 231, 255], "font": 22, "reason": "v1 ROI ended above the bottom of the source label, leaving a duplicate"},
    "10": {"roi": [126, 68, 166, 93], "font": 18, "reason": "v1 ROI erased triangle-side pixels around the apex label"},
    "14": {"roi": [61, 108, 114, 140], "font": 17, "reason": "v1 ROI was horizontally displaced and did not cover the source label"},
    "34": {"roi": [132, 111, 199, 144], "font": 21, "reason": "v1 ROI did not cover the lower source glyph pixels"},
    "45": {"roi": [159, 75, 206, 108], "font": 16, "reason": "v1 ROI did not cover the lower source glyph pixels"},
    "56": {"roi": [114, 72, 164, 106], "font": 18, "reason": "v1 ROI was horizontally displaced and left the source label"},
    "58": {"roi": [119, 41, 170, 74], "font": 18, "reason": "v1 ROI did not cover the lower source glyph pixels"},
    "61": {"roi": [71, 44, 120, 70], "font": 19, "reason": "v1 ROI overlapped the upper horizontal segment"},
    "62": {"roi": [170, 44, 231, 83], "font": 20, "reason": "v1 ROI did not cover all source degree-symbol pixels"},
    "65": {"roi": [131, 104, 208, 138], "font": 20, "reason": "v1 ROI was horizontally displaced and left source digits"},
    "66": {"roi": [163, 31, 242, 64], "font": 17, "reason": "v1 ROI was horizontally displaced and left source digits"},
}


def main() -> None:
    records = []
    repaired_at = datetime.now(timezone.utc).isoformat()
    for base, repair in REPAIRS.items():
        base_dir = OUT / "counterfactuals" / base
        version_dir = base_dir / "versions/v1"
        if version_dir.exists():
            raise FileExistsError(f"Archived v1 already exists: {version_dir}")
        version_dir.mkdir(parents=True)
        for name in ("original", "counterfactual", "sham", "edit_metadata.json", "validation.md", "manual_review_sheet.png"):
            source = base_dir / name
            if source.exists():
                shutil.move(str(source), str(version_dir / name))
        metadata = json.loads((version_dir / "edit_metadata.json").read_text(encoding="utf-8"))
        old_text = metadata["candidate_original"].strip().split(" is ")[-1].replace(" degrees", "°")
        new_text = metadata["candidate_counterfactual"].strip().split(" is ")[-1].replace(" degrees", "°")
        if base == "9":
            old_text, new_text = "6.0", "7.0"
        render_spec = {
            "roi_xyxy": repair["roi"],
            "original_text": old_text,
            "counterfactual_text": new_text,
            "font_size": repair["font"],
            "text_color": [0, 0, 0],
            "background_mode": "roi_bright_median",
            "text_anchor": [2, 1],
        }
        paths = build_text_conditions(Path(metadata["source_image"]), base_dir, render_spec)
        checks = validate_edit_conditions(paths, repair["roi"])
        if not checks["passed"]:
            raise RuntimeError(f"Automatic v2 validation failed for base {base}: {checks}")
        metadata["conditions"] = {name: str(path.relative_to(ROOT)) for name, path in paths.items()}
        metadata["target_evidence_roi_xyxy"] = repair["roi"]
        metadata["automatic_validation"] = checks
        metadata["manual_validation"] = {"status": "pending", "reviewer": None}
        metadata["construction_version"] = 2
        metadata["construction_history"] = [
            {
                "version": 1,
                "status": "failed_construction_review",
                "reason": repair["reason"],
                "archive": str(version_dir.relative_to(ROOT)),
            },
            {"version": 2, "status": "pending_manual_review", "built_at": repaired_at},
        ]
        write_json(base_dir / "edit_metadata.json", metadata)
        write_text(
            base_dir / "validation.md",
            f"# Edit Validation — base {base}, construction v2\n\n"
            "Automatic checks: **PASS**\n\nManual image review: **PENDING**\n\n"
            f"v1 was preserved at `{version_dir.relative_to(ROOT)}` because: {repair['reason']}.\n",
        )
        records.append(
            {
                "base_problem_id": base,
                "failed_version": 1,
                "repair_version": 2,
                "reason": repair["reason"],
                "model_outcomes_available_at_repair": False,
                "repaired_at": repaired_at,
            }
        )
    write_jsonl(OUT / "cohort/expansion_edit_repair_log.jsonl", records)
    print(json.dumps({"repaired_v2": sorted(REPAIRS), "outcomes_seen": False}, indent=2))


if __name__ == "__main__":
    main()
