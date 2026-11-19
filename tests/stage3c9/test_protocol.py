from __future__ import annotations

from visual_reasoning.stage3c9.protocol import (
    canonical_streaming_kwargs,
    first_route_pair,
    intervention_boundaries,
    long_horizon_cohort_gate,
    phase_d_route_gate,
    select_prospective_screen,
)


def test_canonical_streaming_runtime_is_config_driven_and_fixed() -> None:
    config = {
        "runtime": {
            "gpu_class": "A6000",
            "canonical_scoring": {
                "path": "P2_fixed_streaming_cached",
                "chunk_size": 2048,
                "release_allocator_cache_between_chunks": True,
                "per_example_chunk_switching": False,
            },
        }
    }
    assert canonical_streaming_kwargs(config) == {
        "chunk_size": 2048,
        "release_allocator_cache": True,
    }


def test_canonical_streaming_runtime_rejects_switching_or_wrong_path() -> None:
    config = {
        "runtime": {
            "gpu_class": "A6000",
            "canonical_scoring": {
                "path": "P1_one_shot_cached",
                "chunk_size": 2048,
                "release_allocator_cache_between_chunks": True,
                "per_example_chunk_switching": True,
            },
        }
    }
    try:
        canonical_streaming_kwargs(config)
    except ValueError as exc:
        assert "canonical" in str(exc).lower()
    else:
        raise AssertionError("expected invalid canonical runtime to fail")


def test_intervention_boundaries_are_condition_invariant_union() -> None:
    assert intervention_boundaries([3, 4], [8], [], end_generated_index=12) == [4, 5, 9]
    assert intervention_boundaries([11], end_generated_index=12) == [12]
    assert intervention_boundaries([12], end_generated_index=12) == []


def _row(base: int, variant: str, *, words: int, numeric_candidates: int) -> dict:
    return {
        "problem_index": str(base),
        "sample_index": str(base * 5 + (0 if variant == "Vision Intensive" else 1)),
        "problem_version": variant,
        "metadata": {"source": "GeoQA", "subject": "Geometry", "subfield": "Length"},
        "image": f"images/image_{base}.png",
        "question_for_eval": " ".join(["word"] * words),
        "stage3c9_static_numeric_candidate_count": numeric_candidates,
    }


def test_screen_prioritizes_static_evidence_then_question_length_without_outcomes() -> None:
    rows = [
        _row(1, "Vision Dominant", words=10, numeric_candidates=0),
        _row(2, "Vision Dominant", words=5, numeric_candidates=1),
        _row(3, "Vision Dominant", words=12, numeric_candidates=1),
        _row(1, "Vision Intensive", words=10, numeric_candidates=0),
        _row(2, "Vision Intensive", words=5, numeric_candidates=1),
        _row(3, "Vision Intensive", words=12, numeric_candidates=1),
    ]
    selected = select_prospective_screen(rows, total_budget=5, initial_budget=3)
    assert [(row["base_problem_id"], row["variant"]) for row in selected] == [
        ("3", "Vision Dominant"),
        ("2", "Vision Dominant"),
        ("1", "Vision Dominant"),
        ("3", "Vision Intensive"),
        ("2", "Vision Intensive"),
    ]
    assert all(not row["selection_used_attention"] for row in selected)
    assert all(not row["selection_used_generation_outcome"] for row in selected)
    assert all(not row["selection_used_carrier_outcome"] for row in selected)
    assert [row["screen_order"] for row in selected] == list(range(5))
    assert all(row["screen_phase"] == ("initial" if i < 3 else "reserve") for i, row in enumerate(selected))


def test_screen_rejects_initial_budget_larger_than_unique_vision_dominant_pool() -> None:
    rows = [_row(1, "Vision Dominant", words=2, numeric_candidates=1)]
    try:
        select_prospective_screen(rows, total_budget=2, initial_budget=2)
    except ValueError as exc:
        assert "unique Vision Dominant" in str(exc)
    else:
        raise AssertionError("expected an infeasible initial-budget error")


def test_reserve_finishes_unique_dominant_bases_before_variant_retries() -> None:
    rows = []
    for base in range(1, 5):
        rows.extend([
            _row(base, "Vision Dominant", words=10 - base, numeric_candidates=1),
            _row(base, "Vision Intensive", words=10 - base, numeric_candidates=1),
        ])
    selected = select_prospective_screen(rows, total_budget=5, initial_budget=2)
    assert [(row["base_problem_id"], row["variant"]) for row in selected] == [
        ("1", "Vision Dominant"),
        ("2", "Vision Dominant"),
        ("3", "Vision Dominant"),
        ("4", "Vision Dominant"),
        ("1", "Vision Intensive"),
    ]
    assert [row["screen_phase"] for row in selected] == [
        "initial", "initial", "reserve", "reserve", "reserve"
    ]


def test_long_horizon_gate_requires_40_primary_and_8_disjoint_validation_bases() -> None:
    primary = [str(i) for i in range(40)]
    validation = [str(i) for i in range(40, 48)]
    assert long_horizon_cohort_gate(primary, validation)["run_primary"]
    assert not long_horizon_cohort_gate(primary[:39], validation)["run_primary"]
    assert not long_horizon_cohort_gate(primary, primary[:8])["run_primary"]


def test_long_horizon_gate_deduplicates_base_problem_ids() -> None:
    primary = [str(i) for i in range(39)] + ["1"]
    validation = [str(i) for i in range(40, 48)]
    result = long_horizon_cohort_gate(primary, validation)
    assert result["N_primary_unique"] == 39
    assert not result["run_primary"]


def test_first_route_pair_uses_annotation_order_not_effect_size() -> None:
    events = [
        {"event_id": 4, "classification": "C2", "span_start_token": 10, "span_end_token": 12, "rescue_gain": 0.06},
        {"event_id": 7, "classification": "C3", "span_start_token": 41, "span_end_token": 42, "rescue_gain": 0.08},
        {"event_id": 9, "classification": "C3", "span_start_token": 90, "span_end_token": 92, "rescue_gain": 9.0},
    ]
    pair = first_route_pair(events)
    assert pair["event_a_id"] == 4
    assert pair["event_b_id"] == 7
    assert pair["selection_used_effect_size"] is False


def test_phase_d_gate_requires_16_unique_bases_with_pairs() -> None:
    rows = [{"base_problem_id": str(index), "route_pair": {"event_a_id": 0, "event_b_id": 1}} for index in range(16)]
    assert phase_d_route_gate(rows)["run_phase_d"]
    rows.append({"base_problem_id": "0", "route_pair": {"event_a_id": 1, "event_b_id": 2}})
    assert phase_d_route_gate(rows)["eligible_unique_bases"] == 16
    assert not phase_d_route_gate(rows[:15])["run_phase_d"]
