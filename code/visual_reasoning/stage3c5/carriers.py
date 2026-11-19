"""Nonvisual token-K/V and current-residual carrier interventions."""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager
from typing import Any

import torch
from transformers.models.qwen3_vl.modeling_qwen3_vl import eager_attention_forward

from visual_reasoning.stage3b2.switching import _AttentionInterfaceContext
from visual_reasoning.stage3b5.boundaries import (
    CaptureCurrentBlockBoundaries,
    CurrentPositionBoundaryPatch,
)
from visual_reasoning.stage3c3.runtime import score_evidence_suffix
from visual_reasoning.stage3c5.runtime import summarize_state


def _maximum(value: torch.Tensor) -> float:
    return float(value.abs().max().item()) if value.numel() else 0.0


def replace_token_kv_positions(
    key: torch.Tensor,
    value: torch.Tensor,
    *,
    source_key: torch.Tensor,
    source_value: torch.Tensor,
    positions: Sequence[int],
) -> tuple[torch.Tensor, torch.Tensor, dict[str, Any]]:
    if key.ndim != 4 or value.shape != key.shape:
        raise ValueError("Recipient K/V must be matching [batch,kv_head,sequence,head_dim]")
    indices = sorted({int(item) for item in positions})
    if not indices or indices[0] < 0 or indices[-1] >= int(key.shape[2]):
        raise ValueError("Carrier positions must be nonempty and inside the sequence")
    expected = (int(key.shape[0]), int(key.shape[1]), len(indices), int(key.shape[3]))
    if tuple(source_key.shape) != expected or tuple(source_value.shape) != expected:
        raise ValueError(f"Donor K/V shape mismatch: expected {expected}")
    recipient_key = key[:, :, indices, :]
    recipient_value = value[:, :, indices, :]
    key_match = bool(torch.equal(recipient_key, source_key.to(key.device, key.dtype)))
    value_match = bool(torch.equal(recipient_value, source_value.to(value.device, value.dtype)))
    patched_key = key.clone()
    patched_value = value.clone()
    patched_key[:, :, indices, :] = source_key.to(key.device, key.dtype)
    patched_value[:, :, indices, :] = source_value.to(value.device, value.dtype)
    keep = torch.ones(int(key.shape[2]), dtype=torch.bool, device=key.device)
    keep[indices] = False
    return patched_key, patched_value, {
        "positions_replaced": indices,
        "position_count": len(indices),
        "source_key_exact_recipient_match": key_match,
        "source_value_exact_recipient_match": value_match,
        "selected_key_exact_source_match": bool(torch.equal(patched_key[:, :, indices, :], source_key.to(key.device, key.dtype))),
        "selected_value_exact_source_match": bool(torch.equal(patched_value[:, :, indices, :], source_value.to(value.device, value.dtype))),
        "nonselected_key_max_abs_delta": _maximum(patched_key[:, :, keep, :] - key[:, :, keep, :]),
        "nonselected_value_max_abs_delta": _maximum(patched_value[:, :, keep, :] - value[:, :, keep, :]),
    }


class CaptureTokenKV(AbstractContextManager["CaptureTokenKV"]):
    """Capture post-RoPE K/V at frozen nonvisual positions and layers."""

    def __init__(self, *, model: Any, positions: Sequence[int], selected_layers: Sequence[int]) -> None:
        self.model = model
        self.positions = tuple(sorted({int(value) for value in positions}))
        self.selected_layers = frozenset(int(value) for value in selected_layers)
        layer_count = int(model.config.text_config.num_hidden_layers)
        if not self.positions or not self.selected_layers.issubset(set(range(layer_count))):
            raise ValueError("Invalid carrier positions or layers")
        self.layers: dict[int, tuple[torch.Tensor, torch.Tensor]] = {}
        self.audit: list[dict[str, Any]] = []
        self._interface: _AttentionInterfaceContext | None = None

    def _forward(
        self, module: Any, query: torch.Tensor, key: torch.Tensor, value: torch.Tensor,
        attention_mask: torch.Tensor | None, scaling: float, dropout: float = 0.0, **kwargs: Any,
    ):
        layer = int(module.layer_idx)
        selected = layer in self.selected_layers
        if selected:
            if layer in self.layers:
                raise RuntimeError(f"Layer {layer} carrier K/V captured more than once")
            if self.positions[0] < 0 or self.positions[-1] >= int(key.shape[2]):
                raise RuntimeError("Carrier capture position outside K/V sequence")
            captured_key = key[:, :, self.positions, :].detach().clone()
            captured_value = value[:, :, self.positions, :].detach().clone()
            self.layers[layer] = (captured_key, captured_value)
            self.audit.append({
                "layer_index": layer, "layer_selected": True,
                "positions": list(self.positions), "post_rope_key": True,
                "value_projection": True, "key_shape": list(captured_key.shape),
                "value_shape": list(captured_value.shape),
            })
        else:
            self.audit.append({"layer_index": layer, "layer_selected": False, "positions": []})
        return eager_attention_forward(
            module, query, key, value, attention_mask,
            scaling=scaling, dropout=dropout, **kwargs,
        )

    def __enter__(self) -> "CaptureTokenKV":
        self._interface = _AttentionInterfaceContext(
            model=self.model, name="stage3c5_capture_nonvisual_token_kv", function=self._forward
        )
        self._interface.__enter__()
        return self

    def complete(self) -> dict[int, tuple[torch.Tensor, torch.Tensor]]:
        if set(self.layers) != set(self.selected_layers):
            raise RuntimeError("Carrier K/V capture missed a selected layer")
        return dict(self.layers)

    def close(self) -> None:
        if self._interface is not None:
            self._interface.close()
            self._interface = None

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


def select_captured_positions(
    layers: Mapping[int, tuple[torch.Tensor, torch.Tensor]],
    *, captured_positions: Sequence[int], selected_positions: Sequence[int],
) -> dict[int, tuple[torch.Tensor, torch.Tensor]]:
    captured = [int(value) for value in captured_positions]
    selected = sorted({int(value) for value in selected_positions})
    lookup = {position: index for index, position in enumerate(captured)}
    if not selected or any(position not in lookup for position in selected):
        raise ValueError("Selected carrier position was not captured")
    indices = [lookup[position] for position in selected]
    return {
        int(layer): (key[:, :, indices, :], value[:, :, indices, :])
        for layer, (key, value) in layers.items()
    }


class LayerTokenSourcePatch(AbstractContextManager["LayerTokenSourcePatch"]):
    """Use donor nonvisual K/V for queries at/after t*, at frozen layers only."""

    def __init__(
        self, *, model: Any, source_layers: Mapping[int, tuple[torch.Tensor, torch.Tensor]],
        source_positions: Sequence[int], selected_layers: Sequence[int],
        first_patched_absolute_query: int, visual_positions: Sequence[int],
    ) -> None:
        self.model = model
        self.source_layers = dict(source_layers)
        self.source_positions = tuple(sorted({int(value) for value in source_positions}))
        self.selected_layers = frozenset(int(value) for value in selected_layers)
        self.first_query = int(first_patched_absolute_query)
        self.visual_positions = frozenset(int(value) for value in visual_positions)
        if set(self.source_positions) & self.visual_positions:
            raise ValueError("Carrier patch may not replace visual K/V")
        if self.first_query in self.source_positions:
            raise ValueError("Carrier patch may not replace current-query K/V")
        if set(self.source_layers) != set(self.selected_layers):
            raise ValueError("Donor K/V layers must exactly match selected layers")
        self.audit: list[dict[str, Any]] = []
        self._interface: _AttentionInterfaceContext | None = None

    def _forward(
        self, module: Any, query: torch.Tensor, key: torch.Tensor, value: torch.Tensor,
        attention_mask: torch.Tensor | None, scaling: float, dropout: float = 0.0, **kwargs: Any,
    ):
        layer = int(module.layer_idx)
        baseline_output, baseline_weights = eager_attention_forward(
            module, query, key, value, attention_mask,
            scaling=scaling, dropout=dropout, **kwargs,
        )
        if layer not in self.selected_layers:
            self.audit.append({
                "layer_index": layer, "layer_selected": False,
                "positions_replaced": [], "switched_absolute_query_indices": [],
                "visual_kv_entries_replaced": 0, "current_query_kv_replaced": False,
            })
            return baseline_output, baseline_weights
        source_key, source_value = self.source_layers[layer]
        hybrid_key, hybrid_value, replacement = replace_token_kv_positions(
            key, value, source_key=source_key, source_value=source_value,
            positions=self.source_positions,
        )
        query_length = int(query.shape[2])
        query_start = int(key.shape[2]) - query_length
        active_rows = [row for row in range(query_length) if query_start + row >= self.first_query]
        if not active_rows or (
            replacement["source_key_exact_recipient_match"]
            and replacement["source_value_exact_recipient_match"]
        ):
            output, weights = baseline_output, baseline_weights
        else:
            switched_output, switched_weights = eager_attention_forward(
                module, query, hybrid_key, hybrid_value, attention_mask,
                scaling=scaling, dropout=dropout, **kwargs,
            )
            output = baseline_output.clone()
            weights = baseline_weights.clone()
            output[:, active_rows, :, :] = switched_output[:, active_rows, :, :]
            weights[:, :, active_rows, :] = switched_weights[:, :, active_rows, :]
        active_absolute = [query_start + row for row in active_rows]
        self.audit.append({
            "layer_index": layer, "layer_selected": True, **replacement,
            "first_patched_absolute_query": self.first_query,
            "switched_absolute_query_indices": active_absolute,
            "queries_before_threshold_modified": sum(value < self.first_query for value in active_absolute),
            "visual_kv_entries_replaced": len(set(self.source_positions) & self.visual_positions),
            "current_query_kv_replaced": self.first_query in self.source_positions,
            "query_rows_replaced": len(active_rows),
            "query_vectors_replaced": 0,
        })
        return output, weights

    def __enter__(self) -> "LayerTokenSourcePatch":
        self._interface = _AttentionInterfaceContext(
            model=self.model, name="stage3c5_nonvisual_token_source_patch", function=self._forward
        )
        self._interface.__enter__()
        return self

    def close(self) -> None:
        if self._interface is not None:
            self._interface.close()
            self._interface = None

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


def _preference(original: Mapping[str, Any], counterfactual: Mapping[str, Any]) -> dict[str, Any]:
    lo = float(original["mean_log_probability"])
    lc = float(counterfactual["mean_log_probability"])
    return {"L_o": lo, "L_c": lc, "D": lo - lc, "finite": bool(original["finite"] and counterfactual["finite"])}


@torch.inference_mode()
def capture_preference_carrier_states(
    *, model: Any, prepared: dict[str, Any], prefix_token_ids: Sequence[int],
    bridge_token_ids: Sequence[int], original_suffix_ids: Sequence[int],
    counterfactual_suffix_ids: Sequence[int], capture_positions: Sequence[int],
    selected_layers: Sequence[int], current_absolute_position: int,
    hpre_layer: int, seed: int,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    candidates: dict[str, Any] = {}
    states: dict[str, dict[str, Any]] = {}
    for name, suffix in (("original_candidate", original_suffix_ids), ("counterfactual_candidate", counterfactual_suffix_ids)):
        kv_capture = CaptureTokenKV(model=model, positions=capture_positions, selected_layers=selected_layers)
        boundary_capture = CaptureCurrentBlockBoundaries(
            model=model, position=current_absolute_position, layer_indices=[int(hpre_layer)]
        )
        with boundary_capture:
            with kv_capture:
                candidates[name] = score_evidence_suffix(
                    model=model, prepared=prepared, prefix_token_ids=prefix_token_ids,
                    bridge_token_ids=bridge_token_ids, suffix_token_ids=suffix, seed=seed,
                )
        boundaries = boundary_capture.complete_states()
        hpre = boundaries["h_pre"][int(hpre_layer)]
        states[name] = {
            "kv_layers": kv_capture.complete(),
            "kv_audit": copy.deepcopy(kv_capture.audit),
            "h_pre": hpre,
            "h_pre_summary": summarize_state(hpre),
            "boundary_audit": copy.deepcopy(boundary_capture.audit),
        }
    return {
        **_preference(candidates["original_candidate"], candidates["counterfactual_candidate"]),
        "original_candidate": candidates["original_candidate"],
        "counterfactual_candidate": candidates["counterfactual_candidate"],
    }, states


@torch.inference_mode()
def score_preference_with_token_source(
    *, model: Any, prepared: dict[str, Any], prefix_token_ids: Sequence[int],
    bridge_token_ids: Sequence[int], original_suffix_ids: Sequence[int],
    counterfactual_suffix_ids: Sequence[int], donor_states: Mapping[str, Mapping[str, Any]],
    captured_positions: Sequence[int], source_positions: Sequence[int],
    selected_layers: Sequence[int], current_absolute_position: int,
    visual_positions: Sequence[int], seed: int,
) -> dict[str, Any]:
    candidates: dict[str, Any] = {}
    audits: dict[str, Any] = {}
    for name, suffix in (("original_candidate", original_suffix_ids), ("counterfactual_candidate", counterfactual_suffix_ids)):
        source_layers = select_captured_positions(
            donor_states[name]["kv_layers"], captured_positions=captured_positions,
            selected_positions=source_positions,
        )
        patch = LayerTokenSourcePatch(
            model=model, source_layers=source_layers, source_positions=source_positions,
            selected_layers=selected_layers, first_patched_absolute_query=current_absolute_position,
            visual_positions=visual_positions,
        )
        with patch:
            candidates[name] = score_evidence_suffix(
                model=model, prepared=prepared, prefix_token_ids=prefix_token_ids,
                bridge_token_ids=bridge_token_ids, suffix_token_ids=suffix, seed=seed,
            )
        audits[name] = copy.deepcopy(patch.audit)
    return {
        **_preference(candidates["original_candidate"], candidates["counterfactual_candidate"]),
        "original_candidate": candidates["original_candidate"],
        "counterfactual_candidate": candidates["counterfactual_candidate"],
        "patch_audits": audits,
        "source_positions": sorted({int(value) for value in source_positions}),
        "selected_layers": sorted({int(value) for value in selected_layers}),
        "first_patched_absolute_query": int(current_absolute_position),
        "visual_kv_patched": False,
        "current_query_kv_patched": False,
    }


@torch.inference_mode()
def score_preference_with_hpre_source(
    *, model: Any, prepared: dict[str, Any], prefix_token_ids: Sequence[int],
    bridge_token_ids: Sequence[int], original_suffix_ids: Sequence[int],
    counterfactual_suffix_ids: Sequence[int], donor_states: Mapping[str, Mapping[str, Any]],
    current_absolute_position: int, hpre_layer: int, seed: int,
) -> dict[str, Any]:
    candidates: dict[str, Any] = {}
    audits: dict[str, Any] = {}
    for name, suffix in (("original_candidate", original_suffix_ids), ("counterfactual_candidate", counterfactual_suffix_ids)):
        patch = CurrentPositionBoundaryPatch(
            model=model, position=current_absolute_position, layer_index=int(hpre_layer),
            boundary="h_pre", source_state=donor_states[name]["h_pre"],
        )
        with patch:
            candidates[name] = score_evidence_suffix(
                model=model, prepared=prepared, prefix_token_ids=prefix_token_ids,
                bridge_token_ids=bridge_token_ids, suffix_token_ids=suffix, seed=seed,
            )
        audits[name] = copy.deepcopy(patch.audit)
    return {
        **_preference(candidates["original_candidate"], candidates["counterfactual_candidate"]),
        "original_candidate": candidates["original_candidate"],
        "counterfactual_candidate": candidates["counterfactual_candidate"],
        "patch_audits": audits,
        "current_absolute_position": int(current_absolute_position),
        "h_pre_layer": int(hpre_layer),
        "visual_kv_patched": False,
    }


__all__ = [
    "CaptureTokenKV", "LayerTokenSourcePatch", "capture_preference_carrier_states",
    "replace_token_kv_positions", "score_preference_with_hpre_source",
    "score_preference_with_token_source", "select_captured_positions",
]
