#!/usr/bin/env python3
"""Create coordinate-grid overlays for Stage 3C.9 manual edit specification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pool", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--target", type=Path, default=OUT / "cohort/coordinate_review")
    parser.add_argument("--step", type=int, default=25)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    args = parse_args()
    target = args.target.resolve()
    target.relative_to(OUT.resolve())
    target.mkdir(parents=True, exist_ok=True)
    items = read_jsonl(args.pool.resolve())
    dataset = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    font = ImageFont.load_default(size=10)
    for item in items:
        base = str(item["base_problem_id"])
        row = dataset[str(item["example_id"])]
        source = resolve_image_path(args.dataset_root, str(row["image"]))
        with Image.open(source) as opened:
            source_image = opened.convert("RGBA")
        overlay = Image.new("RGBA", source_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        for x in range(0, source_image.width, int(args.step)):
            draw.line((x, 0, x, source_image.height), fill=(220, 40, 40, 90), width=1)
            draw.text((x + 1, 1), str(x), fill=(180, 0, 0, 230), font=font)
        for y in range(0, source_image.height, int(args.step)):
            draw.line((0, y, source_image.width, y), fill=(40, 80, 220, 90), width=1)
            draw.text((1, y + 1), str(y), fill=(0, 40, 180, 230), font=font)
        composed = Image.alpha_composite(source_image, overlay).convert("RGB")
        scale = max(2, min(4, 900 // max(source_image.width, source_image.height)))
        composed.resize(
            (source_image.width * scale, source_image.height * scale),
            Image.Resampling.NEAREST,
        ).save(target / f"{base}.png")
    print(json.dumps({"created": len(items), "target": str(target.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
