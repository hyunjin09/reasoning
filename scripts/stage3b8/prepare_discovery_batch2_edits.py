#!/usr/bin/env python3
"""Construct four-condition local edits for frozen Stage 3B.8 batch 2."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text
from visual_reasoning.stage3a.edits import _render
from visual_reasoning.stage3b3_redesign.images import validate_four_image_conditions


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b8/discovery_cohort"
CONDITIONS = ("O", "O_sham", "C", "C_sham")


SPECS = {
    "361": {"old": "29 m", "new": "39 m", "roi": [44, 222, 92, 244], "font": 18},
    "362": {"old": "12 m", "new": "18 m", "roi": [290, 137, 334, 160], "font": 17},
    "363": {"old": "13 m", "new": "10 m", "roi": [0, 86, 40, 109], "font": 16},
    "364": {"old": "35.5 m", "new": "45.5 m", "roi": [234, 136, 295, 164], "font": 15},
    "365": {"old": "10369 m", "new": "12000 m", "roi": [284, 136, 366, 163], "font": 15},
    "366": {"old": "37 m", "new": "40 m", "roi": [80, 117, 122, 140], "font": 16},
    "367": {"old": "10.6 m", "new": "12 m", "roi": [151, 231, 220, 252], "font": 16},
    "371": {"old": "11", "new": "8", "roi": [0, 51, 21, 72], "font": 15},
    "373": {"old": "8.5", "new": "6", "roi": [3, 78, 32, 94], "font": 14},
    "377": {"old": "9", "new": "12", "roi": [95, 104, 121, 126], "font": 14},
    "379": {"old": "8", "new": "6", "roi": [292, 64, 310, 81], "font": 14},
    "387": {"old": "8 cm", "new": "12 cm", "roi": [265, 168, 342, 198], "font": 25},
    "389": {"old": "13 cm", "new": "16 cm", "roi": [184, 120, 255, 149], "font": 25},
    "390": {"old": "44 cm", "new": "66 cm", "roi": [265, 69, 338, 98], "font": 25},
    "392": {"old": "10 mm", "new": "12 mm", "roi": [149, 232, 225, 261], "font": 22},
    "393": {"old": "6 cm", "new": "8 cm", "roi": [246, 168, 308, 197], "font": 25},
    "394": {"old": "2 cm", "new": "4 cm", "roi": [306, 119, 362, 148], "font": 25},
    "395": {"old": "3 cm", "new": "5 cm", "roi": [264, 162, 326, 192], "font": 25},
    "396": {"old": "11 cm", "new": "7 cm", "roi": [258, 169, 330, 198], "font": 25},
    "397": {"old": "50 cm", "new": "25 cm", "roi": [286, 161, 360, 191], "font": 25},
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def render(source: Path, destination: Path, *, text: str, spec: dict, anchor: list[int]) -> None:
    ensure_directory(destination.parent)
    with Image.open(source) as image:
        _render(
            image.convert("RGB"),
            text,
            {
                "roi_xyxy": spec["roi"],
                "background_mode": "roi_bright_median",
                "text_color": [0, 0, 0],
                "font_size": spec["font"],
                "text_anchor": anchor,
            },
        ).save(destination)


def make_review_sheet(base_dir: Path, roi: list[int]) -> Path:
    originals = [Image.open(base_dir / condition / "image.png").convert("RGB") for condition in CONDITIONS]
    full = []
    for image in originals:
        scale = min(1.0, 500 / image.width, 500 / image.height)
        full.append(image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale)))))
    crop_scale = min(7, max(2, 460 // max(roi[2] - roi[0], roi[3] - roi[1])))
    crops = [
        image.crop(tuple(roi)).resize(
            ((roi[2] - roi[0]) * crop_scale, (roi[3] - roi[1]) * crop_scale),
            Image.Resampling.NEAREST,
        )
        for image in originals
    ]
    gap, header = 8, 28
    width = max(sum(image.width for image in full) + 3 * gap, sum(image.width for image in crops) + 3 * gap)
    height = header + max(image.height for image in full) + header + max(image.height for image in crops)
    sheet = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=16)
    x = 0
    for label, image in zip(CONDITIONS, full):
        draw.text((x + 2, 4), label, fill="black", font=font)
        sheet.paste(image, (x, header))
        x += image.width + gap
    y = header + max(image.height for image in full)
    x = 0
    for label, image in zip(CONDITIONS, crops):
        draw.text((x + 2, y + 4), f"{label} ROI x{crop_scale}", fill="black", font=font)
        sheet.paste(image, (x, y + header))
        x += image.width + gap
    target = base_dir / "four_image_review_sheet.png"
    sheet.save(target)
    for image in originals + full + crops:
        image.close()
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    args = parser.parse_args()
    target_root = OUT / "edit_validation/batch2_v4"
    if target_root.exists() and any(target_root.iterdir()):
        raise FileExistsError(f"Batch-2 edit directory is nonempty: {target_root}")
    ensure_directory(target_root)
    screening = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(OUT / "candidate_screening_batch2.jsonl")
        if row["selected_for_edit_validation"]
    }
    if set(screening) != set(SPECS):
        raise RuntimeError("Render specs do not exactly match the frozen screen")
    dataset = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    built_at = datetime.now(timezone.utc).isoformat()
    records = []
    for base, spec in SPECS.items():
        item = screening[base]
        source = resolve_image_path(args.dataset_root, str(dataset[str(item["example_id"])]["image"]))
        base_dir = target_root / base
        paths = {condition: base_dir / condition / "image.png" for condition in CONDITIONS}
        ensure_directory(paths["O"].parent)
        shutil.copy2(source, paths["O"])
        render(source, paths["O_sham"], text=spec["old"], spec=spec, anchor=[2, 1])
        render(source, paths["C"], text=spec["new"], spec=spec, anchor=[2, 1])
        render(source, paths["C_sham"], text=spec["new"], spec=spec, anchor=[3, 1])
        checks = validate_four_image_conditions(paths, spec["roi"])
        if not checks["passed"]:
            raise RuntimeError(f"Automatic four-image validation failed for base {base}: {checks}")
        sheet = make_review_sheet(base_dir, spec["roi"])
        metadata = {
            "base_problem_id": base,
            "example_id": item["example_id"],
            "batch": 2,
            "edit_version": 4,
            "supersedes": str((OUT / "edit_validation/batch2_v3" / base).relative_to(ROOT)),
            "repair_reason": "v3 passed target alignment; manual review found three ROIs with avoidable adjacent-line inclusion, so v4 tightens bases 371/373/379 before any generation or causal outcome was inspected",
            "built_at": built_at,
            "semantic_classes": {
                "O": item["original_fact"],
                "O_sham": item["original_fact"],
                "C": item["counterfactual_fact"],
                "C_sham": item["counterfactual_fact"],
            },
            "rendered_text": {"O_sham": spec["old"], "C": spec["new"], "C_sham": spec["new"]},
            "paths": {name: str(path.relative_to(ROOT)) for name, path in paths.items()},
            "target_evidence_roi_xyxy": spec["roi"],
            "counterfactual_expected_answer": item["counterfactual_expected_answer"],
            "semantic_validity_basis": item["semantic_validity_basis"],
            "construction": {
                "renderer": "visual_reasoning.stage3a.edits._render",
                "same_source_image": str(source),
                "same_roi": spec["roi"],
                "same_font_size": spec["font"],
                "O_sham_and_C_anchor": [2, 1],
                "C_sham_anchor": [3, 1],
                "independent_rerender": True,
                "derived_from_C_pixels": False,
            },
            "automatic_validation": checks,
            "manual_validation": {"status": "pending", "reviewer": None},
            "review_sheet": str(sheet.relative_to(ROOT)),
            "selection_used_attention": False,
            "generation_outcome_inspected": False,
            "stage3b8_outcomes_inspected": False,
        }
        write_json(base_dir / "edit_metadata.json", metadata)
        write_text(
            base_dir / "validation.md",
            f"# Four-image validation — base {base}\n\nAutomatic pixel validation: **PASS**\n\nManual review: **PENDING**\n",
        )
        records.append(metadata)
        print(f"built base {base}", flush=True)
    write_jsonl(target_root / "construction_manifest.jsonl", records)
    print(json.dumps({"built": len(records), "automatic_pass": len(records), "manual_pending": len(records)}, indent=2))


if __name__ == "__main__":
    main()
