from __future__ import annotations

import numpy as np

from visual_reasoning.stage3c9.edits import normalize_numeric_surface, validate_quartet_arrays


def test_edit_quartet_validation_requires_changes_inside_roi_only() -> None:
    original = np.zeros((8, 8, 3), dtype=np.uint8)
    arrays = {name: original.copy() for name in ("O", "O_sham", "C", "C_sham")}
    arrays["O_sham"][2, 2] = 10
    arrays["C"][3, 3] = 20
    arrays["C_sham"][4, 4] = 30
    result = validate_quartet_arrays(arrays, [1, 1, 6, 6])
    assert result["passed"]
    arrays["C"][7, 7] = 1
    assert not validate_quartet_arrays(arrays, [1, 1, 6, 6])["passed"]


def test_edit_quartet_validation_requires_every_control_to_change_pixels() -> None:
    original = np.zeros((8, 8, 3), dtype=np.uint8)
    arrays = {name: original.copy() for name in ("O", "O_sham", "C", "C_sham")}
    arrays["O_sham"][2, 2] = 10
    arrays["C"][3, 3] = 20
    assert not validate_quartet_arrays(arrays, [1, 1, 6, 6])["passed"]


def test_numeric_normalization_allows_exact_integer_decimal_reuse() -> None:
    assert normalize_numeric_surface("36.0") == normalize_numeric_surface("36")
    assert normalize_numeric_surface("3.25") != normalize_numeric_surface("3")
