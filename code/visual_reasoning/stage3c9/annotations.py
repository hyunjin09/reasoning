"""Text-semantic annotation helpers for Stage 3C.9."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from visual_reasoning.stage3c8.fresh import exact_numeric_candidate, numeric_surface_matches


_EVIDENCE_STOPWORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "by", "equal", "equals",
    "figure", "for", "from", "given", "goes", "graph", "has", "have", "if",
    "in", "is", "it", "known", "labeled", "line", "of", "on", "or", "passes",
    "point", "points", "shown", "that", "the", "then", "this", "through", "to",
    "was", "were", "what", "when", "where", "which", "with",
})


def _piece(row: Mapping[str, Any]) -> str:
    return str(row.get("decoded_token", ""))


def _is_boundary(piece: str) -> bool:
    stripped = piece.rstrip()
    return "\n" in piece or bool(stripped) and stripped[-1] in ".!?"


def anchor_span_before_readout(
    tokens: Sequence[Mapping[str, Any]], readout_token: int, *, maximum_positions: int = 8,
) -> tuple[int, int]:
    """Return an anchor ending at least one token before a local-use readout.

    The final prefix token is intentionally left outside the frozen checkpoint
    span.  It is the first downstream query that can consume a rescued span
    state before the evidence-specific candidate at ``readout_token`` is
    scored.
    """

    readout = int(readout_token)
    if readout < 2 or readout >= len(tokens):
        raise ValueError(f"Readout {readout} has no span plus downstream bridge")
    if maximum_positions < 1:
        raise ValueError("maximum_positions must be positive")
    end = readout - 1
    start = max(0, end - int(maximum_positions))
    for index in range(start, end):
        if _is_boundary(_piece(tokens[index])):
            start = index + 1
    if start >= end:
        start = end - 1
    return start, end


def sentence_segments(tokens: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Create lossless sentence/paragraph segment proposals for manual semantic audit."""

    if not tokens:
        return []
    result = []
    start = 0
    for index, row in enumerate(tokens):
        if not _is_boundary(_piece(row)):
            continue
        end = index + 1
        text = "".join(_piece(item) for item in tokens[start:end])
        if text.strip():
            result.append({
                "segment_id": len(result),
                "start_token": start,
                "end_token": end,
                "span_text": text,
                "semantic_label": "PENDING_MANUAL_REVIEW",
            })
        start = end
    if start < len(tokens):
        text = "".join(_piece(item) for item in tokens[start:])
        if text.strip():
            result.append({
                "segment_id": len(result),
                "start_token": start,
                "end_token": len(tokens),
                "span_text": text,
                "semantic_label": "PENDING_MANUAL_REVIEW",
            })
    return result


def candidate_event_gate(
    *, final_readout_token: int, events: Sequence[Mapping[str, Any]], segment_count: int,
) -> dict[str, Any]:
    positions = sorted(int(event["span_start_token"]) for event in events)
    readout_distances = [
        int(event["local_use_readout"]["token_index"]) - int(event["span_end_token"])
        for event in events
    ]
    maximum_separation = positions[-1] - positions[0] if len(positions) >= 2 else 0
    separated = any(right - left >= 24 for index, left in enumerate(positions) for right in positions[index + 1 :])
    early = any(position < 0.75 * int(final_readout_token) for position in positions)
    checks = {
        "long_enough_before_final_readout": int(final_readout_token) >= 160,
        "at_least_three_segments": int(segment_count) >= 3,
        "at_least_three_events": len(events) >= 3,
        "has_two_events_separated_by_at_least_24": separated,
        "has_event_before_final_quarter": early,
        "all_events_support_W8": bool(events) and all(position >= 8 for position in positions),
        "all_local_readouts_1_to_32_after_span": bool(events) and all(
            1 <= distance <= 32 for distance in readout_distances
        ),
    }
    return {
        **checks,
        "final_readout_token": int(final_readout_token),
        "event_count": len(events),
        "segment_count": int(segment_count),
        "maximum_event_separation": maximum_separation,
        "local_readout_distances": readout_distances,
        "eligible_before_edit_roi_validation": all(checks.values()),
    }


def _numeric_variants(value: str) -> set[str]:
    result = {str(value)}
    try:
        number = float(value)
    except ValueError:
        return result
    if number.is_integer():
        result.update({str(int(number)), f"{number:.1f}"})
    return result


def evidence_terms(*, target: str, context: str, original_value: str) -> set[str]:
    """Extract score-blind lexical anchors for one static visual fact."""

    text = f"{target} {context}".replace(str(original_value), " ")
    terms = set()
    for token in re.findall(r"[A-Za-z]+", text):
        normalized = token.lower()
        if normalized in _EVIDENCE_STOPWORDS:
            continue
        if len(normalized) >= 2 or token.isupper():
            terms.add(normalized)
    return terms


def numeric_fact_event_proposals(
    *, tokens: list[dict[str, Any]], original_value: str,
    counterfactual_value: str, tokenizer: Any,
    required_evidence_terms: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Propose text-defined event spans preceding exact numeric evidence uses."""

    full_text = "".join(_piece(row) for row in tokens)
    proposals = []
    seen_readouts: set[int] = set()
    for match in numeric_surface_matches(full_text, _numeric_variants(original_value)):
        try:
            candidate = exact_numeric_candidate(
                tokens=tokens,
                match_start=match.start(),
                match_end=match.end(),
                counterfactual_value=str(counterfactual_value),
                tokenizer=tokenizer,
            )
        except (RuntimeError, ValueError):
            continue
        readout = int(candidate["ed_generated_index"])
        if readout in seen_readouts or readout < 1:
            continue
        seen_readouts.add(readout)
        start, end = anchor_span_before_readout(tokens, readout, maximum_positions=8)
        span_text = "".join(_piece(row) for row in tokens[start:end])
        normalized = span_text.strip().lower()
        local_terms = set(re.findall(r"[a-z]+", normalized))
        if required_evidence_terms is not None and not (required_evidence_terms & local_terms):
            continue
        role = "DISCOURSE_TRANSITION" if any(
            marker in normalized.split() for marker in ("therefore", "thus", "hence", "then", "now")
        ) else "VISUAL_FACT_REFERENCE"
        proposals.append({
            "event_id": len(proposals),
            "span_start_token": start,
            "span_end_token": end,
            "span_text": span_text,
            "event_role": role,
            "evidence_relation": "SAME_TARGET_EVIDENCE",
            "local_use_readout": {
                "token_index": readout,
                **{
                    key: value for key, value in candidate.items()
                    if key not in {"history_before_ed_token_ids", "history_before_ed_text"}
                },
            },
            "selection_used_attention": False,
            "causal_scores_available": False,
        })
    return proposals


def select_matched_neighbor_span(
    *, event_span: tuple[int, int], all_event_spans: Sequence[tuple[int, int]],
    readout_token: int, maximum_start_distance: int = 8,
) -> tuple[int, int] | None:
    """Choose the nearest same-length non-event span, preferring the earlier tie."""

    start, end = (int(value) for value in event_span)
    length = end - start
    if length < 1:
        raise ValueError("Event span must be nonempty")
    excluded = [(int(left), int(right)) for left, right in all_event_spans]
    candidates = []
    for candidate_start in range(max(0, start - maximum_start_distance), start + maximum_start_distance + 1):
        candidate_end = candidate_start + length
        # As with the event span, retain at least one downstream bridge token
        # before the evidence candidate. A control ending at the readout would
        # first become visible at the candidate row, too late to affect the
        # logit that predicts that candidate.
        if candidate_start == start or candidate_end >= int(readout_token):
            continue
        if any(candidate_start < right and left < candidate_end for left, right in excluded):
            continue
        candidates.append((abs(candidate_start - start), 0 if candidate_start < start else 1, candidate_start, candidate_end))
    if not candidates:
        return None
    _, _, candidate_start, candidate_end = min(candidates)
    return candidate_start, candidate_end


def canonical_event_trio(events: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Freeze first, midpoint-nearest, and last events without causal scores."""

    ordered = sorted((dict(row) for row in events), key=lambda row: int(row["span_start_token"]))
    if len(ordered) < 3:
        return []
    first, last = ordered[0], ordered[-1]
    midpoint = (int(first["span_start_token"]) + int(last["span_start_token"])) / 2
    middle = min(
        ordered[1:-1],
        key=lambda row: (abs(int(row["span_start_token"]) - midpoint), int(row["span_start_token"])),
    )
    return [first, middle, last]


def freeze_semantic_review(
    proposal: Mapping[str, Any], review: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and freeze one score-blind manual long-horizon semantic audit."""

    base = str(proposal["base_problem_id"])
    if str(review.get("base_problem_id")) != base:
        raise RuntimeError(f"Manual-review identity mismatch for base {base}")
    if review.get("attention_used") is not False or review.get("causal_scores_available") is not False:
        raise RuntimeError(f"Manual review was not score-blind for base {base}")
    decision = str(review.get("decision", "")).upper()
    common = {
        "base_problem_id": base,
        "example_id": str(proposal["example_id"]),
        "screen_order": int(proposal["screen_order"]),
        "variant": str(proposal.get("variant", "")),
        "source": str(proposal.get("source", "")),
        "source_image": str(proposal.get("source_image", "")),
        "question": str(proposal.get("question", "")),
        "generation_path": str(proposal.get("generation_path", "")),
        "tokens_path": str(proposal.get("tokens_path", "")),
        "generated_token_count": int(proposal.get("generated_token_count", 0)),
        "decision": decision,
        "reason": str(review.get("reason", "")),
        "attention_used": False,
        "causal_scores_available": False,
    }
    if decision == "REJECT":
        return common
    if decision != "ACCEPT":
        raise ValueError(f"Unknown manual decision for base {base}: {decision}")
    required_checks = (
        "trace_is_genuinely_multisegment",
        "trace_is_not_pathological_repetition",
        "event_spans_exact",
        "local_use_readouts_exact",
        "events_semantically_independent",
        "edit_feasible",
        "roi_feasible",
    )
    if not all(review.get(key) is True for key in required_checks):
        raise RuntimeError(f"Manual semantic checks failed for base {base}")
    fact_index = int(review["selected_fact_index"])
    facts = [row for row in proposal["fact_proposals"] if int(row["fact_index"]) == fact_index]
    if len(facts) != 1 or not facts[0].get("eligible_for_manual_review"):
        raise RuntimeError(f"Selected fact is not a unique eligible proposal for base {base}")
    fact = facts[0]
    event_ids = {int(value) for value in review["accepted_event_ids"]}
    canonical_ids = {int(row["event_id"]) for row in canonical_event_trio(fact["events"])}
    if event_ids != canonical_ids:
        raise RuntimeError(f"Reviewed events must equal the frozen first/midpoint/last trio for base {base}")
    events = sorted(
        (dict(row) for row in fact["events"] if int(row["event_id"]) in event_ids),
        key=lambda row: int(row["span_start_token"]),
    )
    if len(events) != len(event_ids) or len(events) < 3 or any(row.get("matched_neighbor_span") is None for row in events):
        raise RuntimeError(f"At least three exact events with neighbors are required for base {base}")
    segment_ids = {int(value) for value in review["reasoning_segment_ids"]}
    segments = sorted(
        (dict(row) for row in proposal["segment_proposals"] if int(row["segment_id"]) in segment_ids),
        key=lambda row: int(row["start_token"]),
    )
    if len(segments) != len(segment_ids) or len(segments) < 3:
        raise RuntimeError(f"At least three exact reasoning segments are required for base {base}")
    final_use = max(events, key=lambda row: int(row["local_use_readout"]["token_index"]))["local_use_readout"]
    gate = candidate_event_gate(
        final_readout_token=int(final_use["token_index"]),
        events=events,
        segment_count=len(segments),
    )
    if not gate["eligible_before_edit_roi_validation"]:
        raise RuntimeError(f"Reviewed event subset fails long-horizon criteria for base {base}")
    return {
        **common,
        "selected_fact_index": fact_index,
        "target_evidence": str(review["target_evidence"]),
        "evidence_type": str(review["evidence_type"]),
        "original_value": str(fact["original_value"]),
        "counterfactual_value": str(fact["counterfactual_value"]),
        "fact_context": str(fact["context"]),
        "events": events,
        "reasoning_segments": segments,
        "final_use_readout": final_use,
        "eligibility_gate": gate,
        "manual_checks": {key: True for key in required_checks},
        "event_spans_frozen_before_causal_scoring": True,
        "local_use_readouts_frozen_before_causal_scoring": True,
    }
