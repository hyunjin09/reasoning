#!/usr/bin/env python3
"""Independently validate completeness and invariants of final Stage 3C.9 artifacts."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"


REQUIRED = (
    "config/stage3c9_config.json", "config/cohort_rules.json", "config/event_taxonomy.json",
    "config/source_windows.json", "config/route_rules.json", "config/primary_family.json",
    "cohort/screening_accounting.json", "cohort/validation_manifest.jsonl",
    "cohort/primary_manifest.jsonl", "cohort/exclusions.jsonl",
    "annotations/reasoning_segments.jsonl", "annotations/events.jsonl",
    "annotations/event_spans.jsonl", "annotations/local_use_readouts.jsonl",
    "annotations/evidence_relation_labels.jsonl", "audit/event_index_audit.json",
    "audit/readout_index_audit.json", "audit/suppression_partition_audit.json",
    "audit/cache_layout.json", "audit/span_patch_selectivity.json",
    "audit/neighbor_patch_selectivity.json", "audit/route_patch_order.json",
    "audit/self_patch_validation.json", "audit/reproducibility.json",
    "audit/mechanical_validation.json", "phase_a_source/w8_source_sensitivity.jsonl",
    "phase_a_source/w16_source_sensitivity.jsonl", "phase_a_source/source_statistics.json",
    "phase_b_checkpoint/event_span_rescue.jsonl", "phase_b_checkpoint/single_token_localization.jsonl",
    "phase_b_checkpoint/neighbor_controls.jsonl", "phase_b_checkpoint/checkpoint_classification.json",
    "phase_c_lifetime/lifetime_readouts.jsonl", "phase_c_lifetime/repeated_checkpoint_classification.json",
    "phase_c_lifetime/same_evidence_reinstatement.jsonl", "phase_d_routes/gate.json",
    "phase_d_routes/route_pair_manifest.jsonl",
    "phase_d_routes/direct_route.jsonl", "phase_d_routes/prior_checkpoint_route.jsonl",
    "phase_d_routes/short_history_route.jsonl", "phase_d_routes/joint_route.jsonl",
    "phase_d_routes/route_classification.json", "phase_e_enrichment/checkpoint_type_enrichment.json",
    "phase_e_enrichment/reasoning_role_enrichment.json", "phase_e_enrichment/matched_enrichment_controls.jsonl",
    "secondary/attention_qk_overlap.json", "secondary/sink_overlap.json",
    "analysis/long_horizon_checkpoint_summary.json", "analysis/repeated_checkpoint_analysis.json",
    "analysis/lifetime_analysis.json", "analysis/route_analysis.json", "analysis/target_heterogeneity.json",
    "analysis/figures/figure_manifest.json", "summaries/stage3c9_summary.md",
    "summaries/stage3c9_acceptance.json", "summaries/next_stage_recommendation.md",
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[Any]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def finite(value: Any) -> bool:
    if isinstance(value, dict):
        return all(finite(item) for item in value.values())
    if isinstance(value, list):
        return all(finite(item) for item in value)
    return not isinstance(value, float) or math.isfinite(value)


def attention_selection_flags(value: Any) -> list[bool]:
    flags = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"selection_used_attention", "attention_used", "mapping_used_attention", "annotation_used_attention"} and isinstance(item, bool):
                flags.append(item)
            flags.extend(attention_selection_flags(item))
    elif isinstance(value, list):
        for item in value:
            flags.extend(attention_selection_flags(item))
    return flags


def result_bases(root: Path) -> set[str]:
    return {str(read_json(path)["base_problem_id"]) for path in root.glob("**/examples/*/result.json")}


def main() -> None:
    missing = [name for name in REQUIRED if not (OUT / name).is_file()]
    primary = read_jsonl(OUT / "cohort/primary_manifest.jsonl")
    validation = read_jsonl(OUT / "cohort/validation_manifest.jsonl")
    primary_bases = {str(row["base_problem_id"]) for row in primary}
    validation_bases = {str(row["base_problem_id"]) for row in validation}
    events = read_jsonl(OUT / "annotations/events.jsonl")
    event_counts = {base: 0 for base in primary_bases | validation_bases}
    for row in events:
        event_counts[str(row["base_problem_id"])] += 1
    checkpoint = read_json(OUT / "phase_b_checkpoint/checkpoint_classification.json")
    repeated = read_json(OUT / "phase_c_lifetime/repeated_checkpoint_classification.json")
    independently_repeated = sum(bool(row["repeated_checkpoint"]) for row in checkpoint["bases"])
    route_gate = read_json(OUT / "phase_d_routes/gate.json")
    route_pair_bases = {
        str(row["base_problem_id"])
        for row in read_jsonl(OUT / "phase_d_routes/route_pair_manifest.jsonl")
    }
    figures = read_json(OUT / "analysis/figures/figure_manifest.json")
    payloads = []
    for name in REQUIRED:
        path = OUT / name
        if not path.is_file() or path.suffix == ".md":
            continue
        payloads.extend(read_jsonl(path) if path.suffix == ".jsonl" else [read_json(path)])
    checks = {
        "required_artifacts_present": not missing,
        "primary_N_at_least_40": len(primary_bases) >= 40 and len(primary_bases) == len(primary),
        "validation_N_exactly_8": len(validation_bases) == len(validation) == 8,
        "cohorts_disjoint": not primary_bases & validation_bases,
        "exactly_three_frozen_events_per_retained_base": bool(event_counts) and all(count == 3 for count in event_counts.values()),
        "primary_source_results_complete": result_bases(OUT / "phase_a_source/raw") == primary_bases,
        "primary_checkpoint_results_complete": result_bases(OUT / "phase_b_checkpoint/raw") == primary_bases,
        "primary_lifetime_results_complete": result_bases(OUT / "phase_c_lifetime/raw") == primary_bases,
        "mechanical_validation_16_of_16": read_json(OUT / "audit/mechanical_validation.json")["passed_count"] == 16 and read_json(OUT / "audit/mechanical_validation.json")["passed"],
        "repeated_count_independently_matches": int(repeated["repeated_checkpoint_count"]) == independently_repeated,
        "phase_d_gate_obeyed": (
            (route_gate["run_phase_d"] and result_bases(OUT / "phase_d_routes/raw") == route_pair_bases and len(route_pair_bases) >= 16)
            or (not route_gate["run_phase_d"] and not result_bases(OUT / "phase_d_routes/raw"))
        ),
        "all_json_numeric_values_finite": all(finite(value) for value in payloads),
        "no_true_attention_selection_flag": not any(flag for value in payloads for flag in attention_selection_flags(value)),
        "required_figures_present": len(figures["figures"]) >= (15 if figures["route_figures_required"] else 13) and all((OUT / "analysis/figures" / name).is_file() for name in figures["figures"]),
        "acceptance_20_of_20": read_json(OUT / "summaries/stage3c9_acceptance.json")["passed_count"] == 20,
        "exactly_one_recommendation": read_json(OUT / "summaries/stage3c9_acceptance.json")["recommendation_count"] == 1,
    }
    result = {
        "checks": checks,
        "passed_count": sum(checks.values()),
        "total_checks": len(checks),
        "passed": all(checks.values()),
        "missing": missing,
        "primary_N": len(primary_bases),
        "validation_N": len(validation_bases),
        "repeated_checkpoint_count": independently_repeated,
    }
    write_json(OUT / "audit/artifact_validation.json", result)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
