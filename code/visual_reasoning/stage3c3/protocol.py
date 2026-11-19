"""Prospective protocol decisions for Stage 3C.3."""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from typing import Any


FORMULATION_ORDER = ("content_recipient_rope", "direct_post_rope")
MECHANICAL_FORMULATION_FIELDS = (
    "self_exact",
    "kv_exact",
    "nonselected_heads_exact",
    "deterministic",
)


def split_validation_primary(
    base_problem_ids: Sequence[str], *, validation_count: int, seed: int
) -> dict[str, list[str]]:
    """Make an outcome-blind deterministic validation/primary split."""

    bases = [str(value) for value in base_problem_ids]
    if len(bases) != len(set(bases)):
        raise ValueError("Base problem IDs must be unique")
    if validation_count <= 0 or validation_count >= len(bases):
        raise ValueError("Validation count must leave a nonempty primary cohort")
    selected = set(random.Random(int(seed)).sample(bases, int(validation_count)))
    return {
        "validation": [base for base in bases if base in selected],
        "primary": [base for base in bases if base not in selected],
    }


def choose_query_formulation(audits: Mapping[str, Mapping[str, Any]]) -> str:
    """Prefer content-space recipient-RoPE when mechanical audits pass.

    Effect-size fields are deliberately ignored so formulation choice cannot be
    tuned to the scientific outcome.
    """

    for name in FORMULATION_ORDER:
        audit = audits.get(name, {})
        if all(bool(audit.get(field)) for field in MECHANICAL_FORMULATION_FIELDS):
            return name
    raise ValueError("No mechanically valid query formulation is available")


def phase_a_target_passes(summary: Mapping[str, Any]) -> bool:
    """Evaluate the frozen directional Phase-A gate for one target."""

    for direction in ("necessity", "sufficiency"):
        row = summary[direction]
        if not (
            float(row["routing_median"]) > 0.0
            and float(row["routing_positive_fraction"]) >= 2.0 / 3.0
            and float(row["alpha_v_median"]) > 0.0
            and float(row["evidence_median"]) > 0.0
        ):
            return False
    return bool(
        float(summary["causal_minus_noncausal_median"]) > 0.0
        and summary["self_exact"]
    )


__all__ = [
    "FORMULATION_ORDER",
    "MECHANICAL_FORMULATION_FIELDS",
    "choose_query_formulation",
    "phase_a_target_passes",
    "split_validation_primary",
]
