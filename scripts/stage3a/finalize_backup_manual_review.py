#!/usr/bin/env python3
"""Record manual edit review and generation eligibility for backup expansion."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a"
PASSES = {"69", "72", "74", "75", "76"}
REJECTIONS = {
    "71": "The target label overlaps diagonal geometry; the mask leaves a visible line gap.",
    "73": "The target label overlaps two task-relevant radial/chord segments; masking damages both.",
    "77": "The corrected label ROI overlaps the left transversal and removes a long visible segment.",
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
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
            }
            status, reason = "**PASS**", "All seven manual edit checks passed; baseline generation remains outcome-blind."
        else:
            reason = REJECTIONS[base]
            metadata["manual_validation"] = {
                "status": "reject",
                "reviewer": "Stage 3A primary-agent lossless side-by-side inspection",
                "reason": reason,
            }
            exclusions.append({"base_problem_id": base, "example_id": metadata["example_id"], "stage": "manual_edit_validation", "reason": reason})
            status = "**REJECT**"
        write_json(metadata_path, metadata)
        write_text(base_dir / "validation.md", f"# Edit Validation — base {base}\n\nAutomatic checks: **PASS**\n\nManual review: {status}\n\nReason: {reason}\n")
    frozen_generation = read_jsonl(OUT / "cohort/backup_expansion_generation_manifest.jsonl")
    eligible_generation = [row for row in frozen_generation if str(row["base_problem_id"]) in PASSES]
    write_jsonl(OUT / "cohort/backup_valid_generation_manifest.jsonl", eligible_generation)
    write_jsonl(OUT / "cohort/backup_manual_edit_exclusions.jsonl", exclusions)
    print(json.dumps({"passed": len(PASSES), "rejected": len(REJECTIONS), "generation_examples": len(eligible_generation)}, indent=2))


if __name__ == "__main__":
    main()
