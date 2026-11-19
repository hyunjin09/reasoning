#!/usr/bin/env python3
"""Archive failed Stage 3C.9 v1 edits and build score-blind v2 repairs."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage3c9.edits import construct_quartet, sha256


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"
CAUSAL_SCORES_AVAILABLE = False


# These changes address only defects observed in lossless v1 image review.
# No causal score or attention measurement existed when they were frozen.
REPAIRS: dict[str, dict[str, Any]] = {
    "104": {"roi_xyxy": [105, 62, 145, 94], "font_size": 20, "text_anchor": [1, 0], "renderer": "rectangle"},
    "128": {"roi_xyxy": [101, 86, 170, 118], "font_size": 14, "text_anchor": [2, 1], "renderer": "rectangle"},
    "129": {"roi_xyxy": [60, 174, 86, 195], "font_size": 17, "text_anchor": [2, 0], "renderer": "rectangle"},
    "142": {"roi_xyxy": [301, 126, 321, 160], "font_size": 20, "text_anchor": [1, 0], "renderer": "rectangle"},
    "149": {"roi_xyxy": [132, 145, 183, 190], "font_size": 22, "text_anchor": [1, 0], "renderer": "rectangle"},
    "161": {"roi_xyxy": [100, 64, 131, 96], "font_size": 18, "text_anchor": [1, 1], "renderer": "rectangle"},
    "226": {"roi_xyxy": [210, 160, 260, 215], "font_size": 22, "text_anchor": [1, 0], "renderer": "rectangle"},
    "254": {"roi_xyxy": [134, 75, 168, 109], "font_size": 20, "text_anchor": [1, 0], "renderer": "rectangle"},
    "331": {"roi_xyxy": [165, 160, 225, 195], "font_size": 20, "text_anchor": [1, 0], "renderer": "rectangle"},
    "353": {"roi_xyxy": [132, 113, 180, 142], "font_size": 18, "text_anchor": [1, 0], "renderer": "rectangle"},
    "363": {"roi_xyxy": [1, 77, 73, 106], "font_size": 18, "text_anchor": [1, 0], "renderer": "preserve_crossing_strokes"},
    "425": {"roi_xyxy": [104, 40, 152, 68], "font_size": 16, "text_anchor": [1, 0], "renderer": "rectangle"},
    "675": {"roi_xyxy": [425, 178, 530, 218], "font_size": 24, "text_anchor": [1, 0], "renderer": "rectangle"},
    "743": {"roi_xyxy": [346, 42, 366, 69], "font_size": 18, "text_anchor": [1, 0], "renderer": "rectangle"},
    "752": {"roi_xyxy": [274, 130, 293, 158], "font_size": 18, "text_anchor": [1, 0], "renderer": "rectangle"},
    "762": {"roi_xyxy": [140, 250, 195, 290], "font_size": 22, "text_anchor": [1, 0], "renderer": "rectangle"},
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    archive_root = OUT / "cohort/edit_versions/v1"
    probe_root = OUT / "cohort/work/edit_repair_probe_v2"
    log_path = OUT / "cohort/edit_repair_log_v2.jsonl"
    if archive_root.exists() or probe_root.exists() or log_path.exists():
        raise FileExistsError("Stage 3C.9 v2 edit repair outputs are create-once")
    specs = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "cohort/work/all_edit_specs.jsonl")}
    repaired_specs: dict[str, dict[str, Any]] = {}
    for base, repair in REPAIRS.items():
        spec = {**specs[base], **repair}
        spec["repair_reason"] = "v1 lossless review found a misplaced/tight ROI, retained source glyph, or erased crossing stroke"
        spec["attention_used"] = False
        spec["causal_scores_available"] = False
        repaired_specs[base] = spec

    # Prove every repair passes containment before moving any v1 artifact.
    for base, spec in repaired_specs.items():
        metadata = read_json(OUT / "counterfactuals" / base / "edit_metadata.json")
        construct_quartet(source_image=Path(metadata["source_image"]), target_dir=probe_root / base, spec=spec)

    repaired_at = datetime.now(timezone.utc).isoformat()
    records = []
    for base, spec in repaired_specs.items():
        base_dir = OUT / "counterfactuals" / base
        archive = archive_root / base
        archive.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(base_dir), str(archive))
        previous = read_json(archive / "edit_metadata.json")
        built = construct_quartet(source_image=Path(previous["source_image"]), target_dir=base_dir, spec=spec)
        metadata = {
            **previous,
            **spec,
            "edit_version": "stage3c9_v2",
            "built_at": repaired_at,
            "source_image_sha256": sha256(Path(previous["source_image"])),
            "paths": {name: str(path.relative_to(ROOT)) for name, path in built["paths"].items()},
            "target_evidence_roi_xyxy": [int(value) for value in spec["roi_xyxy"]],
            "construction": built["construction"],
            "automatic_validation": built["automatic_validation"],
            "manual_validation": {"status": "pending", "reviewer": None, "causal_scores_available": False},
            "review_sheet": str(built["review_sheet"].relative_to(ROOT)),
            "construction_history": [
                {"version": 1, "status": "failed_manual_review", "archive": str(archive.relative_to(ROOT)), "causal_scores_available": False},
                {"version": 2, "status": "pending_manual_review", "built_at": repaired_at, "causal_scores_available": False},
            ],
        }
        write_json(base_dir / "edit_metadata.json", metadata)
        (base_dir / "validation.md").write_text(
            f"# Stage 3C.9 edit validation — base {base}, construction v2\n\n"
            "Automatic containment/dimension validation: **PASS**\n\nManual review: **PENDING**\n\n"
            f"The failed v1 is preserved at `{archive.relative_to(ROOT)}`. No causal scores existed when this repair was frozen.\n",
            encoding="utf-8",
        )
        records.append({
            "base_problem_id": base,
            "failed_version": 1,
            "repair_version": 2,
            "reason": spec["repair_reason"],
            "archive": str(archive.relative_to(ROOT)),
            "attention_used": False,
            "causal_scores_available": False,
            "repaired_at": repaired_at,
        })
    write_jsonl(log_path, records)
    print(json.dumps({"repaired_v2": len(records), "automatic_pass": len(records), "causal_scores_available": False}, indent=2))


if __name__ == "__main__":
    main()
