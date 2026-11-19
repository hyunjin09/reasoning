#!/usr/bin/env python3
"""CPU-only unit tests for the Stage 0 instrumentation primitives."""

from __future__ import annotations

import unittest
from pathlib import Path

import torch

from visual_reasoning.stage0.analysis import (
    aggregate_span_signals,
    build_reasoning_spans,
    extract_answer,
    predictive_metrics,
)
from visual_reasoning.stage0.attention import OnlineAttentionRecorder, visual_grid_metadata
from visual_reasoning.stage0.data import image_path_candidates, select_stage0_subset
from visual_reasoning.stage0.modeling import _incremental_decode_pieces


def synthetic_mathverse_rows(problem_count: int = 20) -> list[dict]:
    rows: list[dict] = []
    sample_index = 1
    for problem_index in range(1, problem_count + 1):
        for variant in (
            "Text Dominant",
            "Text Lite",
            "Vision Intensive",
            "Vision Dominant",
            "Vision Only",
        ):
            rows.append(
                {
                    "sample_index": str(sample_index),
                    "problem_index": str(problem_index),
                    "problem_version": variant,
                    "question": f"Question {problem_index}",
                    "answer": "A",
                    "image": f"images_version_1-4/image_{problem_index}.png",
                    "metadata": {"subject": "Geometry" if problem_index % 2 else "Algebra"},
                }
            )
            sample_index += 1
    return rows


class DatasetTests(unittest.TestCase):
    def test_image_candidates_cover_local_nested_layout(self) -> None:
        root = Path("/dataset")
        candidates = image_path_candidates(root, "images_version_1-4/image_1.png")
        self.assertEqual(candidates[0], root / "images_version_1-4/image_1.png")
        self.assertEqual(candidates[1], root / "images" / "images_version_1-4/image_1.png")

    def test_full_subset_is_paired_and_visually_demanding(self) -> None:
        selected = select_stage0_subset(synthetic_mathverse_rows(), count=30, mode="full")
        self.assertEqual(len(selected), 30)
        self.assertEqual({row["problem_version"] for row in selected}, {"Vision Intensive", "Vision Dominant"})
        by_problem: dict[str, set[str]] = {}
        for row in selected:
            by_problem.setdefault(row["problem_index"], set()).add(row["problem_version"])
        self.assertEqual(len(by_problem), 15)
        self.assertTrue(all(len(variants) == 2 for variants in by_problem.values()))

    def test_smoke_subset_has_requested_size(self) -> None:
        selected = select_stage0_subset(synthetic_mathverse_rows(), count=3, mode="smoke")
        self.assertEqual(len(selected), 3)
        self.assertEqual([row["sample_index"] for row in selected], ["3", "4", "8"])


class AnalysisTests(unittest.TestCase):
    def test_incremental_decode_handles_multibyte_prefix_rewrite(self) -> None:
        class RewritingTokenizer:
            decoded = {
                (1,): "x �",
                (1, 2): "x ∠",
                (1, 2, 3): "x ∠ y",
            }

            def decode(self, token_ids, **_kwargs):
                return self.decoded[tuple(token_ids)]

        pieces, full, aligned = _incremental_decode_pieces(RewritingTokenizer(), [1, 2, 3])
        self.assertEqual(pieces, ["x ", "∠", " y"])
        self.assertEqual("".join(pieces), full)
        self.assertTrue(aligned)

    def test_extract_answer_prefers_explicit_final_marker(self) -> None:
        response = "We compute 40 first. Therefore, the final answer is D."
        self.assertEqual(extract_answer(response, choices=("A", "B", "C", "D")), "D")

    def test_predictive_metrics(self) -> None:
        logits = torch.tensor([0.0, 1.0, 2.0])
        metrics = predictive_metrics(logits, selected_token_id=2)
        self.assertGreater(metrics["top1_probability"], 0.6)
        self.assertGreater(metrics["top1_top2_margin"], 0.3)
        self.assertAlmostEqual(metrics["token_log_probability"], -0.4076, places=3)
        self.assertGreater(metrics["next_token_entropy"], 0.8)

    def test_spans_and_signal_aggregation(self) -> None:
        token_rows = [
            {"token_index": 0, "decoded_token": "Look", "visual_attention_mass": 0.8},
            {"token_index": 1, "decoded_token": " at", "visual_attention_mass": 0.7},
            {"token_index": 2, "decoded_token": " diagram.", "visual_attention_mass": 0.6},
            {"token_index": 3, "decoded_token": " Calculate", "visual_attention_mass": 0.2},
            {"token_index": 4, "decoded_token": " 2+2.", "visual_attention_mass": 0.1},
        ]
        spans = build_reasoning_spans(token_rows)
        self.assertEqual(len(spans), 2)
        self.assertEqual(spans[0]["start_token"], 0)
        self.assertEqual(spans[0]["end_token"], 3)
        self.assertEqual(spans[0]["provisional_semantic_label"], "visual_reference")
        aggregate_span_signals(spans, token_rows, signal_names=("visual_attention_mass",))
        self.assertAlmostEqual(spans[0]["signals"]["visual_attention_mass"], 0.7)


class AttentionTests(unittest.TestCase):
    def test_visual_grid_metadata(self) -> None:
        metadata = visual_grid_metadata([1, 14, 20], merge_size=2, patch_size=16)
        self.assertEqual(metadata["visual_token_count"], 70)
        self.assertEqual(metadata["merged_grid_shape"], [1, 7, 10])
        self.assertEqual(metadata["resized_image_size"], [320, 224])

    def test_online_attention_aggregation(self) -> None:
        recorder = OnlineAttentionRecorder(
            prompt_length=4,
            visual_indices=[1, 2],
            num_layers=2,
            selected_head_layers=[1],
        )
        first = torch.tensor([[[[0.1, 0.2, 0.3, 0.4]], [[0.1, 0.2, 0.3, 0.4]]]])
        recorder.consume(0, first)
        recorder.consume(1, first)
        second = torch.full((1, 2, 1, 5), 0.2)
        recorder.consume(0, second)
        recorder.consume(1, second)
        arrays = recorder.as_arrays()
        self.assertEqual(arrays["modality_by_layer"].shape, (2, 2, 3))
        self.assertEqual(arrays["selected_head_mass"].shape, (2, 1, 2, 3))
        self.assertEqual(arrays["visual_focus"].shape, (2, 2))
        self.assertAlmostEqual(float(arrays["modality_by_layer"][0, 0, 0]), 0.5, places=5)
        self.assertAlmostEqual(float(arrays["modality_by_layer"][0, 0, 1]), 0.5, places=5)
        self.assertAlmostEqual(float(arrays["modality_by_layer"][1, 0, 2]), 0.2, places=5)
        self.assertTrue(recorder.validate(expected_steps=2)["passed"])


if __name__ == "__main__":
    unittest.main()
