"""Frozen cohort and gate helpers for Stage 3C.9."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any


def canonical_streaming_kwargs(config: Mapping[str, Any]) -> dict[str, Any]:
    """Resolve the frozen A6000 scorer without allowing path/chunk switching."""

    runtime = config.get("runtime", {})
    scoring = runtime.get("canonical_scoring", {})
    valid = (
        "A6000" in str(runtime.get("gpu_class", ""))
        and scoring.get("path") == "P2_fixed_streaming_cached"
        and int(scoring.get("chunk_size", 0)) > 0
        and scoring.get("release_allocator_cache_between_chunks") is True
        and scoring.get("per_example_chunk_switching") is False
    )
    if not valid:
        raise ValueError("Invalid or non-canonical Stage 3C.9 A6000 streaming runtime")
    return {
        "chunk_size": int(scoring["chunk_size"]),
        "release_allocator_cache": True,
    }


def intervention_boundaries(
    *position_groups: Sequence[int], end_generated_index: int,
) -> list[int]:
    """Return the shared partition boundaries required by every causal arm.

    A cache patch must be installed immediately after its final donor position.
    Every arm receives the union so chunk shapes do not depend on condition.
    """

    end = int(end_generated_index)
    return sorted({
        int(position) + 1
        for group in position_groups
        for position in group
        if 0 < int(position) + 1 <= end
    })


def _static_rank(row: Mapping[str, Any]) -> tuple[int, int, str, int]:
    numeric_count = int(row.get("stage3c9_static_numeric_candidate_count", 0))
    question = str(row.get("question_for_eval") or row.get("query") or "")
    source = str(row.get("metadata", {}).get("source", ""))
    return (-int(numeric_count > 0), -len(question.split()), source, int(row["problem_index"]))


def select_prospective_screen(
    dataset_rows: Sequence[Mapping[str, Any]], *, total_budget: int, initial_budget: int,
) -> list[dict[str, Any]]:
    """Select an outcome- and attention-blind long-horizon screen.

    The initial tranche contains one Vision Dominant row per base. The reserve
    adds Vision Intensive rows in the same frozen base order, so a base can be
    retried without being counted twice as an independent primary sample.
    """

    if initial_budget < 1 or total_budget < initial_budget:
        raise ValueError("Require 1 <= initial_budget <= total_budget")
    by_variant: dict[str, dict[str, Mapping[str, Any]]] = {}
    for row in dataset_rows:
        variant = str(row.get("problem_version", ""))
        if variant not in {"Vision Dominant", "Vision Intensive"}:
            continue
        base = str(row["problem_index"])
        variants = by_variant.setdefault(base, {})
        if variant in variants:
            raise ValueError(f"Duplicate {variant} row for base {base}")
        variants[variant] = row

    dominant = [variants["Vision Dominant"] for variants in by_variant.values() if "Vision Dominant" in variants]
    dominant.sort(key=_static_rank)
    if len(dominant) < initial_budget:
        raise ValueError(
            f"Only {len(dominant)} unique Vision Dominant bases are available for initial budget {initial_budget}"
        )
    all_bases = [str(row["problem_index"]) for row in dominant]
    selected_rows: list[tuple[Mapping[str, Any], str]] = [
        (row, "initial" if index < initial_budget else "reserve")
        for index, row in enumerate(dominant[:total_budget])
    ]

    if len(selected_rows) < total_budget:
        for base in all_bases:
            row = by_variant[base].get("Vision Intensive")
            if row is not None:
                selected_rows.append((row, "reserve"))
                if len(selected_rows) == total_budget:
                    break
    if len(selected_rows) < total_budget:
        raise ValueError(f"Only {len(selected_rows)} prospective rows are available for total budget {total_budget}")

    result = []
    for order, (row, phase) in enumerate(selected_rows):
        result.append({
            "screen_order": order,
            "screen_phase": phase,
            "base_problem_id": str(row["problem_index"]),
            "example_id": str(row["sample_index"]),
            "variant": str(row["problem_version"]),
            "image_id": str(row["image"]),
            "source": str(row.get("metadata", {}).get("source", "")),
            "subject": str(row.get("metadata", {}).get("subject", "")),
            "subfield": str(row.get("metadata", {}).get("subfield", "")),
            "static_question_word_count": len(str(row.get("question_for_eval") or row.get("query") or "").split()),
            "static_numeric_candidate_count": int(row.get("stage3c9_static_numeric_candidate_count", 0)),
            "selection_basis": "static numeric-edit feasibility, descending question word count, source, base ID",
            "selection_used_attention": False,
            "selection_used_generation_outcome": False,
            "selection_used_carrier_outcome": False,
        })
    return result


def long_horizon_cohort_gate(
    primary_base_ids: Iterable[str], validation_base_ids: Iterable[str],
    *, minimum_primary: int = 40, required_validation: int = 8,
) -> dict[str, Any]:
    primary = {str(value) for value in primary_base_ids}
    validation = {str(value) for value in validation_base_ids}
    overlap = sorted(primary & validation, key=lambda value: int(value) if value.isdigit() else value)
    return {
        "run_primary": len(primary) >= minimum_primary and len(validation) >= required_validation and not overlap,
        "N_primary_unique": len(primary),
        "N_validation_unique": len(validation),
        "minimum_primary": int(minimum_primary),
        "required_validation": int(required_validation),
        "overlap_base_problem_ids": overlap,
    }


def first_route_pair(events: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    """Return the first separated C2/C3 pair in frozen annotation order."""

    qualified = sorted(
        (
            row for row in events
            if str(row.get("classification")) in {"C2", "C3"}
        ),
        key=lambda row: (int(row["span_start_token"]), int(row["event_id"])),
    )
    for left_index, left in enumerate(qualified):
        for right in qualified[left_index + 1:]:
            if int(right["span_start_token"]) - int(left["span_start_token"]) < 24:
                continue
            if int(left["span_end_token"]) > int(right["span_start_token"]):
                continue
            return {
                "event_a_id": int(left["event_id"]),
                "event_b_id": int(right["event_id"]),
                "separation": int(right["span_start_token"]) - int(left["span_start_token"]),
                "selection_rule": "first eligible pair by frozen annotation order",
                "selection_used_effect_size": False,
                "selection_used_attention": False,
            }
    return None


def phase_d_route_gate(rows: Sequence[Mapping[str, Any]], *, minimum_bases: int = 16) -> dict[str, Any]:
    """Apply the predeclared unique-base feasibility gate for route decomposition."""

    eligible = {
        str(row["base_problem_id"])
        for row in rows
        if row.get("route_pair") is not None
    }
    return {
        "run_phase_d": len(eligible) >= int(minimum_bases),
        "eligible_unique_bases": len(eligible),
        "minimum_unique_bases": int(minimum_bases),
        "pair_selection": "first eligible pair per base by frozen annotation order",
        "selection_used_effect_size": False,
        "selection_used_attention": False,
    }
