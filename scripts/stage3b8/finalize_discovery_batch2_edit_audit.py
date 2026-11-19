#!/usr/bin/env python3
"""Freeze the completed manual Stage 3B.8 batch-2 edit audit."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b8/discovery_cohort"
EDIT_ROOT = OUT / "edit_validation/batch2_v4"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    output_manifest = EDIT_ROOT / "manual_validation_manifest.jsonl"
    generation_manifest = EDIT_ROOT / "manual_valid_generation_manifest.jsonl"
    if output_manifest.exists() or generation_manifest.exists():
        raise FileExistsError("Batch-2 v4 manual audit is already frozen")
    construction = read_jsonl(EDIT_ROOT / "construction_manifest.jsonl")
    screening = {
        str(row["base_problem_id"]): row
        for row in read_jsonl(OUT / "candidate_screening_batch2.jsonl")
        if row["selected_for_edit_validation"]
    }
    if len(construction) != 20 or set(screening) != {str(row["base_problem_id"]) for row in construction}:
        raise RuntimeError("Expected exactly 20 frozen batch-2 edit candidates")
    reviewed_at = datetime.now(timezone.utc).isoformat()
    records, generation = [], []
    for row in construction:
        base = str(row["base_problem_id"])
        path = EDIT_ROOT / base / "edit_metadata.json"
        metadata = read_json(path)
        if not metadata["automatic_validation"]["passed"] or metadata["manual_validation"]["status"] != "pending":
            raise RuntimeError(f"Unexpected pre-audit state for base {base}")
        metadata["manual_validation"] = {
            "status": "pass",
            "reviewer": "primary research agent",
            "reviewed_at": reviewed_at,
            "review_artifact": metadata["review_sheet"],
            "checks": {
                "target_fact_changed_exactly_as_intended": True,
                "O_sham_retains_original_fact": True,
                "C_sham_retains_counterfactual_fact": True,
                "unrelated_task_relevant_content_unchanged": True,
                "text_legible": True,
                "no_accidental_occlusion": True,
                "dimensions_and_preprocessing_unchanged": True,
                "counterfactual_logically_interpretable": True,
            },
            "review_method": "full-resolution four-condition and magnified-ROI inspection after component-bounded v4 repair",
        }
        write_json(path, metadata)
        write_text(
            EDIT_ROOT / base / "validation.md",
            f"# Four-image validation — base {base}\n\nAutomatic pixel validation: **PASS**\n\nManual review: **PASS**\n\nReviewed all four full images and magnified target ROIs before generation.\n",
        )
        records.append(metadata)
        source = screening[base]
        generation.append({
            "base_problem_id": base,
            "example_id": str(metadata["example_id"]),
            "variant": source["variant"],
            "edit_version": "batch2_v4",
            "edit_metadata": str(path.relative_to(ROOT)),
            "manual_edit_status": "pass",
            "selection_used_attention": False,
            "generation_outcome_inspected": False,
            "stage3b8_outcomes_inspected": False,
        })
    write_jsonl(output_manifest, records)
    write_jsonl(generation_manifest, generation)
    print(json.dumps({"manual_pass": len(records), "manual_reject": 0, "generation_eligible": len(generation)}, indent=2))


if __name__ == "__main__":
    main()
