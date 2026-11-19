"""Prospectively defined Stage 3B.1 cutoff checkpoint schedules."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any


E0_RELATIVE_OFFSETS = (128, 64, 32, 16, 8, 4, 1)
NORMALIZED_PROGRESS = (0.0, 0.25, 0.50, 0.75, 0.90)


def build_checkpoint_schedule(e0_start_token: int) -> list[dict[str, Any]]:
    """Map requested coordinates to unique generated-query cutoff indices.

    A cutoff index ``c`` means generated queries ``y_0`` through ``y_(c-1)``
    retain normal visual access and the query at ``y_c`` is the first blocked
    query. Consequently ``c=0`` reproduces the Stage 3B.0 generation-start
    cutoff and every returned index is strictly before E0.
    """

    e0 = int(e0_start_token)
    if e0 <= 0:
        raise ValueError("E0 must follow at least one generated reasoning token")
    labels: dict[int, list[str]] = defaultdict(list)
    requested: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for offset in E0_RELATIVE_OFFSETS:
        index = e0 - int(offset)
        if 0 <= index < e0:
            labels[index].append(f"E0_minus_{offset}")
            requested[index].append({"coordinate": "e0_relative", "offset": int(offset)})
    for progress in NORMALIZED_PROGRESS:
        index = int(math.floor(float(progress) * e0))
        if not 0 <= index < e0:
            raise RuntimeError("Normalized checkpoint escaped the strict pre-E0 interval")
        label = f"progress_{int(round(progress * 100))}"
        labels[index].append(label)
        requested[index].append({"coordinate": "normalized_progress", "requested_progress": progress})
    return [
        {
            "cutoff_generated_index": index,
            "labels": labels[index],
            "requested_coordinates": requested[index],
            "tokens_before_e0": e0 - index,
            "actual_progress": index / e0,
            "strictly_pre_e0": index < e0,
        }
        for index in sorted(labels)
    ]
