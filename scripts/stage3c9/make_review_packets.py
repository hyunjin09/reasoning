#!/usr/bin/env python3
"""Create image sheets and indexed text packets for manual Stage 3C.9 audit."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path
from visual_reasoning.stage0.io import ensure_directory, write_json


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def event_snippet(tokens: list[dict[str, Any]], event: dict[str, Any]) -> str:
    readout = int(event["local_use_readout"]["token_index"])
    return "".join(str(row["decoded_token"]) for row in tokens[max(0, readout - 32):min(len(tokens), readout + 28)]).replace("\n", "\\n")


def main() -> None:
    config = json.loads((OUT / "config/stage3c9_config.json").read_text(encoding="utf-8"))
    dataset_root = Path(config["dataset_root"])
    proposals = [
        row for row in read_jsonl(OUT / "cohort/candidate_proposals.jsonl")
        if row["proposal_status"] == "manual_review_required"
    ]
    target = OUT / "cohort/review_packets"
    if target.exists() and any(target.iterdir()):
        raise FileExistsError(target)
    ensure_directory(target)
    dataset = {str(row["sample_index"]): row for row in load_mathverse_rows(dataset_root)}
    packet_paths = []
    for proposal in proposals:
        base = str(proposal["base_problem_id"])
        tokens = read_jsonl(ROOT / proposal["tokens_path"])
        fact_index = int(proposal["selected_fact_index_proposed"])
        fact = next(row for row in proposal["fact_proposals"] if int(row["fact_index"]) == fact_index)
        lines = [
            f"# Stage 3C.9 semantic review — base {base}",
            "",
            f"- Screen order: {proposal['screen_order']}",
            f"- Example / variant: {proposal['example_id']} / {proposal['variant']}",
            f"- Source: {proposal['source']}",
            f"- Generated tokens: {proposal['generated_token_count']}",
            f"- Source image: `{resolve_image_path(dataset_root, str(dataset[str(proposal['example_id'])]['image']))}`",
            f"- Generation: `{proposal['generation_path']}`",
            f"- Exact normalized sentence uniqueness: {proposal['repetition_diagnostic']['unique_normalized_sentence_fraction']:.3f}",
            f"- Maximum exact sentence repetition: {proposal['repetition_diagnostic']['maximum_exact_sentence_repetition']}",
            "",
            "## Question",
            "",
            proposal["question"],
            "",
            "## Proposed visual fact",
            "",
            f"- Fact index: {fact_index}",
            f"- Target/context: `{fact['target']}` / `{fact['context']}`",
            f"- Original → counterfactual: `{fact['original_value']}` → `{fact['counterfactual_value']}`",
            f"- Required evidence terms: {', '.join(fact['required_evidence_terms'])}",
            f"- Proposed events: {len(fact['events'])}",
            f"- Final E_d: {fact['final_use_readout']['token_index']}",
            "",
            "## Event proposals",
            "",
        ]
        for event in fact["events"]:
            neighbor = event["matched_neighbor_span"]
            lines.extend([
                f"### Event {event['event_id']} at {event['span_start_token']}:{event['span_end_token']} → readout {event['local_use_readout']['token_index']}",
                "",
                f"- Span: `{event['span_text']}`",
                f"- Role/relation: `{event['event_role']}` / `{event['evidence_relation']}`",
                f"- Neighbor: `{None if neighbor is None else neighbor['span_text']}`",
                f"- Snippet: `{event_snippet(tokens, event)}`",
                "",
            ])
        path = target / f"base_{int(base):04d}.md"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        packet_paths.append(str(path.relative_to(ROOT)))

    per_sheet, columns = 12, 4
    sheet_paths = []
    font = ImageFont.load_default(size=15)
    small = ImageFont.load_default(size=11)
    for sheet_index, start in enumerate(range(0, len(proposals), per_sheet)):
        page = proposals[start:start + per_sheet]
        cell_w, cell_h = 430, 385
        rows = (len(page) + columns - 1) // columns
        sheet = Image.new("RGB", (columns * cell_w, rows * cell_h), "white")
        draw = ImageDraw.Draw(sheet)
        for local_index, proposal in enumerate(page):
            row = dataset[str(proposal["example_id"])]
            with Image.open(resolve_image_path(dataset_root, str(row["image"]))) as opened:
                image = opened.convert("RGB")
                scale = min(1.0, 400 / image.width, 270 / image.height)
                image = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))), Image.Resampling.LANCZOS)
            x = local_index % columns * cell_w
            y = local_index // columns * cell_h
            draw.text((x + 5, y + 4), f"order {proposal['screen_order']} | base {proposal['base_problem_id']} | {proposal['generated_token_count']} tok", fill="black", font=font)
            sheet.paste(image, (x + (cell_w - image.width) // 2, y + 28))
            fact = next(row for row in proposal["fact_proposals"] if int(row["fact_index"]) == int(proposal["selected_fact_index_proposed"]))
            caption = f"{fact['target']} :: {fact['original_value']}->{fact['counterfactual_value']} :: {len(fact['events'])} events"
            for line_index, line in enumerate(textwrap.wrap(caption, width=58)[:4]):
                draw.text((x + 5, y + 310 + 15 * line_index), line, fill="black", font=small)
        sheet_path = target / f"image_sheet_{sheet_index:02d}.png"
        sheet.save(sheet_path)
        sheet_paths.append(str(sheet_path.relative_to(ROOT)))
    write_json(target / "index.json", {
        "candidate_count": len(proposals),
        "packet_paths": packet_paths,
        "image_sheets": sheet_paths,
        "attention_used": False,
        "causal_scores_available": False,
    })
    print(json.dumps({"candidate_count": len(proposals), "image_sheets": len(sheet_paths)}, indent=2))


if __name__ == "__main__":
    main()
