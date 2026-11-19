"""Deterministic counterfactual-sham construction and pixel validation."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from visual_reasoning.stage3a.edits import _checked_roi, _render


_TEXT_PATTERN = re.compile(
    r"render\s+'(?P<original>[^']+)'\s+\(sham\)\s+or\s+'(?P<counterfactual>[^']+)'\s+\(counterfactual\)"
)


def extract_rendered_texts(description: str) -> tuple[str, str]:
    match = _TEXT_PATTERN.search(str(description))
    if match is None:
        raise ValueError(f"Cannot extract numeric render labels from: {description!r}")
    return match.group("original"), match.group("counterfactual")


def build_counterfactual_sham(
    source_path: Path,
    output_path: Path,
    render_spec: Mapping[str, Any],
    *,
    anchor: Sequence[int],
) -> Path:
    """Independently rerender the C semantic label from the original source image."""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    spec = dict(render_spec)
    spec["text_anchor"] = [int(value) for value in anchor]
    with Image.open(source_path) as image:
        _render(image.convert("RGB"), str(spec["counterfactual_text"]), spec).save(output_path)
    return output_path


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_four_image_conditions(
    paths: Mapping[str, Path], roi_xyxy: Sequence[int]
) -> dict[str, Any]:
    required = {"O", "O_sham", "C", "C_sham"}
    if set(paths) != required:
        raise ValueError(f"Four-image validation requires exactly {sorted(required)}")
    arrays = {name: np.asarray(Image.open(path).convert("RGB")) for name, path in paths.items()}
    shapes = {name: list(value.shape) for name, value in arrays.items()}
    dimensions_match = len({tuple(value.shape) for value in arrays.values()}) == 1
    if not dimensions_match:
        return {"passed": False, "dimensions_match": False, "shapes": shapes}
    height, width = arrays["O"].shape[:2]
    x0, y0, x1, y1 = _checked_roi(roi_xyxy, width, height)
    inside = np.zeros((height, width), dtype=bool)
    inside[y0:y1, x0:x1] = True
    outside = ~inside
    original = arrays["O"]
    outside_exact = {
        name: bool(np.array_equal(original[outside], arrays[name][outside]))
        for name in ("O_sham", "C", "C_sham")
    }

    def diff(left: str, right: str) -> int:
        return int(np.count_nonzero(np.any(arrays[left][inside] != arrays[right][inside], axis=-1)))

    changes = {
        "O_vs_O_sham_diff_pixels_inside_roi": diff("O", "O_sham"),
        "O_vs_C_diff_pixels_inside_roi": diff("O", "C"),
        "O_vs_C_sham_diff_pixels_inside_roi": diff("O", "C_sham"),
        "O_sham_vs_C_diff_pixels_inside_roi": diff("O_sham", "C"),
        "C_vs_C_sham_diff_pixels_inside_roi": diff("C", "C_sham"),
    }
    passed = bool(
        all(outside_exact.values())
        and all(value > 0 for value in changes.values())
    )
    return {
        "passed": passed,
        "dimensions_match": True,
        "shapes": shapes,
        "outside_roi_exact_to_O": outside_exact,
        "all_outside_roi_exact_to_O": all(outside_exact.values()),
        **changes,
        "sha256": {name: _sha256(Path(path)) for name, path in paths.items()},
    }
