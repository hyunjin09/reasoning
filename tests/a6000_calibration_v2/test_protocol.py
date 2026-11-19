from __future__ import annotations

import pytest
import torch

from visual_reasoning.a6000_calibration_v2.protocol import (
    decide_p1,
    select_streaming_chunk,
    summarize_tensor_pair,
    token_by_token_is_unlocked,
    validate_stress_manifest,
)


def stress_row(index: int) -> dict:
    return {
        "stress_order": index,
        "base_problem_id": str(index),
        "example_id": str(100 + index),
        "stress_prefix_token_count": 1000 - index,
        "visual_token_count": 10 + index,
        "candidate_length": 3,
        "original_suffix_ids": [1, 2, 3],
        "counterfactual_suffix_ids": [4, 2, 3],
        "complete": True,
        "normal_termination": True,
        "selection_used_attention": False,
        "selection_used_causal_effect": False,
    }


def test_validate_stress_manifest_requires_six_unique_effect_independent_cases() -> None:
    result = validate_stress_manifest([stress_row(index) for index in range(6)])
    assert result["passed"] is True
    assert result["unique_base_count"] == 6


def test_validate_stress_manifest_rejects_attention_selection() -> None:
    rows = [stress_row(index) for index in range(6)]
    rows[2]["selection_used_attention"] = True
    with pytest.raises(ValueError, match="attention"):
        validate_stress_manifest(rows)


def test_decide_p1_passes_only_when_all_cases_meet_memory_and_mechanics() -> None:
    rows = [
        {
            "base_problem_id": str(index),
            "status": "PASS",
            "oom": False,
            "finite": True,
            "deterministic": True,
            "backend_unchanged": True,
            "silent_truncation": False,
            "peak_reserved_vram_fraction": 0.80,
        }
        for index in range(6)
    ]
    assert decide_p1(rows, expected_count=6, memory_fraction_max=0.90)["selected_path"] == "P1"
    rows[0]["peak_reserved_vram_fraction"] = 0.91
    decision = decide_p1(rows, expected_count=6, memory_fraction_max=0.90)
    assert decision["status"] == "NOT_FEASIBLE"
    assert decision["selected_path"] == "P2_REQUIRED"


def test_decide_p1_rejects_oom_without_requiring_remaining_cases() -> None:
    rows = [{
        "base_problem_id": "351",
        "status": "OOM",
        "oom": True,
        "finite": False,
        "deterministic": False,
        "backend_unchanged": True,
        "silent_truncation": False,
        "peak_reserved_vram_fraction": None,
    }]
    decision = decide_p1(rows, expected_count=6, memory_fraction_max=0.90)
    assert decision["status"] == "NOT_FEASIBLE"
    assert decision["conclusive_early_failure"] is True


def test_select_streaming_chunk_uses_largest_complete_memory_safe_candidate() -> None:
    rows = []
    for chunk in (8192, 4096):
        for index in range(6):
            rows.append({
                "chunk_size": chunk,
                "base_problem_id": str(index),
                "status": "OOM" if chunk == 8192 and index == 0 else "PASS",
                "oom": chunk == 8192 and index == 0,
                "finite": not (chunk == 8192 and index == 0),
                "backend_unchanged": True,
                "peak_reserved_vram_fraction": 0.7,
            })
    decision = select_streaming_chunk(
        rows,
        candidates_descending=[8192, 4096, 2048],
        expected_bases={str(index) for index in range(6)},
        memory_fraction_max=0.90,
    )
    assert decision["status"] == "SELECTED"
    assert decision["selected_chunk_size"] == 4096
    assert decision["selection_uses_scientific_effects"] is False


def test_select_streaming_chunk_waits_for_all_stress_bases() -> None:
    rows = [{
        "chunk_size": 4096,
        "base_problem_id": "0",
        "status": "PASS",
        "oom": False,
        "finite": True,
        "backend_unchanged": True,
        "peak_reserved_vram_fraction": 0.5,
    }]
    decision = select_streaming_chunk(
        rows,
        candidates_descending=[4096],
        expected_bases={"0", "1"},
        memory_fraction_max=0.90,
    )
    assert decision["status"] == "INCOMPLETE"
    assert decision["selected_chunk_size"] is None


def test_token_by_token_unlock_requires_every_listed_chunk_to_fail_gate_case() -> None:
    rows = [
        {
            "chunk_size": chunk,
            "base_problem_id": "351",
            "oom": chunk == 8192,
            "finite": chunk != 8192,
            "backend_unchanged": True,
            "peak_reserved_vram_fraction": 0.95 if chunk == 4096 else 0.80,
        }
        for chunk in (8192, 4096)
    ]
    assert token_by_token_is_unlocked(
        rows,
        candidates_descending=[8192, 4096],
        gate_base="351",
        memory_fraction_max=0.90,
    )
    assert not token_by_token_is_unlocked(
        rows[:1],
        candidates_descending=[8192, 4096],
        gate_base="351",
        memory_fraction_max=0.90,
    )


def test_tensor_pair_summary_reports_shape_exactness_and_fp32_delta() -> None:
    left = torch.tensor([[1.0, 2.0]], dtype=torch.bfloat16)
    exact = summarize_tensor_pair(left, left.clone())
    assert exact == {"shape": [1, 2], "exact": True, "max_abs_delta": 0.0, "finite": True}
    shifted = summarize_tensor_pair(left, torch.tensor([[1.0, 2.5]], dtype=torch.bfloat16))
    assert shifted["exact"] is False
    assert shifted["max_abs_delta"] == 0.5
