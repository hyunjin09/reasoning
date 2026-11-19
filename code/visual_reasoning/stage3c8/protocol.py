"""Frozen cohort, token-taxonomy, and gate rules for Stage 3C.8."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any


SOURCE_PRIORITY = {"GeoQA": 0, "GEOS": 1, "Geometry3K": 2}
FUNCTION_WORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in",
    "is", "of", "on", "or", "the", "to", "was", "were", "with",
})
INTERROGATIVES = frozenset({"what", "which", "where", "when", "who", "whom", "whose", "why", "how"})
RELATION_OPERATORS = frozenset({
    "above", "below", "between", "equal", "equals", "greater", "inside", "left",
    "less", "parallel", "perpendicular", "right", "same", "similar", "than",
})
DISCOURSE_MARKERS = frozenset({
    "also", "first", "however", "next", "now", "so", "then", "therefore", "thus", "verify", "wait",
})
MATH_OPERATORS = frozenset({"+", "-", "−", "*", "×", "/", "÷", "=", "≈", "<", ">", "≤", "≥"})


def local_cuda_device_index(
    environment: Mapping[str, str], *, visible_device_count: int | None = None,
) -> int:
    """Return a valid process-local CUDA ordinal for torchrun or Slurm."""

    raw = environment.get("LOCAL_RANK", environment.get("SLURM_LOCALID", "0"))
    value = int(raw)
    if value < 0:
        raise ValueError(f"CUDA local rank must be non-negative, observed {value}")
    if visible_device_count is not None:
        if visible_device_count < 1:
            raise ValueError("At least one CUDA device must be visible")
        if visible_device_count == 1:
            return 0
        if value >= visible_device_count:
            raise ValueError(
                f"CUDA local rank {value} lies outside {visible_device_count} visible devices"
            )
    return value


def distributed_process_info(
    environment: Mapping[str, str], *, visible_device_count: int | None = None,
) -> tuple[int, int, int]:
    """Return world size, global rank, and local CUDA device for torchrun or srun."""

    world_size = int(environment.get("WORLD_SIZE", environment.get("SLURM_NTASKS", "1")))
    rank = int(environment.get("RANK", environment.get("SLURM_PROCID", "0")))
    local_device = local_cuda_device_index(
        environment, visible_device_count=visible_device_count,
    )
    if world_size < 1:
        raise ValueError(f"World size must be positive, observed {world_size}")
    if rank < 0 or rank >= world_size:
        raise ValueError(f"Rank {rank} lies outside world size {world_size}")
    return world_size, rank, local_device


def select_fresh_screen(
    dataset_rows: Sequence[Mapping[str, Any]], *, excluded_base_ids: Iterable[str], budget: int,
) -> list[dict[str, Any]]:
    """Select the frozen source-prioritized fresh screen without outcome signals."""

    excluded = {str(value) for value in excluded_base_ids}
    candidates = []
    for row in dataset_rows:
        base = str(row["problem_index"])
        source = str(row.get("metadata", {}).get("source", ""))
        if str(row.get("problem_version")) != "Vision Dominant" or base in excluded or source not in SOURCE_PRIORITY:
            continue
        candidates.append((SOURCE_PRIORITY[source], int(base), row))
    candidates.sort(key=lambda item: (item[0], item[1]))
    if len(candidates) < int(budget):
        raise ValueError(f"Only {len(candidates)} eligible fresh bases for budget {budget}")
    selected = []
    for order, (_, _, row) in enumerate(candidates[: int(budget)]):
        selected.append({
            "order": order,
            "base_problem_id": str(row["problem_index"]),
            "example_id": str(row["sample_index"]),
            "variant": str(row["problem_version"]),
            "image_id": str(row["image"]),
            "source": str(row["metadata"]["source"]),
            "subject": str(row["metadata"].get("subject", "")),
            "subfield": str(row["metadata"].get("subfield", "")),
            "selection_basis": "source-prioritized ascending base order after conservative prior-use exclusion",
            "selection_used_attention": False,
            "selection_used_generation_outcome": False,
            "selection_used_carrier_outcome": False,
        })
    return selected


def normalize_piece(text: str) -> str:
    return str(text).strip().lower().replace("▁", "").replace("Ġ", "")


def classify_lexical_token(text: str, *, visual_entities: Iterable[str] = ()) -> str:
    """Assign the frozen lexical class from text and manual entity membership."""

    raw = str(text).strip().replace("▁", "").replace("Ġ", "")
    normalized = raw.lower()
    entities = {normalize_piece(value) for value in visual_entities}
    if re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:%|°)?", normalized):
        return "NUMERIC_LITERAL"
    if normalized and normalized in entities:
        return "VISUAL_ENTITY"
    if normalized in INTERROGATIVES:
        return "INTERROGATIVE"
    if normalized in RELATION_OPERATORS:
        return "RELATION_OPERATOR"
    if normalized in MATH_OPERATORS:
        return "MATH_OPERATOR"
    if normalized in FUNCTION_WORDS:
        return "FUNCTION_WORD"
    if normalized in DISCOURSE_MARKERS:
        return "DISCOURSE_MARKER"
    if raw and re.fullmatch(r"[^\w\s]+", raw, flags=re.UNICODE):
        return "PUNCTUATION"
    if normalized.startswith("<|") and normalized.endswith("|>"):
        return "SPECIAL_TOKEN"
    return "OTHER_CONTENT"


def phase_d_gate(
    *, phase_a_robust: Mapping[str, bool], phase_b_all_recent_median_rr: float,
    phase_b_local_or_group_robust: bool,
) -> dict[str, Any]:
    phase_a_pass = any(bool(value) for value in phase_a_robust.values())
    phase_b_pass = float(phase_b_all_recent_median_rr) >= 0.50 and bool(phase_b_local_or_group_robust)
    return {
        "run": bool(phase_a_pass or phase_b_pass),
        "phase_a_robust_any_coordinate": phase_a_pass,
        "phase_b_all_recent_substantial_and_local_or_group_robust": phase_b_pass,
        "phase_b_all_recent_median_rr": float(phase_b_all_recent_median_rr),
        "threshold": 0.50,
    }
