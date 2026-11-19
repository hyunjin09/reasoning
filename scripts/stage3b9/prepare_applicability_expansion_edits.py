#!/usr/bin/env python3
"""Build the outcome-, attention-, and projection-blind applicability expansion edits."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from prepare_edit_repairs_v2 import render, review_sheet, sha256, text_fits, validate
from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"
DATASET = Path("/data/dataset/MathVerse")
SCREEN = OUT / "phase_a_shared/blind_expansion_screen/screening_manifest.json"
EDIT_ROOT = OUT / "fresh_edits/applicability_expansion_v1"


# ROIs are image-space xyxy boxes enclosing the complete source label.
SPECS = {
    "776": {"roi": [375, 655, 510, 730], "font": 25, "suffix": "°"},
    "777": {"roi": [210, 380, 310, 445], "font": 22, "suffix": "°"},
    "780": {"roi": [70, 85, 150, 155], "font": 22, "suffix": ""},
    "782": {"roi": [365, 270, 445, 350], "font": 22, "suffix": ""},
    "783": {"roi": [590, 35, 675, 95], "font": 22, "suffix": "°"},
    "784": {"roi": [195, 90, 285, 155], "font": 22, "suffix": "°"},
    "786": {"roi": [145, 170, 215, 245], "font": 22, "suffix": ""},
    "787": {"roi": [70, 175, 145, 250], "font": 22, "suffix": ""},
}


def main() -> None:
    if EDIT_ROOT.exists() and any(EDIT_ROOT.iterdir()):
        raise FileExistsError(f"Applicability expansion edits already exist: {EDIT_ROOT}")
    screen = json.loads(SCREEN.read_text(encoding="utf-8"))
    selected = screen["selected"]
    if {str(row["base_problem_id"]) for row in selected} != set(SPECS):
        raise RuntimeError("Edit specs must exactly cover the frozen expansion screen")
    rows = {str(row["sample_index"]): row for row in load_mathverse_rows(DATASET)}
    built_at = datetime.now(timezone.utc).isoformat()
    manifest = []
    for item in selected:
        base = str(item["base_problem_id"])
        row = rows[str(item["example_id"])]
        if str(row["problem_index"]) != base or str(row["problem_version"]) != "Vision Dominant":
            raise RuntimeError(f"Dataset identity mismatch for base {base}")
        spec = SPECS[base]
        source = resolve_image_path(DATASET, str(row["image"]))
        base_dir = EDIT_ROOT / base
        paths = {
            "O": base_dir / "O/image.png",
            "O_sham": base_dir / "O_sham/image.png",
            "C": base_dir / "C/image.png",
            "C_sham": base_dir / "C_sham/image.png",
        }
        ensure_directory(paths["O"].parent)
        shutil.copy2(source, paths["O"])
        original = str(item["original"])
        counterfactual = str(item["counterfactual"])
        for value in (original, counterfactual):
            if not text_fits(f"{value}{spec['suffix']}", spec, [4, 2]):
                raise RuntimeError(f"Text does not fit base {base}: {value}{spec['suffix']}")
        render(source, paths["O_sham"], value=original, spec=spec, anchor=[4, 2])
        render(source, paths["C"], value=counterfactual, spec=spec, anchor=[4, 2])
        render(source, paths["C_sham"], value=counterfactual, spec=spec, anchor=[5, 2])
        checks = validate(paths, spec["roi"])
        if not checks["passed"]:
            raise RuntimeError(f"Automatic edit validation failed for base {base}: {checks}")
        sheet = review_sheet(base_dir, paths, spec["roi"])
        metadata = {
            **item,
            "phase": "phase_a",
            "edit_version": "stage3b9_applicability_expansion_v1",
            "built_at": built_at,
            "source_image": str(source),
            "source_image_sha256": sha256(source),
            "paths": {name: str(path.relative_to(ROOT)) for name, path in paths.items()},
            "target_evidence_roi_xyxy": spec["roi"],
            "render_suffix": spec["suffix"],
            "font_size": spec["font"],
            "construction": {
                "renderer": "visual_reasoning.stage3b9.edits.render_preserving_crossing_strokes",
                "same_original_source_for_every_condition": True,
                "semantic_anchor": [4, 2],
                "sham_anchor": [5, 2],
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
        write_text(base_dir / "validation.md", f"# Stage 3B.9 applicability-expansion edit — base {base}\n\nAutomatic validation: **PASS**\n\nManual review: **PENDING**\n")
        manifest.append({
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "phase": "phase_a",
            "edit_version": metadata["edit_version"],
            "edit_metadata": str((base_dir / "edit_metadata.json").relative_to(ROOT)),
            "automatic_edit_status": "pass",
            "manual_edit_status": "pending",
            "generation_outcome_inspected": False,
            "stage3b9_value_or_causal_outcome_inspected": False,
        })
    write_jsonl(EDIT_ROOT / "construction_manifest.jsonl", manifest)
    print(json.dumps({"built": len(manifest), "output": str(EDIT_ROOT.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
