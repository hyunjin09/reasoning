#!/usr/bin/env python3
"""Repair the two remaining blinded applicability-expansion edit failures."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from prepare_edit_repairs_v2 import render, review_sheet, sha256, text_fits, validate
from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"
V2 = OUT / "fresh_edits/applicability_expansion_v2"
V3 = OUT / "fresh_edits/applicability_expansion_v3"
REPAIRS = {
    "777": {"roi": [200, 370, 325, 490], "font": 30, "anchor": [28, 58], "reason": "v2 replacement overlapped the A label"},
    "787": {"roi": [65, 190, 108, 275], "font": 30, "anchor": [7, 30], "reason": "v2 ROI erased the enclosed measurement arrow"},
}


def main() -> None:
    if V3.exists() and any(V3.iterdir()):
        raise FileExistsError(f"Applicability expansion v3 already exists: {V3}")
    manifest = []
    built_at = datetime.now(timezone.utc).isoformat()
    for base, repair in REPAIRS.items():
        old_path = V2 / base / "edit_metadata.json"
        old = json.loads(old_path.read_text(encoding="utf-8"))
        spec = {"roi": repair["roi"], "font": repair["font"], "suffix": old["render_suffix"]}
        source = Path(old["source_image"])
        base_dir = V3 / base
        paths = {name: base_dir / f"{name}/image.png" for name in ("O", "O_sham", "C", "C_sham")}
        ensure_directory(paths["O"].parent)
        shutil.copy2(source, paths["O"])
        for value in (str(old["original"]), str(old["counterfactual"])):
            if not text_fits(f"{value}{spec['suffix']}", spec, repair["anchor"]):
                raise RuntimeError(f"Repair text does not fit base {base}")
        render(source, paths["O_sham"], value=str(old["original"]), spec=spec, anchor=repair["anchor"])
        render(source, paths["C"], value=str(old["counterfactual"]), spec=spec, anchor=repair["anchor"])
        sham_anchor = [repair["anchor"][0] + 1, repair["anchor"][1]]
        render(source, paths["C_sham"], value=str(old["counterfactual"]), spec=spec, anchor=sham_anchor)
        checks = validate(paths, spec["roi"])
        if not checks["passed"]:
            raise RuntimeError(f"Automatic v3 validation failed for base {base}: {checks}")
        sheet = review_sheet(base_dir, paths, spec["roi"])
        metadata = {
            **{key: old[key] for key in ("base_problem_id", "example_id", "target", "original", "counterfactual", "phase")},
            "edit_version": "stage3b9_applicability_expansion_v3_localized_repair",
            "supersedes": str(old_path.relative_to(ROOT)),
            "repair_reason": repair["reason"],
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
                "semantic_anchor": repair["anchor"],
                "sham_anchor": sham_anchor,
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
        write_text(base_dir / "validation.md", f"# Stage 3B.9 applicability-expansion v3 — base {base}\n\nAutomatic validation: **PASS**\n\nManual review: **PENDING**\n")
        manifest.append({
            "base_problem_id": base,
            "example_id": str(old["example_id"]),
            "phase": "phase_a",
            "edit_version": metadata["edit_version"],
            "edit_metadata": str((base_dir / "edit_metadata.json").relative_to(ROOT)),
            "automatic_edit_status": "pass",
            "manual_edit_status": "pending",
            "generation_outcome_inspected": False,
            "stage3b9_value_or_causal_outcome_inspected": False,
        })
    write_jsonl(V3 / "construction_manifest.jsonl", manifest)
    print(json.dumps({"built": len(manifest), "output": str(V3.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
