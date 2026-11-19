#!/usr/bin/env python3
"""Map validated Stage 3C.9 edit pixels to visual tokens without attention."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from transformers import AutoProcessor

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import write_jsonl
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3b7.roi import build_roi_token_groups, cell_darkness, choose_matched_irrelevant, fixed_ring, map_changed_pixels_to_tokens
from visual_reasoning.stage3c9.edits import CONDITIONS


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=OUT / "cohort/edit_manifest_reviewed.jsonl")
    return parser.parse_args()


def cell_box(index: int, *, width: int, height: int, rows: int, cols: int) -> tuple[int, int, int, int]:
    row, col = divmod(int(index), int(cols))
    return col * width // cols, row * height // rows, (col + 1) * width // cols, (row + 1) * height // rows


def main() -> None:
    args = parse_args()
    output = OUT / "cohort/roi_mapping_pending.jsonl"
    if output.exists():
        raise FileExistsError(output)
    config = read_json(OUT / "config/stage3c9_config.json")
    dataset = {str(row["sample_index"]): row for row in load_mathverse_rows(Path(config["dataset_root"]))}
    processor = AutoProcessor.from_pretrained(config["model_checkpoint"], local_files_only=True)
    mappings = []
    for item in read_jsonl(args.manifest):
        base = str(item["base_problem_id"])
        edit = read_json(ROOT / item["edit_metadata"])
        if edit["manual_validation"]["status"] != "pass":
            raise RuntimeError(f"Edit manual validation has not passed for base {base}")
        paths = {name: ROOT / edit["paths"][name] for name in CONDITIONS}
        images = {name: np.asarray(Image.open(path).convert("RGB")) for name, path in paths.items()}
        original = images["O"]
        changed = np.logical_or.reduce([np.any(original != images[name], axis=2) for name in CONDITIONS[1:]])
        roi = [int(value) for value in edit["target_evidence_roi_xyxy"]]
        x0, y0, x1, y1 = roi
        inside = np.zeros(changed.shape, dtype=bool)
        inside[y0:y1, x0:x1] = True
        if np.any(changed & ~inside):
            raise RuntimeError(f"Edit pixels escaped declared ROI for base {base}")
        metadata = {}
        for condition in CONDITIONS:
            prepared, metadata[condition] = prepare_custom_image(
                processor, dataset[str(item["example_id"])], paths[condition], device="cpu"
            )
            del prepared
        prompt_ids = [metadata[name]["prompt_token_ids"] for name in CONDITIONS]
        visual_positions = [metadata[name]["visual_token_indices"] for name in CONDITIONS]
        grids = [metadata[name]["visual_mapping"]["merged_grid_shape"] for name in CONDITIONS]
        if not (all(value == prompt_ids[0] for value in prompt_ids[1:]) and all(value == visual_positions[0] for value in visual_positions[1:]) and all(value == grids[0] for value in grids[1:])):
            raise RuntimeError(f"Four-condition preprocessing mismatch for base {base}")
        temporal, rows, cols = (int(value) for value in grids[0])
        if temporal != 1:
            raise RuntimeError(f"Expected a still-image layout for base {base}")
        target_local = map_changed_pixels_to_tokens(changed, merged_rows=rows, merged_cols=cols)
        ring_local = fixed_ring(target_local, merged_rows=rows, merged_cols=cols, radius=1)
        irrelevant_local, irrelevant_audit = choose_matched_irrelevant(
            target_local=target_local,
            excluded_local=ring_local,
            darkness_by_cell=cell_darkness(original, merged_rows=rows, merged_cols=cols),
        )
        groups = build_roi_token_groups(
            visual_positions=visual_positions[0], target_local=target_local,
            irrelevant_local=irrelevant_local, merged_rows=rows, merged_cols=cols, ring_radius=1,
        )
        with Image.open(paths["O"]) as opened:
            image = opened.convert("RGBA")
        layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        for position in target_local:
            draw.rectangle(cell_box(position, width=image.width, height=image.height, rows=rows, cols=cols), fill=(220, 30, 30, 105), outline=(220, 30, 30, 255), width=2)
        composed = Image.alpha_composite(image, layer).convert("RGB")
        ImageDraw.Draw(composed).rectangle(tuple(roi), outline=(20, 180, 50), width=3)
        panel = Image.new("RGB", (composed.width, composed.height + 35), "white")
        panel.paste(composed, (0, 35))
        ImageDraw.Draw(panel).text((5, 5), f"base {base} | grid {rows}x{cols} | target {len(target_local)}", fill="black", font=ImageFont.load_default(size=14))
        overlay = OUT / "cohort/roi_overlays" / f"{base}.png"
        overlay.parent.mkdir(parents=True, exist_ok=True)
        panel.save(overlay)
        mappings.append({
            "base_problem_id": base,
            "example_id": str(item["example_id"]),
            "roi_xyxy": roi,
            "merged_grid_shape": grids[0],
            "visual_token_count": len(visual_positions[0]),
            "changed_pixel_count": int(changed.sum()),
            "target_local_positions": target_local,
            "target_token_count": len(target_local),
            "irrelevant_local_positions": irrelevant_local,
            "irrelevant_selection": irrelevant_audit,
            "absolute_source_groups": groups,
            "four_condition_layout_exact": True,
            "edit_pixels_inside_declared_roi": True,
            "mapping_used_attention": False,
            "overlay": str(overlay.relative_to(ROOT)),
            "manual_overlay_validation": {"status": "pending", "causal_scores_available": False},
        })
        print(f"mapped base {base}: {len(target_local)} visual tokens", flush=True)
    write_jsonl(output, mappings)
    print(json.dumps({"mapped": len(mappings)}, indent=2))


if __name__ == "__main__":
    main()
