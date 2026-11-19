#!/usr/bin/env python3
"""Record the completed manual strict-E_d trace review."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from visual_reasoning.stage0.io import write_json


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b8/discovery_cohort"

# Manual context review found two semantic synonyms earlier than the automated
# search terms: "two people" for observer separation and "airplane" for
# aircraft altitude.  Move E0 to the start of those first referent spans.
E0_OVERRIDES = {"361": 17, "362": 6}
EXPECTED = {
    "303", "309", "312", "314", "319", "322", "324", "325", "332", "334",
    "361", "362", "363", "365", "367", "371", "373", "379", "387", "389",
}


def main() -> None:
    proposed = json.loads((OUT / "ed_audit_decisions_proposed.json").read_text(encoding="utf-8"))
    if {str(row["base_problem_id"]) for row in proposed["decisions"]} != EXPECTED:
        raise RuntimeError("Manual review set does not match the frozen 20-base E_d screen")
    decisions = []
    for row in proposed["decisions"]:
        base = str(row["base_problem_id"])
        item = {
            key: value for key, value in row.items()
            if key not in {"proposal_requires_manual_confirmation", "first_referent_match", "first_evidence_value_match", "audit_context"}
        }
        if base in E0_OVERRIDES:
            item["e0_start_token"] = E0_OVERRIDES[base]
            item["baseline_trace_common_prefix_match_count"] = 0
            item["baseline_trace_common_prefix_exact"] = False
        item["reason"] = (
            "ACCEPT after manual complete-context review: E0 begins the earliest target-referent span "
            "(including synonym review), E1 closes the first explicit target-value span, and y_<E0 "
            "contains neither the edited value nor an explicit target-fact statement."
        )
        item["strict_prefix_evidence_neutral"] = True
        item["complete_context_manually_reviewed"] = True
        decisions.append(item)
    write_json(OUT / "ed_audit_decisions.json", {
        "reviewer": "Codex manual complete-context audit",
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "causal_scores_inspected": False,
        "attention_used": False,
        "subspace_fit_inspected": False,
        "manual_review_count": len(decisions),
        "decisions": decisions,
    })
    print(json.dumps({"reviewed": len(decisions), "accepted": len(decisions), "e0_overrides": E0_OVERRIDES}, indent=2))


if __name__ == "__main__":
    main()
