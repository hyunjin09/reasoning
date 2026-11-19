#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "code"))

from piqd.data.mathverse_loader import load_smoke_samples
from piqd.fastv.fastv_adapter import (
    find_local_minima,
    retained_count,
    select_active_shift_event,
    select_top_visual_indices,
)


class FastVLogicTest(unittest.TestCase):
    def test_retained_count_uses_fastv_rounding_with_minimum_one(self) -> None:
        self.assertEqual(retained_count(729, 0.333), 243)
        self.assertEqual(retained_count(1, 0.333), 1)
        self.assertEqual(retained_count(0, 0.333), 0)

    def test_select_top_visual_indices_returns_sorted_original_indices(self) -> None:
        self.assertEqual(select_top_visual_indices([0.1, 0.9, 0.4, 0.8], 0.5), [1, 3])

    def test_first_active_shift_prefers_first_local_minimum(self) -> None:
        event = select_active_shift_event([0.95, 0.92, 0.93, 0.78])
        self.assertEqual(event.event_name, "first_active_attention_shift")
        self.assertEqual(event.event_step, 1)
        self.assertFalse(event.fallback_used)

    def test_local_minima(self) -> None:
        self.assertEqual(find_local_minima([1.0, 0.9, 0.95, 0.4, 0.5]), [1, 3])


class MathVerseLoaderTest(unittest.TestCase):
    def test_loads_local_smoke_samples(self) -> None:
        root = Path("/data/dataset/MathVerse")
        if not root.exists():
            self.skipTest("local MathVerse path is not available")
        samples = load_smoke_samples(root, limit=3)
        self.assertEqual(len(samples), 3)
        for sample in samples:
            self.assertTrue(Path(sample.image_path).exists())
            self.assertTrue(sample.prompt)
            self.assertTrue(sample.sample_id)


if __name__ == "__main__":
    unittest.main()
