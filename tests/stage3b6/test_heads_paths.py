from __future__ import annotations

import torch
from transformers.models.qwen3_vl import modeling_qwen3_vl as qwen_impl

from visual_reasoning.stage3b6.heads import (
    CaptureQwenHeadState,
    HybridQueryHeadIntervention,
    gqa_query_to_kv_map,
    splice_query_head_outputs,
    swap_kv_positions,
)
from visual_reasoning.stage3b6.paths import build_source_token_groups


def test_gqa_mapping_keeps_logical_query_heads_distinct() -> None:
    mapping = gqa_query_to_kv_map(query_heads=32, kv_heads=8)
    assert mapping == [head // 4 for head in range(32)]
    assert len(mapping) == 32
    assert {mapping.count(group) for group in range(8)} == {4}


def test_splice_changes_only_requested_query_heads_at_current_position() -> None:
    recipient = torch.arange(24, dtype=torch.float32).reshape(1, 3, 4, 2)
    swapped = recipient + 100.0
    merged, audit = splice_query_head_outputs(
        recipient,
        swapped,
        position=1,
        selected_heads=[1, 3],
    )

    assert torch.equal(merged[:, 0], recipient[:, 0])
    assert torch.equal(merged[:, 2], recipient[:, 2])
    assert torch.equal(merged[:, 1, 0], recipient[:, 1, 0])
    assert torch.equal(merged[:, 1, 2], recipient[:, 1, 2])
    assert torch.equal(merged[:, 1, 1], swapped[:, 1, 1])
    assert torch.equal(merged[:, 1, 3], swapped[:, 1, 3])
    assert audit["selected_query_heads"] == [1, 3]
    assert audit["changed_query_heads"] == [1, 3]
    assert audit["changed_sequence_positions"] == [1]
    assert audit["nonselected_head_max_abs_delta"] == 0.0


def test_source_groups_are_frozen_by_token_layout_not_attention() -> None:
    groups = build_source_token_groups(
        prompt_length=10,
        current_absolute_position=13,
        visual_positions=[2, 3],
        eligible_prefix_positions=[4, 5, 6, 7, 8, 9],
    )
    assert groups["V"] == [2, 3]
    assert groups["P"] == [4, 5, 6, 7, 8, 9]
    assert groups["R"] == [10, 11, 12]
    assert groups["all"] == [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    assert 13 not in groups["all"]
    assert set(groups["V"]).isdisjoint(groups["P"])
    assert set(groups["P"]).isdisjoint(groups["R"])


def test_source_groups_reject_overlap_and_current_token_leakage() -> None:
    try:
        build_source_token_groups(
            prompt_length=10,
            current_absolute_position=13,
            visual_positions=[2, 3],
            eligible_prefix_positions=[3, 4],
        )
    except ValueError as error:
        assert "disjoint" in str(error)
    else:
        raise AssertionError("overlapping V/P groups must fail")


def test_kv_swap_changes_only_frozen_source_positions() -> None:
    recipient_k = torch.arange(40, dtype=torch.float32).reshape(1, 2, 5, 4)
    recipient_v = recipient_k + 50.0
    source_k = recipient_k + 100.0
    source_v = recipient_v + 200.0
    key, value, audit = swap_kv_positions(
        recipient_k,
        recipient_v,
        source_k,
        source_v,
        positions=[1, 3],
    )
    assert torch.equal(key[:, :, [1, 3]], source_k[:, :, [1, 3]])
    assert torch.equal(value[:, :, [1, 3]], source_v[:, :, [1, 3]])
    assert torch.equal(key[:, :, [0, 2, 4]], recipient_k[:, :, [0, 2, 4]])
    assert torch.equal(value[:, :, [0, 2, 4]], recipient_v[:, :, [0, 2, 4]])
    assert audit["assigned_positions"] == [1, 3]
    assert audit["nonassigned_key_max_abs_delta"] == 0.0
    assert audit["nonassigned_value_max_abs_delta"] == 0.0


class _IdentityNorm(torch.nn.Module):
    def forward(self, value: torch.Tensor) -> torch.Tensor:
        return value


class _FakeConfig:
    _attn_implementation = "eager"


class _FakeQwenAttention(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.layer_idx = 0
        self.head_dim = 2
        self.num_key_value_groups = 2
        self.scaling = self.head_dim**-0.5
        self.attention_dropout = 0.0
        self.training = False
        self.config = _FakeConfig()
        self.q_proj = torch.nn.Linear(8, 8, bias=False)
        self.k_proj = torch.nn.Linear(8, 4, bias=False)
        self.v_proj = torch.nn.Linear(8, 4, bias=False)
        self.o_proj = torch.nn.Linear(8, 8, bias=False)
        self.q_norm = _IdentityNorm()
        self.k_norm = _IdentityNorm()
        torch.manual_seed(7)
        for parameter in self.parameters():
            torch.nn.init.uniform_(parameter, -0.2, 0.2)

    def forward(
        self,
        hidden_states: torch.Tensor,
        position_embeddings: tuple[torch.Tensor, torch.Tensor],
        attention_mask: torch.Tensor | None,
        past_key_values=None,
        **kwargs,
    ):
        shape = hidden_states.shape[:-1]
        hidden_shape = (*shape, -1, self.head_dim)
        query = self.q_proj(hidden_states).view(hidden_shape).transpose(1, 2)
        key = self.k_proj(hidden_states).view(hidden_shape).transpose(1, 2)
        value = self.v_proj(hidden_states).view(hidden_shape).transpose(1, 2)
        query, key = qwen_impl.apply_rotary_pos_emb(
            query, key, *position_embeddings
        )
        output, weights = qwen_impl.eager_attention_forward(
            self,
            query,
            key,
            value,
            attention_mask,
            scaling=self.scaling,
            dropout=0.0,
        )
        return self.o_proj(output.reshape(*shape, -1).contiguous()), weights


class _FakeLayer(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.self_attn = _FakeQwenAttention()


class _FakeLanguage(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.layers = torch.nn.ModuleList([_FakeLayer()])


class _FakeInner(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.language_model = _FakeLanguage()


class _FakeModel(torch.nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.model = _FakeInner()


def _attention_inputs():
    hidden = torch.arange(32, dtype=torch.float32).reshape(1, 4, 8) / 10.0
    cos = torch.ones((1, 4, 2), dtype=torch.float32)
    sin = torch.zeros((1, 4, 2), dtype=torch.float32)
    mask = torch.full((1, 1, 4, 4), float("-inf"))
    mask = torch.triu(mask, diagonal=1)
    return hidden, (cos, sin), mask


def test_qwen_reconstruction_is_transparent_and_self_swap_is_exact() -> None:
    model = _FakeModel()
    attention = model.model.language_model.layers[0].self_attn
    hidden, positions, mask = _attention_inputs()
    baseline = attention(hidden, positions, mask)[0]

    capture = CaptureQwenHeadState(model=model, layer_index=0, position=2)
    with capture:
        reconstructed = attention(hidden, positions, mask)[0]
    state = capture.complete_state()
    assert torch.equal(reconstructed, baseline)
    assert state["key"].shape == (1, 2, 4, 2)
    assert state["value"].shape == (1, 2, 4, 2)

    patch = HybridQueryHeadIntervention(
        model=model,
        layer_index=0,
        position=2,
        selected_heads=[1],
        source_key=state["key"],
        source_value=state["value"],
        source_positions=[0, 1],
    )
    with patch:
        self_swapped = attention(hidden, positions, mask)[0]
    assert torch.equal(self_swapped, baseline)
    assert patch.audit[0]["selected_query_heads"] == [1]
    assert patch.audit[0]["nonselected_head_max_abs_delta"] == 0.0
