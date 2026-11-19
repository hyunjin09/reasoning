#!/usr/bin/env python3
"""Independently validate the frozen Stage 3C.2 deliverable tree."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c2"


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    required = [
        "config/stage3c2_config.json", "config/frozen_targets.json", "config/primary_contrasts.json",
        "config/temporal_grid.json", "config/sink_definitions.json", "cohort/candidate_manifest.jsonl",
        "cohort/primary_dissociation_manifest.jsonl", "cohort/exclusions.jsonl",
        "annotations/mention_roi_annotations.jsonl", "annotations/required_roi_annotations.jsonl",
        "annotations/irrelevant_roi_annotations.jsonl", "annotations/semantic_state_labels.jsonl",
        "annotations/state_pair_annotations.jsonl", "audit/token_roi_layout_audit.json",
        "audit/source_partition_audit.json", "audit/attention_reconstruction_audit.json",
        "audit/sink_definition_audit.json", "audit/measurement_reproducibility.json",
        "measurements/per_head_time_condition.jsonl", "measurements/source_mass_results.jsonl",
        "measurements/qk_results.jsonl", "measurements/value_contribution_results.jsonl",
        "measurements/sink_results.jsonl", "analysis/mention_vs_required_statistics.json",
        "analysis/temporal_crossover_statistics.json", "analysis/qk_sharpening_statistics.json",
        "analysis/attention_budget_statistics.json", "analysis/sink_dynamics_statistics.json",
        "analysis/entropy_statistics.json", "analysis/causal_vs_noncausal_head_comparison.json",
        "analysis/head_heterogeneity.json", "analysis/condition_controls.json",
        "summaries/stage3c2_summary.md", "summaries/stage3c2_acceptance.json",
        "summaries/next_stage_recommendation.md",
    ]
    checks = []
    checks.append({"name": "required_files", "passed": all((OUT / path).is_file() for path in required), "missing": [path for path in required if not (OUT / path).is_file()]})
    manifest = rows(OUT / "cohort/primary_dissociation_manifest.jsonl")
    base_ids = [row["base_problem_id"] for row in manifest]
    checks.append({"name": "cohort_size_and_unique", "passed": 24 <= len(base_ids) <= 36 and len(base_ids) == len(set(base_ids)), "observed": len(base_ids)})
    mention = rows(OUT / "annotations/mention_roi_annotations.jsonl")
    checks.append({"name": "M_T_I_disjoint_and_attention_blind", "passed": len(mention) == len(base_ids) and all(row["M_not_equal_T"] and row["M_disjoint_I"] and not row["annotation_used_attention"] for row in mention)})
    states = rows(OUT / "annotations/semantic_state_labels.jsonl")
    checks.append({"name": "state_grid_complete", "passed": len(states) == len(base_ids) * 2 * 6 and all(not row["annotation_used_attention"] for row in states), "observed": len(states)})
    head = rows(OUT / "measurements/per_head_time_condition.jsonl")
    expected_head = len(base_ids) * 4 * 2 * 6 * 8
    conditions = {row["condition"] for row in head}; targets = {row["target_id"] for row in head}
    checks.append({"name": "per_head_measurement_cardinality", "passed": len(head) == expected_head and conditions == {"O", "O_sham", "C", "C_sham"} and targets == {"target_a", "target_b"}, "observed": len(head), "expected": expected_head})
    checks.append({"name": "passive_only", "passed": all(not row["attention_manipulated"] for row in head)})
    source = json.loads((OUT / "audit/source_partition_audit.json").read_text())
    recon = json.loads((OUT / "audit/attention_reconstruction_audit.json").read_text())
    repeat = json.loads((OUT / "audit/measurement_reproducibility.json").read_text())
    checks.append({"name": "source_closure", "passed": source["passed"] and source["maximum_source_mass_absolute_error"] <= source["tolerance"]})
    checks.append({"name": "reconstruction", "passed": recon["exact"] and recon["all_values_finite"]})
    checks.append({"name": "smoke_reproducibility", "passed": repeat["all_passed"] and len(repeat["smoke_bases"]) == 2})
    figures = sorted((OUT / "analysis/figures").glob("*.png"))
    checks.append({"name": "required_figures", "passed": len(figures) == 14 and all(path.stat().st_size > 10_000 for path in figures), "observed": len(figures)})
    acceptance = json.loads((OUT / "summaries/stage3c2_acceptance.json").read_text())
    checks.append({"name": "acceptance", "passed": acceptance["overall"] == "PASS" and acceptance["passed"] == acceptance["total"] == 20})
    recommendation = (OUT / "summaries/next_stage_recommendation.md").read_text()
    checks.append({"name": "single_review_only_recommendation", "passed": recommendation.count("## GO —") == 1 and "did not execute" in recommendation})
    hashes = {path: hashlib.sha256((OUT / path).read_bytes()).hexdigest() for path in required}
    validation = {"passed": all(check["passed"] for check in checks), "checks": checks, "required_file_sha256": hashes, "artifact_bundles": len(list((OUT / "extraction").glob("shard_*/examples/*/result.json"))), "raw_tensor_files": len(list((OUT / "extraction/raw_tensors").glob("*/*.npz")))}
    path = OUT / "audit/independent_validation.json"
    path.write_text(json.dumps(validation, indent=2) + "\n")
    print(json.dumps({"passed": validation["passed"], "checks": len(checks), "bundles": validation["artifact_bundles"], "raw_tensors": validation["raw_tensor_files"]}, indent=2))
    if not validation["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
