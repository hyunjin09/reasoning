#!/usr/bin/env python3
"""Freeze a second outcome/attention-blind expansion needed to target 40 bases."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a/cohort"

SPECS = [
    ("69", "344", "angle 2 is 35 degrees", "angle 2 is 65 degrees", "A", "180 - 40 - changed angle"),
    ("71", "354", "angle DAC is 78 degrees", "angle DAC is 88 degrees", "B", "parallel-line angle sum"),
    ("72", "359", "quadrilateral perimeter is 16", "quadrilateral perimeter is 12", "C", "triangle perimeter is half the parallelogram perimeter"),
    ("73", "364", "inscribed angle ABC is 70 degrees", "inscribed angle ABC is 60 degrees", "C", "central angle is twice the inscribed angle"),
    ("74", "369", "angle 1 is 115 degrees", "angle 1 is 105 degrees", "C", "same-side supplementary angle"),
    ("75", "374", "the marked angle is 42 degrees", "the marked angle is 34 degrees", "C", "right-angle complement"),
    ("76", "379", "angle 1 is 36 degrees", "angle 1 is 44 degrees", "D", "right-angle complement"),
    ("77", "384", "angle 2 is 60 degrees", "angle 2 is 50 degrees", "D", "parallel-line supplementary angle"),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    args = parser.parse_args()
    screen_path = OUT / "backup_candidate_screening.jsonl"
    manifest_path = OUT / "backup_expansion_generation_manifest.jsonl"
    if screen_path.exists() or manifest_path.exists():
        raise FileExistsError("Backup screen is already frozen")
    dataset = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    stage1_bases = {
        str(json.loads(line)["base_problem_id"])
        for line in (ROOT / "outputs/stage1/discovery/preparation/cohort_attempt_manifest.jsonl").read_text(encoding="utf-8").splitlines()
    }
    first_screen_bases = {
        str(json.loads(line)["base_problem_id"])
        for line in (OUT / "candidate_screening.jsonl").read_text(encoding="utf-8").splitlines()
    }
    frozen_at = datetime.now(timezone.utc).isoformat()
    rows = []
    generation = []
    for base, example, fact_o, fact_c, answer_c, validity in SPECS:
        row = dataset[example]
        if str(row["problem_index"]) != base or row["problem_version"] != "Vision Dominant":
            raise RuntimeError(f"Dataset identity mismatch for backup base {base}")
        if base in stage1_bases or base in first_screen_bases:
            raise RuntimeError(f"Backup base is not unseen/unique: {base}")
        item = {
            "base_problem_id": base,
            "example_id": example,
            "variant": "Vision Dominant",
            "source": "prospective_unseen_backup_expansion",
            "screening_status": "frozen_before_generation",
            "completed_correct_at_screening": None,
            "localized_fact": fact_o,
            "counterfactual_fact": fact_c,
            "counterfactual_expected_answer": answer_c,
            "semantic_validity_basis": validity,
            "edit_tier": "tier1_local_numeric_label",
            "selection_used_attention": False,
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
    write_jsonl(screen_path, rows)
    write_jsonl(manifest_path, generation)
    write_json(
        OUT / "backup_screening_summary.json",
        {
            "frozen_at": frozen_at,
            "unique_bases": len(rows),
            "selection_used_attention": False,
            "new_outcomes_seen": False,
            "rationale": "The first accepted-edit pool could contain at most 33 eligible bases, below the Stage 3A target of 40.",
        },
    )
    print(json.dumps({"frozen": len(rows), "bases": [row["base_problem_id"] for row in rows]}, indent=2))


if __name__ == "__main__":
    main()
