#!/usr/bin/env python3
"""Build a versioned Stage 3B.9 edit repair pass after blinded manual audit."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text
from visual_reasoning.stage3b9.edits import render_preserving_crossing_strokes

from prepare_fresh_edits import DATASET, OUT, SCREEN, SPECS, review_sheet, sha256, validate


ROOT = Path(__file__).resolve().parents[2]


# These boxes were frozen from the original images during the outcome-blind v1
# manual audit.  Each encloses the complete original label with padding.  The
# v2 renderer restores edge-connected diagram strokes before adding text.
ROI_V2: dict[str, list[int]] = {
    "646":[215,215,310,244], "647":[248,195,273,222], "650":[212,26,286,58],
    "656":[555,140,610,176], "659":[174,46,250,72], "661":[180,84,247,113],
    "673":[229,444,347,477], "676":[267,100,385,142], "679":[301,36,390,79],
    "680":[258,52,276,88], "682":[178,56,208,82], "684":[114,192,165,210],
    "685":[76,93,101,122], "688":[235,167,295,196], "689":[233,290,305,318],
    "692":[207,324,265,352], "695":[162,242,210,271], "696":[278,29,338,56],
    "698":[193,177,252,205], "699":[95,256,155,280], "700":[0,146,34,171],
    "701":[223,103,280,128], "702":[73,151,132,175], "703":[244,103,292,133],
    "704":[13,191,58,215], "706":[224,123,282,147], "707":[392,184,434,214],
    "708":[107,186,157,210], "710":[189,261,238,285], "712":[173,157,235,181],
    "713":[341,139,420,163], "714":[260,263,310,287], "715":[270,229,327,253],
    "716":[187,78,209,102], "717":[132,99,175,121], "718":[52,134,71,156],
    "725":[389,170,446,198], "726":[45,145,96,172], "727":[334,103,390,135],
    "728":[81,332,140,354],
    "648":[222,123,280,150], "649":[271,178,340,205], "651":[232,124,325,151],
    "652":[234,132,360,159], "653":[195,105,218,133], "654":[155,87,270,116],
    "664":[273,147,370,178], "665":[342,209,410,235], "666":[319,196,445,223],
    "667":[254,146,276,173], "668":[243,125,275,152], "669":[238,114,345,144],
    "686":[166,76,235,104], "687":[110,69,180,97], "690":[112,217,182,246],
    "691":[129,244,198,272],
}


def render(source: Path, destination: Path, *, value: str, spec: dict[str, Any], anchor: list[int]) -> None:
    ensure_directory(destination.parent)
    with Image.open(source) as opened:
        rendered = render_preserving_crossing_strokes(
            opened.convert("RGB"),
            f"{value}{spec['suffix']}",
            roi_xyxy=spec["roi"],
            text_anchor=anchor,
            font_size=spec["font"],
        )
        rendered.save(destination)


def text_fits(text: str, spec: dict[str, Any], anchor: list[int]) -> bool:
    try:
        font = ImageFont.load_default(size=int(spec["font"]))
    except TypeError:
        font = ImageFont.load_default()
    box = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), text, font=font)
    width, height = box[2] - box[0], box[3] - box[1]
    roi = spec["roi"]
    return anchor[0] + width <= roi[2] - roi[0] and anchor[1] + height <= roi[3] - roi[1]


def main() -> None:
    screen = json.loads(SCREEN.read_text(encoding="utf-8"))
    all_items = [*screen["phase_a_screen"], *screen["phase_b_screen"]]
    if {str(item["base_problem_id"]) for item in all_items} != set(ROI_V2):
        raise RuntimeError("v2 ROIs must exactly cover the frozen 56-base screen")
    rows = {str(row["sample_index"]): row for row in load_mathverse_rows(DATASET)}
    root = OUT / "fresh_edits/v2"
    ensure_directory(root)
    built_at = datetime.now(timezone.utc).isoformat()
    manifest: list[dict[str, Any]] = []
    for phase, items in (("phase_a", screen["phase_a_screen"]), ("phase_b", screen["phase_b_screen"])):
        for item in items:
            base = str(item["base_problem_id"])
            spec = {**SPECS[base], "roi": ROI_V2[base]}
            dataset_row = rows[str(item["example_id"])]
            source = resolve_image_path(DATASET, str(dataset_row["image"]))
            base_dir = root / phase / base
            paths: dict[str, Path] = {"O": base_dir / "O/image.png", "O_sham": base_dir / "O_sham/image.png"}
            ensure_directory(paths["O"].parent)
            shutil.copy2(source, paths["O"])
            values = [str(item["original"])]
            if phase == "phase_a":
                values.append(str(item["counterfactual"]))
            else:
                values.extend(str(value) for value in item["alternatives"])
            for value in values:
                text = f"{value}{spec['suffix']}"
                if not text_fits(text, spec, [4, 2]):
                    raise RuntimeError(f"Text does not fit v2 ROI for base {base}: {text!r}")
            render(source, paths["O_sham"], value=values[0], spec=spec, anchor=[4, 2])
            if phase == "phase_a":
                paths["C"] = base_dir / "C/image.png"
                paths["C_sham"] = base_dir / "C_sham/image.png"
                render(source, paths["C"], value=values[1], spec=spec, anchor=[4, 2])
                render(source, paths["C_sham"], value=values[1], spec=spec, anchor=[5, 2])
            else:
                for index, value in enumerate(values[1:], start=1):
                    paths[f"C{index}"] = base_dir / f"C{index}/image.png"
                    paths[f"C{index}_sham"] = base_dir / f"C{index}_sham/image.png"
                    render(source, paths[f"C{index}"], value=value, spec=spec, anchor=[4, 2])
                    render(source, paths[f"C{index}_sham"], value=value, spec=spec, anchor=[5, 2])
            checks = validate(paths, spec["roi"])
            if not checks["passed"]:
                raise RuntimeError(f"Automatic v2 validation failed for base {base}: {checks}")
            sheet = review_sheet(base_dir, paths, spec["roi"])
            metadata = {
                **item,
                "phase": phase,
                "edit_version": "stage3b9_v2_edge_preserving",
                "supersedes": f"outputs/stage3b9/fresh_edits/v1/{phase}/{base}/edit_metadata.json",
                "repair_reason": "v1 blinded manual audit found incomplete original-label removal and/or erased crossing diagram strokes",
                "built_at": built_at,
                "source_image": str(source),
                "source_image_sha256": sha256(source),
                "paths": {name: str(path.relative_to(ROOT)) for name, path in paths.items()},
                "target_evidence_roi_xyxy": spec["roi"],
                "render_suffix": spec["suffix"],
                "font_size": spec["font"],
                "construction": {
                    "renderer": "visual_reasoning.stage3b9.edits.render_preserving_crossing_strokes",
                    "same_original_source_for_every_condition": True,
                    "semantic_anchor": [4, 2],
                    "sham_anchor": [5, 2],
                    "edge_connected_original_strokes_restored": True,
                    "selection_used_attention": False,
                    "selection_used_generation_outcomes": False,
                    "selection_used_stage3b9_value_or_causal_outcomes": False,
                },
                "automatic_validation": checks,
                "manual_validation": {"status": "pending", "reviewer": None},
                "review_sheet": str(sheet.relative_to(ROOT)),
            }
            write_json(base_dir / "edit_metadata.json", metadata)
            write_text(
                base_dir / "validation.md",
                f"# Stage 3B.9 v2 edit validation — base {base}\n\n"
                "Automatic containment/dimension validation: **PASS**\n\n"
                "Manual semantic and geometry review: **PENDING**\n",
            )
            manifest.append({
                "base_problem_id": base,
                "example_id": str(item["example_id"]),
                "phase": phase,
                "edit_version": "stage3b9_v2_edge_preserving",
                "edit_metadata": str((base_dir / "edit_metadata.json").relative_to(ROOT)),
                "automatic_edit_status": "pass",
                "manual_edit_status": "pending",
                "generation_outcome_inspected": False,
                "stage3b9_value_or_causal_outcome_inspected": False,
            })
            print(f"built v2 {phase} base {base}", flush=True)
    write_jsonl(root / "construction_manifest.jsonl", manifest)
    print(json.dumps({"built": len(manifest), "phase_a": 40, "phase_b": 16}, indent=2))


if __name__ == "__main__":
    main()
