from __future__ import annotations

import torch

from visual_reasoning.stage3c5.carriers import replace_token_kv_positions


def test_token_kv_replacement_changes_only_selected_positions() -> None:
    key = torch.arange(1 * 2 * 6 * 3, dtype=torch.float32).reshape(1, 2, 6, 3)
    value = key + 100.0
    donor_key = torch.full((1, 2, 2, 3), -7.0)
    donor_value = torch.full((1, 2, 2, 3), 9.0)

    patched_key, patched_value, audit = replace_token_kv_positions(
        key, value,
        source_key=donor_key,
        source_value=donor_value,
        positions=[1, 4],
    )

    assert torch.equal(patched_key[:, :, [1, 4], :], donor_key)
    assert torch.equal(patched_value[:, :, [1, 4], :], donor_value)
    assert torch.equal(patched_key[:, :, [0, 2, 3, 5], :], key[:, :, [0, 2, 3, 5], :])
    assert torch.equal(patched_value[:, :, [0, 2, 3, 5], :], value[:, :, [0, 2, 3, 5], :])
    assert audit["nonselected_key_max_abs_delta"] == 0.0
    assert audit["nonselected_value_max_abs_delta"] == 0.0
    assert audit["positions_replaced"] == [1, 4]


def test_self_token_kv_replacement_is_exact_noop() -> None:
    key = torch.randn(1, 2, 5, 4)
    value = torch.randn(1, 2, 5, 4)
    positions = [0, 3]
    patched_key, patched_value, audit = replace_token_kv_positions(
        key, value,
        source_key=key[:, :, positions, :].clone(),
        source_value=value[:, :, positions, :].clone(),
        positions=positions,
    )
    assert torch.equal(patched_key, key)
    assert torch.equal(patched_value, value)
    assert audit["source_key_exact_recipient_match"] is True
    assert audit["source_value_exact_recipient_match"] is True
