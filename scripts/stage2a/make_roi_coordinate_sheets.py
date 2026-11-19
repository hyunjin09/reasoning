#!/usr/bin/env python3
"""Create coordinate-grid sheets for attention-blind manual ROI annotation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


DEFAULT_IDS = [
    "594", "699", "739", "764", "774", "2749", "2799", "2824",
    "2834", "2869", "2874", "2894", "2969", "3044", "3069", "3074",
    "3079", "3084", "3839", "3939",
]


def annotate(image: Image.Image, example_id: str) -> Image.Image:
    im = image.convert("RGB")
    draw = ImageDraw.Draw(im)
    step = 25 if max(im.size) < 400 else 50
    for x in range(0, im.width, step):
        draw.line((x, 0, x, im.height), fill=(255, 0, 0), width=1)
        draw.text((x + 2, 2), str(x), fill=(180, 0, 0))
    for y in range(0, im.height, step):
        draw.line((0, y, im.width, y), fill=(255, 0, 0), width=1)
        draw.text((2, y + 2), str(y), fill=(180, 0, 0))
    header = Image.new("RGB", (im.width, 24), "white")
    ImageDraw.Draw(header).text((4, 4), f"example {example_id} | {im.width}x{im.height}", fill="black")
    out = Image.new("RGB", (im.width, im.height + 24), "white")
    out.paste(header, (0, 0))
    out.paste(im, (0, 24))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="outputs/stage1/discovery/cohort_manifest.jsonl")
    parser.add_argument("--output-dir", default="outputs/stage2a/evidence_subset/screening/coordinates")
    parser.add_argument("--ids", nargs="*", default=DEFAULT_IDS)
    args = parser.parse_args()

    wanted = set(args.ids)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for line in Path(args.manifest).read_text().splitlines():
        row = json.loads(line)
        eid = str(row["example_id"])
        if eid not in wanted:
            continue
        input_path = Path(row["example_view"]) / "input.json"
        item = json.loads(input_path.read_text())
        image = Image.open(item["resolved_image_path"])
        annotate(image, eid).save(output_dir / f"{eid}_coordinates.png")


if __name__ == "__main__":
    main()
