#!/usr/bin/env python3
"""Record the completed manual review of existing Stage 3A edit sheets."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PASS = {"119", "136", "140", "141", "147", "148", "154", "155", "753"}
REJECT = {
    "153": "The numeric label intersects the ground segment; masking it visibly removes a task-relevant line segment.",
    "161": "The numeric label overlaps the triangle-ruler outline; masking it changes task-relevant geometry.",
}


def main() -> None:
    reviewed_at = datetime.now(timezone.utc).isoformat()
    exclusions = []
    for base in sorted(PASS | set(REJECT), key=int):
        directory = ROOT / "outputs/stage3a/counterfactuals" / base
        metadata_path = directory / "edit_metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata["manual_validation"]["status"] != "pending":
            raise RuntimeError(f"Manual decision already recorded for base {base}")
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
                    "text_legible": True,
                    "no_accidental_occlusion": True,
                    "dimensions_and_preprocessing_unchanged": True,
                    "counterfactual_logically_interpretable": True,
                },
                "review_method": "construction pass followed by full-resolution original/counterfactual/sham side-by-side inspection",
            }
            status = "PASS"
            detail = "All seven manual edit criteria passed."
        else:
            reason = REJECT[base]
            manual = {
                "status": "reject",
                "reviewer": "primary research agent",
                "reviewed_at": reviewed_at,
                "review_artifact": str((directory / "manual_review_sheet.png").relative_to(ROOT)),
                "reason": reason,
            }
            status = "REJECT"
            detail = reason
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
        metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (directory / "validation.md").write_text(
            "\n".join(
                [
                    f"# Edit Validation — base {base}",
                    "",
                    "Construction-pass automatic checks: **PASS**",
                    "",
                    f"Manual image review: **{status}**",
                    "",
                    detail,
                    "",
                    f"Review sheet: `manual_review_sheet.png`",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
    path = ROOT / "outputs/stage3a/cohort/existing_manual_edit_exclusions.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in exclusions), encoding="utf-8")
    print(json.dumps({"manual_pass": len(PASS), "manual_reject": len(REJECT)}, indent=2))


if __name__ == "__main__":
    main()

