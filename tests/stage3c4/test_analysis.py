from __future__ import annotations

import pytest

from visual_reasoning.stage3c4.analysis import (
    holm_adjust,
    retention_summary,
    tested_window_threshold as compute_tested_window_threshold,
)


def test_retention_summary_keeps_unnormalized_effect_primary() -> None:
    result = retention_summary(
        native=[10.0, 5.0, 2.0],
        suppressed=[8.0, 1.0, 2.2],
        seed=7,
        resamples=100,
    )

    assert result["unnormalized_loss"] == pytest.approx([2.0, 4.0, -0.2])
    assert result["retained_evidence"] == pytest.approx([0.8, 0.2, 1.1])
    assert result["retained_evidence_is_clipped"] is False
    assert result["fraction_retaining_at_least_0_80"] == pytest.approx(2 / 3)


def test_tested_window_threshold_uses_shortest_tested_backward_scope() -> None:
    curve = {"T0": 0.95, "T1": 0.9, "T2": 0.81, "T4": 0.79, "T8": 0.5, "T16": 0.2}
    assert compute_tested_window_threshold(curve, threshold=0.80) == "T4"
    assert compute_tested_window_threshold(curve, threshold=0.50) == "T16"


def test_holm_adjust_is_monotone_in_sorted_p_values() -> None:
    assert holm_adjust([0.01, 0.04, 0.03, 0.2]) == pytest.approx([0.04, 0.09, 0.09, 0.2])
