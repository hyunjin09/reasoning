#!/usr/bin/env python3
"""Render blind coordinate guides and a contact sheet for bases 775--788."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage0.io import ensure_directory


ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path("/data/dataset/MathVerse/images/images_version_5")
OUT = ROOT / "outputs/stage3b9/phase_a_shared/blind_expansion_screen"
BASES = tuple(range(775, 789))


def main() -> None:
    ensure_directory(OUT / "guides")
    font = ImageFont.load_default(size=13)
    label_font = ImageFont.load_default(size=18)
    thumbnails = []
    for base in BASES:
        with Image.open(SOURCE / f"image_{base}.png") as opened:
            image = opened.convert("RGB")
        border = 32
        guide = Image.new("RGB", (image.width + border, image.height + border), "white")
        guide.paste(image, (border, border))
        draw = ImageDraw.Draw(guide)
        for x in range(0, image.width + 1, 20):
            px = x + border
            draw.line((px, border, px, image.height + border - 1), fill=(255, 175, 175), width=1)
            draw.text((px + 1, 2), str(x), fill=(160, 0, 0), font=font)
        for y in range(0, image.height + 1, 20):
            py = y + border
            draw.line((border, py, image.width + border - 1, py), fill=(255, 175, 175), width=1)
            draw.text((1, py + 1), str(y), fill=(160, 0, 0), font=font)
        guide.save(OUT / "guides" / f"base_{base}.png")
        thumb = image.copy()
        thumb.thumbnail((360, 260))
        cell = Image.new("RGB", (390, 310), "white")
        cell.paste(thumb, ((390 - thumb.width) // 2, 35 + (260 - thumb.height) // 2))
        ImageDraw.Draw(cell).text((12, 8), f"base {base}", fill="black", font=label_font)
        thumbnails.append(cell)
    sheet = Image.new("RGB", (4 * 390, 4 * 310), (230, 230, 230))
    for index, thumbnail in enumerate(thumbnails):
        sheet.paste(thumbnail, ((index % 4) * 390, (index // 4) * 310))
    sheet.save(OUT / "contact_sheet.png")
    print(f"wrote {len(BASES)} guides and contact sheet to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
