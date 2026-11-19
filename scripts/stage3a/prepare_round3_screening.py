#!/usr/bin/env python3
"""Freeze 30 outcome- and attention-blind Stage 3A round-3 candidates."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a/cohort"


# Each tuple is base, original fact, counterfactual fact, expected answer under
# the counterfactual, and the prospective geometric relation used to verify it.
SPECS = [
    ("78", "angle ACD is 70 degrees", "angle ACD is 40 degrees", "A", "AED = 90 + ACD/2"),
    ("79", "quadrilateral perimeter is 32", "quadrilateral perimeter is 20", "C", "triangle DCE perimeter is half the parallelogram perimeter"),
    ("80", "cylinder height is 5", "cylinder height is 9", "B", "unrolled half-circumference is 12; sqrt(12^2+9^2)=15"),
    ("83", "minor central angle AOB is 100 degrees", "minor central angle AOB is 120 degrees", "B", "target inscribed angle is half the complementary major arc"),
    ("87", "central angle EOD is 50 degrees", "central angle EOD is 20 degrees", "B", "parallel chords give BOC=(180+EOD)/2"),
    ("89", "inscribed angle ACB is 25 degrees", "inscribed angle ACB is 35 degrees", "B", "BAO = 90 - ACB"),
    ("92", "inscribed angle ADC is 34 degrees", "inscribed angle ADC is 29 degrees", "C", "BOC = 180 - 2*ADC"),
    ("93", "base angle OBC is 40 degrees", "base angle OBC is 35 degrees", "B", "BAC = 90 - OBC"),
    ("94", "perpendicular segment CE is 6", "perpendicular segment CE is 3", "B", "the 45-degree right triangle scales CD from 6sqrt(2) to 3sqrt(2)"),
    ("96", "central angle AOB is 40 degrees", "central angle AOB is 100 degrees", "D", "inscribed angle APB is half the central angle"),
    ("98", "inscribed angle BAC is 50 degrees", "inscribed angle BAC is 40 degrees", "A", "OBC = 90 - BAC"),
    ("99", "inscribed angle ADC is 26 degrees", "inscribed angle ADC is 36 degrees", "D", "CAB = 90 - ADC because AB is a diameter"),
    ("100", "central angle COA is 30 degrees", "central angle COA is 40 degrees", "C", "inscribed angle BAD is half the central angle"),
    ("101", "central angle AOC is 126 degrees", "central angle AOC is 106 degrees", "D", "CDB = (180-AOC)/2"),
    ("103", "inscribed angle ABC is 130 degrees", "inscribed angle ABC is 125 degrees", "B", "minor central angle AOC = 360 - 2*ABC"),
    ("106", "central angle AOD is 136 degrees", "central angle AOD is 108 degrees", "D", "angle C = (180-AOD)/2"),
    ("107", "central angle BOD is 130 degrees", "central angle BOD is 120 degrees", "B", "ACD = (180-BOD)/2"),
    ("109", "exterior angle alpha is 130 degrees", "exterior angle alpha is 120 degrees", "A", "beta = alpha - 90 degrees"),
    ("113", "vertical angle CEB is 110 degrees", "vertical angle CEB is 90 degrees", "B", "equal arcs give BDC=(180-CEB)/2"),
    ("115", "sector angle is 120 degrees", "sector angle is 90 degrees", "B", "sector arc becomes cone circumference: 4pi to 3pi"),
    ("116", "cone height is 12", "cone height is 5", "D", "with slant 13, base radius changes from 5 to 12 and lateral area to 156pi"),
    ("118", "semicircle diameter is 10", "semicircle diameter is 8", "B", "cone base radius is half the semicircle diameter"),
    ("120", "cone height is 4", "cone height is 3", "C", "with slant 5, radius changes from 3 to 4 and base area to 16pi"),
    ("124", "construction scale is 1", "construction scale is 2", "D", "all lengths scale linearly; sector radius changes from 4 to 8"),
    ("125", "sector radius is 30", "sector radius is 15", "A", "120-degree arc gives cone base radius R/3"),
    ("126", "cone slant height is 10", "cone slant height is 16", "D", "lateral area pi*r*l changes from 60pi to 96pi"),
    ("127", "small-circle radius is 1", "small-circle radius is 2", "D", "120-degree sector radius is three times the small-circle radius"),
    ("128", "sector angle is 120 degrees", "sector angle is 90 degrees", "C", "with sector radius 6, cone diameter changes from 4 to 3"),
    ("129", "cone base radius is 5", "cone base radius is 3", "B", "lateral area pi*r*l changes from 50pi to 30pi"),
    ("130", "inscribed angle ACB is 45 degrees", "inscribed angle ACB is 30 degrees", "D", "diameter = chord AB / sin(ACB), changing from 10sqrt(2) to 20"),
]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    args = parser.parse_args()
    screen_path = OUT / "round3_candidate_screening.jsonl"
    manifest_path = OUT / "round3_generation_manifest.jsonl"
    if screen_path.exists() or manifest_path.exists():
        raise FileExistsError("Round-3 prospective screen is already frozen")
    dataset = {
        str(row["problem_index"]): row
        for row in load_mathverse_rows(args.dataset_root)
        if str(row["problem_version"]) == "Vision Dominant"
    }
    attempted = {
        str(row["base_problem_id"])
        for row in read_jsonl(ROOT / "outputs/stage1/discovery/preparation/cohort_attempt_manifest.jsonl")
    }
    prior = set()
    for path in (OUT / "candidate_screening.jsonl", OUT / "backup_candidate_screening.jsonl"):
        prior.update(str(row["base_problem_id"]) for row in read_jsonl(path))
    frozen_at = datetime.now(timezone.utc).isoformat()
    rows = []
    generation = []
    for base, fact_o, fact_c, answer_c, validity in SPECS:
        if base in attempted or base in prior:
            raise RuntimeError(f"Round-3 base is not previously unseen: {base}")
        row = dataset[base]
        example = str(row["sample_index"])
        item = {
            "base_problem_id": base,
            "example_id": example,
            "variant": "Vision Dominant",
            "source": "prospective_unseen_round3_expansion",
            "screening_status": "frozen_before_edit_and_generation",
            "completed_correct_at_screening": None,
            "localized_fact": fact_o,
            "counterfactual_fact": fact_c,
            "counterfactual_expected_answer": answer_c,
            "semantic_validity_basis": validity,
            "edit_tier": "tier1_local_numeric_label",
            "selection_used_attention": False,
            "causal_scores_inspected": False,
            "selection_basis": "unseen unique base; isolated image-only number; counterfactual answer remains among fixed choices",
            "image_reference": row["image"],
            "ground_truth_answer": row["answer"],
            "frozen_at": frozen_at,
        }
        rows.append(item)
        generation.append(
            {
                "example_id": example,
                "base_problem_id": base,
                "variant": "Vision Dominant",
                "selection_reason": item["selection_basis"],
            }
        )
    if len(rows) != 30 or len({row["base_problem_id"] for row in rows}) != 30:
        raise RuntimeError("Round-3 screen must contain 30 unique bases")
    write_jsonl(screen_path, rows)
    write_jsonl(manifest_path, generation)
    write_json(
        OUT / "round3_screening_summary.json",
        {
            "frozen_at": frozen_at,
            "unique_bases": len(rows),
            "selection_used_attention": False,
            "causal_scores_inspected": False,
            "all_previously_unseen_in_stage1": True,
            "reason": "The strict 30-base audit passed, but the complete remaining Stage 1B screen yielded no additional clean items; 30 prospective bases are frozen to target 40--50 final bases.",
        },
    )
    print(json.dumps({"frozen": len(rows), "bases": [row["base_problem_id"] for row in rows]}, indent=2))


if __name__ == "__main__":
    main()
