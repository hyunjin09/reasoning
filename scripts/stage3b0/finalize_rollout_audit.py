#!/usr/bin/env python3
"""Record the manual semantic audit of exact target-number rollout hits."""

from __future__ import annotations

import json
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_jsonl


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "outputs/stage3b0/cutoff/rollout_results.jsonl"
OUTPUT = ROOT / "outputs/stage3b0/cutoff"

# Every automatic target-number hit was manually read in full. True means the
# number was semantically asserted as the edited visual fact, rather than only
# appearing in an answer choice or unrelated calculation.
TRUE_HITS = {
    ("6", "original"),
    ("6", "sham"),
    ("83", "sham"),
    ("98", "original"),
    ("98", "sham"),
    ("103", "original"),
    ("103", "sham"),
    ("136", "counterfactual"),
    ("155", "sham"),
}
FALSE_HIT_REASONS = {
    ("83", "counterfactual"): "120 appeared in the listed answer choices; no central-angle fact was asserted.",
    ("100", "counterfactual"): "30 appeared in the listed answer choices; no COE fact was asserted.",
    ("120", "counterfactual"): "3 appeared as the coefficient in option 3π; no cone-height fact was asserted.",
}


def main() -> None:
    rows = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip()]
    audited = []
    for row in rows:
        key = (str(row["base_problem_id"]), str(row["condition"]))
        automatic = row.get("first_target_numeric_mention")
        if key in TRUE_HITS:
            status = "explicit_target_fact_statement"
            identity = automatic["identity"]
            reason = "Manual reading confirmed that the target entity/relation and target number were asserted together."
        elif key in FALSE_HIT_REASONS:
            status = "lexical_false_positive"
            identity = None
            reason = FALSE_HIT_REASONS[key]
        elif automatic is not None:
            raise RuntimeError(f"Unreviewed automatic hit: {key}")
        elif not row["original_unique_numeric_strings"] and not row["counterfactual_unique_numeric_strings"]:
            status = "non_numeric_structural_not_explicit_within_128_tokens"
            identity = None
            reason = "Manual reading of all 12 structural rollouts found no explicit assertion of either edited graph shape."
        else:
            status = "no_exact_target_fact_statement_within_128_tokens"
            identity = None
            reason = "Neither unique target number occurred in the 128-token continuation."
        audited.append(
            {
                "base_problem_id": row["base_problem_id"],
                "example_id": row["example_id"],
                "condition": row["condition"],
                "status": status,
                "stated_fact_identity": identity,
                "automatic_hit": automatic,
                "manual_reason": reason,
                "original_fact": row["original_fact"],
                "counterfactual_fact": row["counterfactual_fact"],
            }
        )
    write_jsonl(OUTPUT / "rollout_manual_audit.jsonl", audited)
    counts = {
        condition: {
            status: sum(row["condition"] == condition and row["status"] == status for row in audited)
            for status in sorted({row["status"] for row in audited})
        }
        for condition in ("original", "counterfactual", "sham")
    }
    explicit = [row for row in audited if row["status"] == "explicit_target_fact_statement"]
    summary = {
        "row_count": len(audited),
        "automatic_numeric_hits_manually_reviewed": 12,
        "structural_rollouts_manually_reviewed": 12,
        "explicit_target_fact_statement_count": len(explicit),
        "explicit_identity_counts": {
            "original": sum(row["stated_fact_identity"] == "original" for row in explicit),
            "counterfactual": sum(row["stated_fact_identity"] == "counterfactual" for row in explicit),
        },
        "by_condition_and_status": counts,
        "interpretation": "The 128-token cutoff rollouts rarely reached an explicit target fact, so they are an inconclusive secondary behavioral check; primary claims use evidence-specific teacher-forced scores.",
    }
    write_json(OUTPUT / "rollout_audit_summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
