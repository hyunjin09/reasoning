#!/usr/bin/env python3
"""Build the remaining clean completed-correct Stage 1 numeric edit (base 751)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path
from visual_reasoning.stage0.io import write_json, write_text
from visual_reasoning.stage3a.edits import build_text_conditions, validate_edit_conditions


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    args = parser.parse_args()
    example, base = "3754", "751"
    row = {str(item["sample_index"]): item for item in load_mathverse_rows(args.dataset_root)}[example]
    source = resolve_image_path(args.dataset_root, str(row["image"]))
    target = OUT / "counterfactuals" / base
    if target.exists():
        raise FileExistsError(target)
    render_spec = {
        "roi_xyxy": [211, 15, 251, 43],
        "original_text": "30",
        "counterfactual_text": "34",
        "font_size": 20,
        "text_color": [0, 0, 0],
        "background_mode": "roi_bright_median",
        "text_anchor": [3, 1],
    }
    paths = build_text_conditions(source, target, render_spec)
    checks = validate_edit_conditions(paths, render_spec["roi_xyxy"])
    if not checks["passed"]:
        raise RuntimeError(checks)
    annotation = next(
        item
        for item in read_jsonl(OUT.parent / "stage2c/annotations/evidence_event_annotations.jsonl")
        if item["evidence_id"] == "3754:A"
    )
    generation = json.loads((ROOT / f"outputs/stage1/discovery/examples/{example}/generation.json").read_text(encoding="utf-8"))
    ids = [int(value) for value in generation["generated_token_ids"]]
    e0 = int(annotation["e0"]["start_token"])
    metadata = {
        "base_problem_id": base,
        "example_id": example,
        "variant": str(row["problem_version"]),
        "source_image": str(source),
        "conditions": {name: str(path.relative_to(ROOT)) for name, path in paths.items()},
        "target_evidence_roi_xyxy": render_spec["roi_xyxy"],
        "original_fact": "the tube length AB is 30",
        "counterfactual_fact": "the tube length AB is 34",
        "counterfactual_expected_answer": "D",
        "edit_description": "mask only the isolated AB numeric-label ROI and render '30' (sham) or '34' (counterfactual) with one shared renderer",
        "edit_tier": "tier1_local_numeric_label",
        "sham_control": "same ROI mask, inferred background, typography, and renderer retaining label 30",
        "irrelevant_control": None,
        "irrelevant_control_omission_reason": "The figure has no comparably isolated task-irrelevant label; C2 controls target-region rendering artifacts.",
        "automatic_validation": checks,
        "manual_validation": {"status": "pending", "reviewer": None},
        "event": {
            "e0_start_token": e0,
            "e1_completion_token": int(annotation["e1"]["completion_token"]),
            "e2_start_token": int(annotation["e2"]["start_token"]),
            "source": "Stage 2C manual annotation",
        },
        "candidate_original": " the tube length AB is 30",
        "candidate_counterfactual": " the tube length AB is 34",
        "prefix_token_ids": ids[:e0],
        "prefix_rule": "all original generated reasoning tokens strictly before E0; no E0 token included",
        "selection_used_attention": False,
    }
    write_json(target / "edit_metadata.json", metadata)
    write_text(target / "validation.md", "# Edit Validation — base 751\n\nAutomatic checks: **PASS**\n\nManual image review: **PENDING**\n")
    print(json.dumps({"built": base, "e0": e0}, indent=2))


if __name__ == "__main__":
    main()
