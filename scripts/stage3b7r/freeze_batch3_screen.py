#!/usr/bin/env python3
"""Freeze outcome-blind Stage 3B.7-R contingency screen batch 3."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage3b7r.protocol import validate_disjoint_split


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b7r"
SPECS = {
    "302": ("total segment GJ is 8", "total segment GJ is 16", "B", "Similarity gives KJ=GJ*(HI/GI), changing 2 to 4."),
    "303": ("angle B is 3x+40 degrees", "angle B is 3x+36 degrees", "A", "Congruence gives 5x+20=3x+c, changing x from 10 to 8."),
    "309": ("equilateral side is x+9", "equilateral side is x+6", "B", "Equating x+c to 2x changes x from 9 to 6."),
    "312": ("left triangle angle is 36 degrees", "left triangle angle is 40 degrees", "A", "The vertical/supplementary angle relation changes angle 2 from 68 to 64 degrees."),
    "314": ("lower base angle M is 80 degrees", "lower base angle M is 120 degrees", "B", "In the isosceles trapezoid, angle K changes from 100 to 60 degrees."),
    "319": ("blue similar-rhombus area is 36 square yards", "blue similar-rhombus area is 72 square yards", "B", "The green-to-blue linear scale is 1/2, so its area changes from 9 to 18."),
    "322": ("perpendicular distance MQ is 2x+2", "perpendicular distance MQ is 2x+0", "B", "An angle-bisector point is equidistant from the sides, changing QM from 12 to 8."),
    "324": ("regular-octagon circumradius is 6 cm", "regular-octagon circumradius is 3 cm", "B", "Area scales quadratically, changing 101.8 to 25.5 square cm."),
    "325": ("included angle is 45 degrees", "included angle is 30 degrees", "A", "The parallelogram area changes from 13*10*sin45=91.9 to 65."),
    "326": ("triangle height is 7 ft", "triangle height is 14 ft", "C", "The area changes from 35.7 to 71.4 square ft."),
    "332": ("bearing offset west of south is 50 degrees", "bearing offset west of south is 40 degrees", "220°T", "The true bearing changes from 230 to 220 degrees."),
    "334": ("bearing offset south of east is 28 degrees", "bearing offset south of east is 38 degrees", "128°T", "The true bearing changes from 118 to 128 degrees."),
    "335": ("bearing offset west of south is 32 degrees", "bearing offset west of south is 42 degrees", "222°T", "The true bearing changes from 212 to 222 degrees."),
    "336": ("bearing offset west of north is 31 degrees", "bearing offset west of north is 41 degrees", "319°T", "The true bearing changes from 329 to 319 degrees."),
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    args = parser.parse_args()
    sentinels = [OUT / "config/prospective_expansion_batch3.json", OUT / "validation_cohort/candidate_screening_batch3.jsonl", OUT / "validation_cohort/prospective_generation_manifest_batch3.jsonl"]
    if any(path.exists() for path in sentinels):
        raise FileExistsError("Batch 3 screen is already frozen")
    primary = {int(row["base_problem_id"]) for row in read_jsonl(ROOT / "outputs/stage3b7/config/cohort_manifest.jsonl")}
    historical = {int(row["base_problem_id"]) for row in read_jsonl(ROOT / "outputs/stage3b7/config/validation_manifest.jsonl")}
    prior = {int(row["base_problem_id"]) for name in ("prospective_generation_manifest.jsonl", "prospective_generation_manifest_batch2.jsonl") for row in read_jsonl(OUT / "validation_cohort" / name)}
    selected = {int(value) for value in SPECS}
    validate_disjoint_split(fresh=selected, primary=primary, historical=historical, diagnostic=prior | historical)
    vision = {int(row["problem_index"]): row for row in load_mathverse_rows(args.dataset_root) if str(row["problem_version"]) == "Vision Dominant"}
    eligible = [base for base in range(301, 361) if base in vision]
    if not selected <= set(eligible):
        raise RuntimeError("Batch 3 contains an unavailable Vision-Dominant base")
    frozen_at = datetime.now(timezone.utc).isoformat()
    screen, generation, exclusions = [], [], []
    for base in eligible:
        row = vision[base]
        chosen = str(base) in SPECS
        item = {"base_problem_id": str(base), "example_id": str(row["sample_index"]), "variant": "Vision Dominant", "screening_range": [301, 360], "selected_for_contingency_edit_validation": chosen, "selection_used_attention": False, "selection_used_generation_outcome_for_this_base": False, "selection_used_stage3b7r_causal_outcome": False, "question": row["question"], "ground_truth_answer": row["answer"], "image_reference": row["image"], "frozen_at": frozen_at}
        if chosen:
            fact_o, fact_c, answer_c, validity = SPECS[str(base)]
            item.update({"screening_decision": "prospective_contingency_batch_3", "original_fact": fact_o, "counterfactual_fact": fact_c, "counterfactual_expected_answer": answer_c, "semantic_validity_basis": validity, "edit_tier": "tier1_local_numeric_label"})
            generation.append({"base_problem_id": str(base), "example_id": str(row["sample_index"]), "variant": "Vision Dominant", "selection_reason": "outcome-blind localized numeric evidence with a verified counterfactual answer"})
        else:
            reason = "not selected in bounded contingency screen: no simple verified single-label edit-to-answer mapping"
            item.update({"screening_decision": "not_selected_batch_3", "reason": reason})
            exclusions.append({"base_problem_id": str(base), "example_id": str(row["sample_index"]), "stage": "prospective_visual_screen_batch_3", "reason": reason, "causal_scores_inspected": False, "frozen_at": frozen_at})
        screen.append(item)
    write_json(OUT / "config/prospective_expansion_batch3.json", {"frozen_at": frozen_at, "reason": "The first 9 of 16 prospective generations yielded 6 correct and 3 wrong, making the minimum-12 final yield uncertain; activate the predefined score-blind expansion contingency.", "screening_range": [301, 360], "screened": len(screen), "selected": len(generation), "selected_bases": sorted(selected), "selection_blinding": {"attention_inspected": False, "candidate_base_generation_outcomes_inspected": False, "stage3b7r_causal_scores_exist": False}, "continue_only_as_needed": True})
    write_jsonl(OUT / "validation_cohort/candidate_screening_batch3.jsonl", screen)
    write_jsonl(OUT / "validation_cohort/prospective_screen_exclusions_batch3.jsonl", exclusions)
    write_jsonl(OUT / "validation_cohort/prospective_generation_manifest_batch3.jsonl", generation)
    print(json.dumps({"screened": len(screen), "selected": len(generation), "bases": sorted(selected)}, indent=2))


if __name__ == "__main__":
    main()
