from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


FASTV_STATUS = "approximate_fastv_style_static_pruning"


@dataclass(frozen=True)
class EventSelection:
    event_name: str
    event_step: int | None
    fallback_used: bool
    similarity: float | None


def retained_count(num_visual_tokens: int, retention_ratio: float) -> int:
    if num_visual_tokens <= 0:
        return 0
    return max(1, min(num_visual_tokens, round(num_visual_tokens * retention_ratio)))


def select_top_visual_indices(scores: Sequence[float], retention_ratio: float) -> list[int]:
    k = retained_count(len(scores), retention_ratio)
    ranked = sorted(range(len(scores)), key=lambda idx: (-scores[idx], idx))
    return sorted(ranked[:k])


def find_local_minima(values: Sequence[float]) -> list[int]:
    minima: list[int] = []
    for idx in range(1, len(values) - 1):
        if values[idx] <= values[idx - 1] and values[idx] <= values[idx + 1]:
            minima.append(idx)
    return minima


def select_active_shift_event(
    similarities: Sequence[float],
    pre_answer_step: int | None = None,
) -> EventSelection:
    if not similarities:
        return EventSelection("normalized_50_percent_step", None, True, None)

    minima = find_local_minima(similarities)
    if minima:
        idx = minima[0]
        return EventSelection("first_active_attention_shift", idx, False, float(similarities[idx]))

    min_step = min(range(len(similarities)), key=lambda idx: similarities[idx])
    if min_step is not None:
        return EventSelection("minimum_active_similarity_step", min_step, True, float(similarities[min_step]))

    if pre_answer_step is not None:
        value = similarities[pre_answer_step] if 0 <= pre_answer_step < len(similarities) else None
        return EventSelection("pre_answer_selection_step", pre_answer_step, True, value)

    fallback = math.floor((len(similarities) - 1) * 0.5)
    return EventSelection("normalized_50_percent_step", fallback, True, float(similarities[fallback]))
