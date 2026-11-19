"""Token/event alignment and descriptive timing helpers for Stage 2C."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

import numpy as np


REGION_NAMES = ("PRE", "ENTITY", "FACT", "POST", "USE")


def attention_row_convention(
    query_lengths: np.ndarray,
    key_lengths: np.ndarray,
    prompt_length: int,
    generated_token_ids: Sequence[int],
) -> list[dict]:
    """Describe each retained row's query and predicted generated token.

    Generation step ``t`` retains the last query row of the forward that
    produces logits for ``y_t``. At ``t=0`` the query is the final prompt
    token. At later steps it is ``y_(t-1)``.
    """
    queries = np.asarray(query_lengths, dtype=np.int64)
    keys = np.asarray(key_lengths, dtype=np.int64)
    token_ids = [int(value) for value in generated_token_ids]
    if queries.shape != (len(token_ids),) or keys.shape != (len(token_ids),):
        raise ValueError("query/key arrays must have one row per generated token")
    expected_keys = np.arange(int(prompt_length), int(prompt_length) + len(token_ids), dtype=np.int64)
    if not np.array_equal(keys, expected_keys):
        raise ValueError("key lengths do not advance from prompt length by one per generation step")
    if len(queries) and int(queries[0]) != int(prompt_length):
        raise ValueError("first query length must equal the uncached prompt length")
    if len(queries) > 1 and not np.all(queries[1:] == 1):
        raise ValueError("cached generation rows after prefill must have query length one")

    return [
        {
            "stored_row_index": index,
            "query_source": "final_prompt_token" if index == 0 else "previous_generated_token",
            "query_generated_token_index": None if index == 0 else index - 1,
            "predicted_generated_token_index": index,
            "predicted_token_id": token_ids[index],
            "query_length": int(queries[index]),
            "key_length": int(keys[index]),
        }
        for index in range(len(token_ids))
    ]


def _token_character_ranges(decoded_tokens: Sequence[str]) -> tuple[str, list[tuple[int, int]]]:
    ranges: list[tuple[int, int]] = []
    pieces: list[str] = []
    cursor = 0
    for token in decoded_tokens:
        piece = str(token)
        pieces.append(piece)
        ranges.append((cursor, cursor + len(piece)))
        cursor += len(piece)
    return "".join(pieces), ranges


def find_token_intervals(decoded_tokens: Sequence[str], pattern: str, flags: int = re.IGNORECASE) -> list[tuple[int, int]]:
    """Map all nonempty regex matches in reconstructed text to token intervals."""
    text, ranges = _token_character_ranges(decoded_tokens)
    intervals: list[tuple[int, int]] = []
    for match in re.finditer(pattern, text, flags=flags):
        if match.start() == match.end():
            raise ValueError(f"zero-width event pattern is not supported: {pattern}")
        overlapping = [index for index, (start, end) in enumerate(ranges) if end > match.start() and start < match.end()]
        if not overlapping:
            raise ValueError(f"match could not be mapped to tokens: {pattern}")
        intervals.append((overlapping[0], overlapping[-1] + 1))
    return intervals


def find_token_interval(
    decoded_tokens: Sequence[str],
    pattern: str,
    occurrence: int = 0,
    flags: int = re.IGNORECASE,
) -> tuple[int, int]:
    intervals = find_token_intervals(decoded_tokens, pattern, flags=flags)
    if not intervals:
        raise ValueError(f"event pattern not found: {pattern}")
    try:
        return intervals[int(occurrence)]
    except IndexError as exc:
        raise ValueError(f"event pattern occurrence {occurrence} not found: {pattern}") from exc


def event_regions(
    token_count: int,
    e0_interval: tuple[int, int],
    e1_token: int,
    e2_interval: tuple[int, int],
    window: int = 64,
    fact_start: int | None = None,
) -> dict[str, tuple[int, int]]:
    """Define fixed semantic regions around one evidence event.

    If ``fact_start`` is supplied, FACT retains the full annotated fact span
    even when it overlaps the wider E0 entity span. Without it, the historical
    nonoverlapping convention starts FACT at the end of E0.
    """
    total = int(token_count)
    e0_start, e0_end = map(int, e0_interval)
    e2_start, e2_end = map(int, e2_interval)
    e1 = int(e1_token)
    fact = e0_end if fact_start is None else int(fact_start)
    if not (0 <= e0_start < e0_end <= e1 + 1 <= e2_start < e2_end <= total):
        raise ValueError("events must satisfy E0 <= E1 < E2 inside the generated trace")
    if not e0_start <= fact <= e1:
        raise ValueError("fact start must lie between E0 and E1")
    return {
        "PRE": (max(0, e0_start - int(window)), e0_start),
        "ENTITY": (e0_start, e0_end),
        "FACT": (fact, e1 + 1),
        "POST": (e1 + 1, min(e2_start, e1 + 1 + int(window))),
        "USE": (e2_start, e2_end),
    }


def region_means(values: np.ndarray, regions: Mapping[str, tuple[int, int]]) -> dict[str, float | None]:
    curve = np.asarray(values, dtype=np.float64)
    if curve.ndim != 1:
        raise ValueError("region signal must be one-dimensional")
    result: dict[str, float | None] = {}
    for name, (start, end) in regions.items():
        segment = curve[int(start) : int(end)]
        result[name] = float(segment.mean()) if segment.size else None
    return result


def classify_timing(
    means: Mapping[str, float | None],
    repeated_mean: float | None,
    matched_mean: float | None,
    margin: float = 0.10,
) -> str:
    """Assign a conservative descriptive T1-T6 timing category."""
    finite = {name: float(value) for name, value in means.items() if value is not None and np.isfinite(value)}
    if not finite or max(finite.values()) <= 0:
        return "T6_no_clear_temporal_structure"
    peak = max(finite.values())
    floor = min(finite.values())
    if repeated_mean is not None and matched_mean is not None:
        if repeated_mean >= (1 + margin) * max(matched_mean, 1e-12) and repeated_mean >= (1 - margin) * peak:
            return "T4_repeated_mention_locked"
    if floor >= (1 - 3 * margin) * peak:
        return "T5_persistent"

    grouped = {
        "T1_pre_mention_lead": finite.get("PRE", float("-inf")),
        "T2_mention_centered": max(finite.get("ENTITY", float("-inf")), finite.get("FACT", float("-inf"))),
        "T3_post_mention_lag": max(finite.get("POST", float("-inf")), finite.get("USE", float("-inf"))),
    }
    ordered = sorted(grouped.items(), key=lambda item: item[1], reverse=True)
    if len(ordered) > 1 and ordered[0][1] < (1 + margin) * max(ordered[1][1], 1e-12):
        return "T6_no_clear_temporal_structure"
    return ordered[0][0]


def event_window(values: np.ndarray, center: int, radius: int = 64) -> np.ndarray:
    """Return a NaN-padded fixed-width window centered on a token index."""
    curve = np.asarray(values, dtype=np.float64)
    result = np.full((2 * int(radius) + 1,), np.nan, dtype=np.float64)
    source_start = max(0, int(center) - int(radius))
    source_end = min(len(curve), int(center) + int(radius) + 1)
    target_start = source_start - (int(center) - int(radius))
    result[target_start : target_start + source_end - source_start] = curve[source_start:source_end]
    return result


def center_of_mass_offset(values: np.ndarray, center: int, radius: int = 64) -> float | None:
    window = event_window(values, center=center, radius=radius)
    offsets = np.arange(-int(radius), int(radius) + 1, dtype=np.float64)
    weights = np.nan_to_num(window, nan=0.0)
    total = float(weights.sum())
    return float(np.dot(offsets, weights) / total) if total > 0 else None


def classify_window_relation(window: tuple[int, int], event: Mapping[str, Mapping[str, int]]) -> str:
    """Classify a half-open intervention window relative to E0/E1/E2.

    A window fully contained in one temporal interval receives the plan's
    corresponding label. A window crossing boundaries reports every interval
    it overlaps so the temporal ambiguity is not hidden by precedence rules.
    """
    start, end = map(int, window)
    if start >= end:
        raise ValueError("intervention window must be a nonempty half-open interval")
    e0 = int(event["e0"]["start_token"])
    e1_end = int(event["e1"]["completion_token"]) + 1
    e2_start = int(event["e2"]["start_token"])
    e2_end = int(event["e2"]["end_token"])
    if not (e0 < e1_end <= e2_start < e2_end):
        raise ValueError("event must satisfy E0 <= E1 < E2")

    intervals = (
        ("PRE-E0", -float("inf"), e0),
        ("E0-to-E1", e0, e1_end),
        ("POST-E1 before use", e1_end, e2_start),
        ("USE", e2_start, e2_end),
        ("late POST", e2_end, float("inf")),
    )
    labels = [label for label, left, right in intervals if start < right and end > left]
    if len(labels) == 1:
        return labels[0]
    return "spans " + " + ".join(labels)
