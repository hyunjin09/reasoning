"""Timed all-visual attention cutoff for Stage 3B.1."""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Iterable

import torch


def valid_cutoff_audit(
    audit: dict[str, Any],
    *,
    prompt_length: int,
    prefix_token_count: int,
    candidate_token_count: int,
    cutoff_generated_index: int,
    visual_indices: list[int],
    layer_count: int,
    logical_heads: int,
) -> bool:
    """Verify exact edge coverage from the cutoff through the full probe."""

    expected_start = int(prompt_length) + int(cutoff_generated_index)
    expected_final = int(prompt_length) + int(prefix_token_count) + int(candidate_token_count) - 1
    expected_query_count = expected_final - expected_start + 1
    expected_entries = int(layer_count) * expected_query_count * len(visual_indices)
    return bool(
        expected_query_count > 0
        and audit["enabled"]
        and audit["cutoff_absolute_query_index"] == expected_start
        and audit["minimum_modified_absolute_query_index"] == expected_start
        and audit["maximum_modified_absolute_query_index"] == expected_final
        and audit["generated_query_count_per_layer"] == expected_query_count
        and audit["queries_before_cutoff_modified"] == 0
        and not audit["prefill_modified"]
        and audit["visual_key_indices"] == visual_indices
        and sorted(set(audit["layers_modified"])) == list(range(layer_count))
        and audit["query_range_consistent_across_layers"]
        and audit["tensor_entries_modified"] == expected_entries
        and audit["target_entries_actually_changed"] == expected_entries
        and audit["logical_head_edges_modified"] == expected_entries * logical_heads
    )


def apply_timed_visual_cutoff(
    attention_mask: torch.Tensor,
    *,
    prompt_length: int,
    cutoff_generated_index: int,
    visual_key_indices: Iterable[int],
    query_length: int,
    key_length: int,
) -> tuple[torch.Tensor, dict[str, Any]]:
    """Block only generated-query→visual-key edges at/after one cutoff."""

    if attention_mask.ndim != 4:
        raise ValueError(f"Expected additive mask [batch, heads|1, query, key], got {attention_mask.shape}")
    if query_length <= 0 or key_length <= 0 or attention_mask.shape[-2:] != (query_length, key_length):
        raise ValueError("Declared query/key lengths do not match attention mask")
    prompt = int(prompt_length)
    cutoff = int(cutoff_generated_index)
    visual = sorted({int(index) for index in visual_key_indices})
    if cutoff < 0:
        raise ValueError("Cutoff generated index must be nonnegative")
    if prompt <= 0 or not visual or visual[0] < 0 or visual[-1] >= prompt or visual[-1] >= key_length:
        raise ValueError("Visual keys must be nonempty prompt positions inside the key sequence")

    cutoff_absolute = prompt + cutoff
    query_start_absolute = key_length - query_length
    absolute = [query_start_absolute + row for row in range(query_length)]
    active_rows = [row for row, position in enumerate(absolute) if position >= cutoff_absolute]
    active_absolute = [absolute[row] for row in active_rows]
    audit = {
        "cutoff_generated_index": cutoff,
        "cutoff_absolute_query_index": cutoff_absolute,
        "absolute_query_indices": active_absolute,
        "generated_query_indices": [position - prompt for position in active_absolute],
        "query_rows": active_rows,
        "visual_key_indices": visual,
        "queries_before_cutoff_modified": sum(position < cutoff_absolute for position in active_absolute),
        "prefill_modified": any(position < prompt for position in active_absolute),
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
            "tensor_entries_modified": int(masked.shape[0] * masked.shape[1] * len(active_rows) * len(visual)),
            "target_entries_actually_changed": changed,
            "mask_value": float(minimum),
        }
    )
    return masked, audit


class TimedVisualCutoff(AbstractContextManager["TimedVisualCutoff"]):
    """Apply one generated-query cutoff to every Qwen language layer."""

    def __init__(
        self,
        *,
        prompt_length: int,
        cutoff_generated_index: int,
        visual_key_indices: Iterable[int],
        num_attention_heads: int,
        enabled: bool = True,
    ) -> None:
        self.prompt_length = int(prompt_length)
        self.cutoff_generated_index = int(cutoff_generated_index)
        self.visual_key_indices = tuple(sorted({int(value) for value in visual_key_indices}))
        self.num_attention_heads = int(num_attention_heads)
        self.enabled = bool(enabled)
        self._handles: list[Any] = []
        self.reset_audit()

    def reset_audit(self) -> None:
        self.audit: dict[str, Any] = {
            "enabled": self.enabled,
            "prompt_length": self.prompt_length,
            "cutoff_generated_index": self.cutoff_generated_index,
            "cutoff_absolute_query_index": self.prompt_length + self.cutoff_generated_index,
            "visual_key_indices": list(self.visual_key_indices),
            "modified_calls": 0,
            "layers_modified": [],
            "minimum_modified_absolute_query_index": None,
            "maximum_modified_absolute_query_index": None,
            "generated_query_count_per_layer": None,
            "query_range_consistent_across_layers": True,
            "tensor_entries_modified": 0,
            "target_entries_actually_changed": 0,
            "logical_head_edges_modified": 0,
            "queries_before_cutoff_modified": 0,
            "prefill_modified": False,
        }

    def attach(self, attention_modules: list[torch.nn.Module]) -> "TimedVisualCutoff":
        if self._handles:
            raise RuntimeError("Timed visual cutoff is already attached")
        for layer_index, module in enumerate(attention_modules):
            self._handles.append(module.register_forward_pre_hook(self._make_pre_hook(layer_index), with_kwargs=True))
        return self

    def _make_pre_hook(self, layer_index: int):
        def hook(module: torch.nn.Module, args: tuple[Any, ...], kwargs: dict[str, Any]):
            if not self.enabled:
                return args, kwargs
            hidden_states = kwargs.get("hidden_states", args[0] if args else None)
            attention_mask = kwargs.get("attention_mask")
            if not isinstance(hidden_states, torch.Tensor):
                raise RuntimeError("Unable to locate attention hidden_states")
            if not isinstance(attention_mask, torch.Tensor):
                raise RuntimeError("Stage 3B.1 full-sequence eager scoring requires an additive attention mask")
            query_length = int(hidden_states.shape[-2])
            key_length = int(attention_mask.shape[-1])
            masked, call = apply_timed_visual_cutoff(
                attention_mask,
                prompt_length=self.prompt_length,
                cutoff_generated_index=self.cutoff_generated_index,
                visual_key_indices=self.visual_key_indices,
                query_length=query_length,
                key_length=key_length,
            )
            if call["tensor_entries_modified"]:
                kwargs = dict(kwargs)
                kwargs["attention_mask"] = masked
                count = len(call["absolute_query_indices"])
                prior_count = self.audit["generated_query_count_per_layer"]
                if prior_count is not None and prior_count != count:
                    self.audit["query_range_consistent_across_layers"] = False
                self.audit["generated_query_count_per_layer"] = count
                minimum = min(call["absolute_query_indices"])
                maximum = max(call["absolute_query_indices"])
                prior_min = self.audit["minimum_modified_absolute_query_index"]
                prior_max = self.audit["maximum_modified_absolute_query_index"]
                if prior_min is not None and (prior_min != minimum or prior_max != maximum):
                    self.audit["query_range_consistent_across_layers"] = False
                self.audit["minimum_modified_absolute_query_index"] = minimum
                self.audit["maximum_modified_absolute_query_index"] = maximum
                self.audit["modified_calls"] += 1
                self.audit["layers_modified"].append(int(layer_index))
                self.audit["tensor_entries_modified"] += int(call["tensor_entries_modified"])
                self.audit["target_entries_actually_changed"] += int(call["target_entries_actually_changed"])
                self.audit["logical_head_edges_modified"] += int(
                    call["tensor_entries_modified"] * self.num_attention_heads
                )
                self.audit["queries_before_cutoff_modified"] += int(call["queries_before_cutoff_modified"])
                self.audit["prefill_modified"] = bool(self.audit["prefill_modified"] or call["prefill_modified"])
            return args, kwargs

        return hook

    def close(self) -> None:
        for handle in self._handles:
            handle.remove()
        self._handles.clear()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
