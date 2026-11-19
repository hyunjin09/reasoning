#!/usr/bin/env python3
"""Make coordinate guides for the score-blind Stage 3B.9 expansion screen."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage0.io import ensure_directory


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9/screening/expansion_guides"
BASES = (643, 644, 729, 731, 732, 733, 735, 736, 737, 738, 739, 742, 746, 747, 748, 749, 750, 751, 756, 759, 761, 771, 773, 774, 730, 734, 740, 741, 744, 745, 753, 754, 758, 762)


def main() -> None:
    ensure_directory(OUT)
    font = ImageFont.load_default(size=13)
    border = 32
    for base in BASES:
        source = Path(f"/data/dataset/MathVerse/images/images_version_5/image_{base}.png")
        with Image.open(source) as opened:
            image = opened.convert("RGB")
        canvas = Image.new("RGB", (image.width + border, image.height + border), "white")
        canvas.paste(image, (border, border))
        draw = ImageDraw.Draw(canvas)
        for x in range(0, image.width + 1, 20):
            px = x + border; draw.line((px, border, px, image.height + border - 1), fill=(255, 175, 175), width=1); draw.text((px + 1, 2), str(x), fill=(160, 0, 0), font=font)
        for y in range(0, image.height + 1, 20):
            py = y + border; draw.line((border, py, image.width + border - 1, py), fill=(255, 175, 175), width=1); draw.text((1, py + 1), str(y), fill=(160, 0, 0), font=font)
        canvas.save(OUT / f"base_{base}.png")
    print(f"wrote {len(BASES)} guides to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
