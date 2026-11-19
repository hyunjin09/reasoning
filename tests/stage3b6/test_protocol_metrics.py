from __future__ import annotations

import pytest

from visual_reasoning.stage3b6.metrics import aggregate_base_medians, head_restoration_metrics
from visual_reasoning.stage3b6.protocol import (
    build_frozen_cells,
    discovery_head_passes,
    freeze_ranked_head_sets,
    primary_head_passes,
)


def _recipient_scores(scale: float = 1.0) -> dict[str, dict[str, float]]:
    return {
        "O": {"O": 4.0, "O_sham": 3.9, "C": 2.0, "C_sham": 2.1},
        "C": {"O": 3.0, "O_sham": 2.9, "C": 1.0, "C_sham": 1.1},
    }


def test_head_metric_preserves_bidirectional_paired_semantic_controls() -> None:
    metrics = head_restoration_metrics(
        recipient_scores=_recipient_scores(),
        stage3b5_attention_gain=4.0,
    )
    assert metrics["BHR_O"] == pytest.approx(1.9)
    assert metrics["BHR_C"] == pytest.approx(1.9)
    assert metrics["BHR"] == pytest.approx(1.9)
    assert metrics["HRR"] == pytest.approx(0.475)
    assert metrics["bidirectionally_source_consistent"]
    assert metrics["sham_effect"] == pytest.approx(0.1)


def test_exact_cells_and_layers_are_loaded_without_search() -> None:
    cells = build_frozen_cells(
        target_by_window={
            "W4": {"fine_window": "F28_29", "layers": [28, 29]},
            "W5": {"fine_window": "F32_33", "layers": [32, 33]},
        },
        qualifying={
            "attention": [
                {"coordinate": "Ed_minus_1", "window": "W4"},
                {"coordinate": "Ed_minus_1", "window": "W5"},
                {"coordinate": "Ed", "window": "W4"},
            ],
            "upstream": [{"coordinate": "Ed", "window": "W5"}],
        },
    )
    assert [(row["cell_id"], row["layer_index"]) for row in cells] == [
        ("Ed_minus_1__W4", 28),
        ("Ed_minus_1__W5", 32),
        ("Ed__W4", 29),
        ("Ed__W5", 32),
    ]
    assert cells[-1]["role"] == "upstream_control"


def test_discovery_ranking_and_cumulative_sets_are_outcome_frozen() -> None:
    rows = [
        {"head_index": 0, "median_BHR": 0.2, "discovery_pass": False},
        {"head_index": 1, "median_BHR": 1.2, "discovery_pass": True},
        {"head_index": 2, "median_BHR": 0.8, "discovery_pass": True},
        {"head_index": 3, "median_BHR": -0.1, "discovery_pass": False},
    ]
    frozen = freeze_ranked_head_sets(rows, total_query_heads=4)
    assert frozen["ranking"] == [1, 2, 0, 3]
    assert frozen["robust_heads"] == [1, 2]
    assert frozen["sets"]["Top_1"] == [1]
    assert frozen["sets"]["Top_2"] == [1, 2]
    assert frozen["sets"]["Top_4"] == [1, 2, 0, 3]
    assert frozen["sets"]["All_robust"] == [1, 2]


def test_discovery_and_primary_gates_use_frozen_control_thresholds() -> None:
    discovery = {
        "median_BHR": 0.5,
        "bidirectional_count": 7,
        "base_count": 8,
        "median_sham_to_semantic_ratio": 0.2,
        "all_self_exact": True,
        "median_HRR": 0.11,
    }
    assert discovery_head_passes(discovery)
    assert not discovery_head_passes({**discovery, "bidirectional_count": 6})

    primary = {
        "holm_adjusted_p": 0.01,
        "bootstrap_95_CI": [0.1, 0.8],
        "bidirectional_fraction": 0.75,
        "median_sham_to_semantic_ratio": 0.2,
        "all_self_exact": True,
        "median_HRR": 0.3,
    }
    assert primary_head_passes(primary)
    assert not primary_head_passes({**primary, "median_HRR": 0.24})


def test_secondary_moderators_aggregate_to_one_row_per_base() -> None:
    rows = [
        {"base_problem_id": "1", "x": 1.0, "y": 10.0},
        {"base_problem_id": "1", "x": 3.0, "y": 30.0},
        {"base_problem_id": "2", "x": 7.0, "y": 70.0},
    ]
    assert aggregate_base_medians(rows, value_keys=("x", "y")) == [
        {"base_problem_id": "1", "x": 2.0, "y": 20.0, "aggregated_cell_count": 2},
        {"base_problem_id": "2", "x": 7.0, "y": 70.0, "aggregated_cell_count": 1},
    ]
