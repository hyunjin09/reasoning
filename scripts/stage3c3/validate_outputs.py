#!/usr/bin/env python3
"""Independently validate persisted Stage 3C.3 artifacts from raw bundles."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c3"
TARGETS = ("target_a", "target_b")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finite(value: Any) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(finite(item) for item in value.values())
    if isinstance(value, list):
        return all(finite(item) for item in value)
    return True


def main() -> None:
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any) -> None:
        checks.append({"name": name, "status": "PASS" if passed else "FAIL", "detail": detail})

    validation_manifest = read_jsonl(OUT / "cohort/validation_manifest.jsonl")
    primary_manifest = read_jsonl(OUT / "cohort/primary_manifest.jsonl")
    validation_ids = {str(row["base_problem_id"]) for row in validation_manifest}
    primary_ids = {str(row["base_problem_id"]) for row in primary_manifest}
    check("validation_primary_disjoint", not (validation_ids & primary_ids), sorted(validation_ids & primary_ids))
    check("cohort_sizes", len(validation_ids) == 7 and len(primary_ids) == 24, {"validation": len(validation_ids), "primary": len(primary_ids)})
    check(
        "frozen_targets_byte_exact",
        sha256(OUT / "config/frozen_targets.json") == sha256(ROOT / "outputs/stage3c2/config/frozen_targets.json"),
        sha256(OUT / "config/frozen_targets.json"),
    )

    validation_paths = sorted((OUT / "validation/query_forms").glob("shard_*/examples/*/result.json"))
    primary_paths = sorted((OUT / "phase_a_query/raw").glob("shard_*/examples/*/result.json"))
    validation = [read_json(path) for path in validation_paths]
    primary = sorted(
        (read_json(path) for path in primary_paths),
        key=lambda row: int(row["base_problem_id"]),
    )
    check("validation_bundle_count", {str(row["base_problem_id"]) for row in validation} == validation_ids, len(validation))
    check("primary_bundle_count", {str(row["base_problem_id"]) for row in primary} == primary_ids and len(primary) == 24, len(primary))
    check("all_json_finite", all(finite(row) for row in [*validation, *primary]), len(validation) + len(primary))

    form = read_json(OUT / "config/rope_query_formulation.json")
    earliest_primary = min(path.stat().st_mtime for path in primary_paths)
    check("form_frozen_before_primary", form["selected_form"] == "content_recipient_rope" and (OUT / "config/rope_query_formulation.json").stat().st_mtime <= earliest_primary, {"form": form["selected_form"]})
    validation_summary = read_json(OUT / "validation/validation_summary.json")
    check("validation_gate_pass", validation_summary["status"] == "pass" and validation_summary["primary_scoring_authorized"], validation_summary["direction_gate"])

    selected = form["selected_form"]
    mechanics = {"self": True, "kv": True, "nonselected": True, "finite": True}
    recomputed: dict[str, dict[str, list[float]]] = {
        target: {name: [] for name in ("nec_rds", "suf_rds", "nec_alpha", "suf_alpha", "nec_evidence", "suf_evidence", "control_difference")}
        for target in TARGETS
    }
    for row in primary:
        check_row_layout = bool(row["condition_layout_exact"] and row["conditions"] == ["O"] and row["query_only_intervention"])
        mechanics["finite"] &= check_row_layout
        for target_id in TARGETS:
            target = row["target_results"][target_id]["O"]
            forms = target["forms"][selected]
            for state in ("M", "R"):
                arm = forms["causal"][f"self_{state}"]
                mechanics["self"] &= bool(
                    arm["preference"]["D"] == target["native"][state]["preference"]["D"]
                    and all(audit["selected_head_max_abs_delta"] == 0.0 for audit in arm["query_patch_audits"])
                )
            role_effects: dict[str, list[float]] = {"causal": [], "noncausal": []}
            for role in ("causal", "noncausal"):
                for direction, state, arm_name, sign in (
                    ("necessity", "R", "Q_R_to_Q_M", -1.0),
                    ("sufficiency", "M", "Q_M_to_Q_R", 1.0),
                ):
                    native = target["native"][state]
                    arm = forms[role][arm_name]
                    nr = native["routing"][role]
                    pr = arm["routing"]
                    rds = sign * (float(pr["RDS_T_vs_M"]) - float(nr["RDS_T_vs_M"]))
                    alpha = sign * (float(pr["groups"]["T"]["mean_alpha_v_norm"]) - float(nr["groups"]["T"]["mean_alpha_v_norm"]))
                    evidence = sign * (float(arm["preference"]["D"]) - float(native["preference"]["D"]))
                    role_effects[role].append(rds)
                    if role == "causal":
                        prefix = "nec" if direction == "necessity" else "suf"
                        recomputed[target_id][f"{prefix}_rds"].append(rds)
                        recomputed[target_id][f"{prefix}_alpha"].append(alpha)
                        recomputed[target_id][f"{prefix}_evidence"].append(evidence)
                    for invariant in arm["recipient_state_invariance"].values():
                        mechanics["kv"] &= bool(invariant["recipient_prefix_exact"] and invariant["visual_kv_exact"])
                    for audit in arm["query_patch_audits"]:
                        mechanics["nonselected"] &= bool(
                            audit["nonselected_head_max_abs_delta"] == 0.0
                            and audit["nonselected_attention_max_abs_delta"] == 0.0
                            and audit["nonselected_head_output_max_abs_delta"] == 0.0
                        )
            recomputed[target_id]["control_difference"].append(statistics.mean(role_effects["causal"]) - statistics.mean(role_effects["noncausal"]))
    check("primary_self_query_exact", mechanics["self"], mechanics["self"])
    check("primary_recipient_kv_exact", mechanics["kv"], mechanics["kv"])
    check("primary_nonselected_heads_exact", mechanics["nonselected"], mechanics["nonselected"])
    check("primary_layout_and_condition", mechanics["finite"], mechanics["finite"])

    stats = read_json(OUT / "analysis/query_causality_statistics.json")
    metric_map = {
        "nec_rds": ("necessity", "RDS_T_vs_M"),
        "suf_rds": ("sufficiency", "RDS_T_vs_M"),
        "nec_alpha": ("necessity", "alpha_v_T"),
        "suf_alpha": ("sufficiency", "alpha_v_T"),
        "nec_evidence": ("necessity", "evidence"),
        "suf_evidence": ("sufficiency", "evidence"),
    }
    stats_exact = True
    for target_id in TARGETS:
        for name, (direction, metric) in metric_map.items():
            persisted = stats["targets"][target_id][direction][metric]
            values = recomputed[target_id][name]
            stats_exact &= bool(
                persisted["values"] == values
                and persisted["median"] == float(statistics.median(values))
                and persisted["positive_count"] == sum(value > 0 for value in values)
            )
        control = recomputed[target_id]["control_difference"]
        persisted_control = stats["targets"][target_id]["causal_minus_noncausal_reciprocal_RDS"]
        stats_exact &= persisted_control["values"] == control
    check("statistics_exactly_recomputed", stats_exact, stats_exact)
    check("phase_a_gate_failed", not stats["phase_a_gate"]["phase_b_authorized"] and not any(row["pass"] for row in stats["phase_a_gate"]["targets"].values()), stats["phase_a_gate"])

    expected_counts = {
        "per_problem_query_patch_results.jsonl": 24,
        "routing_metrics.jsonl": 192,
        "value_influx_metrics.jsonl": 768,
        "evidence_results.jsonl": 192,
        "noncausal_head_controls.jsonl": 48,
    }
    counts = {name: len(read_jsonl(OUT / "phase_a_query" / name)) for name in expected_counts}
    check("phase_a_table_counts", counts == expected_counts, counts)
    check("sink_table_count", len(read_jsonl(OUT / "observational_sink/sink_under_query_intervention.jsonl")) == 192, 192)
    check("phase_b_not_run", (OUT / "phase_b_hpre/per_problem_hpre_patch_results.jsonl").stat().st_size == 0 and read_json(OUT / "analysis/hpre_causality_statistics.json")["status"] == "not_run", "gate obeyed")
    check("phase_c_not_run", (OUT / "phase_c_optional_alpha/alpha_intervention_results.jsonl").stat().st_size == 0, "disabled")
    figures = sorted((OUT / "analysis/figures").glob("*.png"))
    check("fourteen_figures", len(figures) == 14 and all(path.stat().st_size > 10_000 for path in figures), {"count": len(figures), "minimum_bytes": min(path.stat().st_size for path in figures)})
    acceptance = read_json(OUT / "summaries/stage3c3_acceptance.json")
    recommendation = (OUT / "summaries/next_stage_recommendation.md").read_text(encoding="utf-8")
    check("single_redirect", acceptance["recommendation"] == "REDIRECT — Routing Intervention Not Behavioral" and "GO —" not in recommendation, acceptance["recommendation"])
    check("later_stages_not_started", not (ROOT / "outputs/stage3c4").exists() and not (ROOT / "outputs/stage4").exists(), "no output directories")

    report = {
        "status": "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL",
        "check_count": len(checks),
        "passed": sum(row["status"] == "PASS" for row in checks),
        "failed": sum(row["status"] == "FAIL" for row in checks),
        "checks": checks,
    }
    write_path = OUT / "summaries/artifact_validation.json"
    write_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "check_count", "passed", "failed")}, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
