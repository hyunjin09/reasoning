#!/usr/bin/env python3
"""Create lossless labeled sheets for manual screening of frozen expansion images."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "outputs/stage3a/cohort/candidate_screening.jsonl"
OUTPUT = ROOT / "outputs/stage3a/cohort/expansion_review_sheets"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--per-sheet", type=int, default=4)
    args = parser.parse_args()
    rows = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    candidates = [row for row in read_jsonl(MANIFEST) if row["source"] == "prospective_unseen_expansion"]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default(size=18)
    for page_start in range(0, len(candidates), args.per_sheet):
        page = candidates[page_start : page_start + args.per_sheet]
        images = []
        labels = []
        for item in page:
            source = resolve_image_path(args.dataset_root, str(rows[str(item["example_id"])]["image"]))
            images.append(Image.open(source).convert("RGB"))
            labels.append(
                f"base {item['base_problem_id']} / ex {item['example_id']} | "
                f"{item['localized_fact']} -> {item['counterfactual_fact']}"
            )
        width = max(image.width for image in images)
        block_heights = [image.height + 44 for image in images]
        sheet = Image.new("RGB", (width, sum(block_heights)), "white")
        draw = ImageDraw.Draw(sheet)
        y = 0
        for image, label, block_height in zip(images, labels, block_heights):
            draw.text((4, y + 4), label, fill="black", font=font)
            sheet.paste(image, (0, y + 36))
            y += block_height
        page_index = page_start // args.per_sheet
        path = OUTPUT / f"sheet_{page_index:02d}.png"
        sheet.save(path)
        print(path)


if __name__ == "__main__":
    main()
