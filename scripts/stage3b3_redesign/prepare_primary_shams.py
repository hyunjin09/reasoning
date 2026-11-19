#!/usr/bin/env python3
"""Construct paired controls for the 37 authorized numeric primary bases."""

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
CONDITIONS = ("O", "O_sham", "C", "C_sham")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def make_review_sheet(base_dir: Path, roi: list[int]) -> Path:
    images = [Image.open(base_dir / condition / "image.png").convert("RGB") for condition in CONDITIONS]
    header, gap, scale = 30, 10, 5
    crops = [image.crop(tuple(roi)).resize(
        ((roi[2] - roi[0]) * scale, (roi[3] - roi[1]) * scale), Image.Resampling.NEAREST
    ) for image in images]
    full_width = sum(image.width for image in images) + gap * 3
    crop_width = sum(image.width for image in crops) + gap * 3
    full_height = max(image.height for image in images)
    crop_height = max(image.height for image in crops)
    sheet = Image.new("RGB", (max(full_width, crop_width), header * 2 + full_height + crop_height), "white")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default(size=16)
    except TypeError:
        font = ImageFont.load_default()
    x = 0
    for label, image in zip(CONDITIONS, images):
        draw.text((x + 3, 5), label, fill="black", font=font)
        sheet.paste(image, (x, header))
        x += image.width + gap
    crop_y = header + full_height
    x = 0
    for label, crop in zip(CONDITIONS, crops):
        draw.text((x + 3, crop_y + 5), f"{label} ROI x{scale}", fill="black", font=font)
        sheet.paste(crop, (x, crop_y + header))
        x += crop.width + gap
    path = base_dir / "four_image_review_sheet.png"
    sheet.save(path)
    for image in images + crops:
        image.close()
    return path


def main() -> None:
    decision = json.loads((OUT / "validation/validation_decision.json").read_text(encoding="utf-8"))
    if decision["decision"] != "PASS" or not decision["restoration_in_primary"]:
        raise RuntimeError("Primary paired controls require a validation PASS with restoration")
    manifest = [
        row for row in read_jsonl(OUT / "primary/primary_41_manifest.jsonl")
        if row["edit_tier"] == "tier1_local_numeric_label"
    ]
    if len(manifest) != 37:
        raise RuntimeError("Expected 37 numeric primary bases")
    specs = json.loads((OUT / "config/primary_render_specs.json").read_text(encoding="utf-8"))
    if set(specs) != {str(row["base_problem_id"]) for row in manifest}:
        raise RuntimeError("Primary render specs do not exactly cover the numeric primary cohort")
    target_root = OUT / "counterfactual_shams"
    existing = [str(row["base_problem_id"]) for row in manifest if (target_root / str(row["base_problem_id"])).exists()]
    if existing:
        raise FileExistsError(f"Refusing to overwrite primary paired controls: {existing}")
    built_at = datetime.now(timezone.utc).isoformat()
    records = []
    for item in manifest:
        base = str(item["base_problem_id"])
        spec = dict(specs[base])
        description_old, description_new = extract_rendered_texts(item["edit_description"])
        old_text = str(spec.get("original_text_override", description_old))
        new_text = str(spec.get("counterfactual_text_override", description_new))
        roi = [int(value) for value in item["target_evidence_roi_xyxy"]]
        base_dir = target_root / base
        paths = {condition: base_dir / condition / "image.png" for condition in CONDITIONS}
        for path in paths.values():
            ensure_directory(path.parent)
        sources = {
            "O": ROOT / item["conditions"]["original"],
            "O_sham": ROOT / item["conditions"]["sham"],
            "C": ROOT / item["conditions"]["counterfactual"],
        }
        for condition, source in sources.items():
            shutil.copy2(source, paths[condition])
        render_spec = {
            "roi_xyxy": roi,
            "counterfactual_text": new_text,
            "font_size": int(spec["font_size"]),
            "text_color": spec["text_color"],
        }
        if spec["background_mode"] is None:
            render_spec["background_color"] = spec["background_color"]
        else:
            render_spec["background_mode"] = spec["background_mode"]
        build_counterfactual_sham(
            sources["O"], paths["C_sham"], render_spec,
            anchor=spec["counterfactual_sham_anchor"],
        )
        checks = validate_four_image_conditions(paths, roi)
        if not checks["passed"]:
            raise RuntimeError(f"Automatic four-image validation failed for primary base {base}: {checks}")
        review_sheet = make_review_sheet(base_dir, roi)
        metadata = {
            "base_problem_id": base,
            "primary_cohort": True,
            "built_at": built_at,
            "semantic_classes": {
                "O": item["original_fact"], "O_sham": item["original_fact"],
                "C": item["counterfactual_fact"], "C_sham": item["counterfactual_fact"],
            },
            "rendered_text": {"O_sham": old_text, "C": new_text, "C_sham": new_text},
            "paths": {name: str(path.relative_to(ROOT)) for name, path in paths.items()},
            "construction": {
                "renderer": "visual_reasoning.stage3a.edits._render",
                "source_for_C_sham": str(sources["O"].relative_to(ROOT)),
                "same_roi": roi,
                "same_font_size": int(spec["font_size"]),
                "C_anchor": spec["text_anchor"],
                "C_sham_anchor": spec["counterfactual_sham_anchor"],
                "source_spec": spec["source_spec"],
                "independent_rerender": True,
                "derived_from_C_pixels": False,
            },
            "automatic_validation": checks,
            "manual_validation": {"status": "pending", "reviewer": None},
            "review_sheet": str(review_sheet.relative_to(ROOT)),
            "constructed_after_validation_PASS": True,
            "primary_scores_available_during_construction": False,
        }
        write_json(base_dir / "edit_metadata.json", metadata)
        write_text(
            base_dir / "validation.md",
            f"# Primary four-image validation — base {base}\n\n"
            "Automatic pixel validation: **PASS**\n\nManual semantic/legibility review: **PENDING**\n",
        )
        records.append(metadata)
    write_jsonl(OUT / "counterfactual_shams/primary_construction_manifest.jsonl", records)
    print(json.dumps({"built": len(records), "automatic_pass": len(records), "manual_pending": len(records)}, indent=2))


if __name__ == "__main__":
    main()
