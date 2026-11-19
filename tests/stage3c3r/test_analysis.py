from __future__ import annotations

import pytest

from visual_reasoning.stage3c3r.analysis import holm_adjust, query_operating_point


def test_query_operating_point_keeps_direction_information() -> None:
    result = query_operating_point([1.0, 0.0, 0.0], [0.5, 0.5, 0.0])

    assert result["lambda_query_norm"] == pytest.approx(2.0**-0.5)
    assert result["lambda_query_proj"] == pytest.approx(0.5)


def test_query_operating_point_rejects_zero_native_vector() -> None:
    with pytest.raises(ValueError):
        query_operating_point([0.0, 0.0], [1.0, 0.0])


def test_holm_adjust_is_monotone_in_sorted_p_values() -> None:
    adjusted = holm_adjust([0.01, 0.04, 0.03, 0.2])

    assert adjusted == pytest.approx([0.04, 0.09, 0.09, 0.2])
