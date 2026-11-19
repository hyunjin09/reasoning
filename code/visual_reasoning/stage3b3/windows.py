"""Prospectively frozen layer windows for Stage 3B.3."""

from __future__ import annotations

from typing import Sequence


LANGUAGE_LAYER_COUNT = 36
COARSE_WIDTH = 6


def coarse_layer_windows() -> list[dict]:
    return [
        {
            "name": f"W{index}",
            "start_layer": start,
            "end_layer": start + COARSE_WIDTH - 1,
            "layers": list(range(start, start + COARSE_WIDTH)),
        }
        for index, start in enumerate(range(0, LANGUAGE_LAYER_COUNT, COARSE_WIDTH))
    ]


def cumulative_layer_windows() -> dict[str, list[dict]]:
    lower = [
        {
            "name": f"lower_0_{end}",
            "family": "lower_prefix",
            "layers": list(range(0, end + 1)),
        }
        for end in (5, 11, 17, 23, 29, 35)
    ]
    upper = [
        {
            "name": f"upper_{start}_35",
            "family": "upper_suffix",
            "layers": list(range(start, 36)),
        }
        for start in (30, 24, 18, 12, 6, 0)
    ]
    return {"lower_prefix": lower, "upper_suffix": upper}


def fine_two_layer_windows(qualifying_coarse_names: Sequence[str]) -> list[dict]:
    if not qualifying_coarse_names:
        return []
    indices = {int(name.removeprefix("W")) for name in qualifying_coarse_names}
    if any(index < 0 or index >= 6 for index in indices):
        raise ValueError("Fine localization received an unknown coarse window")
    eligible = set(indices)
    for index in tuple(indices):
        if index > 0:
            eligible.add(index - 1)
        if index < 5:
            eligible.add(index + 1)
    windows = []
    for parent_index in sorted(eligible):
        parent_start = parent_index * COARSE_WIDTH
        for start in range(parent_start, parent_start + COARSE_WIDTH, 2):
            windows.append(
                {
                    "name": f"F{start}_{start + 1}",
                    "parent_window": f"W{parent_index}",
                    "qualifying_parent": parent_index in indices,
                    "layers": [start, start + 1],
                }
            )
    return windows
