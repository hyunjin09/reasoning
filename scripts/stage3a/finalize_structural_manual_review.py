#!/usr/bin/env python3
"""Record the completed manual review of Stage 3A structural graph edits."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PASS = {"613", "614", "616", "617"}
REJECT = {"615": "The original sharp-drop vertex leaves a visible residual point on the x-axis after the counterfactual redraw."}


def main() -> None:
    reviewed_at = datetime.now(timezone.utc).isoformat()
    exclusions = []
    for base in sorted(PASS | set(REJECT), key=int):
        directory = ROOT / "outputs/stage3a/counterfactuals" / base
        path = directory / "edit_metadata.json"
        metadata = json.loads(path.read_text(encoding="utf-8"))
        if metadata["manual_validation"]["status"] != "pending":
            raise RuntimeError(f"Manual decision already recorded for {base}")
        if base in PASS:
            manual = {
                "status": "pass",
                "reviewer": "primary research agent",
                "reviewed_at": reviewed_at,
                "review_artifact": str((directory / "manual_review_sheet.png").relative_to(ROOT)),
                "checks": {
                    "target_fact_changed_exactly_as_intended": True,
                    "sham_retains_original_fact": True,
                    "unrelated_task_relevant_content_unchanged": True,
                    "trajectory_legible": True,
                    "no_accidental_occlusion": True,
                    "dimensions_and_preprocessing_unchanged": True,
                    "counterfactual_matches_an_existing_answer_choice": True,
                },
                "review_method": "construction pass followed by full-resolution original/counterfactual/sham side-by-side inspection",
            }
            status, detail = "PASS", "All seven manual structural-edit criteria passed."
        else:
            reason = REJECT[base]
            manual = {
                "status": "reject",
                "reviewer": "primary research agent",
                "reviewed_at": reviewed_at,
                "review_artifact": str((directory / "manual_review_sheet.png").relative_to(ROOT)),
                "reason": reason,
            }
            status, detail = "REJECT", reason
            exclusions.append(
                {
                    "base_problem_id": base,
                    "example_id": metadata["example_id"],
                    "stage": "manual_edit_validation",
                    "reason": reason,
                    "model_outcome_was_considered": False,
                    "selection_used_attention": False,
                }
            )
        metadata["manual_validation"] = manual
        path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (directory / "validation.md").write_text(
            f"# Edit Validation — base {base}\n\nConstruction-pass automatic checks: **PASS**\n\nManual image review: **{status}**\n\n{detail}\n\nReview sheet: `manual_review_sheet.png`\n",
            encoding="utf-8",
        )
    path = ROOT / "outputs/stage3a/cohort/structural_manual_edit_exclusions.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in exclusions), encoding="utf-8")
    print(json.dumps({"manual_pass": len(PASS), "manual_reject": len(REJECT)}, indent=2))


if __name__ == "__main__":
    main()

