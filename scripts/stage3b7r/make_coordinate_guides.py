#!/usr/bin/env python3
"""Create coordinate-grid copies for frozen Stage 3B.7-R edit candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCREEN = ROOT / "outputs/stage3b7r/validation_cohort/prospective_generation_manifest.jsonl"
DEFAULT_OUT = ROOT / "outputs/stage3b7r/validation_cohort/coordinate_guides"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_SCREEN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    rows = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    candidates = [json.loads(line) for line in args.manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default(size=13)
    border = 32
    for item in candidates:
        source = resolve_image_path(args.dataset_root, str(rows[str(item["example_id"])]["image"]))
        image = Image.open(source).convert("RGB")
        canvas = Image.new("RGB", (image.width + border, image.height + border), "white")
        canvas.paste(image, (border, border))
        draw = ImageDraw.Draw(canvas)
        for x in range(0, image.width + 1, 20):
            px = x + border
            draw.line((px, border, px, image.height + border - 1), fill=(255, 175, 175), width=1)
            draw.text((px + 1, 2), str(x), fill=(160, 0, 0), font=font)
        for y in range(0, image.height + 1, 20):
            py = y + border
            draw.line((border, py, image.width + border - 1, py), fill=(255, 175, 175), width=1)
            draw.text((1, py + 1), str(y), fill=(160, 0, 0), font=font)
        canvas.save(args.output_dir / f"base_{item['base_problem_id']}_example_{item['example_id']}.png")
    print(f"wrote {len(candidates)} coordinate guides to {args.output_dir}")


if __name__ == "__main__":
    main()
