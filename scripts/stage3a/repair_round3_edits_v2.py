#!/usr/bin/env python3
"""Archive failed round-3 v1 renders and apply one pre-outcome ROI correction."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage0.io import write_json, write_jsonl, write_text
from visual_reasoning.stage3a.edits import build_text_conditions, validate_edit_conditions


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a"


REPAIRS = {
    "78": {"roi": [51, 88, 86, 110], "font": 15},
    "79": {"roi": [213, 4, 240, 25], "font": 14},
    "87": {"roi": [120, 77, 153, 100], "font": 13},
    "89": {"roi": [177, 108, 207, 133], "font": 13},
    "92": {"roi": [111, 154, 135, 176], "font": 12},
    "93": {"roi": [75, 110, 111, 132], "font": 13},
    "94": {"roi": [193, 86, 207, 111], "font": 14},
    "98": {"roi": [80, 51, 104, 69], "font": 11},
    "99": {"roi": [76, 143, 108, 165], "font": 12},
    "100": {"roi": [91, 117, 114, 135], "font": 10},
    "103": {"roi": [72, 149, 108, 168], "font": 12},
    "106": {"roi": [33, 101, 69, 120], "font": 12},
    "113": {"roi": [141, 98, 173, 121], "font": 12},
    "115": {"roi": [114, 100, 157, 124], "font": 15},
    "116": {"roi": [214, 134, 244, 159], "font": 15},
    "118": {"roi": [166, 140, 198, 165], "font": 15},
    "120": {"roi": [70, 55, 82, 71], "font": 9},
    "124": {"roi": [5, 63, 21, 87], "font": 14},
    "127": {"roi": [205, 24, 234, 65], "font": 23},
    "128": {"roi": [104, 90, 153, 114], "font": 14},
    "129": {"roi": [62, 163, 82, 191], "font": 17},
    "130": {"roi": [95, 60, 137, 89], "font": 16},
}


def make_review_sheet(base_dir: Path) -> None:
    paths = [base_dir / condition / "image.png" for condition in ("original", "counterfactual", "sham")]
    images = [Image.open(path).convert("RGB") for path in paths]
    sheet = Image.new("RGB", (sum(image.width for image in images), max(image.height for image in images) + 30), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=16)
    x = 0
    for label, image in zip(("ORIGINAL", "COUNTERFACTUAL", "SHAM"), images):
        draw.text((x + 4, 5), label, fill="black", font=font)
        sheet.paste(image, (x, 30))
        x += image.width
    sheet.save(base_dir / "manual_review_sheet.png")


def main() -> None:
    repaired_at = datetime.now(timezone.utc).isoformat()
    records = []
    screen = {
        str(json.loads(line)["base_problem_id"]): json.loads(line)
        for line in (OUT / "cohort/round3_candidate_screening.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    for base, repair in REPAIRS.items():
        base_dir = OUT / "counterfactuals" / base
        archive = base_dir / "versions/v1"
        if archive.exists():
            raise FileExistsError(f"Round-3 v1 archive already exists: {archive}")
        archive.mkdir(parents=True)
        for name in ("original", "counterfactual", "sham", "edit_metadata.json", "validation.md", "manual_review_sheet.png"):
            source = base_dir / name
            if source.exists():
                shutil.move(str(source), str(archive / name))
        metadata = json.loads((archive / "edit_metadata.json").read_text(encoding="utf-8"))
        item = screen[base]
        old_text = metadata["edit_description"].split("render ", 1)[1].split(" (sham)", 1)[0].strip("'")
        new_text = metadata["edit_description"].split(" or ", 1)[1].split(" (counterfactual)", 1)[0].strip("'")
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
            raise RuntimeError(f"Automatic round-3 v2 validation failed for base {base}")
        metadata["conditions"] = {name: str(path.relative_to(ROOT)) for name, path in paths.items()}
        metadata["target_evidence_roi_xyxy"] = repair["roi"]
        metadata["automatic_validation"] = checks
        metadata["manual_validation"] = {"status": "pending", "reviewer": None}
        metadata["construction_version"] = 2
        metadata["construction_history"] = [
            {
                "version": 1,
                "status": "failed_construction_review",
                "reason": "The first-pass ROI did not fully remove the source glyph or displaced the replacement.",
                "archive": str(archive.relative_to(ROOT)),
                "model_outcomes_available": False,
            },
            {"version": 2, "status": "pending_manual_review", "built_at": repaired_at},
        ]
        metadata["semantic_validity_basis"] = item["semantic_validity_basis"]
        write_json(base_dir / "edit_metadata.json", metadata)
        write_text(
            base_dir / "validation.md",
            f"# Edit Validation — base {base}, construction v2\n\nAutomatic checks: **PASS**\n\nManual review: **PENDING**\n\n"
            f"The failed v1 is preserved at `{archive.relative_to(ROOT)}`. No round-3 model outcome existed at repair time.\n",
        )
        make_review_sheet(base_dir)
        records.append(
            {
                "base_problem_id": base,
                "failed_version": 1,
                "repair_version": 2,
                "reason": "residual or displaced source glyph in v1 manual review",
                "model_outcomes_available_at_repair": False,
                "repaired_at": repaired_at,
            }
        )
    write_jsonl(OUT / "cohort/round3_edit_repair_log.jsonl", records)
    print(json.dumps({"repaired_v2": len(records), "model_outcomes_seen": False}, indent=2))


if __name__ == "__main__":
    main()
