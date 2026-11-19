#!/usr/bin/env python3
"""Create an attention-blind contact-sheet packet for Stage 2A ROI screening."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage0.io import ensure_directory, write_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--per-page", type=int, default=20)
    return parser.parse_args()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default()


def main() -> None:
    args = parse_args()
    rows = [json.loads(line) for line in args.cohort_manifest.read_text(encoding="utf-8").splitlines() if line]
    packet: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: int(item["example_id"])):
        root = Path(row["artifact_dir"])
        input_row = read_json(root / "input.json")
        packet.append(
            {
                "example_id": str(row["example_id"]),
                "base_problem_id": str(row["base_problem_id"]),
                "variant": str(row["variant"]),
                "subject": str(row.get("subject", "")),
                "reasoning_length": int(row["reasoning_length"]),
                "question": str(input_row["question"]),
                "answer": str(input_row["ground_truth_answer"]),
                "image_path": str(input_row["resolved_image_path"]),
                "artifact_dir": str(root),
                "selection_boundary": "screened from input structure and reasoning readability, never from attention pattern",
            }
        )
    output = ensure_directory(args.output_dir)
    write_jsonl(output / "roi_screen_manifest.jsonl", packet)
    columns, cell_w, cell_h = 4, 340, 290
    rows_per_page = (args.per_page + columns - 1) // columns
    for page_start in range(0, len(packet), args.per_page):
        page = packet[page_start : page_start + args.per_page]
        canvas = Image.new("RGB", (columns * cell_w, rows_per_page * cell_h), "white")
        draw = ImageDraw.Draw(canvas)
        for local, row in enumerate(page):
            grid_row, grid_col = divmod(local, columns)
            left, top = grid_col * cell_w, grid_row * cell_h
            image = Image.open(row["image_path"]).convert("RGB")
            image.thumbnail((cell_w - 24, 205), Image.Resampling.LANCZOS)
            x = left + (cell_w - image.width) // 2
            y = top + 32 + (205 - image.height) // 2
            canvas.paste(image, (x, y))
            draw.rectangle((left, top, left + cell_w - 1, top + cell_h - 1), outline=(170, 170, 170))
            draw.text((left + 8, top + 7), f"id {row['example_id']} | base {row['base_problem_id']} | {row['variant']}", fill="black", font=font(13))
            question = " ".join(row["question"].split())
            if len(question) > 84:
                question = question[:81] + "..."
            draw.text((left + 8, top + 244), question, fill=(45, 45, 45), font=font(11))
            draw.text((left + 8, top + 269), f"tokens {row['reasoning_length']}", fill=(80, 80, 80), font=font(11))
        canvas.save(output / f"roi_screen_contact_{page_start // args.per_page:02d}.png")
    print(json.dumps({"screened": len(packet), "pages": (len(packet) + args.per_page - 1) // args.per_page, "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
