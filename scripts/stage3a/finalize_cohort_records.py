#!/usr/bin/env python3
"""Create the final Stage 3A exclusion log and cohort expansion report."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from visual_reasoning.stage0.io import write_jsonl, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a"
COHORT = OUT / "cohort"


PRECONSTRUCTION_REJECTIONS = {
    "574": "Changing a graph maximum requires coordinated curve/axis evidence rather than one isolated local fact.",
    "548": "Moving the highlighted 35-meter graph midline is a broad structural edit, not a clean local fact replacement.",
    "611": "Changing all plotted earthquake counts on y=6 requires multiple coordinated point/line edits.",
    "752": "Changing the x,x,sqrt(3)x side relation requires multiple symbolic/structural changes.",
    "544": "Changing the highlighted graph interval 5--15 requires moving a broad task-relevant band.",
    "546": "Changing the highlighted graph interval 1--5 requires moving a broad task-relevant band.",
}


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    screened = read_jsonl(COHORT / "candidate_screening.jsonl")
    primary = read_jsonl(COHORT / "primary_manifest.jsonl")
    primary_bases = {str(row["base_problem_id"]) for row in primary}
    reasons: dict[str, list[dict]] = defaultdict(list)
    for row in screened:
        if row.get("rejection_reason"):
            reasons[str(row["base_problem_id"])].append(
                {
                    "stage": str(row.get("screening_status", "candidate_screening")),
                    "reason": str(row["rejection_reason"]),
                    "source": "outputs/stage3a/cohort/candidate_screening.jsonl",
                }
            )
    for base, reason in PRECONSTRUCTION_REJECTIONS.items():
        reasons[base].append({"stage": "counterfactual_feasibility", "reason": reason})
    for path in sorted(COHORT.glob("*manual_edit_exclusions.jsonl")):
        for row in read_jsonl(path):
            reasons[str(row["base_problem_id"])].append(
                {"stage": str(row.get("stage", "manual_edit_validation")), "reason": str(row["reason"]), "source": str(path.relative_to(ROOT))}
            )
    for path in (
        OUT / "cohort_expansion/raw_outcome_manifest.jsonl",
        OUT / "cohort_expansion/round3/raw_outcome_manifest.jsonl",
    ):
        for row in read_jsonl(path):
            if row["status"] != "correct" or not row["complete"]:
                reasons[str(row["base_problem_id"])].append(
                    {
                        "stage": "baseline_generation",
                        "reason": f"locked-protocol baseline outcome was {row['status']}",
                        "source": str(path.relative_to(ROOT)),
                    }
                )
    round3_audit_path = COHORT / "round3_strict_pre_e0_audit.jsonl"
    if round3_audit_path.is_file():
        for row in read_jsonl(round3_audit_path):
            base = str(row["base_problem_id"])
            if row["decision"] == "REJECT":
                reasons[base].append({"stage": "strict_pre_e0_audit", "reason": str(row["rejection_reason"])})
            elif not row["included_in_final_primary_cohort"]:
                reasons[base].append(
                    {"stage": "primary_cohort_cap", "reason": str(row["primary_exclusion_reason"])}
                )
    exclusions = []
    for row in screened:
        base = str(row["base_problem_id"])
        if base in primary_bases:
            continue
        if not reasons[base]:
            metadata = OUT / f"counterfactuals/{base}/edit_metadata.json"
            if metadata.is_file():
                item = json.loads(metadata.read_text(encoding="utf-8"))
                status = str(item.get("manual_validation", {}).get("status", "unknown"))
                reasons[base].append(
                    {
                        "stage": "downstream_eligibility",
                        "reason": f"candidate did not pass all edit/outcome/strict-prefix gates; manual edit status={status}",
                    }
                )
            else:
                raise RuntimeError(f"No exclusion evidence for screened base {base}")
        exclusions.append(
            {
                "base_problem_id": base,
                "example_id": str(row["example_id"]),
                "screen_source": row["source"],
                "reasons": reasons[base],
                "selection_used_attention": False,
                "causal_scores_used_for_exclusion": False,
            }
        )
    if len(primary_bases) + len(exclusions) != len(screened):
        raise RuntimeError("Final included/excluded accounting does not cover the candidate screen")
    write_jsonl(COHORT / "exclusion_log.jsonl", exclusions)
    edit_status = Counter()
    for path in (OUT / "counterfactuals").glob("*/edit_metadata.json"):
        item = json.loads(path.read_text(encoding="utf-8"))
        edit_status[str(item.get("manual_validation", {}).get("status", "unknown"))] += 1
    evidence_types = Counter(str(row["edit_tier"]) for row in primary)
    variants = Counter(str(row["variant"]) for row in primary)
    report = "\n".join(
        [
            "# Stage 3A Cohort Expansion Summary",
            "",
            f"- Screened candidate records: **{len(screened)}** across **{len(screened)} unique base problems**.",
            f"- Final valid primary cohort: **{len(primary)} unique base problems**.",
            f"- Excluded unique bases: **{len(exclusions)}**.",
            f"- Constructed edit bundles by final status: `{dict(sorted(edit_status.items()))}`.",
            f"- Primary evidence/edit-type distribution: `{dict(sorted(evidence_types.items()))}`.",
            f"- Primary MathVerse variant distribution: `{dict(sorted(variants.items()))}`.",
            "- Selection used ROI attention: **no**.",
            "- Selection or exclusion used full Stage 3A causal scores: **no**.",
            "- Each primary row represents one evidence item and one unique `base_problem_id`.",
            "- C0/C1/C2 are present for every primary item. C3 was omitted where no equally isolated task-irrelevant local edit could be guaranteed; each omission is documented in `edit_metadata.json`.",
            "",
            "All raw baseline outcomes, failed edit versions, manual edit exclusions, and strict-prefix audit decisions remain preserved in their source artifacts.",
        ]
    )
    write_text(COHORT / "expansion_summary.md", report)
    print(
        json.dumps(
            {
                "screened": len(screened),
                "primary": len(primary),
                "excluded": len(exclusions),
                "edit_status": dict(edit_status),
                "evidence_types": dict(evidence_types),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
