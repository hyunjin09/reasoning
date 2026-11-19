"""Deterministic text edits that preserve diagram strokes crossing an edit ROI."""

from __future__ import annotations

from collections import deque
from collections.abc import Sequence

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def changed_mask_from_conditions(
    images: dict[str, np.ndarray], *, original_condition: str = "O"
) -> np.ndarray:
    """Return pixels changed by any condition relative to the original image."""
    if original_condition not in images:
        raise KeyError(f"Missing original condition: {original_condition}")
    original = images[original_condition]
    comparisons = [
        np.any(original != image, axis=2)
        for name, image in images.items()
        if name != original_condition
    ]
    if not comparisons:
        return np.zeros(original.shape[:2], dtype=bool)
    return np.logical_or.reduce(comparisons)


def edge_connected_foreground_mask(
    region: np.ndarray,
    background: Sequence[int],
    *,
    color_distance_threshold: float = 24.0,
) -> np.ndarray:
    """Return foreground pixels connected to an ROI edge.

    Text labels are enclosed by a generously padded ROI, while diagram strokes
    enter or leave it.  Retaining only edge-connected foreground therefore
    removes the old label without deleting crossing geometry.
    """

    pixels = np.asarray(region, dtype=np.float32)
    if pixels.ndim != 3 or pixels.shape[2] != 3:
        raise ValueError("region must have shape [height, width, 3]")
    background_array = np.asarray(background, dtype=np.float32)
    distance = np.sqrt(np.square(pixels - background_array).sum(axis=-1))
    foreground = distance >= float(color_distance_threshold)
    height, width = foreground.shape
    keep = np.zeros_like(foreground)
    queue: deque[tuple[int, int]] = deque()
    for x in range(width):
        if foreground[0, x]:
            queue.append((0, x))
        if height > 1 and foreground[height - 1, x]:
            queue.append((height - 1, x))
    for y in range(1, max(1, height - 1)):
        if foreground[y, 0]:
            queue.append((y, 0))
        if width > 1 and foreground[y, width - 1]:
            queue.append((y, width - 1))
    while queue:
        y, x = queue.popleft()
        if keep[y, x] or not foreground[y, x]:
            continue
        keep[y, x] = True
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                ny, nx = y + dy, x + dx
                if 0 <= ny < height and 0 <= nx < width and not keep[ny, nx] and foreground[ny, nx]:
                    queue.append((ny, nx))
    return keep


def render_preserving_crossing_strokes(
    source: Image.Image,
    text: str,
    *,
    roi_xyxy: Sequence[int],
    text_anchor: Sequence[int],
    font_size: int,
    background: Sequence[int] | None = None,
    text_color: Sequence[int] = (0, 0, 0),
) -> Image.Image:
    """Replace an enclosed label and restore diagram strokes crossing the ROI."""

    output = source.convert("RGB").copy()
    x0, y0, x1, y1 = (int(value) for value in roi_xyxy)
    if not (0 <= x0 < x1 <= output.width and 0 <= y0 < y1 <= output.height):
        raise ValueError("ROI is outside the source image")
    original = np.asarray(output)
    region = original[y0:y1, x0:x1]
    if background is None:
        brightness = region.astype(np.float32).mean(axis=-1)
        bright = region[brightness >= np.quantile(brightness, 0.65)]
        if not len(bright):
            raise ValueError("Cannot infer edit background")
        inferred = np.median(bright, axis=0).round().astype(np.uint8)
    else:
        inferred = np.asarray(background, dtype=np.uint8)
    keep = edge_connected_foreground_mask(region, inferred)
    replacement = np.broadcast_to(inferred, region.shape).copy()
    replacement[keep] = region[keep]
    edited = original.copy()
    edited[y0:y1, x0:x1] = replacement
    output = Image.fromarray(edited)
    try:
        font = ImageFont.load_default(size=int(font_size))
    except TypeError:
        font = ImageFont.load_default()
    draw = ImageDraw.Draw(output)
    draw.text(
        (x0 + int(text_anchor[0]), y0 + int(text_anchor[1])),
        str(text),
        fill=tuple(int(value) for value in text_color),
        font=font,
    )
    return output
