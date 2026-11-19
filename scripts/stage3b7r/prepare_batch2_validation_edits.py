#!/usr/bin/env python3
"""Construct O/O-sham/C/C-sham edits for frozen Stage 3B.7R batch 2."""

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
OUT = ROOT / "outputs/stage3b7r/validation_cohort"
CONDITIONS = ("O", "O_sham", "C", "C_sham")


SPECS = {
    "255": {"old": "14.9", "new": "22.4", "roi": [530, 1210, 700, 1320], "font": 78},
    "257": {"old": "5", "new": "4", "roi": [1260, 1225, 1360, 1310], "font": 68},
    "261": {"old": "10", "new": "35", "roi": [695, 315, 790, 395], "font": 54},
    "262": {"old": "22 ft", "new": "21 ft", "roi": [87, 2, 165, 38], "font": 20},
    "264": {"old": "20x", "new": "30x", "roi": [438, 158, 520, 205], "font": 30},
    "265": {"old": "2x + 23", "new": "2x + 5", "roi": [238, 270, 390, 310], "font": 32},
    "267": {"old": "122°", "new": "58°", "roi": [240, 40, 345, 85], "font": 34},
    "268": {"old": "5", "new": "6", "roi": [222, 75, 248, 108], "font": 18},
    "271": {"old": "7x - 44", "new": "7x - 28", "roi": [775, 248, 946, 300], "font": 32},
    "277": {"old": "10", "new": "5", "roi": [350, 195, 415, 240], "font": 34},
    "278": {"old": "8", "new": "4", "roi": [292, 385, 335, 430], "font": 32},
    "280": {"old": "x + 4", "new": "x + 0", "roi": [175, 48, 280, 90], "font": 26},
    "282": {"old": "14", "new": "7", "roi": [430, 52, 491, 98], "font": 32},
    "283": {"old": "24", "new": "16", "roi": [210, 183, 272, 220], "font": 27},
    "284": {"old": "3", "new": "0", "roi": [98, 113, 121, 146], "font": 17},
    "287": {"old": "52°", "new": "25°", "roi": [300, 52, 376, 103], "font": 35},
    "288": {"old": "39°", "new": "42°", "roi": [342, 355, 422, 405], "font": 35},
    "289": {"old": "15", "new": "12.5", "roi": [410, 185, 515, 250], "font": 32},
    "290": {"old": "123°", "new": "133°", "roi": [165, 78, 250, 125], "font": 32},
    "292": {"old": "70°", "new": "20°", "roi": [280, 42, 330, 83], "font": 24},
    "293": {"old": "7 ft", "new": "14 ft", "roi": [160, 112, 220, 150], "font": 17},
    "294": {"old": "30°", "new": "80°", "roi": [247, 150, 305, 183], "font": 20},
    "296": {"old": "11", "new": "15", "roi": [276, 35, 336, 78], "font": 30},
    "297": {"old": "123°", "new": "113°", "roi": [135, 425, 215, 470], "font": 28},
    "299": {"old": "20", "new": "10", "roi": [318, 35, 380, 73], "font": 30},
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def render(source: Path, destination: Path, *, text: str, spec: dict, anchor: list[int]) -> None:
    ensure_directory(destination.parent)
    render_spec = {
        "roi_xyxy": spec["roi"],
        "background_mode": "roi_bright_median",
        "text_color": [0, 0, 0],
        "font_size": spec["font"],
        "text_anchor": anchor,
    }
    with Image.open(source) as image:
        _render(image.convert("RGB"), text, render_spec).save(destination)


def make_review_sheet(base_dir: Path, roi: list[int]) -> Path:
    originals = [Image.open(base_dir / condition / "image.png").convert("RGB") for condition in CONDITIONS]
    full = []
    for image in originals:
        scale = min(1.0, 500 / image.width, 500 / image.height)
        full.append(image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale)))))
    crop_scale = min(6, max(2, 420 // max(roi[2] - roi[0], roi[3] - roi[1])))
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
    target_root = OUT / "edit_validation_batch2"
    if target_root.exists() and any(target_root.iterdir()):
        raise FileExistsError(f"Batch 2 edit directory is already non-empty: {target_root}")
    ensure_directory(target_root)
    screening = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(OUT / "candidate_screening_batch2.jsonl")
        if row["selected_for_prospective_generation"]
    }
    if set(screening) != set(SPECS):
        raise RuntimeError("Render specs do not exactly match the frozen batch 2 screen")
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
            "causal_scores_inspected": False,
        }
        write_json(base_dir / "edit_metadata.json", metadata)
        write_text(
            base_dir / "validation.md",
            f"# Four-image validation — base {base} (batch 2)\n\nAutomatic pixel validation: **PASS**\n\nManual review: **PENDING**\n",
        )
        records.append(metadata)
        print(f"built base {base}", flush=True)
    write_jsonl(target_root / "construction_manifest.jsonl", records)
    print(json.dumps({"built": len(records), "automatic_pass": len(records), "manual_pending": len(records)}, indent=2))


if __name__ == "__main__":
    main()
