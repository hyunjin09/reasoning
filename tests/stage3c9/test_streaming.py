from __future__ import annotations

from types import SimpleNamespace

import torch

from visual_reasoning.stage3c9.streaming import (
    StreamingPrefixState,
    clone_streaming_state,
    fixed_chunk_ranges,
    patch_streaming_state,
    release_cuda_allocator_cache,
    snapshot_cache_positions,
)


class _Cache:
    def __init__(self, key: torch.Tensor, value: torch.Tensor) -> None:
        self.layers = [SimpleNamespace(keys=key, values=value)]

    def get_seq_length(self) -> int:
        return int(self.layers[0].keys.shape[2])


def _state(offset: float) -> StreamingPrefixState:
    key = torch.arange(1 * 2 * 8 * 3, dtype=torch.float32).reshape(1, 2, 8, 3) + offset
    value = key + 100
    return StreamingPrefixState(
        cache=_Cache(key, value),
        rope_deltas=torch.zeros((1, 1), dtype=torch.long),
        prompt_length=4,
        generated_length=4,
        last_logits=torch.tensor([1.0, 2.0]),
    )


def test_streaming_clone_does_not_alias_cache_or_logits() -> None:
    source = _state(0)
    cloned = clone_streaming_state(source)
    assert cloned.cache.layers[0].keys.data_ptr() != source.cache.layers[0].keys.data_ptr()
    assert cloned.last_logits.data_ptr() != source.last_logits.data_ptr()


def test_streaming_patch_replaces_only_requested_nonvisual_positions() -> None:
    recipient, donor = _state(0), _state(10)
    patched, audit = patch_streaming_state(
        recipient,
        donor=donor,
        generated_positions=[1, 2],
        visual_positions=[0, 1, 2, 3],
    )
    selected = [5, 6]
    keep = [0, 1, 2, 3, 4, 7]
    assert torch.equal(
        patched.cache.layers[0].keys[:, :, selected, :],
        donor.cache.layers[0].keys[:, :, selected, :],
    )
    assert torch.equal(
        patched.cache.layers[0].keys[:, :, keep, :],
        recipient.cache.layers[0].keys[:, :, keep, :],
    )
    assert audit["patch_generated_indices"] == [1, 2]
    assert audit["first_downstream_absolute_query"] == 8
    assert audit["layer_audits"][0]["native_kv_head_count"] == 2


def test_streaming_patch_can_select_k_only_without_changing_values() -> None:
    recipient, donor = _state(0), _state(10)
    patched, audit = patch_streaming_state(
        recipient,
        donor=donor,
        generated_positions=[1],
        visual_positions=[0, 1, 2, 3],
        selected_layers=[0],
        mode="K",
    )
    assert torch.equal(patched.cache.layers[0].keys[:, :, 5, :], donor.cache.layers[0].keys[:, :, 5, :])
    assert torch.equal(patched.cache.layers[0].values, recipient.cache.layers[0].values)
    assert audit["cache_mode"] == "K"
    assert audit["layer_audits"][0]["unselected_component_value_max_abs_delta"] == 0.0


def test_snapshot_uses_native_gqa_sequence_axis() -> None:
    state = _state(0)
    result = snapshot_cache_positions(state, absolute_positions=[4, 7])
    assert result[0][0].shape == (1, 2, 2, 3)
    assert torch.equal(result[0][1], state.cache.layers[0].values[:, :, [4, 7], :])


def test_allocator_release_is_explicit_and_disabled_by_default(monkeypatch) -> None:
    calls = []
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(torch.cuda, "empty_cache", lambda: calls.append("released"))
    release_cuda_allocator_cache()
    assert calls == []
    release_cuda_allocator_cache(enabled=True)
    assert calls == ["released"]


def test_fixed_chunk_ranges_do_not_depend_on_sparse_suppression_rows() -> None:
    expected = [(0, 8), (8, 16), (16, 20)]
    assert fixed_chunk_ranges(start=0, end=20, chunk_size=8) == expected
    assert fixed_chunk_ranges(start=0, end=20, chunk_size=8, mandatory_boundaries=[]) == expected


def test_fixed_chunk_ranges_apply_condition_invariant_patch_boundary() -> None:
    assert fixed_chunk_ranges(
        start=0, end=20, chunk_size=8, mandatory_boundaries=[13]
    ) == [(0, 8), (8, 13), (13, 20)]
