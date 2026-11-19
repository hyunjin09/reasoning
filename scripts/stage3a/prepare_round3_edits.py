#!/usr/bin/env python3
"""Build outcome-blind C0/C1/C2 edits for the frozen Stage 3A round-3 screen."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path
from visual_reasoning.stage0.io import write_json, write_jsonl, write_text
from visual_reasoning.stage3a.edits import build_text_conditions, validate_edit_conditions


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a"


# Tight numeric-label ROIs were selected from coordinate-grid copies before any
# round-3 generation existed. They intentionally exclude nearby geometry where
# possible; all triplets remain pending lossless manual review.
SPECS = {
    "78": {"old": "70°", "new": "40°", "roi": [56, 77, 111, 104], "font": 19},
    "79": {"old": "32", "new": "20", "roi": [232, 1, 267, 29], "font": 18},
    "80": {"old": "5", "new": "9", "roi": [18, 63, 43, 93], "font": 20},
    "83": {"old": "100°", "new": "120°", "roi": [68, 83, 128, 112], "font": 18},
    "87": {"old": "50°", "new": "20°", "roi": [141, 77, 186, 106], "font": 17},
    "89": {"old": "25°", "new": "35°", "roi": [185, 105, 233, 133], "font": 16},
    "92": {"old": "34°", "new": "29°", "roi": [119, 145, 166, 176], "font": 16},
    "93": {"old": "40°", "new": "35°", "roi": [87, 101, 133, 130], "font": 16},
    "94": {"old": "6", "new": "3", "roi": [221, 88, 235, 114], "font": 16},
    "96": {"old": "40°", "new": "100°", "roi": [83, 135, 132, 166], "font": 16},
    "98": {"old": "50°", "new": "40°", "roi": [108, 46, 142, 72], "font": 13},
    "99": {"old": "26°", "new": "36°", "roi": [101, 140, 147, 170], "font": 16},
    "100": {"old": "30°", "new": "40°", "roi": [111, 108, 143, 137], "font": 14},
    "101": {"old": "126°", "new": "106°", "roi": [83, 142, 145, 172], "font": 16},
    "103": {"old": "130°", "new": "125°", "roi": [87, 139, 148, 170], "font": 16},
    "106": {"old": "136°", "new": "108°", "roi": [54, 91, 114, 122], "font": 16},
    "107": {"old": "130°", "new": "120°", "roi": [90, 99, 153, 129], "font": 16},
    "109": {"old": "130°", "new": "120°", "roi": [17, 13, 70, 42], "font": 15},
    "113": {"old": "110°", "new": "90°", "roi": [158, 93, 214, 124], "font": 16},
    "115": {"old": "120°", "new": "90°", "roi": [119, 94, 184, 127], "font": 18},
    "116": {"old": "12", "new": "5", "roi": [232, 129, 276, 161], "font": 19},
    "118": {"old": "10", "new": "8", "roi": [191, 126, 235, 160], "font": 19},
    "120": {"old": "4", "new": "3", "roi": [99, 46, 113, 70], "font": 11},
    "124": {"old": "1", "new": "2", "roi": [24, 61, 39, 84], "font": 15},
    "125": {"old": "30", "new": "15", "roi": [51, 43, 94, 72], "font": 17},
    "126": {"old": "10", "new": "16", "roi": [65, 47, 108, 80], "font": 18},
    "127": {"old": "1", "new": "2", "roi": [238, 47, 261, 73], "font": 21},
    "128": {"old": "120°", "new": "90°", "roi": [117, 85, 184, 117], "font": 18},
    "129": {"old": "5", "new": "3", "roi": [90, 162, 116, 191], "font": 18},
    "130": {"old": "45°", "new": "30°", "roi": [122, 56, 181, 89], "font": 19},
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    args = parser.parse_args()
    dataset = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    candidates = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(OUT / "cohort/round3_candidate_screening.jsonl")
    }
    if set(candidates) != set(SPECS):
        raise RuntimeError("Round-3 edit specs do not exactly cover the frozen screen")
    drafts = []
    for base, spec in SPECS.items():
        item = candidates[base]
        example = str(item["example_id"])
        row = dataset[example]
        target = OUT / "counterfactuals" / base
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite counterfactual base {base}")
        source = resolve_image_path(args.dataset_root, str(row["image"]))
        render_spec = {
            "roi_xyxy": spec["roi"],
            "original_text": spec["old"],
            "counterfactual_text": spec["new"],
            "font_size": spec["font"],
            "text_color": [0, 0, 0],
            "background_mode": "roi_bright_median",
            "text_anchor": [2, 1],
        }
        paths = build_text_conditions(source, target, render_spec)
        checks = validate_edit_conditions(paths, spec["roi"])
        if not checks["passed"]:
            raise RuntimeError(f"Automatic edit validation failed for base {base}: {checks}")
        metadata = {
            "base_problem_id": base,
            "example_id": example,
            "variant": "Vision Dominant",
            "source_image": str(source),
            "conditions": {name: str(path.relative_to(ROOT)) for name, path in paths.items()},
            "target_evidence_roi_xyxy": spec["roi"],
            "original_fact": item["localized_fact"],
            "counterfactual_fact": item["counterfactual_fact"],
            "counterfactual_expected_answer": item["counterfactual_expected_answer"],
            "edit_description": f"mask only the frozen numeric-label ROI and render {spec['old']!r} (sham) or {spec['new']!r} (counterfactual) with one shared renderer",
            "edit_tier": "tier1_local_numeric_label",
            "sham_control": "same ROI mask, inferred local background, typography, and renderer retaining the original semantic fact",
            "irrelevant_control": None,
            "irrelevant_control_omission_reason": "No equally isolated and task-irrelevant local label was prospectively guaranteed; C2 is the mandatory artifact control.",
            "automatic_validation": checks,
            "manual_validation": {"status": "pending", "reviewer": None},
            "event": None,
            "candidate_original": " " + item["localized_fact"],
            "candidate_counterfactual": " " + item["counterfactual_fact"],
            "prefix_token_ids": None,
            "prefix_rule": "pending completed-correct generation and strict manual E0 audit",
            "selection_used_attention": False,
            "selection_and_edit_frozen_before_generation_outcome": True,
            "expansion_round": 3,
        }
        write_json(target / "edit_metadata.json", metadata)
        write_text(target / "validation.md", f"# Edit Validation — base {base}\n\nAutomatic checks: **PASS**\n\nManual review: **PENDING**\n")
        make_review_sheet(target)
        drafts.append(metadata)
    write_jsonl(OUT / "cohort/round3_edit_draft.jsonl", drafts)
    print(json.dumps({"built": len(drafts), "manual_validation_pending": len(drafts)}, indent=2))


if __name__ == "__main__":
    main()
