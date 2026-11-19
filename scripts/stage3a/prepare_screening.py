#!/usr/bin/env python3
"""Freeze the attention-blind Stage 3A candidate and expansion screen."""

from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "outputs/stage3a/cohort"


# These edits were chosen from question/image geometry and answer choices before
# any new model outcome was generated. Each changes one visible number and keeps
# the counterfactual answer among the original multiple-choice options.
EXPANSION: dict[str, tuple[str, str, str, str]] = OrderedDict(
    [
        ("1", ("angle A is 80 degrees", "angle A is 60 degrees", "C", "triangle angle sum and parallel line")),
        ("2", ("angle 1 is 50 degrees", "angle 1 is 60 degrees", "B", "parallel lines and angle bisector")),
        ("3", ("angle BCD is 70 degrees", "angle BCD is 80 degrees", "B", "parallel lines and angle bisector")),
        ("5", ("angle 1 is 50 degrees", "angle 1 is 40 degrees", "B", "vertical angles")),
        ("6", ("angle 1 is 50 degrees", "angle 1 is 60 degrees", "B", "same-side supplementary angles")),
        ("9", ("AB is 6", "AB is 7", "B", "tangent-length perimeter identity")),
        ("10", ("angle A is 36 degrees", "angle A is 30 degrees", "C", "isosceles and perpendicular-bisector geometry")),
        ("14", ("angle OAB is 35 degrees", "angle OAB is 30 degrees", "C", "central and inscribed angles")),
        ("16", ("angle BOC is 50 degrees", "angle BOC is 60 degrees", "D", "parallel chord-radius geometry")),
        ("20", ("angle DOB is 140 degrees", "angle DOB is 100 degrees", "C", "central and inscribed angles")),
        ("22", ("angle DAC is 28 degrees", "angle DAC is 18 degrees", "D", "rhombus diagonals bisect angles")),
        ("24", ("angle 1 is 50 degrees", "angle 1 is 30 degrees", "A", "same-side supplementary angles")),
        ("29", ("angle A is 50 degrees", "angle A is 60 degrees", "A", "intersection of internal angle bisectors")),
        ("31", ("angle 2 is 65 degrees", "angle 2 is 55 degrees", "C", "parallel and perpendicular lines")),
        ("32", ("angle DEF is 52 degrees", "angle DEF is 56 degrees", "A", "incenter angle relation")),
        ("34", ("angle 1 is 100 degrees", "angle 1 is 80 degrees", "D", "parallel-line supplementary angles")),
        ("38", ("angle 1 is 70 degrees", "angle 1 is 75 degrees", "B", "isosceles triangle and parallel line")),
        ("40", ("angle 1 is 50 degrees", "angle 1 is 60 degrees", "D", "parallel-line corresponding angles")),
        ("45", ("angle C is 35 degrees", "angle C is 75 degrees", "D", "central angle is twice inscribed angle")),
        ("48", ("angle BOC is 100 degrees", "angle BOC is 160 degrees", "C", "major-arc inscribed angle")),
        ("53", ("angle 1 is 55 degrees", "angle 1 is 65 degrees", "D", "parallel-line corresponding angles")),
        ("54", ("angle 1 is 40 degrees", "angle 1 is 50 degrees", "B", "right-angle ruler geometry")),
        ("55", ("angle AOC is 70 degrees", "angle AOC is 90 degrees", "C", "angle bisection and straight line")),
        ("56", ("angle DCF is 20 degrees", "angle DCF is 10 degrees", "B", "inscribed and central angles")),
        ("58", ("angle AEC is 35 degrees", "angle AEC is 25 degrees", "A", "parallel-line angle sum")),
        ("60", ("angle 2 is 135 degrees", "angle 2 is 150 degrees", "A", "parallel-line supplementary angles")),
        ("61", ("angle D is 74 degrees", "angle D is 79 degrees", "C", "isosceles triangle and parallel line")),
        ("62", ("angle BAE is 40 degrees", "angle BAE is 30 degrees", "A", "parallel-line supplementary angles")),
        ("65", ("angle 4 is 30 degrees", "angle 4 is 35 degrees", "C", "parallel-line angle relations")),
        ("66", ("angle B is 20 degrees", "angle B is 30 degrees", "C", "parallel-line broken-transversal sum")),
        ("67", ("angle ACD is 40 degrees", "angle ACD is 20 degrees", "C", "parallel line and angle bisector")),
    ]
)


ADDITIONAL_STAGE1 = OrderedDict(
    [
        ("136", ("679", "tree shadow BC is 9", "localized numeric label")),
        ("141", ("704", "building/shadow diagram contains 2, 3, and 15", "localized numeric label")),
        ("147", ("734", "height diagram contains 1.5, 1, and 6", "localized numeric label")),
        ("154", ("769", "ladder diagram contains 0.55, 1.4, and 1.6", "localized numeric label")),
        ("544", ("2719", "highlighted graph interval is 5 to 15", "localized marker edit")),
        ("546", ("2729", "highlighted graph interval is 1 to 5", "localized marker edit")),
        ("617", ("3084", "speed-time polyline has an editable segment", "localized structural redraw")),
        ("751", ("3754", "cylinder label is 30", "localized numeric label")),
    ]
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    screening_path = OUTPUT / "candidate_screening.jsonl"
    if screening_path.exists():
        raise FileExistsError(f"Frozen screening already exists: {screening_path}")
    dataset_rows = json.loads((args.dataset_root / "testmini.json").read_text(encoding="utf-8"))
    by_variant = {(str(row["problem_index"]), str(row["problem_version"])): row for row in dataset_rows}
    outcomes = {str(row["example_id"]): row for row in read_jsonl(ROOT / "outputs/stage1/discovery/raw_outcome_manifest.jsonl")}
    cohort = {str(row["example_id"]): row for row in read_jsonl(ROOT / "outputs/stage2c/cohort/cohort_manifest.jsonl")}
    ready = read_jsonl(ROOT / "outputs/stage2c/candidates/counterfactual_ready_candidates.jsonl")

    first_ready_by_base: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for candidate in ready:
        base = str(cohort[str(candidate["example_id"])]["base_problem_id"])
        first_ready_by_base.setdefault(base, candidate)

    frozen_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, Any]] = []
    for base, candidate in first_ready_by_base.items():
        example_id = str(candidate["example_id"])
        outcome = outcomes[example_id]
        rows.append(
            {
                "base_problem_id": base,
                "example_id": example_id,
                "variant": outcome["variant"],
                "source": "stage2c_counterfactual_ready",
                "screening_status": "candidate_pending_edit_validation",
                "completed_correct_at_screening": True,
                "localized_fact": candidate["semantic_fact"],
                "edit_tier": "tier1_or_tier3_as_recorded",
                "selection_used_attention": False,
                "selection_basis": candidate["selection_basis"],
                "frozen_at": frozen_at,
            }
        )

    for base, (example_id, fact, edit_kind) in ADDITIONAL_STAGE1.items():
        outcome = outcomes[example_id]
        if not outcome["completed"] or not outcome["correct"]:
            raise RuntimeError(f"Expected completed-correct Stage 1 example {example_id}")
        rows.append(
            {
                "base_problem_id": base,
                "example_id": example_id,
                "variant": outcome["variant"],
                "source": "remaining_stage1b_manual_screen",
                "screening_status": "candidate_pending_event_and_edit_validation",
                "completed_correct_at_screening": True,
                "localized_fact": fact,
                "edit_tier": edit_kind,
                "selection_used_attention": False,
                "selection_basis": "completed-correct; local editable visual fact; image/question inspected without ROI-attention timing",
                "frozen_at": frozen_at,
            }
        )

    expansion_manifest: list[dict[str, Any]] = []
    for base, (fact_o, fact_c, answer_c, relation) in EXPANSION.items():
        row = by_variant[(base, "Vision Dominant")]
        example_id = str(row["sample_index"])
        item = {
            "base_problem_id": base,
            "example_id": example_id,
            "variant": "Vision Dominant",
            "source": "prospective_unseen_expansion",
            "screening_status": "frozen_before_generation",
            "completed_correct_at_screening": None,
            "localized_fact": fact_o,
            "counterfactual_fact": fact_c,
            "counterfactual_expected_answer": answer_c,
            "semantic_validity_basis": relation,
            "edit_tier": "tier1_local_numeric_label",
            "selection_used_attention": False,
            "selection_basis": "unseen base; local image-only number; counterfactual answer remains among fixed choices",
            "image_reference": row["image"],
            "ground_truth_answer": row["answer"],
            "frozen_at": frozen_at,
        }
        rows.append(item)
        expansion_manifest.append(
            {
                "example_id": example_id,
                "base_problem_id": base,
                "variant": "Vision Dominant",
                "selection_reason": item["selection_basis"],
            }
        )

    bases = [row["base_problem_id"] for row in rows]
    if len(bases) != len(set(bases)):
        raise RuntimeError("Candidate screen must contain unique base_problem_id rows")
    write_jsonl(screening_path, rows)
    write_jsonl(OUTPUT / "expansion_generation_manifest.jsonl", expansion_manifest)
    summary = {
        "frozen_at": frozen_at,
        "selection_used_attention": False,
        "existing_stage2c_candidates": len(first_ready_by_base),
        "additional_stage1b_candidates": len(ADDITIONAL_STAGE1),
        "prospective_unseen_generation_candidates": len(EXPANSION),
        "total_screened_unique_bases": len(rows),
        "locked_generation_protocol": {
            "name": "official",
            "do_sample": True,
            "temperature": 0.6,
            "top_p": 0.95,
            "top_k": 20,
            "repetition_penalty": 1.0,
            "seed": 1234,
            "max_new_tokens": 40960,
        },
    }
    (OUTPUT / "screening_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
