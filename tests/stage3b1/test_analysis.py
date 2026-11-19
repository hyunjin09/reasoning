from __future__ import annotations

import unittest

from visual_reasoning.stage3b1.analysis import (
    classify_timing_pattern,
    monotonicity_audit,
    schedule_matches_curve,
    select_frozen_attention_event,
    threshold_times,
)


class TimingAnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.curve = [
            {"cutoff_generated_index": 0, "actual_progress": 0.0, "retention_ratio_raw": 0.1},
            {"cutoff_generated_index": 25, "actual_progress": 0.25, "retention_ratio_raw": 0.6},
            {"cutoff_generated_index": 50, "actual_progress": 0.5, "retention_ratio_raw": 0.85},
            {"cutoff_generated_index": 75, "actual_progress": 0.75, "retention_ratio_raw": 0.75},
            {"cutoff_generated_index": 90, "actual_progress": 0.9, "retention_ratio_raw": 0.95},
        ]

    def test_reports_first_and_stable_threshold_crossings(self) -> None:
        result = threshold_times(self.curve, e0_start_token=100)

        self.assertEqual(result["rho_50"]["first"]["cutoff_generated_index"], 25)
        self.assertEqual(result["rho_50"]["stable"]["cutoff_generated_index"], 25)
        self.assertEqual(result["rho_80"]["first"]["cutoff_generated_index"], 50)
        self.assertEqual(result["rho_80"]["stable"]["cutoff_generated_index"], 90)
        self.assertEqual(result["rho_90"]["first"]["tokens_before_e0"], 10)

    def test_monotonicity_preserves_raw_decrease(self) -> None:
        result = monotonicity_audit(self.curve, control_noise_tolerance=1e-6)

        self.assertEqual(result["local_decrease_count"], 1)
        self.assertAlmostEqual(result["maximum_downward_step"], 0.1)
        self.assertFalse(result["monotonic_raw"])
        self.assertTrue(result["deviation_exceeds_control_noise"])

    def test_complex_curve_is_not_forced_into_handoff_category(self) -> None:
        thresholds = threshold_times(self.curve, e0_start_token=100)
        monotonicity = monotonicity_audit(self.curve, control_noise_tolerance=1e-6)

        self.assertEqual(
            classify_timing_pattern(self.curve, thresholds=thresholds, monotonicity=monotonicity),
            "S3_gradual_accumulation",
        )
        more_irregular = [dict(row) for row in self.curve]
        more_irregular[3]["retention_ratio_raw"] = 0.4
        irregular_audit = monotonicity_audit(more_irregular, control_noise_tolerance=1e-6)
        self.assertEqual(
            classify_timing_pattern(
                more_irregular,
                thresholds=threshold_times(more_irregular, e0_start_token=100),
                monotonicity=irregular_audit,
            ),
            "S6_non_monotonic_complex",
        )

    def test_aggregation_requires_exact_frozen_checkpoint_schedule(self) -> None:
        schedule = [
            {
                "cutoff_generated_index": 0,
                "labels": ["progress_0"],
                "requested_coordinates": [{"coordinate": "normalized_progress", "requested_progress": 0.0}],
                "tokens_before_e0": 10,
                "actual_progress": 0.0,
                "strictly_pre_e0": True,
            }
        ]
        observed = [{**schedule[0], "retention_ratio_raw": 0.2}]

        self.assertTrue(schedule_matches_curve(schedule, observed))
        observed[0]["labels"] = ["wrong"]
        self.assertFalse(schedule_matches_curve(schedule, observed))

    def test_duplicate_e0_events_follow_frozen_stage3a_density_match(self) -> None:
        candidates = [
            {"evidence_id": "x:A", "prediction_aligned_region_means": {"roi_per_token_density": {"PRE": 0.1}}},
            {"evidence_id": "x:B", "prediction_aligned_region_means": {"roi_per_token_density": {"PRE": 0.2}}},
        ]

        selected = select_frozen_attention_event(candidates, frozen_pre_e0_density=0.2)

        self.assertEqual(selected["evidence_id"], "x:B")


if __name__ == "__main__":
    unittest.main()
