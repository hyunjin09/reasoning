#!/usr/bin/env python3
"""Finalize the score-blind Stage 3B.7-R cohort-construction record."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b7r"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    cohort = read_json(OUT / "validation_cohort/strict_ed_freeze_summary.json")
    generation = read_json(OUT / "validation_cohort/generation_collection_summary.json")
    manifest = read_jsonl(OUT / "validation_cohort/fresh_validation_manifest.jsonl")
    if not 12 <= len(manifest) <= 16:
        raise RuntimeError("Final cohort report requires 12--16 frozen fresh bases")
    split_path = OUT / "config/validation_primary_split.json"
    split = read_json(split_path)
    frozen_bases = [int(row["base_problem_id"]) for row in manifest]
    if split["fresh_validation_bases"] not in (None, frozen_bases):
        raise FileExistsError("Fresh validation split was already finalized with a different cohort")
    split.update({
        "fresh_validation_bases": frozen_bases,
        "fresh_validation_status": "frozen after completed-correct, manual four-image, strict-E_d, and ROI-independent eligibility checks; causal scores not yet available",
        "fresh_validation_count": len(manifest),
    })
    protected = set(split["primary_bases"]) | set(split["historical_validation_bases"]) | set(split["target_selection_diagnostic_bases"])
    if protected & set(split["fresh_validation_bases"]):
        raise RuntimeError("Final fresh validation bases overlap a protected cohort")
    write_json(split_path, split)
    screened_first = read_jsonl(OUT / "validation_cohort/candidate_screening.jsonl")
    screened_second = read_jsonl(OUT / "validation_cohort/candidate_screening_batch2.jsonl")
    screened_contingency = read_jsonl(OUT / "validation_cohort/candidate_screening_batch3.jsonl")
    edit_eligible = read_jsonl(OUT / "validation_cohort/prospective_generation_eligible.jsonl")
    contingency_eligible = read_jsonl(OUT / "validation_cohort/edit_validation_batch3_v3/manual_valid_generation_manifest.jsonl")
    lines = [
        "# Stage 3B.7-R fresh-cohort expansion", "",
        f"- Outcome-blind candidate rows reviewed across the two initial screens and one contingency screen: **{len(screened_first) + len(screened_second) + len(screened_contingency)}** (**{len(screened_first) + len(screened_second)} initial + {len(screened_contingency)} contingency**)",
        f"- Initial four-condition edit-valid generation pool: **{len(edit_eligible)}**",
        f"- Additional manually edit-valid contingency bases: **{len(contingency_eligible)}**",
        f"- Initial prospective generations: **{generation['total']}**",
        "- Contingency prospective generations: **0** (not needed after the strict audit retained 13 initial cases)",
        f"- Correct / wrong / truncated / invalid: **{generation['correct']} / {generation['wrong']} / {generation['truncated']} / {generation['invalid']}**",
        f"- Strict-E_d accepted / rejected: **{cohort['accepted']} / {cohort['rejected']}**",
        f"- Final fresh validation bases: **{', '.join(cohort['accepted_base_problem_ids'])}**", "",
        "The fresh cohort is disjoint from the immutable 37-base primary cohort, the old eight validation bases, and the target-selection diagnostic set. Selection used neither raw attention nor causal outcomes. All causal scoring remained unavailable through this freeze.", "",
        "Base 214 received a pre-score semantic-name correction from DAB to FAB after full-resolution review; no pixels, generation artifacts, or model outcomes were changed.", "",
    ]
    write_text(OUT / "validation_cohort/expansion_summary.md", "\n".join(lines))


if __name__ == "__main__":
    main()
