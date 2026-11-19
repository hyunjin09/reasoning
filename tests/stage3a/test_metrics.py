import unittest

import numpy as np

from visual_reasoning.stage3a.metrics import (
    bootstrap_interval,
    counterfactual_effect,
    js_divergence_from_logits,
    pre_e0_checkpoints,
    summarize_effect_values,
)


class MetricsTest(unittest.TestCase):
    def test_counterfactual_effect_and_sham_control(self) -> None:
        result = counterfactual_effect(
            original={"L_o": -0.2, "L_c": -1.2},
            counterfactual={"L_o": -1.1, "L_c": -0.3},
            sham={"L_o": -0.3, "L_c": -1.2},
        )
        self.assertEqual(result["D_original"], 1.0)
        self.assertTrue(np.isclose(result["D_counterfactual"], -0.8))
        self.assertTrue(np.isclose(result["CE"], 1.8))
        self.assertTrue(np.isclose(result["sham_shift"], 0.1))
        self.assertTrue(np.isclose(result["CE_controlled"], 1.7))

    def test_js_divergence_is_symmetric_zero_for_identical_logits(self) -> None:
        left = np.asarray([1.0, 2.0, -1.0])
        right = np.asarray([-0.5, 0.0, 1.5])
        self.assertEqual(js_divergence_from_logits(left, left), 0.0)
        self.assertTrue(
            np.isclose(
                js_divergence_from_logits(left, right),
                js_divergence_from_logits(right, left),
            )
        )

    def test_pre_e0_checkpoints_are_unique_sorted_and_strictly_pre_event(self) -> None:
        self.assertEqual(pre_e0_checkpoints(100), [0, 36, 68, 84, 92, 100])
        self.assertEqual(pre_e0_checkpoints(10), [0, 2, 10])
        self.assertTrue(all(value <= 100 for value in pre_e0_checkpoints(100)))

    def test_bootstrap_interval_is_deterministic_and_contains_point_estimate(self) -> None:
        values = [1.0, 2.0, 3.0, 4.0]
        first = bootstrap_interval(values, statistic="mean", seed=17, resamples=2_000)
        second = bootstrap_interval(values, statistic="mean", seed=17, resamples=2_000)
        self.assertEqual(first, second)
        self.assertEqual(first["estimate"], 2.5)
        self.assertLessEqual(first["ci_low"], first["estimate"])
        self.assertGreaterEqual(first["ci_high"], first["estimate"])

    def test_effect_summary_uses_independent_problem_values(self) -> None:
        summary = summarize_effect_values([2.0, -1.0, 3.0, 0.0], seed=7, resamples=1_000)
        self.assertEqual(summary["n"], 4)
        self.assertEqual(summary["expected_direction_count"], 2)
        self.assertEqual(summary["expected_direction_proportion"], 0.5)
        self.assertEqual(summary["mean"], 1.0)
        self.assertEqual(summary["median"], 1.0)


if __name__ == "__main__":
    unittest.main()
