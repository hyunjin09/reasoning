#!/usr/bin/env python3
"""Render unseen Vision-Dominant MathVerse problems for outcome-blind manual screening."""

from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a/cohort/round3_screening_sheets"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--base-start", type=int, default=78)
    parser.add_argument("--base-end", type=int, default=130)
    parser.add_argument("--per-sheet", type=int, default=4)
    args = parser.parse_args()
    rows = load_mathverse_rows(args.dataset_root)
    vision = {
        int(row["problem_index"]): row
        for row in rows
        if str(row["problem_version"]) == "Vision Dominant"
    }
    attempted = {
        int(row["base_problem_id"])
        for row in read_jsonl(ROOT / "outputs/stage1/discovery/preparation/cohort_attempt_manifest.jsonl")
    }
    prior = set()
    for path in (
        ROOT / "outputs/stage3a/cohort/candidate_screening.jsonl",
        ROOT / "outputs/stage3a/cohort/backup_candidate_screening.jsonl",
    ):
        prior.update(int(row["base_problem_id"]) for row in read_jsonl(path))
    candidates = [
        vision[base]
        for base in range(args.base_start, args.base_end + 1)
        if base in vision and base not in attempted and base not in prior
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default(size=16)
    for page_start in range(0, len(candidates), args.per_sheet):
        page = candidates[page_start : page_start + args.per_sheet]
        blocks = []
        for row in page:
            source = resolve_image_path(args.dataset_root, str(row["image"]))
            image = Image.open(source).convert("RGB")
            if image.width > 800:
                scale = 800 / image.width
                image = image.resize((800, max(1, round(image.height * scale))))
            question = " ".join(str(row["question"]).split())
            label_lines = [
                f"base {row['problem_index']} / ex {row['sample_index']} / answer {row['answer']}",
                *textwrap.wrap(question, width=105),
            ]
            label_height = 24 * len(label_lines) + 10
            block = Image.new("RGB", (max(820, image.width), label_height + image.height + 12), "white")
            draw = ImageDraw.Draw(block)
            for index, line in enumerate(label_lines):
                draw.text((6, 5 + 24 * index), line, fill="black", font=font)
            block.paste(image, ((block.width - image.width) // 2, label_height))
            blocks.append(block)
        sheet = Image.new("RGB", (max(block.width for block in blocks), sum(block.height for block in blocks)), "white")
        y = 0
        for block in blocks:
            sheet.paste(block, (0, y))
            y += block.height
        path = OUT / f"sheet_{page_start // args.per_sheet:02d}.png"
        sheet.save(path)
        print(path)
    print(json.dumps({"screened_images": len(candidates), "excluded_prior_or_stage1": args.base_end - args.base_start + 1 - len(candidates)}, indent=2))


if __name__ == "__main__":
    main()
