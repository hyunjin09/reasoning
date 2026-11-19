from __future__ import annotations

import pytest

from visual_reasoning.stage3c5.protocol import (
    carrier_restoration,
    classify_handoff,
    evaluate_phase_b_gate,
    frozen_tpre_layer_scopes,
    reduced_control_arms,
    select_necessary_scope,
)


def test_frozen_tpre_scopes_match_plan() -> None:
    assert frozen_tpre_layer_scopes(language_layers=36) == {
        "P0": [28, 29],
        "P1": [32, 33],
        "P2": list(range(28, 34)),
        "P3": list(range(24, 36)),
        "P4": list(range(16, 36)),
        "P5": list(range(36)),
    }


def test_phase_b_gate_requires_direction_significance_and_historical_fraction() -> None:
    passed = evaluate_phase_b_gate(
        median_loss=0.30,
        positive_count=19,
        adjusted_p=0.01,
        n=24,
        historical_increment=1.3069,
        minimum_historical_fraction=0.20,
    )
    assert passed["pass"] is True
    failed = evaluate_phase_b_gate(
        median_loss=0.20,
        positive_count=24,
        adjusted_p=0.001,
        n=24,
        historical_increment=1.3069,
        minimum_historical_fraction=0.20,
    )
    assert failed["pass"] is False


def test_selects_smallest_p_scope_reaching_eighty_percent_of_p5() -> None:
    rows = {
        "P0": {"median_loss": 0.20, "positive_count": 18, "adjusted_p": 0.01},
        "P1": {"median_loss": 0.10, "positive_count": 20, "adjusted_p": 0.01},
        "P2": {"median_loss": 0.84, "positive_count": 20, "adjusted_p": 0.01},
        "P3": {"median_loss": 0.90, "positive_count": 21, "adjusted_p": 0.01},
        "P4": {"median_loss": 0.95, "positive_count": 22, "adjusted_p": 0.01},
        "P5": {"median_loss": 1.00, "positive_count": 24, "adjusted_p": 0.01},
    }
    selected = select_necessary_scope(rows, n=24, fraction_of_p5=0.80)
    assert selected["scope_id"] == "P2"
    assert selected["threshold_loss"] == pytest.approx(0.8)


def test_bidirectional_carrier_restoration_uses_source_oriented_shifts() -> None:
    result = carrier_restoration(
        native_o=4.0,
        native_c=-2.0,
        donor_o_into_c=1.0,
        donor_c_into_o=0.5,
    )
    assert result["reference_gap"] == pytest.approx(6.0)
    assert result["o_into_c_shift"] == pytest.approx(3.0)
    assert result["c_into_o_shift"] == pytest.approx(3.5)
    assert result["BCR"] == pytest.approx(3.25)
    assert result["CRR"] == pytest.approx(3.25 / 6.0)


def test_handoff_classification_preserves_separate_carriers() -> None:
    assert classify_handoff(r_robust=True, q_robust=False, hpre_robust=False, r_expands=False) == "H1_immediate_R_carrier"
    assert classify_handoff(r_robust=True, q_robust=False, hpre_robust=False, r_expands=True) == "H2_short_R_accumulation"
    assert classify_handoff(r_robust=False, q_robust=True, hpre_robust=False, r_expands=False) == "H3_Q_carrier"
    assert classify_handoff(r_robust=False, q_robust=False, hpre_robust=True, r_expands=False) == "H4_current_residual_carrier"
    assert classify_handoff(r_robust=True, q_robust=True, hpre_robust=False, r_expands=False) == "H5_mixed_carrier"
    assert classify_handoff(r_robust=False, q_robust=False, hpre_robust=False, r_expands=False) == "H6_no_clean_carrier"


def test_reduced_controls_use_only_selected_scope_at_tpre() -> None:
    assert reduced_control_arms([16, 17]) == [
        {"arm_id": "T_tpre", "source": "T", "layers": [16, 17]},
        {"arm_id": "M_tpre", "source": "M", "layers": [16, 17]},
        {"arm_id": "I_tpre", "source": "I", "layers": [16, 17]},
    ]
