from __future__ import annotations

import math

import pytest
import torch

from visual_reasoning.stage3c1.metrics import (
    build_source_partition,
    class_logsumexp,
    reconstruct_attention_rows,
    source_attention_statistics,
    source_value_contributions,
    wo_head_contributions,
)


def test_source_partition_is_disjoint_and_closes_over_allowed_prefix() -> None:
    partition = build_source_partition(
        current_position=11,
        prompt_length=8,
        visual_positions=[2, 3],
        question_positions=[5, 6],
        special_prompt_positions=[0, 1, 4, 7],
    )

    assert partition == {
        "visual": [2, 3],
        "prompt_question": [5, 6],
        "previous_reasoning": [8, 9, 10],
        "special_other": [0, 1, 4, 7, 11],
    }
    flattened = [position for positions in partition.values() for position in positions]
    assert sorted(flattened) == list(range(12))
    assert len(flattened) == len(set(flattened))


def test_source_partition_rejects_overlapping_declared_prompt_groups() -> None:
    with pytest.raises(ValueError, match="disjoint"):
        build_source_partition(
            current_position=5,
            prompt_length=4,
            visual_positions=[1, 2],
            question_positions=[2, 3],
            special_prompt_positions=[0],
        )


def test_reconstructed_attention_matches_reference_softmax_and_head_output() -> None:
    query = torch.tensor([[[[1.0, 0.0]], [[0.0, 2.0]]]])
    key = torch.tensor(
        [[[[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]], [[2.0, 0.0], [0.0, 1.0], [1.0, -1.0]]]]
    )
    value = torch.tensor(
        [[[[1.0, 0.0], [0.0, 2.0], [3.0, 1.0]], [[-1.0, 1.0], [2.0, 2.0], [4.0, 0.0]]]]
    )
    mask = torch.tensor([[[[0.0, 0.0, -1.0e9]]]])

    result = reconstruct_attention_rows(
        query=query,
        key=key,
        value=value,
        attention_mask=mask,
        scaling=0.5,
        num_key_value_groups=1,
    )

    expected_logits = torch.matmul(query, key.transpose(2, 3)) * 0.5 + mask
    expected_weights = torch.softmax(expected_logits.float(), dim=-1).to(query.dtype)
    expected_output = torch.matmul(expected_weights, value)
    assert torch.equal(result["raw_dot"], torch.matmul(query, key.transpose(2, 3)))
    assert torch.equal(result["final_logits"], expected_logits)
    assert torch.equal(result["attention"], expected_weights)
    assert torch.equal(result["head_output"], expected_output)


def test_attention_and_value_source_statistics_preserve_mass_and_vectors() -> None:
    attention = torch.tensor([[0.1, 0.2, 0.3, 0.4], [0.4, 0.3, 0.2, 0.1]])
    values = torch.tensor(
        [
            [[1.0, 0.0], [0.0, 1.0], [2.0, 0.0], [0.0, 2.0]],
            [[1.0, 1.0], [2.0, 0.0], [0.0, 2.0], [1.0, -1.0]],
        ]
    )
    groups = {"left": [0, 1], "right": [2, 3]}

    attention_stats = source_attention_statistics(attention, groups)
    contributions = source_value_contributions(attention, values, groups)

    assert attention_stats["left"][0]["mass"] == pytest.approx(0.3)
    assert attention_stats["right"][1]["density"] == pytest.approx(0.15)
    for head in range(2):
        assert sum(attention_stats[group][head]["mass"] for group in groups) == pytest.approx(1.0)
        reconstructed = contributions["left"][head]["vector"] + contributions["right"][head]["vector"]
        expected = torch.sum(attention[head, :, None] * values[head], dim=0)
        assert torch.allclose(reconstructed, expected)


def test_class_logsumexp_uses_only_declared_positions() -> None:
    logits = torch.tensor([[0.0, 1.0, 2.0], [2.0, 0.0, -1.0]])
    result = class_logsumexp(logits, {"first_two": [0, 1], "last": [2]})
    assert result["first_two"] == pytest.approx(torch.logsumexp(logits[:, :2], dim=-1).tolist())
    assert result["last"] == pytest.approx([2.0, -1.0])


def test_wo_head_slices_sum_to_zero_filled_selected_projection() -> None:
    head_vectors = torch.tensor([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])
    weight = torch.arange(24, dtype=torch.float32).reshape(4, 6) / 10.0
    result = wo_head_contributions(
        head_vectors=head_vectors,
        wo_weight=weight,
        selected_heads=[0, 2],
    )

    zero_filled = torch.zeros_like(head_vectors)
    zero_filled[[0, 2]] = head_vectors[[0, 2]]
    expected = torch.nn.functional.linear(zero_filled.reshape(-1), weight)
    assert torch.allclose(result["selected_sum"], expected)
    assert torch.allclose(result["per_head"][0] + result["per_head"][2], expected)
    assert math.isfinite(float(result["selected_sum"].norm()))
