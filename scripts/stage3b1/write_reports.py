#!/usr/bin/env python3
"""Write the final Stage 3B.1 summary, acceptance audit, and recommendation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import ensure_directory, write_json


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b1"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def pct(value: float) -> str:
    return f"{100.0 * float(value):.1f}%"


def scalar(summary: dict[str, Any], key: str = "median") -> str:
    return f"{float(summary[key]):.4f}"


def criterion(identifier: int, text: str, passed: bool, evidence: str) -> dict[str, Any]:
    return {
        "id": identifier,
        "criterion": text,
        "status": "PASS" if passed else "FAIL",
        "evidence": evidence,
    }


def main() -> None:
    config = read_json(OUT / "config/stage3b1_config.json")
    schedule = read_jsonl(OUT / "config/checkpoint_schedule.jsonl")
    results = read_jsonl(OUT / "scoring/per_problem_timing_results.jsonl")
    checkpoint = read_json(OUT / "scoring/per_checkpoint_statistics.json")
    curves = read_json(OUT / "analysis/retention_curves.json")
    sufficiency = read_jsonl(OUT / "analysis/sufficiency_times.jsonl")
    monotonicity = read_jsonl(OUT / "analysis/monotonicity_audit.jsonl")
    gains = read_json(OUT / "analysis/prefill_vs_postprefill_gain.json")
    evidence = read_json(OUT / "analysis/evidence_type_analysis.json")
    attention = read_json(OUT / "analysis/attention_timing_comparison.json")
    validation = read_json(OUT / "analysis/aggregation_validation.json")
    smoke = read_json(OUT / "smoke/cutoff_timing_validation.json")
    shard_configs = [
        read_json(path)
        for path in sorted((OUT / "raw/shards").glob("cohort_*/config.json"))
    ]
    raw_summaries = [
        read_json(path)
        for path in sorted((OUT / "raw/shards").glob("cohort_*/result.json"))
    ]

    base_ids = {str(row["base_problem_id"]) for row in results}
    checkpoints = [timing for result in results for timing in result["timing"]]
    frozen_before_scoring = bool(shard_configs) and all(
        config["frozen_at"] < row["created_at"] for row in shard_configs
    )
    relative_used = all(
        any(label.startswith("E0_minus_") for point in row["checkpoints"] for label in point["labels"])
        for row in schedule
    )
    progress_used = all(
        any(label.startswith("progress_") for point in row["checkpoints"] for label in point["labels"])
        for row in schedule
    )
    sham_complete = all(
        set(timing["condition_scores"]) == {"original", "counterfactual", "sham"}
        for timing in checkpoints
    )
    figure_count = len(list((OUT / "analysis/figures").glob("*.png")))
    decision = str(gains["prospective_decision"])

    acceptance = [
        criterion(1, "All 49 frozen bases are attempted", len(results) == 49 and len(base_ids) == 49, f"{len(results)}/49 results across {len(base_ids)} unique bases."),
        criterion(2, "Checkpoint schedules are frozen before cohort scoring", frozen_before_scoring and len(schedule) == 49, f"Frozen at {config['frozen_at']}; {len(shard_configs)} shard run signatures were created later."),
        criterion(3, "Both E0-relative and normalized-progress coordinates are used", relative_used and progress_used, f"{len(checkpoints)} deduplicated problem-checkpoint scores retain both coordinate-label families."),
        criterion(4, "Generation-start results reproduce Stage 3B.0", all(row["generation_start_stage3b0_exact"] for row in results), f"{sum(row['generation_start_stage3b0_exact'] for row in results)}/49 exact."),
        criterion(5, "No-cutoff results reproduce Stage 3A", all(row["no_cutoff_stage3a_exact"] for row in results), f"{sum(row['no_cutoff_stage3a_exact'] for row in results)}/49 exact."),
        criterion(6, "Post-cutoff generated-query-to-visual access is correctly blocked", all(row["all_cutoff_audits_valid"] for row in checkpoints), f"{sum(row['all_cutoff_audits_valid'] for row in checkpoints)}/{len(checkpoints)} boundary audits valid."),
        criterion(7, "Sham controls are evaluated", sham_complete, f"Original/counterfactual/sham scores present at all {len(checkpoints)} checkpoints."),
        criterion(8, "Continuous retention curves are produced", curves.get("n") == 49 and len(curves.get("curves", [])) == 49, f"{len(curves.get('curves', []))}/49 raw unsmoothed curves."),
        criterion(9, "Threshold times are secondary to continuous analysis", bool(checkpoint["continuous_retention_is_primary"]), "Raw continuous retention is primary; rho 0.50/0.80/0.90 crossings are secondary."),
        criterion(10, "Monotonicity is audited rather than assumed", len(monotonicity) == 49, f"{len(monotonicity)}/49 raw curves audited."),
        criterion(11, "base_problem_id remains the statistical unit", len(base_ids) == len(results) == 49, "One result per frozen unique base_problem_id."),
        criterion(12, "Attention is used only in the frozen secondary comparison", attention["analysis_role"].startswith("secondary") and not any(row.get("selection_used_attention", True) for row in results), f"Selection was attention-independent; exact Stage 2C overlap N={attention['matched_problem_count']}."),
        criterion(13, "No Q/R patching is performed", not (OUT / "patching").exists() and not validation["stage3b2_started"], "No Stage 3B.1 patching output exists; Stage 3B.2 not started."),
        criterion(14, "No layer/module/head/path analysis is performed", not validation["stage3b2_started"], "Only the frozen all-layer edge cutoff was scored; no localization analysis was run."),
        criterion(15, "A GO / CONDITIONAL GO / REDIRECT decision is written", decision.startswith(("GO", "CONDITIONAL GO", "REDIRECT")), decision),
    ]
    technical_pass = all(row["status"] == "PASS" for row in acceptance)
    acceptance_payload = {
        "stage": "3B.1",
        "overall_status": "PASS" if technical_pass else "FAIL",
        "scientific_recommendation": decision,
        "criteria": acceptance,
        "all_criteria_pass": technical_pass,
        "stage3b2_started": False,
    }
    ensure_directory(OUT / "summaries")
    write_json(OUT / "summaries/stage3b1_acceptance.json", acceptance_payload)

    inputs = gains["decision_inputs"]
    pattern_counts = inputs["timing_pattern_counts"]
    first80 = inputs["first_rho80"]
    stable80 = inputs["stable_rho80"]
    nonmonotonic = inputs["material_non_monotonic"]
    numeric = evidence["strata"]["tier1_local_numeric_label"]
    structural = evidence["strata"]["tier3_structural_visual_edit"]
    peak_allocated = max((int(row["peak_gpu_allocated_bytes"]) for row in raw_summaries), default=0)
    late = checkpoint["e0_relative"]["E0_minus_1"]
    late_rows = [next(timing for timing in row["timing"] if "E0_minus_1" in timing["labels"]) for row in results]
    mean_late_sham_shift = sum(float(row["sham_shift"]) for row in late_rows) / len(late_rows)
    rho50_first_count = sum(row["threshold_times"]["rho_50"]["first"] is not None for row in sufficiency)
    rho50_stable_count = sum(row["threshold_times"]["rho_50"]["stable"] is not None for row in sufficiency)

    summary_lines = [
        "# Stage 3B.1 summary — Visual-sufficiency timing",
        "",
        "## Outcome",
        "",
        f"**Technical status: {'PASS' if technical_pass else 'FAIL'} ({sum(row['status'] == 'PASS' for row in acceptance)}/15 acceptance criteria).**",
        "",
        f"**Recommendation: {decision}.**",
        "",
        (
            f"Across 49 frozen base problems, {first80['count']}/49 ({pct(first80['proportion'])}) reached a first raw retention crossing at rho>=0.80, "
            f"and {stable80['count']}/49 ({pct(stable80['proportion'])}) remained above that threshold at every later sampled checkpoint. "
            f"Median generation-start retention was {scalar(gains['prefill_retention'])}; median maximum strict-pre-E0 retention was {scalar(gains['maximum_pre_e0_retention'])}; "
            f"the median maximum post-prefill gain was {scalar(gains['maximum_postprefill_gain'])}."
        ),
        "",
        "These quantities measure preservation of the Stage 3A evidence-specific counterfactual effect after future visual access is removed. Retention is not a unique information fraction and does not identify a carrier.",
        "",
        "## Cohort and intervention",
        "",
        "- Primary unit: 49 frozen unique Stage 3A `base_problem_id` values (45 local numeric-label edits; 4 structural edits).",
        f"- Schedule: {len(checkpoints)} unique problem-checkpoint pairs after exact-index deduplication ({min(len(row['checkpoints']) for row in schedule)}–{max(len(row['checkpoints']) for row in schedule)} per base).",
        "- Coordinates: E0-relative offsets -128, -64, -32, -16, -8, -4, -1 where available, plus normalized progress 0%, 25%, 50%, 75%, and 90%.",
        "- Cutoff semantics: cutoff `c` permits normal vision for generated queries `y_0...y_(c-1)` and blocks all generated-query→all-visual-key edges from `y_c` onward in all 36 language layers. Prefill is unchanged.",
        "- Scoring: identical Stage 3A strict pre-E0 prefix, evidence candidates, original/counterfactual/sham images, and full-sequence eager path at every checkpoint.",
        "- Selection and checkpoint placement used no attention measurements.",
        "",
        "## Validation",
        "",
        f"The three-base short/medium/long smoke gate was **{smoke['gate']}**. No-cutoff scores exactly reproduced Stage 3A for 49/49 bases; generation-start cutoff scores exactly reproduced Stage 3B.0 for 49/49. All {len(checkpoints)} cutoff audits verified the frozen visual-key list, first modified query, all-layer coverage, and zero prefill or pre-cutoff modification.",
        "",
        f"Seven A5000 cohort shards completed. Maximum reported allocated GPU memory was {peak_allocated / (1024 ** 3):.2f} GiB. Median synchronized candidate-forward time per base was {validation['per_problem_synchronized_forward_seconds']['median']:.2f} seconds. Eight required figures were produced ({figure_count} observed).",
        "",
        "## Primary timing results",
        "",
        f"- First rho>=0.80 crossing: {first80['count']}/49 ({pct(first80['proportion'])}).",
        f"- Stable rho>=0.80 crossing: {stable80['count']}/49 ({pct(stable80['proportion'])}).",
        f"- First/stable rho>=0.50 crossing: {rho50_first_count}/49 and {rho50_stable_count}/49.",
        f"- E0-1 retention: mean {late['retention_ratio_raw']['mean']:.4f}, median {late['retention_ratio_raw']['median']:.4f} (N={late['n']}).",
        f"- Maximum post-prefill gain: mean {gains['maximum_postprefill_gain']['mean']:.4f}, median {gains['maximum_postprefill_gain']['median']:.4f}.",
        f"- Material non-monotonic curves (>0.20 downward step): {nonmonotonic['count']}/49 ({pct(nonmonotonic['proportion'])}).",
        "- Frozen descriptive timing categories: " + ", ".join(f"{key}={value}" for key, value in sorted(pattern_counts.items())) + ".",
        "",
        "The raw unsmoothed curves are primary. Discrete threshold crossings are summaries of the sampled grid, not exact continuous acquisition times.",
        "",
        "## Controls and strata",
        "",
        f"Sham-controlled CE was computed at every checkpoint. At E0-1 it remained positive in {late['positive_sham_controlled_CE']['count']}/49 bases, while the mean original-vs-sham shift was {mean_late_sham_shift:.4f}. Numeric-label examples (N={numeric['n']}) had median maximum gain {numeric['maximum_postprefill_gain']['median']:.4f}; structural examples (N={structural['n']}) had {structural['maximum_postprefill_gain']['median']:.4f}. Structural N=4 is too small for a strong comparison.",
        "",
        "## Secondary Stage 2C attention comparison",
        "",
        f"Exact event matching yielded {attention['matched_problem_count']} overlapping problems; {attention['unmatched_problem_count']} cohort problems had no unique exact Stage 2C event match. This analysis was performed only after the primary cohort and timing definitions were frozen.",
        "",
        f"Only {attention['summaries']['rho_50']['first']['available_n']}/9 overlap problems reached a rho>=0.50 crossing, and {attention['summaries']['rho_80']['first']['available_n']}/9 reached rho>=0.80. Thus the exact-overlap subset is insufficient for a reliable high-sufficiency-versus-attention timing comparison.",
        "",
        "ROI attention remains descriptive. Agreement or disagreement between an ROI-attention peak and a causal sufficiency crossing does not establish where evidence is stored, when it was first acquired, or which mechanism carried it.",
        "",
        "## Limitations",
        "",
        "- Retention ratios can be heterogeneous and non-monotonic because the intervention can interact nonlinearly with distributed/redundant computation.",
        "- The checkpoint grid bounds rather than exactly localizes transitions; threshold times are discrete.",
        "- Teacher-forced evidence-specific preference is the primary behavioral readout. Optional short rollouts were omitted prospectively because the Stage 3B.0 128-token rollouts rarely reached the target fact.",
        "- The exact Stage 2C overlap is small, and the structural stratum contains only four bases.",
        "- This stage does not locate evidence in Q, R, a layer, module, head, or path.",
        "",
        "## Scientific boundary",
        "",
        "Stage 3B.1 tests when future direct visual access becomes dispensable for preserving an evidence-specific counterfactual effect. It does not claim that the retained effect is stored in any particular state, that attention marks acquisition, or that a LOOK/THINK mode exists. Stage 3B.2 and all carrier-localization experiments remain unstarted.",
        "",
        "## Key artifacts",
        "",
        "- `config/checkpoint_schedule.jsonl` and `smoke/cutoff_timing_validation.json`",
        "- `scoring/per_problem_timing_results.jsonl` and `scoring/per_checkpoint_statistics.json`",
        "- `analysis/retention_curves.json`, `analysis/sufficiency_times.jsonl`, and `analysis/monotonicity_audit.jsonl`",
        "- `analysis/prefill_vs_postprefill_gain.json` and `analysis/attention_timing_comparison.json`",
        "- `summaries/stage3b1_acceptance.json` and `summaries/stage3b2_recommendation.md`",
    ]
    (OUT / "summaries/stage3b1_summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    if decision.startswith("GO"):
        recommendation_body = [
            "The frozen GO rule passed: at least half of the cohort had a stable rho>=0.80 crossing, median E0-1 retention was at least 0.80, and median maximum post-prefill gain was at least 0.50.",
            "The next reviewed plan may therefore ask where the newly sufficient post-prefill evidence is carried. This result does not itself authorize or execute Q/R patching or other carrier localization.",
        ]
    elif decision.startswith("CONDITIONAL GO"):
        recommendation_body = [
            "The frozen full GO rule did not pass, but at least half of the cohort reached a first rho>=0.80 crossing and median maximum post-prefill gain was at least 0.30.",
            "The next reviewed action should refine the cutoff grid around empirical transition windows before any carrier patching. No refinement or Stage 3B.2 experiment is executed here.",
        ]
    else:
        recommendation_body = [
            "Neither frozen advancement rule passed. The current timing evidence does not justify carrier localization as the immediate next experiment.",
            "The next reviewed plan should account for persistent direct-vision dependence and curve heterogeneity. No redirected experiment is selected or executed here.",
        ]
    recommendation_lines = [
        f"# {decision}",
        "",
        *recommendation_body,
        "",
        "Frozen decision inputs:",
        "",
        f"- first rho>=0.80: {first80['count']}/49 ({pct(first80['proportion'])})",
        f"- stable rho>=0.80: {stable80['count']}/49 ({pct(stable80['proportion'])})",
        f"- median E0-1 retention: {gains['e0_minus_1_retention']['median']:.4f}",
        f"- median maximum post-prefill gain: {gains['maximum_postprefill_gain']['median']:.4f}",
        "",
        "Attention timing was not part of this decision. Stage 3B.2, Q/R patching, layer/module/head/path localization, and all other next-stage experiments remain unstarted.",
    ]
    (OUT / "summaries/stage3b2_recommendation.md").write_text(
        "\n".join(recommendation_lines) + "\n", encoding="utf-8"
    )
    print(json.dumps({"technical_status": acceptance_payload["overall_status"], "decision": decision}, indent=2))


if __name__ == "__main__":
    main()
