"""Independent CPU-only regressions for physical receipt-map merging.

Paths are synthetic strings. These tests never open generation files or inspect
scientific answers; archived paths are exclusion evidence, not reusable output.
"""

from copy import deepcopy
import unittest

from scripts.stage14d1_pilot.merge_v8 import merge_physical


class MergePhysicalTests(unittest.TestCase):
    def setUp(self):
        self.design = {
            "completed_reuse": {
                "complete_N": "synthetic/complete/complete_N/generation.json",
                "complete_G": "synthetic/complete/complete_G/generation.json",
            },
            "archived_partial_family_outputs": {
                "partial_QI": "synthetic/archived/partial_QI/generation.json",
                "partial_QIA": "synthetic/archived/partial_QIA/generation.json",
            },
            "attempts": ["attempt_a", "attempt_b"],
            "physical_new": 3,
        }
        self.results = {
            "attempt_a": {
                "partial_QI": "synthetic/fresh_a/partial_QI/generation.json",
                "missing_N": "synthetic/fresh_a/missing_N/generation.json",
            },
            "attempt_b": {
                "missing_G": "synthetic/fresh_b/missing_G/generation.json",
            },
        }

    def assert_rejected(self):
        design_before, results_before = deepcopy(self.design), deepcopy(self.results)
        with self.assertRaises(ValueError):
            merge_physical(self.design, self.results)
        self.assertEqual(self.design, design_before)
        self.assertEqual(self.results, results_before)

    def test_combines_completed_and_new_physical_results_without_mutation(self):
        design_before, results_before = deepcopy(self.design), deepcopy(self.results)
        expected = {
            **self.design["completed_reuse"],
            **self.results["attempt_a"],
            **self.results["attempt_b"],
        }
        merged = merge_physical(self.design, self.results)
        self.assertEqual(merged, expected)
        self.assertEqual(len(merged), 5)
        self.assertEqual(self.design, design_before)
        self.assertEqual(self.results, results_before)
        self.assertIsNot(merged, self.design["completed_reuse"])
        self.assertIsNot(merged, self.results["attempt_a"])

    def test_fresh_rerun_may_share_archived_request_id_with_different_path(self):
        archived_path = self.design["archived_partial_family_outputs"]["partial_QI"]
        fresh_path = self.results["attempt_a"]["partial_QI"]
        merged = merge_physical(self.design, self.results)
        self.assertEqual(merged["partial_QI"], fresh_path)
        self.assertNotEqual(merged["partial_QI"], archived_path)
        self.assertNotIn("partial_QIA", merged)

    def test_archived_outputs_are_never_automatically_added(self):
        self.design.update(completed_reuse={}, attempts=[], physical_new=0)
        self.assertEqual(merge_physical(self.design, {}), {})

    def test_no_new_attempts_returns_only_completed_reuse(self):
        self.design.update(attempts=[], physical_new=0)
        self.assertEqual(merge_physical(self.design, {}), self.design["completed_reuse"])

    def test_declared_empty_attempt_is_allowed_when_no_new_results_expected(self):
        self.design.update(attempts=["empty_attempt"], physical_new=0)
        self.assertEqual(
            merge_physical(self.design, {"empty_attempt": {}}),
            self.design["completed_reuse"],
        )

    def test_missing_attempt_is_rejected_even_if_count_is_adjusted(self):
        del self.results["attempt_b"]
        self.design["physical_new"] = 2
        self.assert_rejected()

    def test_extra_attempt_is_rejected_even_when_empty(self):
        self.results["unexpected_attempt"] = {}
        self.assert_rejected()

    def test_duplicate_attempt_names_are_rejected(self):
        self.design["attempts"].append("attempt_a")
        self.assert_rejected()

    def test_overlap_with_completed_reuse_is_rejected_even_for_identical_path(self):
        for path in (
            self.design["completed_reuse"]["complete_N"],
            "synthetic/fresh_a/complete_N/generation.json",
        ):
            with self.subTest(path=path):
                self.results["attempt_a"]["complete_N"] = path
                self.design["physical_new"] = 4
                self.assert_rejected()

    def test_duplicate_request_ids_across_attempts_are_rejected(self):
        for path in (
            self.results["attempt_a"]["missing_N"],
            "synthetic/fresh_b/missing_N/generation.json",
        ):
            with self.subTest(path=path):
                self.results["attempt_b"]["missing_N"] = path
                self.design["physical_new"] = 4
                self.assert_rejected()

    def test_physical_new_counts_new_results_not_combined_or_archived_outputs(self):
        for expected_count in (0, 2, 4, 5, 7):
            with self.subTest(expected_count=expected_count):
                self.design["physical_new"] = expected_count
                self.assert_rejected()

    def test_physical_new_requires_a_nonnegative_integer(self):
        for invalid_count in (-1, True, 3.0, "3", None):
            with self.subTest(invalid_count=invalid_count):
                self.design["physical_new"] = invalid_count
                self.assert_rejected()

    def test_archived_path_cannot_be_reused_under_its_original_request_id(self):
        self.results["attempt_a"]["partial_QI"] = (
            self.design["archived_partial_family_outputs"]["partial_QI"]
        )
        self.assert_rejected()

    def test_archived_path_cannot_be_smuggled_under_a_different_request_id(self):
        self.results["attempt_a"]["missing_N"] = (
            self.design["archived_partial_family_outputs"]["partial_QIA"]
        )
        self.assert_rejected()

    def test_archived_path_cannot_enter_through_completed_reuse(self):
        self.design["completed_reuse"]["complete_N"] = (
            self.design["archived_partial_family_outputs"]["partial_QI"]
        )
        self.assert_rejected()

    def test_result_dictionary_order_does_not_change_the_merge(self):
        expected = merge_physical(self.design, self.results)
        reversed_results = dict(reversed(list(self.results.items())))
        self.assertEqual(merge_physical(self.design, reversed_results), expected)


if __name__ == "__main__":
    unittest.main()
