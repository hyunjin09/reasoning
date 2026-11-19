#!/usr/bin/env python3
"""Create attention-blind visual/text guides for Stage 3C.2 cohort annotation."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage0.data import load_mathverse_rows


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs" / "stage3c2" / "cohort" / "review_guides"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def wrapped(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], width: int) -> int:
    y = xy[1]
    for line in textwrap.wrap(" ".join(text.split()), width=width) or [""]:
        draw.text((xy[0], y), line, fill="black", font=ImageFont.load_default())
        y += 15
    return y


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = read_jsonl(ROOT / "outputs/stage3b6/config/primary_manifest.jsonl")
    annotations = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(
            ROOT / "outputs/stage3b2/annotations/discriminative_event_annotations.jsonl"
        )
    }
    dataset = {
        str(row["sample_index"]): row
        for row in load_mathverse_rows(Path("/data/dataset/MathVerse"))
    }
    guides: list[Path] = []
    candidate_rows: list[dict] = []
    for item in manifest:
        base = str(item["base_problem_id"])
        row = dataset[str(item["example_id"])]
        annotation = annotations[base]
        image = Image.open(item["source_image"]).convert("RGB")
        scale = min(720 / image.width, 500 / image.height, 2.5)
        display = image.resize(
            (round(image.width * scale), round(image.height * scale)),
            Image.Resampling.LANCZOS,
        )
        draw = ImageDraw.Draw(display)
        x0, y0, x1, y1 = item["target_evidence_roi_xyxy"]
        draw.rectangle(
            (round(x0 * scale), round(y0 * scale), round(x1 * scale), round(y1 * scale)),
            outline=(20, 180, 40),
            width=4,
        )
        canvas = Image.new("RGB", (760, 760), "white")
        canvas.paste(display, ((760 - display.width) // 2, 42))
        text_draw = ImageDraw.Draw(canvas)
        text_draw.text(
            (12, 10),
            f"base {base} | example {item['example_id']} | GREEN = frozen task ROI T",
            fill="black",
            font=ImageFont.load_default(),
        )
        y = 555
        y = wrapped(text_draw, f"TARGET FACT: {item['original_fact']}", (12, y), 105) + 4
        y = wrapped(text_draw, f"QUESTION: {row['question']}", (12, y), 105) + 4
        history = annotation["history_before_ed_text"][-420:]
        wrapped(text_draw, f"PRE-E_d HISTORY: {history}", (12, y), 105)
        path = OUT / f"{int(base):04d}.png"
        canvas.save(path)
        guides.append(path)
        candidate_rows.append(
            {
                "base_problem_id": base,
                "example_id": str(item["example_id"]),
                "question": row["question"],
                "original_fact": item["original_fact"],
                "counterfactual_fact": item["counterfactual_fact"],
                "task_roi_xyxy": item["target_evidence_roi_xyxy"],
                "history_before_ed_text": annotation["history_before_ed_text"],
                "candidate_common_prefix_text": annotation["common_prefix_text"],
                "ed_generated_index": annotation["ed_generated_index"],
                "selection_used_attention": False,
                "annotation_status": "pending",
                "guide": str(path.relative_to(ROOT)),
            }
        )

    candidate_path = ROOT / "outputs/stage3c2/cohort/candidate_manifest.jsonl"
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in candidate_rows),
        encoding="utf-8",
    )
    for page, start in enumerate(range(0, len(guides), 6)):
        selected = guides[start : start + 6]
        sheet = Image.new("RGB", (1520, 2280), "white")
        for offset, path in enumerate(selected):
            image = Image.open(path).convert("RGB")
            x = (offset % 2) * 760
            y = (offset // 2) * 760
            sheet.paste(image, (x, y))
        sheet.save(OUT / f"review_sheet_{page:02d}.png")
    print(json.dumps({"candidate_count": len(candidate_rows), "review_sheets": 7}, indent=2))


if __name__ == "__main__":
    main()
