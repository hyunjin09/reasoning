#!/usr/bin/env python3
"""Reproduce preprocessing and freeze edit-derived Stage 3B.7 ROI token groups."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from transformers import AutoProcessor

from visual_reasoning.stage0.data import load_mathverse_rows
from visual_reasoning.stage0.io import ensure_directory, write_jsonl
from visual_reasoning.stage3a.runtime import prepare_custom_image
from visual_reasoning.stage3b7.roi import (
    build_roi_token_groups,
    cell_darkness,
    choose_matched_irrelevant,
    fixed_ring,
    map_changed_pixels_to_tokens,
)


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b7"
CONDITIONS = ("O", "O_sham", "C", "C_sham")
COLORS = {
    "target": (220, 30, 30, 105),
    "ring": (245, 145, 30, 75),
    "irrelevant": (35, 85, 225, 105),
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def changed_mask(images: dict[str, np.ndarray]) -> np.ndarray:
    original = images["O"]
    return np.logical_or.reduce(
        [np.any(original != images[condition], axis=2) for condition in CONDITIONS[1:]]
    )


def cell_box(index: int, *, width: int, height: int, rows: int, cols: int) -> tuple[int, int, int, int]:
    row, col = divmod(int(index), int(cols))
    return (
        col * width // cols,
        row * height // rows,
        (col + 1) * width // cols,
        (row + 1) * height // rows,
    )


def overlay(
    *,
    image_path: Path,
    base: str,
    roi: list[int],
    rows: int,
    cols: int,
    target: list[int],
    ring: list[int],
    irrelevant: list[int],
    output_path: Path,
) -> None:
    image = Image.open(image_path).convert("RGBA")
    width, height = image.size
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    for name, indices in (
        ("ring", sorted(set(ring) - set(target))),
        ("target", target),
        ("irrelevant", irrelevant),
    ):
        for index in indices:
            box = cell_box(index, width=width, height=height, rows=rows, cols=cols)
            draw.rectangle(box, fill=COLORS[name], outline=COLORS[name][:3] + (255,), width=2)
    composed = Image.alpha_composite(image, layer).convert("RGB")
    draw = ImageDraw.Draw(composed)
    draw.rectangle(tuple(roi), outline=(20, 180, 50), width=3)
    panel_height = 38
    canvas = Image.new("RGB", (width, height + panel_height), "white")
    canvas.paste(composed, (0, panel_height))
    text = (
        f"base {base} | grid {rows}x{cols} | target {len(target)} | "
        f"ring {len(ring)} | irrelevant {len(irrelevant)}"
    )
    ImageDraw.Draw(canvas).text((5, 5), text, fill=(0, 0, 0), font=ImageFont.load_default())
    canvas.save(output_path)


def review_sheets(paths: list[Path]) -> None:
    for page, start in enumerate(range(0, len(paths), 9)):
        selected = paths[start : start + 9]
        sheet = Image.new("RGB", (1500, 1200), "white")
        for offset, path in enumerate(selected):
            image = Image.open(path).convert("RGB")
            image.thumbnail((480, 370), Image.Resampling.LANCZOS)
            x = (offset % 3) * 500 + (500 - image.width) // 2
            y = (offset // 3) * 400 + (390 - image.height) // 2
            sheet.paste(image, (x, y))
        sheet.save(OUT / f"roi_audit/review_sheet_{page:02d}.png")


def main() -> None:
    config = read_json(OUT / "config/stage3b7_config.json")
    output = OUT / "roi_audit/roi_token_mapping.jsonl"
    if output.exists():
        raise FileExistsError("ROI mappings are already frozen")
    manifests = [
        ("validation", read_jsonl(OUT / "config/validation_manifest.jsonl")),
        ("primary", read_jsonl(OUT / "config/cohort_manifest.jsonl")),
    ]
    dataset_root = ROOT / "datasets"
    if not dataset_root.exists():
        dataset_root = Path("/data/dataset/MathVerse")
    data = {str(row["sample_index"]): row for row in load_mathverse_rows(dataset_root)}
    processor = AutoProcessor.from_pretrained(
        Path(config["model_checkpoint"]), local_files_only=True
    )
    mappings: list[dict[str, Any]] = []
    irrelevant_rows: list[dict[str, Any]] = []
    overlay_paths: list[Path] = []
    for role, items in manifests:
        for item in items:
            base = str(item["base_problem_id"])
            paired = read_json(
                ROOT
                / "outputs/stage3b3_redesign/counterfactual_shams"
                / base
                / "edit_metadata.json"
            )
            stage3a = read_json(
                ROOT / "outputs/stage3a/counterfactuals" / base / "edit_metadata.json"
            )
            condition_paths = {
                condition: ROOT / paired["paths"][condition] for condition in CONDITIONS
            }
            images = {
                condition: np.asarray(Image.open(path).convert("RGB"))
                for condition, path in condition_paths.items()
            }
            if len({image.shape for image in images.values()}) != 1:
                raise RuntimeError(f"Image dimensions differ for base {base}")
            mask = changed_mask(images)
            roi = [int(value) for value in stage3a["target_evidence_roi_xyxy"]]
            x0, y0, x1, y1 = roi
            inside = np.zeros(mask.shape, dtype=bool)
            inside[y0:y1, x0:x1] = True
            if np.any(mask & ~inside):
                raise RuntimeError(f"Edit pixels escaped the Stage 3A ROI for base {base}")
            metadata = {}
            for condition in CONDITIONS:
                prepared, metadata[condition] = prepare_custom_image(
                    processor,
                    data[str(item["example_id"])],
                    condition_paths[condition],
                    device="cpu",
                )
                del prepared
            prompt_ids = [metadata[name]["prompt_token_ids"] for name in CONDITIONS]
            visual_positions = [metadata[name]["visual_token_indices"] for name in CONDITIONS]
            grids = [metadata[name]["visual_mapping"]["merged_grid_shape"] for name in CONDITIONS]
            if not (
                all(value == prompt_ids[0] for value in prompt_ids[1:])
                and all(value == visual_positions[0] for value in visual_positions[1:])
                and all(value == grids[0] for value in grids[1:])
            ):
                raise RuntimeError(f"Four-condition preprocessing layout differs for base {base}")
            temporal, rows, cols = (int(value) for value in grids[0])
            if temporal != 1:
                raise RuntimeError(f"Expected a still-image grid for base {base}")
            target = map_changed_pixels_to_tokens(
                mask, merged_rows=rows, merged_cols=cols
            )
            ring = fixed_ring(
                target, merged_rows=rows, merged_cols=cols, radius=1
            )
            darkness = cell_darkness(images["O"], merged_rows=rows, merged_cols=cols)
            irrelevant, irrelevant_audit = choose_matched_irrelevant(
                target_local=target,
                excluded_local=ring,
                darkness_by_cell=darkness,
            )
            groups = build_roi_token_groups(
                visual_positions=visual_positions[0],
                target_local=target,
                irrelevant_local=irrelevant,
                merged_rows=rows,
                merged_cols=cols,
                ring_radius=1,
            )
            overlay_path = OUT / f"roi_audit/overlays/{base}.png"
            overlay(
                image_path=condition_paths["O"],
                base=base,
                roi=roi,
                rows=rows,
                cols=cols,
                target=target,
                ring=ring,
                irrelevant=irrelevant,
                output_path=overlay_path,
            )
            overlay_paths.append(overlay_path)
            mapping = {
                "base_problem_id": base,
                "example_id": str(item["example_id"]),
                "cohort_role": role,
                "stage3a_roi_xyxy": roi,
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
                "target_complement_partition_exact": bool(
                    set(groups["V_target"]) | set(groups["V_other"])
                    == set(groups["V_all"])
                    and set(groups["V_target"]).isdisjoint(groups["V_other"])
                ),
                "target_ring_irrelevant_disjoint": set(groups["V_target_ring"]).isdisjoint(
                    groups["V_irrelevant"]
                ),
                "four_condition_layout_exact": True,
                "edit_pixels_inside_declared_roi": True,
                "mapping_used_attention": False,
                "irrelevant_selection": irrelevant_audit,
                "overlay": str(overlay_path.relative_to(ROOT)),
                "manual_overlay_validation": {
                    "status": "pending",
                    "causal_scores_available": False,
                },
            }
            mappings.append(mapping)
            irrelevant_rows.append({
                "base_problem_id": base,
                "cohort_role": role,
                "target_local_positions": target,
                "irrelevant_local_positions": irrelevant,
                **irrelevant_audit,
                "manual_status": "pending",
            })
            print(f"mapped {role} base {base}: target={len(target)} ring={len(ring)}", flush=True)
    write_jsonl(output, mappings)
    write_jsonl(OUT / "roi_audit/irrelevant_roi_manifest.jsonl", irrelevant_rows)
    review_sheets(overlay_paths)
    (OUT / "roi_audit/roi_mapping_report.md").write_text(
        "# Stage 3B.7 ROI mapping audit\n\n"
        f"Generated {len(mappings)} attention-independent edit-pixel-to-token mappings "
        f"({sum(row['cohort_role']=='validation' for row in mappings)} validation, "
        f"{sum(row['cohort_role']=='primary' for row in mappings)} primary).\n\n"
        "The mappings and matched irrelevant regions are frozen, but manual overlay review is "
        "pending. No Stage 3B.7 causal score existed during construction.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
