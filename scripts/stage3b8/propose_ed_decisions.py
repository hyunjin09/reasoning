#!/usr/bin/env python3
"""Build conservative span proposals for manual Stage 3B.8 E_d review."""

from __future__ import annotations

import json
import re
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b8/discovery_cohort"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def offsets(tokens: list[dict]) -> tuple[str, list[tuple[int, int]]]:
    pieces = [str(row["decoded_token"]) for row in tokens]
    text = "".join(pieces)
    result, cursor = [], 0
    for piece in pieces:
        result.append((cursor, cursor + len(piece)))
        cursor += len(piece)
    return text, result


def token_at(bounds: list[tuple[int, int]], character: int) -> int:
    for index, (start, end) in enumerate(bounds):
        if start <= character < end:
            return index
    return len(bounds) - 1


def main() -> None:
    drafts = read_jsonl(OUT / "ed_audit_draft/discriminative_event_draft.jsonl")
    decisions, review = [], ["# Conservative strict-E_d span proposals", ""]
    for draft in drafts:
        tokens = read_jsonl(ROOT / next(
            row["artifact_dir"] for row in read_jsonl(OUT / "completed_correct_pending_strict_ed.jsonl")
            if str(row["base_problem_id"]) == str(draft["base_problem_id"])
        ) / "tokens.jsonl")
        text, bounds = offsets(tokens)
        matches = draft["search_matches"]
        first_referent = min(matches, key=lambda row: int(row["token_index"]))
        evidence_matches = [row for row in matches if row["term"] == draft["search_terms"][0]]
        if not evidence_matches:
            raise RuntimeError(f"No explicit evidence-value match for base {draft['base_problem_id']}")
        first_evidence = min(evidence_matches, key=lambda row: int(row["token_index"]))
        referent_character = bounds[int(first_referent["token_index"])][0]
        evidence_character = bounds[int(first_evidence["token_index"])][0]
        prior = list(re.finditer(r"(?:[.!?](?:\s+|$)|\n+)", text[:referent_character]))
        span_start_character = prior[-1].end() if prior else 0
        following = re.search(r"(?:[.!?](?:\s+|$)|\n+)", text[evidence_character:])
        span_end_character = evidence_character + (following.end() if following else len(text) - evidence_character)
        e0 = token_at(bounds, span_start_character)
        e1 = min(len(tokens), token_at(bounds, max(span_start_character, span_end_character - 1)) + 1)
        common = [int(value) for value in draft["common_prefix_token_ids"]]
        ids = [int(row["token_id"]) for row in tokens]
        match_count = 0
        for observed, expected in zip(ids[e0:], common):
            if observed != expected:
                break
            match_count += 1
        context_start = max(0, bounds[e0][0] - 220)
        context_end = min(len(text), bounds[e1 - 1][1] + 260)
        context = text[context_start:context_end].replace("\n", "\\n")
        decision = {
            "base_problem_id": str(draft["base_problem_id"]),
            "decision": "ACCEPT",
            "e0_start_token": e0,
            "e1_completion_token": e1,
            "baseline_trace_common_prefix_match_count": match_count,
            "baseline_trace_common_prefix_exact": match_count == len(common),
            "reason": "Maximally strict first-referent span: prefix ends before the earliest matched target entity/value span; the first explicit target-value span completes by E1; no causal score, attention, or fit result was inspected.",
            "proposal_requires_manual_confirmation": True,
            "first_referent_match": first_referent,
            "first_evidence_value_match": first_evidence,
            "audit_context": context,
        }
        decisions.append(decision)
        review.extend([
            f"## Base {draft['base_problem_id']}", "",
            f"- candidate: `{draft['candidate_original']}` vs `{draft['candidate_counterfactual']}`",
            f"- E0/E1 proposal: `{e0}` / `{e1}`",
            f"- first referent: `{first_referent['matched_text']}` at token `{first_referent['token_index']}`",
            f"- first value: `{first_evidence['matched_text']}` at token `{first_evidence['token_index']}`",
            f"- natural/common-lead match: `{match_count}/{len(common)}`",
            "", "```text", context, "```", "",
        ])
    write_json(OUT / "ed_audit_decisions_proposed.json", {
        "reviewer": "pending_manual_review",
        "reviewed_at": None,
        "causal_scores_inspected": False,
        "attention_used": False,
        "subspace_fit_inspected": False,
        "decisions": decisions,
    })
    write_text(OUT / "ed_audit_proposal_review.md", "\n".join(review))
    print(json.dumps({"proposals": len(decisions)}, indent=2))


if __name__ == "__main__":
    main()
