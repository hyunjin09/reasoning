from __future__ import annotations

import pytest

from visual_reasoning.stage3c9.analysis import (
    aligned_preference,
    classify_checkpoint,
    enrichment_match_key,
    lifetime_phenotype,
    repeated_checkpoint_status,
    route_phenotype,
    summarize_source_window,
    source_and_rescue_effects,
)


def test_enrichment_matching_prioritizes_boundary_and_readout_distance() -> None:
    focal = {
        "boundary_position": True,
        "distance_to_local_use_readout": 1,
        "normalized_reasoning_progress": 0.5,
        "span_length": 2,
        "local_token_density": 0.5,
        "event_id": 1,
    }
    boundary_mismatch = {**focal, "boundary_position": False, "event_id": 2}
    progress_mismatch = {**focal, "normalized_reasoning_progress": 0.9, "event_id": 3}
    assert enrichment_match_key(focal, progress_mismatch) < enrichment_match_key(focal, boundary_mismatch)


def test_condition_alignment_flips_counterfactual_semantic_direction() -> None:
    assert aligned_preference(0.4, "O") == 0.4
    assert aligned_preference(-0.4, "C") == 0.4
    assert aligned_preference(0.4, "O_sham") == 0.4
    assert aligned_preference(-0.4, "C_sham") == 0.4


def test_source_and_rescue_effects_are_unnormalized_and_unclipped() -> None:
    result = source_and_rescue_effects(
        condition="C",
        native_D=-0.5,
        suppressed_D=-0.2,
        rescue_D=-0.35,
    )
    assert result["source_loss"] == pytest.approx(0.3)
    assert result["rescue_gain"] == pytest.approx(0.15)
    assert result["rescue_ratio"] == pytest.approx(0.5)


def test_source_and_rescue_effects_preserve_negative_or_over_one_ratios() -> None:
    negative = source_and_rescue_effects(
        condition="O", native_D=0.4, suppressed_D=0.2, rescue_D=0.1,
    )
    over_one = source_and_rescue_effects(
        condition="O", native_D=0.4, suppressed_D=0.2, rescue_D=0.5,
    )
    assert negative["rescue_ratio"] == pytest.approx(-0.5)
    assert over_one["rescue_ratio"] == pytest.approx(1.5)


def test_summarize_source_window_applies_semantic_and_matched_sham_gate() -> None:
    summary = summarize_source_window({
        "O": {"native_D": 0.5, "suppressed_D": 0.3},
        "C": {"native_D": -0.6, "suppressed_D": -0.4},
        "O_sham": {"native_D": 0.5, "suppressed_D": 0.49},
        "C_sham": {"native_D": -0.6, "suppressed_D": -0.59},
    })
    assert summary["source_sensitive"]
    assert summary["source_losses"] == pytest.approx({"O": 0.2, "C": 0.2})
    assert summary["sham_source_effects"] == pytest.approx({"O_sham": 0.01, "C_sham": 0.01})


def test_checkpoint_classification_uses_source_sham_neighbor_and_ratio_gates() -> None:
    result = classify_checkpoint(
        source_losses={"O": 0.4, "C": 0.3},
        sham_source_effects={"O_sham": 0.01, "C_sham": -0.02},
        rescue_gains={"O": 0.2, "C": 0.1},
        rescue_ratios={"O": 0.5, "C": 1 / 3},
        neighbor_gains={"O": 0.02, "C": 0.01},
        final_rescue_gains={"O": 0.01, "C": 0.02},
    )
    assert result["classification"] == "C2"
    assert result["source_sensitive"]
    assert result["functional_span_rescue"]


def test_persistent_checkpoint_requires_meaningful_distant_rescue() -> None:
    result = classify_checkpoint(
        source_losses={"O": 0.4, "C": 0.3},
        sham_source_effects={"O_sham": 0.01, "C_sham": 0.01},
        rescue_gains={"O": 0.2, "C": 0.1},
        rescue_ratios={"O": 0.5, "C": 1 / 3},
        neighbor_gains={"O": 0.02, "C": 0.01},
        final_rescue_gains={"O": 0.08, "C": 0.06},
    )
    assert result["classification"] == "C3"


def test_same_coordinate_local_readout_cannot_establish_persistence() -> None:
    result = classify_checkpoint(
        source_losses={"O": 0.4, "C": 0.3},
        sham_source_effects={"O_sham": 0.01, "C_sham": 0.01},
        rescue_gains={"O": 0.2, "C": 0.1},
        rescue_ratios={"O": 0.5, "C": 1 / 3},
        neighbor_gains={"O": 0.02, "C": 0.01},
        final_rescue_gains=None,
    )
    assert result["classification"] == "C2"
    assert result["final_rescue_gain_mean"] is None


def test_source_sensitive_without_specific_span_rescue_is_c1() -> None:
    result = classify_checkpoint(
        source_losses={"O": 0.4, "C": 0.3},
        sham_source_effects={"O_sham": 0.01, "C_sham": 0.01},
        rescue_gains={"O": 0.04, "C": 0.03},
        rescue_ratios={"O": 0.1, "C": 0.1},
        neighbor_gains={"O": 0.01, "C": 0.01},
    )
    assert result["classification"] == "C1"


def test_checkpoint_is_not_c2_when_a_semantic_direction_has_undefined_ratio() -> None:
    result = classify_checkpoint(
        source_losses={"O": 0.0, "C": 0.2},
        sham_source_effects={"O_sham": 0.01, "C_sham": 0.01},
        rescue_gains={"O": 0.1, "C": 0.1},
        rescue_ratios={"C": 0.5},
        neighbor_gains={"O": 0.01, "C": 0.01},
    )
    assert result["classification"] == "C1"


def test_checkpoint_with_no_defined_rescue_ratio_uses_json_safe_null() -> None:
    result = classify_checkpoint(
        source_losses={"O": 0.0, "C": 0.0},
        sham_source_effects={"O_sham": 0.0, "C_sham": 0.0},
        rescue_gains={"O": 0.0, "C": 0.0},
        rescue_ratios={},
        neighbor_gains={"O": 0.0, "C": 0.0},
    )
    assert result["classification"] == "C0"
    assert result["median_unclipped_rescue_ratio"] is None


def test_repeated_checkpoint_requires_two_nonoverlapping_separated_c2_or_c3() -> None:
    events = [
        {"classification": "C2", "span_start_token": 10, "span_end_token": 12},
        {"classification": "C1", "span_start_token": 30, "span_end_token": 32},
        {"classification": "C3", "span_start_token": 40, "span_end_token": 42},
    ]
    result = repeated_checkpoint_status(events)
    assert result["repeated_checkpoint"]
    assert result["checkpoint_count"] == 2
    assert result["qualifying_pairs"] == [[0, 2]]


def test_repeated_checkpoint_rejects_close_or_overlapping_events() -> None:
    events = [
        {"classification": "C2", "span_start_token": 10, "span_end_token": 15},
        {"classification": "C2", "span_start_token": 20, "span_end_token": 25},
    ]
    assert not repeated_checkpoint_status(events)["repeated_checkpoint"]


def test_lifetime_phenotype_uses_only_frozen_semantic_readout_distances() -> None:
    assert lifetime_phenotype(local_gain=0.2, downstream=[(12, 0.01), (70, 0.02)], final_gain=0.01) == "L-Short"
    assert lifetime_phenotype(local_gain=0.2, downstream=[(40, 0.08)], final_gain=0.01) == "L-Medium"
    assert lifetime_phenotype(local_gain=0.2, downstream=[(70, 0.08)], final_gain=0.01) == "L-Persistent"
    assert lifetime_phenotype(local_gain=0.2, downstream=[(20, 0.01)], final_gain=0.08) == "L-Persistent"


@pytest.mark.parametrize(
    "direct,prior,joint,expected",
    [
        (0.1, 0.01, 0.11, "R-Direct"),
        (0.01, 0.1, 0.11, "R-Inherited"),
        (0.1, 0.1, 0.2, "R-Mixed"),
        (0.01, 0.01, 0.1, "R-Redundant"),
        (0.01, 0.01, 0.01, "R-Unresolved"),
    ],
)
def test_route_phenotype_uses_fixed_short_history_as_prior_route(
    direct: float, prior: float, joint: float, expected: str,
) -> None:
    assert route_phenotype(
        direct_deficit=direct,
        short_history_deficit=prior,
        joint_deficit=joint,
    ) == expected
