#!/usr/bin/env python3
"""Build outcome-blind C0/C1/C2 edits for the frozen backup expansion."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path
from visual_reasoning.stage0.io import write_json, write_text
from visual_reasoning.stage3a.edits import build_text_conditions, validate_edit_conditions


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a"
SPECS = {
    "69": {"old": "35°", "new": "65°", "roi": [143, 51, 194, 81], "font": 21},
    "71": {"old": "78°", "new": "88°", "roi": [85, 55, 130, 84], "font": 19},
    "72": {"old": "16", "new": "12", "roi": [214, 18, 248, 45], "font": 18},
    "73": {"old": "70°", "new": "60°", "roi": [70, 83, 116, 114], "font": 20},
    "74": {"old": "115°", "new": "105°", "roi": [98, 86, 155, 116], "font": 20},
    "75": {"old": "42°", "new": "34°", "roi": [80, 1, 130, 31], "font": 20},
    "76": {"old": "36°", "new": "44°", "roi": [12, 65, 62, 95], "font": 20},
    "77": {"old": "60°", "new": "50°", "roi": [76, 69, 123, 101], "font": 20},
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    args = parser.parse_args()
    dataset = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    candidates = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "cohort/backup_candidate_screening.jsonl")}
    if set(candidates) != set(SPECS):
        raise RuntimeError("Backup edit specs do not exactly match the frozen screen")
    for base, spec in SPECS.items():
        item = candidates[base]
        example = str(item["example_id"])
        row = dataset[example]
        target = OUT / "counterfactuals" / base
        if target.exists():
            raise FileExistsError(target)
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
            raise RuntimeError(f"Automatic backup edit validation failed for {base}: {checks}")
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
            "edit_description": f"mask only the frozen numeric-label ROI and render {spec['old']!r} (sham) or {spec['new']!r} (counterfactual) with the shared renderer",
            "edit_tier": "tier1_local_numeric_label",
            "sham_control": "same ROI mask, inferred local background, typography, and renderer retaining the original fact",
            "irrelevant_control": None,
            "irrelevant_control_omission_reason": "No equally isolated task-irrelevant label is guaranteed across the subset; C2 controls target-region rendering artifacts.",
            "automatic_validation": checks,
            "manual_validation": {"status": "pending", "reviewer": None},
            "event": None,
            "candidate_original": " " + item["localized_fact"],
            "candidate_counterfactual": " " + item["counterfactual_fact"],
            "prefix_token_ids": None,
            "prefix_rule": "pending completed-correct generation and manual E0 annotation; final rule is exact y_<E0",
            "selection_used_attention": False,
            "selection_and_edit_frozen_before_generation_outcome": True,
            "expansion_round": 2,
        }
        write_json(target / "edit_metadata.json", metadata)
        write_text(target / "validation.md", f"# Edit Validation — base {base}\n\nAutomatic checks: **PASS**\n\nManual review: **PENDING**\n")
    print(json.dumps({"built": len(SPECS), "bases": list(SPECS)}, indent=2))


if __name__ == "__main__":
    main()
