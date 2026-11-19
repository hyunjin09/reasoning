"""Prospectively frozen multimodal prompt token groups for Stage 3B.0."""

from __future__ import annotations

from typing import Sequence


def find_unique_subsequence(sequence: Sequence[int], subsequence: Sequence[int]) -> tuple[int, int]:
    """Return the half-open bounds of one unique exact token subsequence."""

    values = [int(value) for value in sequence]
    target = [int(value) for value in subsequence]
    if not target:
        raise ValueError("Question token sequence must be nonempty")
    starts = [
        start
        for start in range(len(values) - len(target) + 1)
        if values[start : start + len(target)] == target
    ]
    if len(starts) != 1:
        raise ValueError(f"Question tokens must have one unique prompt match; found {len(starts)}")
    return starts[0], starts[0] + len(target)


def build_token_groups(
    *,
    prompt_token_ids: Sequence[int],
    visual_token_indices: Sequence[int],
    question_token_ids: Sequence[int],
) -> dict[str, list[int]]:
    """Build the frozen causal-order groups used by Stage 3B.0.

    ``Q`` is the exact question-content token span. ``T`` is every prompt
    position strictly after Q. ``P_post_image`` is every nonvisual prompt
    position after the final visual placeholder, including the vision-end
    bridge, Q, and T.
    """

    prompt = [int(value) for value in prompt_token_ids]
    visual = sorted({int(value) for value in visual_token_indices})
    if not prompt or not visual or visual[0] < 0 or visual[-1] >= len(prompt):
        raise ValueError("Visual positions must be nonempty and inside the prompt")
    q_start, q_end = find_unique_subsequence(prompt, question_token_ids)
    if q_start <= visual[-1]:
        raise ValueError("Question token span must occur after the final visual token")
    visual_set = set(visual)
    post_image = [index for index in range(visual[-1] + 1, len(prompt)) if index not in visual_set]
    question = list(range(q_start, q_end))
    trailing = list(range(q_end, len(prompt)))
    if not post_image or not question:
        raise ValueError("Frozen post-image and question groups must be nonempty")
    if not set(question).issubset(post_image):
        raise ValueError("Question positions must be a subset of P_post_image")
    return {
        "V": visual,
        "Q": question,
        "T": trailing,
        "Q_plus_T": [*question, *trailing],
        "P_post_image": post_image,
    }
