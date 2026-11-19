"""Capture and intervene on the Stage 3B.8 ROI-derived Value representation."""

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
from visual_reasoning.stage3b8.geometry import (
    flatten_head_vectors,
    interpolate_head_delta,
    project_rows,
    roi_value_contribution_from_current,
    unflatten_head_vectors,
)


def roi_head_delta_from_states(
    *,
    recipient_state: dict[str, torch.Tensor],
    donor_state: dict[str, torch.Tensor],
    selected_query_heads: Sequence[int],
    roi_positions: Sequence[int],
    projector_basis: torch.Tensor | None = None,
    projector_complement: bool = False,
) -> tuple[torch.Tensor, dict[str, Any]]:
    """Compute donor-minus-recipient ROI Value content under recipient routing."""

    attention = recipient_state["current_attention_weights"]
    recipient_value = recipient_state["value"]
    donor_value = donor_state["value"]
    if recipient_value.shape != donor_value.shape:
        raise ValueError("Recipient and donor Value tensors do not align")
    recipient_z = roi_value_contribution_from_current(
        current_attention_weights=attention,
        values=recipient_value,
        selected_query_heads=selected_query_heads,
        roi_positions=roi_positions,
    )
    donor_z = roi_value_contribution_from_current(
        current_attention_weights=attention,
        values=donor_value.to(device=recipient_value.device, dtype=recipient_value.dtype),
        selected_query_heads=selected_query_heads,
        roi_positions=roi_positions,
    )
    full_delta = donor_z - recipient_z
    applied_delta = full_delta
    if projector_complement and projector_basis is None:
        raise ValueError("Complement projection requires a projector basis")
    if projector_basis is not None:
        flat = flatten_head_vectors(full_delta)
        projected = project_rows(flat, projector_basis)
        applied_delta = unflatten_head_vectors(
            flat - projected if projector_complement else projected,
            head_count=len(selected_query_heads),
        )
    return applied_delta, {
        "representation_shape": list(recipient_z.shape),
        "flattened_dimension": int(recipient_z.shape[-2] * recipient_z.shape[-1]),
        "full_delta_l2": float(flatten_head_vectors(full_delta).float().norm(dim=-1).mean().item()),
        "applied_delta_l2": float(flatten_head_vectors(applied_delta).float().norm(dim=-1).mean().item()),
        "projector_rank": int(projector_basis.shape[1]) if projector_basis is not None else None,
        "projector_component": (
            "orthogonal_complement" if projector_complement else "parallel"
        ) if projector_basis is not None else "full",
    }


class CaptureQwenROIValueState(AbstractContextManager["CaptureQwenROIValueState"]):
    """Capture current recipient routing and post-RoPE Values at one layer."""

    def __init__(
        self,
        *,
        model: Any,
        layer_index: int,
        position: int,
        selected_query_heads: Sequence[int],
        roi_positions: Sequence[int],
        attention_groups: dict[str, Sequence[int]] | None = None,
    ) -> None:
        self.layer_index = int(layer_index)
        self.position = int(position)
        self.selected_query_heads = [int(head) for head in selected_query_heads]
        self.roi_positions = sorted({int(value) for value in roi_positions})
        self.attention_groups = attention_groups
        self.module = _attention_module(model, self.layer_index)
        self.state: dict[str, torch.Tensor] | None = None
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
        if self.state is not None:
            raise RuntimeError("ROI Value capture executed more than once")
        output, query, key, value, weights = _qwen_attention_parts(
            module,
            hidden_states,
            position_embeddings,
            attention_mask,
            past_key_values,
            kwargs,
        )
        if weights is None:
            raise RuntimeError("Stage 3B.8 requires explicit eager Attention probabilities")
        if self.position < 0 or self.position >= int(output.shape[1]):
            raise ValueError("ROI Value capture position is outside the sequence")
        current_weights = weights[:, :, self.position, :].detach().clone()
        stored_value = value.detach().clone()
        contribution = roi_value_contribution_from_current(
            current_attention_weights=current_weights,
            values=stored_value,
            selected_query_heads=self.selected_query_heads,
            roi_positions=self.roi_positions,
        )
        query_to_kv = gqa_query_to_kv_map(
            query_heads=int(query.shape[1]), kv_heads=int(key.shape[1])
        )
        self.state = {
            "value": stored_value,
            "current_attention_weights": current_weights,
            "roi_value_contribution": contribution.detach().clone(),
            "current_head_output": output[:, self.position, :, :].detach().clone(),
        }
        self.audit.append({
            "layer_index": self.layer_index,
            "position": self.position,
            "selected_query_heads": self.selected_query_heads,
            "selected_kv_groups": sorted({query_to_kv[head] for head in self.selected_query_heads}),
            "query_to_kv_group": query_to_kv,
            "roi_positions": self.roi_positions,
            "roi_position_count": len(self.roi_positions),
            "query_shape": list(query.shape),
            "key_shape": list(key.shape),
            "value_shape": list(value.shape),
            "attention_weights_shape": list(weights.shape),
            "current_attention_weights_shape": list(current_weights.shape),
            "roi_value_contribution_shape": list(contribution.shape),
            "flattened_representation_dimension": int(contribution.shape[-2] * contribution.shape[-1]),
            "location": "selected logical query-head outputs before shared W_O",
            "recipient_attention_summary": _attention_group_summary(
                weights, position=self.position, groups=self.attention_groups
            ),
        })
        return _project_attention_output(module, output, hidden_states), weights

    def __enter__(self) -> "CaptureQwenROIValueState":
        if self._original_forward is not None:
            raise RuntimeError("ROI Value capture context is already active")
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

    def complete_state(self) -> dict[str, torch.Tensor]:
        if self.state is None or len(self.audit) != 1:
            raise RuntimeError("ROI Value capture did not execute exactly once")
        return self.state

    def close(self) -> None:
        if self._original_forward is not None:
            self.module.forward = self._original_forward
            self._original_forward = None

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


class ROIValueDeltaIntervention(AbstractContextManager["ROIValueDeltaIntervention"]):
    """Recompose an ROI Value donor path, then inject its projected head delta.

    Recomposition uses the installed eager Attention implementation over the
    complete source sequence.  This preserves the exact numerical reduction
    order of the validated Stage 3B.7-R V-only endpoint; directly summing only
    the ROI is mathematically equivalent but not bitwise equivalent in BF16.
    """

    def __init__(
        self,
        *,
        model: Any,
        layer_index: int,
        position: int,
        selected_query_heads: Sequence[int],
        dose: float,
        expected_recipient_state: dict[str, torch.Tensor],
        donor_state: dict[str, torch.Tensor],
        roi_positions: Sequence[int],
        projector_basis: torch.Tensor | None = None,
        projector_complement: bool = False,
    ) -> None:
        self.layer_index = int(layer_index)
        self.position = int(position)
        self.selected_query_heads = [int(head) for head in selected_query_heads]
        self.dose = float(dose)
        self.expected_recipient_state = expected_recipient_state
        self.donor_state = donor_state
        self.roi_positions = sorted({int(value) for value in roi_positions})
        self.projector_basis = projector_basis
        self.projector_complement = bool(projector_complement)
        if self.projector_complement and self.projector_basis is None:
            raise ValueError("Complement projection requires a projector basis")
        self.module = _attention_module(model, self.layer_index)
        self.audit: list[dict[str, Any]] = []
        self.full_delta: torch.Tensor | None = None
        self.applied_delta: torch.Tensor | None = None
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
            raise RuntimeError("ROI Value intervention executed more than once")
        output, query, key, value, weights = _qwen_attention_parts(
            module,
            hidden_states,
            position_embeddings,
            attention_mask,
            past_key_values,
            kwargs,
        )
        if weights is None:
            raise RuntimeError("Stage 3B.8 requires explicit eager Attention probabilities")
        expected_weights = self.expected_recipient_state["current_attention_weights"].to(
            device=weights.device, dtype=weights.dtype
        )
        current_weights = weights[:, :, self.position, :]
        expected_values = self.expected_recipient_state["value"].to(
            device=value.device, dtype=value.dtype
        )
        attention_error = float((current_weights - expected_weights).abs().max().item())
        roi_value_error = float(
            (value[:, :, self.roi_positions, :] - expected_values[:, :, self.roi_positions, :])
            .abs()
            .max()
            .item()
        )
        donor_value = self.donor_state["value"].to(device=value.device, dtype=value.dtype)
        if donor_value.shape != value.shape:
            raise ValueError("Donor and recipient Value tensors do not align")
        composed_value = value.clone()
        composed_value[:, :, self.roi_positions, :] = donor_value[:, :, self.roi_positions, :]
        from transformers.models.qwen3_vl import modeling_qwen3_vl as qwen_impl

        attention_interface = qwen_impl.ALL_ATTENTION_FUNCTIONS.get_interface(
            module.config._attn_implementation, qwen_impl.eager_attention_forward
        )
        composed_output, _ = attention_interface(
            module,
            query,
            key,
            composed_value,
            attention_mask,
            dropout=0.0 if not module.training else module.attention_dropout,
            scaling=module.scaling,
            **kwargs,
        )
        full_delta = (
            composed_output[:, self.position, self.selected_query_heads, :]
            - output[:, self.position, self.selected_query_heads, :]
        )
        applied_delta = full_delta
        if self.projector_basis is not None:
            flat = flatten_head_vectors(full_delta)
            projected = project_rows(flat, self.projector_basis)
            applied_delta = unflatten_head_vectors(
                flat - projected if self.projector_complement else projected,
                head_count=len(self.selected_query_heads),
            )
        self.full_delta = full_delta.detach().clone()
        self.applied_delta = applied_delta.detach().clone()
        exact_full_endpoint = bool(
            self.projector_basis is None and self.dose == 1.0
        )
        if exact_full_endpoint:
            merged, splice_audit = splice_query_head_outputs(
                output,
                composed_output,
                position=self.position,
                selected_heads=self.selected_query_heads,
            )
            splice_audit["dose"] = self.dose
        else:
            merged, splice_audit = interpolate_head_delta(
                output,
                applied_delta,
                current_position=self.position,
                selected_query_heads=self.selected_query_heads,
                dose=self.dose,
            )
        endpoint_error = (
            float(
                (
                    merged[:, self.position, self.selected_query_heads, :]
                    - composed_output[:, self.position, self.selected_query_heads, :]
                ).abs().max().item()
            )
            if exact_full_endpoint
            else None
        )
        self.audit.append({
            "layer_index": self.layer_index,
            "position": self.position,
            **splice_audit,
            "recipient_attention_max_abs_error": attention_error,
            "recipient_roi_value_max_abs_error": roi_value_error,
            "recipient_attention_exact": attention_error == 0.0,
            "recipient_roi_value_exact": roi_value_error == 0.0,
            "recipient_keys_and_routing_retained": True,
            "full_delta_l2": float(flatten_head_vectors(full_delta).float().norm(dim=-1).mean().item()),
            "applied_delta_l2": float(flatten_head_vectors(applied_delta).float().norm(dim=-1).mean().item()),
            "projector_rank": int(self.projector_basis.shape[1]) if self.projector_basis is not None else None,
            "projector_component": (
                "orthogonal_complement" if self.projector_complement else "parallel"
            ) if self.projector_basis is not None else "full",
            "exact_full_endpoint_assignment": exact_full_endpoint,
            "exact_full_endpoint_max_abs_error": endpoint_error,
            "intervention_surface": "exact full-source eager recomposition of ROI Value swap -> selected-query-head delta before shared W_O",
        })
        return _project_attention_output(module, merged, hidden_states), weights

    def __enter__(self) -> "ROIValueDeltaIntervention":
        if self._original_forward is not None:
            raise RuntimeError("ROI Value intervention context is already active")
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


__all__ = [
    "CaptureQwenROIValueState",
    "ROIValueDeltaIntervention",
    "roi_head_delta_from_states",
]
