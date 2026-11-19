"""All-layer generated-query to visual-ROI attention knockout."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Iterable

import torch


def apply_roi_mask(
    attention_mask: torch.Tensor,
    *,
    prompt_length: int,
    roi_key_indices: Iterable[int],
    window_start: int,
    window_end: int,
    query_length: int,
    key_length: int,
) -> tuple[torch.Tensor, dict[str, Any]]:
    """Return an additive mask with only the requested query→ROI entries blocked."""

    if attention_mask.ndim != 4:
        raise ValueError(f"Expected additive attention mask [batch, heads|1, query, key], got {attention_mask.shape}")
    if query_length <= 0 or key_length <= 0 or attention_mask.shape[-2:] != (query_length, key_length):
        raise ValueError("Declared query/key lengths do not match attention mask")
    roi = sorted({int(index) for index in roi_key_indices})
    if not roi or roi[0] < 0 or roi[-1] >= key_length:
        raise ValueError("ROI key indices must be non-empty and inside the attention key sequence")
    if not 0 <= window_start < window_end:
        raise ValueError("Intervention window must be non-empty")

    query_start_absolute = key_length - query_length
    decision_indices = [
        query_start_absolute + query_row - (int(prompt_length) - 1) for query_row in range(query_length)
    ]
    active_rows = [
        query_row
        for query_row, decision_index in enumerate(decision_indices)
        if int(window_start) <= decision_index < int(window_end)
    ]
    if not active_rows:
        return attention_mask, {
            "decision_indices": [],
            "query_rows": [],
            "roi_key_indices": roi,
            "tensor_entries_modified": 0,
        }

    masked = attention_mask.clone()
    row_index = torch.tensor(active_rows, device=masked.device, dtype=torch.long)
    key_index = torch.tensor(roi, device=masked.device, dtype=torch.long)
    minimum = torch.finfo(masked.dtype).min
    target_entries_changed = 0
    for query_row in row_index.tolist():
        target_entries_changed += int((masked[:, :, query_row, key_index] != minimum).sum().item())
        masked[:, :, query_row, key_index] = minimum
    return masked, {
        "decision_indices": [decision_indices[row] for row in active_rows],
        "query_rows": active_rows,
        "roi_key_indices": roi,
        "tensor_entries_modified": int(masked.shape[0] * masked.shape[1] * len(active_rows) * len(roi)),
        "target_entries_actually_changed": target_entries_changed,
        "mask_value": float(minimum),
    }


class ROIAttentionKnockout(AbstractContextManager["ROIAttentionKnockout"]):
    """Apply one time-windowed ROI mask to every supplied attention module.

    PyTorch's documented ``with_kwargs=True`` forward-pre-hook contract allows
    replacing keyword arguments before ``forward``:
    https://docs.pytorch.org/docs/stable/generated/torch.nn.Module.html#torch.nn.Module.register_forward_pre_hook

    Qwen3-VL eager attention adds the additive mask to attention logits before
    softmax:
    https://github.com/huggingface/transformers/blob/main/src/transformers/models/qwen3_vl/modeling_qwen3_vl.py
    """

    def __init__(self, prompt_length: int, num_attention_heads: int) -> None:
        self.prompt_length = int(prompt_length)
        self.num_attention_heads = int(num_attention_heads)
        self._roi: tuple[int, ...] = ()
        self._window = (0, 0)
        self._handles: list[Any] = []
        self.audit: dict[str, Any] = {}
        self.reset_audit()

    def set_condition(self, roi_key_indices: Iterable[int] | None, window: tuple[int, int] | None) -> None:
        self._roi = tuple(sorted({int(value) for value in (roi_key_indices or [])}))
        self._window = tuple(int(value) for value in (window or (0, 0)))
        if bool(self._roi) != bool(window):
            raise ValueError("ROI and window must either both be set or both be absent")
        self.reset_audit()

    def reset_audit(self) -> None:
        self.audit = {
            "modified_calls": 0,
            "layers_modified": [],
            "decision_indices": [],
            "tensor_entries_modified": 0,
            "target_entries_actually_changed": 0,
            "logical_head_edges_modified": 0,
            "mask_was_synthesized": False,
        }

    def attach(self, attention_modules: list[torch.nn.Module]) -> "ROIAttentionKnockout":
        if self._handles:
            raise RuntimeError("Intervention is already attached")
        for layer_index, module in enumerate(attention_modules):
            self._handles.append(
                module.register_forward_pre_hook(self._make_pre_hook(layer_index), with_kwargs=True)
            )
        return self

    def _make_pre_hook(self, layer_index: int):
        def hook(module: torch.nn.Module, args: tuple[Any, ...], kwargs: dict[str, Any]):
            if not self._roi:
                return args, kwargs
            hidden_states = kwargs.get("hidden_states", args[0] if args else None)
            if not isinstance(hidden_states, torch.Tensor):
                raise RuntimeError("Unable to locate attention hidden_states")
            query_length = int(hidden_states.shape[-2])
            attention_mask = kwargs.get("attention_mask")
            if attention_mask is None:
                past = kwargs.get("past_key_values")
                past_length = int(past.get_seq_length(layer_index)) if past is not None else 0
                key_length = past_length + query_length
                if query_length != 1:
                    raise RuntimeError("Cannot synthesize a causal mask for a multi-query forward")
                attention_mask = torch.zeros(
                    (int(hidden_states.shape[0]), 1, query_length, key_length),
                    dtype=hidden_states.dtype,
                    device=hidden_states.device,
                )
                self.audit["mask_was_synthesized"] = True
            else:
                key_length = int(attention_mask.shape[-1])

            masked, call_audit = apply_roi_mask(
                attention_mask,
                prompt_length=self.prompt_length,
                roi_key_indices=self._roi,
                window_start=self._window[0],
                window_end=self._window[1],
                query_length=query_length,
                key_length=key_length,
            )
            if call_audit["tensor_entries_modified"]:
                kwargs = dict(kwargs)
                kwargs["attention_mask"] = masked
                self.audit["modified_calls"] += 1
                self.audit["layers_modified"].append(int(layer_index))
                self.audit["decision_indices"].extend(call_audit["decision_indices"])
                self.audit["tensor_entries_modified"] += int(call_audit["tensor_entries_modified"])
                self.audit["target_entries_actually_changed"] += int(call_audit["target_entries_actually_changed"])
                self.audit["logical_head_edges_modified"] += int(
                    call_audit["tensor_entries_modified"] * self.num_attention_heads
                )
            return args, kwargs

        return hook

    def close(self) -> None:
        for handle in self._handles:
            handle.remove()
        self._handles.clear()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
