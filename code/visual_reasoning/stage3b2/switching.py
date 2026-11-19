"""Query-timed all-layer visual K/V source switching."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Callable, Sequence

import torch
from transformers.modeling_utils import ALL_ATTENTION_FUNCTIONS
from transformers.models.qwen3_vl.modeling_qwen3_vl import eager_attention_forward


def valid_switch_audit(
    calls: Sequence[dict[str, Any]],
    *,
    prompt_length: int,
    generated_sequence_length: int,
    switch_generated_index: int,
    visual_indices: Sequence[int],
    layer_count: int,
) -> bool:
    """Validate exact query/layer coverage and the non-visual invariance contract."""

    prompt = int(prompt_length)
    generated = int(generated_sequence_length)
    switch = int(switch_generated_index)
    first = prompt + switch - 1
    final = prompt + generated - 1
    expected_queries = list(range(first, final + 1))
    visual = sorted({int(value) for value in visual_indices})
    return bool(
        generated > 0
        and 0 <= switch <= generated
        and len(calls) == int(layer_count)
        and sorted(int(call["layer_index"]) for call in calls) == list(range(int(layer_count)))
        and all(int(call["first_switched_absolute_query"]) == first for call in calls)
        and all(call["switched_absolute_query_indices"] == expected_queries for call in calls)
        and all(int(call["queries_before_switch_modified"]) == 0 for call in calls)
        and all(call["visual_indices"] == visual for call in calls)
        and all(int(call["nonvisual_key_value_entries_replaced"]) == 0 for call in calls)
        and all(int(call["query_rows_replaced"]) == len(expected_queries) for call in calls)
    )


class _AttentionInterfaceContext(AbstractContextManager["_AttentionInterfaceContext"]):
    """Temporarily route every Qwen text layer through one local interface."""

    def __init__(self, *, model: Any, name: str, function: Callable[..., Any]) -> None:
        self.model = model
        self.name = str(name)
        self.function = function
        self._attached = False

    def __enter__(self) -> "_AttentionInterfaceContext":
        if "eager" in getattr(ALL_ATTENTION_FUNCTIONS, "_local_mapping", {}):
            raise RuntimeError(f"An eager attention override is already active before {self.name}")
        configs = [self.model.config.text_config]
        configs.extend(layer.self_attn.config for layer in self.model.model.language_model.layers)
        if any(str(config._attn_implementation) != "eager" for config in configs):
            raise RuntimeError("Stage 3B.2 requires the validated eager causal-mask path")
        ALL_ATTENTION_FUNCTIONS["eager"] = self.function
        self._attached = True
        return self

    def close(self) -> None:
        if self._attached and "eager" in getattr(ALL_ATTENTION_FUNCTIONS, "_local_mapping", {}):
            del ALL_ATTENTION_FUNCTIONS["eager"]
        self._attached = False

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


class CaptureVisualKV(AbstractContextManager["CaptureVisualKV"]):
    """Capture post-RoPE visual K/V while preserving eager-attention scoring."""

    def __init__(self, *, model: Any, visual_indices: Sequence[int]) -> None:
        self.model = model
        self.visual_indices = tuple(sorted({int(value) for value in visual_indices}))
        self.layer_count = int(model.config.text_config.num_hidden_layers)
        self.layers: list[tuple[torch.Tensor, torch.Tensor] | None] = [None] * self.layer_count
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
        if self.layers[layer] is not None:
            raise RuntimeError(f"Layer {layer} visual K/V was captured more than once")
        visual = list(self.visual_indices)
        if not visual or visual[0] < 0 or visual[-1] >= int(key.shape[2]):
            raise RuntimeError("Visual capture indices are outside the attention key sequence")
        captured_key = key[:, :, visual, :].detach().clone()
        captured_value = value[:, :, visual, :].detach().clone()
        self.layers[layer] = (captured_key, captured_value)
        self.audit.append(
            {
                "layer_index": layer,
                "full_key_shape": list(key.shape),
                "captured_visual_key_shape": list(captured_key.shape),
                "visual_indices": visual,
                "post_rope_key": True,
                "value_projection": True,
            }
        )
        return eager_attention_forward(
            module,
            query,
            key,
            value,
            attention_mask,
            scaling=scaling,
            dropout=dropout,
            **kwargs,
        )

    def __enter__(self) -> "CaptureVisualKV":
        self._interface = _AttentionInterfaceContext(
            model=self.model,
            name="stage3b2_capture_visual_kv",
            function=self._forward,
        )
        self._interface.__enter__()
        return self

    def close(self) -> None:
        if self._interface is not None:
            self._interface.close()
            self._interface = None

    def complete_layers(self) -> list[tuple[torch.Tensor, torch.Tensor]]:
        if any(value is None for value in self.layers):
            raise RuntimeError("Visual K/V capture did not visit every language layer")
        return [value for value in self.layers if value is not None]

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


class VisualSourceSwitch(AbstractContextManager["VisualSourceSwitch"]):
    """Switch visual K/V by query boundary while retaining recipient non-visual K/V."""

    def __init__(
        self,
        *,
        model: Any,
        source_layers: Sequence[tuple[torch.Tensor, torch.Tensor]],
        visual_indices: Sequence[int],
        first_switched_absolute_query: int,
    ) -> None:
        self.model = model
        self.source_layers = list(source_layers)
        self.visual_indices = tuple(sorted({int(value) for value in visual_indices}))
        self.first_switched_absolute_query = int(first_switched_absolute_query)
        if len(self.source_layers) != int(model.config.text_config.num_hidden_layers):
            raise ValueError("Source visual K/V must cover every language layer")
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
        source_key, source_value = self.source_layers[int(module.layer_idx)]
        output, weights, call = switched_eager_attention(
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
            **kwargs,
        )
        self.audit.append(call)
        return output, weights

    def __enter__(self) -> "VisualSourceSwitch":
        self._interface = _AttentionInterfaceContext(
            model=self.model,
            name="stage3b2_visual_source_switch",
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


def switched_eager_attention(
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
    **kwargs: Any,
) -> tuple[torch.Tensor, torch.Tensor, dict[str, Any]]:
    """Use donor visual K/V only for query rows at or after one boundary."""

    if key.ndim != 4 or value.shape != key.shape:
        raise ValueError("Recipient K/V must be matching [batch, kv_head, key, head_dim] tensors")
    visual = sorted({int(index) for index in visual_indices})
    if not visual or visual[0] < 0 or visual[-1] >= int(key.shape[2]):
        raise ValueError("Visual indices must be nonempty positions in recipient K/V")
    expected_source = (int(key.shape[0]), int(key.shape[1]), len(visual), int(key.shape[3]))
    if tuple(source_visual_key.shape) != expected_source or tuple(source_visual_value.shape) != expected_source:
        raise ValueError(
            f"Source visual K/V shape mismatch: expected {expected_source}, "
            f"observed {tuple(source_visual_key.shape)} and {tuple(source_visual_value.shape)}"
        )
    query_length = int(query.shape[2])
    key_length = int(key.shape[2])
    query_start = key_length - query_length
    threshold = int(first_switched_absolute_query)
    active_rows = [row for row in range(query_length) if query_start + row >= threshold]

    baseline_output, baseline_weights = eager_attention_forward(
        module,
        query,
        key,
        value,
        attention_mask,
        scaling=scaling,
        dropout=dropout,
        **kwargs,
    )
    recipient_visual_key = key[:, :, visual, :]
    recipient_visual_value = value[:, :, visual, :]
    exact_key = torch.equal(recipient_visual_key, source_visual_key)
    exact_value = torch.equal(recipient_visual_value, source_visual_value)
    if not active_rows or (exact_key and exact_value):
        output = baseline_output
        weights = baseline_weights
    else:
        hybrid_key = key.clone()
        hybrid_value = value.clone()
        hybrid_key[:, :, visual, :] = source_visual_key
        hybrid_value[:, :, visual, :] = source_visual_value
        switched_output, switched_weights = eager_attention_forward(
            module,
            query,
            hybrid_key,
            hybrid_value,
            attention_mask,
            scaling=scaling,
            dropout=dropout,
            **kwargs,
        )
        output = baseline_output.clone()
        weights = baseline_weights.clone()
        output[:, active_rows, :, :] = switched_output[:, active_rows, :, :]
        weights[:, :, active_rows, :] = switched_weights[:, :, active_rows, :]

    active_absolute = [query_start + row for row in active_rows]
    return output, weights, {
        "layer_index": int(getattr(module, "layer_idx", -1)),
        "first_switched_absolute_query": threshold,
        "switched_absolute_query_indices": active_absolute,
        "queries_before_switch_modified": sum(value < threshold for value in active_absolute),
        "visual_indices": visual,
        "visual_position_count": len(visual),
        "source_visual_key_exact_recipient_match": exact_key,
        "source_visual_value_exact_recipient_match": exact_value,
        "nonvisual_key_value_entries_replaced": 0,
        "query_rows_replaced": len(active_rows),
    }
