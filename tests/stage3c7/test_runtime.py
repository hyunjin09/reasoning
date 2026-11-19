from __future__ import annotations

import pytest
import torch

from visual_reasoning.stage3c7.runtime import replace_prior_cache_entry


@pytest.mark.parametrize("mode", ["K", "V", "KV"])
def test_prior_cache_replacement_is_native_gqa_and_selected_component_only(mode: str) -> None:
    key = torch.arange(1 * 8 * 6 * 4, dtype=torch.float32).reshape(1, 8, 6, 4)
    value = key + 1000.0
    donor_key = torch.full((1, 8, 1, 4), -7.0)
    donor_value = torch.full((1, 8, 1, 4), 9.0)
    patched_key, patched_value, audit = replace_prior_cache_entry(
        key, value, source_key=donor_key, source_value=donor_value,
        tpre_position=3, mode=mode,
    )
    assert patched_key.shape == key.shape
    assert patched_value.shape == value.shape
    assert audit["native_kv_head_count"] == 8
    assert audit["positions_replaced"] == [3]
    assert audit["visual_positions_replaced"] == []
    assert audit["current_query_position_replaced"] is False
    assert torch.equal(patched_key[:, :, [0, 1, 2, 4, 5], :], key[:, :, [0, 1, 2, 4, 5], :])
    assert torch.equal(patched_value[:, :, [0, 1, 2, 4, 5], :], value[:, :, [0, 1, 2, 4, 5], :])
    assert torch.equal(patched_key[:, :, 3:4, :], donor_key if mode in {"K", "KV"} else key[:, :, 3:4, :])
    assert torch.equal(patched_value[:, :, 3:4, :], donor_value if mode in {"V", "KV"} else value[:, :, 3:4, :])


def test_prior_cache_replacement_rejects_fake_query_head_layout() -> None:
    key = torch.zeros(1, 8, 5, 4)
    value = torch.zeros_like(key)
    fake = torch.zeros(1, 32, 1, 4)
    with pytest.raises(ValueError, match="native KV-head"):
        replace_prior_cache_entry(key, value, source_key=fake, source_value=fake, tpre_position=2, mode="KV")


def test_cache_replacement_rejects_visual_or_current_position() -> None:
    key = torch.zeros(1, 8, 5, 4)
    value = torch.zeros_like(key)
    donor = torch.ones(1, 8, 1, 4)
    with pytest.raises(ValueError):
        replace_prior_cache_entry(key, value, source_key=donor, source_value=donor, tpre_position=2, mode="KV", visual_positions=[2])
    with pytest.raises(ValueError):
        replace_prior_cache_entry(key, value, source_key=donor, source_value=donor, tpre_position=4, mode="KV", current_query_position=4)
