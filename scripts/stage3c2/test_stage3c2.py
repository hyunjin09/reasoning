#!/usr/bin/env python3
"""Focused unit tests for Stage 3C.2 source accounting and inference helpers."""

from __future__ import annotations

import unittest

from visual_reasoning.stage3c2.metrics import (
    build_exclusive_budget_groups,
    classify_attention_phenotype,
    holm_adjust,
)


class ExclusiveBudgetTest(unittest.TestCase):
    def test_partition_is_disjoint_and_exhaustive(self) -> None:
        groups = build_exclusive_budget_groups(
            current_position=11,
            prompt_length=8,
            visual_positions=[1, 2, 3, 4],
            target_positions=[1],
            mention_positions=[2],
            irrelevant_positions=[3],
            question_positions=[5, 6],
            sink_positions=[0],
        )
        flattened = [value for values in groups.values() for value in values]
        self.assertEqual(sorted(flattened), list(range(12)))
        self.assertEqual(len(flattened), len(set(flattened)))
        self.assertEqual(groups["previous_reasoning"], [8, 9, 10])
        self.assertEqual(groups["other"], [7, 11])

    def test_overlapping_roi_sets_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_exclusive_budget_groups(
                current_position=5,
                prompt_length=5,
                visual_positions=[1, 2, 3],
                target_positions=[1],
                mention_positions=[1, 2],
                irrelevant_positions=[3],
                question_positions=[4],
                sink_positions=[0],
            )


class StatisticsTest(unittest.TestCase):
    def test_holm_adjust_is_monotone_in_sorted_order(self) -> None:
        adjusted = holm_adjust([0.01, 0.04, 0.03])
        self.assertEqual(adjusted, [0.03, 0.06, 0.06])

    def test_temporal_phenotypes(self) -> None:
        self.assertEqual(classify_attention_phenotype(-0.2, 0.3), "alignment_then_retrieval")
        self.assertEqual(classify_attention_phenotype(0.1, 0.2), "retrieval_only")
        self.assertEqual(classify_attention_phenotype(-0.1, -0.2), "alignment_only")
        self.assertEqual(classify_attention_phenotype(0.0, 0.0), "overlap_or_tie")


if __name__ == "__main__":
    unittest.main()
