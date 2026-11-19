#!/usr/bin/env python3
"""Build prospectively defined speed-graph trajectory edits for Stage 3A."""

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
SPECS: list[dict[str, Any]] = [
    {"base": "613", "example": "3063", "evidence": "3063:A", "roi": [99, 76, 478, 430], "preserve": [[450, 395, 520, 425]], "original": [[101, 427], [472, 81]], "counterfactual": [[101, 427], [220, 427], [472, 81]], "fact_o": "the speed-time graph is one straight rising line", "fact_c": "the graph is initially horizontal and then rises steadily", "candidate_o": " the speed-time graph is one straight rising line", "candidate_c": " the speed-time graph is initially horizontal and then rises steadily", "answer_c": "B"},
    {"base": "614", "example": "3069", "evidence": "3069:A", "roi": [99, 51, 478, 430], "preserve": [[450, 395, 520, 425]], "original": [[101, 427], [360, 300], [472, 56]], "counterfactual": [[101, 427], [290, 100], [472, 300]], "fact_o": "the graph rises gradually and then more steeply", "fact_c": "the graph rises to a peak and then falls", "candidate_o": " the graph rises gradually and then more steeply", "candidate_c": " the graph rises to a peak and then falls", "answer_c": "A"},
    {"base": "615", "example": "3074", "evidence": "3074:A", "roi": [102, 130, 480, 433], "preserve": [[455, 400, 525, 430]], "original": [[104, 430], [232, 174], [251, 430], [344, 173], [475, 136]], "counterfactual": [[104, 430], [300, 170], [475, 170]], "fact_o": "the graph rises, drops sharply, and then recovers", "fact_c": "the graph rises and then remains constant", "candidate_o": " the graph rises, drops sharply, and then recovers", "candidate_c": " the graph rises and then remains constant", "answer_c": "C"},
    {"base": "616", "example": "3079", "evidence": "3079:A", "roi": [89, 145, 468, 424], "preserve": [[435, 385, 505, 420]], "original": [[91, 421], [217, 275], [295, 150], [462, 275]], "counterfactual": [[91, 421], [295, 150], [462, 150]], "fact_o": "the graph rises to a central peak and then falls", "fact_c": "the graph rises and then remains constant", "candidate_o": " the graph rises to a central peak and then falls", "candidate_c": " the graph rises and then remains constant", "answer_c": "B"},
    {"base": "617", "example": "3084", "e0": 61, "e1": 113, "roi": [96, 126, 475, 430], "preserve": [[450, 395, 520, 425]], "original": [[98, 427], [281, 205], [376, 131], [469, 131]], "counterfactual": [[98, 427], [250, 427], [469, 131]], "fact_o": "the graph rises gradually and then becomes horizontal", "fact_c": "the graph is initially horizontal and then rises steadily", "candidate_o": " the graph rises gradually and then becomes horizontal", "candidate_c": " the graph is initially horizontal and then rises steadily", "answer_c": "A"},
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    args = parser.parse_args()
    rows = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    annotations = {row["evidence_id"]: row for row in read_jsonl(ROOT / "outputs/stage2c/annotations/evidence_event_annotations.jsonl")}
    built = []
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
            "line_color": [0, 0, 0],
            "line_width": 3,
            "background_color": [255, 255, 255],
            "preserve_boxes": spec["preserve"],
        }
        paths = build_polyline_conditions(source, target, render_spec)
        checks = validate_edit_conditions(paths, spec["roi"])
        if not checks["passed"]:
            raise RuntimeError(f"Automatic structural validation failed for {base}: {checks}")
        if "evidence" in spec:
            event = annotations[spec["evidence"]]
            e0 = int(event["e0"]["start_token"])
            e1 = int(event["e1"]["completion_token"])
            e2 = int(event["e2"]["start_token"])
            source_label = "Stage 2C manual annotation"
        else:
            e0, e1, e2 = int(spec["e0"]), int(spec["e1"]), None
            source_label = "Stage 3A manual trace inspection before counterfactual inference"
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
            "edit_description": "erase only the plot-interior trajectory ROI and redraw the original (sham) or alternate (counterfactual) speed trajectory with identical settings",
            "edit_tier": "tier3_structural_visual_edit",
            "sham_control": "same plot-interior mask and polyline renderer, retaining the original trajectory semantics",
            "irrelevant_control": None,
            "irrelevant_control_omission_reason": "A matched plot edit elsewhere would itself alter task-relevant graph evidence; C2 controls redraw artifacts.",
            "automatic_validation": checks,
            "manual_validation": {"status": "pending", "reviewer": None},
            "event": {"e0_start_token": e0, "e1_completion_token": e1, "e2_start_token": e2, "source": source_label},
            "candidate_original": spec["candidate_o"],
            "candidate_counterfactual": spec["candidate_c"],
            "prefix_token_ids": token_ids[:e0],
            "prefix_rule": "all original generated reasoning tokens strictly before E0; no E0 token included",
            "selection_used_attention": False,
        }
        write_json(target / "edit_metadata.json", metadata)
        write_text(target / "validation.md", f"# Edit Validation — base {base}\n\nConstruction-pass automatic checks: **PASS**\n\nManual image review: **PENDING**\n")
        built.append(base)
    print(json.dumps({"built": built, "manual_validation_pending": len(built)}, indent=2))


if __name__ == "__main__":
    main()
