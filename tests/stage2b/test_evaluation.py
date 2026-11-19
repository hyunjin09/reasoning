from __future__ import annotations

import unittest

import torch

from visual_reasoning.stage2b.evaluation import classify_local_effects, first_semantic_divergence, first_token_divergence
from visual_reasoning.stage2b.runtime import extend_prepared_inputs


class EvaluationTests(unittest.TestCase):
    def test_classifies_strong_crossover(self) -> None:
        result = classify_local_effects(
            {
                "A": {"A_roi": 0.30, "B_roi": 0.02, "irrelevant_roi": 0.01},
                "B": {"A_roi": 0.01, "B_roi": 0.25, "irrelevant_roi": 0.00},
            }
        )
        self.assertEqual(result["category"], "P1")
        self.assertTrue(result["A_window_specific"])
        self.assertTrue(result["B_window_specific"])

    def test_classifies_no_detectable_effect(self) -> None:
        result = classify_local_effects(
            {
                "A": {"A_roi": 0.01, "B_roi": -0.01, "irrelevant_roi": 0.00},
                "B": {"A_roi": 0.02, "B_roi": 0.01, "irrelevant_roi": -0.02},
            }
        )
        self.assertEqual(result["category"], "P5")

    def test_reports_first_token_divergence(self) -> None:
        self.assertEqual(first_token_divergence([1, 2, 3], [1, 4, 3]), 1)
        self.assertEqual(first_token_divergence([1, 2], [1, 2, 3]), 2)
        self.assertIsNone(first_token_divergence([1, 2], [1, 2]))

    def test_reports_first_sentence_level_semantic_divergence(self) -> None:
        divergence = first_semantic_divergence(
            "First we read A. Then compute five. Final answer A.",
            "First we read A. Then compute nine. Final answer B.",
        )
        self.assertEqual(divergence["segment_index"], 1)
        self.assertEqual(divergence["baseline_segment"], "Then compute five.")
        self.assertEqual(divergence["condition_segment"], "Then compute nine.")

    def test_extends_only_sequence_aligned_input_tensors(self) -> None:
        prepared = {
            "input_ids": torch.tensor([[10, 11, 12]]),
            "attention_mask": torch.ones((1, 3), dtype=torch.long),
            "mm_token_type_ids": torch.tensor([[1, 0, 0]]),
            "pixel_values": torch.ones((4, 8)),
            "image_grid_thw": torch.tensor([[1, 2, 2]]),
        }
        extended = extend_prepared_inputs(prepared, [20, 21])
        self.assertEqual(extended["input_ids"].tolist(), [[10, 11, 12, 20, 21]])
        self.assertEqual(extended["attention_mask"].tolist(), [[1, 1, 1, 1, 1]])
        self.assertEqual(extended["mm_token_type_ids"].tolist(), [[1, 0, 0, 0, 0]])
        self.assertEqual(tuple(extended["pixel_values"].shape), (4, 8))
        self.assertEqual(tuple(extended["image_grid_thw"].shape), (1, 3))


if __name__ == "__main__":
    unittest.main()
