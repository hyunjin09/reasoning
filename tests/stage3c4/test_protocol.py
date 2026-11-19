from __future__ import annotations

import pytest

from visual_reasoning.stage3c4.protocol import (
    classify_spatiotemporal_outcome,
    frozen_layer_scopes,
    temporal_query_indices,
)


def test_layer_scopes_are_exact_nested_plan_family() -> None:
    scopes = frozen_layer_scopes(language_layers=36)

    assert scopes == {
        "L0": [28, 29],
        "L1": [28, 29, 30, 31, 32, 33],
        "L2": list(range(24, 36)),
        "L3": list(range(16, 36)),
        "L4": list(range(36)),
    }
    assert all(set(scopes[left]) <= set(scopes[right]) for left, right in zip(scopes, list(scopes)[1:]))


def test_temporal_window_is_inclusive_and_refuses_missing_history() -> None:
    assert temporal_query_indices(current_generated_index=20, backward=4) == [16, 17, 18, 19, 20]
    with pytest.raises(ValueError):
        temporal_query_indices(current_generated_index=4, backward=4)


@pytest.mark.parametrize(
    ("layer_l4", "time_t16", "c_late4", "c_all4", "expected"),
    [
        (0.6, 0.2, 0.3, 0.2, "O1_layer_redundancy"),
        (0.95, 0.4, 0.4, 0.3, "O2_temporal_redundancy"),
        (0.95, 0.4, 0.95, 0.4, "O3_spatiotemporal_redundancy"),
        (0.95, 0.9, 0.95, 0.9, "O4_earlier_nonvisual_storage"),
    ],
)
def test_classification_uses_frozen_retention_rule(
    layer_l4: float, time_t16: float, c_late4: float, c_all4: float, expected: str
) -> None:
    assert classify_spatiotemporal_outcome(
        layer_l4_retention=layer_l4,
        time_t16_retention=time_t16,
        c_late4_retention=c_late4,
        c_all4_retention=c_all4,
        substantial_retention=0.80,
    ) == expected

