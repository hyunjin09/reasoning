#!/usr/bin/env python3
"""Repair the blinded v1 applicability-expansion edit boxes."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from prepare_edit_repairs_v2 import render, review_sheet, sha256, text_fits, validate
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"
V1 = OUT / "fresh_edits/applicability_expansion_v1"
V2 = OUT / "fresh_edits/applicability_expansion_v2"


# The v1 boxes ended within the source glyphs. These outcome-blind replacements
# enclose each complete original label with padding.
REPAIRS = {
    "776": {"roi": [365, 640, 535, 765], "font": 30},
    "777": {"roi": [200, 370, 325, 490], "font": 30},
    "780": {"roi": [60, 75, 160, 180], "font": 30},
    "782": {"roi": [350, 255, 465, 385], "font": 30},
    "783": {"roi": [575, 20, 695, 120], "font": 30},
    "784": {"roi": [185, 80, 305, 190], "font": 30},
    "786": {"roi": [130, 155, 230, 290], "font": 30},
    "787": {"roi": [55, 160, 160, 295], "font": 30},
}


def main() -> None:
    if V2.exists() and any(V2.iterdir()):
        raise FileExistsError(f"Applicability expansion v2 already exists: {V2}")
    items = [json.loads(line) for line in (V1 / "construction_manifest.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    if {str(row["base_problem_id"]) for row in items} != set(REPAIRS):
        raise RuntimeError("Repair family must exactly cover the blinded v1 manual failures")
    built_at = datetime.now(timezone.utc).isoformat()
    manifest = []
    for item in items:
        base = str(item["base_problem_id"])
        old = json.loads((ROOT / item["edit_metadata"]).read_text(encoding="utf-8"))
        spec = {"roi": REPAIRS[base]["roi"], "font": REPAIRS[base]["font"], "suffix": old["render_suffix"]}
        source = Path(old["source_image"])
        base_dir = V2 / base
        paths = {name: base_dir / f"{name}/image.png" for name in ("O", "O_sham", "C", "C_sham")}
        ensure_directory(paths["O"].parent)
        shutil.copy2(source, paths["O"])
        for value in (str(old["original"]), str(old["counterfactual"])):
            if not text_fits(f"{value}{spec['suffix']}", spec, [8, 8]):
                raise RuntimeError(f"Repair text does not fit base {base}")
        render(source, paths["O_sham"], value=str(old["original"]), spec=spec, anchor=[8, 8])
        render(source, paths["C"], value=str(old["counterfactual"]), spec=spec, anchor=[8, 8])
        render(source, paths["C_sham"], value=str(old["counterfactual"]), spec=spec, anchor=[9, 8])
        checks = validate(paths, spec["roi"])
        if not checks["passed"]:
            raise RuntimeError(f"Automatic v2 validation failed for base {base}: {checks}")
        sheet = review_sheet(base_dir, paths, spec["roi"])
        metadata = {
            **{key: old[key] for key in ("base_problem_id", "example_id", "target", "original", "counterfactual", "phase")},
            "edit_version": "stage3b9_applicability_expansion_v2_complete_label_box",
            "supersedes": item["edit_metadata"],
            "repair_reason": "Blinded v1 manual review found that the edit ROI ended within the original label glyphs.",
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
                "semantic_anchor": [8, 8],
                "sham_anchor": [9, 8],
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
        write_text(base_dir / "validation.md", f"# Stage 3B.9 applicability-expansion v2 — base {base}\n\nAutomatic validation: **PASS**\n\nManual review: **PENDING**\n")
        manifest.append({
            **item,
            "edit_version": metadata["edit_version"],
            "edit_metadata": str((base_dir / "edit_metadata.json").relative_to(ROOT)),
            "manual_edit_status": "pending",
        })
    write_jsonl(V2 / "construction_manifest.jsonl", manifest)
    print(json.dumps({"built": len(manifest), "output": str(V2.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
