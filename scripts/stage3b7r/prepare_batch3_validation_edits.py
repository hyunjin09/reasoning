#!/usr/bin/env python3
"""Construct O/O-sham/C/C-sham edits for frozen Stage 3B.7-R batch 3."""

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
    "302": {"old": "8", "new": "16", "roi": [70, 190, 120, 235], "font": 32},
    "303": {"old": "(3x + 40)°", "new": "(3x + 36)°", "roi": [690, 160, 875, 215], "font": 29},
    "309": {"old": "x + 9", "new": "x + 6", "roi": [48, 140, 115, 175], "font": 24},
    "312": {"old": "36°", "new": "40°", "roi": [78, 88, 124, 123], "font": 23},
    "314": {"old": "80°", "new": "120°", "roi": [42, 145, 115, 177], "font": 22},
    "319": {"old": "36", "new": "72", "roi": [103, 200, 137, 232], "font": 24, "color": [0, 90, 160]},
    "322": {"old": "2x + 2", "new": "2x + 0", "roi": [150, 78, 270, 122], "font": 31},
    "324": {"old": "6 cm", "new": "3 cm", "roi": [80, 38, 140, 68], "font": 22},
    "325": {"old": "45°", "new": "30°", "roi": [275, 135, 325, 165], "font": 22},
    "326": {"old": "7 ft", "new": "14 ft", "roi": [120, 86, 177, 118], "font": 22},
    "332": {"old": "50°", "new": "40°", "roi": [160, 107, 200, 132], "font": 17},
    "334": {"old": "28°", "new": "38°", "roi": [238, 204, 270, 224], "font": 14},
    "335": {"old": "32°", "new": "42°", "roi": [143, 243, 176, 262], "font": 14},
    "336": {"old": "31°", "new": "41°", "roi": [147, 118, 180, 137], "font": 14},
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def render(source: Path, destination: Path, *, text: str, spec: dict, anchor: list[int]) -> None:
    ensure_directory(destination.parent)
    render_spec = {
        "roi_xyxy": spec["roi"],
        "background_mode": "roi_bright_median",
        "text_color": spec.get("color", [0, 0, 0]),
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
    target_root = OUT / "edit_validation_batch3_v3"
    if target_root.exists() and any(target_root.iterdir()):
        raise FileExistsError(f"Batch 3 edit directory is already non-empty: {target_root}")
    ensure_directory(target_root)
    screening = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(OUT / "candidate_screening_batch3.jsonl")
        if row["selected_for_contingency_edit_validation"]
    }
    if set(screening) != set(SPECS):
        raise RuntimeError("Render specs do not exactly match the frozen batch 3 screen")
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
            "batch": 3,
            "edit_version": 3,
            "supersedes": str((OUT / "edit_validation_batch3_v2" / base).relative_to(ROOT)),
            "repair_reason": "Used exact connected-component label bounding boxes after v2 failed manual alignment; no generation or causal outcomes existed for these bases.",
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
            f"# Four-image validation — base {base} (batch 3)\n\nAutomatic pixel validation: **PASS**\n\nManual review: **PENDING**\n",
        )
        records.append(metadata)
        print(f"built base {base}", flush=True)
    write_jsonl(target_root / "construction_manifest.jsonl", records)
    print(json.dumps({"built": len(records), "automatic_pass": len(records), "manual_pending": len(records)}, indent=2))


if __name__ == "__main__":
    main()
