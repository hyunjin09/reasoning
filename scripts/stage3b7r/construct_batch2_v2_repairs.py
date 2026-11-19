#!/usr/bin/env python3
"""Construct the frozen Stage 3B.7R batch-2 v2 repair images."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl, write_text
from visual_reasoning.stage3b3_redesign.images import validate_four_image_conditions

from prepare_batch2_validation_edits import CONDITIONS, make_review_sheet, render


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b7r/validation_cohort"
V1 = OUT / "edit_validation_batch2"
V2 = OUT / "edit_validation_batch2_v2"
REPAIR = OUT / "edit_repair_manifest_batch2_v2.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    if V2.exists() and any(V2.iterdir()):
        raise FileExistsError(f"Batch 2 v2 directory is already non-empty: {V2}")
    ensure_directory(V2)
    built_at = datetime.now(timezone.utc).isoformat()
    records = []
    for repair in read_jsonl(REPAIR):
        base = repair["base_problem_id"]
        spec = repair["corrected_spec"]
        prior = json.loads((V1 / base / "edit_metadata.json").read_text(encoding="utf-8"))
        source = ROOT / prior["paths"]["O"]
        base_dir = V2 / base
        paths = {condition: base_dir / condition / "image.png" for condition in CONDITIONS}
        ensure_directory(paths["O"].parent)
        shutil.copy2(source, paths["O"])
        render(source, paths["O_sham"], text=spec["old"], spec=spec, anchor=[2, 1])
        render(source, paths["C"], text=spec["new"], spec=spec, anchor=[2, 1])
        render(source, paths["C_sham"], text=spec["new"], spec=spec, anchor=[3, 1])
        checks = validate_four_image_conditions(paths, spec["roi"])
        if not checks["passed"]:
            raise RuntimeError(f"Automatic validation failed for base {base}: {checks}")
        sheet = make_review_sheet(base_dir, spec["roi"])
        metadata = {
            **{key: prior[key] for key in (
                "base_problem_id", "example_id", "semantic_classes",
                "counterfactual_expected_answer", "semantic_validity_basis",
            )},
            "batch": 2,
            "edit_version": "batch2_v2",
            "built_at": built_at,
            "v1_metadata": str((V1 / base / "edit_metadata.json").relative_to(ROOT)),
            "v1_manual_status": "reject",
            "v1_outputs_immutable": True,
            "repair_freeze_record": repair,
            "rendered_text": {"O_sham": spec["old"], "C": spec["new"], "C_sham": spec["new"]},
            "paths": {name: str(path.relative_to(ROOT)) for name, path in paths.items()},
            "target_evidence_roi_xyxy": spec["roi"],
            "construction": {
                "renderer": "visual_reasoning.stage3a.edits._render",
                "same_source_image": str(source),
                "same_roi": spec["roi"],
                "same_font_size": spec["font"],
                "O_sham_and_C_anchor": [2, 1],
                "C_sham_anchor": [3, 1],
                "independent_rerender": True,
                "derived_from_C_pixels": False,
            },
            "automatic_validation": checks,
            "manual_validation": {"status": "pending", "reviewer": None},
            "review_sheet": str(sheet.relative_to(ROOT)),
            "selection_used_attention": False,
            "generation_outcome_inspected": False,
            "causal_scores_inspected": False,
        }
        write_json(base_dir / "edit_metadata.json", metadata)
        write_text(
            base_dir / "validation.md",
            f"# Four-image validation — base {base} (batch 2 v2)\n\n"
            "Automatic pixel validation: **PASS**\n\nManual review: **PENDING**\n",
        )
        records.append(metadata)
        print(f"built v2 base {base}", flush=True)
    write_jsonl(V2 / "construction_manifest.jsonl", records)
    print(json.dumps({"built": len(records), "automatic_pass": len(records), "manual_pending": len(records)}, indent=2))


if __name__ == "__main__":
    main()
