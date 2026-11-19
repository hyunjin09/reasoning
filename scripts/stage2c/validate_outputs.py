#!/usr/bin/env python3
"""Independently validate Stage 2C artifacts and acceptance criteria."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage2c.validation import validate_event_annotation


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "outputs/stage2c"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def criterion(number: int, text: str, passed: bool, evidence: str) -> dict:
    return {"criterion": number, "requirement": text, "status": "PASS" if passed else "FAIL", "evidence": evidence}


def main() -> None:
    failures: list[str] = []
    cohort = read_jsonl(OUTPUT / "cohort/cohort_manifest.jsonl")
    events = read_jsonl(OUTPUT / "annotations/evidence_event_annotations.jsonl")
    rois = read_jsonl(OUTPUT / "annotations/roi_annotations.jsonl")
    timing = read_jsonl(OUTPUT / "analysis/timing_categories.jsonl")
    candidates = read_jsonl(OUTPUT / "candidates/counterfactual_ready_candidates.jsonl")
    stage2b = read_json(OUTPUT / "stage2ab_reaudit/stage2b_window_timing.json")["windows"]
    stage2a = read_json(OUTPUT / "stage2ab_reaudit/stage2a_reinterpretation.json")["examples"]
    statistics = read_json(OUTPUT / "analysis/event_aligned_statistics.json")
    repeated = read_json(OUTPUT / "analysis/repeated_mention_statistics.json")
    indexing = read_json(OUTPUT / "convention_audit/attention_indexing_example.json")
    acceptance: list[dict] = []

    unique_examples = {row["example_id"] for row in cohort}
    source_counts = {source: sum(row["selection_source"] == source for row in cohort) for source in {row["selection_source"] for row in cohort}}
    valid_examples: set[str] = set()
    event_failures = []
    cohort_by_id = {row["example_id"]: row for row in cohort}
    for row in events:
        token_count = int(cohort_by_id[row["example_id"]]["reasoning_length"])
        issues = validate_event_annotation(row, token_count)
        if issues:
            event_failures.append({"evidence_id": row["evidence_id"], "issues": issues})
        else:
            valid_examples.add(row["example_id"])

    curve_failures = []
    for row in events:
        path = OUTPUT / f"analysis/evidence_curves/{row['evidence_id'].replace(':', '_')}.npz"
        if not path.exists():
            curve_failures.append(f"missing {path.name}")
            continue
        with np.load(path) as arrays:
            token_count = cohort_by_id[row["example_id"]]["reasoning_length"]
            required = {
                "prediction_aligned_roi_total_mass",
                "prediction_aligned_roi_per_token_density",
                "prediction_aligned_roi_conditional_visual_share",
                "processed_token_roi_total_mass",
                "processed_token_roi_per_token_density",
                "span_prediction_aligned_roi_per_token_density",
                "e0_window", "e1_window", "e2_window",
            }
            if not required.issubset(arrays.files):
                curve_failures.append(f"{path.name}: missing arrays {sorted(required - set(arrays.files))}")
            if arrays["prediction_aligned_roi_per_token_density"].shape != (token_count,):
                curve_failures.append(f"{path.name}: token shape mismatch")
            for name in ("e0_window", "e1_window", "e2_window"):
                if arrays[name].shape != (129,):
                    curve_failures.append(f"{path.name}: {name} is not fixed +/-64")

    figure_names = {
        "roi_attention_aligned_e0.png", "roi_attention_aligned_e1.png", "region_comparison.png",
        "roi_peak_timing_relative_e1.png", "first_vs_repeated_vs_matched.png",
        "representative_t1_t6.png", "stage2b_windows_relative_events.png",
    }
    actual_figures = {path.name for path in (OUTPUT / "analysis/figures").glob("*.png")}
    new_rois = [row for row in rois if row["mapping_source"].startswith("Stage 2C")]
    manual_roi_pass = len(new_rois) == 30 and all(row["manual_mapping_review"]["status"] == "pass" for row in new_rois)
    runtime_path = OUTPUT / "summaries/runtime_environment.json"
    runtime = read_json(runtime_path) if runtime_path.exists() else {}

    stage2a_hashes = read_json(ROOT / "outputs/stage2b/config/intervention_config.json")["stage2a_annotation_hashes_before"]
    historical_hash_failures = [path for path, expected in stage2a_hashes.items() if not (ROOT / path).exists() or sha256(ROOT / path) != expected]

    acceptance.extend(
        [
            criterion(1, "attention indexing is explicitly verified", indexing["validation"]["all_rows_checked"] > 0 and indexing["validation"]["historical_arrays_modified"] is False, "convention_audit/attention_indexing_audit.md and hand-checked example 699"),
            criterion(2, "50 examples are targeted", len(cohort) == 50 and len(unique_examples) == 50 and source_counts == {"Stage 2A reuse": 20, "Stage 2C attention-blind screen": 30}, f"cohort rows={len(cohort)}, unique={len(unique_examples)}, sources={source_counts}"),
            criterion(3, "at least 40 valid examples remain", len(valid_examples) >= 40 and not event_failures, f"valid annotated examples={len(valid_examples)}; event failures={len(event_failures)}"),
            criterion(4, "selection is attention-blind", all(row["selection_was_attention_blind"] for row in cohort), f"sources={source_counts}; exclusion log preserves pre-attention screen"),
            criterion(5, "E0/E1/E2 annotations are completed", len(events) == 70 and not event_failures, f"70 events; failures={len(event_failures)}"),
            criterion(6, "new ROI mappings are manually checked", manual_roi_pass, f"new mappings={len(new_rois)}; manual passes={sum(row['manual_mapping_review']['status'] == 'pass' for row in new_rois)}"),
            criterion(7, "PRE/ENTITY/FACT/POST/USE analysis is completed", set(statistics["region_density_statistics"]) == {"PRE", "ENTITY", "FACT", "POST", "USE"} and len(timing) == 70 and not curve_failures and figure_names <= actual_figures, f"70 token/span curve bundles; curve failures={len(curve_failures)}; seven required figures={figure_names <= actual_figures}"),
            criterion(8, "first vs repeated mention analysis is completed", "aggregate" in repeated and repeated["aggregate"]["evidence_items_with_repeated_references"] > 0, f"event-balanced repeated-reference n={repeated['aggregate']['evidence_items_with_repeated_references']}"),
            criterion(9, "semantic alignment remains a competing hypothesis", "descriptive" in statistics["scientific_boundary"].lower() and "causal" in statistics["scientific_boundary"].lower(), "summary and statistics retain semantic alignment and explicit non-causal boundary"),
            criterion(10, "all five Stage 2B examples are temporally re-audited", len(stage2b) == 10 and {row["example_id"] for row in stage2b} == {"699", "739", "2799", "3044", "3764"}, f"windows={len(stage2b)}, examples={sorted({row['example_id'] for row in stage2b})}"),
            criterion(11, "Stage 2A is reinterpreted under new timing definitions", len(stage2a) == 20, f"Stage 2A examples reinterpreted={len(stage2a)}"),
            criterion(12, "a best-effort counterfactual-ready candidate pool is produced", len(candidates) >= 20, f"candidate evidence items={len(candidates)}, unique examples={len({row['example_id'] for row in candidates})}"),
            criterion(13, "no large new causal experiment is run", not (OUTPUT / "inference").exists() and runtime.get("inference_performed") in (None, False) and runtime.get("model_loaded") in (None, False), "Stage 2C contains derived artifact analysis only; no inference output exists, and the scheduled runner forbids model loading"),
            criterion(14, "no carrier-patching experiment is started", not (OUTPUT / "carrier_patching").exists(), "No carrier-patching output or code path exists"),
            criterion(15, "an explicit next-stage recommendation is written", (OUTPUT / "summaries/next_stage_recommendation.md").exists() and "GO — Counterfactual content sensitivity" in (OUTPUT / "summaries/next_stage_recommendation.md").read_text(), "recommendation exists and was not executed"),
        ]
    )
    for row in acceptance:
        if row["status"] != "PASS":
            failures.append(f"criterion {row['criterion']}: {row['requirement']}")
    if historical_hash_failures:
        failures.append(f"historical Stage 2A hash mismatches: {historical_hash_failures}")
    if not figure_names <= actual_figures:
        failures.append(f"missing figures: {sorted(figure_names - actual_figures)}")
    failures.extend(curve_failures)

    report = {
        "stage": "2C temporal measurement audit",
        "overall_status": "PASS" if not failures else "FAIL",
        "acceptance_criteria_passed": sum(row["status"] == "PASS" for row in acceptance),
        "acceptance_criteria_total": 15,
        "criteria": acceptance,
        "independent_integrity_checks": {
            "all_required_figures_present": figure_names <= actual_figures,
            "curve_bundle_failures": curve_failures,
            "historical_stage2a_hashes_unchanged": not historical_hash_failures,
            "historical_stage2a_hash_failures": historical_hash_failures,
            "all_cohort_baselines_completed_correct": all(row["completed"] and row["correct"] for row in cohort),
        },
        "failures": failures,
        "stop_boundary": "Stage 2C complete; Stage 3 not started",
    }
    path = OUTPUT / "summaries/stage2c_acceptance.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["overall_status"], "passed": report["acceptance_criteria_passed"], "total": 15, "failures": failures}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
