#!/usr/bin/env python3
"""Draw frozen T/M/I token sets for the final pre-measurement manual audit."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c2/audit/roi_overlays"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    primary = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3b6/config/primary_manifest.jsonl")}
    mappings = {str(row["base_problem_id"]): row for row in read_jsonl(ROOT / "outputs/stage3b7/roi_audit/roi_token_mapping.jsonl")}
    mentions = read_jsonl(ROOT / "outputs/stage3c2/annotations/mention_roi_annotations.jsonl")
    paths = []
    for mention in mentions:
        base = str(mention["base_problem_id"])
        image = Image.open(primary[base]["source_image"]).convert("RGBA")
        mapping = mappings[base]
        _, rows, cols = map(int, mapping["merged_grid_shape"])
        target = set(map(int, mapping["target_local_positions"]))
        irrelevant = set(map(int, mapping["irrelevant_local_positions"]))
        mention_set = set(map(int, mention["mention_local_visual_positions"]))
        layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        for row in range(rows):
            for col in range(cols):
                index = row * cols + col
                x0, x1 = col * image.width // cols, (col + 1) * image.width // cols
                y0, y1 = row * image.height // rows, (row + 1) * image.height // rows
                fill = None
                if index in target:
                    fill = (30, 180, 40, 95)
                elif index in mention_set:
                    fill = (210, 20, 180, 95)
                elif index in irrelevant:
                    fill = (230, 140, 10, 75)
                if fill:
                    draw.rectangle((x0, y0, x1, y1), fill=fill, outline=fill[:3] + (220,), width=2)
        composed = Image.alpha_composite(image, layer).convert("RGB")
        scale = min(680 / composed.width, 480 / composed.height, 3.0)
        composed = composed.resize((round(composed.width * scale), round(composed.height * scale)), Image.Resampling.NEAREST)
        canvas = Image.new("RGB", (720, 600), "white")
        canvas.paste(composed, ((720 - composed.width) // 2, 54))
        header = ImageDraw.Draw(canvas)
        header.text((8, 8), f"base {base}: green=T, magenta=M, orange=I", fill="black", font=ImageFont.load_default())
        header.text((8, 25), f"M: {mention['mention_entity']}", fill="black", font=ImageFont.load_default())
        path = OUT / f"{int(base):04d}.png"
        canvas.save(path)
        paths.append(path)
    for page, start in enumerate(range(0, len(paths), 6)):
        sheet = Image.new("RGB", (1440, 1800), "white")
        for offset, path in enumerate(paths[start:start + 6]):
            sheet.paste(Image.open(path), ((offset % 2) * 720, (offset // 2) * 600))
        sheet.save(OUT / f"audit_sheet_{page:02d}.png")
    print(json.dumps({"overlays": len(paths), "sheets": (len(paths) + 5) // 6}))


if __name__ == "__main__":
    main()
