#!/usr/bin/env python3
"""Independently validate the complete Stage 3C.8 artifact tree."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c8"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def result_ids(root: Path) -> set[str]:
    return {
        str(read_json(path)["base_problem_id"])
        for path in root.glob("**/examples/*/result.json")
    }


def finite(value: Any) -> bool:
    if isinstance(value, bool) or value is None or isinstance(value, (str, int)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(finite(item) for item in value)
    if isinstance(value, dict):
        return all(finite(item) for item in value.values())
    return False


def main() -> None:
    historical = {str(row["base_problem_id"]) for row in read_jsonl(OUT / "cohort/historical_anchor_manifest.jsonl")}
    fresh_rows = read_jsonl(OUT / "cohort/fresh_atlas_manifest.jsonl")
    fresh = {str(row["base_problem_id"]) for row in fresh_rows}
    validation = {str(row["base_problem_id"]) for row in read_jsonl(OUT / "cohort/validation_manifest.jsonl")}
    accounting = read_json(OUT / "cohort/sample_accounting.json")
    mechanics = read_json(OUT / "audit/mechanical_validation.json")
    replication = read_json(OUT / "analysis/historical_vs_fresh_replication.json")
    phase_c_gate = read_json(OUT / "config/phase_c_kv_gate.json")
    phase_d_cohort = read_json(OUT / "phase_d_anchor/cohort_gate.json")
    acceptance = read_json(OUT / "summaries/stage3c8_acceptance.json")

    required = [
        "config/stage3c8_config.json", "config/cohort_plan.json", "config/token_taxonomy.json",
        "config/span_rules.json", "config/primary_family.json", "config/phase_c_kv_gate.json",
        "cohort/validation_manifest.jsonl", "cohort/historical_anchor_manifest.jsonl",
        "cohort/fresh_atlas_manifest.jsonl", "cohort/exclusions.jsonl", "cohort/sample_accounting.json",
        "annotations/per_token_annotations.jsonl", "annotations/lexical_spans.jsonl",
        "annotations/visual_alignment_annotations.jsonl", "annotations/reasoning_role_annotations.jsonl",
        "audit/tokenizer_span_audit.json", "audit/cache_layout.json", "audit/position_patch_selectivity.json",
        "audit/group_patch_selectivity.json", "audit/visual_cache_invariance.json",
        "audit/phase_b_t16_validation.json", "audit/phase_c_cutoff_validation.json",
        "audit/self_patch_validation.json", "audit/reproducibility.json", "audit/mechanical_validation.json",
        "phase_a_tpre/per_base_tpre_rescue.jsonl", "phase_a_tpre/k_only_results.jsonl",
        "phase_a_tpre/v_only_results.jsonl", "phase_a_tpre/kv_results.jsonl",
        "phase_a_tpre/token_type_statistics.json",
        "phase_b_recent/all_recent_cache_reference.jsonl", "phase_b_recent/per_position_rescue.jsonl",
        "phase_b_recent/fixed_position_kv_decomposition.jsonl", "phase_b_recent/span_rescue.jsonl",
        "phase_b_recent/type_group_rescue.jsonl", "phase_b_recent/recency_matched_controls.jsonl",
        "phase_c_prompt/full_q_reference.jsonl", "phase_c_prompt/per_prompt_position_rescue.jsonl",
        "phase_c_prompt/prompt_span_rescue.jsonl", "phase_c_prompt/prompt_type_group_rescue.jsonl",
        "phase_c_prompt/structural_controls.jsonl", "phase_c_prompt/gated_type_kv_decomposition.jsonl",
        "phase_d_anchor/gate.json", "phase_d_anchor/long_horizon_manifest.jsonl",
        "phase_d_anchor/landmark_annotations.jsonl", "phase_d_anchor/local_acquisition_deficits.jsonl",
        "phase_d_anchor/per_landmark_anchor_rescue.jsonl", "phase_d_anchor/future_use_results.jsonl",
        "phase_d_anchor/gated_necessity_results.jsonl", "phase_d_anchor/route_ablation_results.jsonl",
        "phase_d_anchor/anchor_classification.json", "phase_d_anchor/anchor_density.json",
        "phase_d_anchor/anchor_type_enrichment.json",
        "analysis/historical_vs_fresh_replication.json", "analysis/token_type_atlas.json",
        "analysis/position_vs_type_analysis.json", "analysis/visual_alignment_analysis.json",
        "analysis/boundary_analysis.json", "analysis/sparse_vs_distributed_analysis.json",
        "analysis/phase_specificity_analysis.json", "analysis/hierarchical_descriptive_model.json",
        "summaries/stage3c8_summary.md", "summaries/stage3c8_acceptance.json",
        "summaries/next_stage_recommendation.md",
    ]
    required_paths = [OUT / name for name in required]
    structured_paths = [path for path in required_paths if path.suffix in {".json", ".jsonl"}]
    structured_finite = True
    for path in structured_paths:
        if not path.is_file():
            structured_finite = False
            continue
        value = read_json(path) if path.suffix == ".json" else read_jsonl(path)
        structured_finite = structured_finite and finite(value)

    phase_ids = {
        phase: {
            role: result_ids(OUT / f"raw/{phase}/{role}")
            for role in ("historical", "fresh")
        }
        for phase in ("phase_a", "phase_b", "phase_c")
    }
    gated_ids = result_ids(OUT / "raw/phase_c_gated_kv")
    gated_rows = read_jsonl(OUT / "phase_c_prompt/gated_type_kv_decomposition.jsonl")
    phase_d_raw = result_ids(OUT / "raw/phase_d")
    phase_d_derived = [
        read_jsonl(OUT / name) for name in (
            "phase_d_anchor/local_acquisition_deficits.jsonl",
            "phase_d_anchor/per_landmark_anchor_rescue.jsonl",
            "phase_d_anchor/future_use_results.jsonl",
            "phase_d_anchor/gated_necessity_results.jsonl",
            "phase_d_anchor/route_ablation_results.jsonl",
        )
    ]
    annotations = read_jsonl(OUT / "annotations/per_token_annotations.jsonl")
    annotation_bases = {str(row["base_problem_id"]) for row in annotations}
    figures = sorted((OUT / "analysis/figures").glob("*.png"))
    prohibited = [
        path for path in OUT.rglob("*")
        if path.is_dir() and path.name.lower() in {
            "sink_intervention", "stage4", "residual_feature_learning",
            "unconstrained_history_search", "failure_analysis", "multi_evidence_refresh",
        }
    ]
    checks = {
        "required_files": all(path.is_file() for path in required_paths),
        "structured_metrics_finite": structured_finite,
        "cohort_counts": len(validation) == 8 and len(historical) == 24 and len(fresh) == 64,
        "cohorts_disjoint": not (validation & fresh) and not (historical & fresh),
        "fresh_accounting_frozen": accounting["retained"] == 64 and not accounting["selection_used_attention"] and not accounting["selection_used_carrier_outcome"],
        "mechanical_validation": mechanics["status"] == "PASS" and len(mechanics["base_problem_ids"]) == 8 and all(mechanics["checks"].values()),
        "phase_raw_cardinality": all(rows["historical"] == historical and rows["fresh"] == fresh for rows in phase_ids.values()),
        "historical_reproduction_exact": replication["historical_exact"] and replication["historical_count"] == 24,
        "annotations_cover_all_scored_bases": historical | fresh | validation <= annotation_bases,
        "phase_c_full_q_reference": len(read_jsonl(OUT / "phase_c_prompt/full_q_reference.jsonl")) == 88,
        "phase_c_gate_obeyed": (gated_ids == fresh and bool(gated_rows)) if phase_c_gate["run"] else (not gated_ids and not gated_rows),
        "phase_d_gate_obeyed": (bool(phase_d_raw) if phase_d_cohort["run"] else not phase_d_raw and not any(phase_d_derived)),
        "figures_complete": len(figures) == 22 and all(path.stat().st_size > 0 for path in figures),
        "acceptance_complete": acceptance["status"] == "PASS" and acceptance["passed"] == 25 and acceptance["total"] == 25 and all(row["status"] == "PASS" for row in acceptance["criteria"]),
        "one_recommendation": bool(acceptance.get("recommendation")) and acceptance.get("recommendation_count") == 1,
        "no_prohibited_follow_on": not prohibited and acceptance.get("follow_on_started") is False,
    }
    output = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "passed": sum(checks.values()),
        "total": len(checks),
        "checks": checks,
        "raw_counts": {
            phase: {role: len(ids) for role, ids in roles.items()}
            for phase, roles in phase_ids.items()
        },
        "phase_c_gated_kv_raw_count": len(gated_ids),
        "phase_d_raw_count": len(phase_d_raw),
        "figure_count": len(figures),
    }
    path = OUT / "audit/artifact_validation.json"
    path.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))
    if output["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
