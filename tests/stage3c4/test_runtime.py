from __future__ import annotations

import pytest
import torch

from visual_reasoning.stage3c4.runtime import apply_source_contribution_window


def fixture_tensors() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    attention = torch.tensor(
        [[
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.2, 0.8, 0.0, 0.0],
                [0.1, 0.2, 0.7, 0.0],
                [0.1, 0.2, 0.3, 0.4],
            ],
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.4, 0.6, 0.0, 0.0],
                [0.2, 0.3, 0.5, 0.0],
                [0.4, 0.1, 0.2, 0.3],
            ],
        ]],
        dtype=torch.float32,
    )
    value = torch.arange(1 * 2 * 4 * 3, dtype=torch.float32).reshape(1, 2, 4, 3)
    output = torch.einsum("bhqk,bhkd->bqhd", attention, value)
    return output, attention, value


def test_zero_gain_removes_only_selected_sources_heads_and_queries() -> None:
    output, attention, value = fixture_tensors()
    patched, contributions, audit = apply_source_contribution_window(
        output,
        attention,
        value,
        source_positions=[0, 1],
        selected_heads=[0],
        query_positions=[2, 3],
        gain=0.0,
    )

    expected = output.clone()
    for position in (2, 3):
        expected[:, position, [0], :] -= contributions[position]

    assert torch.equal(patched, expected)
    assert torch.equal(patched[:, :2], output[:, :2])
    assert torch.equal(patched[:, :, 1], output[:, :, 1])
    assert audit["query_positions"] == [2, 3]
    assert audit["changed_query_positions"] == [2, 3]
    assert audit["outside_window_max_abs_delta"] == 0.0
    assert audit["nonselected_head_max_abs_delta"] == 0.0
    assert audit["lambda_zero_exact"] is True


def test_lambda_one_is_bit_exact_for_multi_query_window() -> None:
    output, attention, value = fixture_tensors()
    patched, _, audit = apply_source_contribution_window(
        output,
        attention,
        value,
        source_positions=[0],
        selected_heads=[0, 1],
        query_positions=[1, 2, 3],
        gain=1.0,
    )

    assert torch.equal(patched, output)
    assert audit["lambda_one_exact"] is True
    assert audit["partition_compute_dtype"] == "float32"


def test_window_requires_unique_in_range_causally_visible_queries() -> None:
    output, attention, value = fixture_tensors()
    with pytest.raises(ValueError):
        apply_source_contribution_window(
            output, attention, value,
            source_positions=[2], selected_heads=[0], query_positions=[1], gain=0.0,
        )
    with pytest.raises(ValueError):
        apply_source_contribution_window(
            output, attention, value,
            source_positions=[0], selected_heads=[0], query_positions=[], gain=0.0,
        )


def test_bfloat16_window_uses_float32_partition() -> None:
    output, attention, value = fixture_tensors()
    patched, _, audit = apply_source_contribution_window(
        output.to(torch.bfloat16),
        attention.to(torch.bfloat16),
        value.to(torch.bfloat16),
        source_positions=[0],
        selected_heads=[0, 1],
        query_positions=[2, 3],
        gain=0.0,
    )

    assert patched.dtype == torch.bfloat16
    assert audit["partition_max_abs_error"] <= 1e-6
    assert audit["all_outputs_finite"] is True


def test_cached_query_rows_use_absolute_causal_coordinates() -> None:
    output, attention, value = fixture_tensors()
    patched, contributions, audit = apply_source_contribution_window(
        output[:, 2:, :, :],
        attention[:, :, 2:, :],
        value,
        source_positions=[0],
        selected_heads=[0, 1],
        query_positions=[0, 1],
        query_position_offset=2,
        gain=0.0,
    )
    assert patched.shape[1] == 2
    assert sorted(contributions) == [2, 3]
    assert audit["query_positions"] == [2, 3]
    assert audit["local_query_positions"] == [0, 1]
    assert audit["changed_query_positions"] == [2, 3]
