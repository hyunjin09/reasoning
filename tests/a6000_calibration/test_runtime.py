from __future__ import annotations

import pytest
import torch

from visual_reasoning.a6000_calibration.runtime import (
    replace_selected_cache_positions,
    tensor_pair_max_abs_delta,
)


def test_replace_selected_cache_positions_changes_only_requested_layers_and_positions() -> None:
    recipient = [
        (torch.zeros(1, 2, 5, 3), torch.zeros(1, 2, 5, 3)),
        (torch.zeros(1, 2, 5, 3), torch.zeros(1, 2, 5, 3)),
    ]
    donor = [
        (torch.full((1, 2, 5, 3), 2.0), torch.full((1, 2, 5, 3), 3.0)),
        (torch.full((1, 2, 5, 3), 4.0), torch.full((1, 2, 5, 3), 5.0)),
    ]
    audit = replace_selected_cache_positions(
        recipient,
        donor,
        absolute_positions=[2, 3],
        selected_layers=[1],
        visual_positions=[0, 1],
    )
    assert torch.count_nonzero(recipient[0][0]) == 0
    assert torch.all(recipient[1][0][:, :, 2:4, :] == 4)
    assert torch.all(recipient[1][1][:, :, 2:4, :] == 5)
    assert torch.count_nonzero(recipient[1][0][:, :, :2, :]) == 0
    assert audit[1]["nonselected_key_max_abs_delta"] == 0.0
    assert audit[1]["selected_key_exact_expected"] is True


def test_replace_selected_cache_positions_rejects_visual_overlap() -> None:
    tensors = [(torch.zeros(1, 2, 5, 3), torch.zeros(1, 2, 5, 3))]
    with pytest.raises(ValueError, match="visual"):
        replace_selected_cache_positions(
            tensors,
            tensors,
            absolute_positions=[1],
            selected_layers=[0],
            visual_positions=[1],
        )


def test_tensor_pair_max_abs_delta_covers_keys_and_values() -> None:
    left = {0: (torch.zeros(1), torch.zeros(1))}
    right = {0: (torch.tensor([0.25]), torch.tensor([-0.5]))}
    result = tensor_pair_max_abs_delta(left, right)
    assert result["key_max_abs_delta"] == 0.25
    assert result["value_max_abs_delta"] == 0.5
    assert result["maximum_abs_delta"] == 0.5
