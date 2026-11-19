#!/usr/bin/env python3
"""Build attention- and outcome-independent ROI-token mappings for fresh edits."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from transformers import AutoProcessor

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import ensure_directory, write_jsonl, write_text
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3b9.edits import changed_mask_from_conditions
from visual_reasoning.stage3b7.roi import (
    build_roi_token_groups,
    cell_darkness,
    choose_matched_irrelevant,
    fixed_ring,
    map_changed_pixels_to_tokens,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9/roi_validation"
DATASET = Path("/data/dataset/MathVerse")
CHECKPOINT = Path("/data/dataset/huggingface/hub/models--Qwen--Qwen3-VL-4B-Thinking/snapshots/1de27d8c51f12e819435303b9e84c4e25ba8401e")
sys.path.insert(0, str(ROOT / "scripts/stage3b7r"))
from build_fresh_roi_audit import make_review_sheets, overlay  # noqa: E402


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    mapping_path = OUT / "roi_token_mapping_draft.jsonl"
    if mapping_path.exists():
        raise FileExistsError(f"Fresh ROI draft already exists: {mapping_path}")
    items = [
        *read_jsonl(ROOT / "outputs/stage3b9/phase_a_shared/prospective_edit_manifest.jsonl"),
        *read_jsonl(ROOT / "outputs/stage3b9/phase_b_local/prospective_edit_manifest.jsonl"),
    ]
    if len(items) != 51 or len({str(row["base_problem_id"]) for row in items}) != 51:
        raise RuntimeError("Fresh ROI mapping requires the 51 unique manually valid edits")
    data = {str(row["sample_index"]): row for row in load_mathverse_rows(DATASET)}
    processor = AutoProcessor.from_pretrained(CHECKPOINT, local_files_only=True)
    mappings, overlays = [], []
    for item in items:
        base = str(item["base_problem_id"])
        edit = read_json(ROOT / item["edit_metadata"])
        if edit["manual_validation"]["status"] != "pass":
            raise RuntimeError(f"Manual edit validation failed for base {base}")
        conditions = list(edit["paths"])
        expected = 4 if item["phase"] == "phase_a" else 10
        if len(conditions) != expected or conditions[0:2] != ["O", "O_sham"]:
            raise RuntimeError(f"Unexpected condition family for base {base}: {conditions}")
        paths = {name: ROOT / edit["paths"][name] for name in conditions}
        images = {name: np.asarray(Image.open(path).convert("RGB")) for name, path in paths.items()}
        if len({image.shape for image in images.values()}) != 1:
            raise RuntimeError(f"Image dimensions differ for base {base}")
        mask = changed_mask_from_conditions(images)
        roi = [int(value) for value in edit["target_evidence_roi_xyxy"]]
        x0, y0, x1, y1 = roi
        inside = np.zeros(mask.shape, dtype=bool)
        inside[y0:y1, x0:x1] = True
        if np.any(mask & ~inside):
            raise RuntimeError(f"Edit pixels escaped the declared ROI for base {base}")
        metadata = {}
        for condition in conditions:
            prepared, metadata[condition] = prepare_custom_image(
                processor, data[str(item["example_id"])], paths[condition], device="cpu"
            )
            del prepared
        prompt_ids = [metadata[name]["prompt_token_ids"] for name in conditions]
        visual_positions = [metadata[name]["visual_token_indices"] for name in conditions]
        grids = [metadata[name]["visual_mapping"]["merged_grid_shape"] for name in conditions]
        if not (
            all(value == prompt_ids[0] for value in prompt_ids[1:])
            and all(value == visual_positions[0] for value in visual_positions[1:])
            and all(value == grids[0] for value in grids[1:])
        ):
            raise RuntimeError(f"Condition preprocessing layout differs for base {base}")
        temporal, rows, cols = (int(value) for value in grids[0])
        if temporal != 1:
            raise RuntimeError(f"Expected one image frame for base {base}")
        target = map_changed_pixels_to_tokens(mask, merged_rows=rows, merged_cols=cols)
        ring = fixed_ring(target, merged_rows=rows, merged_cols=cols, radius=1)
        darkness = cell_darkness(images["O"], merged_rows=rows, merged_cols=cols)
        irrelevant, irrelevant_audit = choose_matched_irrelevant(
            target_local=target, excluded_local=ring, darkness_by_cell=darkness
        )
        groups = build_roi_token_groups(
            visual_positions=visual_positions[0], target_local=target, irrelevant_local=irrelevant,
            merged_rows=rows, merged_cols=cols, ring_radius=1,
        )
        overlay_path = OUT / "overlays" / f"{base}.png"
        overlay(
            image_path=paths["O"], base=base, roi=roi, rows=rows, cols=cols,
            target=target, ring=ring, irrelevant=irrelevant, output_path=overlay_path,
        )
        overlays.append(overlay_path)
        mappings.append({
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "phase": item["phase"],
            "edit_version": item["edit_version"],
            "edit_metadata": item["edit_metadata"],
            "conditions": conditions,
            "declared_roi_xyxy": roi,
            "image_size": metadata["O"]["image_size"],
            "image_grid_thw": metadata["O"]["image_grid_thw"],
            "merged_grid_shape": grids[0],
            "visual_token_count": len(visual_positions[0]),
            "visual_absolute_positions": visual_positions[0],
            "changed_pixel_count": int(mask.sum()),
            "target_local_positions": target,
            "target_token_count": len(target),
            "ring_local_positions": ring,
            "ring_token_count": len(ring),
            "irrelevant_local_positions": irrelevant,
            "irrelevant_token_count": len(irrelevant),
            "absolute_source_groups": groups,
            "target_complement_partition_exact": set(groups["V_target"]) | set(groups["V_other"]) == set(groups["V_all"]) and set(groups["V_target"]).isdisjoint(groups["V_other"]),
            "target_ring_irrelevant_disjoint": set(groups["V_target_ring"]).isdisjoint(groups["V_irrelevant"]),
            "all_condition_layout_exact": True,
            "edit_pixels_inside_declared_roi": True,
            "mapping_used_attention": False,
            "generation_outcomes_available": False,
            "stage3b9_value_or_causal_outcomes_available": False,
            "irrelevant_selection": irrelevant_audit,
            "overlay": str(overlay_path.relative_to(ROOT)),
            "manual_overlay_validation": {"status": "pending"},
        })
        print(f"mapped phase={item['phase']} base={base}: target={len(target)} ring={len(ring)}", flush=True)
    ensure_directory(OUT)
    write_jsonl(mapping_path, mappings)
    make_review_sheets(overlays, OUT)
    write_text(
        OUT / "roi_mapping_report.md",
        f"# Stage 3B.9 fresh ROI mapping draft\n\nGenerated {len(mappings)} attention-, outcome-, and score-independent mappings. Manual overlay review is pending.\n",
    )
    print(json.dumps({"mapped": len(mappings), "manual_pending": len(mappings)}, indent=2))


if __name__ == "__main__":
    main()
