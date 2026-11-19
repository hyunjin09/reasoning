"""Combined P4 suppression and current-position residual rescue mechanics."""

from __future__ import annotations

import copy
import math
from collections.abc import Mapping, Sequence
from contextlib import ExitStack
from typing import Any

import torch

from visual_reasoning.stage3b4.runtime import absolute_intervention_position
from visual_reasoning.stage3b5.boundaries import (
    CaptureCurrentBlockBoundaries,
    CurrentPositionBoundaryPatch,
    valid_boundary_patch_audit,
)
from visual_reasoning.stage3c3.runtime import score_evidence_suffix
from visual_reasoning.stage3c4.runtime import SourceContributionWindowPatch


CANDIDATES = ("original_candidate", "counterfactual_candidate")


def _maximum(value: torch.Tensor) -> float:
    return float(value.abs().max().item()) if value.numel() else 0.0


def _preference(candidates: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    original = candidates["original_candidate"]
    counterfactual = candidates["counterfactual_candidate"]
    lo = float(original["mean_log_probability"])
    lc = float(counterfactual["mean_log_probability"])
    return {
        "L_o": lo,
        "L_c": lc,
        "D": lo - lc,
        "finite": bool(original["finite"] and counterfactual["finite"]),
        "original_candidate": original,
        "counterfactual_candidate": counterfactual,
    }


def interpolate_residual(
    suppressed: torch.Tensor, native: torch.Tensor, gain: float
) -> torch.Tensor:
    if suppressed.shape != native.shape:
        raise ValueError("Native and suppressed residuals must have matching shapes")
    scalar = float(gain)
    if not math.isfinite(scalar) or not 0.0 <= scalar <= 1.0:
        raise ValueError("Residual-delta gain must be finite and inside [0,1]")
    if scalar == 0.0:
        return suppressed.detach().clone()
    if scalar == 1.0:
        return native.detach().clone()
    return suppressed + scalar * (native - suppressed)


def residual_delta_summaries(
    native: Mapping[str, Mapping[int, torch.Tensor]],
    suppressed: Mapping[str, Mapping[int, torch.Tensor]],
    *,
    boundary: str,
) -> list[dict[str, Any]]:
    native_layers = native[boundary]
    suppressed_layers = suppressed[boundary]
    if set(native_layers) != set(suppressed_layers):
        raise ValueError("Native/suppressed residual layer sets differ")
    rows = []
    for layer in sorted(native_layers):
        left = native_layers[layer].detach().float()
        right = suppressed_layers[layer].detach().float()
        if left.shape != right.shape:
            raise ValueError("Native/suppressed residual tensor shapes differ")
        delta = left - right
        native_norm = float(torch.linalg.vector_norm(left).item())
        rows.append({
            "layer": int(layer),
            "boundary": boundary,
            "shape": list(left.shape),
            "delta_l2": float(torch.linalg.vector_norm(delta).item()),
            "native_l2": native_norm,
            "suppressed_l2": float(torch.linalg.vector_norm(right).item()),
            "relative_delta_l2": float(torch.linalg.vector_norm(delta).item()) / native_norm if native_norm else None,
            "max_abs_delta": _maximum(delta),
            "finite": bool(torch.isfinite(left).all() and torch.isfinite(right).all()),
        })
    return rows


def boundary_equivalence(
    states: Mapping[str, Mapping[int, torch.Tensor]],
) -> list[dict[str, Any]]:
    post = states["h_post_block"]
    pre = states["h_pre"]
    rows = []
    for layer in sorted(set(post) & {index - 1 for index in pre}):
        delta = post[layer].detach().float() - pre[layer + 1].detach().float()
        rows.append({
            "layer": int(layer),
            "next_layer": int(layer + 1),
            "exact": bool(torch.equal(post[layer], pre[layer + 1])),
            "max_abs_delta": _maximum(delta),
        })
    return rows


def _suppression_patches(
    *, model: Any, absolute_tpre: int, layers: Sequence[int], source_positions: Sequence[int],
    selected_heads: Sequence[int], gain: float,
) -> list[SourceContributionWindowPatch]:
    return [
        SourceContributionWindowPatch(
            model=model,
            layer_index=int(layer),
            query_positions=[int(absolute_tpre)],
            selected_heads=selected_heads,
            source_positions=source_positions,
            gain=float(gain),
        )
        for layer in sorted({int(value) for value in layers})
    ]


@torch.inference_mode()
def capture_preference_states(
    *,
    model: Any,
    prepared: dict[str, Any],
    prefix_token_ids: Sequence[int],
    bridge_token_ids: Sequence[int],
    original_suffix_ids: Sequence[int],
    counterfactual_suffix_ids: Sequence[int],
    current_generated_index: int,
    capture_layers: Sequence[int],
    suppression_generated_index: int | None,
    suppression_layers: Sequence[int],
    source_positions: Sequence[int],
    selected_heads: Sequence[int],
    suppression_gain: float,
    seed: int,
) -> tuple[dict[str, Any], dict[str, dict[str, dict[int, torch.Tensor]]]]:
    """Score and capture current-position states, optionally under P4 suppression."""

    prompt_length = int(prepared["input_ids"].shape[1])
    current_absolute = absolute_intervention_position(
        prompt_length=prompt_length,
        intervention_generated_index=int(current_generated_index),
    )
    absolute_tpre = (
        absolute_intervention_position(
            prompt_length=prompt_length,
            intervention_generated_index=int(suppression_generated_index),
        )
        if suppression_generated_index is not None
        else None
    )
    candidates: dict[str, Any] = {}
    states: dict[str, dict[str, dict[int, torch.Tensor]]] = {}
    capture_audits: dict[str, Any] = {}
    residual_audits: dict[str, Any] = {}
    suppression_audits: dict[str, Any] = {}
    for candidate, suffix in zip(CANDIDATES, (original_suffix_ids, counterfactual_suffix_ids)):
        capture = CaptureCurrentBlockBoundaries(
            model=model, position=current_absolute, layer_indices=capture_layers
        )
        patches = (
            _suppression_patches(
                model=model, absolute_tpre=int(absolute_tpre), layers=suppression_layers,
                source_positions=source_positions, selected_heads=selected_heads,
                gain=suppression_gain,
            )
            if absolute_tpre is not None
            else []
        )
        with ExitStack() as stack:
            stack.enter_context(capture)
            for patch in patches:
                stack.enter_context(patch)
            candidates[candidate] = score_evidence_suffix(
                model=model, prepared=prepared, prefix_token_ids=prefix_token_ids,
                bridge_token_ids=bridge_token_ids, suffix_token_ids=suffix, seed=seed,
            )
        states[candidate] = capture.complete_states()
        capture_audits[candidate] = copy.deepcopy(capture.audit)
        residual_audits[candidate] = copy.deepcopy(capture.residual_addition_audit)
        suppression_audits[candidate] = [patch.complete() for patch in patches]
    result = _preference(candidates)
    result.update({
        "current_generated_index": int(current_generated_index),
        "current_absolute_position": current_absolute,
        "suppression_generated_index": suppression_generated_index,
        "suppression_absolute_position": absolute_tpre,
        "suppression_layers": sorted({int(value) for value in suppression_layers}) if absolute_tpre is not None else [],
        "suppression_gain": float(suppression_gain) if absolute_tpre is not None else None,
        "capture_layers": sorted({int(value) for value in capture_layers}),
        "capture_audits": capture_audits,
        "residual_addition_audits": residual_audits,
        "suppression_audits": suppression_audits,
    })
    return result, states


@torch.inference_mode()
def score_preference_with_residual_source(
    *,
    model: Any,
    prepared: dict[str, Any],
    prefix_token_ids: Sequence[int],
    bridge_token_ids: Sequence[int],
    original_suffix_ids: Sequence[int],
    counterfactual_suffix_ids: Sequence[int],
    current_generated_index: int,
    layer_index: int,
    boundary: str,
    source_states_by_candidate: Mapping[str, Mapping[str, Mapping[int, torch.Tensor]]],
    suppression_generated_index: int | None,
    suppression_layers: Sequence[int],
    source_positions: Sequence[int],
    selected_heads: Sequence[int],
    suppression_gain: float,
    seed: int,
) -> dict[str, Any]:
    """Patch one current residual while leaving all past/visual K/V donor-free."""

    prompt_length = int(prepared["input_ids"].shape[1])
    current_absolute = absolute_intervention_position(
        prompt_length=prompt_length,
        intervention_generated_index=int(current_generated_index),
    )
    absolute_tpre = (
        absolute_intervention_position(
            prompt_length=prompt_length,
            intervention_generated_index=int(suppression_generated_index),
        )
        if suppression_generated_index is not None
        else None
    )
    candidates: dict[str, Any] = {}
    patch_audits: dict[str, Any] = {}
    suppression_audits: dict[str, Any] = {}
    for candidate, suffix in zip(CANDIDATES, (original_suffix_ids, counterfactual_suffix_ids)):
        residual_patch = CurrentPositionBoundaryPatch(
            model=model,
            position=current_absolute,
            layer_index=int(layer_index),
            boundary=boundary,
            source_state=source_states_by_candidate[candidate][boundary][int(layer_index)],
        )
        patches = (
            _suppression_patches(
                model=model, absolute_tpre=int(absolute_tpre), layers=suppression_layers,
                source_positions=source_positions, selected_heads=selected_heads,
                gain=suppression_gain,
            )
            if absolute_tpre is not None
            else []
        )
        with ExitStack() as stack:
            for patch in patches:
                stack.enter_context(patch)
            stack.enter_context(residual_patch)
            candidates[candidate] = score_evidence_suffix(
                model=model, prepared=prepared, prefix_token_ids=prefix_token_ids,
                bridge_token_ids=bridge_token_ids, suffix_token_ids=suffix, seed=seed,
            )
        patch_audits[candidate] = copy.deepcopy(residual_patch.audit)
        suppression_audits[candidate] = [patch.complete() for patch in patches]
    result = _preference(candidates)
    result.update({
        "layer_index": int(layer_index),
        "boundary": boundary,
        "current_generated_index": int(current_generated_index),
        "current_absolute_position": current_absolute,
        "suppression_generated_index": suppression_generated_index,
        "suppression_absolute_position": absolute_tpre,
        "suppression_layers": sorted({int(value) for value in suppression_layers}) if absolute_tpre is not None else [],
        "suppression_gain": float(suppression_gain) if absolute_tpre is not None else None,
        "boundary_patch_audits": patch_audits,
        "boundary_patch_audits_valid": all(
            valid_boundary_patch_audit(
                patch_audits[candidate], layer_index=int(layer_index),
                boundary=boundary, position=current_absolute,
            )
            for candidate in CANDIDATES
        ),
        "suppression_audits": suppression_audits,
        "current_position_only": True,
        "past_token_kv_donor_patched": False,
        "visual_kv_donor_patched": False,
    })
    return result


__all__ = [
    "CANDIDATES",
    "boundary_equivalence",
    "capture_preference_states",
    "interpolate_residual",
    "residual_delta_summaries",
    "score_preference_with_residual_source",
]
