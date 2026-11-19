"""Pure helpers for Stage 3C.2 source accounting and descriptive analysis."""

from __future__ import annotations

from collections.abc import Sequence


def _indices(values: Sequence[int], *, upper: int) -> list[int]:
    result = sorted({int(value) for value in values})
    if any(value < 0 or value >= upper for value in result):
        raise ValueError("Source position outside the causally visible sequence")
    return result


def build_exclusive_budget_groups(
    *,
    current_position: int,
    prompt_length: int,
    visual_positions: Sequence[int],
    target_positions: Sequence[int],
    mention_positions: Sequence[int],
    irrelevant_positions: Sequence[int],
    question_positions: Sequence[int],
    sink_positions: Sequence[int],
) -> dict[str, list[int]]:
    """Build the mutually exclusive eight-way Stage 3C.2 attention budget."""

    current = int(current_position)
    prompt = int(prompt_length)
    if prompt <= 0 or current < prompt:
        raise ValueError("Current query must follow a nonempty prompt")
    upper = current + 1
    visual = set(_indices(visual_positions, upper=upper))
    target = set(_indices(target_positions, upper=upper))
    mention = set(_indices(mention_positions, upper=upper))
    irrelevant = set(_indices(irrelevant_positions, upper=upper))
    question = set(_indices(question_positions, upper=upper))
    sink = set(_indices(sink_positions, upper=upper))
    if not (target | mention | irrelevant).issubset(visual):
        raise ValueError("T, M, and I must be visual-token subsets")
    declared_roi = [target, mention, irrelevant]
    if any(declared_roi[left] & declared_roi[right] for left in range(3) for right in range(left + 1, 3)):
        raise ValueError("T, M, and I must be mutually disjoint")
    if (question | sink) & visual or question & sink:
        raise ValueError("Visual, question, and sink prompt groups must be disjoint")
    previous = set(range(prompt, current))
    if previous & (visual | question | sink):
        raise ValueError("Prompt groups cannot overlap previous reasoning")
    named = target | mention | irrelevant | question | sink | previous
    other_visual = visual - target - mention - irrelevant
    named |= other_visual
    other = set(range(upper)) - named
    groups = {
        "target_roi": sorted(target),
        "mention_roi": sorted(mention),
        "irrelevant_roi": sorted(irrelevant),
        "other_visual": sorted(other_visual),
        "prompt_question": sorted(question),
        "previous_reasoning": sorted(previous),
        "candidate_sink": sorted(sink),
        "other": sorted(other),
    }
    flattened = [value for values in groups.values() for value in values]
    if len(flattened) != len(set(flattened)) or sorted(flattened) != list(range(upper)):
        raise ValueError("Attention-budget groups are not disjoint and exhaustive")
    return groups


def holm_adjust(p_values: Sequence[float]) -> list[float]:
    """Return Holm step-down adjusted p-values in the original order."""

    count = len(p_values)
    order = sorted(range(count), key=lambda index: float(p_values[index]))
    adjusted = [0.0] * count
    running = 0.0
    for rank, index in enumerate(order):
        candidate = min(1.0, (count - rank) * float(p_values[index]))
        running = max(running, candidate)
        adjusted[index] = running
    return adjusted


def classify_attention_phenotype(early_t_minus_m: float, retrieval_t_minus_m: float) -> str:
    """Classify a descriptive T-vs-M temporal phenotype from signed differences."""

    early = float(early_t_minus_m)
    retrieval = float(retrieval_t_minus_m)
    if early < 0 < retrieval:
        return "alignment_then_retrieval"
    if retrieval > 0:
        return "retrieval_only"
    if retrieval < 0:
        return "alignment_only"
    return "overlap_or_tie"


__all__ = ["build_exclusive_budget_groups", "classify_attention_phenotype", "holm_adjust"]
