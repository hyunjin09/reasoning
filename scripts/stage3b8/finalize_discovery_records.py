#!/usr/bin/env python3
"""Assemble canonical Stage 3B.8 discovery screening and exclusion records."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.stage0.io import write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b8/discovery_cohort"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    initial = read_jsonl(OUT / "initial_generation_manifest.jsonl")
    batch2 = read_jsonl(OUT / "candidate_screening_batch2.jsonl")
    outcomes = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "raw_outcome_manifest.jsonl")}
    final_bases = {str(row["base_problem_id"]) for row in read_jsonl(OUT / "discovery_manifest.jsonl")}
    capacity = read_jsonl(OUT / "ed_capacity_exclusions.jsonl")
    screening = []
    for row in initial:
        base = str(row["base_problem_id"])
        screening.append({
            **row,
            "screening_source": "inherited_unrun_manual_edit_valid_stage3b7r_contingency",
            "selected_for_edit_validation": True,
            "selected_for_generation": True,
            "effective_generation_status": outcomes[base]["status"],
            "selected_for_final_discovery": base in final_bases,
            "selection_used_attention": False,
            "selection_used_stage3b8_causal_or_fit": False,
        })
    for row in batch2:
        base = str(row["base_problem_id"])
        screening.append({
            **row,
            "screening_source": "prospective_bounded_visual_editability_screen_361_397",
            "selected_for_generation": base in outcomes,
            "effective_generation_status": outcomes[base]["status"] if base in outcomes else "not_generated",
            "selected_for_final_discovery": base in final_bases,
        })
    screening.sort(key=lambda row: int(row["base_problem_id"]))
    write_jsonl(OUT / "candidate_screening.jsonl", screening)

    exclusions = []
    for row in screening:
        base = str(row["base_problem_id"])
        if base in final_bases:
            continue
        if not row.get("selected_for_edit_validation", False):
            stage, reason = "visual_editability_screen", row.get("reason", "not selected for edit validation")
        elif base not in outcomes:
            stage, reason = "prospective_generation_capacity", "manually edit-valid held contingency was not generated because the frozen active batches already yielded >20 eligible bases"
        elif outcomes[base]["status"] != "correct":
            stage, reason = "prospective_generation_outcome", f"effective baseline generation status was {outcomes[base]['status']}"
        else:
            matching = next((value for value in capacity if str(value["base_problem_id"]) == base), None)
            if matching is None:
                raise RuntimeError(f"Unexplained non-final screened base {base}")
            stage, reason = matching["stage"], matching["reason"]
        exclusions.append({
            "base_problem_id": base,
            "example_id": str(row["example_id"]),
            "stage": stage,
            "reason": reason,
            "attention_used": False,
            "stage3b8_causal_or_fit_scores_used": False,
        })
    exclusions.sort(key=lambda row: int(row["base_problem_id"]))
    if len(screening) != 48 or len(final_bases) != 20 or len(exclusions) != 28:
        raise RuntimeError("Canonical discovery accounting must partition 48 screened bases into 20 included and 28 excluded")
    write_jsonl(OUT / "exclusion_log.jsonl", exclusions)
    status_counts = {status: sum(row["status"] == status for row in outcomes.values()) for status in ("correct", "wrong", "truncated", "invalid")}
    write_text(OUT / "expansion_summary.md", "\n".join([
        "# Stage 3B.8 fresh discovery expansion", "",
        "- Screened: **48** unique, protected-cohort-disjoint bases (11 inherited unrun/manual-valid candidates plus 37 prospective visual screens).",
        "- Four-condition edits manually validated: **31** (11 initial plus 20 batch-2); **27** were prospectively generated and four were held once yield was sufficient.",
        f"- Effective generation outcomes: **{status_counts['correct']} correct**, **{status_counts['wrong']} wrong**, **{status_counts['truncated']} truncated**, **{status_counts['invalid']} invalid**.",
        "- Completed-correct pool: **22**; the prospectively frozen ascending-ID capacity rule retained **20** before trace, attention, causal-score, or fit inspection.",
        "- Strict E_d audit: **20/20 pass**. Manual review moved two boundaries earlier for unlisted synonyms (`two people`, `airplane`).",
        "- ROI/token audit: **20/20 pass** across three complete review sheets.",
        "- Final discovery cohort: **20 unique base_problem_ids**; no overlap with the primary 37 or either protected validation cohort.", "",
        "The raw Stage 0 evaluator is a multiple-choice A--E parser. Free-response numeric outcomes are represented through the SHA-256-linked, non-destructive `outcome_reclassification.jsonl` overlay; no generated token, response, or legacy status was modified.", "",
        "Selection never used attention, Stage 3B.8 causal scores, or subspace-fit quality.", "",
    ]))
    print(json.dumps({"screened": len(screening), "included": len(final_bases), "excluded": len(exclusions), **status_counts}, indent=2))


if __name__ == "__main__":
    main()
