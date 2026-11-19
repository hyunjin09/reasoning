from __future__ import annotations

import unittest

import numpy as np

from visual_reasoning.stage2c.temporal import (
    attention_row_convention,
    classify_window_relation,
    classify_timing,
    event_regions,
    find_token_interval,
    region_means,
)


class AttentionConventionTests(unittest.TestCase):
    def test_rows_are_aligned_to_the_token_their_logits_predict(self) -> None:
        rows = attention_row_convention(
            query_lengths=np.asarray([5, 1, 1]),
            key_lengths=np.asarray([5, 6, 7]),
            prompt_length=5,
            generated_token_ids=[101, 102, 103],
        )
        self.assertEqual(rows[0]["query_source"], "final_prompt_token")
        self.assertIsNone(rows[0]["query_generated_token_index"])
        self.assertEqual(rows[0]["predicted_generated_token_index"], 0)
        self.assertEqual(rows[1]["query_generated_token_index"], 0)
        self.assertEqual(rows[1]["predicted_generated_token_index"], 1)
        self.assertEqual(rows[1]["predicted_token_id"], 102)

    def test_invalid_key_progression_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "key lengths"):
            attention_row_convention(
                query_lengths=np.asarray([5, 1]),
                key_lengths=np.asarray([5, 7]),
                prompt_length=5,
                generated_token_ids=[101, 102],
            )


class EventTests(unittest.TestCase):
    def test_regex_character_match_maps_to_exact_token_interval(self) -> None:
        pieces = ["AB", " is", " 3", ".", " Therefore", " AB", " squared", " is", " 9", "."]
        entity = find_token_interval(pieces, r"\bAB\b", occurrence=0)
        fact = find_token_interval(pieces, r"\bAB\s+is\s+3\b", occurrence=0)
        repeat = find_token_interval(pieces, r"\bAB\b", occurrence=1)
        self.assertEqual(entity, (0, 1))
        self.assertEqual(fact, (0, 3))
        self.assertEqual(repeat, (5, 6))

    def test_regions_are_fixed_and_nonoverlapping(self) -> None:
        regions = event_regions(
            token_count=200,
            e0_interval=(80, 82),
            e1_token=85,
            e2_interval=(120, 130),
            window=64,
        )
        self.assertEqual(regions["PRE"], (16, 80))
        self.assertEqual(regions["ENTITY"], (80, 82))
        self.assertEqual(regions["FACT"], (82, 86))
        self.assertEqual(regions["POST"], (86, 120))
        self.assertEqual(regions["USE"], (120, 130))

    def test_fact_region_can_begin_at_annotated_fact_start(self) -> None:
        regions = event_regions(
            token_count=200,
            e0_interval=(80, 90),
            e1_token=95,
            e2_interval=(120, 130),
            window=64,
            fact_start=82,
        )
        self.assertEqual(regions["ENTITY"], (80, 90))
        self.assertEqual(regions["FACT"], (82, 96))

    def test_region_means_use_one_value_per_region(self) -> None:
        values = np.arange(20, dtype=float)
        means = region_means(values, {"PRE": (0, 4), "ENTITY": (4, 6), "FACT": (6, 8)})
        self.assertAlmostEqual(means["PRE"], 1.5)
        self.assertAlmostEqual(means["ENTITY"], 4.5)
        self.assertAlmostEqual(means["FACT"], 6.5)


class TimingCategoryTests(unittest.TestCase):
    def test_pre_mention_lead(self) -> None:
        self.assertEqual(
            classify_timing(
                {"PRE": 3.0, "ENTITY": 1.0, "FACT": 1.0, "POST": 0.8, "USE": 0.7},
                repeated_mean=None,
                matched_mean=None,
            ),
            "T1_pre_mention_lead",
        )

    def test_repeated_mention_locked_has_priority(self) -> None:
        self.assertEqual(
            classify_timing(
                {"PRE": 0.5, "ENTITY": 2.0, "FACT": 2.2, "POST": 0.8, "USE": 0.7},
                repeated_mean=2.5,
                matched_mean=0.7,
            ),
            "T4_repeated_mention_locked",
        )

    def test_broadly_similar_regions_are_persistent(self) -> None:
        self.assertEqual(
            classify_timing(
                {"PRE": 1.0, "ENTITY": 1.2, "FACT": 1.1, "POST": 0.9, "USE": 1.0},
                repeated_mean=None,
                matched_mean=None,
            ),
            "T5_persistent",
        )


class InterventionWindowTests(unittest.TestCase):
    def test_window_relations_follow_evidence_event_order(self) -> None:
        event = {
            "e0": {"start_token": 10, "end_token": 12},
            "e1": {"completion_token": 15},
            "e2": {"start_token": 30, "end_token": 35},
        }
        self.assertEqual(classify_window_relation((2, 8), event), "PRE-E0")
        self.assertEqual(classify_window_relation((10, 16), event), "E0-to-E1")
        self.assertEqual(classify_window_relation((16, 25), event), "POST-E1 before use")
        self.assertEqual(classify_window_relation((30, 32), event), "USE")
        self.assertEqual(classify_window_relation((40, 45), event), "late POST")

    def test_spanning_window_reports_all_overlapped_event_regions(self) -> None:
        event = {
            "e0": {"start_token": 10, "end_token": 12},
            "e1": {"completion_token": 15},
            "e2": {"start_token": 30, "end_token": 35},
        }
        relation = classify_window_relation((8, 32), event)
        self.assertEqual(relation, "spans PRE-E0 + E0-to-E1 + POST-E1 before use + USE")

if __name__ == "__main__":
    unittest.main()
