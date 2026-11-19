"""Compose a per-layer visual K/V source from two captured image sources."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def compose_source_layers(
    default_source_layers: Sequence[tuple[Any, Any]],
    window_source_layers: Sequence[tuple[Any, Any]],
    *,
    selected_layers: Sequence[int],
) -> list[tuple[Any, Any]]:
    """Use ``default`` outside a window and ``window`` inside it."""

    if len(default_source_layers) != len(window_source_layers):
        raise ValueError("Both visual sources must cover the same number of layers")
    selected = {int(value) for value in selected_layers}
    valid = set(range(len(default_source_layers)))
    if not selected.issubset(valid):
        raise ValueError("Selected layer index is outside the captured layer range")
    return [
        window_source_layers[index] if index in selected else default_source_layers[index]
        for index in range(len(default_source_layers))
    ]

