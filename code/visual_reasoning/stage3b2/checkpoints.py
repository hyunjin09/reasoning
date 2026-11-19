"""Prospectively defined visual-source switch checkpoints."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any


ED_RELATIVE_OFFSETS = (64, 32, 16, 8, 4, 2, 1)
NORMALIZED_PROGRESS = (0.0, 0.25, 0.50, 0.75, 0.90)


def build_switch_schedule(ed_generated_index: int) -> list[dict[str, Any]]:
    """Map requested E_d coordinates to unique generated-token decision indices."""

    ed = int(ed_generated_index)
    if ed <= 0:
        raise ValueError("E_d must follow reasoning start")
    labels: dict[int, list[str]] = defaultdict(list)
    requested: dict[int, list[dict[str, Any]]] = defaultdict(list)

    labels[0].append("generation_start")
    requested[0].append({"coordinate": "reference", "name": "generation_start"})
    for offset in ED_RELATIVE_OFFSETS:
        index = ed - int(offset)
        if 0 <= index <= ed:
            labels[index].append(f"Ed_minus_{offset}")
            requested[index].append({"coordinate": "ed_relative", "offset": int(offset)})
    for progress in NORMALIZED_PROGRESS:
        index = int(math.floor(float(progress) * ed))
        labels[index].append(f"progress_{int(round(progress * 100))}")
        requested[index].append(
            {"coordinate": "normalized_progress", "requested_progress": float(progress)}
        )
    labels[ed].append("Ed")
    requested[ed].append({"coordinate": "ed_relative", "offset": 0})

    return [
        {
            "switch_generated_index": index,
            "labels": labels[index],
            "requested_coordinates": requested[index],
            "tokens_before_ed": ed - index,
            "actual_progress": index / ed,
            "at_or_before_ed": index <= ed,
        }
        for index in sorted(labels)
    ]
