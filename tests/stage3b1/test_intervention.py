from __future__ import annotations

import unittest

import torch

from visual_reasoning.stage3b1.intervention import (
    TimedVisualCutoff,
    apply_timed_visual_cutoff,
    valid_cutoff_audit,
)


class CaptureAttention(torch.nn.Module):
    def forward(self, hidden_states: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        return attention_mask


class TimedCutoffTests(unittest.TestCase):
    def test_blocks_only_visual_keys_at_and_after_frozen_generated_index(self) -> None:
        original = torch.zeros((1, 1, 10, 10), dtype=torch.float32)
        masked, audit = apply_timed_visual_cutoff(
            original,
            prompt_length=5,
            cutoff_generated_index=2,
            visual_key_indices=[1, 3],
            query_length=10,
            key_length=10,
        )

        changed = torch.nonzero(masked != original, as_tuple=False).tolist()
        self.assertEqual(changed, [[0, 0, row, key] for row in range(7, 10) for key in (1, 3)])
        self.assertEqual(audit["absolute_query_indices"], [7, 8, 9])
        self.assertEqual(audit["generated_query_indices"], [2, 3, 4])
        self.assertEqual(audit["visual_key_indices"], [1, 3])
        self.assertEqual(audit["queries_before_cutoff_modified"], 0)
        self.assertFalse(audit["prefill_modified"])

    def test_generation_start_matches_stage3b0_boundary(self) -> None:
        original = torch.zeros((1, 1, 8, 8), dtype=torch.bfloat16)
        masked, audit = apply_timed_visual_cutoff(
            original,
            prompt_length=5,
            cutoff_generated_index=0,
            visual_key_indices=[1, 2],
            query_length=8,
            key_length=8,
        )

        self.assertEqual(audit["absolute_query_indices"], [5, 6, 7])
        self.assertEqual(torch.nonzero(masked != original).shape[0], 6)

    def test_hook_records_compact_explicit_boundary_audit(self) -> None:
        module = CaptureAttention()
        cutoff = TimedVisualCutoff(
            prompt_length=5,
            cutoff_generated_index=2,
            visual_key_indices=[1, 3],
            num_attention_heads=4,
        ).attach([module])
        try:
            output = module(
                hidden_states=torch.zeros((1, 10, 4), dtype=torch.float32),
                attention_mask=torch.zeros((1, 1, 10, 10), dtype=torch.float32),
            )
        finally:
            cutoff.close()

        self.assertEqual(torch.nonzero(output).shape[0], 6)
        self.assertEqual(cutoff.audit["visual_key_indices"], [1, 3])
        self.assertEqual(cutoff.audit["minimum_modified_absolute_query_index"], 7)
        self.assertEqual(cutoff.audit["maximum_modified_absolute_query_index"], 9)
        self.assertEqual(cutoff.audit["layers_modified"], [0])
        self.assertTrue(cutoff.audit["query_range_consistent_across_layers"])

    def test_runtime_audit_requires_cutoff_to_persist_through_probe(self) -> None:
        audit = {
            "enabled": True,
            "cutoff_absolute_query_index": 7,
            "minimum_modified_absolute_query_index": 7,
            "maximum_modified_absolute_query_index": 8,
            "generated_query_count_per_layer": 2,
            "queries_before_cutoff_modified": 0,
            "prefill_modified": False,
            "visual_key_indices": [1, 3],
            "layers_modified": [0],
            "query_range_consistent_across_layers": True,
            "tensor_entries_modified": 4,
            "target_entries_actually_changed": 4,
            "logical_head_edges_modified": 16,
        }

        self.assertFalse(
            valid_cutoff_audit(
                audit,
                prompt_length=5,
                prefix_token_count=4,
                candidate_token_count=3,
                cutoff_generated_index=2,
                visual_indices=[1, 3],
                layer_count=1,
                logical_heads=4,
            )
        )


if __name__ == "__main__":
    unittest.main()
