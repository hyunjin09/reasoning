"""Validated semantic edit-quartet helpers for Stage 3C.9."""

from __future__ import annotations

import hashlib
import shutil
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from visual_reasoning.stage3a.edits import _render
from visual_reasoning.stage3b9.edits import render_preserving_crossing_strokes


CONDITIONS = ("O", "O_sham", "C", "C_sham")


def normalize_numeric_surface(value: str) -> str:
    raw = str(value).strip().rstrip("°%").strip()
    try:
        number = Decimal(raw)
    except InvalidOperation:
        return raw
    normalized = format(number.normalize(), "f")
    return "0" if normalized in {"-0", "-0.0"} else normalized


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_quartet_arrays(
    arrays: Mapping[str, np.ndarray], roi_xyxy: list[int],
) -> dict[str, Any]:
    if set(arrays) != set(CONDITIONS):
        raise ValueError(f"Edit arrays must contain exactly {CONDITIONS}")
    shapes = {tuple(array.shape) for array in arrays.values()}
    if len(shapes) != 1:
        return {"passed": False, "reason": "dimension mismatch"}
    shape = next(iter(shapes))
    if len(shape) != 3 or shape[2] != 3:
        return {"passed": False, "reason": "expected RGB arrays"}
    height, width, _ = shape
    x0, y0, x1, y1 = (int(value) for value in roi_xyxy)
    if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
        return {"passed": False, "reason": "ROI outside image"}
    outside = np.ones((height, width), dtype=bool)
    outside[y0:y1, x0:x1] = False
    original = arrays["O"]
    exact_outside = {
        name: bool(np.array_equal(original[outside], arrays[name][outside]))
        for name in CONDITIONS[1:]
    }
    inside_diffs = {
        name: int(np.count_nonzero(np.any(original[y0:y1, x0:x1] != arrays[name][y0:y1, x0:x1], axis=-1)))
        for name in CONDITIONS[1:]
    }
    return {
        "passed": bool(all(exact_outside.values()) and all(value > 0 for value in inside_diffs.values())),
        "image_shape": [height, width, 3],
        "outside_roi_exact": exact_outside,
        "inside_roi_diff_pixels": inside_diffs,
    }


def make_review_sheet(paths: Mapping[str, Path], roi_xyxy: list[int], target: Path) -> None:
    images = [Image.open(paths[name]).convert("RGB") for name in CONDITIONS]
    scale = min(1.0, 420 / max(image.width for image in images), 320 / max(image.height for image in images))
    full = [image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))), Image.Resampling.LANCZOS) for image in images]
    x0, y0, x1, y1 = (int(value) for value in roi_xyxy)
    crop_scale = min(10, max(2, 380 // max(x1 - x0, y1 - y0)))
    crops = [image.crop((x0, y0, x1, y1)).resize(((x1 - x0) * crop_scale, (y1 - y0) * crop_scale), Image.Resampling.NEAREST) for image in images]
    cell_w = max(max(image.width for image in full), max(image.width for image in crops)) + 12
    cell_h = 30 + max(image.height for image in full) + 30 + max(image.height for image in crops)
    sheet = Image.new("RGB", (len(CONDITIONS) * cell_w, cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=15)
    for index, (name, image, crop) in enumerate(zip(CONDITIONS, full, crops)):
        x = index * cell_w
        draw.text((x + 3, 5), name, fill="black", font=font)
        sheet.paste(image, (x, 30))
        crop_y = 30 + max(value.height for value in full)
        draw.text((x + 3, crop_y + 4), f"ROI x{crop_scale}", fill="black", font=font)
        sheet.paste(crop, (x, crop_y + 30))
    sheet.save(target)
    for image in images + full + crops:
        image.close()


def construct_quartet(
    *, source_image: Path, target_dir: Path, spec: Mapping[str, Any],
) -> dict[str, Any]:
    if target_dir.exists() and any(target_dir.iterdir()):
        raise FileExistsError(target_dir)
    paths = {name: target_dir / name / "image.png" for name in CONDITIONS}
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_image, paths["O"])
    roi = [int(value) for value in spec["roi_xyxy"]]
    anchor = [int(value) for value in spec.get("text_anchor", [2, 1])]
    sham_delta = [int(value) for value in spec.get("counterfactual_sham_anchor_delta", [1, 0])]
    if len(sham_delta) != 2 or sham_delta == [0, 0]:
        raise ValueError("Counterfactual sham anchor delta must be a nonzero x/y pair")
    counterfactual_sham_anchor = [anchor[0] + sham_delta[0], anchor[1] + sham_delta[1]]
    suffix = str(spec.get("render_suffix", ""))
    original_text = f"{normalize_numeric_surface(str(spec['original_value']))}{suffix}"
    counterfactual_text = f"{normalize_numeric_surface(str(spec['counterfactual_value']))}{suffix}"
    with Image.open(source_image) as opened:
        original = opened.convert("RGB")
        if spec.get("renderer") == "preserve_crossing_strokes":
            common = {"roi_xyxy": roi, "font_size": int(spec["font_size"]), "text_color": [0, 0, 0]}
            render = lambda text, selected_anchor: render_preserving_crossing_strokes(
                original, text, **common, text_anchor=selected_anchor
            )
            renderer = "visual_reasoning.stage3b9.edits.render_preserving_crossing_strokes"
        else:
            render_spec = {
                "roi_xyxy": roi,
                "background_mode": "roi_bright_median",
                "text_color": [0, 0, 0],
                "font_size": int(spec["font_size"]),
            }
            render = lambda text, selected_anchor: _render(original, text, {**render_spec, "text_anchor": selected_anchor})
            renderer = "visual_reasoning.stage3a.edits._render"
        render(original_text, anchor).save(paths["O_sham"])
        render(counterfactual_text, anchor).save(paths["C"])
        render(counterfactual_text, counterfactual_sham_anchor).save(paths["C_sham"])
    arrays = {name: np.asarray(Image.open(path).convert("RGB")) for name, path in paths.items()}
    validation = validate_quartet_arrays(arrays, roi)
    validation["sha256"] = {name: sha256(path) for name, path in paths.items()}
    if not validation["passed"]:
        raise RuntimeError(f"Automatic edit validation failed: {validation}")
    review_sheet = target_dir / "review_sheet.png"
    make_review_sheet(paths, roi, review_sheet)
    return {
        "paths": paths,
        "review_sheet": review_sheet,
        "automatic_validation": validation,
        "construction": {
            "renderer": renderer,
            "semantic_anchor": anchor,
            "counterfactual_sham_anchor_delta": sham_delta,
            "counterfactual_sham_anchor": counterfactual_sham_anchor,
            "same_original_source_for_every_condition": True,
            "selection_used_attention": False,
            "causal_scores_available": False,
        },
    }
