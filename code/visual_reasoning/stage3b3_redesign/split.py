"""Outcome-independent method-validation split construction."""

from __future__ import annotations

import random
from collections.abc import Iterable, Mapping, Sequence
from typing import Any


def _sort_key(value: str) -> tuple[int, str]:
    text = str(value)
    return (int(text), text) if text.isdigit() else (10**18, text)


def freeze_method_validation_split(
    rows: Sequence[Mapping[str, Any]],
    *,
    exact_base_ids: Iterable[str],
    seed: int,
    validation_count: int = 8,
    required_exact_count: int = 2,
) -> dict[str, Any]:
    """Select a seeded numeric-only validation set with an exact-token stratum."""

    all_ids = [str(row["base_problem_id"]) for row in rows]
    if len(all_ids) != len(set(all_ids)):
        raise ValueError("base_problem_id must be unique before splitting")
    numeric = sorted(
        (
            str(row["base_problem_id"])
            for row in rows
            if row["edit_tier"] == "tier1_local_numeric_label"
        ),
        key=_sort_key,
    )
    exact = sorted(set(str(value) for value in exact_base_ids) & set(numeric), key=_sort_key)
    if validation_count > len(numeric):
        raise ValueError("Not enough numeric examples for the requested validation split")
    if required_exact_count > len(exact) or required_exact_count > validation_count:
        raise ValueError("Not enough exact-baseline numeric examples")

    rng = random.Random(int(seed))
    selected_exact = rng.sample(exact, required_exact_count)
    remaining = [base for base in numeric if base not in selected_exact]
    selected_other = rng.sample(remaining, validation_count - required_exact_count)
    validation = sorted(selected_exact + selected_other, key=_sort_key)
    validation_set = set(validation)
    primary = [base for base in all_ids if base not in validation_set]
    return {
        "seed": int(seed),
        "selection_rule": (
            "sample 2 exact-baseline numeric-label bases, then 6 additional numeric-label "
            "bases from the remainder with Python random.Random(seed); sort selected IDs numerically"
        ),
        "structural_restoration_omitted": True,
        "structural_omission_reason": (
            "A genuinely independent semantics-preserving structural C_sham was not cleanly "
            "guaranteed; the approved plan permits eight numeric-label validation bases."
        ),
        "selected_exact_base_problem_ids": sorted(selected_exact, key=_sort_key),
        "validation_base_problem_ids": validation,
        "primary_base_problem_ids": primary,
    }

