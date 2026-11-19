#!/usr/bin/env python3
"""Compose Stage 3C.9 ROI overlays into score-blind manual-review sheets."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    rows = read_jsonl(OUT / "cohort/roi_mapping_pending.jsonl")
    target = OUT / "cohort/work/roi_review_sheets"
    target.mkdir(parents=True, exist_ok=False)
    columns, per_sheet = 4, 8
    cell_w, cell_h = 480, 430
    font = ImageFont.load_default(size=18)
    outputs = []
    for sheet_index, start in enumerate(range(0, len(rows), per_sheet)):
        page = rows[start:start + per_sheet]
        sheet = Image.new("RGB", (columns * cell_w, 2 * cell_h), "white")
        draw = ImageDraw.Draw(sheet)
        for offset, row in enumerate(page):
            base = str(row["base_problem_id"])
            source = ROOT / str(row["overlay"])
            with Image.open(source) as opened:
                image = opened.convert("RGB")
            image.thumbnail((cell_w - 16, cell_h - 38), Image.Resampling.LANCZOS)
            x = (offset % columns) * cell_w
            y = (offset // columns) * cell_h
            draw.text((x + 6, y + 6), f"base {base}", fill="black", font=font)
            sheet.paste(image, (x + (cell_w - image.width) // 2, y + 34))
        path = target / f"roi_sheet_{sheet_index:02d}.png"
        sheet.save(path)
        outputs.append(str(path.relative_to(ROOT)))
    print(json.dumps({"overlays": len(rows), "sheets": len(outputs), "outputs": outputs}, indent=2))


if __name__ == "__main__":
    main()
