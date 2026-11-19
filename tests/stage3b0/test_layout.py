from __future__ import annotations

import unittest

from visual_reasoning.stage3b0.layout import build_token_groups, find_unique_subsequence


class TokenLayoutTests(unittest.TestCase):
    def test_unique_question_span_and_post_image_groups(self) -> None:
        prompt = [10, 11, 99, 99, 12, 20, 21, 22, 30, 31]
        groups = build_token_groups(
            prompt_token_ids=prompt,
            visual_token_indices=[2, 3],
            question_token_ids=[20, 21, 22],
        )

        self.assertEqual(groups["V"], [2, 3])
        self.assertEqual(groups["Q"], [5, 6, 7])
        self.assertEqual(groups["T"], [8, 9])
        self.assertEqual(groups["Q_plus_T"], [5, 6, 7, 8, 9])
        self.assertEqual(groups["P_post_image"], [4, 5, 6, 7, 8, 9])

    def test_question_must_be_a_unique_post_image_subsequence(self) -> None:
        with self.assertRaisesRegex(ValueError, "unique"):
            find_unique_subsequence([1, 2, 3, 2, 3], [2, 3])
        with self.assertRaisesRegex(ValueError, "after the final visual"):
            build_token_groups(
                prompt_token_ids=[1, 7, 8, 2, 3],
                visual_token_indices=[3],
                question_token_ids=[7, 8],
            )


if __name__ == "__main__":
    unittest.main()
