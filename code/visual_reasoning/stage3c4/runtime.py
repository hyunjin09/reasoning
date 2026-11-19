"""Exact multi-layer, multi-query target-source contribution suppression."""

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


def apply_source_contribution_window(
    head_output: torch.Tensor,
    attention: torch.Tensor,
    repeated_value: torch.Tensor,
    *,
    source_positions: Sequence[int],
    selected_heads: Sequence[int],
    query_positions: Sequence[int],
    gain: float,
    query_position_offset: int = 0,
) -> tuple[torch.Tensor, dict[int, torch.Tensor], dict[str, Any]]:
    """Scale one source contribution at several queries, before ``W_O``.

    The native Attention result, Attention probabilities, and expanded Values
    are read-only. Source/rest bookkeeping is performed in FP32 and only the
    selected head-output rows are replaced.
    """

    if head_output.ndim != 4 or attention.ndim != 4 or repeated_value.ndim != 4:
        raise ValueError("Expected head_output [B,Q,H,D] and attention/value [B,H,Q/K,D]")
    batch, query_count, head_count, head_dim = map(int, head_output.shape)
    if tuple(attention.shape[:3]) != (batch, head_count, query_count):
        raise ValueError("Attention layout does not align with head output")
    if tuple(repeated_value.shape[:2]) != (batch, head_count):
        raise ValueError("Expanded Value layout does not align with logical heads")
    if int(repeated_value.shape[2]) < int(attention.shape[3]) or int(repeated_value.shape[3]) != head_dim:
        raise ValueError("Expanded Value layout is incompatible")
    heads = sorted({int(value) for value in selected_heads})
    sources = sorted({int(value) for value in source_positions})
    queries = sorted({int(value) for value in query_positions})
    offset = int(query_position_offset)
    absolute_queries = [offset + position for position in queries]
    if not heads or heads[0] < 0 or heads[-1] >= head_count:
        raise ValueError("Selected logical head is outside the model")
    if not sources or sources[0] < 0:
        raise ValueError("Source positions must be nonempty and nonnegative")
    if not queries or queries[0] < 0 or queries[-1] >= query_count:
        raise ValueError("Query positions must be nonempty and inside the sequence")
    if any(sources[-1] >= position + 1 for position in absolute_queries):
        raise ValueError("A source position is not causally visible at every selected query")
    scalar_gain = float(gain)
    if not math.isfinite(scalar_gain) or scalar_gain < 0.0:
        raise ValueError("Gain must be finite and nonnegative")

    patched = head_output if scalar_gain == 1.0 else head_output.clone()
    source_index = torch.tensor(sources, dtype=torch.long, device=head_output.device)
    contributions: dict[int, torch.Tensor] = {}
    partition_errors: list[float] = []
    expected_errors: list[float] = []
    per_query_native_norm: dict[str, float] = {}
    for position, absolute_position in zip(queries, absolute_queries):
        key_limit = min(absolute_position + 1, int(attention.shape[3]))
        alpha = attention[:, heads, position, :key_limit][:, :, source_index]
        values = repeated_value[:, heads, :key_limit, :][:, :, source_index, :]
        contribution = (alpha[..., None].to(values.dtype) * values).sum(dim=2).float()
        contributions[absolute_position] = contribution
        native_selected = head_output[:, position, heads, :]
        native_float = native_selected.float()
        rest = native_float - contribution
        expected = (rest + scalar_gain * contribution).to(native_selected.dtype)
        partition_errors.append(_maximum(contribution + rest - native_float))
        if scalar_gain != 1.0:
            patched[:, position, heads, :] = expected
        expected_errors.append(_maximum(patched[:, position, heads, :] - expected))
        per_query_native_norm[str(absolute_position)] = float(
            contribution.norm(dim=-1).mean().item()
        )

    delta = patched - head_output
    nonselected = [head for head in range(head_count) if head not in heads]
    outside = [position for position in range(query_count) if position not in queries]
    per_position = delta.abs().amax(dim=(0, 2, 3))
    changed = torch.nonzero(per_position > 0, as_tuple=False).flatten().tolist()
    audit = {
        "selected_heads": heads,
        "source_positions": sources,
        "query_positions": absolute_queries,
        "local_query_positions": queries,
        "query_position_offset": offset,
        "changed_query_positions": [offset + int(value) for value in changed],
        "gain": scalar_gain,
        "partition_compute_dtype": "float32",
        "head_output_shape": list(head_output.shape),
        "attention_shape": list(attention.shape),
        "expanded_value_shape": list(repeated_value.shape),
        "partition_max_abs_error": max(partition_errors, default=0.0),
        "selected_head_expected_max_abs_error": max(expected_errors, default=0.0),
        "nonselected_head_max_abs_delta": (
            _maximum(delta[:, :, nonselected, :]) if nonselected else 0.0
        ),
        "outside_window_max_abs_delta": _maximum(delta[:, outside, :, :]) if outside else 0.0,
        "lambda_one_exact": bool(scalar_gain != 1.0 or torch.equal(patched, head_output)),
        "lambda_zero_exact": bool(scalar_gain != 0.0 or max(expected_errors, default=0.0) == 0.0),
        "qkv_directly_modified": False,
        "attention_directly_modified": False,
        "per_query_native_contribution_norm": per_query_native_norm,
        "all_outputs_finite": bool(
            torch.isfinite(patched).all().item()
            and all(torch.isfinite(value).all().item() for value in contributions.values())
        ),
    }
    return patched, contributions, audit


class SourceContributionWindowPatch(AbstractContextManager["SourceContributionWindowPatch"]):
    """Suppress one source contribution at fixed queries in one language layer."""

    def __init__(
        self,
        *,
        model: Any,
        layer_index: int,
        query_positions: Sequence[int],
        selected_heads: Sequence[int],
        source_positions: Sequence[int],
        gain: float,
    ) -> None:
        self.layer_index = int(layer_index)
        self.query_positions = sorted({int(value) for value in query_positions})
        self.selected_heads = sorted({int(value) for value in selected_heads})
        self.source_positions = sorted({int(value) for value in source_positions})
        self.gain = float(gain)
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
            raise RuntimeError("Contribution window patch executed more than once")
        pre_q, pre_k, query, key, value = _projection_parts(module, hidden_states, position_embeddings)
        if past_key_values is not None:
            key, value = past_key_values.update(key, value, int(module.layer_idx))
        native_output, attention = _run_attention(module, query, key, value, attention_mask, kwargs)
        repeated_value = _repeat_kv(value, int(module.num_key_value_groups))
        query_start = int(key.shape[2]) - int(query.shape[2])
        local_queries = [position - query_start for position in self.query_positions]
        if not local_queries or local_queries[0] < 0 or local_queries[-1] >= int(query.shape[2]):
            raise RuntimeError("Contribution-window queries must all lie in the current cached chunk")
        query_snapshot = query[:, :, local_queries, :].detach().clone()
        key_snapshot = key.detach().clone()
        value_snapshot = value.detach().clone()
        attention_snapshot = attention[:, :, local_queries, :].detach().clone()
        patched_output, _, audit = apply_source_contribution_window(
            native_output,
            attention,
            repeated_value,
            source_positions=self.source_positions,
            selected_heads=self.selected_heads,
            query_positions=local_queries,
            query_position_offset=query_start,
            gain=self.gain,
        )
        self.result = {
            **audit,
            "layer_index": self.layer_index,
            "query_max_abs_delta": _maximum(query[:, :, local_queries, :] - query_snapshot),
            "key_max_abs_delta": _maximum(key - key_snapshot),
            "value_max_abs_delta": _maximum(value - value_snapshot),
            "attention_max_abs_delta": _maximum(
                attention[:, :, local_queries, :] - attention_snapshot
            ),
            "local_attention_is_native_for_current_layer_input": True,
            "downstream_recomputation_allowed": True,
        }
        return _project_attention_output(module, patched_output, hidden_states), attention

    def __enter__(self) -> "SourceContributionWindowPatch":
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
            raise RuntimeError("Contribution window patch did not execute")
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
def score_window_preference(
    *,
    model: Any,
    prepared: dict[str, Any],
    prefix_token_ids: Sequence[int],
    bridge_token_ids: Sequence[int],
    original_suffix_ids: Sequence[int],
    counterfactual_suffix_ids: Sequence[int],
    query_generated_indices: Sequence[int],
    layer_indices: Sequence[int],
    source_positions: Sequence[int],
    selected_heads: Sequence[int],
    gain: float,
    seed: int,
) -> dict[str, Any]:
    prompt_length = int(prepared["input_ids"].shape[1])
    generated = sorted({int(value) for value in query_generated_indices})
    positions = [
        absolute_intervention_position(
            prompt_length=prompt_length, intervention_generated_index=value
        )
        for value in generated
    ]
    layers = sorted({int(value) for value in layer_indices})
    if not layers:
        raise ValueError("At least one language layer is required")
    candidates: dict[str, Any] = {}
    audits: dict[str, list[dict[str, Any]]] = {}
    for name, suffix in (
        ("original_candidate", original_suffix_ids),
        ("counterfactual_candidate", counterfactual_suffix_ids),
    ):
        patches = [
            SourceContributionWindowPatch(
                model=model,
                layer_index=layer,
                query_positions=positions,
                selected_heads=selected_heads,
                source_positions=source_positions,
                gain=gain,
            )
            for layer in layers
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
        "query_generated_indices": generated,
        "absolute_query_positions": positions,
        "layer_indices": layers,
        "selected_heads": sorted({int(value) for value in selected_heads}),
        "source_positions": sorted({int(value) for value in source_positions}),
        "gain": float(gain),
    }


__all__ = [
    "SourceContributionWindowPatch",
    "apply_source_contribution_window",
    "score_window_preference",
]
