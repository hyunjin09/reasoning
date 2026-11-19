#!/usr/bin/env python3
"""Render unseen Vision-Dominant problems for outcome-blind Stage 3B.7-R screening."""

from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b7r/validation_cohort/screening_sheets"


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def prior_bases() -> set[int]:
    paths = [
        ROOT / "outputs/stage1/discovery/preparation/cohort_attempt_manifest.jsonl",
        ROOT / "outputs/stage3a/cohort/candidate_screening.jsonl",
        ROOT / "outputs/stage3a/cohort/backup_candidate_screening.jsonl",
        ROOT / "outputs/stage3a/cohort/round3_candidate_screening.jsonl",
        ROOT / "outputs/stage3b7/config/primary_manifest.jsonl",
        ROOT / "outputs/stage3b7/config/validation_manifest.jsonl",
    ]
    return {
        int(row["base_problem_id"])
        for path in paths
        for row in read_jsonl(path)
        if row.get("base_problem_id") is not None
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--base-start", type=int, default=156)
    parser.add_argument("--base-end", type=int, default=300)
    parser.add_argument("--per-sheet", type=int, default=4)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()

    vision = {
        int(row["problem_index"]): row
        for row in load_mathverse_rows(args.dataset_root)
        if str(row["problem_version"]) == "Vision Dominant"
    }
    excluded = prior_bases()
    candidates = [
        vision[base]
        for base in range(args.base_start, args.base_end + 1)
        if base in vision and base not in excluded
    ]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default(size=16)
    for page_start in range(0, len(candidates), args.per_sheet):
        blocks = []
        for row in candidates[page_start : page_start + args.per_sheet]:
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
        sheet.save(args.output_dir / f"sheet_{page_start // args.per_sheet:02d}.png")
    print(json.dumps({"rendered": len(candidates), "excluded_prior": len(excluded), "output": str(args.output_dir)}, indent=2))


if __name__ == "__main__":
    main()
