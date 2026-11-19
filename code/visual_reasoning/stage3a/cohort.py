"""Validation helpers for the Stage 3A prospectively frozen cohort."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any, Iterable, Mapping


def merge_expansion_outcomes(
    frozen_rows: Iterable[Mapping[str, Any]],
    outcome_rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Validate and order raw outcomes against the frozen generation manifest."""

    frozen = [dict(row) for row in frozen_rows]
    outcomes = [dict(row) for row in outcome_rows]
    frozen_ids = [str(row["example_id"]) for row in frozen]
    outcome_ids = [str(row["example_id"]) for row in outcomes]
    duplicate_ids = sorted(key for key, count in Counter(outcome_ids).items() if count > 1)
    if duplicate_ids:
        raise ValueError(f"duplicate expansion outcome example IDs: {duplicate_ids}")
    missing = sorted(set(frozen_ids) - set(outcome_ids))
    extra = sorted(set(outcome_ids) - set(frozen_ids))
    if missing or extra:
        raise ValueError(f"expansion result mismatch; missing={missing}, extra={extra}")
    by_id = {str(row["example_id"]): row for row in outcomes}
    merged = []
    for planned in frozen:
        example_id = str(planned["example_id"])
        outcome = by_id[example_id]
        if str(outcome["base_problem_id"]) != str(planned["base_problem_id"]):
            raise ValueError(f"base_problem_id mismatch for example {example_id}")
        merged.append({**planned, **outcome})
    return merged


def validate_strict_pre_e0_audit(
    *,
    generated_token_ids: Iterable[int],
    e0_start_token: int,
    e1_completion_token: int,
    evidence_neutral: bool,
) -> dict[str, Any]:
    """Validate and hash an exact ``y_<E0`` prefix for one accepted audit row."""

    token_ids = [int(value) for value in generated_token_ids]
    e0 = int(e0_start_token)
    e1 = int(e1_completion_token)
    if not 0 <= e0 < len(token_ids):
        raise ValueError(f"E0 must index a generated token: e0={e0}, length={len(token_ids)}")
    if not e0 <= e1 < len(token_ids):
        raise ValueError(f"E1 must be at or after E0 and within the trace: e0={e0}, e1={e1}")
    if not evidence_neutral:
        raise ValueError("Accepted strict pre-E0 prefixes must be strictly evidence-neutral")
    prefix = token_ids[:e0]
    payload = json.dumps(prefix, separators=(",", ":")).encode("ascii")
    return {
        "prefix_token_ids": prefix,
        "prefix_token_count": len(prefix),
        "prefix_sha256": hashlib.sha256(payload).hexdigest(),
    }
