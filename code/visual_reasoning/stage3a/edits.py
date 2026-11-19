"""Deterministic local text edits and image-condition validation."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _checked_roi(roi_xyxy: Sequence[int], width: int, height: int) -> tuple[int, int, int, int]:
    if len(roi_xyxy) != 4:
        raise ValueError("ROI must contain x0, y0, x1, y1")
    x0, y0, x1, y1 = (int(value) for value in roi_xyxy)
    if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
        raise ValueError(f"ROI {(x0, y0, x1, y1)} is outside image {(width, height)}")
    return x0, y0, x1, y1


def _font(spec: Mapping[str, Any]) -> ImageFont.ImageFont:
    # The default Pillow font is project-environment local, deterministic, and
    # avoids depending on machine-global font paths.
    size = int(spec.get("font_size", 16))
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _text_background(source: Image.Image, roi: tuple[int, int, int, int], spec: Mapping[str, Any]) -> tuple[int, int, int]:
    if spec.get("background_mode") != "roi_bright_median":
        return tuple(int(value) for value in spec.get("background_color", (255, 255, 255)))
    x0, y0, x1, y1 = roi
    region = np.asarray(source.convert("RGB"))[y0:y1, x0:x1].reshape(-1, 3)
    brightness = region.astype(np.float32).mean(axis=1)
    bright = region[brightness >= np.quantile(brightness, 0.65)]
    if not len(bright):
        raise ValueError("Cannot infer ROI background from an empty pixel selection")
    return tuple(int(round(value)) for value in np.median(bright, axis=0))


def _render(source: Image.Image, text: str, spec: Mapping[str, Any]) -> Image.Image:
    output = source.copy().convert("RGB")
    x0, y0, x1, y1 = _checked_roi(spec["roi_xyxy"], output.width, output.height)
    background = _text_background(source, (x0, y0, x1, y1), spec)
    foreground = tuple(int(value) for value in spec.get("text_color", (0, 0, 0)))
    anchor_x, anchor_y = (int(value) for value in spec.get("text_anchor", (2, 2)))
    draw = ImageDraw.Draw(output)
    draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=background)
    draw.text((x0 + anchor_x, y0 + anchor_y), str(text), fill=foreground, font=_font(spec))
    return output


def build_text_conditions(source_path: Path, output_root: Path, spec: Mapping[str, Any]) -> dict[str, Path]:
    """Create C0/C1/C2 using one declared target ROI and one render path."""

    source_path = Path(source_path)
    output_root = Path(output_root)
    paths = {
        "original": output_root / "original" / "image.png",
        "counterfactual": output_root / "counterfactual" / "image.png",
        "sham": output_root / "sham" / "image.png",
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, paths["original"])
    with Image.open(source_path) as handle:
        source = handle.convert("RGB")
        _render(source, str(spec["counterfactual_text"]), spec).save(paths["counterfactual"])
        _render(source, str(spec["original_text"]), spec).save(paths["sham"])
    return paths


def _render_polyline(source: Image.Image, points: Sequence[Sequence[int]], spec: Mapping[str, Any]) -> Image.Image:
    output = source.copy().convert("RGB")
    x0, y0, x1, y1 = _checked_roi(spec["roi_xyxy"], output.width, output.height)
    background = tuple(int(value) for value in spec.get("background_color", (255, 255, 255)))
    foreground = tuple(int(value) for value in spec.get("line_color", (0, 0, 0)))
    width = int(spec.get("line_width", 2))
    vertices = [(int(point[0]), int(point[1])) for point in points]
    if len(vertices) < 2:
        raise ValueError("Polyline requires at least two vertices")
    margin = max(1, (width + 1) // 2)
    if any(not (x0 + margin <= x < x1 - margin and y0 + margin <= y < y1 - margin) for x, y in vertices):
        raise ValueError("Polyline vertices and stroke must remain inside the declared ROI")
    erase_mode = spec.get("erase_mode", "rectangle")
    if erase_mode in {"color_mask", "cyan_mask", "dark_mask"}:
        array = np.asarray(output).copy()
        region = array[y0:y1, x0:x1]
        if erase_mode == "color_mask":
            target = np.asarray(spec["erase_color"], dtype=np.int32)
            distance = np.sqrt(np.square(region.astype(np.int32) - target).sum(axis=-1))
            mask = distance <= float(spec.get("erase_tolerance", 0.0))
        elif erase_mode == "cyan_mask":
            signed = region.astype(np.int16)
            threshold = int(spec.get("cyan_excess_threshold", 5))
            mask = (signed[..., 1] - signed[..., 0] >= threshold) & (
                signed[..., 2] - signed[..., 0] >= threshold
            )
        else:
            mask = region.max(axis=-1) <= int(spec.get("dark_threshold", 200))
        region[mask] = background
        output = Image.fromarray(array)
    else:
        draw = ImageDraw.Draw(output)
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=background)
    draw = ImageDraw.Draw(output)
    if int(spec.get("erase_stroke_width", 0)) > 0:
        original_vertices = [(int(point[0]), int(point[1])) for point in spec["original_points"]]
        draw.line(original_vertices, fill=background, width=int(spec["erase_stroke_width"]), joint="curve")
        radius = int(spec.get("erase_marker_radius", 0))
        for point in spec.get("erase_marker_points", []):
            px, py = int(point[0]), int(point[1])
            draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill=background)
    grid_color = tuple(int(value) for value in spec.get("grid_color", (225, 225, 225)))
    for grid_x in spec.get("grid_lines_x", []):
        draw.line((int(grid_x), y0, int(grid_x), y1 - 1), fill=grid_color, width=1)
    for grid_y in spec.get("grid_lines_y", []):
        draw.line((x0, int(grid_y), x1 - 1, int(grid_y)), fill=grid_color, width=1)
    draw.line(vertices, fill=foreground, width=width, joint="curve")
    for box in spec.get("preserve_boxes", []):
        px0, py0, px1, py1 = _checked_roi(box, output.width, output.height)
        output.paste(source.crop((px0, py0, px1, py1)), (px0, py0))
    return output


def build_polyline_conditions(source_path: Path, output_root: Path, spec: Mapping[str, Any]) -> dict[str, Path]:
    """Create C0/C1/C2 for one plot trajectory using a shared redraw path."""

    source_path = Path(source_path)
    output_root = Path(output_root)
    paths = {
        "original": output_root / "original" / "image.png",
        "counterfactual": output_root / "counterfactual" / "image.png",
        "sham": output_root / "sham" / "image.png",
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, paths["original"])
    with Image.open(source_path) as handle:
        source = handle.convert("RGB")
        _render_polyline(source, spec["counterfactual_points"], spec).save(paths["counterfactual"])
        _render_polyline(source, spec["original_points"], spec).save(paths["sham"])
    return paths


def validate_edit_conditions(paths: Mapping[str, Path], roi_xyxy: Sequence[int]) -> dict[str, Any]:
    arrays = {name: np.asarray(Image.open(path).convert("RGB")) for name, path in paths.items()}
    shapes = {name: list(value.shape) for name, value in arrays.items()}
    dimensions_match = len({tuple(value.shape) for value in arrays.values()}) == 1
    if not dimensions_match:
        return {"passed": False, "dimensions_match": False, "shapes": shapes}
    height, width = arrays["original"].shape[:2]
    x0, y0, x1, y1 = _checked_roi(roi_xyxy, width, height)
    outside = np.ones((height, width), dtype=bool)
    outside[y0:y1, x0:x1] = False
    original = arrays["original"]
    counterfactual = arrays["counterfactual"]
    sham = arrays["sham"]
    cf_outside = bool(np.array_equal(original[outside], counterfactual[outside]))
    sham_outside = bool(np.array_equal(original[outside], sham[outside]))
    cf_inside = int(np.count_nonzero(np.any(original[y0:y1, x0:x1] != counterfactual[y0:y1, x0:x1], axis=-1)))
    sham_inside = int(np.count_nonzero(np.any(original[y0:y1, x0:x1] != sham[y0:y1, x0:x1], axis=-1)))
    checks = {
        "dimensions_match": dimensions_match,
        "shapes": shapes,
        "counterfactual_outside_roi_exact": cf_outside,
        "sham_outside_roi_exact": sham_outside,
        "counterfactual_diff_pixels_inside_roi": cf_inside,
        "sham_diff_pixels_inside_roi": sham_inside,
        "sha256": {name: _sha256(Path(path)) for name, path in paths.items()},
    }
    checks["passed"] = bool(dimensions_match and cf_outside and sham_outside and cf_inside > 0 and sham_inside > 0)
    return checks
