from types import SimpleNamespace

import torch
from transformers.modeling_utils import ALL_ATTENTION_FUNCTIONS

from visual_reasoning.stage3b2.switching import (
    _AttentionInterfaceContext,
    switched_eager_attention,
    valid_switch_audit,
)


def _module() -> SimpleNamespace:
    return SimpleNamespace(num_key_value_groups=1, layer_idx=0, training=False)


def test_switch_changes_only_queries_at_or_after_predictor_boundary() -> None:
    query = torch.tensor([[[[1.0], [1.0], [1.0], [1.0]]]])
    key = torch.tensor([[[[0.0], [1.0], [0.5], [0.25]]]])
    value = torch.tensor([[[[0.0], [1.0], [2.0], [3.0]]]])
    source_key = torch.tensor([[[[9.0]]]])
    source_value = torch.tensor([[[[7.0]]]])
    mask = torch.zeros((1, 1, 4, 4))
    mask[..., 0, 1:] = torch.finfo(mask.dtype).min
    mask[..., 1, 2:] = torch.finfo(mask.dtype).min
    mask[..., 2, 3:] = torch.finfo(mask.dtype).min

    output, _, audit = switched_eager_attention(
        _module(),
        query,
        key,
        value,
        mask,
        scaling=1.0,
        dropout=0.0,
        source_visual_key=source_key,
        source_visual_value=source_value,
        visual_indices=[1],
        first_switched_absolute_query=2,
    )
    baseline, _, _ = switched_eager_attention(
        _module(),
        query,
        key,
        value,
        mask,
        scaling=1.0,
        dropout=0.0,
        source_visual_key=key[:, :, [1], :],
        source_visual_value=value[:, :, [1], :],
        visual_indices=[1],
        first_switched_absolute_query=2,
    )

    assert torch.equal(output[:, :2], baseline[:, :2])
    assert not torch.equal(output[:, 2:], baseline[:, 2:])
    assert audit["switched_absolute_query_indices"] == [2, 3]
    assert audit["queries_before_switch_modified"] == 0


def test_self_switch_is_exactly_transparent() -> None:
    generator = torch.Generator().manual_seed(7)
    query = torch.randn((1, 2, 5, 3), generator=generator)
    key = torch.randn((1, 2, 5, 3), generator=generator)
    value = torch.randn((1, 2, 5, 3), generator=generator)
    mask = torch.zeros((1, 1, 5, 5))

    switched, _, audit = switched_eager_attention(
        _module(),
        query,
        key,
        value,
        mask,
        scaling=3**-0.5,
        dropout=0.0,
        source_visual_key=key[:, :, [1, 2], :].clone(),
        source_visual_value=value[:, :, [1, 2], :].clone(),
        visual_indices=[1, 2],
        first_switched_absolute_query=3,
    )
    baseline, _, _ = switched_eager_attention(
        _module(),
        query,
        key,
        value,
        mask,
        scaling=3**-0.5,
        dropout=0.0,
        source_visual_key=key[:, :, [1, 2], :],
        source_visual_value=value[:, :, [1, 2], :],
        visual_indices=[1, 2],
        first_switched_absolute_query=99,
    )

    assert torch.equal(switched, baseline)
    assert audit["source_visual_key_exact_recipient_match"] is True
    assert audit["source_visual_value_exact_recipient_match"] is True
    assert audit["nonvisual_key_value_entries_replaced"] == 0


def test_valid_switch_audit_requires_all_layers_and_exact_query_boundary() -> None:
    calls = [
        {
            "layer_index": layer,
            "first_switched_absolute_query": 12,
            "switched_absolute_query_indices": [12, 13, 14],
            "queries_before_switch_modified": 0,
            "visual_indices": [2, 3],
            "nonvisual_key_value_entries_replaced": 0,
            "query_rows_replaced": 3,
        }
        for layer in range(4)
    ]

    assert valid_switch_audit(
        calls,
        prompt_length=10,
        generated_sequence_length=5,
        switch_generated_index=3,
        visual_indices=[2, 3],
        layer_count=4,
    )


def test_attention_override_preserves_eager_config_for_causal_mask_construction() -> None:
    config = SimpleNamespace(_attn_implementation="eager")
    model = SimpleNamespace(
        config=SimpleNamespace(text_config=config),
        model=SimpleNamespace(
            language_model=SimpleNamespace(
                layers=[SimpleNamespace(self_attn=SimpleNamespace(config=config))]
            )
        ),
    )
    function = lambda *args, **kwargs: None

    with _AttentionInterfaceContext(model=model, name="test_override", function=function):
        assert config._attn_implementation == "eager"
        assert ALL_ATTENTION_FUNCTIONS["eager"] is function

    assert "eager" not in ALL_ATTENTION_FUNCTIONS._local_mapping
