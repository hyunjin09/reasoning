"""Full-sequence scoring with current-position module restoration."""

from __future__ import annotations

import copy
from collections.abc import Sequence
from typing import Any

from visual_reasoning.stage3a.runtime import score_candidate
from visual_reasoning.stage3b4.modules import (
    CaptureCurrentModuleContributions,
    CurrentPositionModulePatch,
    valid_module_capture_audit,
    valid_module_patch_audit,
)


CANDIDATES = ("original_candidate", "counterfactual_candidate")


def absolute_intervention_position(
    *, prompt_length: int, intervention_generated_index: int
) -> int:
    """Map the frozen generated-token coordinate to its absolute sequence position."""
    if prompt_length <= 0 or intervention_generated_index <= 0:
        raise ValueError("Module intervention requires a nonempty prompt and positive coordinate")
    return int(prompt_length) + int(intervention_generated_index) - 1


def capture_candidate_current_modules(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_token_ids: Sequence[int],
    intervention_generated_index: int,
    layer_indices: Sequence[int],
    module_kinds: Sequence[str],
    seed: int,
) -> dict[str, Any]:
    prompt_length = int(prepared["input_ids"].shape[1])
    position = absolute_intervention_position(
        prompt_length=prompt_length,
        intervention_generated_index=intervention_generated_index,
    )
    if intervention_generated_index > len(context_token_ids):
        raise ValueError("Module intervention coordinate lies after the frozen context")
    capture = CaptureCurrentModuleContributions(
        model=model,
        position=position,
        layer_indices=layer_indices,
        module_kinds=module_kinds,
    )
    with capture:
        score = score_candidate(
            model=model,
            prepared=prepared,
            prefix_token_ids=context_token_ids,
            candidate_token_ids=candidate_token_ids,
            seed=seed,
        )
    states = capture.complete_states()
    audit = copy.deepcopy(capture.audit)
    return {
        "score": score,
        "states": states,
        "capture_audit": audit,
        "capture_audit_valid": valid_module_capture_audit(
            audit,
            layer_indices=layer_indices,
            module_kinds=module_kinds,
            position=position,
        ),
        "current_absolute_position": position,
    }


def capture_preference_current_modules(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_original_ids: Sequence[int],
    candidate_counterfactual_ids: Sequence[int],
    intervention_generated_index: int,
    layer_indices: Sequence[int],
    module_kinds: Sequence[str],
    seed: int,
) -> dict[str, Any]:
    captures = {
        "original_candidate": capture_candidate_current_modules(
            model=model,
            prepared=prepared,
            context_token_ids=context_token_ids,
            candidate_token_ids=candidate_original_ids,
            intervention_generated_index=intervention_generated_index,
            layer_indices=layer_indices,
            module_kinds=module_kinds,
            seed=seed,
        ),
        "counterfactual_candidate": capture_candidate_current_modules(
            model=model,
            prepared=prepared,
            context_token_ids=context_token_ids,
            candidate_token_ids=candidate_counterfactual_ids,
            intervention_generated_index=intervention_generated_index,
            layer_indices=layer_indices,
            module_kinds=module_kinds,
            seed=seed,
        ),
    }
    original = captures["original_candidate"]["score"]
    counterfactual = captures["counterfactual_candidate"]["score"]
    return {
        "original_candidate": original,
        "counterfactual_candidate": counterfactual,
        "L_o": float(original["mean_log_probability"]),
        "L_c": float(counterfactual["mean_log_probability"]),
        "D": float(
            original["mean_log_probability"] - counterfactual["mean_log_probability"]
        ),
        "states": {
            candidate: captures[candidate]["states"] for candidate in CANDIDATES
        },
        "capture_audits": {
            candidate: captures[candidate]["capture_audit"] for candidate in CANDIDATES
        },
        "all_module_capture_audits_valid": all(
            bool(captures[candidate]["capture_audit_valid"])
            for candidate in CANDIDATES
        ),
        "current_absolute_position": captures["original_candidate"][
            "current_absolute_position"
        ],
    }


def score_candidate_with_current_modules(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_token_ids: Sequence[int],
    intervention_generated_index: int,
    layer_indices: Sequence[int],
    module_kinds: Sequence[str],
    source_states: dict[str, dict[int, Any]],
    seed: int,
) -> dict[str, Any]:
    position = absolute_intervention_position(
        prompt_length=int(prepared["input_ids"].shape[1]),
        intervention_generated_index=intervention_generated_index,
    )
    if intervention_generated_index > len(context_token_ids):
        raise ValueError("Module intervention coordinate lies after the frozen context")
    patch = CurrentPositionModulePatch(
        model=model,
        position=position,
        source_states=source_states,
        layer_indices=layer_indices,
        module_kinds=module_kinds,
    )
    with patch:
        score = score_candidate(
            model=model,
            prepared=prepared,
            prefix_token_ids=context_token_ids,
            candidate_token_ids=candidate_token_ids,
            seed=seed,
        )
    audit = copy.deepcopy(patch.audit)
    score["module_patch_audit"] = audit
    score["module_patch_audit_valid"] = valid_module_patch_audit(
        audit,
        layer_indices=layer_indices,
        module_kinds=module_kinds,
        position=position,
    )
    return score


def score_preference_with_current_modules(
    *,
    model: Any,
    prepared: dict[str, Any],
    context_token_ids: Sequence[int],
    candidate_original_ids: Sequence[int],
    candidate_counterfactual_ids: Sequence[int],
    intervention_generated_index: int,
    layer_indices: Sequence[int],
    module_kinds: Sequence[str],
    source_states_by_candidate: dict[str, dict[str, dict[int, Any]]],
    seed: int,
) -> dict[str, Any]:
    original = score_candidate_with_current_modules(
        model=model,
        prepared=prepared,
        context_token_ids=context_token_ids,
        candidate_token_ids=candidate_original_ids,
        intervention_generated_index=intervention_generated_index,
        layer_indices=layer_indices,
        module_kinds=module_kinds,
        source_states=source_states_by_candidate["original_candidate"],
        seed=seed,
    )
    counterfactual = score_candidate_with_current_modules(
        model=model,
        prepared=prepared,
        context_token_ids=context_token_ids,
        candidate_token_ids=candidate_counterfactual_ids,
        intervention_generated_index=intervention_generated_index,
        layer_indices=layer_indices,
        module_kinds=module_kinds,
        source_states=source_states_by_candidate["counterfactual_candidate"],
        seed=seed,
    )
    return {
        "original_candidate": original,
        "counterfactual_candidate": counterfactual,
        "L_o": float(original["mean_log_probability"]),
        "L_c": float(counterfactual["mean_log_probability"]),
        "D": float(original["mean_log_probability"] - counterfactual["mean_log_probability"]),
        "all_module_patch_audits_valid": bool(
            original["module_patch_audit_valid"]
            and counterfactual["module_patch_audit_valid"]
        ),
    }
