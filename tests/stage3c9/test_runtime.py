from __future__ import annotations

import pytest

from visual_reasoning.stage3c9.runtime import (
    absolute_reasoning_token_position,
    validate_checkpoint_coordinates,
    validate_rescue_positions,
    validate_route_coordinates,
)


def test_zero_based_reasoning_index_maps_after_the_full_prompt() -> None:
    assert absolute_reasoning_token_position(prompt_length=100, token_index=0) == 100
    assert absolute_reasoning_token_position(prompt_length=100, token_index=20) == 120
    with pytest.raises(ValueError):
        absolute_reasoning_token_position(prompt_length=100, token_index=-1)


def test_checkpoint_coordinates_require_exact_pre_span_source_window() -> None:
    result = validate_checkpoint_coordinates(
        span_generated_indices=[20, 21],
        source_window_generated_indices=list(range(12, 20)),
        readout_generated_index=25,
    )
    assert result["source_window_width"] == 8
    assert result["span_width"] == 2
    assert result["first_downstream_query"] == 22


@pytest.mark.parametrize(
    "span,window,readout",
    [
        ([20, 21], list(range(13, 20)), 25),
        ([20, 21], list(range(12, 21)), 25),
        ([20, 22], list(range(12, 20)), 25),
        ([20, 21], list(range(12, 20)), 21),
    ],
)
def test_checkpoint_coordinates_reject_nonprospective_or_nondownstream_layouts(span, window, readout) -> None:
    with pytest.raises(ValueError):
        validate_checkpoint_coordinates(
            span_generated_indices=span,
            source_window_generated_indices=window,
            readout_generated_index=readout,
        )


def test_rescue_positions_may_be_event_single_token_or_matched_neighbor() -> None:
    assert validate_rescue_positions([20, 21], readout_generated_index=25)["first_downstream_query"] == 22
    assert validate_rescue_positions([20], readout_generated_index=25)["first_downstream_query"] == 21
    assert validate_rescue_positions([18, 19], readout_generated_index=25)["first_downstream_query"] == 20


def test_rescue_positions_must_be_contiguous_and_precede_readout() -> None:
    with pytest.raises(ValueError):
        validate_rescue_positions([18, 20], readout_generated_index=25)
    with pytest.raises(ValueError):
        validate_rescue_positions([24, 25], readout_generated_index=25)


def test_route_coordinates_freeze_a_span_short_history_and_b_w8() -> None:
    result = validate_route_coordinates(
        event_a_span=[20, 21],
        event_b_span=[60, 61],
        readout_generated_index=65,
    )
    assert result["prior_checkpoint_positions"] == [20, 21]
    assert result["short_history_positions"] == list(range(20, 30))
    assert result["direct_w8_query_positions"] == list(range(52, 60))
    assert result["separation"] == 40


def test_route_coordinates_reject_close_or_overlapping_events() -> None:
    with pytest.raises(ValueError):
        validate_route_coordinates(
            event_a_span=[20, 21], event_b_span=[40, 41], readout_generated_index=45,
        )
