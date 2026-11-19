#!/usr/bin/env python3
"""Freeze the blind manual edit audit for the Phase-A applicability expansion."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"
TARGET = OUT / "phase_a_shared/blind_expansion_screen/edit_audit"
SELECTED_VERSION = {
    "776": "applicability_expansion_v2",
    "777": "applicability_expansion_v3",
    "780": "applicability_expansion_v2",
    "782": "applicability_expansion_v2",
    "783": "applicability_expansion_v2",
    "784": "applicability_expansion_v2",
    "786": "applicability_expansion_v2",
}


def main() -> None:
    manifest_path = TARGET / "validated_edit_manifest.jsonl"
    if manifest_path.exists():
        raise FileExistsError(f"Expansion edit audit is already frozen: {manifest_path}")
    frozen_at = datetime.now(timezone.utc).isoformat()
    selected = []
    for base, version in SELECTED_VERSION.items():
        metadata_path = OUT / f"fresh_edits/{version}/{base}/edit_metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["manual_validation"] = {
            "status": "pass",
            "reviewer": "Codex primary agent",
            "frozen_at": frozen_at,
            "review_basis": "Full O/O_sham/C/C_sham sheet and enlarged target crop; no new-base generation, Value vector, attention, or projected-rank result existed.",
            "checks": {
                "target_value_changed_exactly": True,
                "sham_semantics_match": True,
                "target_label_legible": True,
                "unrelated_task_content_unchanged": True,
                "diagram_strokes_preserved": True,
                "dimensions_and_crop_fixed": True,
                "counterfactual_problem_valid": True
            }
        }
        write_json(metadata_path, metadata)
        write_text(
            metadata_path.parent / "validation.md",
            f"# Stage 3B.9 applicability-expansion edit — base {base}\n\n"
            "Automatic containment/dimension validation: **PASS**\n\n"
            "Blind manual semantic and visual validation: **PASS**\n\n"
            "This edit was frozen before generation or new-base Value/projection scoring.\n",
        )
        selected.append({
            "base_problem_id": base,
            "example_id": str(metadata["example_id"]),
            "phase": "phase_a",
            "edit_version": metadata["edit_version"],
            "edit_metadata": str(metadata_path.relative_to(ROOT)),
            "automatic_edit_status": "pass",
            "manual_edit_status": "pass",
            "generation_outcome_inspected": False,
            "stage3b9_value_or_causal_outcome_inspected": False,
        })
    excluded = [{
        "base_problem_id": "787",
        "stage": "blind_manual_edit_validation",
        "reason": "The v2 ROI erased the measurement arrow and the v3 localized repair retained the old 3 glyph, producing ambiguous 33/23 labels.",
        "generation_outcome_inspected": False,
        "stage3b9_value_or_causal_outcome_inspected": False,
    }]
    ensure_directory(TARGET)
    write_jsonl(manifest_path, selected)
    write_jsonl(TARGET / "edit_exclusions.jsonl", excluded)
    write_json(TARGET / "freeze.json", {
        "frozen_at": frozen_at,
        "screened": 8,
        "manual_pass": len(selected),
        "manual_fail": len(excluded),
        "attention_used": False,
        "generation_outcomes_used": False,
        "stage3b9_value_vectors_used": False,
        "projected_rank_outcomes_used": False,
        "selected_base_problem_ids": list(SELECTED_VERSION),
    })
    print(json.dumps({"manual_pass": len(selected), "manual_fail": len(excluded)}, indent=2))


if __name__ == "__main__":
    main()
