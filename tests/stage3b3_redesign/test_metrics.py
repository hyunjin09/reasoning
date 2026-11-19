import pytest

from visual_reasoning.stage3b3_redesign.metrics import (
    evaluate_restoration_gates,
    semantic_restoration_metrics,
)


def test_semantic_restoration_separates_identity_from_render_variation() -> None:
    result = semantic_restoration_metrics(
        original_history={"O": 2.0, "O_sham": 1.8, "C": -1.0, "C_sham": -0.8},
        counterfactual_history={"O": 1.0, "O_sham": 0.8, "C": -2.0, "C_sham": -1.8},
        all_layer_bri=8.0,
    )

    assert result["SRC_O"] == pytest.approx(2.8)
    assert result["SRC_C"] == pytest.approx(2.8)
    assert result["BSRC"] == pytest.approx(2.8)
    assert result["A_render"] == pytest.approx(0.2)
    assert result["active"] is True
    assert result["render_to_semantic_ratio"] == pytest.approx(0.2 / 2.8)
    assert result["render_to_all_layer_ratio"] == pytest.approx(0.025)


def _gate_rows(*, consistent_bases: int, active_bases: int = 8, artifact: float = 0.1):
    rows = []
    for base in range(8):
        active = base < active_bases
        consistent = base < consistent_bases
        rows.append({
            "base_problem_id": str(base),
            "window": "W0",
            "coordinate": "Ed",
            "SRC_O": 1.0 if consistent else -1.0,
            "SRC_C": 1.0 if consistent else -1.0,
            "BSRC": 1.0 if active else 0.05,
            "A_render": artifact,
            "all_layer_BRI": 5.0,
            "active": active,
            "render_to_semantic_ratio": artifact / (1.0 if active else 0.05),
            "render_to_all_layer_ratio": artifact / 5.0,
        })
    return rows


def test_gate_requires_seven_of_eight_independent_bases() -> None:
    passed = evaluate_restoration_gates(_gate_rows(consistent_bases=7))
    failed_direction = evaluate_restoration_gates(_gate_rows(consistent_bases=6))
    failed_activity = evaluate_restoration_gates(_gate_rows(consistent_bases=7, active_bases=6))

    assert passed["all_gates_passed"] is True
    assert passed["gate_A"]["one_sided_exact_binomial_p"] < 0.05
    assert failed_direction["gate_A"]["passed"] is False
    assert failed_activity["gate_B"]["passed"] is False


def test_render_gates_use_within_base_active_window_medians() -> None:
    rows = _gate_rows(consistent_bases=8, artifact=0.1)
    rows.append({**rows[0], "window": "W1", "A_render": 100.0,
                 "render_to_semantic_ratio": 100.0, "render_to_all_layer_ratio": 20.0,
                 "active": False, "BSRC": 0.01})

    result = evaluate_restoration_gates(rows)

    assert result["gate_C"]["passed"] is True
    assert result["gate_D"]["passed"] is True

