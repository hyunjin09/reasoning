#!/usr/bin/env python3
"""CPU-only tests for Stage 1 selection and descriptive analysis."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
import torch

from visual_reasoning.stage0.modeling import OnlineGenerationScoreRecorder
from visual_reasoning.stage1.analysis import add_source_densities, aggregate_spans, build_spans, candidate_visual_peaks, semantic_label, visual_reference_context
from visual_reasoning.stage1.data import PILOT_COMPLETED_IDS, PILOT_TRUNCATED_IDS, build_pilot_manifest, select_discovery_rows
from visual_reasoning.stage1.protocol import (
    classify_protocol_generation,
    protocol_parameters,
    repeated_ngram_fraction,
    repetition_diagnostics,
    transformers_generation_kwargs,
)
from visual_reasoning.stage1.plotting import save_span_timeline
from visual_reasoning.stage1.reporting import generation_environment_line


def synthetic_rows(problem_count: int = 120) -> list[dict]:
    rows = []
    sample_index = 1
    for problem_index in range(1, problem_count + 1):
        for variant in ("Text Dominant", "Text Lite", "Vision Intensive", "Vision Dominant", "Vision Only"):
            rows.append(
                {
                    "sample_index": str(sample_index),
                    "problem_index": str(problem_index),
                    "problem_version": variant,
                    "question": "A deliberately multi step geometry question " * (1 + problem_index % 3),
                    "answer": "A",
                    "image": f"image_{problem_index}.png",
                    "metadata": {"subject": f"subject_{problem_index % 4}"},
                }
            )
            sample_index += 1
    return rows


class SelectionTests(unittest.TestCase):
    def test_pilot_has_sixteen_truncated_and_four_completed(self) -> None:
        rows = synthetic_rows(20)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for sample_id in (*PILOT_TRUNCATED_IDS, *PILOT_COMPLETED_IDS):
                directory = root / "examples" / sample_id
                directory.mkdir(parents=True)
                status = "correct" if sample_id in PILOT_COMPLETED_IDS else "truncated"
                (directory / "result.json").write_text(
                    f'{{"status":"{status}","generated_token_count":2048}}', encoding="utf-8"
                )
            manifest = build_pilot_manifest(rows, root)
        self.assertEqual(len(manifest), 20)
        self.assertEqual(sum(row["stage0_status"] == "truncated" for row in manifest), 16)
        self.assertEqual(sum(row["stage0_status"] == "correct" for row in manifest), 4)

    def test_discovery_selection_is_paired_and_bounded(self) -> None:
        selected = select_discovery_rows(synthetic_rows(), max_attempts=200)
        self.assertEqual(len(selected), 200)
        self.assertEqual({row["problem_version"] for row in selected}, {"Vision Intensive", "Vision Dominant"})
        by_problem = {}
        for row in selected:
            by_problem.setdefault(row["problem_index"], set()).add(row["problem_version"])
        self.assertEqual(len(by_problem), 100)
        self.assertTrue(all(len(variants) == 2 for variants in by_problem.values()))


class AnalysisTests(unittest.TestCase):
    def test_semantic_labels_are_textual(self) -> None:
        self.assertEqual(semantic_label("Look at the diagram."), "VISUAL_READ")
        self.assertEqual(semantic_label("Compute 2 + 3 = 5."), "COMPUTE")
        self.assertEqual(semantic_label("The lines are parallel."), "RELATION_INFERENCE")
        self.assertEqual(semantic_label("Check the result."), "VERIFY")
        self.assertEqual(semantic_label("The final answer is C."), "ANSWER_SELECTION")
        self.assertEqual(semantic_label("**D**<|im_end|>"), "ANSWER_SELECTION")
        self.assertNotEqual(semantic_label("I need to figure out this problem."), "VISUAL_READ")
        self.assertNotEqual(semantic_label("Okay, let's see."), "VISUAL_READ")
        self.assertFalse(visual_reference_context("Let's figure out what to do.")["has_visual_reference"])

    def test_common_abbreviation_does_not_split_span(self) -> None:
        spans = build_spans([{"decoded_token": "The graph is speed vs."}, {"decoded_token": " time."}])
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0]["span_text"], "The graph is speed vs. time.")

    def test_density_normalizes_by_source_count(self) -> None:
        rows = [{"visual_attention_mass": 0.4, "prompt_attention_mass": 0.6, "reasoning_attention_mass": 0.0}]
        arrays = {
            "modality_by_layer": np.asarray([[[0.4, 0.6, 0.0]]], dtype=np.float32),
            "key_lengths": np.asarray([10], dtype=np.int32),
            "visual_focus": np.asarray([[0.2, 0.2]], dtype=np.float32),
        }
        updated = add_source_densities(rows, arrays, prompt_length=10, visual_count=2)
        self.assertAlmostEqual(rows[0]["visual_attention_density"], 0.2)
        self.assertAlmostEqual(rows[0]["prompt_attention_density"], 0.075)
        self.assertEqual(rows[0]["reasoning_attention_density"], 0.0)
        self.assertEqual(updated["source_token_counts"].tolist(), [[2, 8, 0]])

    def test_spans_focus_and_peaks(self) -> None:
        rows = []
        visual_values = [0.1, 0.1, 0.8, 0.1, 0.1, 0.7, 0.1]
        for index, value in enumerate(visual_values):
            rows.append(
                {
                    "decoded_token": f"Step {index}. ",
                    "visual_attention_mass": value,
                    "prompt_attention_mass": 0.5,
                    "reasoning_attention_mass": 0.5 - value / 2,
                    "visual_attention_density": value / 2,
                    "prompt_attention_density": 0.1,
                    "reasoning_attention_density": 0.1,
                    "next_token_entropy": 0.2 + index / 100,
                    "top1_probability": 0.9,
                    "top1_top2_margin": 0.8,
                }
            )
        spans = build_spans(rows)
        modality = np.asarray([[[v, 0.5, 0.5 - v / 2]] for v in visual_values], dtype=np.float32)
        arrays = {
            "modality_by_layer": modality,
            "modality_density_by_layer": modality / 2,
            "visual_focus": np.asarray([[v, 1 - v] for v in visual_values], dtype=np.float32),
        }
        span_arrays = aggregate_spans(spans, rows, arrays)
        peaks = candidate_visual_peaks(spans)
        self.assertEqual(span_arrays["modality_mass_by_span_layer"].shape, (7, 1, 3))
        self.assertGreaterEqual(peaks["peak_count"], 2)
        for peak in peaks["peaks"]:
            span = spans[peak["span_id"]]
            expected = (span["start_token"] + span["end_token"]) / 2 / len(rows)
            self.assertAlmostEqual(peak["normalized_generation_position"], expected)

    def test_whitespace_boundary_tokens_remain_covered(self) -> None:
        rows = [
            {"decoded_token": "First."},
            {"decoded_token": " \n\n"},
            {"decoded_token": "---\n\n"},
            {"decoded_token": "Next."},
        ]
        spans = build_spans(rows)
        self.assertEqual(spans[0]["start_token"], 0)
        self.assertEqual(spans[-1]["end_token"], len(rows))
        self.assertEqual(
            [(span["start_token"], span["end_token"]) for span in spans],
            [(0, 1), (1, 3), (3, 4)],
        )

    def test_span_timeline_is_reproducibly_rendered(self) -> None:
        rows = []
        for index, value in enumerate((0.1, 0.8, 0.2)):
            rows.append(
                {
                    "decoded_token": f"Step {index}.",
                    "visual_attention_mass": value,
                    "prompt_attention_mass": 0.5,
                    "reasoning_attention_mass": 0.5 - value / 2,
                    "visual_attention_density": value / 2,
                    "prompt_attention_density": 0.1,
                    "reasoning_attention_density": 0.1,
                    "next_token_entropy": 0.2 + index / 10,
                    "top1_probability": 0.9,
                    "top1_top2_margin": 0.8,
                }
            )
        spans = build_spans(rows)
        modality = np.asarray([[[v, 0.5, 0.5 - v / 2]] for v in (0.1, 0.8, 0.2)], dtype=np.float32)
        aggregate_spans(
            spans,
            rows,
            {
                "modality_by_layer": modality,
                "modality_density_by_layer": modality / 2,
                "visual_focus": np.asarray([[0.2, 0.8], [0.8, 0.2], [0.3, 0.7]], dtype=np.float32),
            },
        )
        peaks = candidate_visual_peaks(spans)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "timeline.png"
            save_span_timeline(spans, peaks, path, "test")
            self.assertTrue(path.is_file())
            self.assertGreater(path.stat().st_size, 1000)


class ProtocolTests(unittest.TestCase):
    def test_environment_line_reflects_official_sampling(self) -> None:
        line = generation_environment_line("official", protocol_parameters("official"))
        self.assertIn("sampling enabled", line)
        self.assertIn("temperature=`0.6`", line)
        self.assertNotIn("sampling disabled", line)

    def test_official_protocol_matches_recorded_qwen_recipe(self) -> None:
        parameters = protocol_parameters("official")
        self.assertEqual(parameters["seed"], 1234)
        self.assertEqual(parameters["max_new_tokens"], 40960)
        self.assertEqual(parameters["temperature"], 0.6)
        self.assertEqual(parameters["top_p"], 0.95)
        self.assertEqual(parameters["top_k"], 20)
        kwargs = transformers_generation_kwargs(parameters)
        self.assertNotIn("presence_penalty", kwargs)
        self.assertTrue(kwargs["do_sample"])

    def test_cap_hit_overrides_answer_like_text(self) -> None:
        classified = classify_protocol_generation(
            [7, 8, 9], "The final answer is A.", "A", max_new_tokens=3, eos_token_ids=[2]
        )
        self.assertEqual(classified["status"], "truncated")
        self.assertFalse(classified["complete"])
        self.assertEqual(classified["termination_reason"], "safety_cap")
        eos_on_ceiling = classify_protocol_generation(
            [7, 8, 2], "The final answer is A.", "A", max_new_tokens=3, eos_token_ids=[2]
        )
        self.assertEqual(eos_on_ceiling["status"], "truncated")

    def test_repetition_diagnostics_flag_simple_loop(self) -> None:
        text = "Wait. Let's check again. " * 30
        diagnostics = repetition_diagnostics(text)
        self.assertTrue(diagnostics["any_pathology_flag"])
        self.assertGreater(repeated_ngram_fraction(text.lower().split(), 3), 0.9)

    def test_online_score_recorder_keeps_only_one_step(self) -> None:
        recorder = OnlineGenerationScoreRecorder()
        recorder.put(torch.tensor([[1, 2, 3]]))  # initial streamed prompt
        scores = torch.tensor([[0.0, 1.0, 2.0]])
        returned = recorder(torch.tensor([[1, 2, 3]]), scores)
        self.assertIs(returned, scores)
        recorder.put(torch.tensor([2]))
        recorder.end()
        self.assertEqual(len(recorder.rows), 1)
        self.assertGreater(recorder.rows[0]["top1_probability"], 0.6)
        self.assertTrue(np.isfinite(recorder.rows[0]["next_token_entropy"]))


if __name__ == "__main__":
    unittest.main()
