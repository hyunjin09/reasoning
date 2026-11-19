"""Outcome-independent helpers for fresh visual-evidence screening."""

from __future__ import annotations

import re
import hashlib
import json
from typing import Any


NUMBER = re.compile(r"(?<![A-Za-z0-9_.])[+-]?\d+(?:\.\d+)?(?![A-Za-z0-9_]|\.\d)")
EDIT_OVERRIDE_FIELDS = {
    "renderer",
    "roi_xyxy",
    "font_size",
    "text_anchor",
    "counterfactual_sham_anchor_delta",
}


def apply_edit_spec_overrides(
    specs: list[dict[str, Any]], overrides: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Apply manually audited, pre-score construction-only overrides."""

    order = [str(row["base_problem_id"]) for row in specs]
    if len(order) != len(set(order)):
        raise RuntimeError("Edit specifications contain duplicate bases")
    by_base = {str(row["base_problem_id"]): dict(row) for row in specs}
    seen: set[str] = set()
    for override in overrides:
        base = str(override["base_problem_id"])
        if base in seen:
            raise RuntimeError(f"Duplicate edit override for base {base}")
        seen.add(base)
        if base not in by_base:
            raise RuntimeError(f"Edit override has no source specification for base {base}")
        if override.get("attention_used") is not False or override.get("carrier_scores_available") is not False:
            raise RuntimeError(f"Edit override was not score-blind for base {base}")
        changes = dict(override.get("changes", {}))
        unknown = set(changes) - EDIT_OVERRIDE_FIELDS
        if unknown:
            raise RuntimeError(f"Edit override changes non-construction fields for base {base}: {sorted(unknown)}")
        if not changes:
            raise RuntimeError(f"Edit override is empty for base {base}")
        reason = str(override.get("reason", "")).strip()
        if not reason:
            raise RuntimeError(f"Edit override lacks an audit reason for base {base}")
        by_base[base].update(changes)
        by_base[base]["edit_override_audit"] = {
            "reason": reason,
            "attention_used": False,
            "carrier_scores_available": False,
        }
    return [by_base[base] for base in order]


def validate_frozen_screen_prefix(
    *,
    screen: list[dict[str, Any]],
    raw: list[dict[str, Any]],
    candidate_audit: list[dict[str, Any]],
    reviewed_edits: list[dict[str, Any]],
    retained: list[dict[str, Any]],
) -> dict[str, int]:
    """Prove that retained cases come from a fully resolved screen prefix."""

    if not retained:
        raise RuntimeError("Cannot validate an empty retained cohort")
    screen_order = {str(row["base_problem_id"]): int(row["order"]) for row in screen}
    if len(screen_order) != len(screen):
        raise RuntimeError("Prospective screen contains duplicate bases")
    retained_bases = {str(row["base_problem_id"]) for row in retained}
    if not retained_bases.issubset(screen_order):
        raise RuntimeError("Retained cohort contains a base outside the prospective screen")
    cutoff = max(screen_order[base] for base in retained_bases)
    prefix = {base for base, order in screen_order.items() if order <= cutoff}
    raw_by_base = {str(row["base_problem_id"]): row for row in raw}
    missing_outcomes = sorted(prefix - set(raw_by_base), key=int)
    if missing_outcomes:
        raise RuntimeError(f"Frozen cohort has unattempted earlier bases: {missing_outcomes}")
    correct = {base for base in prefix if str(raw_by_base[base]["status"]) == "correct"}
    audited = {str(row["base_problem_id"]): row for row in candidate_audit}
    missing_audits = sorted(correct - set(audited), key=int)
    if missing_audits:
        raise RuntimeError(f"Frozen cohort has unaudited earlier correct bases: {missing_audits}")
    semantic_accepts = {
        base for base in correct if str(audited[base].get("decision", "")).upper() == "ACCEPT"
    }
    edit_reviewed = {str(row["base_problem_id"]) for row in reviewed_edits}
    missing_edit_reviews = sorted(semantic_accepts - edit_reviewed, key=int)
    if missing_edit_reviews:
        raise RuntimeError(f"Frozen cohort has unreviewed earlier edits: {missing_edit_reviews}")
    return {"cutoff_screen_order": cutoff, "prefix_size": len(prefix)}


def _surface_number(value: str) -> str:
    number = float(value)
    return str(int(number)) if number.is_integer() else f"{number:g}"


def numeric_surface_matches(text: str, surfaces: set[str]) -> list[re.Match[str]]:
    """Find standalone numeric surfaces without rejecting sentence punctuation.

    A period following a number is punctuation unless it begins a decimal
    continuation.  The prospective-screen proposal code previously treated
    every following period as part of a number and could therefore skip an
    earlier sentence-final mention such as ``AC = 6.``.
    """

    matches: list[re.Match[str]] = []
    for surface in sorted(surfaces, key=len, reverse=True):
        matches.extend(
            re.finditer(
                rf"(?<![A-Za-z0-9_.]){re.escape(surface)}(?![A-Za-z0-9_]|\.\d)",
                text,
            )
        )
    return matches


def propose_counterfactual_numeric_value(value: str, context: str) -> str:
    """Choose the frozen lightweight numeric perturbation by semantic type."""

    number = float(value)
    is_angle = bool(
        re.search(r"\b(?:angle|rotate|rotating|rotation|rotated)\b", context, flags=re.IGNORECASE)
    ) or "°" in context
    if is_angle:
        changed = number + 10 if number <= 160 else number - 10
    else:
        changed = number + max(2.0, round(abs(number) * 0.5))
    return str(int(changed)) if changed.is_integer() else f"{changed:g}"


def _stem(question: str) -> str:
    return re.split(r"\n\s*Choices\s*:", str(question), maxsplit=1, flags=re.IGNORECASE)[0]


def infer_missing_numeric_facts(text_dominant_question: str, vision_dominant_question: str) -> list[dict[str, str]]:
    """Return numeric facts explicit in Text Dominant but absent from Vision Dominant."""

    text = _stem(text_dominant_question)
    vision = _stem(vision_dominant_question)
    vision_values = {match.group(0) for match in NUMBER.finditer(vision)}
    rows = []
    seen: set[str] = set()
    for match in NUMBER.finditer(text):
        value = match.group(0)
        if value in vision_values or value in seen:
            continue
        seen.add(value)
        clause_start = max(text.rfind(",", 0, match.start()), text.rfind(";", 0, match.start()), text.rfind(".", 0, match.start())) + 1
        clause_end_candidates = [position for position in (text.find(",", match.end()), text.find(";", match.end()), text.find(".", match.end())) if position >= 0]
        clause_end = min(clause_end_candidates) if clause_end_candidates else len(text)
        context = text[clause_start:clause_end].strip()
        prefix = text[max(clause_start, match.start() - 48):match.start()]
        target_match = re.search(
            r"((?:angle|length|radius|diameter|side|arc|segment|line|height|width|area)?\s*[A-Z]{1,4}(?:\s*[A-Z]{1,4})?)\s*(?:=|is(?:\s+equal\s+to)?|are|of)\s*$",
            prefix,
            flags=re.IGNORECASE,
        )
        target = target_match.group(1).strip() if target_match else prefix.strip(" ,;:=")[-40:].strip()
        rows.append({"original_value": value, "target": target, "context": context})
    return rows


def exact_numeric_candidate(
    *,
    tokens: list[dict[str, Any]],
    match_start: int,
    match_end: int,
    counterfactual_value: str,
    tokenizer: Any,
) -> dict[str, Any]:
    """Build a numeric candidate pair at exact generated-token boundaries."""

    if not tokens or not 0 <= int(match_start) < int(match_end):
        raise ValueError("Numeric match must be a nonempty range in a token sequence")
    pieces = [str(row["decoded_token"]) for row in tokens]
    bounds: list[tuple[int, int]] = []
    cursor = 0
    for piece in pieces:
        bounds.append((cursor, cursor + len(piece)))
        cursor += len(piece)
    if int(match_end) > cursor:
        raise ValueError("Numeric match lies outside decoded generated text")

    start_token = next((index for index, (start, end) in enumerate(bounds) if start <= int(match_start) < end), None)
    end_token = next((index for index, (start, end) in enumerate(bounds) if start < int(match_end) <= end), None)
    if start_token is None or end_token is None:
        raise ValueError("Numeric match could not be aligned to generated tokens")
    piece_start = bounds[start_token][0]
    piece_end = bounds[end_token][1]
    full_text = "".join(pieces)
    original_piece_text = full_text[piece_start:piece_end]
    counterfactual_piece_text = (
        full_text[piece_start:int(match_start)]
        + str(counterfactual_value)
        + full_text[int(match_end):piece_end]
    )
    original_ids = [int(row["token_id"]) for row in tokens[start_token:end_token + 1]]
    counterfactual_ids = [int(value) for value in tokenizer.encode(counterfactual_piece_text, add_special_tokens=False)]
    decoded_original = tokenizer.decode(
        original_ids, skip_special_tokens=False, clean_up_tokenization_spaces=False
    )
    if decoded_original != original_piece_text:
        raise RuntimeError("Generated candidate IDs do not decode to their exact token-boundary text")
    if not counterfactual_ids or original_ids == counterfactual_ids:
        raise RuntimeError("Counterfactual candidate must be nonempty and differ from the generated candidate")
    history_ids = [int(row["token_id"]) for row in tokens[:start_token]]
    history_payload = json.dumps(history_ids, separators=(",", ":")).encode("ascii")
    return {
        "ed_generated_index": start_token,
        "history_before_ed_token_ids": history_ids,
        "history_before_ed_text": full_text[:piece_start],
        "history_before_ed_sha256": hashlib.sha256(history_payload).hexdigest(),
        "original_divergent_suffix_ids": original_ids,
        "counterfactual_divergent_suffix_ids": counterfactual_ids,
        "original_divergent_suffix_text": original_piece_text,
        "counterfactual_divergent_suffix_text": tokenizer.decode(
            counterfactual_ids, skip_special_tokens=False, clean_up_tokenization_spaces=False
        ),
        "original_candidate_exact_generated_tokens": True,
        "prefix_ends_at_token_boundary": True,
    }


def materialize_manual_candidate(
    proposal: dict[str, Any], review: dict[str, Any]
) -> dict[str, Any]:
    """Validate one score-blind manual screen and materialize its frozen inputs."""

    base = str(proposal["base_problem_id"])
    if str(review["base_problem_id"]) != base:
        raise RuntimeError(f"Manual-review identity mismatch for base {base}")
    if review.get("attention_used") is not False or review.get("carrier_scores_available") is not False:
        raise RuntimeError(f"Manual review was not score-blind for base {base}")
    decision = str(review["decision"]).upper()
    common = {
        "base_problem_id": base,
        "example_id": str(proposal["example_id"]),
        "screen_order": int(proposal["screen_order"]),
        "decision": decision,
        "reason": str(review.get("reason", "")),
        "attention_used": False,
        "carrier_scores_available": False,
    }
    if decision == "REJECT":
        return common
    if decision != "ACCEPT":
        raise ValueError(f"Unknown manual decision for base {base}: {decision}")
    fact_index = int(review["selected_fact_index"])
    matches = [
        row for row in proposal["numeric_fact_proposals"]
        if int(row.get("fact_index", -1)) == fact_index
    ]
    if len(matches) != 1:
        raise RuntimeError(f"Selected fact {fact_index} is not unique for base {base}")
    fact = matches[0]
    if fact.get("proposal_status") != "manual_review_required":
        raise RuntimeError(f"Selected fact is not trace-aligned for base {base}")
    if not fact.get("original_candidate_exact_generated_tokens") or not fact.get("prefix_ends_at_token_boundary"):
        raise RuntimeError(f"Selected fact is not exact-token aligned for base {base}")
    if not review.get("semantic_decision_meaningful") or not review.get("pre_ed_discriminative_content_absent"):
        raise RuntimeError(f"Manual semantic audit failed for base {base}")
    target = str(review["target_evidence"])
    original = _surface_number(str(fact["original_value"]))
    counterfactual = _surface_number(str(fact["counterfactual_value"]))
    event_keys = (
        "history_before_ed_token_ids",
        "history_before_ed_text",
        "history_before_ed_sha256",
        "original_divergent_suffix_ids",
        "counterfactual_divergent_suffix_ids",
        "original_divergent_suffix_text",
        "counterfactual_divergent_suffix_text",
        "original_candidate_exact_generated_tokens",
        "prefix_ends_at_token_boundary",
    )
    event = {
        "ed_generated_index": int(fact["ed_generated_index_proposed"]),
        **{key: fact[key] for key in event_keys},
        "original_fact": f"{target} = {original}",
        "counterfactual_fact": f"{target} = {counterfactual}",
        "manual_audit_status": "pass",
        "semantic_decision_meaningful": True,
        "pre_ed_discriminative_content_absent": True,
        "audit_reason": str(review.get("reason", "")),
        "attention_used": False,
        "carrier_scores_available": False,
    }
    edit_spec = {
        "base_problem_id": base,
        "example_id": str(proposal["example_id"]),
        "original_value": original,
        "counterfactual_value": counterfactual,
        "roi_xyxy": [int(value) for value in review["roi_xyxy"]],
        "font_size": int(review["font_size"]),
        "text_anchor": [int(value) for value in review.get("text_anchor", [3, 2])],
        "counterfactual_sham_anchor_delta": [
            int(value) for value in review.get("counterfactual_sham_anchor_delta", [1, 0])
        ],
        "render_suffix": str(review.get("render_suffix", "")),
        "renderer": str(review.get("renderer", "rectangle")),
        "target_evidence": target,
        "evidence_type": str(review["evidence_type"]),
        "selection_used_attention": False,
        "carrier_scores_available": False,
    }
    return {
        **common,
        "selected_fact_index": fact_index,
        "target_evidence": target,
        "evidence_type": str(review["evidence_type"]),
        "event": event,
        "edit_spec": edit_spec,
    }


__all__ = [
    "apply_edit_spec_overrides",
    "exact_numeric_candidate",
    "infer_missing_numeric_facts",
    "materialize_manual_candidate",
    "numeric_surface_matches",
    "propose_counterfactual_numeric_value",
    "validate_frozen_screen_prefix",
]
