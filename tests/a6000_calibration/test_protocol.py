from __future__ import annotations

import pytest

from visual_reasoning.a6000_calibration.protocol import (
    extract_a5000_reference,
    target_cell_id,
)


def test_target_cell_id_maps_stage3c7_targets_to_stage3b7r_cells() -> None:
    assert target_cell_id("target_a") == "Ed__W4"
    assert target_cell_id("target_b") == "Ed_minus_1__W4"
    with pytest.raises(ValueError, match="Unknown calibration target"):
        target_cell_id("target_c")


def test_extract_a5000_reference_uses_same_frozen_cell() -> None:
    cell = {
        "base_problem_id": "7",
        "target_id": "target_b",
        "effect_stratum": "medium",
        "archived_anchor_effect": 0.4,
    }
    kv = {
        "base_problem_id": "7",
        "target_id": "target_b",
        "conditions": {
            "O": {"aligned_native": 2.0},
            "C": {"aligned_native": 1.5},
        },
        "sign_aligned": {"suppression_loss": 0.4, "rescue_gain": 0.35},
    }
    residual = {
        "base_problem_id": "7",
        "target_id": "target_b",
        "sign_aligned": {"rescue_gain": 0.1},
    }
    target_roi = {"base_problem_id": "7", "cell_id": "Ed_minus_1__W4", "BPR": 0.6}
    irrelevant = {"base_problem_id": "7", "cell_id": "Ed_minus_1__W4", "BPR": 0.05}
    row = extract_a5000_reference(
        cell,
        kv_row=kv,
        residual_row=residual,
        target_roi_row=target_roi,
        irrelevant_roi_row=irrelevant,
    )
    assert row["visual_content_effect"] == 3.5
    assert row["target_roi_effect"] == 0.6
    assert row["irrelevant_roi_effect"] == 0.05
    assert row["target_minus_irrelevant_roi"] == pytest.approx(0.55)
    assert row["kv_rescue_gain"] == 0.35
    assert row["current_residual_rescue_gain"] == 0.1


def test_extract_a5000_reference_rejects_cross_cell_mismatch() -> None:
    cell = {"base_problem_id": "7", "target_id": "target_a", "effect_stratum": "strong"}
    with pytest.raises(ValueError, match="reference rows do not match"):
        extract_a5000_reference(
            cell,
            kv_row={"base_problem_id": "8", "target_id": "target_a"},
            residual_row={"base_problem_id": "7", "target_id": "target_a"},
            target_roi_row={"base_problem_id": "7", "cell_id": "Ed__W4"},
            irrelevant_roi_row={"base_problem_id": "7", "cell_id": "Ed__W4"},
        )
