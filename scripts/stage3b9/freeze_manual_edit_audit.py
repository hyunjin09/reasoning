#!/usr/bin/env python3
"""Freeze the outcome-blind Stage 3B.9 v2 manual edit audit."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"
V2 = OUT / "fresh_edits/v2"
PHASE_A_REJECTS = {
    "661": "original italic radius label remained connected to the preserved radius stroke",
    "684": "leading original digit remained, producing 119/123 rather than 19/23",
    "685": "original height value remained below the rerendered value",
    "692": "original digit remained connected to the arrow, obscuring the counterfactual value",
    "707": "original side-length label remained below the rerendered value",
}


def main() -> None:
    frozen_at = datetime.now(timezone.utc).isoformat()
    construction = [json.loads(line) for line in (V2 / "construction_manifest.jsonl").read_text().splitlines() if line]
    audit = []
    phase_a_valid = []
    phase_b_valid = []
    exclusions = []
    for row in construction:
        base = str(row["base_problem_id"])
        phase = row["phase"]
        rejected = phase == "phase_a" and base in PHASE_A_REJECTS
        status = "reject" if rejected else "pass"
        reason = PHASE_A_REJECTS.get(base)
        metadata_path = ROOT / row["edit_metadata"]
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["manual_validation"] = {
            "status": status,
            "reviewer": "primary_agent_visual_review",
            "frozen_at": frozen_at,
            "review_basis": "all rendered full images and enlarged target ROI crops; no model outcomes inspected",
            "reason": reason,
            "checks": {
                "target_values_legible_and_exact": not rejected,
                "original_value_fully_removed_in_rerenders": not rejected,
                "crossing_diagram_strokes_preserved": not rejected,
                "unrelated_task_relevant_content_unchanged": not rejected,
                "dimensions_and_crop_fixed": True,
            },
        }
        write_json(metadata_path, metadata)
        decision = "PASS" if not rejected else "REJECT"
        write_text(
            metadata_path.parent / "validation.md",
            f"# Stage 3B.9 v2 edit validation — base {base}\n\n"
            "Automatic containment/dimension validation: **PASS**\n\n"
            f"Manual semantic and geometry review: **{decision}**\n\n"
            f"Reason: {reason or 'All values were exact and legible; original label was removed; crossing geometry and unrelated content were retained.'}\n\n"
            "The decision was frozen before prospective generation or any Stage 3B.9 Value/causal scoring.\n",
        )
        audited = {
            **row,
            "manual_edit_status": status,
            "manual_audit_frozen_at": frozen_at,
            "rejection_reason": reason,
            "generation_outcome_inspected": False,
            "stage3b9_value_or_causal_outcome_inspected": False,
        }
        audit.append(audited)
        if rejected:
            exclusions.append({
                "base_problem_id": base,
                "phase": phase,
                "stage": "v2_manual_edit_validation",
                "reason": reason,
                "edit_metadata": row["edit_metadata"],
                "outcome_blind": True,
            })
        elif phase == "phase_a":
            phase_a_valid.append(audited)
        else:
            phase_b_valid.append(audited)
    if len(phase_a_valid) != 35 or len(phase_b_valid) != 16 or len(exclusions) != 5:
        raise RuntimeError("Unexpected frozen manual-audit counts")
    write_jsonl(V2 / "manual_edit_audit.jsonl", audit)
    write_jsonl(OUT / "phase_a_shared/prospective_edit_manifest.jsonl", phase_a_valid)
    write_jsonl(OUT / "phase_b_local/prospective_edit_manifest.jsonl", phase_b_valid)
    write_jsonl(OUT / "exclusions/edit_validation_exclusions.jsonl", exclusions)
    write_json(OUT / "config/manual_edit_audit_freeze.json", {
        "frozen_at": frozen_at,
        "screened": 56,
        "phase_a_screened": 40,
        "phase_a_manual_pass": 35,
        "phase_a_manual_reject": 5,
        "phase_b_screened": 16,
        "phase_b_manual_pass": 16,
        "generation_outcomes_inspected": False,
        "stage3b9_value_or_causal_outcomes_inspected": False,
        "phase_a_rejected_base_problem_ids": sorted(PHASE_A_REJECTS, key=int),
    })
    print(json.dumps({"phase_a_valid": 35, "phase_b_valid": 16, "rejected": 5}, indent=2))


if __name__ == "__main__":
    main()
