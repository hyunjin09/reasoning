#!/usr/bin/env python3
"""CPU-only unit tests for Stage 2A analysis helpers."""

from __future__ import annotations

import unittest

import numpy as np

from visual_reasoning.stage2a.analysis import (
    holm_adjust,
    normalized_token_bins,
    paired_effect,
    progress_window_mean,
    token_weighted_semantic_means,
)
from visual_reasoning.stage2a.roi import classify_shift, map_boxes_to_visual_tokens, roi_curves


class Stage2AAnalysisTests(unittest.TestCase):
    def test_normalized_bins_preserve_linear_blocks(self) -> None:
        values = np.arange(40, dtype=np.float64).reshape(20, 2)
        result = normalized_token_bins(values, 4)
        np.testing.assert_allclose(result, np.stack([values[i : i + 5].mean(0) for i in range(0, 20, 5)]))

    def test_progress_windows(self) -> None:
        values = np.arange(8, dtype=np.float64)
        self.assertEqual(float(progress_window_mean(values, 0.0, 0.25)), 0.5)
        self.assertEqual(float(progress_window_mean(values, 0.25, 0.75)), 3.5)
        self.assertEqual(float(progress_window_mean(values, 0.75, 1.0)), 6.5)

    def test_paired_effect_uses_vd_minus_vi(self) -> None:
        result = paired_effect([1.0, 2.0, 3.0], [2.0, 4.0, 6.0])
        self.assertEqual(result["difference_definition"], "Vision Dominant minus Vision Intensive")
        self.assertAlmostEqual(result["paired_mean_difference"], 2.0)
        self.assertEqual(result["differences"], [1.0, 2.0, 3.0])
        self.assertGreater(result["matched_rank_biserial"], 0)
        self.assertEqual(len(result["paired_difference_bootstrap_median_95ci"]), 2)

    def test_identical_pairs_are_valid_null(self) -> None:
        result = paired_effect([1.0, 2.0], [1.0, 2.0])
        self.assertEqual(result["wilcoxon_p_value"], 1.0)
        self.assertEqual(result["zero_difference_pairs"], 2)

    def test_holm_is_monotone_in_sorted_order(self) -> None:
        result = holm_adjust({"a": 0.01, "b": 0.04, "c": 0.03})
        self.assertAlmostEqual(result["a"], 0.03)
        self.assertAlmostEqual(result["c"], 0.06)
        self.assertAlmostEqual(result["b"], 0.06)

    def test_semantic_means_use_tokens_not_span_count(self) -> None:
        spans = [
            {"start_token": 0, "end_token": 3, "semantic_label": "A"},
            {"start_token": 3, "end_token": 4, "semantic_label": "A"},
            {"start_token": 4, "end_token": 6, "semantic_label": "B"},
        ]
        values = np.arange(6, dtype=np.float64)
        result = token_weighted_semantic_means(spans, values)
        self.assertAlmostEqual(float(result["A"]), 1.5)
        self.assertAlmostEqual(float(result["B"]), 4.5)

    def test_roi_mapping_is_row_major_and_center_based(self) -> None:
        # A 100x100 image with a 2x2 merged grid has centers at 25 and 75.
        self.assertEqual(map_boxes_to_visual_tokens([[0, 0, 50, 50]], [100, 100], [1, 2, 2]), [0])
        self.assertEqual(map_boxes_to_visual_tokens([[50, 50, 100, 100]], [100, 100], [1, 2, 2]), [3])

    def test_roi_curve_retains_raw_mass_and_conditional_share(self) -> None:
        focus = np.asarray([[0.1, 0.2, 0.3], [0.2, 0.2, 0.0]])
        result = roi_curves(focus, [0, 1])
        np.testing.assert_allclose(result["raw_mass"], [0.3, 0.4])
        np.testing.assert_allclose(result["density"], [0.15, 0.2])
        np.testing.assert_allclose(result["conditional_share"], [0.5, 1.0])

    def test_shift_classification_uses_roi_size_normalized_density(self) -> None:
        self.assertEqual(classify_shift(0.8, 0.2, 0.2, 0.8), "expected_A_to_B_shift")
        self.assertEqual(classify_shift(0.8, 0.2, 0.7, 0.3), "persistent_A")


if __name__ == "__main__":
    unittest.main()
