from __future__ import annotations

import pytest
import torch

from visual_reasoning.stage3c3r.runtime import apply_source_contribution_gain


def fixture_tensors() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    attention = torch.tensor(
        [[
            [[0.5, 0.3, 0.2], [0.2, 0.5, 0.3]],
            [[0.1, 0.6, 0.3], [0.4, 0.1, 0.5]],
            [[0.2, 0.2, 0.6], [0.3, 0.3, 0.4]],
        ]],
        dtype=torch.float32,
    )
    value = torch.arange(1 * 3 * 3 * 2, dtype=torch.float32).reshape(1, 3, 3, 2)
    output = torch.einsum("bhqk,bhkd->bqhd", attention, value)
    return output, attention, value


def test_lambda_one_is_exact_native_and_partition_closes() -> None:
    output, attention, value = fixture_tensors()
    patched, contribution, audit = apply_source_contribution_gain(
        output,
        attention,
        value,
        source_positions=[0, 1],
        selected_heads=[0, 2],
        query_position=1,
        gain=1.0,
    )

    assert torch.equal(patched, output)
    assert contribution.shape == (1, 2, 2)
    assert audit["partition_max_abs_error"] == 0.0
    assert audit["lambda_one_exact"] is True


def test_lambda_zero_removes_only_selected_source_contribution() -> None:
    output, attention, value = fixture_tensors()
    patched, contribution, audit = apply_source_contribution_gain(
        output,
        attention,
        value,
        source_positions=[0, 1],
        selected_heads=[0, 2],
        query_position=1,
        gain=0.0,
    )
    expected = output.clone()
    expected[:, 1, [0, 2], :] -= contribution

    assert torch.equal(patched, expected)
    assert torch.equal(patched[:, 1, 1, :], output[:, 1, 1, :])
    assert torch.equal(patched[:, 0, :, :], output[:, 0, :, :])
    assert audit["lambda_zero_exact"] is True
    assert audit["nonselected_head_max_abs_delta"] == 0.0
    assert audit["other_position_max_abs_delta"] == 0.0


def test_half_gain_changes_selected_contribution_linearly() -> None:
    output, attention, value = fixture_tensors()
    patched, contribution, audit = apply_source_contribution_gain(
        output,
        attention,
        value,
        source_positions=[0],
        selected_heads=[1],
        query_position=1,
        gain=0.5,
    )

    assert torch.allclose(patched[:, 1, [1], :], output[:, 1, [1], :] - 0.5 * contribution)
    assert audit["selected_head_expected_max_abs_error"] == 0.0
    assert audit["qkv_directly_modified"] is False
    assert audit["attention_directly_modified"] is False


@pytest.mark.parametrize("gain", [-0.1, float("nan"), float("inf")])
def test_invalid_gain_is_rejected(gain: float) -> None:
    output, attention, value = fixture_tensors()
    with pytest.raises(ValueError):
        apply_source_contribution_gain(
            output,
            attention,
            value,
            source_positions=[0],
            selected_heads=[0],
            query_position=0,
            gain=gain,
        )


def test_out_of_range_source_and_head_are_rejected() -> None:
    output, attention, value = fixture_tensors()
    with pytest.raises(ValueError):
        apply_source_contribution_gain(
            output, attention, value,
            source_positions=[3], selected_heads=[0], query_position=0, gain=0.0,
        )
    with pytest.raises(ValueError):
        apply_source_contribution_gain(
            output, attention, value,
            source_positions=[0], selected_heads=[3], query_position=0, gain=0.0,
        )


def test_bfloat16_partition_is_audited_in_float32() -> None:
    output, attention, value = fixture_tensors()
    output = output.to(torch.bfloat16)
    attention = attention.to(torch.bfloat16)
    value = value.to(torch.bfloat16)

    patched, _, audit = apply_source_contribution_gain(
        output,
        attention,
        value,
        source_positions=[0, 1],
        selected_heads=[0, 2],
        query_position=1,
        gain=0.25,
    )

    assert patched.dtype == torch.bfloat16
    assert audit["partition_compute_dtype"] == "float32"
    assert audit["partition_max_abs_error"] <= 1e-6
    assert audit["selected_head_expected_max_abs_error"] == 0.0
