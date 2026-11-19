from pathlib import Path

import numpy as np
from PIL import Image

from visual_reasoning.stage3b3_redesign.images import (
    build_counterfactual_sham,
    extract_rendered_texts,
    validate_four_image_conditions,
)


def test_extract_rendered_texts_from_frozen_edit_description() -> None:
    old, new = extract_rendered_texts(
        "mask ROI and render '40°' (sham) or '100°' (counterfactual) with one shared renderer"
    )
    assert (old, new) == ("40°", "100°")


def test_counterfactual_sham_is_local_distinct_and_shape_matched(tmp_path: Path) -> None:
    source = tmp_path / "source.png"
    o_sham = tmp_path / "o_sham.png"
    counterfactual = tmp_path / "counterfactual.png"
    c_sham = tmp_path / "c_sham.png"
    Image.fromarray(np.full((30, 60, 3), 255, dtype=np.uint8)).save(source)
    spec = {
        "roi_xyxy": [10, 5, 40, 25],
        "counterfactual_text": "12",
        "font_size": 12,
        "text_anchor": [2, 1],
        "counterfactual_sham_anchor": [3, 1],
        "text_color": [0, 0, 0],
        "background_color": [255, 255, 255],
    }
    build_counterfactual_sham(source, o_sham, {**spec, "counterfactual_text": "10"}, anchor=[2, 1])
    build_counterfactual_sham(source, counterfactual, spec, anchor=[2, 1])
    build_counterfactual_sham(source, c_sham, spec, anchor=[3, 1])
    conditions = {"O": source, "O_sham": o_sham, "C": counterfactual, "C_sham": c_sham}

    checks = validate_four_image_conditions(conditions, spec["roi_xyxy"])

    assert checks["dimensions_match"] is True
    assert checks["all_outside_roi_exact_to_O"] is True
    assert checks["C_vs_C_sham_diff_pixels_inside_roi"] > 0
    assert checks["passed"] is True
