#!/usr/bin/env python3
"""Build conservative strict-E_d span proposals for complete manual review."""

from __future__ import annotations

import json
import re
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"


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
    output = OUT / "evidence_audit/ed_audit_decisions_proposed_v2.json"
    if output.exists():
        raise FileExistsError(f"E_d proposals already exist: {output}")
    drafts = read_jsonl(OUT / "evidence_audit/draft_v2/ed_audit_draft.jsonl")
    pools = [
        *read_jsonl(OUT / "prospective_generation/phase_a_completed_correct_pool.jsonl"),
        *read_jsonl(OUT / "prospective_generation/phase_b_completed_correct_pool.jsonl"),
    ]
    pool_by_base = {str(row["base_problem_id"]): row for row in pools}
    decisions, review = [], ["# Conservative strict-E_d proposals", ""]
    for draft in drafts:
        base = str(draft["base_problem_id"])
        tokens = read_jsonl(ROOT / pool_by_base[base]["artifact_dir"] / "tokens.jsonl")
        text, bounds = offsets(tokens)
        mentions = draft["search_mentions"]
        if not mentions:
            decisions.append(
                {
                    "base_problem_id": base,
                    "decision": "REJECT",
                    "e0_start_token": None,
                    "e1_completion_token": None,
                    "pre_e0_discriminative_content_absent": False,
                    "semantic_decision_meaningful": False,
                    "reason": "No explicit target term or original evidence value was found in the complete baseline trace.",
                    "proposal_requires_manual_confirmation": True,
                    "audit_context": text[:1000].replace("\n", "\\n"),
                }
            )
            review.extend([f"## Base {base}", "", "- Proposal: **REJECT** — no explicit evidence mention", ""])
            continue
        target_terms = {term.lower() for term in str(draft["target"]).split()}
        referents = [row for row in mentions if str(row["term"]).lower() in target_terms]
        values = [row for row in mentions if str(row["term"]) == str(draft["original_value"])]
        if not referents or not values:
            decisions.append(
                {
                    "base_problem_id": base,
                    "decision": "REJECT",
                    "e0_start_token": None,
                    "e1_completion_token": None,
                    "pre_e0_discriminative_content_absent": False,
                    "semantic_decision_meaningful": False,
                    "reason": "The complete trace lacks an explicit target referent or original evidence-value mention.",
                    "proposal_requires_manual_confirmation": True,
                    "audit_context": " | ".join(row["context"] for row in mentions[:8]),
                }
            )
            review.extend([f"## Base {base}", "", "- Proposal: **REJECT** — missing referent/value", ""])
            continue
        first_referent = min(referents, key=lambda row: int(row["token_index"]))
        first_value = min(values, key=lambda row: int(row["token_index"]))
        referent_character = bounds[int(first_referent["token_index"])][0]
        value_character = bounds[int(first_value["token_index"])][0]
        prior = list(re.finditer(r"(?:[.!?](?:\s+|$)|\n+)", text[:referent_character]))
        span_start_character = prior[-1].end() if prior else 0
        following = re.search(r"(?:[.!?](?:\s+|$)|\n+)", text[value_character:])
        span_end_character = value_character + (following.end() if following else len(text) - value_character)
        e0 = token_at(bounds, span_start_character)
        e1 = min(len(tokens), token_at(bounds, max(span_start_character, span_end_character - 1)) + 1)
        context_start = max(0, bounds[e0][0] - 220)
        context_end = min(len(text), bounds[e1 - 1][1] + 320)
        context = text[context_start:context_end].replace("\n", "\\n")
        decision = {
            "base_problem_id": base,
            "decision": "ACCEPT",
            "e0_start_token": e0,
            "e1_completion_token": e1,
            "pre_e0_discriminative_content_absent": True,
            "semantic_decision_meaningful": True,
            "reason": "Conservative first-referent span proposal; requires complete-context manual confirmation.",
            "proposal_requires_manual_confirmation": True,
            "first_referent_match": first_referent,
            "first_evidence_value_match": first_value,
            "audit_context": context,
        }
        decisions.append(decision)
        review.extend(
            [
                f"## Base {base} ({draft['phase']})",
                "",
                f"- Target/value: `{draft['target']}` / `{draft['original_value']}`",
                f"- E0/E1 proposal: `{e0}` / `{e1}`",
                f"- First referent: `{first_referent['matched_text']}` at token `{first_referent['token_index']}`",
                f"- First value: `{first_value['matched_text']}` at token `{first_value['token_index']}`",
                "",
                "```text",
                context,
                "```",
                "",
            ]
        )
    write_json(
        output,
        {
            "reviewer": "pending_manual_review",
            "reviewed_at": None,
            "causal_scores_inspected": False,
            "attention_used": False,
            "subspace_fit_inspected": False,
            "decisions": decisions,
        },
    )
    write_text(OUT / "evidence_audit/ed_audit_proposal_review_v2.md", "\n".join(review))
    print(json.dumps({"proposals": len(decisions), "accept": sum(row["decision"] == "ACCEPT" for row in decisions), "reject": sum(row["decision"] == "REJECT" for row in decisions)}, indent=2))


if __name__ == "__main__":
    main()
