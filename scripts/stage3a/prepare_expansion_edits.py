#!/usr/bin/env python3
"""Build outcome-blind C0/C1/C2 image edits for frozen expansion candidates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path
from visual_reasoning.stage0.io import write_json, write_jsonl, write_text
from visual_reasoning.stage3a.edits import build_text_conditions, validate_edit_conditions


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a"


# ROI and typography were specified from coordinate-guide copies before any new
# model output existed. The values are construction candidates, not approvals;
# every rendered triplet still requires lossless side-by-side manual review.
SPECS: dict[str, dict[str, Any]] = {
    "1": {"old": "80°", "new": "60°", "roi": [148, 63, 199, 94], "font": 25},
    "2": {"old": "50°", "new": "60°", "roi": [158, 168, 204, 196], "font": 22},
    "3": {"old": "70°", "new": "80°", "roi": [343, 610, 493, 695], "font": 78},
    "5": {"old": "50°", "new": "40°", "roi": [42, 148, 91, 181], "font": 22},
    "6": {"old": "50°", "new": "60°", "roi": [253, 38, 314, 71], "font": 22},
    "9": {"old": "6.0", "new": "7.0", "roi": [176, 211, 226, 244], "font": 22},
    "10": {"old": "36°", "new": "30°", "roi": [122, 62, 168, 94], "font": 20},
    "14": {"old": "35°", "new": "30°", "roi": [93, 109, 134, 136], "font": 17},
    "16": {"old": "50°", "new": "60°", "roi": [171, 111, 222, 145], "font": 20},
    "20": {"old": "140°", "new": "100°", "roi": [83, 136, 149, 168], "font": 23},
    "22": {"old": "28°", "new": "18°", "roi": [92, 103, 136, 130], "font": 18},
    "24": {"old": "50°", "new": "30°", "roi": [12, 27, 64, 59], "font": 20},
    "29": {"old": "50°", "new": "60°", "roi": [214, 56, 261, 88], "font": 18},
    "31": {"old": "65°", "new": "55°", "roi": [280, 18, 330, 49], "font": 20},
    "32": {"old": "52°", "new": "56°", "roi": [148, 100, 193, 128], "font": 17},
    "34": {"old": "100°", "new": "80°", "roi": [134, 106, 194, 136], "font": 21},
    "38": {"old": "70°", "new": "75°", "roi": [133, 65, 179, 94], "font": 18},
    "40": {"old": "50°", "new": "60°", "roi": [256, 17, 311, 49], "font": 18},
    "45": {"old": "35°", "new": "75°", "roi": [162, 74, 203, 100], "font": 16},
    "48": {"old": "100°", "new": "160°", "roi": [97, 127, 158, 159], "font": 21},
    "53": {"old": "55°", "new": "65°", "roi": [179, 8, 229, 38], "font": 22},
    "54": {"old": "40°", "new": "50°", "roi": [55, 12, 104, 42], "font": 20},
    "55": {"old": "70°", "new": "90°", "roi": [54, 99, 103, 130], "font": 20},
    "56": {"old": "20°", "new": "10°", "roi": [142, 73, 186, 102], "font": 18},
    "58": {"old": "35°", "new": "25°", "roi": [122, 40, 166, 66], "font": 18},
    "60": {"old": "135°", "new": "150°", "roi": [8, 92, 77, 125], "font": 23},
    "61": {"old": "74°", "new": "79°", "roi": [72, 39, 118, 67], "font": 20},
    "62": {"old": "40°", "new": "30°", "roi": [174, 46, 226, 75], "font": 20},
    "65": {"old": "30°", "new": "35°", "roi": [152, 104, 203, 133], "font": 20},
    "66": {"old": "20°", "new": "30°", "roi": [191, 33, 238, 60], "font": 17},
    "67": {"old": "40°", "new": "20°", "roi": [73, 94, 121, 124], "font": 20},
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    args = parser.parse_args()
    dataset = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    candidates = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(OUT / "cohort/candidate_screening.jsonl")
        if row["source"] == "prospective_unseen_expansion"
    }
    if set(candidates) != set(SPECS):
        raise RuntimeError("Expansion edit specs must exactly cover the prospectively frozen generation candidates")
    draft = []
    for base, spec in SPECS.items():
        item = candidates[base]
        example = str(item["example_id"])
        row = dataset[example]
        target = OUT / "counterfactuals" / base
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite existing counterfactual: {target}")
        source = resolve_image_path(args.dataset_root, str(row["image"]))
        render_spec = {
            "roi_xyxy": spec["roi"],
            "original_text": spec["old"],
            "counterfactual_text": spec["new"],
            "font_size": spec["font"],
            "text_color": [0, 0, 0],
            "background_mode": "roi_bright_median",
            "text_anchor": [2, 1],
        }
        paths = build_text_conditions(source, target, render_spec)
        checks = validate_edit_conditions(paths, spec["roi"])
        if not checks["passed"]:
            raise RuntimeError(f"Automatic edit validation failed for base {base}: {checks}")
        metadata = {
            "base_problem_id": base,
            "example_id": example,
            "variant": str(row["problem_version"]),
            "source_image": str(source),
            "conditions": {name: str(path.relative_to(ROOT)) for name, path in paths.items()},
            "target_evidence_roi_xyxy": spec["roi"],
            "original_fact": item["localized_fact"],
            "counterfactual_fact": item["counterfactual_fact"],
            "counterfactual_expected_answer": item["counterfactual_expected_answer"],
            "edit_description": f"mask only the prospectively declared numeric-label ROI and render {spec['old']!r} (sham) or {spec['new']!r} (counterfactual) with one shared renderer",
            "edit_tier": "tier1_local_numeric_label",
            "sham_control": "same ROI mask, inferred local background, typography, and renderer while retaining the original numeric fact",
            "irrelevant_control": None,
            "irrelevant_control_omission_reason": "No equally isolated task-irrelevant label was guaranteed across this homogeneous diagram subset; the mandatory C2 sham controls the target-region rendering artifact.",
            "automatic_validation": checks,
            "manual_validation": {"status": "pending", "reviewer": None},
            "event": None,
            "candidate_original": " " + item["localized_fact"],
            "candidate_counterfactual": " " + item["counterfactual_fact"],
            "prefix_token_ids": None,
            "prefix_rule": "pending completed-correct generation and manual E0 annotation; final rule is exact y_<E0",
            "selection_used_attention": False,
            "selection_and_edit_frozen_before_generation_outcome": True,
        }
        write_json(target / "edit_metadata.json", metadata)
        write_text(
            target / "validation.md",
            f"# Edit Validation — base {base}\n\n"
            "Construction-pass automatic checks: **PASS**\n\n"
            "Manual image review: **PENDING**\n\n"
            "Generation eligibility and strict pre-E0 event annotation: **PENDING**\n",
        )
        draft.append(metadata)
    write_jsonl(OUT / "cohort/expansion_edit_draft.jsonl", draft)
    print(json.dumps({"built": len(draft), "manual_validation_pending": len(draft)}, indent=2))


if __name__ == "__main__":
    main()
