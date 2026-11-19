#!/usr/bin/env python3
"""Render coordinate guides for the frozen Stage 3B.9 prospective screen."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path
from visual_reasoning.stage0.io import ensure_directory


ROOT = Path(__file__).resolve().parents[2]
DATASET = Path("/data/dataset/MathVerse")
CONFIG = ROOT / "outputs/stage3b9/config/prospective_cohort_screen.json"
OUT = ROOT / "outputs/stage3b9/screening/coordinate_guides"


def main() -> None:
    payload = json.loads(CONFIG.read_text(encoding="utf-8"))
    candidates = [*payload["phase_a_screen"], *payload["phase_b_screen"]]
    rows = {str(row["sample_index"]): row for row in load_mathverse_rows(DATASET)}
    ensure_directory(OUT)
    font = ImageFont.load_default(size=13)
    border = 32
    for item in candidates:
        source = resolve_image_path(DATASET, str(rows[str(item["example_id"])]["image"]))
        with Image.open(source) as opened:
            image = opened.convert("RGB")
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
        canvas.save(OUT / f"base_{item['base_problem_id']}_example_{item['example_id']}.png")
    print(json.dumps({"guides": len(candidates), "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
