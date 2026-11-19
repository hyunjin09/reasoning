#!/usr/bin/env python3
"""Create lossless side-by-side sheets for manual Stage 3A edit review."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counterfactual-root", type=Path, required=True)
    args = parser.parse_args()
    for base_dir in sorted((path for path in args.counterfactual_root.iterdir() if path.is_dir()), key=lambda p: int(p.name)):
        paths = [base_dir / condition / "image.png" for condition in ("original", "counterfactual", "sham")]
        if not all(path.is_file() for path in paths):
            continue
        images = [Image.open(path).convert("RGB") for path in paths]
        width = sum(image.width for image in images)
        height = max(image.height for image in images) + 30
        sheet = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(sheet)
        font = ImageFont.load_default(size=16)
        x = 0
        for label, image in zip(("ORIGINAL", "COUNTERFACTUAL", "SHAM"), images):
            draw.text((x + 4, 5), label, fill="black", font=font)
            sheet.paste(image, (x, 30))
            x += image.width
        sheet.save(base_dir / "manual_review_sheet.png")
        print(base_dir / "manual_review_sheet.png")


if __name__ == "__main__":
    main()

