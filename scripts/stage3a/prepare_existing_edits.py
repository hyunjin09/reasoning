#!/usr/bin/env python3
"""Build the prospectively specified existing-cohort Stage 3A numeric edits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text
from visual_reasoning.stage3a.edits import build_text_conditions, validate_edit_conditions


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a"


SPECS: list[dict[str, Any]] = [
    {"base": "119", "example": "594", "evidence": "594:A", "old": "24", "new": "48", "fact_o": "the sector radius is 24 cm", "fact_c": "the sector radius is 48 cm", "candidate_o": " the sector radius is 24 cm", "candidate_c": " the sector radius is 48 cm", "answer_c": "B", "roi": [18, 96, 36, 116], "font": 14, "anchor": [1, 1]},
    {"base": "140", "example": "699", "evidence": "699:A", "old": "1.52", "new": "1.44", "fact_o": "the net height AO is 1.52 m", "fact_c": "the net height AO is 1.44 m", "candidate_o": " the vertical segment AO is 1.52 m", "candidate_c": " the vertical segment AO is 1.44 m", "answer_c": "D", "roi": [115, 70, 151, 95], "font": 18, "anchor": [1, 1]},
    {"base": "148", "example": "739", "evidence": "739:B", "old": "22m", "new": "17m", "fact_o": "the farther ground segment is 22 m", "fact_c": "the farther ground segment is 17 m", "candidate_o": " the ground distances are 8 m and 22 m", "candidate_c": " the ground distances are 8 m and 17 m", "answer_c": "B", "roi": [194, 146, 236, 168], "font": 16, "anchor": [1, 1]},
    {"base": "153", "example": "764", "evidence": "764:A", "old": "1.8", "new": "1.92", "fact_o": "the left base segment DE is 1.8", "fact_c": "the left base segment DE is 1.92", "candidate_o": " the left base segment DE is 1.8", "candidate_c": " the left base segment DE is 1.92", "answer_c": "B", "roi": [104, 164, 150, 192], "font": 16, "anchor": [1, 1]},
    {"base": "155", "example": "774", "evidence": "774:A", "old": "1.6", "new": "1.8", "fact_o": "the person's height is 1.6 m", "fact_c": "the person's height is 1.8 m", "candidate_o": " the person's height is 1.6 m", "candidate_c": " the person's height is 1.8 m", "answer_c": "D", "roi": [111, 121, 143, 145], "font": 14, "anchor": [1, 1]},
    {"base": "753", "example": "3764", "evidence": "3764:B", "old": "6", "new": "5.4", "fact_o": "the rectangular container length is 6", "fact_c": "the rectangular container length is 5.4", "candidate_o": " the rectangular water block dimensions are 6 by 5 by 4", "candidate_c": " the rectangular water block dimensions are 5.4 by 5 by 4", "answer_c": "C", "roi": [288, 183, 324, 207], "font": 16, "anchor": [2, 1]},
    {"base": "161", "example": "804", "evidence": "804:A", "old": "8", "new": "4", "fact_o": "the triangle-ruler edge is 8", "fact_c": "the triangle-ruler edge is 4", "candidate_o": " the triangle ruler has an edge labeled 8", "candidate_c": " the triangle ruler has an edge labeled 4", "answer_c": "D", "roi": [112, 66, 137, 94], "font": 18, "anchor": [3, 2]},
    {"base": "136", "example": "679", "e0": 55, "e1": 66, "old": "9", "new": "7.5", "fact_o": "the tree shadow BC is 9 m", "fact_c": "the tree shadow BC is 7.5 m", "candidate_o": " a tree AB with a shadow BC which is 9 meters", "candidate_c": " a tree AB with a shadow BC which is 7.5 meters", "answer_c": "B", "roi": [115, 212, 160, 241], "font": 20, "anchor": [2, 1]},
    {"base": "141", "example": "704", "e0": 92, "e1": 112, "old": "15", "new": "18", "fact_o": "building shadow BA is 15 m", "fact_c": "building shadow BA is 18 m", "candidate_o": " the building shadow BA is 15 meters", "candidate_c": " the building shadow BA is 18 meters", "answer_c": "B", "roi": [166, 138, 197, 158], "font": 18, "anchor": [1, 1]},
    {"base": "147", "example": "734", "e0": 64, "e1": 76, "old": "1.5", "new": "1", "fact_o": "benchmark DF has height 1.5 m", "fact_c": "benchmark DF has height 1 m", "candidate_o": " a benchmark DF with a height of 1.5 meters", "candidate_c": " a benchmark DF with a height of 1 meter", "answer_c": "A", "roi": [83, 128, 117, 154], "font": 18, "anchor": [1, 1]},
    {"base": "154", "example": "769", "e0": 223, "e1": 237, "old": "0.55", "new": "0.50", "fact_o": "ladder segment BD is 0.55 m", "fact_c": "ladder segment BD is 0.50 m", "candidate_o": " the length BD is 0.55 meters", "candidate_c": " the length BD is 0.50 meters", "answer_c": "B", "roi": [18, 382, 139, 442], "font": 44, "anchor": [5, 2]},
]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    args = parser.parse_args()
    rows = load_mathverse_rows(args.dataset_root)
    by_id = {str(row["sample_index"]): row for row in rows}
    annotations = {
        row["evidence_id"]: row
        for row in read_jsonl(ROOT / "outputs/stage2c/annotations/evidence_event_annotations.jsonl")
    }
    draft_manifest: list[dict[str, Any]] = []
    for spec in SPECS:
        base = spec["base"]
        example = spec["example"]
        row = by_id[example]
        source = resolve_image_path(args.dataset_root, str(row["image"]))
        target = OUT / "counterfactuals" / base
        if target.exists():
            raise FileExistsError(f"Refusing to overwrite existing counterfactual: {target}")
        render_spec = {
            "roi_xyxy": spec["roi"],
            "original_text": spec["old"],
            "counterfactual_text": spec["new"],
            "font_size": spec["font"],
            "text_color": [0, 0, 0],
            "background_color": [255, 255, 255],
            "text_anchor": spec["anchor"],
        }
        paths = build_text_conditions(source, target, render_spec)
        checks = validate_edit_conditions(paths, spec["roi"])
        if not checks["passed"]:
            raise RuntimeError(f"Automatic edit validation failed for base {base}: {checks}")
        if "evidence" in spec:
            event = annotations[spec["evidence"]]
            e0 = int(event["e0"]["start_token"])
            e1 = int(event["e1"]["completion_token"])
            e2 = int(event["e2"]["start_token"])
            event_source = "Stage 2C manual annotation"
        else:
            e0 = int(spec["e0"])
            e1 = int(spec["e1"])
            e2 = None
            event_source = "Stage 3A manual trace inspection before counterfactual inference"
        generation = json.loads((ROOT / f"outputs/stage1/discovery/examples/{example}/generation.json").read_text(encoding="utf-8"))
        token_ids = [int(value) for value in generation["generated_token_ids"]]
        if not (0 < e0 <= e1 < len(token_ids)):
            raise RuntimeError(f"Invalid event boundary for base {base}")
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
            "edit_description": f"mask only the declared numeric-label ROI and render {spec['old']!r} (sham) or {spec['new']!r} (counterfactual) with the identical renderer",
            "edit_tier": "tier1_local_numeric_label",
            "sham_control": "same mask and renderer, retaining the original fact",
            "irrelevant_control": None,
            "irrelevant_control_omission_reason": "No consistently isolated, equally sized task-irrelevant label was available without risking a second task-relevant change; C2 is the mandatory artifact control.",
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
        write_text(
            target / "validation.md",
            "\n".join(
                [
                    f"# Edit Validation — base {base}",
                    "",
                    "Construction-pass automatic checks: **PASS**",
                    "",
                    "Manual image review: **PENDING**",
                    "",
                    "The original, counterfactual, and sham have identical dimensions. Pixels outside the declared target ROI are byte-identical after RGB decoding. Manual legibility and semantic review must pass before inference.",
                ]
            ),
        )
        draft_manifest.append(metadata)
    ensure_directory(OUT / "cohort")
    write_jsonl(OUT / "cohort/existing_numeric_edit_draft.jsonl", draft_manifest)
    print(json.dumps({"built": len(draft_manifest), "manual_validation_pending": len(draft_manifest)}, indent=2))


if __name__ == "__main__":
    main()
