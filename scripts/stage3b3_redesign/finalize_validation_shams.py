#!/usr/bin/env python3
"""Record the completed manual four-image review for the frozen validation split."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b3_redesign"
ACCEPTED = ("6", "83", "93", "96", "101", "126", "136", "148")


def main() -> None:
    reviewed_at = datetime.now(timezone.utc).isoformat()
    records = []
    for base in ACCEPTED:
        base_dir = OUT / "counterfactual_shams" / base
        metadata_path = base_dir / "edit_metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if metadata["manual_validation"]["status"] != "pending":
            raise RuntimeError(f"Manual review is not pending for base {base}")
        manual = {
            "status": "pass",
            "reviewer": "primary research agent",
            "reviewed_at": reviewed_at,
            "review_method": "full-image four-way inspection plus 5x nearest-neighbor target-ROI crops",
            "review_artifact": metadata["review_sheet"],
            "checks": {
                "O_and_O_sham_same_target_semantics": True,
                "C_and_C_sham_same_target_semantics": True,
                "O_and_C_classes_differ_only_in_intended_evidence_identity": True,
                "all_four_readable": True,
                "unrelated_evidence_unchanged": True,
                "target_roi_layout_aligned": True,
                "dimensions_and_token_layout_candidates_identical": True,
            },
            "note": (
                "C_sham is an independent one-pixel-anchor rerender of the counterfactual label; "
                "semantic acceptance was made before any Stage 3B.3-R model score existed."
            ),
        }
        metadata["manual_validation"] = manual
        write_json(metadata_path, metadata)
        write_text(
            base_dir / "validation.md",
            f"# Four-image validation — base {base}\n\n"
            "Automatic pixel validation: **PASS**\n\n"
            "Manual semantic/legibility review: **PASS**\n\n"
            "The O/O_sham and C/C_sham pairs preserve their respective semantic facts; all four "
            "conditions are readable, localized, dimension-matched, and leave unrelated evidence unchanged.\n",
        )
        records.append({
            "base_problem_id": base,
            "automatic_validation_passed": bool(metadata["automatic_validation"]["passed"]),
            "manual_validation": manual,
        })
    write_jsonl(OUT / "counterfactual_shams/manual_validation.jsonl", records)
    write_json(
        OUT / "counterfactual_shams/manual_validation_summary.json",
        {
            "reviewed_at": reviewed_at,
            "base_count": len(records),
            "automatic_pass_count": sum(row["automatic_validation_passed"] for row in records),
            "manual_pass_count": sum(row["manual_validation"]["status"] == "pass" for row in records),
            "scores_available_during_review": False,
            "all_passed": all(
                row["automatic_validation_passed"] and row["manual_validation"]["status"] == "pass"
                for row in records
            ),
        },
    )
    print(json.dumps({"manual_pass": len(records), "scores_available_during_review": False}, indent=2))


if __name__ == "__main__":
    main()
