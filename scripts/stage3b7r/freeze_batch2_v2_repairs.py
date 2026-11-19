#!/usr/bin/env python3
"""Freeze one geometry-safe repair version for batch-2 edit undercoverage."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b7r"
SOURCE = OUT / "validation_cohort/edit_validation_batch2"

SPECS = {
    "257": {"old": "5", "new": "4", "roi": [1335, 1240, 1405, 1320], "font": 68, "component_bounds": [1351, 1252, 1386, 1310]},
    "264": {"old": "20x", "new": "30x", "roi": [430, 172, 505, 205], "font": 30, "component_bounds": [441, 176, 493, 199]},
    "268": {"old": "5", "new": "6", "roi": [197, 77, 217, 106], "font": 18, "component_bounds": [197, 79, 211, 105]},
    "278": {"old": "8", "new": "4", "roi": [265, 390, 292, 432], "font": 32, "component_bounds": [272, 396, 286, 426]},
    "282": {"old": "14", "new": "7", "roi": [402, 60, 450, 102], "font": 32, "component_bounds": [410, 68, 444, 97]},
    "283": {"old": "24", "new": "16", "roi": [184, 190, 238, 228], "font": 27, "component_bounds": [192, 199, 230, 225]},
    "287": {"old": "52°", "new": "25°", "roi": [275, 60, 342, 104], "font": 35, "component_bounds": [284, 68, 334, 100]},
    "292": {"old": "70°", "new": "20°", "roi": [248, 44, 300, 78], "font": 24, "component_bounds": [256, 48, 293, 72]},
    "296": {"old": "11", "new": "15", "roi": [245, 35, 290, 78], "font": 30, "component_bounds": [253, 43, 281, 73]},
    "297": {"old": "123°", "new": "113°", "roi": [102, 432, 185, 468], "font": 28, "component_bounds": [113, 439, 177, 462]},
    "299": {"old": "20", "new": "10", "roi": [288, 34, 340, 74], "font": 30, "component_bounds": [297, 41, 331, 72]},
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    target = OUT / "config/edit_repair_batch2_v2.json"
    manifest_path = OUT / "validation_cohort/edit_repair_manifest_batch2_v2.jsonl"
    if target.exists() or manifest_path.exists():
        raise FileExistsError("Batch 2 v2 repair is already frozen")
    audit = {row["base_problem_id"]: row for row in read_jsonl(SOURCE / "manual_validation_manifest.jsonl")}
    if set(SPECS) - set(audit):
        raise RuntimeError("Repair contains a base absent from the frozen v1 audit")
    for base in SPECS:
        if audit[base]["manual_edit_status"] != "reject" or "eligible" not in audit[base]["rationale"]:
            raise RuntimeError(f"Base {base} was not prospectively marked eligible for v2")
    frozen_at = datetime.now(timezone.utc).isoformat()
    records = []
    for base in sorted(SPECS, key=int):
        prior = json.loads((SOURCE / base / "edit_metadata.json").read_text(encoding="utf-8"))
        records.append({
            "base_problem_id": base,
            "example_id": prior["example_id"],
            "edit_version": "batch2_v2",
            "supersedes_for_edit_validation_only": "batch2_v1",
            "v1_remains_immutable_reject": True,
            "supported_failure_cause": "v1 ROI did not fully cover the isolated dark-neutral text component",
            "corrected_spec": SPECS[base],
            "correction_basis": "dark-neutral connected-component bounds on the original image plus geometry clearance in the frozen coordinate guide",
            "generation_outcome_inspected": False,
            "causal_scores_inspected": False,
            "attention_used": False,
            "frozen_at": frozen_at,
        })
    write_json(target, {
        "frozen_at": frozen_at,
        "repair_count": len(records),
        "repair_scope": "one versioned ROI-undercoverage correction before generation",
        "same_semantic_edits": True,
        "v1_outputs_immutable": True,
        "no_model_outcomes_existed_or_were_inspected": True,
        "no_causal_scores_existed_or_were_inspected": True,
        "selection_used_attention": False,
        "bases": sorted(int(base) for base in SPECS),
    })
    write_jsonl(manifest_path, records)
    print(json.dumps({"frozen": len(records), "bases": sorted(SPECS, key=int)}, indent=2))


if __name__ == "__main__":
    main()
