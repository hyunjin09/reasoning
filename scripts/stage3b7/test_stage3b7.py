from __future__ import annotations

import numpy as np
import pytest
import torch

from visual_reasoning.stage3b7.kv import compose_kv_sources
from visual_reasoning.stage3b7.protocol import classify_kv_mechanism, phase_a_gate_passes
from visual_reasoning.stage3b7.roi import (
    build_roi_token_groups,
    choose_matched_irrelevant,
    map_changed_pixels_to_tokens,
)


def test_changed_pixel_support_maps_to_merged_token_cells() -> None:
    changed = np.zeros((4, 6), dtype=bool)
    changed[0, 0] = True
    changed[3, 5] = True
    assert map_changed_pixels_to_tokens(changed, merged_rows=2, merged_cols=3) == [0, 5]


def test_roi_groups_are_disjoint_absolute_visual_positions() -> None:
    groups = build_roi_token_groups(
        visual_positions=list(range(10, 19)),
        target_local=[1],
        irrelevant_local=[8],
        merged_rows=3,
        merged_cols=3,
        ring_radius=1,
    )
    assert groups["V_target"] == [11]
    assert groups["V_other"] == [10, 12, 13, 14, 15, 16, 17, 18]
    assert groups["V_irrelevant"] == [18]
    assert groups["V_target_ring"] == [10, 11, 12, 13, 14, 15]
    assert set(groups["V_target"]).isdisjoint(groups["V_irrelevant"])
    assert set(groups["V_target"]) | set(groups["V_other"]) == set(range(10, 19))


def test_irrelevant_region_matches_cardinality_and_avoids_ring() -> None:
    darkness = np.asarray(
        [[0.8, 0.9, 0.7, 0.1], [0.9, 0.9, 0.8, 0.2], [0.6, 0.7, 0.5, 0.0]],
        dtype=np.float64,
    )
    selected, audit = choose_matched_irrelevant(
        target_local=[0, 1],
        excluded_local=[0, 1, 4, 5],
        darkness_by_cell=darkness,
    )
    assert len(selected) == 2
    assert set(selected).isdisjoint({0, 1, 4, 5})
    assert audit["matched_cardinality"]
    assert audit["selection_used_attention"] is False


@pytest.mark.parametrize(
    ("mode", "key_changed", "value_changed"),
    [("K", True, False), ("V", False, True), ("KV", True, True)],
)
def test_kv_composition_changes_only_requested_component_and_positions(
    mode: str, key_changed: bool, value_changed: bool
) -> None:
    recipient_key = torch.zeros((1, 2, 4, 3))
    recipient_value = torch.ones((1, 2, 4, 3))
    donor_key = recipient_key + 2
    donor_value = recipient_value + 3
    key, value, audit = compose_kv_sources(
        recipient_key,
        recipient_value,
        donor_key,
        donor_value,
        positions=[1, 3],
        mode=mode,
    )
    assert bool(torch.any(key[:, :, [1, 3]] != recipient_key[:, :, [1, 3]])) is key_changed
    assert bool(torch.any(value[:, :, [1, 3]] != recipient_value[:, :, [1, 3]])) is value_changed
    assert torch.equal(key[:, :, [0, 2]], recipient_key[:, :, [0, 2]])
    assert torch.equal(value[:, :, [0, 2]], recipient_value[:, :, [0, 2]])
    assert audit["key_swapped"] is key_changed
    assert audit["value_swapped"] is value_changed
    assert audit["nonassigned_key_max_abs_delta"] == 0.0
    assert audit["nonassigned_value_max_abs_delta"] == 0.0


def test_phase_a_gate_requires_robust_target_irrelevant_separation_and_half_recovery() -> None:
    robust = {
        "robust": True,
        "median_PRR": 0.62,
    }
    contrast = {
        "bootstrap_95_CI": [0.1, 0.7],
        "target_greater_fraction": 0.76,
    }
    assert phase_a_gate_passes(
        target_summary=robust,
        ring_summary={"median_PRR": 0.8},
        target_minus_irrelevant=contrast,
    )
    assert not phase_a_gate_passes(
        target_summary={**robust, "robust": False},
        ring_summary={"median_PRR": 0.8},
        target_minus_irrelevant=contrast,
    )
    assert not phase_a_gate_passes(
        target_summary={**robust, "median_PRR": 0.4},
        ring_summary={"median_PRR": 0.49},
        target_minus_irrelevant=contrast,
    )


def test_kv_mechanism_classification_uses_frozen_dominance_rules() -> None:
    assert classify_kv_mechanism(
        k={"robust": False, "median_KVR": 0.1},
        v={"robust": True, "median_KVR": 0.9},
        interaction={"bootstrap_95_CI": [-0.1, 0.2]},
    ) == "Value-Dominant"
    assert classify_kv_mechanism(
        k={"robust": True, "median_KVR": 0.85},
        v={"robust": False, "median_KVR": 0.2},
        interaction={"bootstrap_95_CI": [-0.1, 0.2]},
    ) == "Routing-Dominant"
    assert classify_kv_mechanism(
        k={"robust": True, "median_KVR": 0.45},
        v={"robust": True, "median_KVR": 0.55},
        interaction={"bootstrap_95_CI": [0.05, 0.3]},
    ) == "Routing+Value-Interaction"
