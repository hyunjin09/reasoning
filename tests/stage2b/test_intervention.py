from __future__ import annotations

import unittest
from pathlib import Path

import torch

from visual_reasoning.stage2b.config import build_frozen_pilot_specs
from visual_reasoning.stage2b.intervention import apply_roi_mask


ROOT = Path(__file__).resolve().parents[2]


class ApplyRoiMaskTests(unittest.TestCase):
    def test_full_sequence_masks_only_requested_rows_and_keys(self) -> None:
        original = torch.zeros((1, 1, 10, 10), dtype=torch.float32)
        masked, audit = apply_roi_mask(
            original,
            prompt_length=4,
            roi_key_indices=(1, 2),
            window_start=1,
            window_end=3,
            query_length=10,
            key_length=10,
        )

        changed = torch.nonzero(masked != original, as_tuple=False).tolist()
        self.assertEqual(changed, [[0, 0, 4, 1], [0, 0, 4, 2], [0, 0, 5, 1], [0, 0, 5, 2]])
        self.assertEqual(audit["decision_indices"], [1, 2])
        self.assertEqual(audit["tensor_entries_modified"], 4)
        self.assertEqual(audit["target_entries_actually_changed"], 4)
        self.assertTrue(torch.equal(original, torch.zeros_like(original)))

    def test_cached_single_query_uses_key_length_for_decision_index(self) -> None:
        original = torch.zeros((1, 1, 1, 7), dtype=torch.bfloat16)
        masked, audit = apply_roi_mask(
            original,
            prompt_length=4,
            roi_key_indices=(1, 2),
            window_start=3,
            window_end=4,
            query_length=1,
            key_length=7,
        )

        self.assertEqual(audit["decision_indices"], [3])
        self.assertEqual(torch.nonzero(masked != original, as_tuple=False).tolist(), [[0, 0, 0, 1], [0, 0, 0, 2]])

    def test_inactive_window_returns_unmodified_mask(self) -> None:
        original = torch.zeros((1, 1, 1, 7), dtype=torch.float32)
        masked, audit = apply_roi_mask(
            original,
            prompt_length=4,
            roi_key_indices=(1, 2),
            window_start=4,
            window_end=5,
            query_length=1,
            key_length=7,
        )

        self.assertIs(masked, original)
        self.assertEqual(audit["tensor_entries_modified"], 0)


class FrozenPilotConfigTests(unittest.TestCase):
    def test_frozen_specs_select_predeclared_windows_and_disjoint_controls(self) -> None:
        specs = build_frozen_pilot_specs(
            ROOT / "outputs/stage2a/evidence_subset/examples",
            ROOT / "outputs/stage1/discovery/examples",
        )
        expected = {
            "699": ((583, 598), (561, 583), (604, 639)),
            "739": ((190, 218), (218, 263), (263, 312)),
            "2799": ((140, 211), (303, 349), (359, 390)),
            "3044": ((593, 614), (614, 630), (630, 673)),
            "3764": ((420, 475), (533, 627), (819, 847)),
        }

        self.assertEqual(set(specs), set(expected))
        for example_id, spec in specs.items():
            self.assertEqual(
                (tuple(spec["A_window"]), tuple(spec["B_window"]), tuple(spec["joint_computation_window"])),
                expected[example_id],
            )
            roi_a = set(spec["roi_A_visual_token_indices"])
            roi_b = set(spec["roi_B_visual_token_indices"])
            self.assertTrue(roi_a.isdisjoint(roi_b))
            for window_name in ("A", "B"):
                irrelevant = set(spec[f"irrelevant_{window_name}_visual_token_indices"])
                self.assertTrue(irrelevant.isdisjoint(roi_a | roi_b))
                target = roi_a if window_name == "A" else roi_b
                self.assertLessEqual(abs(len(irrelevant) - len(target)), 1)
            visual = set(spec["all_visual_token_indices"])
            self.assertTrue((roi_a | roi_b).issubset(visual))


if __name__ == "__main__":
    unittest.main()
