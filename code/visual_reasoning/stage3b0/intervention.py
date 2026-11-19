"""Generation-start all-visual attention cutoff for Stage 3B.0."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Iterable

import torch


def apply_generation_start_visual_cutoff(
    attention_mask: torch.Tensor,
    *,
    prompt_length: int,
    visual_key_indices: Iterable[int],
    query_length: int,
    key_length: int,
) -> tuple[torch.Tensor, dict[str, Any]]:
    """Block generated-token queries to visual prompt keys and no other edges."""

    if attention_mask.ndim != 4:
        raise ValueError(f"Expected additive mask [batch, heads|1, query, key], got {attention_mask.shape}")
    if query_length <= 0 or key_length <= 0 or attention_mask.shape[-2:] != (query_length, key_length):
        raise ValueError("Declared query/key lengths do not match attention mask")
    prompt = int(prompt_length)
    visual = sorted({int(index) for index in visual_key_indices})
    if prompt <= 0 or not visual or visual[0] < 0 or visual[-1] >= prompt or visual[-1] >= key_length:
        raise ValueError("Visual keys must be nonempty prompt positions inside the key sequence")

    query_start_absolute = key_length - query_length
    absolute = [query_start_absolute + row for row in range(query_length)]
    active_rows = [row for row, position in enumerate(absolute) if position >= prompt]
    audit = {
        "absolute_query_indices": [absolute[row] for row in active_rows],
        "query_rows": active_rows,
        "visual_key_indices": visual,
        "prefill_modified": any(position < prompt for position in (absolute[row] for row in active_rows)),
        "tensor_entries_modified": 0,
        "target_entries_actually_changed": 0,
    }
    if not active_rows:
        return attention_mask, audit

    masked = attention_mask.clone()
    minimum = torch.finfo(masked.dtype).min
    keys = torch.tensor(visual, dtype=torch.long, device=masked.device)
    changed = 0
    for row in active_rows:
        changed += int((masked[:, :, row, keys] != minimum).sum().item())
        masked[:, :, row, keys] = minimum
    audit.update(
        {
            "tensor_entries_modified": int(
                masked.shape[0] * masked.shape[1] * len(active_rows) * len(visual)
            ),
            "target_entries_actually_changed": changed,
            "mask_value": float(minimum),
        }
    )
    return masked, audit


class GenerationStartVisualCutoff(AbstractContextManager["GenerationStartVisualCutoff"]):
    """Apply the cutoff to every Qwen language self-attention module."""

    def __init__(
        self,
        *,
        prompt_length: int,
        visual_key_indices: Iterable[int],
        num_attention_heads: int,
        enabled: bool = True,
    ) -> None:
        self.prompt_length = int(prompt_length)
        self.visual_key_indices = tuple(sorted({int(value) for value in visual_key_indices}))
        self.num_attention_heads = int(num_attention_heads)
        self.enabled = bool(enabled)
        self._handles: list[Any] = []
        self.reset_audit()

    def reset_audit(self) -> None:
        self.audit: dict[str, Any] = {
            "enabled": self.enabled,
            "modified_calls": 0,
            "layers_modified": [],
            "absolute_query_indices": [],
            "tensor_entries_modified": 0,
            "target_entries_actually_changed": 0,
            "logical_head_edges_modified": 0,
            "prefill_modified": False,
            "mask_was_synthesized": False,
        }

    def attach(self, attention_modules: list[torch.nn.Module]) -> "GenerationStartVisualCutoff":
        if self._handles:
            raise RuntimeError("Visual cutoff is already attached")
        for layer_index, module in enumerate(attention_modules):
            self._handles.append(
                module.register_forward_pre_hook(self._make_pre_hook(layer_index), with_kwargs=True)
            )
        return self

    def _make_pre_hook(self, layer_index: int):
        def hook(module: torch.nn.Module, args: tuple[Any, ...], kwargs: dict[str, Any]):
            if not self.enabled:
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
                    (int(hidden_states.shape[0]), 1, 1, key_length),
                    dtype=hidden_states.dtype,
                    device=hidden_states.device,
                )
                self.audit["mask_was_synthesized"] = True
            else:
                key_length = int(attention_mask.shape[-1])
            masked, call = apply_generation_start_visual_cutoff(
                attention_mask,
                prompt_length=self.prompt_length,
                visual_key_indices=self.visual_key_indices,
                query_length=query_length,
                key_length=key_length,
            )
            if call["tensor_entries_modified"]:
                kwargs = dict(kwargs)
                kwargs["attention_mask"] = masked
                self.audit["modified_calls"] += 1
                self.audit["layers_modified"].append(int(layer_index))
                self.audit["absolute_query_indices"].extend(call["absolute_query_indices"])
                self.audit["tensor_entries_modified"] += int(call["tensor_entries_modified"])
                self.audit["target_entries_actually_changed"] += int(call["target_entries_actually_changed"])
                self.audit["logical_head_edges_modified"] += int(
                    call["tensor_entries_modified"] * self.num_attention_heads
                )
                self.audit["prefill_modified"] = bool(self.audit["prefill_modified"] or call["prefill_modified"])
            return args, kwargs

        return hook

    def close(self) -> None:
        for handle in self._handles:
            handle.remove()
        self._handles.clear()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
