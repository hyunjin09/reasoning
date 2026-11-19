#!/usr/bin/env python3
"""Build frozen four-condition local numeric edits from manually reviewed specs."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage0.data import load_mathverse_rows, resolve_image_path
from visual_reasoning.stage0.io import write_json, write_jsonl
from visual_reasoning.stage3a.edits import _render
from visual_reasoning.stage3b9.edits import render_preserving_crossing_strokes


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c8"
CONDITIONS = ("O", "O_sham", "C", "C_sham")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--specs", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--append", action="store_true", help="Keep exact previously built rows and add new bases")
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(paths: dict[str, Path], roi: list[int]) -> dict[str, Any]:
    arrays = {name: np.asarray(Image.open(path).convert("RGB")) for name, path in paths.items()}
    dimensions = len({array.shape for array in arrays.values()}) == 1
    if not dimensions:
        return {"passed": False, "reason": "dimension mismatch"}
    height, width = arrays["O"].shape[:2]
    x0, y0, x1, y1 = (int(value) for value in roi)
    if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
        return {"passed": False, "reason": "ROI outside image"}
    outside = np.ones((height, width), dtype=bool)
    outside[y0:y1, x0:x1] = False
    exact_outside = {
        name: bool(np.array_equal(arrays["O"][outside], arrays[name][outside]))
        for name in CONDITIONS[1:]
    }
    inside_diffs = {
        name: int(np.count_nonzero(np.any(arrays["O"][y0:y1, x0:x1] != arrays[name][y0:y1, x0:x1], axis=-1)))
        for name in CONDITIONS[1:]
    }
    return {
        "passed": bool(all(exact_outside.values()) and all(value > 0 for value in inside_diffs.values())),
        "image_shape": [height, width, 3],
        "outside_roi_exact": exact_outside,
        "inside_roi_diff_pixels": inside_diffs,
        "sha256": {name: sha(path) for name, path in paths.items()},
    }


def make_review_sheet(base_dir: Path, paths: dict[str, Path], roi: list[int]) -> Path:
    images = [Image.open(paths[name]).convert("RGB") for name in CONDITIONS]
    scale = min(1.0, 420 / max(image.width for image in images), 320 / max(image.height for image in images))
    full = [image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))), Image.Resampling.LANCZOS) for image in images]
    x0, y0, x1, y1 = roi
    crop_scale = min(10, max(2, 380 // max(x1 - x0, y1 - y0)))
    crops = [image.crop((x0, y0, x1, y1)).resize(((x1 - x0) * crop_scale, (y1 - y0) * crop_scale), Image.Resampling.NEAREST) for image in images]
    cell_w = max(max(image.width for image in full), max(image.width for image in crops)) + 12
    cell_h = 30 + max(image.height for image in full) + 30 + max(image.height for image in crops)
    sheet = Image.new("RGB", (4 * cell_w, cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=15)
    for index, (name, image, crop) in enumerate(zip(CONDITIONS, full, crops)):
        x = index * cell_w
        draw.text((x + 3, 5), name, fill="black", font=font)
        sheet.paste(image, (x, 30))
        cy = 30 + max(value.height for value in full)
        draw.text((x + 3, cy + 4), f"ROI x{crop_scale}", fill="black", font=font)
        sheet.paste(crop, (x, cy + 30))
    path = base_dir / "review_sheet.png"
    sheet.save(path)
    for image in images + full + crops:
        image.close()
    return path


def main() -> None:
    args = parse_args()
    specs = read_jsonl(args.specs)
    if not specs:
        raise ValueError("No manually reviewed edit specs")
    pool = {str(row["base_problem_id"]): row for row in read_jsonl(OUT / "prospective_generation/completed_correct_pool.jsonl")}
    dataset = {str(row["sample_index"]): row for row in load_mathverse_rows(args.dataset_root)}
    built_at = datetime.now(timezone.utc).isoformat()
    manifest_path = OUT / "cohort/fresh_edit_manifest_pending.jsonl"
    manifest = read_jsonl(manifest_path) if args.append and manifest_path.is_file() else []
    existing = {str(row["base_problem_id"]): row for row in manifest}
    if len(existing) != len(manifest):
        raise RuntimeError("Existing pending edit manifest contains duplicate bases")
    for spec in specs:
        base = str(spec["base_problem_id"])
        if base not in pool:
            raise RuntimeError(f"Edit spec base {base} is not in the completed-correct pool")
        item = pool[base]
        example = str(item["example_id"])
        if str(spec["example_id"]) != example:
            raise RuntimeError(f"Example identity mismatch for base {base}")
        if base in existing:
            metadata = read_json(ROOT / existing[base]["edit_metadata"])
            exact_keys = (
                "example_id", "original_value", "counterfactual_value", "roi_xyxy",
                "font_size", "text_anchor", "render_suffix", "target_evidence", "evidence_type",
                "renderer", "counterfactual_sham_anchor_delta",
            )
            if any(metadata.get(key) != spec.get(key) for key in exact_keys):
                raise RuntimeError(f"Existing edit specification changed for base {base}")
            continue
        source = resolve_image_path(args.dataset_root, str(dataset[example]["image"]))
        base_dir = OUT / "counterfactuals" / base
        if base_dir.exists() and any(base_dir.iterdir()):
            raise FileExistsError(base_dir)
        paths = {name: base_dir / name / "image.png" for name in CONDITIONS}
        for path in paths.values():
            path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, paths["O"])
        roi = [int(value) for value in spec["roi_xyxy"]]
        anchor = [int(value) for value in spec.get("text_anchor", [3, 2])]
        sham_delta = [int(value) for value in spec.get("counterfactual_sham_anchor_delta", [1, 0])]
        if len(sham_delta) != 2 or sham_delta == [0, 0]:
            raise ValueError(f"Counterfactual sham anchor delta must be a nonzero x/y pair for base {base}")
        counterfactual_sham_anchor = [anchor[0] + sham_delta[0], anchor[1] + sham_delta[1]]
        original_text = f"{spec['original_value']}{spec.get('render_suffix', '')}"
        counterfactual_text = f"{spec['counterfactual_value']}{spec.get('render_suffix', '')}"
        with Image.open(source) as opened:
            original = opened.convert("RGB")
            if spec.get("renderer") == "preserve_crossing_strokes":
                render_common = {
                    "roi_xyxy": roi,
                    "font_size": int(spec["font_size"]),
                    "text_color": [0, 0, 0],
                }
                render = lambda text, selected_anchor: render_preserving_crossing_strokes(
                    original, text, **render_common, text_anchor=selected_anchor
                )
                renderer_name = "visual_reasoning.stage3b9.edits.render_preserving_crossing_strokes"
            else:
                render_spec = {
                    "roi_xyxy": roi,
                    "background_mode": "roi_bright_median",
                    "text_color": [0, 0, 0],
                    "font_size": int(spec["font_size"]),
                }
                render = lambda text, selected_anchor: _render(
                    original, text, {**render_spec, "text_anchor": selected_anchor}
                )
                renderer_name = "visual_reasoning.stage3a.edits._render"
            render(original_text, anchor).save(paths["O_sham"])
            render(counterfactual_text, anchor).save(paths["C"])
            render(counterfactual_text, counterfactual_sham_anchor).save(paths["C_sham"])
        automatic = validate(paths, roi)
        if not automatic["passed"]:
            raise RuntimeError(f"Automatic edit validation failed for base {base}: {automatic}")
        sheet = make_review_sheet(base_dir, paths, roi)
        metadata = {
            **spec,
            "base_problem_id": base,
            "example_id": example,
            "edit_version": "stage3c8_v1",
            "built_at": built_at,
            "source_image": str(source),
            "source_image_sha256": sha(source),
            "paths": {name: str(path.relative_to(ROOT)) for name, path in paths.items()},
            "target_evidence_roi_xyxy": roi,
            "construction": {
                "renderer": renderer_name,
                "edge_connected_diagram_strokes_preserved": spec.get("renderer") == "preserve_crossing_strokes",
                "same_original_source_for_every_condition": True,
                "semantic_anchor": anchor,
                "counterfactual_sham_anchor_delta": sham_delta,
                "counterfactual_sham_anchor": counterfactual_sham_anchor,
                "selection_used_attention": False,
                "carrier_scores_available": False,
            },
            "automatic_validation": automatic,
            "manual_validation": {"status": "pending", "reviewer": None},
            "review_sheet": str(sheet.relative_to(ROOT)),
        }
        write_json(base_dir / "edit_metadata.json", metadata)
        (base_dir / "validation.md").write_text(
            f"# Stage 3C8 edit validation — base {base}\n\nAutomatic containment/dimension validation: **PASS**\n\nManual review: **PENDING**\n",
            encoding="utf-8",
        )
        manifest.append({
            "base_problem_id": base,
            "example_id": example,
            "screen_order": int(item["screen_order"]),
            "edit_metadata": str((base_dir / "edit_metadata.json").relative_to(ROOT)),
            "automatic_edit_status": "pass",
            "manual_edit_status": "pending",
            "selection_used_attention": False,
            "carrier_scores_available": False,
        })
    manifest.sort(key=lambda row: int(row["screen_order"]))
    write_jsonl(manifest_path, manifest)
    print(json.dumps({"pending_total": len(manifest), "automatic_pass": len(manifest)}, indent=2))


if __name__ == "__main__":
    main()
