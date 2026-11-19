"""Query-head-selective K-only, V-only, and joint K/V interventions."""

from __future__ import annotations

from contextlib import AbstractContextManager
from types import MethodType
from typing import Any, Sequence

import torch

from visual_reasoning.stage3b6.heads import (
    _attention_group_summary,
    _attention_module,
    _project_attention_output,
    _qwen_attention_parts,
    gqa_query_to_kv_map,
    splice_query_head_outputs,
)
from visual_reasoning.stage3b7.kv import KV_MODES, compose_kv_sources


class HybridQueryHeadKVIntervention(
    AbstractContextManager["HybridQueryHeadKVIntervention"]
):
    """Compose donor K/V at frozen positions, then splice selected query heads.

    Recipient queries are always retained. Depending on ``mode``, donor post-RoPE
    keys, donor values, or both are installed only at ``source_positions``. The
    recomputed pre-``W_O`` output is then copied only for ``selected_heads`` at
    the frozen recipient position.
    """

    def __init__(
        self,
        *,
        model: Any,
        layer_index: int,
        position: int,
        selected_heads: Sequence[int],
        source_key: torch.Tensor,
        source_value: torch.Tensor,
        source_positions: Sequence[int],
        mode: str,
        attention_groups: dict[str, Sequence[int]] | None = None,
    ) -> None:
        if mode not in KV_MODES:
            raise ValueError(f"Unknown K/V intervention mode: {mode}")
        self.layer_index = int(layer_index)
        self.position = int(position)
        self.selected_heads = sorted({int(head) for head in selected_heads})
        self.source_key = source_key
        self.source_value = source_value
        self.source_positions = sorted({int(value) for value in source_positions})
        self.mode = mode
        self.attention_groups = attention_groups
        self.module = _attention_module(model, self.layer_index)
        self.audit: list[dict[str, Any]] = []
        self._original_forward: Any | None = None

    def _run(
        self,
        module: torch.nn.Module,
        hidden_states: torch.Tensor,
        position_embeddings: tuple[torch.Tensor, torch.Tensor],
        attention_mask: torch.Tensor | None,
        past_key_values: Any | None = None,
        **kwargs: Any,
    ) -> tuple[torch.Tensor, torch.Tensor | None]:
        if self.audit:
            raise RuntimeError("K/V intervention executed more than once")
        native, query, recipient_key, recipient_value, native_weights = (
            _qwen_attention_parts(
                module,
                hidden_states,
                position_embeddings,
                attention_mask,
                past_key_values,
                kwargs,
            )
        )
        composed_key, composed_value, kv_audit = compose_kv_sources(
            recipient_key,
            recipient_value,
            self.source_key.to(device=recipient_key.device, dtype=recipient_key.dtype),
            self.source_value.to(
                device=recipient_value.device, dtype=recipient_value.dtype
            ),
            positions=self.source_positions,
            mode=self.mode,
        )

        from transformers.models.qwen3_vl import modeling_qwen3_vl as qwen_impl

        attention_interface = qwen_impl.ALL_ATTENTION_FUNCTIONS.get_interface(
            module.config._attn_implementation, qwen_impl.eager_attention_forward
        )
        composed, composed_weights = attention_interface(
            module,
            query,
            composed_key,
            composed_value,
            attention_mask,
            dropout=0.0 if not module.training else module.attention_dropout,
            scaling=module.scaling,
            **kwargs,
        )
        merged, head_audit = splice_query_head_outputs(
            native,
            composed,
            position=self.position,
            selected_heads=self.selected_heads,
        )
        query_heads = int(query.shape[1])
        kv_heads = int(recipient_key.shape[1])
        query_to_kv = gqa_query_to_kv_map(
            query_heads=query_heads, kv_heads=kv_heads
        )
        changed_heads = set(head_audit["changed_query_heads"])
        query_selective = bool(
            changed_heads.issubset(self.selected_heads)
            and head_audit["nonselected_head_max_abs_delta"] == 0.0
            and set(head_audit["changed_sequence_positions"]).issubset(
                {self.position}
            )
        )
        source_isolated = bool(
            kv_audit["nonassigned_key_max_abs_delta"] == 0.0
            and kv_audit["nonassigned_value_max_abs_delta"] == 0.0
            and kv_audit["unswapped_key_max_abs_delta"] in (None, 0.0)
            and kv_audit["unswapped_value_max_abs_delta"] in (None, 0.0)
        )
        self.audit.append({
            "layer_index": self.layer_index,
            "position": self.position,
            "mode": self.mode,
            **head_audit,
            "selected_kv_groups": sorted(
                {query_to_kv[head] for head in self.selected_heads}
            ),
            "query_to_kv_group": query_to_kv,
            "kv_composition": kv_audit,
            "query_head_selectivity_valid": query_selective,
            "source_group_isolation_valid": source_isolated,
            "recipient_query_retained": True,
            "intervention_surface": (
                f"post-RoPE donor {self.mode} at frozen source positions -> "
                "selected-query-head pre-W_O output"
            ),
            "recipient_attention_summary": _attention_group_summary(
                native_weights,
                position=self.position,
                groups=self.attention_groups,
            ),
            "composed_attention_summary": _attention_group_summary(
                composed_weights,
                position=self.position,
                groups=self.attention_groups,
            ),
        })
        return _project_attention_output(module, merged, hidden_states), native_weights

    def __enter__(self) -> "HybridQueryHeadKVIntervention":
        if self._original_forward is not None:
            raise RuntimeError("K/V intervention context is already active")
        self._original_forward = self.module.forward

        def forward(
            module: torch.nn.Module,
            hidden_states: torch.Tensor,
            position_embeddings: tuple[torch.Tensor, torch.Tensor],
            attention_mask: torch.Tensor | None,
            past_key_values: Any | None = None,
            **kwargs: Any,
        ):
            return self._run(
                module,
                hidden_states,
                position_embeddings,
                attention_mask,
                past_key_values,
                **kwargs,
            )

        self.module.forward = MethodType(forward, self.module)
        return self

    def close(self) -> None:
        if self._original_forward is not None:
            self.module.forward = self._original_forward
            self._original_forward = None

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


__all__ = ["HybridQueryHeadKVIntervention"]
