"""Event-span source-suppression and cache-rescue runtime for Stage 3C.9."""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from contextlib import ExitStack
from typing import Any

import torch

from visual_reasoning.stage3c3.runtime import score_evidence_suffix
from visual_reasoning.stage3c4.runtime import SourceContributionWindowPatch
from visual_reasoning.stage3c5.carriers import CaptureTokenKV, select_captured_positions
from visual_reasoning.stage3c7.runtime import CANDIDATES
from visual_reasoning.stage3c8.runtime import MultiPositionCachePatch, summarize_cache_state_difference


def absolute_reasoning_token_position(*, prompt_length: int, token_index: int) -> int:
    """Map a zero-based generated-token index to an absolute sequence position."""

    if int(prompt_length) <= 0 or int(token_index) < 0:
        raise ValueError("Reasoning-token mapping requires a prompt and nonnegative token index")
    return int(prompt_length) + int(token_index)


def validate_checkpoint_coordinates(
    *, span_generated_indices: Sequence[int], source_window_generated_indices: Sequence[int],
    readout_generated_index: int,
) -> dict[str, Any]:
    span = sorted({int(value) for value in span_generated_indices})
    window = sorted({int(value) for value in source_window_generated_indices})
    if not span or span != list(range(span[0], span[-1] + 1)):
        raise ValueError("Checkpoint span must be nonempty and contiguous")
    if len(window) not in {8, 16} or window != list(range(window[0], window[-1] + 1)):
        raise ValueError("Source window must be a contiguous prospective W8 or W16")
    if window != list(range(span[0] - len(window), span[0])):
        raise ValueError("Source window must end immediately before checkpoint span")
    if window[0] < 0:
        raise ValueError("Source window begins before generated reasoning")
    if span[-1] >= int(readout_generated_index):
        raise ValueError("Checkpoint span must precede the downstream readout")
    return {
        "span_generated_indices": span,
        "source_window_generated_indices": window,
        "span_width": len(span),
        "source_window_width": len(window),
        "readout_generated_index": int(readout_generated_index),
        "first_downstream_query": span[-1] + 1,
    }


def validate_rescue_positions(
    positions: Sequence[int], *, readout_generated_index: int,
) -> dict[str, Any]:
    selected = sorted({int(value) for value in positions})
    if not selected or selected != list(range(selected[0], selected[-1] + 1)):
        raise ValueError("Rescue positions must be nonempty and contiguous")
    if selected[0] < 0 or selected[-1] >= int(readout_generated_index):
        raise ValueError("Rescue positions must lie in reasoning history before the readout")
    return {
        "patch_generated_indices": selected,
        "patch_width": len(selected),
        "first_downstream_query": selected[-1] + 1,
    }


def validate_route_coordinates(
    *, event_a_span: Sequence[int], event_b_span: Sequence[int],
    readout_generated_index: int,
) -> dict[str, Any]:
    """Validate the frozen A→B route pair and fixed A-through-next-8 history."""

    left = sorted({int(value) for value in event_a_span})
    right = sorted({int(value) for value in event_b_span})
    if not left or left != list(range(left[0], left[-1] + 1)):
        raise ValueError("Route event A must be a contiguous nonempty span")
    if not right or right != list(range(right[0], right[-1] + 1)):
        raise ValueError("Route event B must be a contiguous nonempty span")
    separation = right[0] - left[0]
    if separation < 24 or left[-1] >= right[0]:
        raise ValueError("Route events must be nonoverlapping and separated by at least 24 tokens")
    if right[0] < 8 or right[-1] >= int(readout_generated_index):
        raise ValueError("Route event B must support W8 and precede its local-use readout")
    short_history = list(range(left[0], left[-1] + 9))
    if short_history[-1] >= right[0]:
        raise ValueError("Frozen A-through-next-8 history overlaps checkpoint B")
    return {
        "event_a_span": left,
        "event_b_span": right,
        "prior_checkpoint_positions": left,
        "short_history_positions": short_history,
        "direct_w8_query_positions": list(range(right[0] - 8, right[0])),
        "separation": separation,
        "readout_generated_index": int(readout_generated_index),
    }


class _RouteCachePatchWithCapture(MultiPositionCachePatch):
    """Apply a frozen route patch while capturing a later checkpoint's K/V."""

    def __init__(self, *, target_capture_positions: Sequence[int], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.target_capture_positions = tuple(sorted({int(value) for value in target_capture_positions}))
        self.target_layers: dict[int, tuple[torch.Tensor, torch.Tensor]] = {}

    def _forward(
        self, module: Any, query: torch.Tensor, key: torch.Tensor, value: torch.Tensor,
        attention_mask: torch.Tensor | None, scaling: float, dropout: float = 0.0,
        **kwargs: Any,
    ):
        layer = int(module.layer_idx)
        if layer in self.selected_layers:
            if layer in self.target_layers:
                raise RuntimeError(f"Route target K/V captured more than once at layer {layer}")
            if not self.target_capture_positions or self.target_capture_positions[-1] >= int(key.shape[2]):
                raise RuntimeError("Route target capture position is outside the cache")
            self.target_layers[layer] = (
                key[:, :, self.target_capture_positions, :].detach().clone(),
                value[:, :, self.target_capture_positions, :].detach().clone(),
            )
        return super()._forward(
            module, query, key, value, attention_mask,
            scaling=scaling, dropout=dropout, **kwargs,
        )

    def complete_target_capture(self) -> dict[int, tuple[torch.Tensor, torch.Tensor]]:
        if set(self.target_layers) != set(self.selected_layers):
            raise RuntimeError("Route target K/V capture missed a selected layer")
        return dict(self.target_layers)


def _preference(candidates: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    original = candidates[CANDIDATES[0]]
    counterfactual = candidates[CANDIDATES[1]]
    return {
        "L_o": float(original["mean_log_probability"]),
        "L_c": float(counterfactual["mean_log_probability"]),
        "D": float(original["mean_log_probability"]) - float(counterfactual["mean_log_probability"]),
        "finite": bool(original["finite"] and counterfactual["finite"]),
        CANDIDATES[0]: original,
        CANDIDATES[1]: counterfactual,
    }


def _suppressions(
    *, model: Any, layers: Sequence[int], absolute_queries: Sequence[int],
    source_positions: Sequence[int], selected_heads: Sequence[int],
) -> list[SourceContributionWindowPatch]:
    return [
        SourceContributionWindowPatch(
            model=model,
            layer_index=int(layer),
            query_positions=absolute_queries,
            selected_heads=selected_heads,
            source_positions=source_positions,
            gain=0.0,
        )
        for layer in sorted({int(value) for value in layers})
    ]


@torch.inference_mode()
def capture_checkpoint_span_states(
    *, model: Any, prepared: dict[str, Any], history_before_readout_ids: Sequence[int],
    original_suffix_ids: Sequence[int], counterfactual_suffix_ids: Sequence[int],
    span_generated_indices: Sequence[int], source_window_generated_indices: Sequence[int],
    cache_layers: Sequence[int], source_positions: Sequence[int], selected_heads: Sequence[int],
    seed: int, suppression_enabled: bool,
    additional_capture_generated_indices: Sequence[int] = (),
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Score one readout and capture a frozen event span under native/suppressed vision."""

    coordinates = validate_checkpoint_coordinates(
        span_generated_indices=span_generated_indices,
        source_window_generated_indices=source_window_generated_indices,
        readout_generated_index=len(history_before_readout_ids),
    )
    prompt_length = int(prepared["input_ids"].shape[1])
    absolute_span = [
        absolute_reasoning_token_position(prompt_length=prompt_length, token_index=index)
        for index in coordinates["span_generated_indices"]
    ]
    capture_generated = sorted({
        *coordinates["span_generated_indices"],
        *(int(value) for value in additional_capture_generated_indices),
    })
    if not capture_generated or capture_generated[0] < 0 or capture_generated[-1] >= len(history_before_readout_ids):
        raise ValueError("All capture positions must precede the readout")
    absolute_capture = [
        absolute_reasoning_token_position(prompt_length=prompt_length, token_index=index)
        for index in capture_generated
    ]
    absolute_window = [
        absolute_reasoning_token_position(prompt_length=prompt_length, token_index=index)
        for index in coordinates["source_window_generated_indices"]
    ]
    candidates: dict[str, Any] = {}
    states: dict[str, dict[str, Any]] = {}
    for candidate, suffix in zip(CANDIDATES, (original_suffix_ids, counterfactual_suffix_ids)):
        capture = CaptureTokenKV(model=model, positions=absolute_capture, selected_layers=cache_layers)
        suppressions = _suppressions(
            model=model, layers=cache_layers, absolute_queries=absolute_window,
            source_positions=source_positions, selected_heads=selected_heads,
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
            "cache_positions": absolute_capture,
            "cache_audit": copy.deepcopy(capture.audit),
            "suppression_audit": [suppression.complete() for suppression in suppressions],
        }
    result = _preference(candidates)
    result.update({
        **coordinates,
        "span_absolute_positions": absolute_span,
        "capture_generated_indices": capture_generated,
        "capture_absolute_positions": absolute_capture,
        "source_window_absolute_positions": absolute_window,
        "suppression_enabled": bool(suppression_enabled),
    })
    return result, states


@torch.inference_mode()
def score_checkpoint_span_rescue(
    *, model: Any, prepared: dict[str, Any], history_before_readout_ids: Sequence[int],
    original_suffix_ids: Sequence[int], counterfactual_suffix_ids: Sequence[int],
    span_generated_indices: Sequence[int], source_window_generated_indices: Sequence[int],
    suppression_layers: Sequence[int], source_positions: Sequence[int], selected_heads: Sequence[int],
    donor_states: Mapping[str, Mapping[str, Any]], visual_positions: Sequence[int], seed: int,
    suppression_enabled: bool = True,
    patch_generated_indices: Sequence[int] | None = None,
) -> dict[str, Any]:
    """Patch a native-GQA event-span K+V cache into a matching recipient run."""

    coordinates = validate_checkpoint_coordinates(
        span_generated_indices=span_generated_indices,
        source_window_generated_indices=source_window_generated_indices,
        readout_generated_index=len(history_before_readout_ids),
    )
    patch_coordinates = validate_rescue_positions(
        coordinates["span_generated_indices"] if patch_generated_indices is None else patch_generated_indices,
        readout_generated_index=len(history_before_readout_ids),
    )
    prompt_length = int(prepared["input_ids"].shape[1])
    absolute_span = [
        absolute_reasoning_token_position(prompt_length=prompt_length, token_index=index)
        for index in coordinates["span_generated_indices"]
    ]
    absolute_window = [
        absolute_reasoning_token_position(prompt_length=prompt_length, token_index=index)
        for index in coordinates["source_window_generated_indices"]
    ]
    absolute_patch = [
        absolute_reasoning_token_position(prompt_length=prompt_length, token_index=index)
        for index in patch_coordinates["patch_generated_indices"]
    ]
    first_downstream_absolute = absolute_reasoning_token_position(
        prompt_length=prompt_length,
        token_index=int(patch_coordinates["first_downstream_query"]),
    )
    candidates: dict[str, Any] = {}
    patch_audits: dict[str, Any] = {}
    suppression_audits: dict[str, Any] = {}
    for candidate, suffix in zip(CANDIDATES, (original_suffix_ids, counterfactual_suffix_ids)):
        donor = select_captured_positions(
            donor_states[candidate]["cache"],
            captured_positions=donor_states[candidate]["cache_positions"],
            selected_positions=absolute_patch,
        )
        patch = MultiPositionCachePatch(
            model=model,
            donor_layers=donor,
            selected_layers=suppression_layers,
            positions=absolute_patch,
            current_query_position=first_downstream_absolute,
            visual_positions=visual_positions,
            mode="KV",
        )
        suppressions = _suppressions(
            model=model, layers=suppression_layers, absolute_queries=absolute_window,
            source_positions=source_positions, selected_heads=selected_heads,
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
        **coordinates,
        "span_absolute_positions": absolute_span,
        **patch_coordinates,
        "patch_absolute_positions": absolute_patch,
        "source_window_absolute_positions": absolute_window,
        "first_downstream_absolute_query": first_downstream_absolute,
        "cache_mode": "KV",
        "cache_patch_audits": patch_audits,
        "suppression_audits": suppression_audits,
        "suppression_enabled": bool(suppression_enabled),
        "visual_kv_donor_patched": False,
        "non_event_cache_donor_patched": False,
    })
    return result


@torch.inference_mode()
def score_route_arm(
    *, model: Any, prepared: dict[str, Any], history_before_readout_ids: Sequence[int],
    original_suffix_ids: Sequence[int], counterfactual_suffix_ids: Sequence[int],
    direct_source_window_generated_indices: Sequence[int], layers: Sequence[int],
    source_positions: Sequence[int], selected_heads: Sequence[int], visual_positions: Sequence[int],
    target_capture_generated_indices: Sequence[int], seed: int,
    direct_suppression: bool, donor_states: Mapping[str, Mapping[str, Any]] | None = None,
    patch_generated_indices: Sequence[int] = (),
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Score one native/direct/prior/joint route arm and capture checkpoint B."""

    prompt_length = int(prepared["input_ids"].shape[1])
    direct_generated = sorted({int(value) for value in direct_source_window_generated_indices})
    if len(direct_generated) != 8 or direct_generated != list(range(direct_generated[0], direct_generated[-1] + 1)):
        raise ValueError("Route direct-source intervention must use the frozen contiguous W8")
    target_generated = sorted({int(value) for value in target_capture_generated_indices})
    if not target_generated:
        raise ValueError("Route target checkpoint capture must be nonempty")
    target_absolute = [
        absolute_reasoning_token_position(prompt_length=prompt_length, token_index=index)
        for index in target_generated
    ]
    direct_absolute = [
        absolute_reasoning_token_position(prompt_length=prompt_length, token_index=index)
        for index in direct_generated
    ]
    patch_generated = sorted({int(value) for value in patch_generated_indices})
    patch_absolute = [
        absolute_reasoning_token_position(prompt_length=prompt_length, token_index=index)
        for index in patch_generated
    ]
    if (donor_states is None) != (not patch_generated):
        raise ValueError("Route donor states and patch positions must be supplied together")
    candidates: dict[str, Any] = {}
    states: dict[str, dict[str, Any]] = {}
    for candidate, suffix in zip(CANDIDATES, (original_suffix_ids, counterfactual_suffix_ids)):
        route_patch: _RouteCachePatchWithCapture | None = None
        capture: CaptureTokenKV | None = None
        if donor_states is None:
            capture = CaptureTokenKV(model=model, positions=target_absolute, selected_layers=layers)
            cache_context = capture
        else:
            donor = select_captured_positions(
                donor_states[candidate]["cache"],
                captured_positions=donor_states[candidate]["cache_positions"],
                selected_positions=patch_absolute,
            )
            route_patch = _RouteCachePatchWithCapture(
                model=model,
                donor_layers=donor,
                selected_layers=layers,
                positions=patch_absolute,
                current_query_position=patch_absolute[-1] + 1,
                visual_positions=visual_positions,
                mode="KV",
                target_capture_positions=target_absolute,
            )
            cache_context = route_patch
        suppressions = _suppressions(
            model=model,
            layers=layers,
            absolute_queries=direct_absolute,
            source_positions=source_positions,
            selected_heads=selected_heads,
        ) if direct_suppression else []
        with ExitStack() as stack:
            stack.enter_context(cache_context)
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
        if route_patch is None:
            assert capture is not None
            cache = capture.complete()
            cache_audit = copy.deepcopy(capture.audit)
            patch_audit = []
        else:
            cache = route_patch.complete_target_capture()
            cache_audit = [{
                "layer_index": int(layer),
                "layer_selected": True,
                "positions": target_absolute,
                "key_shape": list(cache[int(layer)][0].shape),
                "value_shape": list(cache[int(layer)][1].shape),
                "post_rope_key": True,
                "value_projection": True,
            } for layer in sorted(cache)]
            patch_audit = route_patch.complete()
        states[candidate] = {
            "cache": cache,
            "cache_positions": target_absolute,
            "cache_audit": cache_audit,
            "route_patch_audit": patch_audit,
            "suppression_audit": [suppression.complete() for suppression in suppressions],
        }
    result = _preference(candidates)
    result.update({
        "direct_suppression": bool(direct_suppression),
        "direct_source_window_generated_indices": direct_generated,
        "direct_source_window_absolute_positions": direct_absolute,
        "patch_generated_indices": patch_generated,
        "patch_absolute_positions": patch_absolute,
        "target_capture_generated_indices": target_generated,
        "target_capture_absolute_positions": target_absolute,
        "cache_mode": "KV",
        "visual_cache_donor_patched": False,
    })
    return result, states


__all__ = [
    "absolute_reasoning_token_position",
    "capture_checkpoint_span_states",
    "score_checkpoint_span_rescue",
    "score_route_arm",
    "summarize_cache_state_difference",
    "validate_checkpoint_coordinates",
    "validate_rescue_positions",
    "validate_route_coordinates",
]
