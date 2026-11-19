#!/usr/bin/env python3
"""Freeze the outcome-blind Stage 3B.7R validation expansion batch 2."""

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


# Selected from bases 253--300 using only the question, image, ground-truth
# answer, and an algebraically verified edit-to-answer mapping. No model
# outcome, attention value, or causal score was available or inspected.
SPECS = {
    "255": ("segment WZ is 14.9", "segment WZ is 22.4", "C", "W lies on the perpendicular bisector of XZ, so WX changes from 14.9 to 22.4"),
    "257": ("segment ED is 5", "segment ED is 4", "B", "AB/AC=12/16 and BE is parallel to CD, so AE changes from 15 to 12"),
    "261": ("rhombus side length is 10", "rhombus side length is 35", "D", "the rhombus perimeter changes from 40 to 140"),
    "262": ("upper trapezoid base is 22 ft", "upper trapezoid base is 21 ft", "B", "with lower base 37 and height 23, area changes from 678.5 to 667"),
    "264": ("angle N is 20x", "angle N is 30x", "B", "adjacent parallelogram angles give 10x+30x=180, so angle M changes from 60 to 45 degrees"),
    "265": ("angle 4 is 2x+23", "angle 4 is 2x+5", "C", "same-side interior angles give (2x+5)+(7x-5)=180, so x changes from 18 to 20"),
    "267": ("arc AC is 122 degrees", "arc AC is 58 degrees", "A", "inscribed angle ABC changes from 61 to 29 degrees"),
    "268": ("small-triangle side NL is 5", "small-triangle side NL is 6", "B", "similarity to the 12-35-37 triangle changes the small perimeter from 35 to 42"),
    "271": ("second diameter is 7x-44", "second diameter is 7x-28", "A", "congruent circles give 3x=7x-28, changing x from 11 to 7"),
    "277": ("large-circle radius GH is 10", "large-circle radius GH is 5", "B", "diameter FH changes from 20 to 10"),
    "278": ("segment W-prime-W is 8", "segment W-prime-W is 4", "B", "with FW=12, FW-prime changes from 4 to 8 and the scale factor changes from 1/3 to 2/3"),
    "280": ("diagonal half is x+4", "diagonal half is x+0", "A", "parallelogram diagonals bisect, so x+0=3x-6 changes x from 5 to 3"),
    "282": ("chord expression is 2x+14", "chord expression is 2x+7", "A", "congruent chords give 9x=2x+7, changing x from 2 to 1"),
    "283": ("half-chord FL is 24", "half-chord FL is 16", "B", "the perpendicular radius bisects FG, changing FG from 48 to 32"),
    "284": ("equal segment is 2x+3", "equal segment is 2x+0", "D", "equal parallel intercepts give 2x=6-x, changing x from 1 to 2"),
    "287": ("upper interior angle is 52 degrees", "upper interior angle is 25 degrees", "C", "the exterior angle changes from 27+52=79 to 27+25=52 degrees"),
    "288": ("angle 3 is 39 degrees", "angle 3 is 42 degrees", "B", "parallel bases make angle 2 equal to angle 3, changing it from 39 to 42 degrees"),
    "289": ("segment PT is 15", "segment PT is 12.5", "A", "ST parallel RQ gives TQ=PT*SR/PS, changing TQ from 6 to 5"),
    "290": ("exterior angle is 123 degrees", "exterior angle is 133 degrees", "B", "with the remote right angle, angle 4 changes from 33 to 43 degrees"),
    "292": ("acute angle is 70 degrees", "acute angle is 20 degrees", "C", "with adjacent leg 15, the hypotenuse changes from 43.86 to 15.96"),
    "293": ("half-diagonal is 7 ft", "half-diagonal is 14 ft", "D", "the rhombus area changes from (24*14)/2=168 to (24*28)/2=336"),
    "294": ("angle MJL is 30 degrees", "angle MJL is 80 degrees", "C", "parallel JK and ML make angle KJL equal to angle MJL, changing it from 30 to 80 degrees"),
    "296": ("equilateral side is 2x+11", "equilateral side is 2x+15", "C", "2x+15=6x-9 changes x from 5 to 6"),
    "297": ("reference angle 1 is 123 degrees", "reference angle 1 is 113 degrees", "C", "two pairs of parallel lines make angle 14 supplementary, changing it from 57 to 67 degrees"),
    "299": ("isosceles-right hypotenuse is 20", "isosceles-right hypotenuse is 10", "B", "each leg changes from 20/sqrt(2)=14.1 to 10/sqrt(2)=7.1"),
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    args = parser.parse_args()
    sentinels = [
        OUT / "config/prospective_expansion_batch2.json",
        OUT / "validation_cohort/candidate_screening_batch2.jsonl",
        OUT / "validation_cohort/prospective_generation_manifest_batch2.jsonl",
    ]
    if any(path.exists() for path in sentinels):
        raise FileExistsError("Batch 2 screen is already frozen")

    primary = {int(row["base_problem_id"]) for row in read_jsonl(OUT / "config/primary_manifest.jsonl")} if (OUT / "config/primary_manifest.jsonl").is_file() else {
        int(row["base_problem_id"]) for row in read_jsonl(ROOT / "outputs/stage3b7/config/cohort_manifest.jsonl")
    }
    historical = {int(row["base_problem_id"]) for row in read_jsonl(ROOT / "outputs/stage3b7/config/validation_manifest.jsonl")}
    diagnostic = {148, 136, 6, 83, 93, 96, 101, 126}
    batch1 = {int(row["base_problem_id"]) for row in read_jsonl(OUT / "validation_cohort/prospective_generation_manifest.jsonl")}
    selected = {int(base) for base in SPECS}
    validate_disjoint_split(fresh=selected, primary=primary, historical=historical, diagnostic=diagnostic | batch1)

    vision = {
        int(row["problem_index"]): row
        for row in load_mathverse_rows(args.dataset_root)
        if str(row["problem_version"]) == "Vision Dominant"
    }
    eligible = [base for base in range(253, 301) if base in vision]
    if not selected <= set(eligible):
        raise RuntimeError("Batch 2 contains an unavailable base")

    frozen_at = datetime.now(timezone.utc).isoformat()
    screen, exclusions, generation = [], [], []
    for base in eligible:
        row = vision[base]
        chosen = str(base) in SPECS
        item = {
            "base_problem_id": str(base),
            "example_id": str(row["sample_index"]),
            "variant": "Vision Dominant",
            "screening_range": [253, 300],
            "selected_for_prospective_generation": chosen,
            "selection_used_attention": False,
            "selection_used_generation_outcome": False,
            "selection_used_stage3b7r_causal_outcome": False,
            "question": row["question"],
            "ground_truth_answer": row["answer"],
            "image_reference": row["image"],
            "frozen_at": frozen_at,
        }
        if chosen:
            fact_o, fact_c, answer_c, validity = SPECS[str(base)]
            item.update({
                "screening_decision": "prospective_generation_batch_2",
                "original_fact": fact_o,
                "counterfactual_fact": fact_c,
                "counterfactual_expected_answer": answer_c,
                "semantic_validity_basis": validity,
                "edit_tier": "tier1_local_numeric_label",
            })
            generation.append({
                "base_problem_id": str(base),
                "example_id": str(row["sample_index"]),
                "variant": "Vision Dominant",
                "selection_reason": "outcome-blind isolated numeric-label edit with a fixed-choice-valid counterfactual",
            })
        else:
            reason = "not selected in bounded batch 2: no prospectively specified clean single-label edit-to-answer mapping"
            item.update({"screening_decision": "not_selected_batch_2", "reason": reason})
            exclusions.append({
                "base_problem_id": str(base),
                "example_id": str(row["sample_index"]),
                "stage": "prospective_visual_screen_batch_2",
                "reason": reason,
                "causal_scores_inspected": False,
                "frozen_at": frozen_at,
            })
        screen.append(item)

    write_json(
        OUT / "config/prospective_expansion_batch2.json",
        {
            "frozen_at": frozen_at,
            "reason": "batch 1 manual edit validation retained only 6 of 24 candidates; expand before generation",
            "screening_range": [253, 300],
            "screened": len(screen),
            "selected": len(generation),
            "selected_bases": sorted(selected),
            "selection_blinding": {
                "attention_inspected": False,
                "generation_outcomes_inspected": False,
                "stage3b7r_causal_scores_exist": False,
            },
            "original_config_unchanged": True,
            "final_selection_rule_unchanged": "ascending base_problem_id among completed-correct, manually edit-valid, strict-E_d-valid cases; retain first 16",
        },
    )
    write_jsonl(OUT / "validation_cohort/candidate_screening_batch2.jsonl", screen)
    write_jsonl(OUT / "validation_cohort/prospective_screen_exclusions_batch2.jsonl", exclusions)
    write_jsonl(OUT / "validation_cohort/prospective_generation_manifest_batch2.jsonl", generation)
    print(json.dumps({"screened": len(screen), "selected": len(generation), "bases": sorted(selected)}, indent=2))


if __name__ == "__main__":
    main()
