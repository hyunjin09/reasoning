"""Frozen token and lexical-span annotation rules for Stage 3C.8."""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from typing import Any

from visual_reasoning.stage3c8.protocol import classify_lexical_token, normalize_piece


def _is_punctuation(text: str) -> bool:
    stripped = str(text).strip()
    return bool(stripped and re.fullmatch(r"[^\w\s]+", stripped, flags=re.UNICODE))


def group_lexical_spans(*, token_ids: Sequence[int], token_texts: Sequence[str]) -> list[dict[str, Any]]:
    """Group contiguous BPE pieces into lexical spans without semantic outcomes."""

    if len(token_ids) != len(token_texts):
        raise ValueError("Token IDs and decoded pieces must have equal length")
    spans: list[dict[str, Any]] = []
    for position, (token_id, text) in enumerate(zip(token_ids, token_texts)):
        starts_word = bool(str(text)[:1].isspace())
        punctuation = _is_punctuation(text)
        if not spans or starts_word or punctuation or _is_punctuation(spans[-1]["decoded_text"]):
            spans.append({
                "span_id": len(spans),
                "start_position": position,
                "end_position": position + 1,
                "constituent_positions": [position],
                "constituent_token_ids": [int(token_id)],
                "decoded_text": str(text),
            })
        else:
            span = spans[-1]
            span["end_position"] = position + 1
            span["constituent_positions"].append(position)
            span["constituent_token_ids"].append(int(token_id))
            span["decoded_text"] += str(text)
    return spans


def _structural_role(text: str, *, position: int, count: int, stream: str) -> str:
    stripped = text.strip()
    if stream == "PROMPT_QUESTION" and position == 0:
        return "QUESTION_INITIAL"
    if stream == "PROMPT_QUESTION" and position == count - 1:
        return "QUESTION_FINAL"
    if stripped in {".", "!", "?"}:
        return "SENTENCE_FINAL"
    if stripped in {",", ";", ":"}:
        return "CLAUSE_FINAL"
    return "NONE"


def annotate_token_sequence(
    *,
    token_ids: Sequence[int],
    token_texts: Sequence[str],
    stream: str,
    visual_entities: Iterable[str] = (),
    target_entities: Iterable[str] = (),
    mention_entities: Iterable[str] = (),
    absolute_offset: int = 0,
    target_position: int | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Attach the frozen orthogonal taxonomy to one token sequence."""

    if stream not in {"PROMPT_QUESTION", "SPECIAL_CONTROL", "PREVIOUS_REASONING"}:
        raise ValueError(f"Unknown token stream: {stream}")
    spans = group_lexical_spans(token_ids=token_ids, token_texts=token_texts)
    visual = {normalize_piece(value) for value in visual_entities}
    target = {normalize_piece(value) for value in target_entities}
    mention = {normalize_piece(value) for value in mention_entities}
    position_to_span = {
        position: span for span in spans for position in span["constituent_positions"]
    }
    rows = []
    for position, (token_id, text) in enumerate(zip(token_ids, token_texts)):
        normalized = normalize_piece(text)
        lexical = classify_lexical_token(text, visual_entities=visual)
        if normalized in target:
            alignment = "TARGET_ALIGNED"
        elif normalized in mention:
            alignment = "MENTION_ALIGNED"
        elif normalized in visual:
            alignment = "OTHER_VISUAL_ENTITY"
        else:
            alignment = "NO_DIRECT_VISUAL_ALIGNMENT"
        structural = _structural_role(text, position=position, count=len(token_ids), stream=stream)
        if stream != "PREVIOUS_REASONING":
            reasoning_role = None
        elif alignment == "TARGET_ALIGNED":
            reasoning_role = "TARGET_ENTITY_MENTION"
        elif alignment in {"MENTION_ALIGNED", "OTHER_VISUAL_ENTITY"}:
            reasoning_role = "NON_TARGET_ENTITY_MENTION"
        elif lexical == "NUMERIC_LITERAL":
            reasoning_role = "INTERMEDIATE_RESULT"
        elif lexical in {"RELATION_OPERATOR", "MATH_OPERATOR"}:
            reasoning_role = "SUBGOAL_OPERATOR"
        elif lexical == "DISCOURSE_MARKER":
            reasoning_role = "DISCOURSE_TRANSITION"
        elif structural != "NONE" or lexical == "PUNCTUATION":
            reasoning_role = "BOUNDARY"
        else:
            reasoning_role = "OTHER"
        absolute = int(absolute_offset) + position
        rows.append({
            "token_position": position,
            "absolute_sequence_position": absolute,
            "token_id": int(token_id),
            "decoded_text": str(text),
            "lexical_span_id": int(position_to_span[position]["span_id"]),
            "stream": stream,
            "lexical_semantic_class": lexical,
            "visual_alignment": alignment,
            "structural_role": structural,
            "reasoning_role": reasoning_role,
            "distance_to_t_star": None if target_position is None else int(target_position) - absolute,
            "distance_to_t_pre": None if target_position is None else int(target_position) - 1 - absolute,
            "annotation_used_attention": False,
        })
    for span in spans:
        members = [rows[position] for position in span["constituent_positions"]]
        span["stream"] = stream
        span["lexical_semantic_class"] = members[0]["lexical_semantic_class"]
        span["visual_alignment"] = members[0]["visual_alignment"]
        span["structural_role"] = members[-1]["structural_role"]
        span["reasoning_role"] = members[0]["reasoning_role"]
        span["absolute_start_position"] = int(absolute_offset) + int(span["start_position"])
        span["absolute_end_position"] = int(absolute_offset) + int(span["end_position"])
        span["annotation_used_attention"] = False
    return rows, spans
