#!/usr/bin/env python3
"""Persist the complete score-blind manual Stage 3B.9 E_d audit."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_json


ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "outputs/stage3b9/evidence_audit"


# Boundary corrections made by reading the complete baseline traces. Indices are
# generated-token indices and the end index is exclusive.
BOUNDARY_OVERRIDES = {
    "649": (6, 73),
    "665": (6, 131),
    "706": (111, 211),
    "758": (6, 606),
    "761": (6, 195),
}


CORRECTION_REASONS = {
    "649": "Prefix is evidence-neutral; E1 extends through the first sentence identifying the 4 cm line as the sphere diameter.",
    "665": "Prefix is evidence-neutral; E1 extends through the first sentence identifying 9 cm as the probable sphere diameter.",
    "706": "E0 moves to the start of the first sentence containing the 16 cm label, before any target-value leakage; E1 closes after the trace relates 16 cm to a prism-side length.",
    "758": "Prefix is evidence-neutral; E1 extends through the first explicit statement that AB is the hypotenuse and equals 6.",
    "761": "Prefix is evidence-neutral; E1 extends through the first explicit statement that side MN equals 4.",
}


def main() -> None:
    source = AUDIT / "ed_audit_decisions_proposed_v2.json"
    target = AUDIT / "ed_audit_decisions_manual.json"
    if target.exists():
        raise FileExistsError(f"Manual decisions already exist: {target}")
    payload = json.loads(source.read_text(encoding="utf-8"))
    decisions = []
    for proposal in payload["decisions"]:
        base = str(proposal["base_problem_id"])
        decision = {
            "base_problem_id": base,
            "decision": proposal["decision"],
            "e0_start_token": proposal["e0_start_token"],
            "e1_completion_token": proposal["e1_completion_token"],
            "pre_e0_discriminative_content_absent": proposal["pre_e0_discriminative_content_absent"],
            "semantic_decision_meaningful": proposal["semantic_decision_meaningful"],
            "reason": proposal["reason"],
            "complete_context_manually_reviewed": True,
        }
        if base in BOUNDARY_OVERRIDES:
            decision["e0_start_token"], decision["e1_completion_token"] = BOUNDARY_OVERRIDES[base]
            decision["reason"] = CORRECTION_REASONS[base]
        elif decision["decision"] == "ACCEPT":
            decision["reason"] = (
                "Complete trace manually reviewed: the frozen prefix ends before target-specific "
                "visual content, and the semantic evidence decision is meaningful."
            )
        else:
            decision["reason"] = (
                "Complete trace manually reviewed: the proposed pyramid-edge target is absent and "
                "does not match the trace's quadrilateral evidence, so no meaningful strict E_d exists."
            )
        decisions.append(decision)
    write_json(
        target,
        {
            "reviewer": "Codex primary agent",
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "causal_scores_inspected": False,
            "attention_used": False,
            "subspace_fit_inspected": False,
            "review_scope": "All complete baseline traces and all proposed E0/E1 contexts for every completed-correct prospective candidate.",
            "boundary_convention": "Generated-token indices; E0 inclusive and E1 exclusive.",
            "decisions": decisions,
        },
    )
    print(json.dumps({
        "reviewed": len(decisions),
        "accepted": sum(row["decision"] == "ACCEPT" for row in decisions),
        "rejected": sum(row["decision"] == "REJECT" for row in decisions),
        "boundary_corrections": sorted(BOUNDARY_OVERRIDES, key=int),
        "output": str(target.relative_to(ROOT)),
    }, indent=2))


if __name__ == "__main__":
    main()
