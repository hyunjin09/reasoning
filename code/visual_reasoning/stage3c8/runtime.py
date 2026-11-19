"""Native-GQA multi-position cache helpers for Stage 3C.8."""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from contextlib import AbstractContextManager, ExitStack
from typing import Any

import torch
from transformers.models.qwen3_vl.modeling_qwen3_vl import eager_attention_forward

from visual_reasoning.stage3b2.switching import _AttentionInterfaceContext
from visual_reasoning.stage3b0.cache import clone_cache
from visual_reasoning.stage3b4.runtime import absolute_intervention_position
from visual_reasoning.stage3c3.runtime import score_evidence_suffix
from visual_reasoning.stage3c4.runtime import SourceContributionWindowPatch
from visual_reasoning.stage3c5.carriers import CaptureTokenKV, select_captured_positions
from visual_reasoning.stage3c7.runtime import CANDIDATES


CACHE_MODES = frozenset({"K", "V", "KV"})


def _maximum(value: torch.Tensor) -> float:
    return float(value.abs().max().item()) if value.numel() else 0.0


def summarize_cache_state_difference(
    native: Mapping[int, tuple[torch.Tensor, torch.Tensor]],
    suppressed: Mapping[int, tuple[torch.Tensor, torch.Tensor]],
) -> dict[str, Any]:
    """Summarize native-vs-suppressed landmark cache divergence."""

    if set(native) != set(suppressed) or not native:
        raise ValueError("Native and suppressed cache states must cover the same nonempty layers")
    key_squared = 0.0
    value_squared = 0.0
    key_max = 0.0
    value_max = 0.0
    for layer in sorted(native):
        native_key, native_value = native[layer]
        suppressed_key, suppressed_value = suppressed[layer]
        if native_key.shape != suppressed_key.shape or native_value.shape != suppressed_value.shape:
            raise ValueError(f"Cache-state shape mismatch at layer {layer}")
        key_delta = (native_key.float() - suppressed_key.float())
        value_delta = (native_value.float() - suppressed_value.float())
        key_squared += float(torch.sum(key_delta.square()).item())
        value_squared += float(torch.sum(value_delta.square()).item())
        key_max = max(key_max, _maximum(key_delta))
        value_max = max(value_max, _maximum(value_delta))
    return {
        "layers": sorted(int(value) for value in native),
        "K_l2": key_squared ** 0.5,
        "V_l2": value_squared ** 0.5,
        "K_max_abs": key_max,
        "V_max_abs": value_max,
        "any_difference": bool(key_squared > 0.0 or value_squared > 0.0),
    }


def _cache_layer_tensors(cache: Any) -> list[tuple[torch.Tensor, torch.Tensor]]:
    layers = getattr(cache, "layers", None)
    if not isinstance(layers, list) or not layers:
        raise ValueError("Cache must expose a nonempty layers list")
    tensors: list[tuple[torch.Tensor, torch.Tensor]] = []
    for layer_index, layer in enumerate(layers):
        keys = getattr(layer, "keys", None)
        values = getattr(layer, "values", None)
        if not isinstance(keys, torch.Tensor) or not isinstance(values, torch.Tensor):
            raise ValueError(f"Cache layer {layer_index} does not expose tensor keys/values")
        if keys.ndim != 4 or keys.shape != values.shape:
            raise ValueError(f"Cache layer {layer_index} has invalid K/V shape")
        tensors.append((keys, values))
    return tensors


def patch_prefill_cache_positions(
    recipient: Any,
    source: Any,
    *,
    positions: Sequence[int],
    mode: str,
    forbidden_positions: Sequence[int] = (),
) -> tuple[Any, dict[str, Any]]:
    """Clone a prefill cache and replace selected all-layer K, V, or K+V states."""

    recipient_tensors = _cache_layer_tensors(recipient)
    source_tensors = _cache_layer_tensors(source)
    if len(recipient_tensors) != len(source_tensors):
        raise ValueError("Source and recipient cache layer counts differ")
    if any(left[0].shape != right[0].shape for left, right in zip(recipient_tensors, source_tensors)):
        raise ValueError("Source and recipient cache tensor shapes differ")
    selected = sorted({int(position) for position in positions})
    sequence_length = int(recipient_tensors[0][0].shape[2])
    if not selected or selected[0] < 0 or selected[-1] >= sequence_length:
        raise ValueError("Patch positions must be nonempty and inside the cache sequence")
    forbidden = {int(position) for position in forbidden_positions}
    if forbidden.intersection(selected):
        raise ValueError("Patch positions include a forbidden cache position")
    normalized_mode = str(mode).upper()
    if normalized_mode not in CACHE_MODES:
        raise ValueError(f"Unsupported cache mode: {mode}")

    patched = clone_cache(recipient)
    patched_tensors = _cache_layer_tensors(patched)
    layers_patched: list[int] = []
    nonselected_key_delta = 0.0
    nonselected_value_delta = 0.0
    index = torch.tensor(selected, dtype=torch.long, device=patched_tensors[0][0].device)
    keep = torch.ones(sequence_length, dtype=torch.bool, device=index.device)
    keep[index] = False
    for layer_index, ((target_key, target_value), (recipient_key, recipient_value), (source_key, source_value)) in enumerate(
        zip(patched_tensors, recipient_tensors, source_tensors)
    ):
        if normalized_mode in {"K", "KV"}:
            target_key[:, :, index, :] = source_key[:, :, index, :].to(target_key.device, target_key.dtype)
        if normalized_mode in {"V", "KV"}:
            target_value[:, :, index, :] = source_value[:, :, index, :].to(target_value.device, target_value.dtype)
        nonselected_key_delta = max(
            nonselected_key_delta,
            _maximum(target_key[:, :, keep, :] - recipient_key[:, :, keep, :]),
        )
        nonselected_value_delta = max(
            nonselected_value_delta,
            _maximum(target_value[:, :, keep, :] - recipient_value[:, :, keep, :]),
        )
        layers_patched.append(layer_index)

    return patched, {
        "mode": normalized_mode,
        "positions": selected,
        "position_count": len(selected),
        "layers_patched": layers_patched,
        "kv_tensors_patched_per_layer": 2 if normalized_mode == "KV" else 1,
        "sequence_axis": 2,
        "nonselected_key_max_abs_delta": nonselected_key_delta,
        "nonselected_value_max_abs_delta": nonselected_value_delta,
        "unselected_component_unchanged": True,
        "forbidden_positions_replaced": sorted(forbidden.intersection(selected)),
    }


def replace_cache_positions(
    key: torch.Tensor,
    value: torch.Tensor,
    *,
    source_key: torch.Tensor,
    source_value: torch.Tensor,
    positions: Sequence[int],
    mode: str,
    visual_positions: Sequence[int] = (),
    current_query_position: int | None = None,
) -> tuple[torch.Tensor, torch.Tensor, dict[str, Any]]:
    """Replace K, V, or K+V at frozen cache positions in native KV-head space."""

    if key.ndim != 4 or value.shape != key.shape:
        raise ValueError("Recipient K/V must match [batch,native KV-head,sequence,head_dim]")
    selected = sorted({int(position) for position in positions})
    if not selected:
        raise ValueError("At least one cache position is required")
    if selected[0] < 0 or selected[-1] >= int(key.shape[2]):
        raise ValueError("Selected cache position is outside the sequence")
    visual = {int(position) for position in visual_positions}
    if visual.intersection(selected):
        raise ValueError("Selected cache positions may not include visual positions")
    if current_query_position is not None and any(position >= int(current_query_position) for position in selected):
        raise ValueError("Selected cache positions must precede the current query")
    normalized_mode = str(mode).upper()
    if normalized_mode not in CACHE_MODES:
        raise ValueError(f"Unsupported cache mode: {mode}")
    expected = (int(key.shape[0]), int(key.shape[1]), len(selected), int(key.shape[3]))
    if tuple(source_key.shape) != expected or tuple(source_value.shape) != expected:
        raise ValueError(f"Donor tensors must use the native KV-head layout {expected}")

    patched_key, patched_value = key.clone(), value.clone()
    index = torch.tensor(selected, dtype=torch.long, device=key.device)
    recipient_key = key.index_select(2, index)
    recipient_value = value.index_select(2, index)
    if normalized_mode in {"K", "KV"}:
        patched_key[:, :, selected, :] = source_key.to(key.device, key.dtype)
    if normalized_mode in {"V", "KV"}:
        patched_value[:, :, selected, :] = source_value.to(value.device, value.dtype)
    keep = torch.ones(int(key.shape[2]), dtype=torch.bool, device=key.device)
    keep[index] = False
    return patched_key, patched_value, {
        "mode": normalized_mode,
        "positions_replaced": selected,
        "position_count": len(selected),
        "native_kv_head_count": int(key.shape[1]),
        "head_dimension": int(key.shape[3]),
        "recipient_key_exact_source_before_patch": bool(torch.equal(recipient_key, source_key.to(key.device, key.dtype))),
        "recipient_value_exact_source_before_patch": bool(torch.equal(recipient_value, source_value.to(value.device, value.dtype))),
        "selected_key_exact_expected": bool(torch.equal(
            patched_key.index_select(2, index),
            source_key.to(key.device, key.dtype) if normalized_mode in {"K", "KV"} else recipient_key,
        )),
        "selected_value_exact_expected": bool(torch.equal(
            patched_value.index_select(2, index),
            source_value.to(value.device, value.dtype) if normalized_mode in {"V", "KV"} else recipient_value,
        )),
        "nonselected_key_max_abs_delta": _maximum(patched_key[:, :, keep, :] - key[:, :, keep, :]),
        "nonselected_value_max_abs_delta": _maximum(patched_value[:, :, keep, :] - value[:, :, keep, :]),
        "unselected_component_key_max_abs_delta": _maximum(patched_key - key) if normalized_mode == "V" else 0.0,
        "unselected_component_value_max_abs_delta": _maximum(patched_value - value) if normalized_mode == "K" else 0.0,
        "visual_positions_replaced": sorted(visual.intersection(selected)),
        "current_query_position_replaced": bool(current_query_position in selected if current_query_position is not None else False),
        "post_rope_key": True,
        "projected_value": True,
    }


class MultiPositionCachePatch(AbstractContextManager["MultiPositionCachePatch"]):
    """Expose native K/V at frozen prior positions only to current/future rows."""

    def __init__(
        self,
        *,
        model: Any,
        donor_layers: Mapping[int, tuple[torch.Tensor, torch.Tensor]],
        selected_layers: Sequence[int],
        positions: Sequence[int],
        current_query_position: int,
        visual_positions: Sequence[int],
        mode: str,
    ) -> None:
        self.model = model
        self.donor_layers = dict(donor_layers)
        self.selected_layers = frozenset(int(layer) for layer in selected_layers)
        self.positions = tuple(sorted({int(position) for position in positions}))
        self.current_query_position = int(current_query_position)
        self.visual_positions = tuple(sorted({int(position) for position in visual_positions}))
        self.mode = str(mode).upper()
        if set(self.donor_layers) != set(self.selected_layers):
            raise ValueError("Donor layer set must equal selected layer set")
        if not self.positions or self.positions[-1] >= self.current_query_position:
            raise ValueError("Every donor cache position must precede the current query")
        if set(self.positions).intersection(self.visual_positions):
            raise ValueError("Carrier positions may not include visual tokens")
        if self.mode not in CACHE_MODES:
            raise ValueError(f"Unsupported cache mode: {mode}")
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
        baseline_output, baseline_weights = eager_attention_forward(
            module, query, key, value, attention_mask, scaling=scaling, dropout=dropout, **kwargs
        )
        query_length = int(query.shape[2])
        query_start = int(key.shape[2]) - query_length
        active_rows = [row for row in range(query_length) if query_start + row >= self.current_query_position]
        if layer not in self.selected_layers:
            self.audit.append({
                "layer_index": layer,
                "layer_selected": False,
                "mode": self.mode,
                "positions_replaced": [],
                "switched_absolute_query_indices": [],
            })
            return baseline_output, baseline_weights
        source_key, source_value = self.donor_layers[layer]
        hybrid_key, hybrid_value, replacement = replace_cache_positions(
            key,
            value,
            source_key=source_key,
            source_value=source_value,
            positions=self.positions,
            mode=self.mode,
            visual_positions=self.visual_positions,
            current_query_position=self.current_query_position,
        )
        donor_differs = not (
            replacement["recipient_key_exact_source_before_patch"] if self.mode == "K" else
            replacement["recipient_value_exact_source_before_patch"] if self.mode == "V" else
            replacement["recipient_key_exact_source_before_patch"] and replacement["recipient_value_exact_source_before_patch"]
        )
        if active_rows and donor_differs:
            switched_output, switched_weights = eager_attention_forward(
                module, query, hybrid_key, hybrid_value, attention_mask,
                scaling=scaling, dropout=dropout, **kwargs,
            )
            output, weights = baseline_output.clone(), baseline_weights.clone()
            output[:, active_rows, :, :] = switched_output[:, active_rows, :, :]
            weights[:, :, active_rows, :] = switched_weights[:, :, active_rows, :]
        else:
            output, weights = baseline_output, baseline_weights
        self.audit.append({
            "layer_index": layer,
            "layer_selected": True,
            **replacement,
            "first_patched_absolute_query": self.current_query_position,
            "switched_absolute_query_indices": [query_start + row for row in active_rows],
            "queries_before_current_modified": 0,
            "query_rows_recomputed": len(active_rows),
            "query_vectors_replaced": 0,
        })
        return output, weights

    def __enter__(self) -> "MultiPositionCachePatch":
        self._interface = _AttentionInterfaceContext(
            model=self.model,
            name="stage3c8_multi_position_cache_patch",
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

    def complete(self) -> list[dict[str, Any]]:
        selected = [row for row in self.audit if row.get("layer_selected")]
        if {int(row["layer_index"]) for row in selected} != set(self.selected_layers):
            raise RuntimeError("Multi-position cache patch missed a selected layer")
        return copy.deepcopy(self.audit)


def _preference(candidates: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    original, counterfactual = candidates[CANDIDATES[0]], candidates[CANDIDATES[1]]
    return {
        "L_o": float(original["mean_log_probability"]),
        "L_c": float(counterfactual["mean_log_probability"]),
        "D": float(original["mean_log_probability"]) - float(counterfactual["mean_log_probability"]),
        "finite": bool(original["finite"] and counterfactual["finite"]),
        CANDIDATES[0]: original,
        CANDIDATES[1]: counterfactual,
    }


def _window_patches(
    *,
    model: Any,
    query_positions: Sequence[int],
    layers: Sequence[int],
    source_positions: Sequence[int],
    selected_heads: Sequence[int],
) -> list[SourceContributionWindowPatch]:
    return [
        SourceContributionWindowPatch(
            model=model,
            layer_index=int(layer),
            query_positions=query_positions,
            selected_heads=selected_heads,
            source_positions=source_positions,
            gain=0.0,
        )
        for layer in sorted({int(layer) for layer in layers})
    ]


@torch.inference_mode()
def capture_native_or_window_suppressed_states(
    *,
    model: Any,
    prepared: dict[str, Any],
    prefix_token_ids: Sequence[int],
    bridge_token_ids: Sequence[int],
    original_suffix_ids: Sequence[int],
    counterfactual_suffix_ids: Sequence[int],
    window_generated_indices: Sequence[int],
    capture_generated_indices: Sequence[int],
    cache_layers: Sequence[int],
    source_positions: Sequence[int],
    selected_heads: Sequence[int],
    seed: int,
    suppression_enabled: bool,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Score and capture native-GQA cache states around a frozen T16 window."""

    prompt_length = int(prepared["input_ids"].shape[1])
    window = sorted({
        absolute_intervention_position(prompt_length=prompt_length, intervention_generated_index=int(index))
        for index in window_generated_indices
    })
    capture = sorted({
        absolute_intervention_position(prompt_length=prompt_length, intervention_generated_index=int(index))
        for index in capture_generated_indices
    })
    if not window or not capture or capture[-1] >= window[-1]:
        raise ValueError("Capture positions must be nonempty and precede the final T16 query")
    candidates: dict[str, Any] = {}
    states: dict[str, dict[str, Any]] = {}
    for candidate, suffix in zip(CANDIDATES, (original_suffix_ids, counterfactual_suffix_ids)):
        capture_cache = CaptureTokenKV(model=model, positions=capture, selected_layers=cache_layers)
        suppressions = _window_patches(
            model=model,
            query_positions=window,
            layers=cache_layers,
            source_positions=source_positions,
            selected_heads=selected_heads,
        ) if suppression_enabled else []
        with ExitStack() as stack:
            stack.enter_context(capture_cache)
            for suppression in suppressions:
                stack.enter_context(suppression)
            candidates[candidate] = score_evidence_suffix(
                model=model,
                prepared=prepared,
                prefix_token_ids=prefix_token_ids,
                bridge_token_ids=bridge_token_ids,
                suffix_token_ids=suffix,
                seed=seed,
            )
        states[candidate] = {
            "cache": capture_cache.complete(),
            "cache_positions": capture,
            "cache_audit": copy.deepcopy(capture_cache.audit),
            "suppression_audit": [suppression.complete() for suppression in suppressions],
        }
    result = _preference(candidates)
    result.update({
        "window_generated_indices": sorted({int(index) for index in window_generated_indices}),
        "absolute_query_positions": window,
        "capture_generated_indices": sorted({int(index) for index in capture_generated_indices}),
        "capture_absolute_positions": capture,
        "suppression_enabled": bool(suppression_enabled),
    })
    return result, states


@torch.inference_mode()
def score_window_suppressed_with_cache_rescue(
    *,
    model: Any,
    prepared: dict[str, Any],
    prefix_token_ids: Sequence[int],
    bridge_token_ids: Sequence[int],
    original_suffix_ids: Sequence[int],
    counterfactual_suffix_ids: Sequence[int],
    window_generated_indices: Sequence[int],
    selected_generated_indices: Sequence[int],
    suppression_layers: Sequence[int],
    source_positions: Sequence[int],
    selected_heads: Sequence[int],
    donor_states: Mapping[str, Mapping[str, Any]],
    cache_mode: str,
    visual_positions: Sequence[int],
    seed: int,
    suppression_enabled: bool = True,
) -> dict[str, Any]:
    """Recreate T16 suppression and expose donor cache positions from t* onward."""

    prompt_length = int(prepared["input_ids"].shape[1])
    window = sorted({
        absolute_intervention_position(prompt_length=prompt_length, intervention_generated_index=int(index))
        for index in window_generated_indices
    })
    selected = sorted({
        absolute_intervention_position(prompt_length=prompt_length, intervention_generated_index=int(index))
        for index in selected_generated_indices
    })
    if not window or not selected or selected[-1] >= window[-1]:
        raise ValueError("Rescued cache positions must precede the final T16 query")
    candidates: dict[str, Any] = {}
    cache_audits: dict[str, Any] = {}
    suppression_audits: dict[str, Any] = {}
    for candidate, suffix in zip(CANDIDATES, (original_suffix_ids, counterfactual_suffix_ids)):
        donor = select_captured_positions(
            donor_states[candidate]["cache"],
            captured_positions=donor_states[candidate]["cache_positions"],
            selected_positions=selected,
        )
        patch = MultiPositionCachePatch(
            model=model,
            donor_layers=donor,
            selected_layers=suppression_layers,
            positions=selected,
            current_query_position=window[-1],
            visual_positions=visual_positions,
            mode=cache_mode,
        )
        suppressions = _window_patches(
            model=model,
            query_positions=window,
            layers=suppression_layers,
            source_positions=source_positions,
            selected_heads=selected_heads,
        ) if suppression_enabled else []
        with ExitStack() as stack:
            stack.enter_context(patch)
            for suppression in suppressions:
                stack.enter_context(suppression)
            candidates[candidate] = score_evidence_suffix(
                model=model,
                prepared=prepared,
                prefix_token_ids=prefix_token_ids,
                bridge_token_ids=bridge_token_ids,
                suffix_token_ids=suffix,
                seed=seed,
            )
        cache_audits[candidate] = patch.complete()
        suppression_audits[candidate] = [suppression.complete() for suppression in suppressions]
    result = _preference(candidates)
    result.update({
        "window_generated_indices": sorted({int(index) for index in window_generated_indices}),
        "selected_generated_indices": sorted({int(index) for index in selected_generated_indices}),
        "absolute_query_positions": window,
        "selected_absolute_positions": selected,
        "cache_mode": str(cache_mode).upper(),
        "cache_patch_audits": cache_audits,
        "suppression_audits": suppression_audits,
        "visual_kv_donor_patched": False,
        "current_query_kv_donor_patched": False,
        "suppression_enabled": bool(suppression_enabled),
    })
    return result


@torch.inference_mode()
def capture_landmark_cache_states(
    *,
    model: Any,
    prepared: dict[str, Any],
    history_before_readout_ids: Sequence[int],
    original_suffix_ids: Sequence[int],
    counterfactual_suffix_ids: Sequence[int],
    landmark_generated_index: int,
    local_suppression_generated_indices: Sequence[int],
    cache_layers: Sequence[int],
    source_positions: Sequence[int],
    selected_heads: Sequence[int],
    seed: int,
    suppression_enabled: bool,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Score a readout and capture one landmark cache under a preceding source deficit."""

    prompt_length = int(prepared["input_ids"].shape[1])
    readout_generated_index = len(history_before_readout_ids)
    landmark_absolute = absolute_intervention_position(
        prompt_length=prompt_length,
        intervention_generated_index=int(landmark_generated_index),
    )
    readout_absolute = absolute_intervention_position(
        prompt_length=prompt_length,
        intervention_generated_index=readout_generated_index,
    )
    suppression_positions = sorted({
        absolute_intervention_position(
            prompt_length=prompt_length,
            intervention_generated_index=int(index),
        )
        for index in local_suppression_generated_indices
    })
    if not suppression_positions or suppression_positions[-1] >= landmark_absolute:
        raise ValueError("Local source-deficit queries must precede the landmark")
    if landmark_absolute >= readout_absolute:
        raise ValueError("Landmark must precede the downstream readout")
    candidates: dict[str, Any] = {}
    states: dict[str, dict[str, Any]] = {}
    for candidate, suffix in zip(CANDIDATES, (original_suffix_ids, counterfactual_suffix_ids)):
        capture = CaptureTokenKV(
            model=model,
            positions=[landmark_absolute],
            selected_layers=cache_layers,
        )
        suppressions = _window_patches(
            model=model,
            query_positions=suppression_positions,
            layers=cache_layers,
            source_positions=source_positions,
            selected_heads=selected_heads,
        ) if suppression_enabled else []
        with ExitStack() as stack:
            stack.enter_context(capture)
            for suppression in suppressions:
                stack.enter_context(suppression)
            candidates[candidate] = score_evidence_suffix(
                model=model,
                prepared=prepared,
                prefix_token_ids=history_before_readout_ids,
                bridge_token_ids=[],
                suffix_token_ids=suffix,
                seed=seed,
            )
        states[candidate] = {
            "cache": capture.complete(),
            "cache_positions": [landmark_absolute],
            "cache_audit": copy.deepcopy(capture.audit),
            "suppression_audit": [suppression.complete() for suppression in suppressions],
        }
    result = _preference(candidates)
    result.update({
        "landmark_generated_index": int(landmark_generated_index),
        "landmark_absolute_position": landmark_absolute,
        "readout_generated_index": readout_generated_index,
        "readout_absolute_position": readout_absolute,
        "local_suppression_generated_indices": sorted({int(value) for value in local_suppression_generated_indices}),
        "local_suppression_absolute_positions": suppression_positions,
        "suppression_enabled": bool(suppression_enabled),
    })
    return result, states


@torch.inference_mode()
def score_landmark_cache_patch(
    *,
    model: Any,
    prepared: dict[str, Any],
    history_before_readout_ids: Sequence[int],
    original_suffix_ids: Sequence[int],
    counterfactual_suffix_ids: Sequence[int],
    landmark_generated_index: int,
    local_suppression_generated_indices: Sequence[int],
    suppression_layers: Sequence[int],
    source_positions: Sequence[int],
    selected_heads: Sequence[int],
    donor_states: Mapping[str, Mapping[str, Any]],
    visual_positions: Sequence[int],
    seed: int,
    suppression_enabled: bool,
) -> dict[str, Any]:
    """Patch one landmark K+V into a native or locally source-suppressed readout."""

    prompt_length = int(prepared["input_ids"].shape[1])
    readout_generated_index = len(history_before_readout_ids)
    landmark_absolute = absolute_intervention_position(
        prompt_length=prompt_length,
        intervention_generated_index=int(landmark_generated_index),
    )
    readout_absolute = absolute_intervention_position(
        prompt_length=prompt_length,
        intervention_generated_index=readout_generated_index,
    )
    suppression_positions = sorted({
        absolute_intervention_position(
            prompt_length=prompt_length,
            intervention_generated_index=int(index),
        )
        for index in local_suppression_generated_indices
    })
    if not suppression_positions or suppression_positions[-1] >= landmark_absolute:
        raise ValueError("Local source-deficit queries must precede the landmark")
    candidates: dict[str, Any] = {}
    patch_audits: dict[str, Any] = {}
    suppression_audits: dict[str, Any] = {}
    for candidate, suffix in zip(CANDIDATES, (original_suffix_ids, counterfactual_suffix_ids)):
        donor = select_captured_positions(
            donor_states[candidate]["cache"],
            captured_positions=donor_states[candidate]["cache_positions"],
            selected_positions=[landmark_absolute],
        )
        patch = MultiPositionCachePatch(
            model=model,
            donor_layers=donor,
            selected_layers=suppression_layers,
            positions=[landmark_absolute],
            current_query_position=readout_absolute,
            visual_positions=visual_positions,
            mode="KV",
        )
        suppressions = _window_patches(
            model=model,
            query_positions=suppression_positions,
            layers=suppression_layers,
            source_positions=source_positions,
            selected_heads=selected_heads,
        ) if suppression_enabled else []
        with ExitStack() as stack:
            stack.enter_context(patch)
            for suppression in suppressions:
                stack.enter_context(suppression)
            candidates[candidate] = score_evidence_suffix(
                model=model,
                prepared=prepared,
                prefix_token_ids=history_before_readout_ids,
                bridge_token_ids=[],
                suffix_token_ids=suffix,
                seed=seed,
            )
        patch_audits[candidate] = patch.complete()
        suppression_audits[candidate] = [suppression.complete() for suppression in suppressions]
    result = _preference(candidates)
    result.update({
        "landmark_generated_index": int(landmark_generated_index),
        "landmark_absolute_position": landmark_absolute,
        "readout_generated_index": readout_generated_index,
        "readout_absolute_position": readout_absolute,
        "local_suppression_generated_indices": sorted({int(value) for value in local_suppression_generated_indices}),
        "cache_mode": "KV",
        "cache_patch_audits": patch_audits,
        "suppression_audits": suppression_audits,
        "suppression_enabled": bool(suppression_enabled),
        "visual_kv_donor_patched": False,
        "current_query_kv_donor_patched": False,
    })
    return result


__all__ = [
    "MultiPositionCachePatch",
    "capture_native_or_window_suppressed_states",
    "capture_landmark_cache_states",
    "patch_prefill_cache_positions",
    "replace_cache_positions",
    "score_landmark_cache_patch",
    "score_window_suppressed_with_cache_rescue",
    "summarize_cache_state_difference",
]
