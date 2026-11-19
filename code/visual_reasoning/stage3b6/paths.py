"""Prospectively frozen token source groups for Stage 3B.6."""

from __future__ import annotations

from collections.abc import Sequence


def _positions(values: Sequence[int], *, upper: int, name: str) -> list[int]:
    result = sorted({int(value) for value in values})
    if not result or result[0] < 0 or result[-1] >= upper:
        raise ValueError(f"{name} positions must be nonempty and precede the current token")
    return result


def build_source_token_groups(
    *,
    prompt_length: int,
    current_absolute_position: int,
    visual_positions: Sequence[int],
    eligible_prefix_positions: Sequence[int],
) -> dict[str, list[int]]:
    """Build disjoint V/P/R groups strictly before the current query token.

    ``P`` is the Stage 3B.0-eligible post-image nonvisual prompt group. The
    pre-image prompt is causally before the image and remains recipient-native.
    """

    prompt_length = int(prompt_length)
    current = int(current_absolute_position)
    if prompt_length <= 0 or current < prompt_length:
        raise ValueError("The intervention must occur after a nonempty prompt")
    visual = _positions(visual_positions, upper=prompt_length, name="Visual")
    prefix = _positions(
        eligible_prefix_positions, upper=prompt_length, name="Eligible prefix"
    )
    if set(visual) & set(prefix):
        raise ValueError("V and P source groups must be disjoint")
    reasoning = list(range(prompt_length, current))
    all_positions = sorted({*visual, *prefix, *reasoning})
    if current in all_positions:
        raise RuntimeError("The recipient current token leaked into a source group")
    return {"V": visual, "P": prefix, "R": reasoning, "all": all_positions}


__all__ = ["build_source_token_groups"]

