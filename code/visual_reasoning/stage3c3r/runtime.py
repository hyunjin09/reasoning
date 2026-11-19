"""Exact pre-W_O source-contribution gain intervention for Qwen3-VL."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager, ExitStack
from types import MethodType
from typing import Any

import torch

from visual_reasoning.stage3b4.runtime import absolute_intervention_position
from visual_reasoning.stage3b6.heads import _attention_module, _project_attention_output
from visual_reasoning.stage3c1.metrics import _repeat_kv
from visual_reasoning.stage3c3.runtime import _projection_parts, _run_attention, score_evidence_suffix


def _maximum(tensor: torch.Tensor) -> float:
    return float(tensor.abs().max().item()) if tensor.numel() else 0.0


def apply_source_contribution_gain(
    head_output: torch.Tensor,
    attention: torch.Tensor,
    repeated_value: torch.Tensor,
    *,
    source_positions: Sequence[int],
    selected_heads: Sequence[int],
    query_position: int,
    gain: float,
) -> tuple[torch.Tensor, torch.Tensor, dict[str, Any]]:
    """Scale one source group's contribution in selected logical heads.

    Layouts are head_output [B,Q,H,D], attention [B,H,Q,K], and expanded
    value [B,H,K,D]. Attention and Value are read but never modified.
    """

    if head_output.ndim != 4 or attention.ndim != 4 or repeated_value.ndim != 4:
        raise ValueError("Expected head_output [B,Q,H,D] and attention/value [B,H,Q/K,D]")
    batch, query_count, head_count, head_dim = map(int, head_output.shape)
    if tuple(attention.shape[:3]) != (batch, head_count, query_count):
        raise ValueError("Attention layout does not align with head output")
    if tuple(repeated_value.shape[:2]) != (batch, head_count):
        raise ValueError("Expanded Value layout does not align with logical heads")
    if int(repeated_value.shape[2]) < int(attention.shape[3]) or int(repeated_value.shape[3]) != head_dim:
        raise ValueError("Expanded Value source/dimension layout is incompatible")
    position = int(query_position)
    if not 0 <= position < query_count:
        raise ValueError("Query position is outside the sequence")
    heads = sorted({int(value) for value in selected_heads})
    sources = sorted({int(value) for value in source_positions})
    if not heads or heads[0] < 0 or heads[-1] >= head_count:
        raise ValueError("Selected logical head is outside the model")
    visible_sources = position + 1
    if not sources or sources[0] < 0 or sources[-1] >= visible_sources:
        raise ValueError("Source position is outside the causally visible sequence")
    scalar_gain = float(gain)
    if not math.isfinite(scalar_gain) or scalar_gain < 0.0:
        raise ValueError("Gain must be finite and nonnegative")

    source_index = torch.tensor(sources, dtype=torch.long, device=head_output.device)
    alpha = attention[:, heads, position, :visible_sources][:, :, source_index]
    values = repeated_value[:, heads, :visible_sources, :][:, :, source_index, :]
    contribution = (alpha[..., None].to(values.dtype) * values).sum(dim=2).float()
    native_selected = head_output[:, position, heads, :]
    native_float = native_selected.float()
    rest = native_float - contribution
    partition_error = _maximum(contribution + rest - native_float)

    if scalar_gain == 1.0:
        patched = head_output
    else:
        patched = head_output.clone()
        patched[:, position, heads, :] = (
            rest + scalar_gain * contribution
        ).to(native_selected.dtype)
    expected_selected = (rest + scalar_gain * contribution).to(native_selected.dtype)
    delta = patched - head_output
    nonselected = [head for head in range(head_count) if head not in heads]
    other_positions = [index for index in range(query_count) if index != position]
    audit = {
        "selected_heads": heads,
        "source_positions": sources,
        "query_position": position,
        "gain": scalar_gain,
        "partition_compute_dtype": "float32",
        "head_output_shape": list(head_output.shape),
        "attention_shape": list(attention.shape),
        "expanded_value_shape": list(repeated_value.shape),
        "partition_max_abs_error": partition_error,
        "selected_head_expected_max_abs_error": _maximum(
            patched[:, position, heads, :] - expected_selected
        ),
        "nonselected_head_max_abs_delta": (
            _maximum(delta[:, position, nonselected, :]) if nonselected else 0.0
        ),
        "other_position_max_abs_delta": (
            _maximum(delta[:, other_positions, :, :]) if other_positions else 0.0
        ),
        "lambda_one_exact": bool(scalar_gain != 1.0 or torch.equal(patched, head_output)),
        "lambda_zero_exact": bool(
            scalar_gain != 0.0
            or torch.equal(patched[:, position, heads, :], rest.to(native_selected.dtype))
        ),
        "qkv_directly_modified": False,
        "attention_directly_modified": False,
        "all_outputs_finite": bool(
            torch.isfinite(patched).all().item() and torch.isfinite(contribution).all().item()
        ),
    }
    return patched, contribution, audit


def _contribution_summary(
    contribution: torch.Tensor,
    *,
    heads: Sequence[int],
    wo_weight: torch.Tensor,
    gain: float,
) -> dict[str, Any]:
    head_dim = int(contribution.shape[-1])
    per_head_native = contribution.float().norm(dim=-1).mean(dim=0)
    scaled = contribution.float() * float(gain)
    per_head_scaled = scaled.norm(dim=-1).mean(dim=0)
    post_native = []
    post_scaled = []
    for index, head in enumerate(heads):
        weight = wo_weight[:, int(head) * head_dim : (int(head) + 1) * head_dim].float()
        post_native.append(torch.nn.functional.linear(contribution[:, index, :].float(), weight))
        post_scaled.append(torch.nn.functional.linear(scaled[:, index, :], weight))
    native_sum = torch.stack(post_native, dim=0).sum(dim=0)
    scaled_sum = torch.stack(post_scaled, dim=0).sum(dim=0)
    return {
        "per_head_native_norm": per_head_native.cpu().tolist(),
        "per_head_scaled_norm": per_head_scaled.cpu().tolist(),
        "mean_native_head_norm": float(per_head_native.mean().item()),
        "mean_scaled_head_norm": float(per_head_scaled.mean().item()),
        "concatenated_native_norm": float(contribution.float().reshape(contribution.shape[0], -1).norm(dim=-1).mean().item()),
        "concatenated_scaled_norm": float(scaled.reshape(scaled.shape[0], -1).norm(dim=-1).mean().item()),
        "head_set_post_wo_native_sum_norm": float(native_sum.norm(dim=-1).mean().item()),
        "head_set_post_wo_scaled_sum_norm": float(scaled_sum.norm(dim=-1).mean().item()),
    }


class SourceContributionGainPatch(AbstractContextManager["SourceContributionGainPatch"]):
    """Scale one locally computed source contribution before `W_O`."""

    def __init__(
        self,
        *,
        model: Any,
        layer_index: int,
        position: int,
        selected_heads: Sequence[int],
        source_positions: Sequence[int],
        gain: float,
        audit_groups: Mapping[str, Sequence[int]],
    ) -> None:
        self.layer_index = int(layer_index)
        self.position = int(position)
        self.selected_heads = sorted({int(value) for value in selected_heads})
        self.source_positions = sorted({int(value) for value in source_positions})
        self.gain = float(gain)
        self.audit_groups = {
            str(name): sorted({int(value) for value in positions})
            for name, positions in audit_groups.items()
        }
        self.module = _attention_module(model, self.layer_index)
        self.result: dict[str, Any] | None = None
        self._original_forward: Any | None = None

    def _run(
        self,
        module: torch.nn.Module,
        hidden_states: torch.Tensor,
        position_embeddings: tuple[torch.Tensor, torch.Tensor],
        attention_mask: torch.Tensor | None,
        past_key_values: Any | None = None,
        **kwargs: Any,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        if self.result is not None:
            raise RuntimeError("Contribution gain patch executed more than once")
        pre_q, pre_k, query, key, value = _projection_parts(module, hidden_states, position_embeddings)
        if past_key_values is not None:
            key, value = past_key_values.update(key, value, int(module.layer_idx))
        native_output, attention = _run_attention(module, query, key, value, attention_mask, kwargs)
        repeated_value = _repeat_kv(value, int(module.num_key_value_groups))
        query_snapshot = query[:, :, self.position, :].detach().clone()
        key_snapshot = key.detach().clone()
        value_snapshot = value.detach().clone()
        attention_snapshot = attention[:, :, self.position, : self.position + 1].detach().clone()
        patched_output, contribution, audit = apply_source_contribution_gain(
            native_output,
            attention,
            repeated_value,
            source_positions=self.source_positions,
            selected_heads=self.selected_heads,
            query_position=self.position,
            gain=self.gain,
        )
        group_summaries: dict[str, Any] = {}
        for name, positions in self.audit_groups.items():
            index = torch.tensor(positions, dtype=torch.long, device=value.device)
            group_alpha = attention[:, self.selected_heads, self.position, : self.position + 1][:, :, index]
            group_value = repeated_value[:, self.selected_heads, : self.position + 1, :][:, :, index, :]
            group_contribution = (group_alpha[..., None].to(group_value.dtype) * group_value).sum(dim=2)
            group_summaries[name] = _contribution_summary(
                group_contribution,
                heads=self.selected_heads,
                wo_weight=module.o_proj.weight,
                gain=self.gain if positions == self.source_positions else 1.0,
            )
        self.result = {
            **audit,
            "layer_index": self.layer_index,
            "target_contribution": _contribution_summary(
                contribution,
                heads=self.selected_heads,
                wo_weight=module.o_proj.weight,
                gain=self.gain,
            ),
            "audit_group_contributions": group_summaries,
            "query_max_abs_delta": _maximum(query[:, :, self.position, :] - query_snapshot),
            "key_max_abs_delta": _maximum(key - key_snapshot),
            "value_max_abs_delta": _maximum(value - value_snapshot),
            "attention_max_abs_delta": _maximum(
                attention[:, :, self.position, : self.position + 1] - attention_snapshot
            ),
            "local_attention_is_native_for_current_layer_input": True,
        }
        return _project_attention_output(module, patched_output, hidden_states), attention

    def __enter__(self) -> "SourceContributionGainPatch":
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
                module, hidden_states, position_embeddings, attention_mask, past_key_values, **kwargs
            )

        self.module.forward = MethodType(forward, self.module)
        return self

    def complete(self) -> dict[str, Any]:
        if self.result is None:
            raise RuntimeError("Contribution gain patch did not execute")
        return self.result

    def close(self) -> None:
        if self._original_forward is not None:
            self.module.forward = self._original_forward
            self._original_forward = None

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


def _preference(original: Mapping[str, Any], counterfactual: Mapping[str, Any]) -> dict[str, Any]:
    lo = float(original["mean_log_probability"])
    lc = float(counterfactual["mean_log_probability"])
    return {
        "L_o": lo,
        "L_c": lc,
        "D": lo - lc,
        "finite": bool(original["finite"] and counterfactual["finite"]),
    }


@torch.inference_mode()
def score_gain_preference(
    *,
    model: Any,
    prepared: dict[str, Any],
    prefix_token_ids: Sequence[int],
    bridge_token_ids: Sequence[int],
    original_suffix_ids: Sequence[int],
    counterfactual_suffix_ids: Sequence[int],
    generated_index: int,
    layer_specs: Sequence[Mapping[str, Any]],
    gain: float,
    audit_groups: Mapping[str, Sequence[int]],
    seed: int,
) -> dict[str, Any]:
    """Score both frozen candidates under one- or multi-layer contribution gain."""

    position = absolute_intervention_position(
        prompt_length=int(prepared["input_ids"].shape[1]),
        intervention_generated_index=int(generated_index),
    )
    candidates: dict[str, Any] = {}
    audits: dict[str, list[dict[str, Any]]] = {}
    for name, suffix in (
        ("original_candidate", original_suffix_ids),
        ("counterfactual_candidate", counterfactual_suffix_ids),
    ):
        patches = [
            SourceContributionGainPatch(
                model=model,
                layer_index=int(spec["layer_index"]),
                position=position,
                selected_heads=spec["heads"],
                source_positions=spec["source_positions"],
                gain=float(gain),
                audit_groups=audit_groups,
            )
            for spec in layer_specs
        ]
        with ExitStack() as stack:
            for patch in patches:
                stack.enter_context(patch)
            candidates[name] = score_evidence_suffix(
                model=model,
                prepared=prepared,
                prefix_token_ids=prefix_token_ids,
                bridge_token_ids=bridge_token_ids,
                suffix_token_ids=suffix,
                seed=seed,
            )
        audits[name] = [patch.complete() for patch in patches]
    return {
        **_preference(candidates["original_candidate"], candidates["counterfactual_candidate"]),
        "original_candidate": candidates["original_candidate"],
        "counterfactual_candidate": candidates["counterfactual_candidate"],
        "candidate_audits": audits,
        "generated_index": int(generated_index),
        "absolute_position": position,
        "gain": float(gain),
        "layer_specs": [dict(spec) for spec in layer_specs],
    }


__all__ = [
    "SourceContributionGainPatch",
    "apply_source_contribution_gain",
    "score_gain_preference",
]
