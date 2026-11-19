#!/usr/bin/env python3
"""Independently validate completed Stage 3B.5 persisted artifacts and metrics."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json
from visual_reasoning.stage3b5.metrics import boundary_restoration_metrics
from visual_reasoning.stage3b5.protocol import evaluate_stage3b5_decision


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b5"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(left: float | None, right: float | None, tolerance: float = 1e-12) -> bool:
    if left is None or right is None:
        return left is right
    return abs(float(left) - float(right)) <= tolerance


def main() -> None:
    checks: dict[str, bool] = {}
    config = read_json(OUT / "config/stage3b5_config.json")
    family = read_json(OUT / "config/primary_family.json")
    cohort = read_jsonl(OUT / "config/cohort_manifest.jsonl")
    validation_manifest = read_jsonl(OUT / "validation/validation_manifest.jsonl")
    validation = read_json(OUT / "validation/validation_results.json")
    stats = read_json(OUT / "analysis/boundary_restoration_statistics.json")
    decision = read_json(OUT / "analysis/decision_rule_evaluation.json")
    acceptance = read_json(OUT / "summaries/stage3b5_acceptance.json")
    gpu_jobs = read_json(OUT / "config/gpu_job_manifest.json")

    checks["source_plan_hash_exact"] = config["source_plan_sha256"] == sha256(ROOT / config["source_plan"])
    checks["stage3b4_config_hash_exact"] = config["source_stage3b4_config_sha256"] == sha256(ROOT / config["source_stage3b4_config"])
    checks["family_exact_40_unique"] = bool(
        family["family_size"] == 40
        and len(family["tests"]) == 40
        and len({row["test_id"] for row in family["tests"]}) == 40
    )
    checks["cohort_exact_37_unique"] = len(cohort) == 37 and len({str(row["base_problem_id"]) for row in cohort}) == 37
    checks["validation_exact_8_disjoint"] = len(validation_manifest) == 8 and not (
        {str(row["base_problem_id"]) for row in validation_manifest}
        & {str(row["base_problem_id"]) for row in cohort}
    )
    checks["validation_passed_before_primary"] = validation["decision"] == "PASS" and validation["primary_authorized"]

    raw_paths = sorted((OUT / "scoring/raw").glob("primary_*/examples/*/result.json"))
    raw_results = [read_json(path) for path in raw_paths]
    raw_bases = [str(row["base_problem_id"]) for row in raw_results]
    checks["raw_results_exact_37_unique"] = len(raw_results) == 37 and set(raw_bases) == {str(row["base_problem_id"]) for row in cohort}
    checks["all_raw_mechanics_pass"] = all(all(row["mechanical_controls"].values()) for row in raw_results)
    shard_summaries = [read_json(path) for path in sorted((OUT / "scoring/raw").glob("primary_*/result.json"))]
    checks["eight_shards_complete"] = len(shard_summaries) == 8 and all(row["all_mechanical_controls_passed"] for row in shard_summaries)
    environments = [read_json(path) for path in sorted((OUT / "scoring/raw").glob("primary_*/environment.json"))]
    checks["all_primary_environments_a5000"] = len(environments) == 8 and all("A5000" in str(row["gpu_name"]) for row in environments)

    recomputed_metric_count = 0
    metrics_exact = True
    raw_test_ids = []
    for result in raw_results:
        for point in result["coordinates"]:
            for row in point["boundary_restoration"]:
                raw_test_ids.append(row["test_id"])
                controls = row["controls"]
                recomputed = boundary_restoration_metrics(
                    recipient_scores={
                        recipient: {
                            donor: float(controls[recipient][donor]["D"])
                            for donor in ("O", "O_sham", "C", "C_sham")
                        }
                        for recipient in ("O", "C")
                    },
                    all_layer_bri=float(row["all_layer_BRI"]),
                )
                for key in (
                    "R_O", "R_C", "BMR_O", "BMR_C", "BMR", "BMR_normalized",
                    "A_render", "render_to_semantic_ratio", "render_to_all_layer_ratio",
                ):
                    metrics_exact = metrics_exact and close(recomputed[key], row[key])
                metrics_exact = metrics_exact and (
                    bool(recomputed["bidirectionally_source_consistent"])
                    == bool(row["bidirectionally_source_consistent"])
                )
                recomputed_metric_count += 1
    checks["all_1480_paired_metrics_recomputed_exact"] = recomputed_metric_count == 1480 and metrics_exact
    family_ids = {row["test_id"] for row in family["tests"]}
    checks["raw_family_matches_frozen_family"] = len(raw_test_ids) == 1480 and set(raw_test_ids) == family_ids
    checks["statistics_exact_40_family"] = len(stats["rows"]) == 40 and {row["test_id"] for row in stats["rows"]} == family_ids
    checks["scoring_files_have_expected_rows"] = bool(
        all(len(read_jsonl(OUT / f"scoring/{name}")) == 296 for name in (
            "pre_block_state_restoration.jsonl", "pre_attn_norm_restoration.jsonl",
            "post_attn_state_restoration.jsonl", "pre_mlp_norm_restoration.jsonl",
            "post_block_restoration.jsonl",
        ))
        and len(read_jsonl(OUT / "scoring/two_layer_recompute_restoration.jsonl")) == 148
    )
    reevaluated = evaluate_stage3b5_decision(
        decision["cells"], controls_pass=all(stats["mechanical_controls"].values())
    )
    checks["decision_recomputed_exact"] = (
        reevaluated["recommendation"] == decision["recommendation"]
        and reevaluated["qualifying_cells"] == decision["qualifying_cells"]
    )
    cross = read_json(OUT / "analysis/cross_layer_sequential_analysis.json")
    equivalence = cross["post_attn_recompute_vs_post_block_equivalence"]
    checks["post_attn_post_block_equivalence_audited"] = bool(
        equivalence["observed_count"] == 296
        and equivalence["all_BMR_exact"]
        and equivalence["all_public_scores_exact"]
    )
    checks["ten_figures_present"] = len(list((OUT / "analysis/figures").glob("*.png"))) == 10
    checks["acceptance_17_of_17"] = bool(
        acceptance["status"] == "PASS"
        and len(acceptance["criteria"]) == 17
        and all(row["passed"] for row in acceptance["criteria"])
        and not acceptance["later_stage_started"]
    )
    allowed = {
        "GO — Attention head/path localization",
        "GO — MLP/residual mechanism localization",
        "GO — Upstream residual-origin search",
        "GO — Cross-layer sequential mediation",
        "REDIRECT — Broader residual/norm interaction",
    }
    checks["one_allowed_recommendation"] = decision["recommendation"] in allowed
    checks["gpu_job_record_complete"] = bool(
        gpu_jobs["job_count"] == 16
        and gpu_jobs["all_jobs_succeeded"]
        and all(job["slurm_job_id"] and job["log_path"] and job["result_path"] for job in gpu_jobs["jobs"])
    )
    passed = all(checks.values())
    payload = {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if passed else "FAIL",
        "checks": checks,
        "passed_count": sum(checks.values()),
        "check_count": len(checks),
        "raw_primary_base_count": len(raw_results),
        "recomputed_metric_row_count": recomputed_metric_count,
        "recommendation": decision["recommendation"],
        "no_new_inference_run": True,
    }
    write_json(OUT / "analysis/artifact_validation.json", payload)
    print(json.dumps(payload, indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
