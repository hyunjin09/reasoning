#!/usr/bin/env python3
"""Independently validate Stage 2A offline deliverables."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import numpy as np


ROOT = Path("outputs/stage2a")


def load(path: Path):
    return json.loads(path.read_text())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    checks: list[dict] = []

    def check(name: str, condition: bool, detail: str) -> None:
        require(condition, f"{name}: {detail}")
        checks.append({"name": name, "status": "PASS", "detail": detail})

    pairs = [json.loads(line) for line in (ROOT / "paired_analysis/both_correct_pair_manifest.jsonl").read_text().splitlines()]
    check("paired_manifest_count", len(pairs) == 36, f"{len(pairs)} both-correct pairs")
    classes = Counter(row["audit_class"] for row in pairs)
    check(
        "paired_strata",
        classes == {"clear_information_shift": 13, "no_effective_visual_shift": 22, "mixed_redistribution": 1},
        str(dict(classes)),
    )
    paired_stats = load(ROOT / "paired_analysis/paired_statistics.json")
    check("paired_analysis_complete", paired_stats["status"] == "complete", paired_stats["status"])
    check("normalized_progress", paired_stats["normalized_progress"]["bin_count"] == 20, "20 token-progress bins")

    annotations = [json.loads(line) for line in (ROOT / "evidence_subset/evidence_annotations.jsonl").read_text().splitlines()]
    check("evidence_annotation_count", len(annotations) == 20, f"{len(annotations)} accepted examples")
    check("evidence_annotation_unique", len({row["example_id"] for row in annotations}) == 20, "20 unique IDs")
    check("mapping_reviews", all(row["ROI_mapping_validation"]["status"] == "pass" for row in annotations), "20/20 pass")

    pattern_counts = Counter(row["descriptive_pattern"] for row in annotations)
    expected = {"expected_A_to_B_shift": 10, "persistent_B": 6, "no_clear_ROI_selectivity": 3, "persistent_A": 1}
    check("pattern_counts", pattern_counts == expected, str(dict(pattern_counts)))

    required_files = {
        "roi_A.json", "roi_B.json", "roi_mapping.png", "evidence_timeline.png",
        "evidence_curves.npz", "candidate_intervention_windows.json",
    }
    shape_checks = 0
    for row in annotations:
        eid = row["example_id"]
        per_dir = ROOT / "evidence_subset/examples" / eid
        check(f"bundle_{eid}", all((per_dir / name).is_file() for name in required_files), "all six ROI-derived files")
        curves = np.load(per_dir / "evidence_curves.npz")
        token_n = curves["token_A_raw_mass"].shape[0]
        span_n = curves["span_A_raw_mass"].shape[0]
        require(curves["token_B_raw_mass"].shape == (token_n,), f"{eid}: token B shape")
        require(curves["span_B_raw_mass"].shape == (span_n,), f"{eid}: span B shape")
        require(curves["span_ranges"].shape == (span_n, 2), f"{eid}: span range shape")
        require(len(row["evidence_A"]["ROI_visual_token_indices"]) == row["evidence_A"]["ROI_visual_token_count"], f"{eid}: ROI A count")
        require(len(row["evidence_B"]["ROI_visual_token_indices"]) == row["evidence_B"]["ROI_visual_token_count"], f"{eid}: ROI B count")
        shape_checks += 1
    checks.append({"name": "curve_shapes", "status": "PASS", "detail": f"{shape_checks}/20 token/span curve bundles"})

    acceptance = load(ROOT / "summaries/stage2a_acceptance.json")
    check("acceptance_criteria", len(acceptance["criteria"]) == 12 and all(item["status"].startswith("PASS") for item in acceptance["criteria"]), "12/12 pass or pass-with-caveat")
    check("stage2b_boundary", acceptance["stage2b_recommendation"] == "CONDITIONAL GO", "CONDITIONAL GO, no Stage 2B execution")

    required_reports = [
        ROOT / "manual_pair_audit.md",
        ROOT / "paired_analysis/paired_analysis.md",
        ROOT / "evidence_subset/evidence_subset_report.md",
        ROOT / "summaries/stage2a_summary.md",
        ROOT / "summaries/stage2b_recommendation.md",
    ]
    check("required_reports", all(path.stat().st_size > 500 for path in required_reports), "five required Markdown reports are nonempty")

    result = {
        "status": "PASS",
        "check_count": len(checks),
        "checks": checks,
        "no_inference_scope": "validator reads only retained/generated Stage 2A files",
    }
    output = ROOT / "summaries/validation.json"
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "check_count": result["check_count"]}, indent=2))


if __name__ == "__main__":
    main()
