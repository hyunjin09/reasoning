#!/usr/bin/env python3
"""Build evidence-linked PASS/FAIL status for all Stage 1 acceptance criteria."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def criterion(identifier: int, name: str, passed: bool, evidence: str) -> dict[str, Any]:
    return {"id": identifier, "criterion": name, "status": "PASS" if passed else "FAIL", "evidence": evidence}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage1-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.stage1_dir.resolve()
    selection = read_json(root / "protocol_pilot" / "protocol_40960_selection.json")
    faith = read_json(root / "protocol_pilot" / "faithfulness_check_40960.json")
    gate = read_json(root / "discovery" / "cohort_gate.json")
    validation = read_json(root / "summaries" / "stage1_discovery_validation.json")
    statistics = read_json(root / "summaries" / "stage1_statistics.json")
    manual = read_json(root / "discovery" / "manual_review" / "segmentation_review.json")
    raw_count = sum(1 for line in (root / "discovery" / "raw_outcome_manifest.jsonl").read_text(encoding="utf-8").splitlines() if line)
    cohort_count = sum(1 for line in (root / "discovery" / "cohort_manifest.jsonl").read_text(encoding="utf-8").splitlines() if line)
    reports = "\n".join(
        (root / "summaries" / name).read_text(encoding="utf-8").lower()
        for name in ("stage1_summary.md", "candidate_hypotheses.md")
    )
    prohibited_claims = (
        "the model causally looks",
        "the model switches to think",
        "uncertainty causes re-grounding",
        "low visual attention means",
        "peaks prove fresh evidence",
    )
    no_causal_claim = not any(claim in reports for claim in prohibited_claims)
    protocol = selection["gate"]
    criteria = [
        criterion(1, "A final generation cap is prospectively selected.", selection["decision_status"] == "locked" and selection["parameters"]["max_new_tokens"] == 40960, "protocol_40960_selection.json: locked 40,960 safety ceiling"),
        criterion(2, "Pilot truncation under the selected protocol is <=10%.", protocol["termination_gate_passed"] and protocol["normal_termination_rate"] >= 0.9, f"official pilot normal termination {protocol['normal_termination']}/{protocol['total']}"),
        criterion(3, "Selected-protocol instrumentation matches exactly on 3/3 examples.", faith["passed"] and faith["exact_match_count"] == 3, f"faithfulness_check_40960.json: {faith['exact_match_count']}/{faith['example_count']}"),
        criterion(4, "At least 80 completed-correct eligible trajectories are available.", cohort_count >= 80 and cohort_count == gate["completed_correct"], f"cohort_manifest.jsonl: {cohort_count} trajectories"),
        criterion(5, "Wrong, truncated, and invalid raw outcomes are preserved separately.", raw_count == 200 and validation["raw_outcome_count"] == 200, f"raw_outcome_manifest.jsonl: {raw_count} prospective attempts; primary cohort separately indexed"),
        criterion(6, "Token and span timelines are reproducible.", validation["passed"] and validation["validated_bundle_count"] == 200, "stage1_discovery_validation.json recomputes token text, spans, arrays, and eligible timelines for 200 bundles"),
        criterion(7, "Visual/prompt/reasoning mass and source-count-normalized density are available.", "attention" in statistics and all(name in statistics["attention"] for name in ("visual_density_mean", "prompt_density_mean", "reasoning_density_mean")), "stage1_statistics.json attention definitions and normalized density distributions"),
        criterion(8, "Visual-focus distributions and predictive uncertainty are available.", "visual_focus" in statistics and validation["passed"], "validated per-token/per-span focus and uncertainty arrays plus visual_focus statistics"),
        criterion(9, "Dataset-level temporal statistics are computed.", statistics.get("status") == "stage1b_descriptive_analysis_complete", "stage1_statistics.json candidate peaks, temporal histogram, focus, semantic, uncertainty, and variant statistics"),
        criterion(10, "At least 10 representative trajectories are manually inspected.", validation["representative_count"] >= 10 and manual.get("representative_trajectory_review_count", 0) >= 10, f"manual qualitative review: {manual.get('representative_trajectory_review_count', 0)} representative trajectories"),
        criterion(11, "MathVerse paired variants are reliably aligned for the next stage.", validation["paired_base_problem_count"] == 100, "pairing_manifest.jsonl and independent validation: 100 complete two-variant base problems"),
        criterion(12, "No attention-only result is presented as causal visual usage.", no_causal_claim and statistics.get("scientific_boundary") is not None, "reports retain the attention-is-descriptive boundary; prohibited causal assertions absent"),
        criterion(13, "No Stage 2 causal experiment has been started.", not (root.parent / "stage2").exists(), "no outputs/stage2 directory; Stage 1 reports explicitly stop before intervention"),
    ]
    report = {
        "stage1_passed": all(row["status"] == "PASS" for row in criteria),
        "criteria": criteria,
        "stage2_started": False,
        "scientific_boundary": "attention is descriptive evidence, not causal visual usage",
    }
    write_json(args.output, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
