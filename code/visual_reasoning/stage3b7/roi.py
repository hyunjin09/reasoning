"""Attention-independent mapping from Stage 3A edit pixels to visual tokens."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np


def map_changed_pixels_to_tokens(
    changed_pixels: np.ndarray, *, merged_rows: int, merged_cols: int
) -> list[int]:
    """Map every changed source pixel to its row-major merged-token cell."""

    mask = np.asarray(changed_pixels, dtype=bool)
    rows, cols = int(merged_rows), int(merged_cols)
    if mask.ndim != 2 or not mask.any():
        raise ValueError("The edit-pixel mask must be nonempty and two-dimensional")
    if rows <= 0 or cols <= 0:
        raise ValueError("Merged visual-grid dimensions must be positive")
    height, width = mask.shape
    y, x = np.nonzero(mask)
    grid_y = np.minimum(rows - 1, y * rows // height)
    grid_x = np.minimum(cols - 1, x * cols // width)
    return sorted({int(row * cols + col) for row, col in zip(grid_y, grid_x)})


def fixed_ring(
    target_local: Sequence[int], *, merged_rows: int, merged_cols: int, radius: int
) -> list[int]:
    """Return target plus a fixed Chebyshev-radius ring on the merged grid."""

    rows, cols, radius = int(merged_rows), int(merged_cols), int(radius)
    target = sorted({int(value) for value in target_local})
    if not target or radius < 0 or target[0] < 0 or target[-1] >= rows * cols:
        raise ValueError("Invalid target tokens or ring radius")
    selected: set[int] = set()
    for value in target:
        row, col = divmod(value, cols)
        for other_row in range(max(0, row - radius), min(rows, row + radius + 1)):
            for other_col in range(max(0, col - radius), min(cols, col + radius + 1)):
                selected.add(other_row * cols + other_col)
    return sorted(selected)


def cell_darkness(image_rgb: np.ndarray, *, merged_rows: int, merged_cols: int) -> np.ndarray:
    """Compute mean grayscale darkness in each merged visual-token footprint."""

    image = np.asarray(image_rgb)
    rows, cols = int(merged_rows), int(merged_cols)
    if image.ndim != 3 or image.shape[2] != 3 or rows <= 0 or cols <= 0:
        raise ValueError("Expected an RGB image and positive merged grid")
    gray = image.astype(np.float64).mean(axis=2) / 255.0
    height, width = gray.shape
    result = np.empty((rows, cols), dtype=np.float64)
    for row in range(rows):
        y0, y1 = row * height // rows, (row + 1) * height // rows
        for col in range(cols):
            x0, x1 = col * width // cols, (col + 1) * width // cols
            result[row, col] = float(1.0 - gray[y0:y1, x0:x1].mean())
    return result


def choose_matched_irrelevant(
    *,
    target_local: Sequence[int],
    excluded_local: Sequence[int],
    darkness_by_cell: np.ndarray,
) -> tuple[list[int], dict[str, Any]]:
    """Choose a translated, cardinality-matched low-ink control before scoring."""

    darkness = np.asarray(darkness_by_cell, dtype=np.float64)
    if darkness.ndim != 2 or not np.isfinite(darkness).all():
        raise ValueError("Cell darkness must be a finite two-dimensional grid")
    rows, cols = darkness.shape
    target = sorted({int(value) for value in target_local})
    excluded = {int(value) for value in excluded_local}
    if not target or target[0] < 0 or target[-1] >= rows * cols:
        raise ValueError("Target local positions are invalid")
    coords = [divmod(value, cols) for value in target]
    min_row = min(row for row, _ in coords)
    min_col = min(col for _, col in coords)
    shape = [(row - min_row, col - min_col) for row, col in coords]
    height = max(row for row, _ in shape) + 1
    width = max(col for _, col in shape) + 1
    target_center = np.asarray(
        [np.mean([row for row, _ in coords]), np.mean([col for _, col in coords])]
    )
    candidates: list[tuple[float, float, tuple[int, ...]]] = []
    for anchor_row in range(rows - height + 1):
        for anchor_col in range(cols - width + 1):
            values = tuple(
                sorted((anchor_row + row) * cols + anchor_col + col for row, col in shape)
            )
            if set(values) & excluded:
                continue
            candidate_coords = [divmod(value, cols) for value in values]
            ink = float(np.mean([darkness[row, col] for row, col in candidate_coords]))
            center = np.asarray(
                [
                    np.mean([row for row, _ in candidate_coords]),
                    np.mean([col for _, col in candidate_coords]),
                ]
            )
            distance = float(np.linalg.norm(center - target_center))
            candidates.append((ink, -distance, values))
    method = "translated_target_shape_minimum_ink"
    if candidates:
        ink, negative_distance, selected_tuple = min(candidates)
        selected = list(selected_tuple)
        distance = -negative_distance
    else:
        available = [value for value in range(rows * cols) if value not in excluded]
        if len(available) < len(target):
            raise ValueError("No cardinality-matched irrelevant region is feasible")
        selected = sorted(available, key=lambda value: (darkness.flat[value], value))[: len(target)]
        ink = float(np.mean([darkness.flat[value] for value in selected]))
        distance = float("nan")
        method = "fallback_individual_minimum_ink_cells"
    return sorted(selected), {
        "method": method,
        "target_token_count": len(target),
        "irrelevant_token_count": len(selected),
        "matched_cardinality": len(selected) == len(target),
        "mean_darkness": ink,
        "distance_from_target_center": distance,
        "excluded_token_count": len(excluded),
        "selection_used_attention": False,
    }


def build_roi_token_groups(
    *,
    visual_positions: Sequence[int],
    target_local: Sequence[int],
    irrelevant_local: Sequence[int],
    merged_rows: int,
    merged_cols: int,
    ring_radius: int,
) -> dict[str, list[int]]:
    """Build frozen absolute visual-source groups and verify isolation."""

    visual = [int(value) for value in visual_positions]
    rows, cols = int(merged_rows), int(merged_cols)
    if len(visual) != rows * cols or len(set(visual)) != len(visual):
        raise ValueError("Visual placeholder positions must match the merged grid")
    target = sorted({int(value) for value in target_local})
    irrelevant = sorted({int(value) for value in irrelevant_local})
    ring = fixed_ring(target, merged_rows=rows, merged_cols=cols, radius=ring_radius)
    valid = set(range(rows * cols))
    if not target or not irrelevant or not (set(target) | set(irrelevant)).issubset(valid):
        raise ValueError("Target and irrelevant token groups must be valid and nonempty")
    if set(target) & set(irrelevant) or set(ring) & set(irrelevant):
        raise ValueError("Matched irrelevant tokens must be disjoint from target plus ring")
    target_set = set(target)
    absolute = lambda values: [visual[index] for index in values]
    return {
        "V_all": visual,
        "V_target": absolute(target),
        "V_other": absolute([index for index in range(rows * cols) if index not in target_set]),
        "V_irrelevant": absolute(irrelevant),
        "V_target_ring": absolute(ring),
    }


__all__ = [
    "build_roi_token_groups",
    "cell_darkness",
    "choose_matched_irrelevant",
    "fixed_ring",
    "map_changed_pixels_to_tokens",
]
