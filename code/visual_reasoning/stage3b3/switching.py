"""Layer-selective visual K/V source switching on the validated eager path."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Sequence

import torch
from transformers.models.qwen3_vl.modeling_qwen3_vl import eager_attention_forward

from visual_reasoning.stage3b2.switching import (
    _AttentionInterfaceContext,
    switched_eager_attention,
)


def layer_switched_eager_attention(
    module: Any,
    query: torch.Tensor,
    key: torch.Tensor,
    value: torch.Tensor,
    attention_mask: torch.Tensor | None,
    *,
    scaling: float,
    dropout: float,
    source_visual_key: torch.Tensor,
    source_visual_value: torch.Tensor,
    visual_indices: Sequence[int],
    first_switched_absolute_query: int,
    layer_selected: bool,
    **kwargs: Any,
) -> tuple[torch.Tensor, torch.Tensor, dict[str, Any]]:
    if layer_selected:
        output, weights, audit = switched_eager_attention(
            module,
            query,
            key,
            value,
            attention_mask,
            scaling=scaling,
            dropout=dropout,
            source_visual_key=source_visual_key,
            source_visual_value=source_visual_value,
            visual_indices=visual_indices,
            first_switched_absolute_query=first_switched_absolute_query,
            **kwargs,
        )
        audit["layer_selected"] = True
        return output, weights, audit

    output, weights = eager_attention_forward(
        module,
        query,
        key,
        value,
        attention_mask,
        scaling=scaling,
        dropout=dropout,
        **kwargs,
    )
    return output, weights, {
        "layer_index": int(getattr(module, "layer_idx", -1)),
        "layer_selected": False,
        "first_switched_absolute_query": int(first_switched_absolute_query),
        "switched_absolute_query_indices": [],
        "queries_before_switch_modified": 0,
        "visual_indices": sorted({int(value) for value in visual_indices}),
        "nonvisual_key_value_entries_replaced": 0,
        "query_rows_replaced": 0,
    }


def valid_layer_switch_audit(
    calls: Sequence[dict[str, Any]],
    *,
    prompt_length: int,
    generated_sequence_length: int,
    switch_generated_index: int,
    visual_indices: Sequence[int],
    layer_count: int,
    selected_layers: Sequence[int],
) -> bool:
    prompt = int(prompt_length)
    generated = int(generated_sequence_length)
    switch = int(switch_generated_index)
    first = prompt + switch - 1
    final = prompt + generated - 1
    expected_queries = list(range(first, final + 1))
    selected = sorted({int(value) for value in selected_layers})
    visual = sorted({int(value) for value in visual_indices})
    if len(calls) != int(layer_count):
        return False
    by_layer = {int(call["layer_index"]): call for call in calls}
    if sorted(by_layer) != list(range(int(layer_count))):
        return False
    for layer, call in by_layer.items():
        active = layer in selected
        if bool(call["layer_selected"]) != active:
            return False
        if int(call["first_switched_absolute_query"]) != first:
            return False
        if call["switched_absolute_query_indices"] != (expected_queries if active else []):
            return False
        if int(call["queries_before_switch_modified"]) != 0:
            return False
        if call["visual_indices"] != visual:
            return False
        if int(call["nonvisual_key_value_entries_replaced"]) != 0:
            return False
        if int(call["query_rows_replaced"]) != (len(expected_queries) if active else 0):
            return False
    return True


class LayerVisualSourceSwitch(AbstractContextManager["LayerVisualSourceSwitch"]):
    def __init__(
        self,
        *,
        model: Any,
        source_layers: Sequence[tuple[torch.Tensor, torch.Tensor]],
        visual_indices: Sequence[int],
        first_switched_absolute_query: int,
        selected_layers: Sequence[int],
    ) -> None:
        self.model = model
        self.source_layers = list(source_layers)
        self.visual_indices = tuple(sorted({int(value) for value in visual_indices}))
        self.first_switched_absolute_query = int(first_switched_absolute_query)
        self.selected_layers = frozenset(int(value) for value in selected_layers)
        layer_count = int(model.config.text_config.num_hidden_layers)
        if len(self.source_layers) != layer_count:
            raise ValueError("Source visual K/V must cover every language layer")
        if not self.selected_layers.issubset(set(range(layer_count))):
            raise ValueError("Selected layer index is outside the language model")
        self.audit: list[dict[str, Any]] = []
        self._interface: _AttentionInterfaceContext | None = None

    def _forward(
        self,
        module: Any,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attention_mask: torch.Tensor | None,
        scaling: float,
        dropout: float = 0.0,
        **kwargs: Any,
    ):
        layer = int(module.layer_idx)
        source_key, source_value = self.source_layers[layer]
        output, weights, audit = layer_switched_eager_attention(
            module,
            query,
            key,
            value,
            attention_mask,
            scaling=scaling,
            dropout=dropout,
            source_visual_key=source_key,
            source_visual_value=source_value,
            visual_indices=self.visual_indices,
            first_switched_absolute_query=self.first_switched_absolute_query,
            layer_selected=layer in self.selected_layers,
            **kwargs,
        )
        self.audit.append(audit)
        return output, weights

    def __enter__(self) -> "LayerVisualSourceSwitch":
        self._interface = _AttentionInterfaceContext(
            model=self.model,
            name="stage3b3_layer_visual_source_switch",
            function=self._forward,
        )
        self._interface.__enter__()
        return self

    def close(self) -> None:
        if self._interface is not None:
            self._interface.close()
            self._interface = None

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
