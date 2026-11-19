#!/usr/bin/env python3
"""Create lossless-indexed review sheets for completed-correct fresh candidates."""

from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path
from visual_reasoning.stage0.io import ensure_directory, write_json


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c8"
DATASET = Path("/data/dataset/MathVerse")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pool", type=Path, default=OUT / "prospective_generation/completed_correct_pool.jsonl")
    parser.add_argument("--target", type=Path, default=OUT / "cohort/candidate_review_sheets")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pool = read_jsonl(args.pool.resolve())
    dataset = {str(row["sample_index"]): row for row in load_mathverse_rows(DATASET)}
    target = args.target.resolve()
    target.relative_to(OUT.resolve())
    ensure_directory(target)
    font = ImageFont.load_default(size=16)
    small = ImageFont.load_default(size=12)
    per_sheet, columns = 12, 4
    sheet_paths = []
    for sheet_index, start in enumerate(range(0, len(pool), per_sheet)):
        page = pool[start : start + per_sheet]
        cell_w, cell_h = 430, 390
        rows = (len(page) + columns - 1) // columns
        sheet = Image.new("RGB", (columns * cell_w, rows * cell_h), "white")
        draw = ImageDraw.Draw(sheet)
        for local_index, item in enumerate(page):
            row = dataset[str(item["example_id"])]
            source = resolve_image_path(DATASET, str(row["image"]))
            with Image.open(source) as opened:
                image = opened.convert("RGB")
                scale = min(1.0, 400 / image.width, 275 / image.height)
                resized = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))), Image.Resampling.LANCZOS)
            x = (local_index % columns) * cell_w
            y = (local_index // columns) * cell_h
            draw.text((x + 6, y + 5), f"order {item['screen_order']} | base {item['base_problem_id']} | ex {item['example_id']}", fill="black", font=font)
            sheet.paste(resized, (x + (cell_w - resized.width) // 2, y + 32))
            question = " ".join(str(row["question_for_eval"]).split())
            for line_index, line in enumerate(textwrap.wrap(question, width=62)[:4]):
                draw.text((x + 6, y + 316 + line_index * 16), line, fill="black", font=small)
        path = target / f"sheet_{sheet_index:02d}.png"
        sheet.save(path)
        sheet_paths.append(str(path.relative_to(ROOT)))
    write_json(target / "index.json", {"candidate_count": len(pool), "per_sheet": per_sheet, "sheets": sheet_paths})
    print(json.dumps({"candidate_count": len(pool), "sheet_count": len(sheet_paths)}, indent=2))


if __name__ == "__main__":
    main()
