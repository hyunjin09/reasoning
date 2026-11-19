#!/usr/bin/env python3
"""Construct frozen O/O-sham/C/C-sham controls for prospective validation."""

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
    "162": {"old": "40°", "new": "30°", "roi": [128, 72, 168, 102], "font": 18},
    "173": {"old": "50°", "new": "70°", "roi": [91, 70, 136, 106], "font": 20},
    "183": {"old": "2", "new": "4", "roi": [286, 428, 340, 486], "font": 52},
    "184": {"old": "2", "new": "1", "roi": [428, 188, 476, 246], "font": 52},
    "190": {"old": "50°", "new": "60°", "roi": [790, 298, 910, 378], "font": 68},
    "199": {"old": "24", "new": "10", "roi": [865, 692, 980, 780], "font": 72},
    "201": {"old": "28°", "new": "14°", "roi": [132, 167, 180, 201], "font": 18},
    "202": {"old": "38°", "new": "28°", "roi": [216, 107, 276, 145], "font": 25},
    "204": {"old": "10", "new": "6", "roi": [548, 296, 660, 366], "font": 58},
    "208": {"old": "55°", "new": "20°", "roi": [452, 448, 580, 525], "font": 68},
    "210": {"old": "5", "new": "4", "roi": [1162, 646, 1228, 724], "font": 64},
    "214": {"old": "32°", "new": "72°", "roi": [220, 48, 273, 82], "font": 17},
    "216": {"old": "3", "new": "2", "roi": [128, 65, 154, 95], "font": 17},
    "217": {"old": "20", "new": "18", "roi": [12, 67, 80, 106], "font": 26},
    "222": {"old": "32", "new": "2", "roi": [452, 151, 492, 185], "font": 20},
    "227": {"old": "16", "new": "8", "roi": [145, 173, 202, 207], "font": 22},
    "229": {"old": "54", "new": "22", "roi": [174, 14, 207, 42], "font": 14},
    "233": {"old": "70°", "new": "40°", "roi": [194, 124, 262, 171], "font": 31},
    "234": {"old": "108°", "new": "72°", "roi": [128, 114, 182, 142], "font": 15},
    "235": {"old": "110°", "new": "55°", "roi": [890, 245, 1055, 338], "font": 78},
    "237": {"old": "33°", "new": "12°", "roi": [458, 88, 528, 132], "font": 30},
    "241": {"old": "20", "new": "12", "roi": [170, 48, 214, 82], "font": 20},
    "246": {"old": "6.2", "new": "12", "roi": [86, 52, 142, 86], "font": 20},
    "252": {"old": "9", "new": "18", "roi": [740, 552, 805, 625], "font": 56},
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
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    target_root = OUT / "edit_validation"
    if target_root.exists() and any(target_root.iterdir()):
        if not args.resume:
            raise FileExistsError(f"Non-empty edit directory requires --resume: {target_root}")
    ensure_directory(target_root)
    screening = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(OUT / "candidate_screening.jsonl")
        if row["selected_for_prospective_generation"]
    }
    if set(screening) != set(SPECS):
        raise RuntimeError("Render specs do not exactly match the frozen generation screen")
    dataset = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    built_at = datetime.now(timezone.utc).isoformat()
    records = []
    for base, spec in SPECS.items():
        item = screening[base]
        source = resolve_image_path(args.dataset_root, str(dataset[str(item["example_id"])]["image"]))
        base_dir = target_root / base
        metadata_path = base_dir / "edit_metadata.json"
        if args.resume and metadata_path.is_file():
            records.append(json.loads(metadata_path.read_text(encoding="utf-8")))
            print(f"resumed completed base {base}", flush=True)
            continue
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
            "causal_scores_inspected": False,
        }
        write_json(metadata_path, metadata)
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
