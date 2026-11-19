from __future__ import annotations

import unittest

import torch

from visual_reasoning.stage3b0.runtime import suffix_position_ids


class CachedPositionTests(unittest.TestCase):
    def test_text_axis_is_absolute_and_visual_axes_include_rope_delta(self) -> None:
        positions = suffix_position_ids(
            prompt_length=10,
            suffix_length=3,
            rope_deltas=torch.tensor([[-4]]),
            device=torch.device("cpu"),
        )
        self.assertEqual(list(positions.shape), [4, 1, 3])
        self.assertEqual(positions[0, 0].tolist(), [10, 11, 12])
        for axis in (1, 2, 3):
            self.assertEqual(positions[axis, 0].tolist(), [6, 7, 8])


if __name__ == "__main__":
    unittest.main()
