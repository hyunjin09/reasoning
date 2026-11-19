#!/usr/bin/env python3
"""Record the manual Stage 3A review decisions for curve-edit candidates."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a"

DECISIONS = {
    "560": "Visible grid discontinuities and curve-rendering differences remain in both the sham and counterfactual image.",
    "567": "The edit leaves visible grid artifacts and an unnaturally rendered replacement curve in the declared plot region.",
    "609": "The edit damages plot borders/grid structure and does not cleanly preserve the original line markers in the sham.",
}


def main() -> None:
    exclusions = []
    for base_problem_id, reason in DECISIONS.items():
        base_dir = OUT / "counterfactuals" / base_problem_id
        metadata_path = base_dir / "edit_metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["manual_validation"] = {
            "status": "reject",
            "reviewer": "Stage 3A primary-agent lossless side-by-side inspection",
            "reason": reason,
        }
        write_json(metadata_path, metadata)
        write_text(
            base_dir / "validation.md",
            f"# Edit Validation — base {base_problem_id}\n\n"
            "Construction-pass automatic checks: **PASS**\n\n"
            "Manual image review: **REJECT**\n\n"
            f"Reason: {reason}\n",
        )
        exclusions.append(
            {
                "base_problem_id": base_problem_id,
                "example_id": metadata["example_id"],
                "stage": "manual_edit_validation",
                "reason": reason,
            }
        )
    write_jsonl(OUT / "cohort/curve_manual_edit_exclusions.jsonl", exclusions)
    print(json.dumps({"rejected": sorted(DECISIONS), "passed": []}, indent=2))


if __name__ == "__main__":
    main()
