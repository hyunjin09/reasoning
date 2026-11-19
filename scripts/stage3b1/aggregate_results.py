#!/usr/bin/env python3
"""Aggregate frozen Stage 3B.1 timing shards and produce causal timing analyses."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr

from visual_reasoning.stage0.io import ensure_directory, write_json, write_jsonl
from visual_reasoning.stage3a.metrics import bootstrap_interval, summarize_effect_values
from visual_reasoning.stage3b1.analysis import (
    classify_timing_pattern,
    monotonicity_audit,
    schedule_matches_curve,
    select_frozen_attention_event,
    threshold_times,
)


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "outputs/stage3b1/raw/shards"
OUT = ROOT / "outputs/stage3b1"
FIGURES = OUT / "analysis/figures"
RELATIVE_LABELS = tuple(f"E0_minus_{value}" for value in (128, 64, 32, 16, 8, 4, 1))
PROGRESS_LABELS = tuple(f"progress_{value}" for value in (0, 25, 50, 75, 90))
REQUIRED_FIGURES = {
    "01_e0_relative_retention.png",
    "02_normalized_progress_retention.png",
    "03_per_problem_retention_curves.png",
    "04_sufficiency_time_distributions.png",
    "05_prefill_vs_maximum_retention.png",
    "06_representative_timing_categories.png",
    "07_evidence_type_curves.png",
    "08_attention_vs_sufficiency_timing.png",
}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def finite(values: Iterable[float]) -> list[float]:
    result = [float(value) for value in values]
    if not result or not all(math.isfinite(value) for value in result):
        raise ValueError("Expected nonempty finite values")
    return result


def proportion(values: list[bool], *, seed: int) -> dict[str, Any]:
    array = np.asarray(values, dtype=np.float64)
    if array.size == 0:
        return {"count": 0, "n": 0, "proportion": None, "bootstrap_ci": None}
    return {
        "count": int(array.sum()),
        "n": int(array.size),
        "proportion": float(array.mean()),
        "bootstrap_ci": bootstrap_interval(array, statistic="mean", seed=seed),
    }


def compact_timing(row: dict[str, Any]) -> dict[str, Any]:
    return {
        key: row[key]
        for key in (
            "cutoff_generated_index",
            "labels",
            "requested_coordinates",
            "tokens_before_e0",
            "actual_progress",
            "CE",
            "CE_controlled",
            "sham_shift",
            "D_original",
            "D_counterfactual",
            "D_sham",
            "retention_ratio_raw",
            "retention_ratio_controlled_raw",
            "all_cutoff_audits_valid",
        )
    }


def result_forward_seconds(result: dict[str, Any]) -> float:
    """Sum synchronized candidate-forward latency for one base problem."""

    scores = list(result["no_cutoff_condition_scores"].values())
    scores.extend(score for timing in result["timing"] for score in timing["condition_scores"].values())
    return float(
        sum(
            score[candidate]["runtime_seconds"]
            for score in scores
            for candidate in ("original_candidate", "counterfactual_candidate")
        )
    )


def checkpoint_statistics(results: list[dict[str, Any]], label: str, seed: int) -> dict[str, Any]:
    selected = [
        (result, timing)
        for result in results
        for timing in result["timing"]
        if label in timing["labels"]
    ]
    retention = finite(timing["retention_ratio_raw"] for _, timing in selected)
    controlled = finite(timing["CE_controlled"] for _, timing in selected)
    return {
        "label": label,
        "n": len(selected),
        "retention_ratio_raw": summarize_effect_values(retention, seed=seed),
        "CE_controlled": summarize_effect_values(controlled, seed=seed + 10),
        "positive_sham_controlled_CE": proportion([value > 0.0 for value in controlled], seed=seed + 20),
        "rho_at_least_0_50": proportion([value >= 0.50 for value in retention], seed=seed + 30),
        "rho_at_least_0_80": proportion([value >= 0.80 for value in retention], seed=seed + 40),
        "rho_at_least_0_90": proportion([value >= 0.90 for value in retention], seed=seed + 50),
        "actual_progress": summarize_effect_values(
            finite(timing["actual_progress"] for _, timing in selected), seed=seed + 60
        ),
        "per_base": [
            {
                "base_problem_id": result["base_problem_id"],
                "cutoff_generated_index": timing["cutoff_generated_index"],
                "tokens_before_e0": timing["tokens_before_e0"],
                "actual_progress": timing["actual_progress"],
                "retention_ratio_raw": timing["retention_ratio_raw"],
                "CE": timing["CE"],
                "CE_controlled": timing["CE_controlled"],
            }
            for result, timing in selected
        ],
    }


def crossing_values(sufficiency: list[dict[str, Any]], threshold: str, kind: str, key: str) -> list[float]:
    return [
        float(row["threshold_times"][threshold][kind][key])
        for row in sufficiency
        if row["threshold_times"][threshold][kind] is not None
    ]


def attention_comparison(sufficiency: list[dict[str, Any]], results: list[dict[str, Any]]) -> dict[str, Any]:
    timing_rows = read_jsonl(ROOT / "outputs/stage2c/analysis/timing_categories.jsonl")
    frozen_stage3a = read_json(ROOT / "outputs/stage3a/analysis/attention_moderator_analysis.json")
    frozen_density_by_base = {
        str(row["base_problem_id"]): float(row["pre_e0_roi_density"])
        for row in frozen_stage3a["matched_rows"]
    }
    by_event: dict[tuple[str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in timing_rows:
        by_event[(str(row["example_id"]), int(row["events"]["e0"][0]))].append(row)
    suff_by_base = {str(row["base_problem_id"]): row for row in sufficiency}
    matched = []
    unmatched = []
    for result in results:
        key = (str(result["example_id"]), int(result["e0_start_token"]))
        candidates = by_event.get(key, [])
        event = select_frozen_attention_event(
            candidates,
            frozen_pre_e0_density=frozen_density_by_base.get(str(result["base_problem_id"])),
        )
        if event is None:
            unmatched.append(
                {
                    "base_problem_id": result["base_problem_id"],
                    "example_id": result["example_id"],
                    "e0_start_token": result["e0_start_token"],
                    "matching_stage2c_events": len(candidates),
                }
            )
            continue
        peak = int(result["e0_start_token"]) + int(event["local_peak_offset_from_e0"])
        suff = suff_by_base[str(result["base_problem_id"])]
        comparisons = {}
        for threshold in ("rho_50", "rho_80", "rho_90"):
            comparisons[threshold] = {}
            for kind in ("first", "stable"):
                crossing = suff["threshold_times"][threshold][kind]
                comparisons[threshold][kind] = (
                    {
                        "sufficiency_cutoff_generated_index": crossing["cutoff_generated_index"],
                        "attention_minus_sufficiency_tokens": peak - crossing["cutoff_generated_index"],
                        "sufficiency_precedes_attention_peak": crossing["cutoff_generated_index"] < peak,
                    }
                    if crossing is not None
                    else None
                )
        matched.append(
            {
                "base_problem_id": result["base_problem_id"],
                "example_id": result["example_id"],
                "evidence_id": event["evidence_id"],
                "e0_start_token": result["e0_start_token"],
                "attention_peak_generated_index": peak,
                "attention_peak_offset_from_e0": event["local_peak_offset_from_e0"],
                "stage2c_timing_category": event["timing_category"],
                "event_selection": (
                    "unique exact example/E0 match"
                    if len(candidates) == 1
                    else "duplicate E0 resolved by exact frozen Stage 3A pre-E0 density match"
                ),
                "comparisons": comparisons,
            }
        )
    summaries = {}
    for threshold in ("rho_50", "rho_80", "rho_90"):
        summaries[threshold] = {}
        for kind in ("first", "stable"):
            available = [row["comparisons"][threshold][kind] for row in matched if row["comparisons"][threshold][kind]]
            deltas = [float(row["attention_minus_sufficiency_tokens"]) for row in available]
            summaries[threshold][kind] = {
                "available_n": len(available),
                "attention_minus_sufficiency_tokens": summarize_effect_values(deltas, seed=74_000 + len(deltas))
                if deltas
                else None,
                "sufficiency_precedes_attention_peak": proportion(
                    [row["sufficiency_precedes_attention_peak"] for row in available], seed=75_000 + len(deltas)
                ),
            }
    first80 = [row for row in matched if row["comparisons"]["rho_80"]["first"]]
    correlation = None
    if len(first80) >= 3:
        statistic = spearmanr(
            [row["comparisons"]["rho_80"]["first"]["sufficiency_cutoff_generated_index"] for row in first80],
            [row["attention_peak_generated_index"] for row in first80],
        )
        correlation = {"rho": float(statistic.statistic), "p_value": float(statistic.pvalue), "n": len(first80)}
    return {
        "analysis_role": "secondary exact-event comparison after primary timing results were frozen",
        "matched_problem_count": len(matched),
        "unmatched_problem_count": len(unmatched),
        "frozen_stage3a_matched_problem_count": int(frozen_stage3a["matched_problem_count"]),
        "join_matches_frozen_stage3a_count": len(matched) == int(frozen_stage3a["matched_problem_count"]),
        "duplicate_e0_resolution": (
            "When multiple Stage 2C events shared the exact example/E0 key, select the unique event whose "
            "pre-E0 density exactly reproduces the already-frozen Stage 3A moderator row."
        ),
        "matched_rows": matched,
        "unmatched_rows": unmatched,
        "summaries": summaries,
        "rho80_first_spearman": correlation,
        "attention_is_descriptive_not_causal": True,
        "small_overlap_limits_inference": True,
    }


def plot_results(
    results: list[dict[str, Any]],
    checkpoint_stats: dict[str, Any],
    sufficiency: list[dict[str, Any]],
    gains: list[dict[str, Any]],
    evidence_analysis: dict[str, Any],
    attention: dict[str, Any],
) -> None:
    ensure_directory(FIGURES)
    x_rel = np.asarray([-128, -64, -32, -16, -8, -4, -1], dtype=float)
    rel_stats = [checkpoint_stats["e0_relative"][label] for label in RELATIVE_LABELS]
    means = np.asarray([row["retention_ratio_raw"]["mean"] for row in rel_stats])
    medians = np.asarray([row["retention_ratio_raw"]["median"] for row in rel_stats])
    low = np.asarray([row["retention_ratio_raw"]["mean_bootstrap_ci"]["ci_low"] for row in rel_stats])
    high = np.asarray([row["retention_ratio_raw"]["mean_bootstrap_ci"]["ci_high"] for row in rel_stats])
    fig, ax = plt.subplots(figsize=(7, 4.5)); ax.plot(x_rel, means, marker="o", label="Mean"); ax.plot(x_rel, medians, marker="s", label="Median")
    ax.fill_between(x_rel, low, high, alpha=0.2); ax.axhline(0.8, color="gray", linestyle="--", linewidth=0.8)
    ax.set(xlabel="Cutoff position relative to E0 (tokens)", ylabel="Raw retention ρ", title="E0-relative visual-sufficiency curve"); ax.legend(); fig.tight_layout(); fig.savefig(FIGURES/"01_e0_relative_retention.png", dpi=180); plt.close(fig)

    x_prog = np.asarray([0, 0.25, 0.5, 0.75, 0.9])
    prog_stats = [checkpoint_stats["normalized_progress"][label] for label in PROGRESS_LABELS]
    means = np.asarray([row["retention_ratio_raw"]["mean"] for row in prog_stats]); medians = np.asarray([row["retention_ratio_raw"]["median"] for row in prog_stats])
    low = np.asarray([row["retention_ratio_raw"]["mean_bootstrap_ci"]["ci_low"] for row in prog_stats]); high = np.asarray([row["retention_ratio_raw"]["mean_bootstrap_ci"]["ci_high"] for row in prog_stats])
    fig, ax = plt.subplots(figsize=(7, 4.5)); ax.plot(x_prog, means, marker="o", label="Mean"); ax.plot(x_prog, medians, marker="s", label="Median"); ax.fill_between(x_prog, low, high, alpha=0.2)
    ax.axhline(0.8, color="gray", linestyle="--", linewidth=0.8); ax.set(xlabel="Normalized progress to E0", ylabel="Raw retention ρ", title="Normalized-progress visual-sufficiency curve"); ax.legend(); fig.tight_layout(); fig.savefig(FIGURES/"02_normalized_progress_retention.png", dpi=180); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    for result in results:
        curve=[compact_timing(row) for row in result["timing"]]; ax.plot([row["actual_progress"] for row in curve],[row["retention_ratio_raw"] for row in curve],alpha=0.28,linewidth=0.8)
    ax.axhline(0.8,color="gray",linestyle="--",linewidth=0.8); ax.set(xlabel="Actual progress to E0",ylabel="Raw retention ρ",title="All 49 unsmoothed per-problem curves"); fig.tight_layout(); fig.savefig(FIGURES/"03_per_problem_retention_curves.png",dpi=180); plt.close(fig)

    distributions=[crossing_values(sufficiency,key,"first","tokens_before_e0") for key in ("rho_50","rho_80","rho_90")]
    fig, ax=plt.subplots(figsize=(6,4.5)); available=[values if values else [np.nan] for values in distributions]; ax.boxplot(available,tick_labels=["ρ≥0.50","ρ≥0.80","ρ≥0.90"]); ax.set(ylabel="Tokens before E0 at first crossing",title="Discrete sufficiency-time distributions"); fig.tight_layout(); fig.savefig(FIGURES/"04_sufficiency_time_distributions.png",dpi=180); plt.close(fig)

    fig, ax=plt.subplots(figsize=(6,5)); ax.scatter([row["prefill_retention"] for row in gains],[row["maximum_pre_e0_retention"] for row in gains],c=["#4472c4" if "numeric" in row["evidence_type"] else "#ed7d31" for row in gains]); ax.plot([-0.2,1.2],[-0.2,1.2],"--",color="gray",linewidth=0.8); ax.set(xlabel="Generation-start retention",ylabel="Maximum strict pre-E0 retention",title="Prefill residual vs maximum pre-E0 retention"); fig.tight_layout(); fig.savefig(FIGURES/"05_prefill_vs_maximum_retention.png",dpi=180); plt.close(fig)

    suff_by_base={row["base_problem_id"]:row for row in sufficiency}; representatives=[]
    for category in sorted(set(row["timing_pattern"] for row in sufficiency)):
        candidates=[row for row in sufficiency if row["timing_pattern"]==category]; representatives.append(candidates[len(candidates)//2])
    fig, ax=plt.subplots(figsize=(8,5))
    result_by_base={row["base_problem_id"]:row for row in results}
    for rep in representatives:
        curve=result_by_base[rep["base_problem_id"]]["timing"]; ax.plot([row["actual_progress"] for row in curve],[row["retention_ratio_raw"] for row in curve],marker="o",markersize=3,label=f"{rep['timing_pattern'].split('_')[0]}: {rep['base_problem_id']}")
    ax.axhline(0.8,color="gray",linestyle="--",linewidth=0.8); ax.set(xlabel="Actual progress to E0",ylabel="Raw retention ρ",title="Representative frozen timing categories"); ax.legend(fontsize=7); fig.tight_layout(); fig.savefig(FIGURES/"06_representative_timing_categories.png",dpi=180); plt.close(fig)

    fig, ax=plt.subplots(figsize=(7,4.5))
    for evidence_type,color in (("tier1_local_numeric_label","#4472c4"),("tier3_structural_visual_edit","#ed7d31")):
        curve=evidence_analysis["strata"][evidence_type]["normalized_progress_mean_retention"]; ax.plot(x_prog,[curve[label] for label in PROGRESS_LABELS],marker="o",label=f"{evidence_type} (N={evidence_analysis['strata'][evidence_type]['n']})",color=color)
    ax.axhline(0.8,color="gray",linestyle="--",linewidth=0.8); ax.set(xlabel="Normalized progress to E0",ylabel="Mean raw retention ρ",title="Retention by evidence stratum"); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(FIGURES/"07_evidence_type_curves.png",dpi=180); plt.close(fig)

    points=[row for row in attention["matched_rows"] if row["comparisons"]["rho_80"]["first"]]
    fig, ax=plt.subplots(figsize=(6,5))
    if points:
        x=[row["comparisons"]["rho_80"]["first"]["sufficiency_cutoff_generated_index"] for row in points]; y=[row["attention_peak_generated_index"] for row in points]; ax.scatter(x,y); low=min(x+y); high=max(x+y); ax.plot([low,high],[low,high],"--",color="gray",linewidth=0.8)
        for row,xv,yv in zip(points,x,y): ax.annotate(str(row["base_problem_id"]),(xv,yv),fontsize=7)
    else: ax.text(0.5,0.5,"No exact-overlap problem reached ρ≥0.80",ha="center",va="center",transform=ax.transAxes)
    ax.set(xlabel="First ρ≥0.80 cutoff index",ylabel="Stage 2C ROI-attention peak index",title="Secondary attention vs causal sufficiency timing"); fig.tight_layout(); fig.savefig(FIGURES/"08_attention_vs_sufficiency_timing.png",dpi=180); plt.close(fig)


def main() -> None:
    expected = read_jsonl(OUT / "config/cohort_manifest.jsonl")
    expected_bases = {str(row["base_problem_id"]) for row in expected}
    schedules = {
        str(row["base_problem_id"]): row["checkpoints"]
        for row in read_jsonl(OUT / "config/checkpoint_schedule.jsonl")
    }
    shard_dirs = sorted(path for path in RAW.glob("cohort_*") if (path / "result.json").is_file())
    if len(shard_dirs) != 7:
        raise RuntimeError(f"Expected seven completed shards, observed {len(shard_dirs)}")
    results=[]
    for shard in shard_dirs:
        results.extend(read_jsonl(shard/"timing_results.jsonl"))
    if len(results)!=49 or {str(row["base_problem_id"]) for row in results}!=expected_bases:
        raise RuntimeError("Timing aggregation does not exactly cover the frozen cohort")
    results.sort(key=lambda row:int(row["base_problem_id"]))
    if sum(len(row["timing"]) for row in results)!=489:
        raise RuntimeError("Timing aggregation does not contain the frozen 489 unique checkpoints")
    if not all(schedule_matches_curve(schedules[str(row["base_problem_id"])], row["timing"]) for row in results):
        raise RuntimeError("A scored timing curve does not exactly match its frozen checkpoint schedule")
    if not all(row["no_cutoff_stage3a_exact"] and row["generation_start_stage3b0_exact"] for row in results):
        raise RuntimeError("A Stage 3A or Stage 3B.0 reproduction failed")
    if not all(timing["all_cutoff_audits_valid"] for row in results for timing in row["timing"]):
        raise RuntimeError("A timed cutoff boundary audit failed")
    write_jsonl(OUT/"scoring/per_problem_timing_results.jsonl",results)
    write_jsonl(OUT/"scoring/rollout_results.jsonl",[])

    checkpoint_stats={
        "primary_unit":"base_problem_id",
        "e0_relative":{label:checkpoint_statistics(results,label,81_000+i*100) for i,label in enumerate(RELATIVE_LABELS)},
        "normalized_progress":{label:checkpoint_statistics(results,label,82_000+i*100) for i,label in enumerate(PROGRESS_LABELS)},
        "continuous_retention_is_primary":True,
        "thresholds_are_secondary":[0.5,0.8,0.9],
    }
    write_json(OUT/"scoring/per_checkpoint_statistics.json",checkpoint_stats)

    sufficiency=[]; monotonicity=[]; gains=[]; curves=[]
    for result in results:
        curve=[compact_timing(row) for row in result["timing"]]
        thresholds=threshold_times(curve,e0_start_token=int(result["e0_start_token"]))
        audit=monotonicity_audit(curve,control_noise_tolerance=1e-6)
        category=classify_timing_pattern(curve,thresholds=thresholds,monotonicity=audit)
        start=next(row for row in curve if row["cutoff_generated_index"]==0)
        late=next(row for row in curve if "E0_minus_1" in row["labels"])
        max_row=max(curve,key=lambda row:float(row["retention_ratio_raw"]))
        sufficiency.append({"base_problem_id":result["base_problem_id"],"example_id":result["example_id"],"evidence_type":result["evidence_type"],"e0_start_token":result["e0_start_token"],"threshold_times":thresholds,"timing_pattern":category})
        monotonicity.append({"base_problem_id":result["base_problem_id"],"example_id":result["example_id"],"evidence_type":result["evidence_type"],"timing_pattern":category,**audit})
        gains.append({"base_problem_id":result["base_problem_id"],"example_id":result["example_id"],"evidence_type":result["evidence_type"],"prefill_retention":start["retention_ratio_raw"],"maximum_pre_e0_retention":max_row["retention_ratio_raw"],"maximum_retention_cutoff_index":max_row["cutoff_generated_index"],"maximum_postprefill_gain":float(max_row["retention_ratio_raw"]-start["retention_ratio_raw"]),"e0_minus_1_retention":late["retention_ratio_raw"],"e0_minus_1_gain":float(late["retention_ratio_raw"]-start["retention_ratio_raw"])})
        curves.append({"base_problem_id":result["base_problem_id"],"example_id":result["example_id"],"evidence_type":result["evidence_type"],"e0_start_token":result["e0_start_token"],"timing_pattern":category,"curve":curve})
    write_jsonl(OUT/"analysis/sufficiency_times.jsonl",sufficiency)
    write_jsonl(OUT/"analysis/monotonicity_audit.jsonl",monotonicity)
    write_json(OUT/"analysis/retention_curves.json",{"primary_unit":"base_problem_id","n":49,"curves":curves})

    first80=[row["threshold_times"]["rho_80"]["first"] is not None for row in sufficiency]
    stable80=[row["threshold_times"]["rho_80"]["stable"] is not None for row in sufficiency]
    final_values=finite(row["e0_minus_1_retention"] for row in gains); max_gains=finite(row["maximum_postprefill_gain"] for row in gains)
    decision_inputs={"first_rho80":proportion(first80,seed=83_001),"stable_rho80":proportion(stable80,seed=83_002),"e0_minus_1_retention":summarize_effect_values(final_values,seed=83_003),"maximum_postprefill_gain":summarize_effect_values(max_gains,seed=83_004),"material_non_monotonic":proportion([row["material_non_monotonic"] for row in monotonicity],seed=83_005),"timing_pattern_counts":dict(Counter(row["timing_pattern"] for row in sufficiency))}
    go=decision_inputs["stable_rho80"]["proportion"]>=0.5 and decision_inputs["e0_minus_1_retention"]["median"]>=0.8 and decision_inputs["maximum_postprefill_gain"]["median"]>=0.5
    conditional=(not go and decision_inputs["first_rho80"]["proportion"]>=0.5 and decision_inputs["maximum_postprefill_gain"]["median"]>=0.3)
    decision="GO — Stage 3B.2 carrier localization" if go else ("CONDITIONAL GO — Timing refinement" if conditional else "REDIRECT — Persistent direct-vision dependence")
    gain_analysis={"primary_unit":"base_problem_id","n":49,"per_base":gains,"prefill_retention":summarize_effect_values(finite(row["prefill_retention"] for row in gains),seed=84_001),"maximum_pre_e0_retention":summarize_effect_values(finite(row["maximum_pre_e0_retention"] for row in gains),seed=84_002),"maximum_postprefill_gain":decision_inputs["maximum_postprefill_gain"],"e0_minus_1_retention":decision_inputs["e0_minus_1_retention"],"e0_minus_1_gain":summarize_effect_values(finite(row["e0_minus_1_gain"] for row in gains),seed=84_003),"decision_inputs":decision_inputs,"prospective_decision":decision,"retention_is_not_a_unique_information_fraction":True}
    write_json(OUT/"analysis/prefill_vs_postprefill_gain.json",gain_analysis)

    strata={}
    for evidence_type in sorted({row["evidence_type"] for row in results}):
        bases={row["base_problem_id"] for row in results if row["evidence_type"]==evidence_type}; selected_gains=[row for row in gains if row["base_problem_id"] in bases]
        strata[evidence_type]={"n":len(bases),"maximum_postprefill_gain":summarize_effect_values(finite(row["maximum_postprefill_gain"] for row in selected_gains),seed=85_000+len(bases)),"e0_minus_1_retention":summarize_effect_values(finite(row["e0_minus_1_retention"] for row in selected_gains),seed=85_100+len(bases)),"normalized_progress_mean_retention":{label:float(np.mean([entry["retention_ratio_raw"] for entry in checkpoint_stats["normalized_progress"][label]["per_base"] if entry["base_problem_id"] in bases])) for label in PROGRESS_LABELS}}
    evidence_analysis={"primary_unit":"base_problem_id","strata":strata,"structural_n_is_too_small_for_strong_claims":True}
    write_json(OUT/"analysis/evidence_type_analysis.json",evidence_analysis)
    attention=attention_comparison(sufficiency,results)
    if not attention["join_matches_frozen_stage3a_count"]:
        raise RuntimeError("Secondary attention join does not reproduce the frozen Stage 3A overlap count")
    write_json(OUT/"analysis/attention_timing_comparison.json",attention)
    plot_results(results,checkpoint_stats,sufficiency,gains,evidence_analysis,attention)
    observed_figures = {path.name for path in FIGURES.glob("*.png")}
    if not REQUIRED_FIGURES.issubset(observed_figures):
        raise RuntimeError(f"Missing required figures: {sorted(REQUIRED_FIGURES - observed_figures)}")
    forward_seconds = finite(result_forward_seconds(result) for result in results)
    write_json(OUT/"analysis/aggregation_validation.json",{"status":"PASS","completed_shards":[path.name for path in shard_dirs],"frozen_bases":49,"unique_problem_checkpoints":489,"all_schedules_exact":True,"all_no_cutoff_stage3a_exact":True,"all_generation_start_stage3b0_exact":True,"all_cutoff_audits_valid":True,"required_figure_count":len(REQUIRED_FIGURES),"figure_count":len(observed_figures),"rollouts_run":0,"per_problem_synchronized_forward_seconds":{"mean":float(np.mean(forward_seconds)),"median":float(np.median(forward_seconds)),"minimum":float(np.min(forward_seconds)),"maximum":float(np.max(forward_seconds)),"total":float(np.sum(forward_seconds))},"attention_overlap_n":attention["matched_problem_count"],"prospective_decision":decision,"stage3b2_started":False})
    print(json.dumps({"status":"PASS","decision":decision,"decision_inputs":decision_inputs,"attention_overlap":attention["matched_problem_count"]},indent=2))


if __name__ == "__main__":
    main()
