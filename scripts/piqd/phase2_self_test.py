#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import torch

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "code"))

from piqd.hooks.query_key_capture import CapturedLayer, stack_queries, stack_visual_keys
from piqd.phase2.artifacts import (
    build_candidate_events,
    event_context_token_ids,
    load_phase1_artifacts,
    validate_phase1_row,
)
from piqd.phase2.replay import append_generated_tokens, event_key, hash_token_ids
from piqd.utils.io import write_json, write_jsonl


class Phase2ArtifactTest(unittest.TestCase):
    def test_rejects_missing_generated_token_ids(self) -> None:
        blockers = validate_phase1_row(
            {"sample_id": "s1", "prompt": "p", "image_path": __file__},
            {
                "status": "ok",
                "active_visual_token_indices": [0],
                "num_visual_tokens_full": 3,
                "num_visual_tokens_retained": 1,
                "decoding_config": {},
            },
            {"status": "ok", "event_token_index": 0, "similarity_curve": [{"step": 0, "token_id": 1}]},
        )
        self.assertIn("missing exact generated_prefix_token_ids", blockers)

    def test_builds_primary_and_minimum_events(self) -> None:
        generation = {"generated_prefix_token_ids": [10, 11, 12, 13]}
        event = {
            "event_name": "first_active_attention_shift",
            "event_token_index": 1,
            "fallback_used": False,
            "similarity_curve": [
                {"step": 0, "token_id": 10, "risd_similarity_active": 0.9},
                {"step": 1, "token_id": 11, "risd_similarity_active": 0.8},
                {"step": 2, "token_id": 12, "risd_similarity_active": 0.2},
            ],
        }
        events = build_candidate_events(generation, event)
        self.assertEqual([item.event_type for item in events], ["first_active_attention_shift", "minimum_active_similarity_step"])
        self.assertEqual([item.generated_token_index for item in events], [1, 2])

    def test_context_token_ids_clamps_to_bounds(self) -> None:
        self.assertEqual(event_context_token_ids([1, 2, 3], 0, radius=2), [1, 2, 3])

    def test_loads_real_phase1_artifacts_if_available(self) -> None:
        phase1_dir = REPO / "outputs/piqd/phase1"
        if not phase1_dir.exists():
            self.skipTest("Phase 1 artifacts are not available")
        rows, blockers = load_phase1_artifacts(phase1_dir)
        self.assertFalse(blockers)
        self.assertEqual(len(rows), 10)
        self.assertTrue(all(row.generated_token_ids for row in rows))
        self.assertTrue(all(row.retained_visual_token_indices for row in rows))

    def test_load_reports_blockers_for_incomplete_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_json(root / "phase1_config.json", {"fastv_status": "approximate_fastv_style_static_pruning"})
            write_jsonl(root / "phase1_samples.jsonl", [{"sample_id": "s1", "prompt": "p", "image_path": __file__}])
            write_jsonl(root / "phase1_generation_logs.jsonl", [{"sample_id": "s1", "status": "ok"}])
            write_jsonl(root / "phase1_event_logs.jsonl", [{"sample_id": "s1", "status": "ok"}])
            rows, blockers = load_phase1_artifacts(root)
        self.assertFalse(rows)
        self.assertTrue(any("missing exact generated_prefix_token_ids" in item for item in blockers))


class Phase2ReplayTest(unittest.TestCase):
    def test_append_generated_tokens_extends_masks_and_mm_types(self) -> None:
        inputs = {
            "input_ids": torch.tensor([[1, 2, 3]], dtype=torch.long),
            "attention_mask": torch.tensor([[1, 1, 1]], dtype=torch.long),
            "mm_token_type_ids": torch.tensor([[1, 0, 0]], dtype=torch.long),
        }
        result = append_generated_tokens(inputs, [4, 5])
        self.assertEqual(result["input_ids"].tolist(), [[1, 2, 3, 4, 5]])
        self.assertEqual(result["attention_mask"].tolist(), [[1, 1, 1, 1, 1]])
        self.assertEqual(result["mm_token_type_ids"].tolist(), [[1, 0, 0, 0, 0]])

    def test_event_key_is_position_specific(self) -> None:
        event = type("Event", (), {"event_type": "first_active_attention_shift", "generated_token_index": 3})()
        self.assertEqual(event_key(event), "first_active_attention_shift::3")

    def test_hash_token_ids_is_stable(self) -> None:
        self.assertEqual(hash_token_ids([1, 2, 3]), hash_token_ids([1, 2, 3]))
        self.assertNotEqual(hash_token_ids([1, 2, 3]), hash_token_ids([1, 2, 4]))


class QueryKeyCaptureTest(unittest.TestCase):
    def test_stack_queries_preserves_layer_head_shape(self) -> None:
        captured = {
            2: CapturedLayer(queries_by_event={"event::1": torch.zeros(4, 8)}),
            3: CapturedLayer(queries_by_event={"event::1": torch.ones(4, 8)}),
        }
        stacked = stack_queries(captured, "event::1", [2, 3])
        self.assertEqual(tuple(stacked.shape), (2, 4, 8))

    def test_stack_visual_keys_preserves_layer_head_visual_shape(self) -> None:
        captured = {
            2: CapturedLayer(visual_keys=torch.zeros(4, 5, 8)),
            3: CapturedLayer(visual_keys=torch.ones(4, 5, 8)),
        }
        stacked = stack_visual_keys(captured, [2, 3])
        self.assertEqual(tuple(stacked.shape), (2, 4, 5, 8))


if __name__ == "__main__":
    unittest.main()
