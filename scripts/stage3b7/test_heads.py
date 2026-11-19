from __future__ import annotations

import pytest
import torch
from transformers.models.qwen3_vl import modeling_qwen3_vl as qwen_impl

from visual_reasoning.stage3b6.heads import CaptureQwenHeadState
from visual_reasoning.stage3b7.heads import HybridQueryHeadKVIntervention


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
        torch.manual_seed(71)
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
        query, key = qwen_impl.apply_rotary_pos_emb(query, key, *position_embeddings)
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


def _inputs(offset: float = 0.0):
    hidden = torch.arange(32, dtype=torch.float32).reshape(1, 4, 8) / 10.0 + offset
    cos = torch.ones((1, 4, 2), dtype=torch.float32)
    sin = torch.zeros((1, 4, 2), dtype=torch.float32)
    mask = torch.full((1, 1, 4, 4), float("-inf"))
    return hidden, (cos, sin), torch.triu(mask, diagonal=1)


def _capture(model: _FakeModel, offset: float):
    attention = model.model.language_model.layers[0].self_attn
    hidden, positions, mask = _inputs(offset)
    capture = CaptureQwenHeadState(model=model, layer_index=0, position=2)
    with capture:
        output = attention(hidden, positions, mask)[0]
    return hidden, positions, mask, output, capture.complete_state()


@pytest.mark.parametrize(
    ("mode", "key_swapped", "value_swapped"),
    [("K", True, False), ("V", False, True), ("KV", True, True)],
)
def test_query_head_kv_intervention_is_component_and_head_selective(
    mode: str, key_swapped: bool, value_swapped: bool
) -> None:
    model = _FakeModel()
    attention = model.model.language_model.layers[0].self_attn
    hidden, positions, mask, baseline, recipient = _capture(model, 0.0)
    _, _, _, _, donor = _capture(model, 0.6)
    patch = HybridQueryHeadKVIntervention(
        model=model,
        layer_index=0,
        position=2,
        selected_heads=[1],
        source_key=donor["key"],
        source_value=donor["value"],
        source_positions=[0, 1],
        mode=mode,
    )
    with patch:
        changed = attention(hidden, positions, mask)[0]
    audit = patch.audit[0]
    assert audit["kv_composition"]["key_swapped"] is key_swapped
    assert audit["kv_composition"]["value_swapped"] is value_swapped
    assert audit["kv_composition"]["unswapped_key_max_abs_delta"] in (None, 0.0)
    assert audit["kv_composition"]["unswapped_value_max_abs_delta"] in (None, 0.0)
    assert audit["nonselected_head_max_abs_delta"] == 0.0
    assert audit["query_head_selectivity_valid"]
    assert audit["source_group_isolation_valid"]
    assert not torch.equal(changed, baseline)


@pytest.mark.parametrize("mode", ["K", "V", "KV"])
def test_self_intervention_is_exact_for_every_kv_mode(mode: str) -> None:
    model = _FakeModel()
    attention = model.model.language_model.layers[0].self_attn
    hidden, positions, mask, baseline, recipient = _capture(model, 0.0)
    patch = HybridQueryHeadKVIntervention(
        model=model,
        layer_index=0,
        position=2,
        selected_heads=[1, 3],
        source_key=recipient["key"],
        source_value=recipient["value"],
        source_positions=[0, 1],
        mode=mode,
    )
    with patch:
        self_swapped = attention(hidden, positions, mask)[0]
    assert torch.equal(self_swapped, baseline)
    assert patch.audit[0]["query_head_selectivity_valid"]
    assert patch.audit[0]["source_group_isolation_valid"]
