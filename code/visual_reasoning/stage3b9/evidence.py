"""Score-blind evidence-candidate and boundary-audit helpers for Stage 3B.9."""

from __future__ import annotations

import re


def build_candidate_text(target: str, value: str, suffix: str) -> str:
    """Build the frozen evidence statement used to locate the numeric decision."""
    clean_target = " ".join(str(target).strip().split())
    clean_value = str(value).strip()
    clean_suffix = str(suffix).strip()
    tail = f" {clean_suffix}" if clean_suffix else ""
    return f" the {clean_target} is {clean_value}{tail}"


def find_evidence_mentions(text: str, *, target: str, original_value: str) -> list[dict]:
    """Return exact score-blind target/value mentions for a manual E_d audit."""
    terms: list[str] = []
    for term in [*str(target).split(), str(original_value)]:
        term = term.strip()
        if term and term.lower() not in {value.lower() for value in terms}:
            terms.append(term)
    rows = []
    for term in terms:
        pattern = re.escape(term)
        if term.replace(".", "").isdigit():
            pattern = rf"(?<![\d.]){pattern}(?!\d|\.\d)"
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            rows.append({
                "term": term,
                "matched_text": match.group(0),
                "character_start": match.start(),
                "character_end": match.end(),
            })
    return sorted(rows, key=lambda row: (row["character_start"], terms.index(row["term"])))


__all__ = ["build_candidate_text", "find_evidence_mentions"]
