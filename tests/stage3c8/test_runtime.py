from __future__ import annotations

import pytest
import torch
from types import SimpleNamespace

from visual_reasoning.stage3c8.runtime import (
    patch_prefill_cache_positions,
    replace_cache_positions,
    summarize_cache_state_difference,
)


def test_multi_position_kv_patch_changes_only_selected_positions() -> None:
    key = torch.zeros((1, 2, 8, 3))
    value = torch.zeros_like(key)
    source_key = torch.stack((torch.full((1, 2, 3), 2.0), torch.full((1, 2, 3), 5.0)), dim=2)
    source_value = source_key + 10
    patched_k, patched_v, audit = replace_cache_positions(
        key,
        value,
        source_key=source_key,
        source_value=source_value,
        positions=[2, 5],
        mode="KV",
        visual_positions=[0, 1],
        current_query_position=7,
    )
    assert torch.equal(patched_k[:, :, [2, 5], :], source_key)
    assert torch.equal(patched_v[:, :, [2, 5], :], source_value)
    assert torch.count_nonzero(patched_k[:, :, [0, 1, 3, 4, 6, 7], :]) == 0
    assert audit["positions_replaced"] == [2, 5]
    assert audit["nonselected_key_max_abs_delta"] == 0.0
    assert audit["nonselected_value_max_abs_delta"] == 0.0


def test_multi_position_v_only_keeps_all_keys_exact() -> None:
    key = torch.randn((1, 2, 6, 4))
    value = torch.randn_like(key)
    source = torch.randn((1, 2, 2, 4))
    patched_k, patched_v, audit = replace_cache_positions(
        key, value, source_key=source, source_value=source,
        positions=[1, 4], mode="V", current_query_position=5,
    )
    assert torch.equal(patched_k, key)
    assert torch.equal(patched_v[:, :, [1, 4], :], source)
    assert audit["unselected_component_key_max_abs_delta"] == 0.0


def test_multi_position_patch_rejects_visual_or_current_query_positions() -> None:
    tensor = torch.zeros((1, 2, 6, 4))
    source = torch.zeros((1, 2, 1, 4))
    with pytest.raises(ValueError, match="visual"):
        replace_cache_positions(
            tensor, tensor, source_key=source, source_value=source,
            positions=[1], mode="KV", visual_positions=[1], current_query_position=5,
        )
    with pytest.raises(ValueError, match="current query"):
        replace_cache_positions(
            tensor, tensor, source_key=source, source_value=source,
            positions=[5], mode="KV", current_query_position=5,
        )


def test_prefill_cache_patch_supports_component_modes() -> None:
    recipient = SimpleNamespace(layers=[SimpleNamespace(keys=torch.zeros((1, 2, 5, 3)), values=torch.zeros((1, 2, 5, 3)))])
    source = SimpleNamespace(layers=[SimpleNamespace(keys=torch.full((1, 2, 5, 3), 2.0), values=torch.full((1, 2, 5, 3), 7.0))])
    patched, audit = patch_prefill_cache_positions(recipient, source, positions=[1, 3], mode="V")
    assert torch.equal(patched.layers[0].keys, recipient.layers[0].keys)
    assert torch.all(patched.layers[0].values[:, :, [1, 3], :] == 7)
    assert torch.count_nonzero(patched.layers[0].values[:, :, [0, 2, 4], :]) == 0
    assert audit["mode"] == "V"
    assert audit["positions"] == [1, 3]


def test_prefill_cache_patch_rejects_forbidden_visual_positions() -> None:
    cache = SimpleNamespace(layers=[SimpleNamespace(keys=torch.zeros((1, 2, 5, 3)), values=torch.zeros((1, 2, 5, 3)))])
    with pytest.raises(ValueError, match="forbidden"):
        patch_prefill_cache_positions(cache, cache, positions=[2], mode="KV", forbidden_positions=[2])


def test_cache_state_difference_reports_k_and_v_separately() -> None:
    native = {0: (torch.zeros(1, 2, 1, 3), torch.zeros(1, 2, 1, 3))}
    suppressed = {0: (torch.ones(1, 2, 1, 3), torch.full((1, 2, 1, 3), 2.0))}
    summary = summarize_cache_state_difference(native, suppressed)
    assert summary["layers"] == [0]
    assert summary["K_l2"] == pytest.approx(6 ** 0.5)
    assert summary["V_l2"] == pytest.approx(24 ** 0.5)
    assert summary["any_difference"]
