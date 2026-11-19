#!/usr/bin/env python3
"""Freeze manual edit validation and generation eligibility for round 3."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a"

PASSES = {
    "78", "79", "80", "83", "87", "93", "94", "96", "98", "100", "101", "103",
    "106", "107", "109", "113", "116", "118", "120", "124", "125", "126", "128",
}

REJECTIONS = {
    "89": "v2 retains the leading source digit, yielding an ambiguous composite label.",
    "92": "v2 retains a visible source-glyph fragment beside both rendered labels.",
    "99": "the corrected ROI removes a task-relevant portion of the C-D segment.",
    "115": "v2 retains the leading source digit, yielding an ambiguous composite sector angle.",
    "127": "the corrected ROI removes a visible portion of the small-circle outline.",
    "129": "v2 leaves a visible source-glyph fragment below the replacement radius.",
    "130": "the corrected ROI removes task-relevant chord segments adjacent to the angle label.",
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    if len(PASSES) != 23 or len(REJECTIONS) != 7 or PASSES & set(REJECTIONS):
        raise RuntimeError("Round-3 manual review must partition all 30 frozen candidates")
    exclusions = []
    for base in sorted(PASSES | set(REJECTIONS), key=int):
        base_dir = OUT / "counterfactuals" / base
        metadata_path = base_dir / "edit_metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        if base in PASSES:
            metadata["manual_validation"] = {
                "status": "pass",
                "reviewer": "Stage 3A primary-agent lossless side-by-side inspection",
                "checks": [
                    "target fact changed exactly as intended",
                    "sham retained the original fact",
                    "unrelated task-relevant content unchanged",
                    "replacement label legible",
                    "no accidental occlusion observed",
                    "dimensions unchanged",
                    "counterfactual remains logically interpretable",
                ],
                "model_outcomes_available_at_review": False,
            }
            status = "**PASS**"
            reason = "All seven manual edit checks passed before round-3 generation."
        else:
            reason = REJECTIONS[base]
            metadata["manual_validation"] = {
                "status": "reject",
                "reviewer": "Stage 3A primary-agent lossless side-by-side inspection",
                "reason": reason,
                "model_outcomes_available_at_review": False,
            }
            status = "**REJECT**"
            exclusions.append(
                {
                    "base_problem_id": base,
                    "example_id": str(metadata["example_id"]),
                    "stage": "round3_manual_edit_validation",
                    "reason": reason,
                    "causal_scores_inspected": False,
                    "generation_outcome_available": False,
                }
            )
        write_json(metadata_path, metadata)
        write_text(
            base_dir / "validation.md",
            f"# Edit Validation — base {base}\n\nAutomatic checks: **PASS**\n\nManual review: {status}\n\nReason: {reason}\n",
        )
    frozen = read_jsonl(OUT / "cohort/round3_generation_manifest.jsonl")
    valid = [row for row in frozen if str(row["base_problem_id"]) in PASSES]
    write_jsonl(OUT / "cohort/round3_valid_generation_manifest.jsonl", valid)
    write_jsonl(OUT / "cohort/round3_manual_edit_exclusions.jsonl", exclusions)
    print(json.dumps({"screened": 30, "passed": len(valid), "rejected": len(exclusions), "generation_examples": len(valid)}, indent=2))


if __name__ == "__main__":
    main()
