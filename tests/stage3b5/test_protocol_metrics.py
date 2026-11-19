from __future__ import annotations

from visual_reasoning.stage3b5.metrics import boundary_increments, recompute_contrasts
from visual_reasoning.stage3b5.protocol import (
    BOUNDARIES,
    build_primary_family,
    evaluate_stage3b5_decision,
)


def test_primary_family_is_exactly_40_unique_boundary_tests() -> None:
    targets = {
        "W4": {"fine_window": "F28_29", "layers": [28, 29]},
        "W5": {"fine_window": "F32_33", "layers": [32, 33]},
    }
    family = build_primary_family(targets)
    assert len(family) == 40
    assert len({row["test_id"] for row in family}) == 40
    assert {row["boundary"] for row in family} == set(BOUNDARIES)
    assert sum(row["two_layer_entry_alias"] for row in family) == 4


def test_boundary_increments_and_recompute_comparisons_are_signed() -> None:
    values = {
        "h_pre": 2.0,
        "pre_attn_norm": 2.5,
        "h_post_attn": 6.0,
        "pre_mlp_norm": 6.5,
        "h_post_block": 10.0,
    }
    increments = boundary_increments(values)
    assert increments["G_attn"] == 4.0
    assert increments["G_mlp"] == 4.0
    assert increments["G_input_norm"] == 0.5
    assert increments["G_post_attn_norm"] == 0.5
    contrasts = recompute_contrasts(
        h_pre_recompute=6.0,
        h_post_attn_recompute=5.0,
        precomputed_joint=2.0,
        precomputed_mlp=1.5,
    )
    assert contrasts == {
        "h_pre_vs_precomputed_joint": 4.0,
        "h_post_attn_vs_precomputed_mlp": 3.5,
    }


def robust(median: float, *, ratio: float = 0.0) -> dict:
    return {
        "robust": True,
        "BMR_median": median,
        "final_block_ratio_median": ratio,
        "gain_to_final_block_median": ratio,
        "gain_bootstrap_CI_low": 0.1,
    }


def blank_cell(coordinate: str, window: str) -> dict:
    return {
        "coordinate": coordinate,
        "window": window,
        "final_block": robust(10.0, ratio=1.0),
        "first_h_pre": robust(1.0, ratio=0.1),
        "attention_gain": {"qualifies": False},
        "mlp_gain": {"qualifies": False},
        "two_layer_recompute": {"qualifies": False},
    }


def test_decision_priority_is_frozen_and_requires_two_cells() -> None:
    cells = [
        blank_cell(coordinate, window)
        for coordinate in ("Ed_minus_1", "Ed")
        for window in ("W4", "W5")
    ]
    for row in cells[:2]:
        row["first_h_pre"] = robust(8.5, ratio=0.85)
    decision = evaluate_stage3b5_decision(cells, controls_pass=True)
    assert decision["recommendation"] == "GO — Upstream residual-origin search"

    for row in cells:
        row["first_h_pre"] = robust(1.0, ratio=0.1)
    for row in cells[:2]:
        row["two_layer_recompute"] = {"qualifies": True}
        row["attention_gain"] = {"qualifies": True}
    decision = evaluate_stage3b5_decision(cells, controls_pass=True)
    assert decision["recommendation"] == "GO — Cross-layer sequential mediation"

    decision = evaluate_stage3b5_decision(cells, controls_pass=False)
    assert decision["recommendation"] == "REDIRECT — Broader residual/norm interaction"

