"""Native-GQA prior-cache capture and suppression/cache/residual joint scoring."""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager, ExitStack
from typing import Any

import torch
from transformers.models.qwen3_vl.modeling_qwen3_vl import eager_attention_forward

from visual_reasoning.stage3b2.switching import _AttentionInterfaceContext
from visual_reasoning.stage3b4.runtime import absolute_intervention_position
from visual_reasoning.stage3b5.boundaries import (
    CaptureCurrentBlockBoundaries,
    CurrentPositionBoundaryPatch,
    valid_boundary_patch_audit,
)
from visual_reasoning.stage3c3.runtime import score_evidence_suffix
from visual_reasoning.stage3c4.runtime import SourceContributionWindowPatch
from visual_reasoning.stage3c5.carriers import CaptureTokenKV
from visual_reasoning.stage3c5.carriers import LayerTokenSourcePatch, select_captured_positions


CANDIDATES = ("original_candidate", "counterfactual_candidate")
CACHE_MODES = frozenset({"K", "V", "KV"})


def _maximum(value: torch.Tensor) -> float:
    return float(value.abs().max().item()) if value.numel() else 0.0


def _preference(candidates: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    left, right = candidates[CANDIDATES[0]], candidates[CANDIDATES[1]]
    return {
        "L_o": float(left["mean_log_probability"]),
        "L_c": float(right["mean_log_probability"]),
        "D": float(left["mean_log_probability"]) - float(right["mean_log_probability"]),
        "finite": bool(left["finite"] and right["finite"]),
        CANDIDATES[0]: left,
        CANDIDATES[1]: right,
    }


def replace_prior_cache_entry(
    key: torch.Tensor,
    value: torch.Tensor,
    *,
    source_key: torch.Tensor,
    source_value: torch.Tensor,
    tpre_position: int,
    mode: str,
    visual_positions: Sequence[int] = (),
    current_query_position: int | None = None,
) -> tuple[torch.Tensor, torch.Tensor, dict[str, Any]]:
    """Replace K, V, or K+V at one prior-token position in native KV-head space."""

    if key.ndim != 4 or value.shape != key.shape:
        raise ValueError("Recipient K/V must match [batch,native KV-head,sequence,head_dim]")
    position = int(tpre_position)
    if not 0 <= position < int(key.shape[2]):
        raise ValueError("t_pre cache position is outside the sequence")
    if position in {int(item) for item in visual_positions}:
        raise ValueError("t_pre cache entry may not be a visual position")
    if current_query_position is not None and position == int(current_query_position):
        raise ValueError("t_pre cache entry may not be the current query position")
    normalized_mode = str(mode).upper()
    if normalized_mode not in CACHE_MODES:
        raise ValueError(f"Unsupported cache mode: {mode}")
    expected = (int(key.shape[0]), int(key.shape[1]), 1, int(key.shape[3]))
    if tuple(source_key.shape) != expected or tuple(source_value.shape) != expected:
        raise ValueError(f"Donor tensors must use the native KV-head layout {expected}")
    patched_key, patched_value = key.clone(), value.clone()
    recipient_key = key[:, :, position : position + 1, :]
    recipient_value = value[:, :, position : position + 1, :]
    if normalized_mode in {"K", "KV"}:
        patched_key[:, :, position : position + 1, :] = source_key.to(key.device, key.dtype)
    if normalized_mode in {"V", "KV"}:
        patched_value[:, :, position : position + 1, :] = source_value.to(value.device, value.dtype)
    keep = torch.ones(int(key.shape[2]), dtype=torch.bool, device=key.device)
    keep[position] = False
    return patched_key, patched_value, {
        "mode": normalized_mode,
        "positions_replaced": [position],
        "native_kv_head_count": int(key.shape[1]),
        "head_dimension": int(key.shape[3]),
        "recipient_key_exact_source_before_patch": bool(torch.equal(recipient_key, source_key.to(key.device, key.dtype))),
        "recipient_value_exact_source_before_patch": bool(torch.equal(recipient_value, source_value.to(value.device, value.dtype))),
        "selected_key_exact_expected": bool(torch.equal(patched_key[:, :, position : position + 1, :], source_key.to(key.device, key.dtype) if normalized_mode in {"K", "KV"} else recipient_key)),
        "selected_value_exact_expected": bool(torch.equal(patched_value[:, :, position : position + 1, :], source_value.to(value.device, value.dtype) if normalized_mode in {"V", "KV"} else recipient_value)),
        "non_tpre_key_max_abs_delta": _maximum(patched_key[:, :, keep, :] - key[:, :, keep, :]),
        "non_tpre_value_max_abs_delta": _maximum(patched_value[:, :, keep, :] - value[:, :, keep, :]),
        "unselected_component_key_max_abs_delta": _maximum(patched_key - key) if normalized_mode == "V" else 0.0,
        "unselected_component_value_max_abs_delta": _maximum(patched_value - value) if normalized_mode == "K" else 0.0,
        "visual_positions_replaced": [],
        "current_query_position_replaced": False,
        "post_rope_key": True,
        "projected_value": True,
    }


class PriorCacheEntryPatch(AbstractContextManager["PriorCacheEntryPatch"]):
    """Expose donor native K/V at t_pre only to current/future query rows."""

    def __init__(
        self, *, model: Any, donor_layers: Mapping[int, tuple[torch.Tensor, torch.Tensor]],
        selected_layers: Sequence[int], tpre_position: int, current_query_position: int,
        visual_positions: Sequence[int], mode: str,
    ) -> None:
        self.model = model
        self.donor_layers = dict(donor_layers)
        self.selected_layers = frozenset(int(item) for item in selected_layers)
        self.tpre_position = int(tpre_position)
        self.current_position = int(current_query_position)
        self.visual_positions = tuple(sorted({int(item) for item in visual_positions}))
        self.mode = str(mode).upper()
        if set(self.donor_layers) != set(self.selected_layers):
            raise ValueError("Donor layer set must equal selected layer set")
        if self.tpre_position >= self.current_position:
            raise ValueError("t_pre must precede the current query")
        self.audit: list[dict[str, Any]] = []
        self._interface: _AttentionInterfaceContext | None = None

    def _forward(
        self, module: Any, query: torch.Tensor, key: torch.Tensor, value: torch.Tensor,
        attention_mask: torch.Tensor | None, scaling: float, dropout: float = 0.0, **kwargs: Any,
    ):
        layer = int(module.layer_idx)
        baseline_output, baseline_weights = eager_attention_forward(
            module, query, key, value, attention_mask, scaling=scaling, dropout=dropout, **kwargs
        )
        query_length = int(query.shape[2])
        query_start = int(key.shape[2]) - query_length
        current_rows = [row for row in range(query_length) if query_start + row >= self.current_position]
        current_snapshot = query[:, :, current_rows, :].detach().clone() if current_rows else query[:, :, :0, :]
        if layer not in self.selected_layers:
            self.audit.append({
                "layer_index": layer, "layer_selected": False, "mode": self.mode,
                "positions_replaced": [], "switched_absolute_query_indices": [],
                "query_max_abs_delta": 0.0, "visual_positions_replaced": [],
                "current_query_position_replaced": False,
            })
            return baseline_output, baseline_weights
        donor_key, donor_value = self.donor_layers[layer]
        hybrid_key, hybrid_value, audit = replace_prior_cache_entry(
            key, value, source_key=donor_key, source_value=donor_value,
            tpre_position=self.tpre_position, mode=self.mode,
            visual_positions=self.visual_positions, current_query_position=self.current_position,
        )
        donor_differs = not (
            audit["recipient_key_exact_source_before_patch"] if self.mode == "K" else
            audit["recipient_value_exact_source_before_patch"] if self.mode == "V" else
            audit["recipient_key_exact_source_before_patch"] and audit["recipient_value_exact_source_before_patch"]
        )
        if current_rows and donor_differs:
            switched_output, switched_weights = eager_attention_forward(
                module, query, hybrid_key, hybrid_value, attention_mask,
                scaling=scaling, dropout=dropout, **kwargs,
            )
            output, weights = baseline_output.clone(), baseline_weights.clone()
            output[:, current_rows, :, :] = switched_output[:, current_rows, :, :]
            weights[:, :, current_rows, :] = switched_weights[:, :, current_rows, :]
        else:
            output, weights = baseline_output, baseline_weights
        audit.update({
            "layer_index": layer,
            "layer_selected": True,
            "first_patched_absolute_query": self.current_position,
            "switched_absolute_query_indices": [query_start + row for row in current_rows],
            "queries_before_current_modified": 0,
            "query_rows_recomputed": len(current_rows),
            "query_vectors_replaced": 0,
            "query_max_abs_delta": _maximum(query[:, :, current_rows, :] - current_snapshot) if current_rows else 0.0,
        })
        self.audit.append(audit)
        return output, weights

    def __enter__(self) -> "PriorCacheEntryPatch":
        self._interface = _AttentionInterfaceContext(
            model=self.model, name="stage3c7_prior_cache_entry_patch", function=self._forward
        )
        self._interface.__enter__()
        return self

    def close(self) -> None:
        if self._interface is not None:
            self._interface.close()
            self._interface = None

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


def cache_delta_summaries(
    native: Mapping[int, tuple[torch.Tensor, torch.Tensor]],
    suppressed: Mapping[int, tuple[torch.Tensor, torch.Tensor]],
) -> list[dict[str, Any]]:
    if set(native) != set(suppressed):
        raise ValueError("Native and suppressed cache layers differ")
    rows = []
    for layer in sorted(native):
        nk, nv = native[layer]
        sk, sv = suppressed[layer]
        if nk.shape != sk.shape or nv.shape != sv.shape:
            raise ValueError("Native/suppressed cache layouts differ")
        dk, dv = nk.float() - sk.float(), nv.float() - sv.float()
        rows.append({
            "layer": int(layer), "key_shape": list(nk.shape), "value_shape": list(nv.shape),
            "key_delta_l2": float(torch.linalg.vector_norm(dk).item()),
            "value_delta_l2": float(torch.linalg.vector_norm(dv).item()),
            "key_max_abs_delta": _maximum(dk), "value_max_abs_delta": _maximum(dv),
            "finite": bool(torch.isfinite(dk).all() and torch.isfinite(dv).all()),
        })
    return rows


def _suppression_patches(
    *, model: Any, absolute_tpre: int, layers: Sequence[int], source_positions: Sequence[int],
    selected_heads: Sequence[int], gain: float,
) -> list[SourceContributionWindowPatch]:
    return [
        SourceContributionWindowPatch(
            model=model, layer_index=int(layer), query_positions=[int(absolute_tpre)],
            selected_heads=selected_heads, source_positions=source_positions, gain=float(gain),
        )
        for layer in sorted({int(item) for item in layers})
    ]


@torch.inference_mode()
def capture_native_or_suppressed_states(
    *, model: Any, prepared: dict[str, Any], prefix_token_ids: Sequence[int],
    bridge_token_ids: Sequence[int], original_suffix_ids: Sequence[int],
    counterfactual_suffix_ids: Sequence[int], current_generated_index: int,
    tpre_generated_index: int, cache_layers: Sequence[int], residual_layer: int,
    suppression_enabled: bool, suppression_layers: Sequence[int], source_positions: Sequence[int],
    selected_heads: Sequence[int], seed: int, additional_cache_positions: Sequence[int] = (),
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    prompt_length = int(prepared["input_ids"].shape[1])
    current = absolute_intervention_position(prompt_length=prompt_length, intervention_generated_index=current_generated_index)
    tpre = absolute_intervention_position(prompt_length=prompt_length, intervention_generated_index=tpre_generated_index)
    candidates: dict[str, Any] = {}
    states: dict[str, dict[str, Any]] = {}
    capture_positions = sorted({tpre, *[int(item) for item in additional_cache_positions]})
    for candidate, suffix in zip(CANDIDATES, (original_suffix_ids, counterfactual_suffix_ids)):
        capture_cache = CaptureTokenKV(model=model, positions=capture_positions, selected_layers=cache_layers)
        capture_residual = CaptureCurrentBlockBoundaries(model=model, position=current, layer_indices=[residual_layer])
        patches = _suppression_patches(
            model=model, absolute_tpre=tpre, layers=suppression_layers,
            source_positions=source_positions, selected_heads=selected_heads, gain=0.0,
        ) if suppression_enabled else []
        with ExitStack() as stack:
            stack.enter_context(capture_residual)
            stack.enter_context(capture_cache)
            for patch in patches:
                stack.enter_context(patch)
            candidates[candidate] = score_evidence_suffix(
                model=model, prepared=prepared, prefix_token_ids=prefix_token_ids,
                bridge_token_ids=bridge_token_ids, suffix_token_ids=suffix, seed=seed,
            )
        states[candidate] = {
            "cache": capture_cache.complete(),
            "cache_positions": capture_positions,
            "cache_audit": copy.deepcopy(capture_cache.audit),
            "residual": capture_residual.complete_states(),
            "residual_audit": copy.deepcopy(capture_residual.audit),
            "suppression_audit": [patch.complete() for patch in patches],
        }
    result = _preference(candidates)
    result.update({
        "current_generated_index": current_generated_index, "current_absolute_position": current,
        "tpre_generated_index": tpre_generated_index, "tpre_absolute_position": tpre,
        "suppression_enabled": suppression_enabled,
    })
    return result, states


@torch.inference_mode()
def score_suppressed_with_rescue(
    *, model: Any, prepared: dict[str, Any], prefix_token_ids: Sequence[int],
    bridge_token_ids: Sequence[int], original_suffix_ids: Sequence[int],
    counterfactual_suffix_ids: Sequence[int], current_generated_index: int,
    tpre_generated_index: int, suppression_layers: Sequence[int], source_positions: Sequence[int],
    selected_heads: Sequence[int], native_states: Mapping[str, Mapping[str, Any]],
    cache_layers: Sequence[int], cache_mode: str | None,
    residual_layer: int | None, residual_boundary: str | None,
    visual_positions: Sequence[int], seed: int, suppression_enabled: bool = True,
) -> dict[str, Any]:
    prompt_length = int(prepared["input_ids"].shape[1])
    current = absolute_intervention_position(prompt_length=prompt_length, intervention_generated_index=current_generated_index)
    tpre = absolute_intervention_position(prompt_length=prompt_length, intervention_generated_index=tpre_generated_index)
    candidates: dict[str, Any] = {}
    cache_audits: dict[str, Any] = {}
    residual_audits: dict[str, Any] = {}
    suppression_audits: dict[str, Any] = {}
    event_orders: dict[str, list[str]] = {}
    for candidate, suffix in zip(CANDIDATES, (original_suffix_ids, counterfactual_suffix_ids)):
        patches = _suppression_patches(
            model=model, absolute_tpre=tpre, layers=suppression_layers,
            source_positions=source_positions, selected_heads=selected_heads, gain=0.0,
        ) if suppression_enabled else []
        cache_patch = None
        if cache_mode is not None:
            donor_tpre = select_captured_positions(
                native_states[candidate]["cache"],
                captured_positions=native_states[candidate]["cache_positions"],
                selected_positions=[tpre],
            )
            cache_patch = PriorCacheEntryPatch(
                model=model, donor_layers={int(layer): donor_tpre[int(layer)] for layer in cache_layers},
                selected_layers=cache_layers, tpre_position=tpre, current_query_position=current,
                visual_positions=visual_positions, mode=cache_mode,
            )
        residual_patch = None
        if residual_layer is not None:
            assert residual_boundary is not None
            residual_patch = CurrentPositionBoundaryPatch(
                model=model, position=current, layer_index=int(residual_layer), boundary=residual_boundary,
                source_state=native_states[candidate]["residual"][residual_boundary][int(residual_layer)],
            )
        with ExitStack() as stack:
            if cache_patch is not None:
                stack.enter_context(cache_patch)
            for patch in patches:
                stack.enter_context(patch)
            if residual_patch is not None:
                stack.enter_context(residual_patch)
            candidates[candidate] = score_evidence_suffix(
                model=model, prepared=prepared, prefix_token_ids=prefix_token_ids,
                bridge_token_ids=bridge_token_ids, suffix_token_ids=suffix, seed=seed,
            )
        cache_audits[candidate] = copy.deepcopy(cache_patch.audit) if cache_patch is not None else []
        residual_audits[candidate] = copy.deepcopy(residual_patch.audit) if residual_patch is not None else []
        suppression_audits[candidate] = [patch.complete() for patch in patches]
        cache_events = [f"L{row['layer_index']}:cache_attention" for row in cache_audits[candidate] if row.get("layer_selected")]
        residual_events = [f"L{residual_layer}:{residual_boundary}"] if residual_patch is not None else []
        event_orders[candidate] = sorted(cache_events + residual_events, key=lambda value: (int(value.split(':')[0][1:]), 0 if value.endswith('h_pre') else 2 if value.endswith('h_post_attn') else 1))
    result = _preference(candidates)
    result.update({
        "current_generated_index": current_generated_index, "current_absolute_position": current,
        "tpre_generated_index": tpre_generated_index, "tpre_absolute_position": tpre,
        "cache_mode": cache_mode, "cache_layers": sorted({int(item) for item in cache_layers}),
        "residual_layer": residual_layer, "residual_boundary": residual_boundary,
        "cache_patch_audits": cache_audits, "residual_patch_audits": residual_audits,
        "suppression_audits": suppression_audits, "joint_event_order": event_orders,
        "visual_kv_donor_patched": False, "current_query_kv_donor_patched": False,
        "past_non_tpre_kv_donor_patched": False,
        "suppression_enabled": bool(suppression_enabled),
        "residual_patch_audits_valid": bool(
            residual_layer is None or all(
                valid_boundary_patch_audit(
                    residual_audits[candidate], layer_index=int(residual_layer),
                    boundary=str(residual_boundary), position=current,
                ) for candidate in CANDIDATES
            )
        ),
    })
    return result


@torch.inference_mode()
def score_suppressed_with_prompt_cache_control(
    *, model: Any, prepared: dict[str, Any], prefix_token_ids: Sequence[int],
    bridge_token_ids: Sequence[int], original_suffix_ids: Sequence[int],
    counterfactual_suffix_ids: Sequence[int], current_generated_index: int,
    tpre_generated_index: int, suppression_layers: Sequence[int], source_positions: Sequence[int],
    selected_heads: Sequence[int], native_states: Mapping[str, Mapping[str, Any]],
    prompt_positions: Sequence[int], visual_positions: Sequence[int], seed: int,
) -> dict[str, Any]:
    """Replace frozen question/prompt cache entries while recreating P4 suppression."""

    prompt_length = int(prepared["input_ids"].shape[1])
    current = absolute_intervention_position(prompt_length=prompt_length, intervention_generated_index=current_generated_index)
    tpre = absolute_intervention_position(prompt_length=prompt_length, intervention_generated_index=tpre_generated_index)
    candidates: dict[str, Any] = {}
    patch_audits: dict[str, Any] = {}
    suppression_audits: dict[str, Any] = {}
    for candidate, suffix in zip(CANDIDATES, (original_suffix_ids, counterfactual_suffix_ids)):
        donor = select_captured_positions(
            native_states[candidate]["cache"],
            captured_positions=native_states[candidate]["cache_positions"],
            selected_positions=prompt_positions,
        )
        patch = LayerTokenSourcePatch(
            model=model, source_layers=donor, source_positions=prompt_positions,
            selected_layers=suppression_layers, first_patched_absolute_query=current,
            visual_positions=visual_positions,
        )
        suppressions = _suppression_patches(
            model=model, absolute_tpre=tpre, layers=suppression_layers,
            source_positions=source_positions, selected_heads=selected_heads, gain=0.0,
        )
        with ExitStack() as stack:
            stack.enter_context(patch)
            for suppression in suppressions:
                stack.enter_context(suppression)
            candidates[candidate] = score_evidence_suffix(
                model=model, prepared=prepared, prefix_token_ids=prefix_token_ids,
                bridge_token_ids=bridge_token_ids, suffix_token_ids=suffix, seed=seed,
            )
        patch_audits[candidate] = copy.deepcopy(patch.audit)
        suppression_audits[candidate] = [suppression.complete() for suppression in suppressions]
    result = _preference(candidates)
    result.update({
        "prompt_positions": sorted({int(item) for item in prompt_positions}),
        "cache_layers": sorted({int(item) for item in suppression_layers}),
        "patch_audits": patch_audits, "suppression_audits": suppression_audits,
        "visual_kv_donor_patched": False, "current_query_kv_donor_patched": False,
    })
    return result


__all__ = [
    "CANDIDATES", "PriorCacheEntryPatch", "cache_delta_summaries",
    "capture_native_or_suppressed_states", "replace_prior_cache_entry",
    "score_suppressed_with_prompt_cache_control", "score_suppressed_with_rescue",
]
