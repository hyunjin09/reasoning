import unittest

import numpy as np

from visual_reasoning.stage3a.runtime import candidate_logit_rows, summarize_candidate_log_probs


class RuntimeIndexingTest(unittest.TestCase):
    def test_candidate_rows_begin_at_last_context_position(self) -> None:
        self.assertEqual(candidate_logit_rows(prompt_length=100, prefix_length=12, candidate_length=3), [111, 112, 113])

    def test_candidate_log_probs_are_per_token_normalized(self) -> None:
        result = summarize_candidate_log_probs([-0.2, -0.4, -0.6])
        self.assertEqual(result["token_count"], 3)
        self.assertTrue(np.isclose(result["sum_log_probability"], -1.2))
        self.assertTrue(np.isclose(result["mean_log_probability"], -0.4))


if __name__ == "__main__":
    unittest.main()

