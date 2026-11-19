from __future__ import annotations

import unittest

from visual_reasoning.stage3b0.metrics import directional_recovery, retention_ratio


class Stage3B0MetricTests(unittest.TestCase):
    def test_metrics_are_raw_and_unclipped(self) -> None:
        self.assertEqual(retention_ratio(ce_cut=3.0, ce_full=2.0), 1.5)
        self.assertEqual(
            directional_recovery(recipient_preference=-2.0, source_preference=2.0, patched_preference=3.0),
            1.25,
        )

    def test_zero_denominator_is_explicitly_undefined(self) -> None:
        self.assertIsNone(retention_ratio(ce_cut=1.0, ce_full=0.0))
        self.assertIsNone(
            directional_recovery(recipient_preference=1.0, source_preference=1.0, patched_preference=2.0)
        )


if __name__ == "__main__":
    unittest.main()
