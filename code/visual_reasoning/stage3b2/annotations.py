"""Token-level discriminative-event definitions for Stage 3B.2."""

from __future__ import annotations

from typing import Any, Sequence


def longest_common_prefix(left: Sequence[int], right: Sequence[int]) -> list[int]:
    common: list[int] = []
    for left_value, right_value in zip(left, right):
        if int(left_value) != int(right_value):
            break
        common.append(int(left_value))
    return common


def discriminative_event(
    *,
    e0_start_token: int,
    original_candidate_ids: Sequence[int],
    counterfactual_candidate_ids: Sequence[int],
) -> dict[str, Any]:
    """Define E_d from the first token where frozen evidence candidates differ."""

    original = [int(value) for value in original_candidate_ids]
    counterfactual = [int(value) for value in counterfactual_candidate_ids]
    if not original or not counterfactual:
        raise ValueError("Evidence candidates must be nonempty")
    common = longest_common_prefix(original, counterfactual)
    if len(common) == len(original) or len(common) == len(counterfactual):
        raise ValueError("Evidence candidates must diverge before either candidate ends")
    original_suffix = original[len(common) :]
    counterfactual_suffix = counterfactual[len(common) :]
    e0 = int(e0_start_token)
    if e0 < 0:
        raise ValueError("E0 cannot be negative")
    return {
        "e0_start_token": e0,
        "common_prefix_token_count": len(common),
        "common_prefix_token_ids": common,
        "ed_generated_index": e0 + len(common),
        "first_original_divergent_token_id": original_suffix[0],
        "first_counterfactual_divergent_token_id": counterfactual_suffix[0],
        "original_divergent_suffix_ids": original_suffix,
        "counterfactual_divergent_suffix_ids": counterfactual_suffix,
    }
