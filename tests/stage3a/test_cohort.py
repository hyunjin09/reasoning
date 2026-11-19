import unittest

from visual_reasoning.stage3a.cohort import merge_expansion_outcomes, validate_strict_pre_e0_audit


class CohortTest(unittest.TestCase):
    def test_merge_expansion_outcomes_preserves_frozen_order_and_all_statuses(self) -> None:
        frozen = [{"example_id": "4", "base_problem_id": "1"}, {"example_id": "9", "base_problem_id": "2"}]
        shard_rows = [
            {"example_id": "9", "base_problem_id": "2", "status": "wrong"},
            {"example_id": "4", "base_problem_id": "1", "status": "correct"},
        ]
        merged = merge_expansion_outcomes(frozen, shard_rows)
        self.assertEqual([row["example_id"] for row in merged], ["4", "9"])
        self.assertEqual([row["status"] for row in merged], ["correct", "wrong"])

    def test_merge_expansion_outcomes_rejects_missing_or_duplicate_results(self) -> None:
        frozen = [{"example_id": "4", "base_problem_id": "1"}]
        with self.assertRaisesRegex(ValueError, "missing"):
            merge_expansion_outcomes(frozen, [])
        duplicate = [
            {"example_id": "4", "base_problem_id": "1", "status": "correct"},
            {"example_id": "4", "base_problem_id": "1", "status": "correct"},
        ]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            merge_expansion_outcomes(frozen, duplicate)

    def test_merge_expansion_outcomes_rejects_base_mismatch(self) -> None:
        frozen = [{"example_id": "4", "base_problem_id": "1"}]
        with self.assertRaisesRegex(ValueError, "base_problem_id"):
            merge_expansion_outcomes(
                frozen,
                [{"example_id": "4", "base_problem_id": "99", "status": "correct"}],
            )

    def test_strict_pre_e0_audit_requires_exact_neutral_prefix(self) -> None:
        generated = [10, 20, 30, 40]
        row = validate_strict_pre_e0_audit(
            generated_token_ids=generated,
            e0_start_token=2,
            e1_completion_token=3,
            evidence_neutral=True,
        )
        self.assertEqual(row["prefix_token_ids"], [10, 20])
        self.assertEqual(
            row["prefix_sha256"],
            "28c5e638bdf2b3cd7335d680a7f32d01211825619b54c746897d4842c46b5878",
        )

    def test_strict_pre_e0_audit_rejects_bad_boundaries_or_leakage(self) -> None:
        with self.assertRaisesRegex(ValueError, "strictly evidence-neutral"):
            validate_strict_pre_e0_audit(
                generated_token_ids=[10, 20],
                e0_start_token=1,
                e1_completion_token=1,
                evidence_neutral=False,
            )
        with self.assertRaisesRegex(ValueError, "E1"):
            validate_strict_pre_e0_audit(
                generated_token_ids=[10, 20],
                e0_start_token=1,
                e1_completion_token=0,
                evidence_neutral=True,
            )


if __name__ == "__main__":
    unittest.main()
