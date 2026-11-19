#!/usr/bin/env python3
"""Independently validate completed Stage 3C.3-R persisted artifacts."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from visual_reasoning.stage3c3r.analysis import holm_adjust
from visual_reasoning.stage3c3r.protocol import redundancy_gate


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c3r"
TARGETS = ("target_a", "target_b")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def raw_rows(phase: str) -> list[dict[str, Any]]:
    return [read_json(path) for path in sorted((OUT / "raw" / phase).glob("shard_*/examples/*/result.json"))]


def main() -> None:
    config = read_json(OUT / "config/stage3c3r_config.json")
    validation_manifest = read_jsonl(OUT / "cohort/validation_manifest.jsonl")
    primary_manifest = read_jsonl(OUT / "cohort/primary_manifest.jsonl")
    validation = raw_rows("validation")
    phase_a = raw_rows("phase_a")
    phase_b = raw_rows("phase_b")
    primary_ids = {str(row["base_problem_id"]) for row in primary_manifest}
    validation_ids = {str(row["base_problem_id"]) for row in validation_manifest}
    target_flat = read_jsonl(OUT / "phase_a_gain/target_gain_results.jsonl")
    control_paths = [
        OUT / "phase_a_gain/mention_control_results.jsonl",
        OUT / "phase_a_gain/irrelevant_control_results.jsonl",
        OUT / "phase_a_gain/noncausal_head_controls.jsonl",
    ]
    scope_flat = {
        scope: read_jsonl(OUT / f"phase_b_redundancy/scope_{scope.lower()}_results.jsonl")
        for scope in ("R1", "R2", "R3")
    }
    gate = read_json(OUT / "phase_b_redundancy/redundancy_gate.json")
    family = read_json(OUT / "analysis/primary_family_statistics.json")
    acceptance = read_json(OUT / "summaries/stage3c3r_acceptance.json")
    required = [
        "config/stage3c3r_config.json", "config/frozen_targets.json", "config/lambda_grid.json",
        "config/nested_scope_family.json", "config/primary_family.json",
        "cohort/validation_manifest.jsonl", "cohort/primary_manifest.jsonl", "cohort/exclusions.jsonl",
        "audit/contribution_partition.json", "audit/lambda_endpoint_validation.json",
        "audit/head_selectivity.json", "audit/source_invariance.json",
        "audit/attention_invariance.json", "audit/reproducibility.json",
        "phase_a_gain/per_problem_lambda_results.jsonl", "phase_a_gain/target_gain_results.jsonl",
        "phase_a_gain/mention_control_results.jsonl", "phase_a_gain/irrelevant_control_results.jsonl",
        "phase_a_gain/noncausal_head_controls.jsonl", "phase_a_gain/query_patch_operating_points.jsonl",
        "phase_b_redundancy/scope_r1_results.jsonl", "phase_b_redundancy/scope_r2_results.jsonl",
        "phase_b_redundancy/scope_r3_results.jsonl", "phase_b_redundancy/redundancy_gate.json",
        "analysis/dose_response_statistics.json", "analysis/threshold_descriptives.json",
        "analysis/saturation_analysis.json", "analysis/query_patch_curve_comparison.json",
        "analysis/target_specificity_analysis.json", "analysis/redundancy_scope_analysis.json",
        "summaries/stage3c3r_summary.md", "summaries/stage3c3r_acceptance.json",
        "summaries/next_stage_recommendation.md",
    ]
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, evidence: Any) -> None:
        checks.append({"name": name, "status": "PASS" if passed else "FAIL", "evidence": evidence})

    add("required_outputs_exist", all((OUT / path).is_file() for path in required), {"count": len(required)})
    add("source_plan_hash_exact", config["source_plan_sha256"] == sha256(ROOT / config["source_plan"]), config["source_plan_sha256"])
    add("cohort_7_24_disjoint", len(validation_ids) == 7 and len(primary_ids) == 24 and not validation_ids & primary_ids, {"validation": len(validation_ids), "primary": len(primary_ids)})
    add("raw_cohorts_complete", {str(row["base_problem_id"]) for row in validation} == validation_ids and {str(row["base_problem_id"]) for row in phase_a} == primary_ids and {str(row["base_problem_id"]) for row in phase_b} == primary_ids, {"validation": len(validation), "phase_a": len(phase_a), "phase_b": len(phase_b)})
    add("flat_row_counts", len(target_flat) == 288 and all(len(read_jsonl(path)) == 144 for path in control_paths) and all(len(rows) == 144 for rows in scope_flat.values()), {"target": len(target_flat), "controls": [len(read_jsonl(path)) for path in control_paths], "scopes": {scope: len(rows) for scope, rows in scope_flat.items()}})

    raw_target = {}
    mechanics_flags = []
    for row in phase_a:
        base = str(row["base_problem_id"])
        mechanics_flags.extend([
            not row["selection_used_attention"], row["contribution_gain_only"],
            not row["sink_directly_intervened"], not row["query_or_hpre_directly_intervened"],
        ])
        groups = [set(row["source_groups"][name]) for name in ("T", "M", "I")]
        mechanics_flags.append(all(groups[i].isdisjoint(groups[j]) for i in range(3) for j in range(i + 1, 3)))
        for target in TARGETS:
            arm = row["target_results"][target]["arms"]["target_causal"]
            for gain, scored in arm["lambda_results"].items():
                raw_target[(base, target, float(gain))] = float(scored["D"])
                mechanics_flags.append(bool(scored["finite"]))
                for candidate in scored["candidate_audits"].values():
                    for audit in candidate:
                        mechanics_flags.extend([
                            audit["partition_max_abs_error"] <= 1e-6,
                            audit["selected_head_expected_max_abs_error"] == 0.0,
                            audit["query_max_abs_delta"] == 0.0,
                            audit["key_max_abs_delta"] == 0.0,
                            audit["value_max_abs_delta"] == 0.0,
                            audit["attention_max_abs_delta"] == 0.0,
                            audit["nonselected_head_max_abs_delta"] == 0.0,
                            audit["other_position_max_abs_delta"] == 0.0,
                        ])
    flat_exact = all(
        math.isclose(float(row["E"]), raw_target[(str(row["base_problem_id"]), row["target_id"], float(row["lambda"]))], rel_tol=0, abs_tol=0)
        for row in target_flat
    )
    add("phase_a_flat_recomputes_exact", flat_exact, len(raw_target))
    add("phase_a_mechanics_recompute", all(mechanics_flags), {"booleans": len(mechanics_flags)})

    retained = {}
    for base in primary_ids:
        retained[base] = {
            target: raw_target[(base, target, 0.0)] / raw_target[(base, target, 1.0)]
            for target in TARGETS
        }
    recomputed_gate = redundancy_gate(retained)
    add("gate_recomputes_exact", recomputed_gate["passed"] == gate["passed"] and recomputed_gate["median_retained"] == gate["median_retained"] and recomputed_gate["fraction_at_least_0_80"] == gate["fraction_at_least_0_80"], {"median": recomputed_gate["median_retained"], "fraction": recomputed_gate["fraction_at_least_0_80"]})
    add("phase_b_was_prospectively_gated", gate["phase_b_authorized"] and gate["nested_family_frozen_before_phase_a"], gate["decision"])

    phase_b_flags = []
    raw_scope = {}
    for row in phase_b:
        base = str(row["base_problem_id"])
        phase_b_flags.extend([
            row["contribution_gain_only"], not row["sink_directly_intervened"],
            not row["query_or_hpre_directly_intervened"],
        ])
        for target in TARGETS:
            for scope, arm in row["target_results"][target]["arms"].items():
                for gain, scored in arm["lambda_results"].items():
                    raw_scope[(base, target, scope, float(gain))] = float(scored["D"])
                    phase_b_flags.append(bool(scored["finite"]))
                    phase_b_flags.extend(int(spec["layer_index"]) in (28, 29) for spec in arm["layer_specs"])
    scope_exact = all(
        math.isclose(float(row["E"]), raw_scope[(str(row["base_problem_id"]), row["target_id"], row["scope"], float(row["lambda"]))], rel_tol=0, abs_tol=0)
        for rows in scope_flat.values() for row in rows
    )
    add("phase_b_flat_recomputes_exact", scope_exact, len(raw_scope))
    add("phase_b_scope_and_boundary_valid", all(phase_b_flags), {"allowed_layers": [28, 29]})
    add("lambda_one_phase_a_phase_b_exact", all(raw_scope[(base, target, scope, 1.0)] == raw_target[(base, target, 1.0)] for base in primary_ids for target in TARGETS for scope in ("R1", "R2", "R3")), "all 144 base/target/scope native comparisons")

    adjusted = holm_adjust([float(row["raw_p"]) for row in family["rows"]])
    add("holm_family_recomputes", len(family["rows"]) == 26 and all(a == float(row["holm_adjusted_p"]) for a, row in zip(adjusted, family["rows"])), {"family_size": len(family["rows"])})
    figures = sorted((OUT / "analysis/figures").glob("*.png"))
    add("twelve_nonempty_figures", len(figures) == 12 and all(path.stat().st_size > 1000 for path in figures), {"count": len(figures), "minimum_bytes": min(path.stat().st_size for path in figures)})
    add("validation_and_mechanics_pass", all(read_json(path)["status"] == "PASS" for path in (
        OUT / "validation/validation_summary.json", OUT / "audit/primary_mechanics.json", OUT / "audit/phase_b_mechanics.json"
    )), "validation, Phase A, Phase B")
    add("failed_smoke_preserved", (OUT / "raw/validation_smoke/examples/141/result.json").is_file() and (OUT / "raw/validation_smoke_v2/examples/141/result.json").is_file(), "v1 and corrected v2")
    add("acceptance_20_of_20", acceptance["all_criteria_pass"] and len(acceptance["criteria"]) == 20 and all(row["status"] == "PASS" for row in acceptance["criteria"]), len(acceptance["criteria"]))
    add("single_recommendation", acceptance["recommendation"] == "GO — Redundancy Localization Beyond W4" and "GO — Redundancy Localization Beyond W4" in (OUT / "summaries/next_stage_recommendation.md").read_text(encoding="utf-8"), acceptance["recommendation"])
    add("prohibited_actions_absent", not config["sink_manipulated"] and not config["query_or_hpre_intervention_added"] and not config["broader_than_w4_allowed"] and not config["stage3c4_authorized"] and not config["stage4_authorized"], "sink/query/h_pre/broader-W4/later stages false")
    add("all_json_finite", all("NaN" not in path.read_text(encoding="utf-8") and "Infinity" not in path.read_text(encoding="utf-8") for path in OUT.rglob("*.json")), "all Stage 3C.3-R JSON")

    passed = all(row["status"] == "PASS" for row in checks)
    report = {
        "status": "PASS" if passed else "FAIL",
        "check_count": len(checks),
        "passed_count": sum(row["status"] == "PASS" for row in checks),
        "checks": checks,
        "validated_from_raw_artifacts": True,
        "scientific_outcome": acceptance["scientific_outcome"],
        "recommendation": acceptance["recommendation"],
    }
    write_json(OUT / "summaries/artifact_validation.json", report)
    print(json.dumps(report, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
