from __future__ import annotations

import unittest

import torch

from visual_reasoning.stage3b0.intervention import apply_generation_start_visual_cutoff


class GenerationStartCutoffTests(unittest.TestCase):
    def test_full_sequence_masks_only_generated_queries_to_visual_keys(self) -> None:
        original = torch.zeros((1, 1, 9, 9), dtype=torch.float32)
        masked, audit = apply_generation_start_visual_cutoff(
            original,
            prompt_length=5,
            visual_key_indices=[1, 2],
            query_length=9,
            key_length=9,
        )

        changed = torch.nonzero(masked != original, as_tuple=False).tolist()
        self.assertEqual(
            changed,
            [[0, 0, row, key] for row in range(5, 9) for key in (1, 2)],
        )
        self.assertEqual(audit["absolute_query_indices"], [5, 6, 7, 8])
        self.assertFalse(audit["prefill_modified"])

    def test_cached_suffix_masks_every_suffix_query(self) -> None:
        original = torch.zeros((1, 1, 3, 8), dtype=torch.bfloat16)
        masked, audit = apply_generation_start_visual_cutoff(
            original,
            prompt_length=5,
            visual_key_indices=[1, 2],
            query_length=3,
            key_length=8,
        )

        self.assertEqual(audit["absolute_query_indices"], [5, 6, 7])
        self.assertEqual(torch.nonzero(masked != original).shape[0], 6)


if __name__ == "__main__":
    unittest.main()
