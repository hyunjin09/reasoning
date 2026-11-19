from __future__ import annotations

from visual_reasoning.stage3c8.protocol import (
    classify_lexical_token,
    distributed_process_info,
    local_cuda_device_index,
    phase_d_gate,
    select_fresh_screen,
)


def _row(base: int, source: str, variant: str = "Vision Dominant") -> dict:
    return {
        "problem_index": str(base),
        "sample_index": str(base * 5 - 1),
        "problem_version": variant,
        "metadata": {"source": source, "subject": "Plane Geometry", "subfield": "Length"},
        "image": f"images/image_{base}.png",
        "question_for_eval": f"Find the marked length for problem {base}.",
    }


def test_fresh_screen_is_source_ordered_disjoint_and_vision_dominant() -> None:
    rows = [
        _row(7, "Geometry3K"),
        _row(3, "GEOS"),
        _row(5, "GeoQA"),
        _row(2, "GeoQA"),
        _row(4, "GEOS"),
        _row(6, "Geometry3K"),
        _row(1, "GeoQA", "Vision Intensive"),
    ]
    selected = select_fresh_screen(rows, excluded_base_ids={"5"}, budget=5)
    assert [row["base_problem_id"] for row in selected] == ["2", "3", "4", "6", "7"]
    assert all(row["variant"] == "Vision Dominant" for row in selected)
    assert all(not row["selection_used_attention"] for row in selected)
    assert all(not row["selection_used_generation_outcome"] for row in selected)


def test_token_taxonomy_handles_visual_entity_function_and_boundary() -> None:
    assert classify_lexical_token("AB", visual_entities={"AB"}) == "VISUAL_ENTITY"
    assert classify_lexical_token(" is", visual_entities={"AB"}) == "FUNCTION_WORD"
    assert classify_lexical_token("?", visual_entities={"AB"}) == "PUNCTUATION"
    assert classify_lexical_token("42", visual_entities={"AB"}) == "NUMERIC_LITERAL"
    assert classify_lexical_token("therefore", visual_entities={"AB"}) == "DISCOURSE_MARKER"
    assert classify_lexical_token("42", visual_entities={"42"}) == "NUMERIC_LITERAL"


def test_phase_d_gate_uses_only_frozen_phase_a_or_phase_b_rules() -> None:
    assert phase_d_gate(
        phase_a_robust={"a_like": True, "b_like": False},
        phase_b_all_recent_median_rr=0.1,
        phase_b_local_or_group_robust=False,
    )["run"]
    assert phase_d_gate(
        phase_a_robust={"a_like": False, "b_like": False},
        phase_b_all_recent_median_rr=0.5,
        phase_b_local_or_group_robust=True,
    )["run"]
    assert not phase_d_gate(
        phase_a_robust={"a_like": False, "b_like": False},
        phase_b_all_recent_median_rr=0.9,
        phase_b_local_or_group_robust=False,
    )["run"]


def test_local_cuda_device_prefers_torchrun_then_slurm_local_rank() -> None:
    assert local_cuda_device_index({"LOCAL_RANK": "3", "SLURM_LOCALID": "1"}) == 3
    assert local_cuda_device_index({"SLURM_LOCALID": "1"}) == 1
    assert local_cuda_device_index({}) == 0


def test_local_cuda_device_uses_ordinal_zero_when_slurm_exposes_one_gpu_per_task() -> None:
    assert local_cuda_device_index({"SLURM_LOCALID": "1"}, visible_device_count=1) == 0


def test_distributed_process_info_supports_torchrun_and_plain_srun() -> None:
    assert distributed_process_info({"WORLD_SIZE": "2", "RANK": "1", "LOCAL_RANK": "1"}) == (2, 1, 1)
    assert distributed_process_info({"SLURM_NTASKS": "2", "SLURM_PROCID": "1", "SLURM_LOCALID": "1"}) == (2, 1, 1)
    assert distributed_process_info({}) == (1, 0, 0)


def test_distributed_process_info_uses_process_local_ordinal_for_one_visible_gpu() -> None:
    assert distributed_process_info(
        {"SLURM_NTASKS": "2", "SLURM_PROCID": "1", "SLURM_LOCALID": "1"},
        visible_device_count=1,
    ) == (2, 1, 0)
