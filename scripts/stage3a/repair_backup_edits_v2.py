#!/usr/bin/env python3
"""Archive failed backup v1 placement and build one pre-outcome v2 correction."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl, write_text
from visual_reasoning.stage3a.edits import build_text_conditions, validate_edit_conditions


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a"
REPAIRS = {
    "72": {"old": "=16", "new": "=12", "roi": [190, 17, 250, 46], "font": 18, "reason": "v1 covered only the right edge of the equation value"},
    "74": {"old": "115°", "new": "105°", "roi": [72, 84, 157, 119], "font": 20, "reason": "v1 missed the leading source digits"},
    "75": {"old": "42°", "new": "34°", "roi": [52, 0, 105, 34], "font": 20, "reason": "v1 ROI was horizontally displaced from the source label"},
    "77": {"old": "60°", "new": "50°", "roi": [46, 67, 100, 103], "font": 20, "reason": "v1 ROI was horizontally displaced from the source label"},
}


def main() -> None:
    repaired_at = datetime.now(timezone.utc).isoformat()
    records = []
    for base, spec in REPAIRS.items():
        base_dir = OUT / "counterfactuals" / base
        archive = base_dir / "versions/v1"
        archive.mkdir(parents=True)
        for name in ("original", "counterfactual", "sham", "edit_metadata.json", "validation.md", "manual_review_sheet.png"):
            source = base_dir / name
            if source.exists():
                shutil.move(str(source), str(archive / name))
        metadata = json.loads((archive / "edit_metadata.json").read_text(encoding="utf-8"))
        render_spec = {
            "roi_xyxy": spec["roi"],
            "original_text": spec["old"],
            "counterfactual_text": spec["new"],
            "font_size": spec["font"],
            "text_color": [0, 0, 0],
            "background_mode": "roi_bright_median",
            "text_anchor": [2, 1],
        }
        paths = build_text_conditions(Path(metadata["source_image"]), base_dir, render_spec)
        checks = validate_edit_conditions(paths, spec["roi"])
        if not checks["passed"]:
            raise RuntimeError(f"Automatic backup v2 check failed for {base}: {checks}")
        metadata["conditions"] = {name: str(path.relative_to(ROOT)) for name, path in paths.items()}
        metadata["target_evidence_roi_xyxy"] = spec["roi"]
        metadata["automatic_validation"] = checks
        metadata["manual_validation"] = {"status": "pending", "reviewer": None}
        metadata["construction_version"] = 2
        metadata["construction_history"] = [
            {"version": 1, "status": "failed_construction_review", "reason": spec["reason"], "archive": str(archive.relative_to(ROOT))},
            {"version": 2, "status": "pending_manual_review", "built_at": repaired_at},
        ]
        write_json(base_dir / "edit_metadata.json", metadata)
        write_text(base_dir / "validation.md", f"# Edit Validation — base {base}, construction v2\n\nAutomatic checks: **PASS**\n\nManual review: **PENDING**\n")
        records.append({"base_problem_id": base, "failed_version": 1, "repair_version": 2, "reason": spec["reason"], "model_outcomes_available_at_repair": False, "repaired_at": repaired_at})
    write_jsonl(OUT / "cohort/backup_edit_repair_log.jsonl", records)
    print(json.dumps({"repaired": sorted(REPAIRS), "outcomes_seen": False}, indent=2))


if __name__ == "__main__":
    main()
