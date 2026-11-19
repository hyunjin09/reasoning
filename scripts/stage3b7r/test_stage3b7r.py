"""CPU-only regression tests for prospectively frozen Stage 3B.7-R rules."""

from __future__ import annotations

import numpy as np

from visual_reasoning.stage3b7r.protocol import (
    aggregate_numeric_fields_by_base,
    flatten_scoring_results,
    paired_margins,
    primary_roi_gate,
    select_historical_visual_row,
    spatial_category,
    target_validation_gate,
    validate_disjoint_split,
)


def test_secondary_rows_are_aggregated_by_base() -> None:
    rows = [
        {"base_problem_id": "2", "attention": 0.2, "effect": 0.4},
        {"base_problem_id": "2", "attention": 0.4, "effect": 0.8},
        {"base_problem_id": "3", "attention": 0.5, "effect": 1.0},
    ]
    aggregated = aggregate_numeric_fields_by_base(rows, fields=["attention", "effect"])
    assert [row["base_problem_id"] for row in aggregated] == ["2", "3"]
    assert [row["target_row_count"] for row in aggregated] == [2, 1]
    np.testing.assert_allclose([row["attention"] for row in aggregated], [0.3, 0.5])
    np.testing.assert_allclose([row["effect"] for row in aggregated], [0.6, 1.0])


def test_flatten_restores_frozen_evidence_type() -> None:
    rows = [
        {
            "base_problem_id": "183",
            "example_id": "914",
            "targets": [{"arm_results": [{"spatial_arm": "target_roi"}]}],
        }
    ]
    flattened = flatten_scoring_results(
        rows,
        evidence_types={"183": "localized_numeric_label"},
    )
    assert flattened == [
        {
            "base_problem_id": "183",
            "example_id": "914",
            "evidence_type": "localized_numeric_label",
            "spatial_arm": "target_roi",
        }
    ]

    try:
        flatten_scoring_results(rows, evidence_types={})
    except ValueError as error:
        assert "base 183" in str(error)
    else:
        raise AssertionError("missing frozen evidence type was accepted")


def test_historical_visual_row_requires_exact_unit_and_heads() -> None:
    result = {
        "cells": [
            {
                "cell_id": "Ed_minus_1__W4",
                "unit_results": [
                    {
                        "unit_id": "Top_2",
                        "source_group": "V",
                        "heads": [16, 0],
                    }
                ],
            }
        ]
    }
    assert select_historical_visual_row(
        result,
        cell_id="Ed_minus_1__W4",
        unit_id="Top_4",
        heads=[16, 0, 3, 6],
    ) is None
    assert select_historical_visual_row(
        result,
        cell_id="Ed_minus_1__W4",
        unit_id="Top_2",
        heads=[16, 0],
    ) == result["cells"][0]["unit_results"][0]


def test_paired_margins_use_absolute_control_effects() -> None:
    target = np.asarray([0.4, 0.2, -0.1])
    sham = np.asarray([0.1, -0.05, 0.2])
    irrelevant = np.asarray([-0.2, 0.1, 0.0])
    sham_margin, irrelevant_margin = paired_margins(target, sham, irrelevant)
    np.testing.assert_allclose(sham_margin, [0.3, 0.15, -0.3])
    np.testing.assert_allclose(irrelevant_margin, [0.2, 0.1, -0.1])


def test_target_gate_requires_every_prospective_semantic_condition() -> None:
    passing = target_validation_gate(
        target_effects=np.asarray([0.4] * 10 + [0.2] * 2),
        sham_effects=np.asarray([0.05] * 12),
        irrelevant_effects=np.asarray([0.04] * 12),
        source_consistent=np.asarray([True] * 10 + [False] * 2),
        bootstrap_iterations=500,
        seed=1234,
    )
    assert passing["semantic_pass"] is True
    assert passing["bidirectional_fraction"] >= 0.75
    assert passing["target_median_ci"][0] > 0
    assert passing["sham_margin_median_ci"][0] > 0
    assert passing["irrelevant_margin_median_ci"][0] > 0

    failing = target_validation_gate(
        target_effects=np.asarray([0.4] * 8 + [-0.1] * 4),
        sham_effects=np.asarray([0.05] * 12),
        irrelevant_effects=np.asarray([0.04] * 12),
        source_consistent=np.asarray([True] * 8 + [False] * 4),
        bootstrap_iterations=500,
        seed=1234,
    )
    assert failing["semantic_pass"] is False
    assert "bidirectional_fraction_at_least_0_75" in failing["failed_conditions"]


def test_disjoint_split_rejects_any_base_overlap() -> None:
    validate_disjoint_split(fresh={1, 2}, primary={3, 4}, historical={5, 6}, diagnostic={7})
    try:
        validate_disjoint_split(fresh={1, 2}, primary={2, 3}, historical={4}, diagnostic=set())
    except ValueError as error:
        assert "primary" in str(error)
    else:
        raise AssertionError("overlapping split was accepted")


def test_primary_roi_gate_and_spatial_categories_use_frozen_thresholds() -> None:
    assert primary_roi_gate(
        target_robust=True,
        target_bidirectional_fraction=0.75,
        sham_margin_ci_low=0.01,
        irrelevant_margin_ci_low=0.02,
        target_greater_irrelevant_fraction=0.75,
        target_prr=0.55,
        ring_prr=0.70,
        mechanical_pass=True,
    )
    assert not primary_roi_gate(
        target_robust=True,
        target_bidirectional_fraction=0.74,
        sham_margin_ci_low=0.01,
        irrelevant_margin_ci_low=0.02,
        target_greater_irrelevant_fraction=0.75,
        target_prr=0.55,
        ring_prr=0.70,
        mechanical_pass=True,
    )
    assert not primary_roi_gate(
        target_robust=True,
        target_bidirectional_fraction=0.80,
        sham_margin_ci_low=0.01,
        irrelevant_margin_ci_low=0.02,
        target_greater_irrelevant_fraction=0.70,
        target_prr=0.55,
        ring_prr=0.70,
        mechanical_pass=True,
    )
    assert spatial_category(
        gate_pass=True,
        target_robust=True,
        all_visual_robust=True,
        target_prr=0.80,
        ring_prr=0.90,
        complement_prr=0.30,
        irrelevant_prr=0.10,
    ) == "ROI-Local"
    assert spatial_category(
        gate_pass=True,
        target_robust=True,
        all_visual_robust=True,
        target_prr=0.30,
        ring_prr=0.80,
        complement_prr=0.40,
        irrelevant_prr=0.10,
    ) == "ROI-Local-Plus-Context"
    assert spatial_category(
        gate_pass=True,
        target_robust=True,
        all_visual_robust=True,
        target_prr=0.20,
        ring_prr=0.40,
        complement_prr=0.70,
        irrelevant_prr=0.10,
    ) == "Visual-Distributed"


if __name__ == "__main__":
    test_secondary_rows_are_aggregated_by_base()
    test_flatten_restores_frozen_evidence_type()
    test_historical_visual_row_requires_exact_unit_and_heads()
    test_paired_margins_use_absolute_control_effects()
    test_target_gate_requires_every_prospective_semantic_condition()
    test_disjoint_split_rejects_any_base_overlap()
    test_primary_roi_gate_and_spatial_categories_use_frozen_thresholds()
    print("Stage 3B.7-R protocol tests passed")
