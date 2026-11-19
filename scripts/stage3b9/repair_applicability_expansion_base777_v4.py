#!/usr/bin/env python3
"""Tighten base 777's ROI so the unrelated figure note remains untouched."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from prepare_edit_repairs_v2 import render, review_sheet, sha256, text_fits, validate
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"


def main() -> None:
    old_path = OUT / "fresh_edits/applicability_expansion_v3/777/edit_metadata.json"
    old = json.loads(old_path.read_text(encoding="utf-8"))
    base_dir = OUT / "fresh_edits/applicability_expansion_v4/777"
    if base_dir.exists() and any(base_dir.iterdir()):
        raise FileExistsError(f"Base 777 v4 already exists: {base_dir}")
    spec = {"roi": [205, 405, 325, 462], "font": 30, "suffix": "°"}
    anchor = [25, 15]
    source = Path(old["source_image"])
    paths = {name: base_dir / f"{name}/image.png" for name in ("O", "O_sham", "C", "C_sham")}
    ensure_directory(paths["O"].parent)
    shutil.copy2(source, paths["O"])
    for value in (str(old["original"]), str(old["counterfactual"])):
        if not text_fits(f"{value}°", spec, anchor):
            raise RuntimeError("Base 777 v4 text does not fit")
    render(source, paths["O_sham"], value=str(old["original"]), spec=spec, anchor=anchor)
    render(source, paths["C"], value=str(old["counterfactual"]), spec=spec, anchor=anchor)
    render(source, paths["C_sham"], value=str(old["counterfactual"]), spec=spec, anchor=[26, 15])
    checks = validate(paths, spec["roi"])
    if not checks["passed"]:
        raise RuntimeError(f"Automatic base 777 v4 validation failed: {checks}")
    sheet = review_sheet(base_dir, paths, spec["roi"])
    metadata = {
        **{key: old[key] for key in ("base_problem_id", "example_id", "target", "original", "counterfactual", "phase")},
        "edit_version": "stage3b9_applicability_expansion_v4_note_safe",
        "supersedes": str(old_path.relative_to(ROOT)),
        "repair_reason": "ROI-token overlay review showed that v3 encroached on the unrelated figure note.",
        "built_at": datetime.now(timezone.utc).isoformat(),
        "source_image": str(source),
        "source_image_sha256": sha256(source),
        "paths": {name: str(path.relative_to(ROOT)) for name, path in paths.items()},
        "target_evidence_roi_xyxy": spec["roi"],
        "render_suffix": "°",
        "font_size": 30,
        "construction": {
            "renderer": "visual_reasoning.stage3b9.edits.render_preserving_crossing_strokes",
            "same_original_source_for_every_condition": True,
            "semantic_anchor": anchor,
            "sham_anchor": [26, 15],
            "selection_used_attention": False,
            "selection_used_generation_outcomes": False,
            "selection_used_stage3b9_value_vectors": False,
            "selection_used_projected_rank_outcomes": False
        },
        "automatic_validation": checks,
        "manual_validation": {"status": "pending", "reviewer": None},
        "review_sheet": str(sheet.relative_to(ROOT)),
    }
    write_json(base_dir / "edit_metadata.json", metadata)
    write_text(base_dir / "validation.md", "# Stage 3B.9 applicability-expansion base 777 v4\n\nAutomatic validation: **PASS**\n\nManual review: **PENDING**\n")
    write_jsonl(base_dir.parent / "construction_manifest.jsonl", [{
        "base_problem_id": "777", "example_id": str(old["example_id"]), "phase": "phase_a",
        "edit_version": metadata["edit_version"], "edit_metadata": str((base_dir / "edit_metadata.json").relative_to(ROOT)),
        "automatic_edit_status": "pass", "manual_edit_status": "pending", "generation_outcome_inspected": False,
        "stage3b9_value_or_causal_outcome_inspected": False,
    }])
    print(json.dumps({"built": 1, "output": str(base_dir.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
