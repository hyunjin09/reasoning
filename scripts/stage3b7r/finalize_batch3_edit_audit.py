#!/usr/bin/env python3
"""Freeze the score-blind manual four-image audit for contingency batch 3 v3."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b7r"
EDIT_ROOT = OUT / "validation_cohort/edit_validation_batch3_v3"

PASS = {
    "302": "The GJ total label is cleanly replaced; the dimension brace and all triangle geometry remain legible.",
    "303": "The complete angle expression is cleanly replaced; the callout arc and both triangles remain intact.",
    "309": "The isolated side expression is cleanly replaced without changing the triangle side.",
    "312": "The isolated 36-degree label is cleanly replaced; the baseline and adjacent angle labels remain intact.",
    "314": "The isolated base-angle label is cleanly replaced; both trapezoid bases and legs remain intact.",
    "319": "Only the blue-rhombus area digits are changed, using the original blue text color; units and geometry remain intact.",
    "322": "The complete MQ expression is cleanly replaced without changing segment MQ or the right-angle marker.",
    "324": "The isolated radius label is cleanly replaced; the radius segment and octagon remain intact.",
    "325": "The isolated included-angle label is cleanly replaced; the parallelogram boundary remains intact.",
    "332": "The isolated bearing-offset label is cleanly replaced; the ray and north-south axis remain intact.",
    "334": "The isolated bearing-offset label is cleanly replaced; the ray, angle sector, and axes remain intact.",
}

REJECT = {
    "326": "The text ROI removes a segment of the task-relevant dashed altitude, violating the unchanged-context requirement.",
    "335": "The text ROI touches the task-relevant bearing ray immediately above the label, leaving an avoidable line artifact.",
    "336": "The text ROI touches the task-relevant bearing ray immediately beside the label, leaving an avoidable line artifact.",
}


def main() -> None:
    expected = {path.name for path in EDIT_ROOT.iterdir() if path.is_dir()}
    decided = set(PASS) | set(REJECT)
    if expected != decided:
        raise RuntimeError(f"Batch-3 v3 audit mismatch: missing={sorted(expected-decided)} extra={sorted(decided-expected)}")
    audited_at = datetime.now(timezone.utc).isoformat()
    records, exclusions, valid = [], [], []
    for base in sorted(decided, key=int):
        metadata_path = EDIT_ROOT / base / "edit_metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        passed = base in PASS
        rationale = (PASS if passed else REJECT)[base]
        metadata["manual_validation"] = {
            "status": "pass" if passed else "reject",
            "reviewer": "primary_agent_visual_audit",
            "audited_at": audited_at,
            "rationale": rationale,
            "audit_blinding": {
                "prospective_generation_inspected": False,
                "causal_scores_inspected": False,
                "attention_used": False,
            },
        }
        write_json(metadata_path, metadata)
        write_text(
            EDIT_ROOT / base / "validation.md",
            f"# Four-image validation — base {base} (batch 3 v3)\n\n"
            "Automatic pixel validation: **PASS**\n\n"
            f"Manual review: **{'PASS' if passed else 'REJECT'}**\n\n{rationale}\n\n"
            "The decision was frozen before prospective generation and causal scoring; attention was not used.\n",
        )
        record = {
            "base_problem_id": base,
            "example_id": str(metadata["example_id"]),
            "edit_version": "batch3_v3",
            "manual_edit_status": "pass" if passed else "reject",
            "rationale": rationale,
            "audited_at": audited_at,
            "prospective_generation_inspected": False,
            "causal_scores_inspected": False,
            "selection_used_attention": False,
        }
        records.append(record)
        if passed:
            valid.append(
                {
                    "base_problem_id": base,
                    "example_id": str(metadata["example_id"]),
                    "variant": "Vision Dominant",
                    "edit_version": "batch3_v3",
                    "edit_metadata": str(metadata_path.relative_to(ROOT)),
                    "manual_edit_status": "pass",
                    "selection_used_attention": False,
                    "generation_outcome_inspected": False,
                    "causal_scores_inspected": False,
                }
            )
        else:
            exclusions.append({**record, "exclusion_stage": "manual_four_image_validation_batch3_v3"})
    write_jsonl(EDIT_ROOT / "manual_validation_manifest.jsonl", records)
    write_jsonl(EDIT_ROOT / "manual_edit_exclusions.jsonl", exclusions)
    write_jsonl(EDIT_ROOT / "manual_valid_generation_manifest.jsonl", valid)
    write_json(
        OUT / "config/batch3_edit_validation_freeze.json",
        {
            "frozen_at": audited_at,
            "screened": len(decided),
            "manual_pass": len(PASS),
            "manual_reject": len(REJECT),
            "eligible_bases": sorted(map(int, PASS)),
            "rejected_bases": sorted(map(int, REJECT)),
            "v1_and_v2_status": "preserved failed construction history; neither version was eligible for inference",
            "attention_used": False,
            "candidate_generation_outcomes_existed_or_were_inspected": False,
            "causal_scores_existed_or_were_inspected": False,
            "continue_only_as_needed": True,
        },
    )
    print(json.dumps({"audited": len(records), "pass": len(PASS), "reject": len(REJECT), "eligible_bases": sorted(map(int, PASS))}, indent=2))


if __name__ == "__main__":
    main()
