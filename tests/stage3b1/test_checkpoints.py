from __future__ import annotations

import unittest

from visual_reasoning.stage3b1.checkpoints import build_checkpoint_schedule


class CheckpointScheduleTests(unittest.TestCase):
    def test_short_prefix_deduplicates_relative_and_progress_labels(self) -> None:
        schedule = build_checkpoint_schedule(e0_start_token=6)

        self.assertEqual([row["cutoff_generated_index"] for row in schedule], [0, 1, 2, 3, 4, 5])
        by_index = {row["cutoff_generated_index"]: row for row in schedule}
        self.assertEqual(by_index[0]["labels"], ["progress_0"])
        self.assertEqual(by_index[2]["labels"], ["E0_minus_4"])
        self.assertEqual(by_index[5]["labels"], ["E0_minus_1", "progress_90"])
        self.assertTrue(all(0 <= row["cutoff_generated_index"] < 6 for row in schedule))

    def test_generation_start_deduplicates_with_e0_minus_128(self) -> None:
        schedule = build_checkpoint_schedule(e0_start_token=128)
        first = schedule[0]

        self.assertEqual(first["cutoff_generated_index"], 0)
        self.assertEqual(first["labels"], ["E0_minus_128", "progress_0"])
        self.assertEqual(first["tokens_before_e0"], 128)
        self.assertEqual(first["actual_progress"], 0.0)


if __name__ == "__main__":
    unittest.main()
