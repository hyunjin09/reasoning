from __future__ import annotations

import math

from visual_reasoning.stage3b4.metrics import (
    bootstrap_summary,
    module_interaction_metrics,
    module_restoration_metrics,
    one_sided_wilcoxon_greater,
)
from visual_reasoning.stage3b4.protocol import (
    evaluate_module_decision,
    holm_adjust,
    retained_module_targets,
)


def test_module_restoration_reuses_paired_semantic_contrast() -> None:
    result = module_restoration_metrics(
        recipient_scores={
            "O": {"O": 5.0, "O_sham": 4.8, "C": 1.0, "C_sham": 1.2},
            "C": {"O": 4.0, "O_sham": 4.2, "C": 0.0, "C_sham": 0.2},
        },
        all_layer_bri=10.0,
    )

    assert math.isclose(result["BMR"], 3.9)
    assert math.isclose(result["BMR_normalized"], 0.39)
    assert result["bidirectionally_source_consistent"]
    assert math.isclose(result["A_render"], 0.2)


def test_module_interaction_and_ratios_are_not_clipped() -> None:
    result = module_interaction_metrics(
        attention=3.0,
        mlp=2.0,
        joint=7.0,
        block=5.0,
    )

    assert result == {
        "attention_to_block_ratio": 0.6,
        "mlp_to_block_ratio": 0.4,
        "joint_to_block_ratio": 1.4,
        "interaction": 2.0,
    }


def test_primary_statistics_are_deterministic_and_one_sided() -> None:
    values = [1.0, 2.0, 3.0, 4.0]
    first = bootstrap_summary(values, seed=1234, resamples=2_000)
    second = bootstrap_summary(values, seed=1234, resamples=2_000)

    assert first == second
    assert first["N"] == 4
    assert first["median"] == 2.5
    assert first["bootstrap_95_CI"][0] > 0.0
    assert 0.0 <= one_sided_wilcoxon_greater(values) <= 1.0
    assert one_sided_wilcoxon_greater([0.0, 0.0]) == 1.0


def test_holm_adjust_uses_the_complete_fixed_family() -> None:
    adjusted = holm_adjust({"a": 0.001, "b": 0.01, "c": 0.04, "d": 0.5}, alpha=0.05)

    assert math.isclose(adjusted["a"]["adjusted_p"], 0.004)
    assert math.isclose(adjusted["b"]["adjusted_p"], 0.03)
    assert math.isclose(adjusted["c"]["adjusted_p"], 0.08)
    assert adjusted["a"]["rejected"]
    assert adjusted["b"]["rejected"]
    assert not adjusted["c"]["rejected"]
    assert not adjusted["d"]["rejected"]


def test_retained_targets_require_one_fine_window_per_authorized_cell() -> None:
    decision = {
        "narrow_candidates": [
            {"coordinate": coordinate, "window": window, "fine_retains": True}
            for coordinate in ("Ed_minus_1", "Ed")
            for window in ("W4", "W5")
        ]
    }
    fine_rows = []
    for coordinate in ("Ed_minus_1", "Ed"):
        fine_rows.extend([
            {
                "coordinate": coordinate,
                "parent_window": "W4",
                "name": "F28_29",
                "layers": [28, 29],
                "BWS_median": 0.25,
                "BSRC_median": 0.32,
            },
            {
                "coordinate": coordinate,
                "parent_window": "W5",
                "name": "F32_33",
                "layers": [32, 33],
                "BWS_median": 0.16,
                "BSRC_median": 0.23,
            },
        ])

    targets = retained_module_targets(decision=decision, fine_rows=fine_rows)

    assert len(targets) == 4
    assert {(row["window"], tuple(row["layers"])) for row in targets} == {
        ("W4", (28, 29)),
        ("W5", (32, 33)),
    }


def test_decision_prefers_attention_to_mlp_cascade_when_joint_is_strongest() -> None:
    rows = []
    for coordinate in ("Ed_minus_1", "Ed"):
        for window in ("W4", "W5"):
            rows.append({
                "coordinate": coordinate,
                "window": window,
                "block_robust": True,
                "attention": {"robust": True, "block_ratio_median": 0.4, "BMR_median": 4.0},
                "mlp": {"robust": True, "block_ratio_median": 0.3, "BMR_median": 3.0},
                "joint": {"robust": True, "block_ratio_median": 0.9, "BMR_median": 9.0},
            })

    decision = evaluate_module_decision(rows, controls_pass=True)

    assert decision["recommendation"] == "GO — Attention→MLP cascade analysis"
    assert len(decision["cascade_cells"]) == 4


def test_decision_redirects_when_only_full_block_is_robust() -> None:
    rows = [
        {
            "coordinate": coordinate,
            "window": window,
            "block_robust": True,
            "attention": {"robust": False, "block_ratio_median": 0.1, "BMR_median": 1.0},
            "mlp": {"robust": False, "block_ratio_median": 0.1, "BMR_median": 1.0},
            "joint": {"robust": False, "block_ratio_median": 0.2, "BMR_median": 2.0},
        }
        for coordinate in ("Ed_minus_1", "Ed")
        for window in ("W4", "W5")
    ]

    decision = evaluate_module_decision(rows, controls_pass=True)

    assert decision["recommendation"] == "REDIRECT — Distributed block computation"
