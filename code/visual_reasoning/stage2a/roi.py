"""Offline evidence-ROI mapping and descriptive curve helpers for Stage 2A."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import numpy as np


Box = tuple[float, float, float, float]


def map_boxes_to_visual_tokens(
    boxes: Sequence[Sequence[float]],
    image_size: Sequence[int],
    merged_grid_shape: Sequence[int],
) -> list[int]:
    """Map original-image boxes to row-major merged visual-token positions.

    A token is included when its cell center falls inside any box. If a very
    small box contains no cell center, the nearest cell center is retained.
    Temporal grids other than one are deliberately rejected: Stage 2A uses
    still images only.
    """
    width, height = map(float, image_size)
    temporal, rows, cols = map(int, merged_grid_shape)
    if temporal != 1:
        raise ValueError(f"expected a still-image grid, got temporal={temporal}")
    clean_boxes: list[Box] = []
    for raw in boxes:
        x0, y0, x1, y1 = map(float, raw)
        if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
            raise ValueError(f"invalid ROI box {raw} for image {image_size}")
        clean_boxes.append((x0, y0, x1, y1))
    if not clean_boxes:
        raise ValueError("at least one ROI box is required")

    centers = [
        ((col + 0.5) * width / cols, (row + 0.5) * height / rows)
        for row in range(rows)
        for col in range(cols)
    ]
    selected = {
        idx
        for idx, (x, y) in enumerate(centers)
        if any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in clean_boxes)
    }
    for box in clean_boxes:
        x0, y0, x1, y1 = box
        if any(x0 <= centers[i][0] <= x1 and y0 <= centers[i][1] <= y1 for i in selected):
            continue
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        selected.add(min(range(len(centers)), key=lambda i: (centers[i][0] - cx) ** 2 + (centers[i][1] - cy) ** 2))
    return sorted(selected)


def token_cell_box(index: int, image_size: Sequence[int], merged_grid_shape: Sequence[int]) -> Box:
    width, height = map(float, image_size)
    temporal, rows, cols = map(int, merged_grid_shape)
    if temporal != 1 or not 0 <= index < rows * cols:
        raise ValueError(f"invalid still-image visual-token index {index}")
    row, col = divmod(index, cols)
    return (
        col * width / cols,
        row * height / rows,
        (col + 1) * width / cols,
        (row + 1) * height / rows,
    )


def span_means(token_values: np.ndarray, span_ranges: np.ndarray) -> np.ndarray:
    values = np.asarray(token_values, dtype=np.float64)
    ranges = np.asarray(span_ranges, dtype=np.int64)
    return np.asarray([values[start:end].mean() if end > start else np.nan for start, end in ranges])


def roi_curves(visual_focus: np.ndarray, roi_indices: Iterable[int]) -> dict[str, np.ndarray]:
    focus = np.asarray(visual_focus, dtype=np.float64)
    indices = np.asarray(sorted(set(roi_indices)), dtype=np.int64)
    if focus.ndim != 2 or indices.size == 0:
        raise ValueError("visual_focus must be [T,V] and ROI must be nonempty")
    raw = focus[:, indices].sum(axis=1)
    visual_total = focus.sum(axis=1)
    conditional = np.divide(raw, visual_total, out=np.zeros_like(raw), where=visual_total > 0)
    return {"raw_mass": raw, "density": raw / indices.size, "conditional_share": conditional}


def dominance_score(a_density: float, b_density: float) -> float:
    denom = a_density + b_density
    return float((a_density - b_density) / denom) if denom > 0 else 0.0


def classify_shift(a_at_a: float, b_at_a: float, a_at_b: float, b_at_b: float, threshold: float = 0.10) -> str:
    """Classify scale-normalized A/B focus without using selection-time attention."""
    score_a = dominance_score(a_at_a, b_at_a)
    score_b = dominance_score(a_at_b, b_at_b)
    if score_a > threshold and score_b < -threshold:
        return "expected_A_to_B_shift"
    if score_a < -threshold and score_b > threshold:
        return "unexpected_reverse_shift"
    if score_a > threshold and score_b > threshold:
        return "persistent_A"
    if score_a < -threshold and score_b < -threshold:
        return "persistent_B"
    if abs(score_a) <= threshold and abs(score_b) <= threshold:
        return "simultaneous_A_B"
    return "no_clear_ROI_selectivity"
