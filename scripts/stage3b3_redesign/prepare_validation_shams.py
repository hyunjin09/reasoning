#!/usr/bin/env python3
"""Construct paired O/O_sham/C/C_sham controls for the frozen validation split."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text
from visual_reasoning.stage3b3_redesign.images import (
    build_counterfactual_sham,
    extract_rendered_texts,
    validate_four_image_conditions,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b3_redesign"
CONDITION_NAMES = ("O", "O_sham", "C", "C_sham")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def make_review_sheet(base_dir: Path, roi: list[int]) -> Path:
    paths = [base_dir / condition / "image.png" for condition in CONDITION_NAMES]
    images = [Image.open(path).convert("RGB") for path in paths]
    header = 30
    gap = 10
    crop_scale = 5
    crops = [image.crop(tuple(roi)).resize(
        ((roi[2] - roi[0]) * crop_scale, (roi[3] - roi[1]) * crop_scale),
        Image.Resampling.NEAREST,
    ) for image in images]
    full_width = sum(image.width for image in images) + gap * (len(images) - 1)
    crop_width = sum(crop.width for crop in crops) + gap * (len(crops) - 1)
    full_height = max(image.height for image in images)
    crop_height = max(crop.height for crop in crops)
    sheet = Image.new("RGB", (max(full_width, crop_width), header + full_height + header + crop_height), "white")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default(size=16)
    except TypeError:
        font = ImageFont.load_default()
    x = 0
    for label, image in zip(CONDITION_NAMES, images):
        draw.text((x + 3, 5), label, fill="black", font=font)
        sheet.paste(image, (x, header))
        x += image.width + gap
    crop_y = header + full_height
    x = 0
    for label, crop in zip(CONDITION_NAMES, crops):
        draw.text((x + 3, crop_y + 5), f"{label} ROI x{crop_scale}", fill="black", font=font)
        sheet.paste(crop, (x, crop_y + header))
        x += crop.width + gap
    target = base_dir / "four_image_review_sheet.png"
    sheet.save(target)
    for image in images + crops:
        image.close()
    return target


def main() -> None:
    target_root = OUT / "counterfactual_shams"
    if target_root.exists() and any(target_root.iterdir()):
        raise FileExistsError(f"Refusing to overwrite paired controls: {target_root}")
    ensure_directory(target_root)
    manifest = read_jsonl(OUT / "config/validation_manifest.jsonl")
    specs = json.loads((OUT / "config/validation_render_specs.json").read_text(encoding="utf-8"))
    built_at = datetime.now(timezone.utc).isoformat()
    records = []
    for item in manifest:
        base = str(item["base_problem_id"])
        if item["edit_tier"] != "tier1_local_numeric_label":
            raise RuntimeError(f"Validation base {base} is not a numeric-label edit")
        old_text, new_text = extract_rendered_texts(item["edit_description"])
        spec = dict(specs[base])
        roi = [int(value) for value in item["target_evidence_roi_xyxy"]]
        if spec["roi_xyxy"] != roi:
            raise RuntimeError(f"Frozen ROI mismatch for base {base}")
        base_dir = target_root / base
        paths = {condition: base_dir / condition / "image.png" for condition in CONDITION_NAMES}
        for path in paths.values():
            ensure_directory(path.parent)
        source_paths = {
            "O": ROOT / item["conditions"]["original"],
            "O_sham": ROOT / item["conditions"]["sham"],
            "C": ROOT / item["conditions"]["counterfactual"],
        }
        for condition, source in source_paths.items():
            shutil.copy2(source, paths[condition])
        render_spec = {
            "roi_xyxy": roi,
            "counterfactual_text": new_text,
            "font_size": int(spec["font_size"]),
            "text_color": spec["text_color"],
            "text_anchor": spec["text_anchor"],
        }
        if spec["background_mode"] is None:
            render_spec["background_color"] = spec["background_color"]
        else:
            render_spec["background_mode"] = spec["background_mode"]
        build_counterfactual_sham(
            source_paths["O"], paths["C_sham"], render_spec,
            anchor=spec["counterfactual_sham_anchor"],
        )
        checks = validate_four_image_conditions(paths, roi)
        if not checks["passed"]:
            raise RuntimeError(f"Automatic four-image validation failed for base {base}: {checks}")
        review_sheet = make_review_sheet(base_dir, roi)
        metadata = {
            "base_problem_id": base,
            "built_at": built_at,
            "source_stage3a_metadata": f"outputs/stage3a/counterfactuals/{base}/edit_metadata.json",
            "semantic_classes": {
                "O": item["original_fact"],
                "O_sham": item["original_fact"],
                "C": item["counterfactual_fact"],
                "C_sham": item["counterfactual_fact"],
            },
            "rendered_text": {"O_sham": old_text, "C": new_text, "C_sham": new_text},
            "paths": {name: str(path.relative_to(ROOT)) for name, path in paths.items()},
            "construction": {
                "renderer": "visual_reasoning.stage3a.edits._render",
                "source_for_C_sham": str(source_paths["O"].relative_to(ROOT)),
                "same_roi": roi,
                "same_font_size": int(spec["font_size"]),
                "C_anchor": spec["text_anchor"],
                "C_sham_anchor": spec["counterfactual_sham_anchor"],
                "independent_rerender": True,
                "derived_from_C_pixels": False,
            },
            "automatic_validation": checks,
            "manual_validation": {"status": "pending", "reviewer": None},
            "review_sheet": str(review_sheet.relative_to(ROOT)),
        }
        write_json(base_dir / "edit_metadata.json", metadata)
        write_text(
            base_dir / "validation.md",
            f"# Four-image validation — base {base}\n\n"
            f"Automatic pixel validation: **PASS**\n\nManual semantic/legibility review: **PENDING**\n",
        )
        records.append(metadata)
    write_jsonl(OUT / "counterfactual_shams/construction_manifest.jsonl", records)
    print(json.dumps({"built": len(records), "automatic_pass": len(records), "manual_pending": len(records)}, indent=2))


if __name__ == "__main__":
    main()
