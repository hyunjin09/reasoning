#!/usr/bin/env python3
"""Build three additional clean curve/line counterfactuals from Stage 1B."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path
from visual_reasoning.stage0.io import write_json, write_text
from visual_reasoning.stage3a.edits import build_polyline_conditions, validate_edit_conditions


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a"


def parabola_points(x0: int, x1: int, vertex_x: float, vertex_y: float, edge_y: float, concave_down: bool) -> list[list[int]]:
    radius = max(abs(x0 - vertex_x), abs(x1 - vertex_x))
    points = []
    for x in range(x0, x1 + 1, 4):
        fraction = ((x - vertex_x) / radius) ** 2
        y = vertex_y + (edge_y - vertex_y) * fraction
        if not concave_down:
            y = vertex_y - (vertex_y - edge_y) * fraction
        points.append([x, int(round(y))])
    return points


SPECS: list[dict[str, Any]] = [
    {
        "base": "560", "example": "2799", "evidence": "2799:A", "roi": [24, 86, 250, 324],
        "original": parabola_points(34, 242, 138, 96, 315, True),
        "counterfactual": parabola_points(34, 242, 138, 194, 290, True),
        "fact_o": "the graph has a maximum of 4 million mosquitoes at 2 cm rainfall",
        "fact_c": "the graph has a maximum of 2 million mosquitoes at 2 cm rainfall",
        "candidate_o": " the graph's maximum is 4 million mosquitoes at 2 cm rainfall",
        "candidate_c": " the graph's maximum is 2 million mosquitoes at 2 cm rainfall",
        "answer_c": "A", "line_color": [42, 162, 187], "erase_mode": "cyan_mask", "erase_stroke_width": 15,
        "grid_x": [65, 89, 113, 137, 161, 185, 209, 233], "grid_y": [96, 120, 144, 168, 192, 216, 240, 264],
        "preserve": [[213, 100, 238, 130]],
    },
    {
        "base": "567", "example": "2833", "evidence": "2833:A", "roi": [0, 45, 123, 282],
        "original": parabola_points(9, 115, 55, 55, 274, True),
        "counterfactual": parabola_points(9, 115, 55, 225, 65, False),
        "fact_o": "g(x) is concave down with a visible maximum",
        "fact_c": "g(x) is concave up with a visible minimum",
        "candidate_o": " the graph of g(x) is concave down with a maximum",
        "candidate_c": " the graph of g(x) is concave up with a minimum",
        "answer_c": "B", "line_color": [42, 162, 187], "erase_mode": "cyan_mask", "erase_stroke_width": 15,
        "grid_x": [9, 24, 39, 54, 69, 84, 99, 114], "grid_y": [55, 70, 85, 100, 115, 130, 160, 175, 190, 205, 220, 235, 250, 265],
        "preserve": [[25, 130, 88, 160]],
    },
    {
        "base": "609", "example": "3044", "e0": 260, "e1": 279, "e2": 630, "roi": [108, 48, 529, 223],
        "original": [[114, 217], [524, 52]], "counterfactual": [[114, 52], [524, 217]],
        "fact_o": "price rises by about 0.50 per additional thousand units",
        "fact_c": "price falls by about 0.50 per additional thousand units",
        "candidate_o": " the plotted price line rises by about 0.50 per additional thousand units",
        "candidate_c": " the plotted price line falls by about 0.50 per additional thousand units",
        "answer_c": "D", "line_color": [0, 0, 0], "erase_mode": "dark_mask",
        "erase_stroke_width": 7, "erase_marker_radius": 9, "erase_marker_points": [[223, 173], [410, 98]],
        "preserve": [[108, 45, 115, 225]],
    },
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    args = parser.parse_args()
    rows = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    annotations = {row["evidence_id"]: row for row in read_jsonl(ROOT / "outputs/stage2c/annotations/evidence_event_annotations.jsonl")}
    for spec in SPECS:
        base, example = spec["base"], spec["example"]
        row = rows[example]
        source = resolve_image_path(args.dataset_root, str(row["image"]))
        target = OUT / "counterfactuals" / base
        if target.exists():
            raise FileExistsError(target)
        render_spec = {
            "roi_xyxy": spec["roi"],
            "original_points": spec["original"],
            "counterfactual_points": spec["counterfactual"],
            "line_color": spec["line_color"],
            "line_width": 3,
            "background_color": [255, 255, 255],
            "erase_mode": spec["erase_mode"],
            "erase_color": spec.get("erase_color", [0, 0, 0]),
            "erase_tolerance": spec.get("tolerance", 0),
            "cyan_excess_threshold": 30,
            "dark_threshold": 210,
            "erase_stroke_width": spec.get("erase_stroke_width", 0),
            "erase_marker_radius": spec.get("erase_marker_radius", 0),
            "erase_marker_points": spec.get("erase_marker_points", []),
            "grid_lines_x": spec.get("grid_x", []),
            "grid_lines_y": spec.get("grid_y", []),
            "grid_color": [225, 225, 225],
            "preserve_boxes": spec.get("preserve", []),
        }
        paths = build_polyline_conditions(source, target, render_spec)
        checks = validate_edit_conditions(paths, spec["roi"])
        if not checks["passed"]:
            raise RuntimeError(f"Automatic curve validation failed for {base}: {checks}")
        if "evidence" in spec:
            event = annotations[spec["evidence"]]
            e0 = int(event["e0"]["start_token"])
            e1 = int(event["e1"]["completion_token"])
            e2 = int(event["e2"]["start_token"])
            event_source = "Stage 2C manual annotation"
        else:
            e0, e1, e2 = int(spec["e0"]), int(spec["e1"]), int(spec["e2"])
            event_source = "Stage 3A manual trace inspection before counterfactual inference"
        generation = json.loads((ROOT / f"outputs/stage1/discovery/examples/{example}/generation.json").read_text(encoding="utf-8"))
        token_ids = [int(value) for value in generation["generated_token_ids"]]
        metadata = {
            "base_problem_id": base,
            "example_id": example,
            "variant": row["problem_version"],
            "source_image": str(source),
            "conditions": {name: str(path.relative_to(ROOT)) for name, path in paths.items()},
            "target_evidence_roi_xyxy": spec["roi"],
            "original_fact": spec["fact_o"],
            "counterfactual_fact": spec["fact_c"],
            "counterfactual_expected_answer": spec["answer_c"],
            "edit_description": "remove only pixels matching the plotted trajectory color inside the declared ROI, then redraw original (sham) or alternate (counterfactual) curve with identical settings",
            "edit_tier": "tier3_structural_visual_edit",
            "sham_control": "same color-mask removal and renderer, retaining original curve semantics",
            "irrelevant_control": None,
            "irrelevant_control_omission_reason": "A second plot edit would alter task-relevant graph evidence; the sham directly controls curve-redraw artifacts.",
            "automatic_validation": checks,
            "manual_validation": {"status": "pending", "reviewer": None},
            "event": {"e0_start_token": e0, "e1_completion_token": e1, "e2_start_token": e2, "source": event_source},
            "candidate_original": spec["candidate_o"],
            "candidate_counterfactual": spec["candidate_c"],
            "prefix_token_ids": token_ids[:e0],
            "prefix_rule": "all original generated reasoning tokens strictly before E0; no E0 token included",
            "selection_used_attention": False,
        }
        write_json(target / "edit_metadata.json", metadata)
        write_text(target / "validation.md", f"# Edit Validation — base {base}\n\nConstruction-pass automatic checks: **PASS**\n\nManual image review: **PENDING**\n")
    print(json.dumps({"built": [spec["base"] for spec in SPECS], "manual_validation_pending": len(SPECS)}, indent=2))


if __name__ == "__main__":
    main()
