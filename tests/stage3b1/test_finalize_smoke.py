from __future__ import annotations

import unittest

from scripts.stage3b1.finalize_smoke import validate_schedule_deduplication


class SmokeDeduplicationTests(unittest.TestCase):
    def test_collision_is_required_across_smoke_not_in_every_base(self) -> None:
        smoke = [
            {"base_problem_id": "short", "checkpoint_count": 3, "duplicate_label_count": 1},
            {"base_problem_id": "long", "checkpoint_count": 4, "duplicate_label_count": 0},
        ]
        schedules = {
            "short": {"checkpoints": [{"labels": ["a"]}, {"labels": ["b", "c"]}, {"labels": ["d"]}]},
            "long": {"checkpoints": [{"labels": ["a"]}, {"labels": ["b"]}, {"labels": ["c"]}, {"labels": ["d"]}]},
        }

        self.assertTrue(validate_schedule_deduplication(smoke, schedules))

    def test_observed_counts_must_match_frozen_schedule(self) -> None:
        smoke = [{"base_problem_id": "x", "checkpoint_count": 2, "duplicate_label_count": 1}]
        schedules = {"x": {"checkpoints": [{"labels": ["a"]}, {"labels": ["b"]}]}}

        self.assertFalse(validate_schedule_deduplication(smoke, schedules))


if __name__ == "__main__":
    unittest.main()
