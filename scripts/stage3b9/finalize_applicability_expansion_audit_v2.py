#!/usr/bin/env python3
"""Freeze the corrected edit/ROI-ready applicability-expansion manifest."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"
TARGET = OUT / "phase_a_shared/blind_expansion_screen/edit_audit_v2"
VERSIONS = {
    "776": "applicability_expansion_v2", "777": "applicability_expansion_v4",
    "780": "applicability_expansion_v2", "782": "applicability_expansion_v2",
    "783": "applicability_expansion_v2", "784": "applicability_expansion_v2",
    "786": "applicability_expansion_v2",
}


def main() -> None:
    target = TARGET / "validated_edit_manifest.jsonl"
    if target.exists():
        raise FileExistsError(f"Corrected expansion audit already exists: {target}")
    frozen_at = datetime.now(timezone.utc).isoformat()
    rows = []
    for base, version in VERSIONS.items():
        metadata_path = OUT / f"fresh_edits/{version}/{base}/edit_metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["manual_validation"] = {
            "status": "pass", "reviewer": "Codex primary agent", "frozen_at": frozen_at,
            "review_basis": "Full condition sheet plus enlarged target crop; base 777 v4 also verified the unrelated figure note is unchanged.",
            "checks": {"target_value_changed_exactly": True, "sham_semantics_match": True,
                       "target_label_legible": True, "unrelated_task_content_unchanged": True,
                       "diagram_strokes_preserved": True, "dimensions_and_crop_fixed": True,
                       "counterfactual_problem_valid": True},
        }
        write_json(metadata_path, metadata)
        write_text(metadata_path.parent / "validation.md", f"# Stage 3B.9 applicability expansion — base {base}\n\nBlind manual edit validation: **PASS**\n\nFrozen before generation or new-base Value/projection scoring.\n")
        rows.append({"base_problem_id": base, "example_id": str(metadata["example_id"]), "phase": "phase_a",
                     "edit_version": metadata["edit_version"], "edit_metadata": str(metadata_path.relative_to(ROOT)),
                     "automatic_edit_status": "pass", "manual_edit_status": "pass",
                     "generation_outcome_inspected": False, "stage3b9_value_or_causal_outcome_inspected": False})
    exclusions = [
        {"base_problem_id": "787", "stage": "blind_manual_edit_validation", "reason": "No version cleanly removed the old glyph while preserving the enclosed measurement arrow.",
         "generation_outcome_inspected": False, "stage3b9_value_or_causal_outcome_inspected": False},
        {"base_problem_id": "777", "edit_version": "stage3b9_applicability_expansion_v3_localized_repair", "stage": "ROI-overlay-informed edit correction",
         "reason": "Superseded before generation because the v3 ROI encroached on the unrelated figure note; v4 is the frozen replacement.",
         "generation_outcome_inspected": False, "stage3b9_value_or_causal_outcome_inspected": False},
    ]
    ensure_directory(TARGET)
    write_jsonl(target, rows)
    write_jsonl(TARGET / "edit_exclusions_and_supersessions.jsonl", exclusions)
    write_json(TARGET / "freeze.json", {"frozen_at": frozen_at, "selected": len(rows), "rejected_base_count": 1,
        "superseded_edit_version_count": 1, "attention_used": False, "generation_outcomes_used": False,
        "stage3b9_value_vectors_used": False, "projected_rank_outcomes_used": False,
        "selected_base_problem_ids": list(VERSIONS)})
    print(json.dumps({"selected": len(rows), "rejected_bases": 1, "superseded_versions": 1}, indent=2))


if __name__ == "__main__":
    main()
