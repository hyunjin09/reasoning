#!/usr/bin/env python3
"""Freeze v2 audit decisions and the combined pre-generation valid set."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b7r"
V2 = OUT / "validation_cohort/edit_validation_batch2_v2"

PASS = {
    "257": "The isolated ED label is cleanly replaced; the dimension bracket and all problem geometry remain intact.",
    "268": "The isolated small-triangle side label is cleanly replaced; the line center remains intact and only boundary antialiasing inside the text ROI changes.",
    "278": "The isolated segment label is cleanly replaced; construction lines and the dimension bracket remain intact.",
    "282": "Only the terminal numeric constant is replaced; the callout arrow, chords, and circle remain intact.",
    "283": "The isolated half-chord label is cleanly replaced; the chord and radius lines remain intact.",
    "296": "Only the terminal numeric constant is replaced; triangle and angle geometry remain intact.",
    "297": "The isolated reference-angle label is cleanly replaced; the callout arrow and parallel-line geometry remain intact.",
    "299": "The isolated hypotenuse label is cleanly replaced; the triangle side below the ROI remains intact.",
}

REJECT = {
    "264": "The corrected ROI still removes the lower tail of the adjacent angle arc.",
    "287": "The corrected ROI erases visible segments of the upper and right triangle sides.",
    "292": "The corrected ROI erases a visible segment of the upper triangle side near the vertex.",
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    expected = {path.name for path in V2.iterdir() if path.is_dir()}
    decided = set(PASS) | set(REJECT)
    if expected != decided:
        raise RuntimeError(f"v2 audit mismatch: missing={sorted(expected-decided)} extra={sorted(decided-expected)}")
    audited_at = datetime.now(timezone.utc).isoformat()
    records, exclusions, v2_valid = [], [], []
    for base in sorted(decided, key=int):
        metadata_path = V2 / base / "edit_metadata.json"
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
            V2 / base / "validation.md",
            f"# Four-image validation — base {base} (batch 2 v2)\n\n"
            "Automatic pixel validation: **PASS**\n\n"
            f"Manual review: **{'PASS' if passed else 'REJECT'}**\n\n{rationale}\n\n"
            "The decision was frozen before prospective generation and causal scoring; attention was not used.\n",
        )
        record = {
            "base_problem_id": base,
            "example_id": metadata["example_id"],
            "edit_version": "batch2_v2",
            "manual_edit_status": "pass" if passed else "reject",
            "rationale": rationale,
            "audited_at": audited_at,
            "prospective_generation_inspected": False,
            "causal_scores_inspected": False,
            "selection_used_attention": False,
        }
        records.append(record)
        if passed:
            v2_valid.append({
                "base_problem_id": base,
                "example_id": metadata["example_id"],
                "edit_version": "batch2_v2",
                "edit_metadata": str(metadata_path.relative_to(ROOT)),
            })
        else:
            exclusions.append({**record, "exclusion_stage": "manual_four_image_validation_v2"})
    write_jsonl(V2 / "manual_validation_manifest.jsonl", records)
    write_jsonl(V2 / "manual_edit_exclusions.jsonl", exclusions)
    write_jsonl(V2 / "manual_valid_generation_manifest.jsonl", v2_valid)

    sources = [
        OUT / "validation_cohort/edit_validation/manual_valid_generation_manifest.jsonl",
        OUT / "validation_cohort/edit_validation_batch2/manual_valid_generation_manifest.jsonl",
        V2 / "manual_valid_generation_manifest.jsonl",
    ]
    combined = []
    for source in sources:
        for row in read_jsonl(source):
            metadata_path = ROOT / row["edit_metadata"]
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            combined.append({
                "base_problem_id": str(row["base_problem_id"]),
                "example_id": str(row["example_id"]),
                "variant": "Vision Dominant",
                "edit_version": metadata.get("edit_version", row.get("selection_stage", "batch1_v1")),
                "edit_metadata": str(metadata_path.relative_to(ROOT)),
                "manual_edit_status": "pass",
                "selection_used_attention": False,
                "generation_outcome_inspected": False,
                "causal_scores_inspected": False,
            })
    combined.sort(key=lambda row: int(row["base_problem_id"]))
    bases = [int(row["base_problem_id"]) for row in combined]
    if len(combined) != 16 or len(set(bases)) != 16:
        raise RuntimeError(f"Expected 16 unique edit-valid bases, got {len(combined)} rows/{len(set(bases))} bases")
    write_jsonl(OUT / "validation_cohort/prospective_generation_eligible.jsonl", combined)
    write_json(
        OUT / "config/validation_edit_valid_freeze.json",
        {
            "frozen_at": audited_at,
            "unique_bases": len(bases),
            "bases": bases,
            "source_sets": [str(path.relative_to(ROOT)) for path in sources],
            "all_manual_edit_pass": True,
            "all_before_generation": True,
            "attention_used": False,
            "causal_scores_existed_or_were_inspected": False,
            "next_filter": "locked-protocol completed-correct generation followed by strict-E_d audit",
        },
    )
    print(json.dumps({"v2_audited": len(records), "v2_pass": len(PASS), "v2_reject": len(REJECT), "combined_valid": len(combined), "bases": bases}, indent=2))


if __name__ == "__main__":
    main()
