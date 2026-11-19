from types import SimpleNamespace

import torch

from visual_reasoning.stage3b3.switching import (
    layer_switched_eager_attention,
    valid_layer_switch_audit,
)


def _module(layer: int) -> SimpleNamespace:
    return SimpleNamespace(num_key_value_groups=1, layer_idx=layer, training=False)


def test_only_selected_layer_uses_donor_visual_key_value() -> None:
    query = torch.ones((1, 1, 3, 1))
    key = torch.tensor([[[[0.0], [1.0], [0.5]]]])
    value = torch.tensor([[[[0.0], [1.0], [2.0]]]])
    mask = torch.zeros((1, 1, 3, 3))
    selected, _, selected_audit = layer_switched_eager_attention(
        _module(2), query, key, value, mask,
        scaling=1.0, dropout=0.0,
        source_visual_key=torch.tensor([[[[9.0]]]]),
        source_visual_value=torch.tensor([[[[7.0]]]]),
        visual_indices=[1], first_switched_absolute_query=1,
        layer_selected=True,
    )
    inactive, _, inactive_audit = layer_switched_eager_attention(
        _module(1), query, key, value, mask,
        scaling=1.0, dropout=0.0,
        source_visual_key=torch.tensor([[[[9.0]]]]),
        source_visual_value=torch.tensor([[[[7.0]]]]),
        visual_indices=[1], first_switched_absolute_query=1,
        layer_selected=False,
    )

    assert not torch.equal(selected, inactive)
    assert selected_audit["layer_selected"] is True
    assert selected_audit["switched_absolute_query_indices"] == [1, 2]
    assert inactive_audit["layer_selected"] is False
    assert inactive_audit["switched_absolute_query_indices"] == []


def test_layer_switch_audit_requires_exact_selected_layer_set() -> None:
    calls = []
    for layer in range(4):
        active = layer in {1, 2}
        calls.append({
            "layer_index": layer,
            "layer_selected": active,
            "first_switched_absolute_query": 12,
            "switched_absolute_query_indices": [12, 13, 14] if active else [],
            "queries_before_switch_modified": 0,
            "visual_indices": [2, 3],
            "nonvisual_key_value_entries_replaced": 0,
            "query_rows_replaced": 3 if active else 0,
        })

    assert valid_layer_switch_audit(
        calls,
        prompt_length=10,
        generated_sequence_length=5,
        switch_generated_index=3,
        visual_indices=[2, 3],
        layer_count=4,
        selected_layers=[1, 2],
    )
