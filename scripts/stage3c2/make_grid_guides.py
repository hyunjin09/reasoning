#!/usr/bin/env python3
"""Draw attention-blind merged visual-token grids for manual mention-ROI audit."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c2/annotations/grid_guides"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(ROOT / "outputs/stage3b6/config/primary_manifest.jsonl")
    }
    mappings = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(ROOT / "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl")
    }
    for base, item in manifest.items():
        mapping = mappings[base]
        _, rows, cols = [int(value) for value in mapping["merged_grid_shape"]]
        image = Image.open(item["source_image"]).convert("RGBA")
        layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        font = ImageFont.load_default()
        for row in range(rows):
            for col in range(cols):
                index = row * cols + col
                x0, x1 = col * image.width // cols, (col + 1) * image.width // cols
                y0, y1 = row * image.height // rows, (row + 1) * image.height // rows
                fill = (30, 180, 40, 65) if index in mapping["target_local_positions"] else (0, 0, 0, 0)
                draw.rectangle((x0, y0, x1, y1), fill=fill, outline=(30, 90, 210, 150), width=1)
                draw.text((x0 + 2, y0 + 2), str(index), fill=(180, 20, 20, 255), font=font)
        composed = Image.alpha_composite(image, layer).convert("RGB")
        scale = max(1.0, min(4.0, 960 / max(composed.size)))
        composed = composed.resize(
            (round(composed.width * scale), round(composed.height * scale)),
            Image.Resampling.NEAREST,
        )
        header = Image.new("RGB", (composed.width, 42), "white")
        ImageDraw.Draw(header).text(
            (8, 8),
            f"base {base} | grid {rows}x{cols} | green=T | red=index | blue=cell",
            fill="black",
            font=font,
        )
        canvas = Image.new("RGB", (composed.width, composed.height + 42), "white")
        canvas.paste(header, (0, 0))
        canvas.paste(composed, (0, 42))
        canvas.save(OUT / f"{int(base):04d}.png")
    print(json.dumps({"grid_guides": len(manifest), "output": str(OUT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
