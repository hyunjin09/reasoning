#!/usr/bin/env python3
"""Record the complete attention-blind screen of remaining Stage 1B base problems."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a/cohort"


REASONS = {
    "27": "All editable numeric givens are repeated in the question text; an image-only change would create prompt-image conflict.",
    "68": "The target evidence is distributed across the full geometric partition; no single localized edit preserves all unrelated task-relevant structure.",
    "82": "The editable angle values are repeated in the question text; an image-only change would create prompt-image conflict.",
    "121": "The editable lengths are repeated in the question text; an image-only change would create prompt-image conflict.",
    "137": "The editable support dimensions are repeated in the question text; an image-only change would create prompt-image conflict.",
    "139": "The editable tube and candle dimensions are repeated in the question text; an image-only change would create prompt-image conflict.",
    "146": "The editable ladder dimensions are repeated in the question text; an image-only change would create prompt-image conflict.",
    "152": "The editable ladder dimensions are repeated in the question text; an image-only change would create prompt-image conflict.",
    "550": "The prompt fixes the garden area at 100, so changing the plotted hyperbola alone would make the visual evidence inconsistent with the text.",
    "551": "The prompt fixes the quadratic formula; changing the graph alone would create a prompt-image conflict rather than a clean visual counterfactual.",
    "565": "The editable evidence is the full plotted curve/root configuration, not a localized fact; a clean C1/C2 local edit is unavailable.",
    "575": "The editable evidence is the full plotted curve/root configuration, not a localized fact; a clean C1/C2 local edit is unavailable.",
    "579": "The target evidence is the global relative decay trajectory of two curves; no localized fact edit leaves other task-relevant evidence fixed.",
    "594": "A local intercept shift would not change the semantic answer ('cost of buying the tablet'), while changing the task relation would require a global curve edit.",
    "618": "Changing the relationship class requires replacing the full curve; the target is not a localized visual fact and a clean sham-matched edit is unavailable.",
    "621": "Changing the relationship class requires replacing the full curve; the target is not a localized visual fact and a clean sham-matched edit is unavailable.",
    "622": "The formula and comparison line y=4 are specified in the question text; an image-only change would conflict with the prompt.",
    "760": "The answer depends on the global circle/tangent construction; moving or replacing a local element changes multiple geometric relations.",
    "768": "The area relation is fixed in the prompt and the remaining visual evidence is the global shaded-region topology, not a clean local fact.",
    "788": "All editable similarity and ratio facts are stated in the question text; an image-only change would create prompt-image conflict.",
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    output = OUT / "remaining_stage1_screening.jsonl"
    summary_path = OUT / "remaining_stage1_screening_summary.json"
    if output.exists() or summary_path.exists():
        raise FileExistsError("Remaining Stage 1B screen is already frozen")
    cohort = read_jsonl(ROOT / "outputs/stage1/discovery/cohort_manifest.jsonl")
    prior = read_jsonl(OUT / "candidate_screening.jsonl") + read_jsonl(OUT / "backup_candidate_screening.jsonl")
    prior_bases = {str(row["base_problem_id"]) for row in prior}
    first_by_base = {}
    for row in cohort:
        first_by_base.setdefault(str(row["base_problem_id"]), row)
    remaining = sorted(set(first_by_base) - prior_bases, key=int)
    if set(remaining) != set(REASONS):
        raise RuntimeError(f"Remaining Stage 1B base set changed: {remaining}")
    frozen_at = datetime.now(timezone.utc).isoformat()
    rows = []
    for base in remaining:
        source = first_by_base[base]
        rows.append(
            {
                "base_problem_id": base,
                "example_id": str(source["example_id"]),
                "variant": source["variant"],
                "source": "complete_remaining_stage1b_manual_screen",
                "screening_status": "rejected_before_edit_or_scoring",
                "completed_correct_at_screening": True,
                "selection_used_attention": False,
                "causal_scores_inspected": False,
                "rejection_reason": REASONS[base],
                "frozen_at": frozen_at,
            }
        )
    write_jsonl(output, rows)
    write_json(
        summary_path,
        {
            "frozen_at": frozen_at,
            "screened_unique_bases": len(rows),
            "accepted": 0,
            "rejected": len(rows),
            "selection_used_attention": False,
            "causal_scores_inspected": False,
            "implication": "Existing Stage 1B artifacts cannot raise the provisional 30-base pool to the 40-base target; prospective expansion is required.",
        },
    )
    print(json.dumps({"screened": len(rows), "accepted": 0, "rejected": len(rows)}, indent=2))


if __name__ == "__main__":
    main()
