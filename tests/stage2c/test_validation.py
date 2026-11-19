from __future__ import annotations

import unittest

from visual_reasoning.stage2c.validation import validate_event_annotation


class AnnotationValidationTests(unittest.TestCase):
    def test_complete_annotation_passes(self) -> None:
        row = {
            "example_id": "x",
            "evidence_id": "x:A",
            "e0": {"start_token": 10, "end_token": 11},
            "e1": {"fact_start_token": 10, "completion_token": 13},
            "e2": {"start_token": 20, "end_token": 24},
            "repeated_mentions": [{"start_token": 30, "end_token": 31}],
        }
        self.assertEqual(validate_event_annotation(row, token_count=40), [])

    def test_temporally_inconsistent_annotation_fails(self) -> None:
        row = {
            "example_id": "x",
            "evidence_id": "x:A",
            "e0": {"start_token": 10, "end_token": 11},
            "e1": {"fact_start_token": 10, "completion_token": 9},
            "e2": {"start_token": 8, "end_token": 12},
            "repeated_mentions": [],
        }
        failures = validate_event_annotation(row, token_count=40)
        self.assertTrue(any("E1" in failure for failure in failures))
        self.assertTrue(any("E2" in failure for failure in failures))


if __name__ == "__main__":
    unittest.main()
