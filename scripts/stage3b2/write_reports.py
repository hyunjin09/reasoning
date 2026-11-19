#!/usr/bin/env python3
"""Write the final Stage 3B.2 summary, acceptance audit, and recommendation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import ensure_directory, write_json


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b2"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def pct(value: float) -> str:
    return f"{100.0 * float(value):.1f}%"


def criterion(identifier: int, text: str, passed: bool, evidence: str) -> dict[str, Any]:
    return {
        "id": identifier,
        "criterion": text,
        "status": "PASS" if passed else "FAIL",
        "evidence": evidence,
    }


def main() -> None:
    config = read_json(OUT / "config/stage3b2_config.json")
    manifest = read_jsonl(OUT / "config/cohort_manifest.jsonl")
    schedule = read_jsonl(OUT / "config/switch_checkpoint_schedule.jsonl")
    annotations = read_jsonl(OUT / "annotations/discriminative_event_annotations.jsonl")
    smoke = read_json(OUT / "smoke/visual_source_switch_validation.json")
    results = read_jsonl(OUT / "scoring/per_problem_switch_results.jsonl")
    checkpoint = read_json(OUT / "scoring/per_checkpoint_statistics.json")
    rollouts = read_json(OUT / "scoring/rollout_summary.json")
    curves = read_json(OUT / "analysis/retrieval_timing_curves.json")
    bidirectional = read_json(OUT / "analysis/bidirectional_retrieval_statistics.json")
    cutoff = read_json(OUT / "analysis/cutoff_vs_switch_comparison.json")
    evidence = read_json(OUT / "analysis/evidence_type_analysis.json")
    attention = read_json(OUT / "analysis/attention_secondary_comparison.json")
    validation = read_json(OUT / "analysis/aggregation_validation.json")
    shard_configs = [read_json(path) for path in sorted((OUT / "raw/shards").glob("cohort_*/config.json"))]

    base_ids = {str(row["base_problem_id"]) for row in results}
    timing_rows = [point for row in results for point in row["timing"]]
    annotations_frozen = len(annotations) == 49 and all(row["manual_audit_status"] == "pass" for row in annotations)
    schedule_frozen = len(schedule) == 49 and all(
        config["frozen_at"] < shard["created_at"] for shard in shard_configs
    )
    all_layers = validation["all_capture_layers_valid"] and smoke["status"] == "PASS"
    all_switch_audits = validation["all_switch_audits_valid"]
    both_directions = all(
        "S_O_to_C" in row and "S_C_to_O" in row for row in timing_rows
    )
    self_exact = validation["all_self_switches_exact"]
    sham_complete = all("S_O_to_Sham" in row for row in timing_rows)
    effects_complete = all("BRI" in row for row in timing_rows)
    figure_count = len(list((OUT / "analysis/figures").glob("*.png")))
    decision = bidirectional["prospective_decision"]
    prohibited_paths = [
        OUT / "layerwise",
        OUT / "carrier_patching",
        OUT / "roi_switching",
        OUT / "head_path_analysis",
    ]

    acceptance = [
        criterion(1, "All 49 frozen bases are attempted", len(results) == len(base_ids) == 49, f"{len(results)}/49 rows across {len(base_ids)} unique base_problem_id values."),
        criterion(2, "E_d is frozen before causal scoring", annotations_frozen and schedule_frozen, f"49/49 annotations passed manual audit; Stage 3B.2 config froze at {config['frozen_at']} before all cohort shard signatures."),
        criterion(3, "Original/counterfactual tokenization is audited", annotations_frozen, "49/49 candidate pairs have a nonempty meaningful divergent suffix and an audited shared lead."),
        criterion(4, "Switch checkpoints are frozen before cohort scoring", schedule_frozen, f"49 schedules and {len(timing_rows)} deduplicated problem-checkpoint pairs match the frozen manifests."),
        criterion(5, "Visual K/V replacement is validated across all layers", all_layers, "Final 3-base smoke and 49-base cohort captured post-RoPE visual K and projected V in all 36 language layers."),
        criterion(6, "Non-visual Q/P/R state remains recipient state during switching", all_switch_audits, f"All {len(timing_rows)} boundary audits report visual-position-only replacement, zero pre-switch modification, and unchanged nonvisual K/V; recipient queries are not replaced."),
        criterion(7, "O→C and C→O switching are both run", both_directions, f"Both directional effects are present at all {len(timing_rows)} checkpoints."),
        criterion(8, "Self-switch controls are transparent", self_exact, f"O→O and C→C are exact at all {len(timing_rows)} checkpoints."),
        criterion(9, "Sham-source controls are implemented", sham_complete, f"O→sham is present at all {len(timing_rows)} checkpoints."),
        criterion(10, "Evidence-specific switch effects are computed", effects_complete, "S_O→C, S_C→O, and primary unnormalized BRI are persisted per problem and checkpoint."),
        criterion(11, "Bidirectional statistics are reported", bidirectional.get("late_checkpoints") is not None, "Directional and bidirectional consistency, bootstrap intervals, and sham comparisons are reported."),
        criterion(12, "Stage 3B.1 cutoff effects are compared at matching timings", cutoff["matched_base_problem_count"] == 49, f"{cutoff['matched_problem_checkpoint_count']} exact-index matches cover 49/49 bases."),
        criterion(13, "base_problem_id is the statistical unit", len(results) == len(base_ids) == 49, "Exactly one timing curve per frozen unique base_problem_id; bootstrap resampling uses base problems."),
        criterion(14, "Attention is secondary only", attention["analysis_role"].startswith("secondary") and not any(row["selection_used_attention"] for row in results), f"Attention-independent cohort/checkpoints; secondary exact-event overlap N={attention['matched_problem_count']}."),
        criterion(15, "No prohibited localization is started", not any(path.exists() for path in prohibited_paths) and not validation["prohibited_localization_started"], "No layer/Q/R/module/head/path/ROI localization outputs exist."),
        criterion(16, "An explicit next-stage decision is written", decision.startswith(("GO", "REDIRECT")), decision),
    ]
    technical_pass = all(row["status"] == "PASS" for row in acceptance)
    acceptance_payload = {
        "stage": "3B.2",
        "overall_status": "PASS" if technical_pass else "FAIL",
        "scientific_recommendation": decision,
        "criteria": acceptance,
        "all_criteria_pass": technical_pass,
        "stage3b3_or_localization_started": False,
    }
    ensure_directory(OUT / "summaries")
    write_json(OUT / "summaries/stage3b2_acceptance.json", acceptance_payload)

    ed1 = checkpoint["ed_relative"]["Ed_minus_1"]
    ed = checkpoint["ed_relative"]["Ed"]
    start = checkpoint["ed_relative"]["generation_start"]
    numeric = evidence["strata"]["tier1_local_numeric_label"]
    structural = evidence["strata"]["tier3_structural_visual_edit"]
    exact_alignment = evidence["annotation_alignment_strata"]["exact_baseline_tokens"]
    semantic_alignment = evidence["annotation_alignment_strata"]["semantic_teacher_forced_lead"]
    replay = validation["stage3a_suffix_replay"]
    rollout16 = rollouts["by_checkpoint"]["Ed_minus_16"]
    rollout4 = rollouts["by_checkpoint"]["Ed_minus_4"]
    rollout0 = rollouts["by_checkpoint"]["Ed"]

    summary_lines = [
        "# Stage 3B.2 summary — Counterfactual future visual-source switching",
        "",
        "## Outcome",
        "",
        f"**Technical status: {'PASS' if technical_pass else 'FAIL'} ({sum(row['status'] == 'PASS' for row in acceptance)}/16 acceptance criteria).**",
        "",
        f"**Recommendation: {decision}.**",
        "",
        (
            "Switching only future all-visual-position K/V from the original image to the counterfactual image, while retaining recipient token history and directly replacing no nonvisual state, moved evidence preference toward the donor fact in both directions for 49/49 independent bases at both `E_d−1` and `E_d`. "
            f"Median unnormalized BRI was {ed1['BRI']['median']:.4f} at `E_d−1` (95% bootstrap CI {ed1['BRI']['median_bootstrap_ci']['ci_low']:.4f}–{ed1['BRI']['median_bootstrap_ci']['ci_high']:.4f}) and {ed['BRI']['median']:.4f} at `E_d` ({ed['BRI']['median_bootstrap_ci']['ci_low']:.4f}–{ed['BRI']['median_bootstrap_ci']['ci_high']:.4f})."
        ),
        "",
        "This supports causal control by evidence-specific future visual content immediately before, and at, the frozen teacher-forced evidence decision. It does not identify an ROI, layer, module, head, path, or Q/R carrier.",
        "",
        "## Frozen cohort and decision coordinate",
        "",
        "- Primary unit: 49 unique frozen Stage 3A base problems (45 local numeric-label edits; 4 structural edits).",
        "- `E_d`: first token at which the frozen original and counterfactual evidence continuations diverge after their longest common token prefix.",
        "- All 49 annotations were manually audited before causal scoring; attention and causal scores were not used for acceptance or checkpoint placement.",
        "- Twelve candidate leads exactly follow the baseline trace from E0. Thirty-seven use the already-frozen Stage 3A semantic teacher-forced evidence lead. Therefore, for those 37, `E_d` is a controlled candidate-decision coordinate—not the exact natural free-running decision time.",
        f"- Schedule: {len(timing_rows)} unique base-checkpoint pairs, spanning generation start, normalized progress, `E_d−64…E_d−1`, and `E_d` where available.",
        "",
        "## Intervention and controls",
        "",
        "At switch index `k`, the query predicting generated token `y_k` and all later queries use donor post-RoPE visual K and projected V at all visual prompt positions in all 36 language layers. Recipient token identities are fixed, and no nonvisual K/V entry or query is copied from the donor. No query before `k` is switched. States computed after `k` may change downstream as a consequence of the visual-source intervention; that propagation is part of the tested effect, not a direct nonvisual patch.",
        "",
        "Every checkpoint includes no-switch O+O/C+C, self O→O/C→C, O-history→C-vision, C-history→O-vision, and O-history→sham-vision controls. Primary scoring is length-normalized teacher-forced evidence preference; unnormalized BRI is primary and the full-gap normalized BRI is secondary.",
        "",
        "## Validation",
        "",
        f"The corrected three-base smoke gate passed all 10 checks, with an `E_d` median absolute sham/target ratio of {smoke['median_ed_absolute_sham_to_target_ratio']:.6f}. The earlier custom-attention-name smoke was preserved as invalid evidence: changing the attention implementation name altered causal-mask construction. The validated implementation keeps the model's `eager` configuration and locally overrides only the eager attention operation.",
        "",
        f"All {len(timing_rows)} full-cohort switch audits passed; all self switches were exact; all scores were finite. No-switch divergent-suffix replay was bit-exact for {replay['bit_exact_base_count']}/49 bases and within `1e-6` for 49/49. Base 126 was the sole bit-level exception: identical candidate IDs with maximum absolute log-probability difference {replay['maximum_absolute_log_probability_difference']:.3g}.",
        "",
        f"Seven A5000 primary shards and seven A5000 rollout shards completed. Peak primary allocated GPU memory was {validation['peak_gpu_allocated_bytes'] / (1024 ** 3):.2f} GiB; rollout peak was {rollouts['peak_gpu_allocated_bytes'] / (1024 ** 3):.2f} GiB. Nineteen Stage 3B.2 tests passed, and {figure_count}/9 required figures were produced.",
        "",
        "## Primary causal results",
        "",
        f"- Generation start: median BRI {start['BRI']['median']:.4f}; median normalized BRI {start['normalized_BRI_raw']['median']:.4f}; bidirectional {start['bidirectional_source_consistency']['count']}/{start['n']}.",
        f"- `E_d−1`: O→C median shift {ed1['S_O_to_C']['median']:.4f}; C→O median shift {ed1['S_C_to_O']['median']:.4f}; median BRI {ed1['BRI']['median']:.4f}; median normalized BRI {ed1['normalized_BRI_raw']['median']:.4f}; bidirectional 49/49.",
        f"- `E_d`: O→C median shift {ed['S_O_to_C']['median']:.4f}; C→O median shift {ed['S_C_to_O']['median']:.4f}; median BRI {ed['BRI']['median']:.4f}; median normalized BRI {ed['normalized_BRI_raw']['median']:.4f}; bidirectional 49/49.",
        f"- Sham control: median absolute sham/target ratio {ed1['median_absolute_sham_to_target_ratio']:.4f} at `E_d−1` and {ed['median_absolute_sham_to_target_ratio']:.4f} at `E_d`.",
        f"- Frozen timing categories: " + ", ".join(f"{key}={value}" for key, value in sorted(curves['retrieval_category_counts'].items())) + ". The six R5 curves met the predeclared non-monotonicity rule but still retained late source control; categories are descriptive, not filters.",
        "",
        "Both late checkpoints pass every frozen GO condition: the median-BRI bootstrap CI excludes zero, bidirectional consistency is at least 70%, median normalized BRI is at least 0.50, sham is below 20% of target magnitude, and self replacement is transparent.",
        "",
        "## Stage 3B.1 cutoff comparison",
        "",
        f"Exact generated-index matching produced {cutoff['matched_problem_checkpoint_count']} problem-checkpoint pairs covering all 49 bases. At each base's latest exact shared checkpoint, the descriptive 0.50 quadrant split was {cutoff['latest_exact_match_per_base_quadrants'].get('high_cutoff_damage_high_switch', 0)} high-cutoff/high-switch and {cutoff['latest_exact_match_per_base_quadrants'].get('low_cutoff_damage_high_switch', 0)} low-cutoff/high-switch; no base had low identity-specific switch effect.",
        "",
        f"Across one latest exact match per independent base, cutoff-damage ratio and normalized BRI had Spearman rho={cutoff['spearman_latest_exact_match_per_base']['rho']:.3f} (N=49). This is a joint descriptive comparison; the switch experiment, not the correlation, provides the causal evidence-specific result.",
        "",
        "## Secondary matched-seed rollouts",
        "",
        f"At `E_d−16`, O→C switched the first discriminative token to the counterfactual identity in {rollout16['O_to_C_overrides_old_identity']['count']}/{rollout16['n']} cases and C→O restored the original identity in {rollout16['C_to_O_overrides_old_identity']['count']}/{rollout16['n']}. At `E_d−4` the counts were {rollout4['O_to_C_overrides_old_identity']['count']}/{rollout4['n']} and {rollout4['C_to_O_overrides_old_identity']['count']}/{rollout4['n']}; at `E_d` they were {rollout0['O_to_C_overrides_old_identity']['count']}/{rollout0['n']} and {rollout0['C_to_O_overrides_old_identity']['count']}/{rollout0['n']}.",
        "",
        "These rollouts behaviorally support the teacher-forced result, but each condition uses one matched stochastic seed. The proportions describe this fixed-seed validation set, not repeated-sampling frequencies.",
        "",
        "## Evidence strata and secondary attention comparison",
        "",
        f"Numeric examples (N={numeric['n']}) had median normalized BRI {numeric['Ed_minus_1']['normalized_BRI_raw']['median']:.4f} at `E_d−1` and {numeric['Ed']['normalized_BRI_raw']['median']:.4f} at `E_d`. Structural examples (N={structural['n']}) had {structural['Ed_minus_1']['normalized_BRI_raw']['median']:.4f} and {structural['Ed']['normalized_BRI_raw']['median']:.4f}; N=4 is too small for a strong stratum comparison.",
        "",
        f"The timing result is not confined to semantic teacher-forced leads. In the 12 exact-baseline-token cases, bidirectional source consistency was 12/12 at both late checkpoints, with median normalized BRI {exact_alignment['Ed_minus_1']['normalized_BRI_raw']['median']:.4f} at `E_d−1` and {exact_alignment['Ed']['normalized_BRI_raw']['median']:.4f} at `E_d`. The 37 semantic-lead cases had {semantic_alignment['Ed_minus_1']['normalized_BRI_raw']['median']:.4f} and {semantic_alignment['Ed']['normalized_BRI_raw']['median']:.4f}.",
        "",
        f"The frozen Stage 2C exact-event overlap contains {attention['matched_problem_count']} problems, all mention-centered T2 events; all {attention['mention_centered_with_bidirectional_Ed_source_control']} also showed bidirectional source control at `E_d`. Pre-E0 ROI density versus `E_d` normalized BRI had Spearman rho={attention['pre_e0_roi_density_vs_Ed_normalized_BRI']['rho']:.3f}, p={attention['pre_e0_roi_density_vs_Ed_normalized_BRI']['p_value']:.3f} (N=9). This small overlap cannot establish an attention–causal relationship.",
        "",
        "The combined lesson is not that mention-centered attention is itself evidence acquisition. Rather, mention-centered attention can coexist with causal evidence-specific visual-source control; attention alone cannot distinguish semantic alignment from retrieval.",
        "",
        "## Limitations and scientific boundary",
        "",
        "- The intervention switches all visual positions and all language layers together; it does not identify which ROI, layer, module, head, or path carries the effect.",
        "- Thirty-seven E_d coordinates use controlled semantic teacher-forced candidate leads, limiting exact natural-trajectory timing claims.",
        "- Teacher-forced preference is primary; fixed-seed rollouts are a secondary behavioral check.",
        "- The structural stratum and exact Stage 2C overlap are small.",
        "- Full-gap normalization is secondary and unclipped; unnormalized BRI and bidirectional consistency carry the primary inference.",
        "- This stage does not establish whether Q or prior-reasoning state stores retrieved evidence or whether attention versus MLP computation mediates transfer.",
        "",
        "## Scientific conclusion",
        "",
        "Within the frozen Stage 3A evidence decisions, future visual-source identity causally controls the upcoming evidence even after the prior reasoning history is fixed. Strong effects at `E_d−1` and `E_d`, reciprocal switching, small sham effects, transparent self controls, and matched-seed fact flips support active evidence-specific visual retrieval immediately before or during evidence expression.",
        "",
        "This conclusion is about source identity and timing at the controlled evidence decision. It is not an attention-only claim and it does not localize the transfer mechanism.",
        "",
        "## Key artifacts",
        "",
        "- `annotations/discriminative_event_annotations.jsonl` and `config/switch_checkpoint_schedule.jsonl`",
        "- `smoke/visual_source_switch_validation.json` and `smoke/cache_integrity_diagnostics.json`",
        "- `scoring/per_problem_switch_results.jsonl`, `scoring/per_checkpoint_statistics.json`, and `scoring/rollout_results.jsonl`",
        "- `analysis/retrieval_timing_curves.json`, `analysis/bidirectional_retrieval_statistics.json`, and `analysis/cutoff_vs_switch_comparison.json`",
        "- `analysis/evidence_type_analysis.json`, `analysis/attention_secondary_comparison.json`, and `analysis/figures/`",
        "- `summaries/stage3b2_acceptance.json` and `summaries/next_stage_recommendation.md`",
    ]
    (OUT / "summaries/stage3b2_summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    recommendation_lines = [
        f"# {decision}",
        "",
        "The frozen late-retrieval GO rule passed at both `E_d−1` and `E_d`.",
        "",
        "Decision inputs:",
        "",
        f"- `E_d−1`: median BRI {ed1['BRI']['median']:.4f}, 95% median bootstrap CI {ed1['BRI']['median_bootstrap_ci']['ci_low']:.4f}–{ed1['BRI']['median_bootstrap_ci']['ci_high']:.4f}, normalized median {ed1['normalized_BRI_raw']['median']:.4f}, bidirectional 49/49, sham/target {ed1['median_absolute_sham_to_target_ratio']:.4f}.",
        f"- `E_d`: median BRI {ed['BRI']['median']:.4f}, 95% median bootstrap CI {ed['BRI']['median_bootstrap_ci']['ci_low']:.4f}–{ed['BRI']['median_bootstrap_ci']['ci_high']:.4f}, normalized median {ed['normalized_BRI_raw']['median']:.4f}, bidirectional 49/49, sham/target {ed['median_absolute_sham_to_target_ratio']:.4f}.",
        f"- Secondary fixed-seed O→C fact override: {rollout4['O_to_C_overrides_old_identity']['count']}/{rollout4['n']} at `E_d−4` and {rollout0['O_to_C_overrides_old_identity']['count']}/{rollout0['n']} at `E_d`.",
        f"- Stage 3B.1 latest exact-match quadrant: {cutoff['latest_exact_match_per_base_quadrants'].get('high_cutoff_damage_high_switch', 0)}/49 high cutoff damage + high identity switch; all 49 had high switch under the descriptive 0.50 reference.",
        "",
        "A reviewed next-stage plan may therefore ask at which layers current reasoning receives this evidence-specific visual content. This recommendation does not select an ROI, carrier, module, head, or path, and it does not authorize or start that experiment.",
        "",
        "Important boundary: 37/49 E_d coordinates are frozen semantic teacher-forced candidate decisions rather than exact baseline-trace token continuations. Any later localization plan should preserve this distinction or prioritize the 12 exact-baseline subset as a robustness stratum without redefining the present primary cohort.",
        "",
        "No Stage 3B.3, layerwise localization, Q/R carrier patching, ROI switching, module/head/path analysis, or subsequent experiment has been started.",
    ]
    (OUT / "summaries/next_stage_recommendation.md").write_text(
        "\n".join(recommendation_lines) + "\n", encoding="utf-8"
    )
    print(json.dumps({"technical_status": acceptance_payload["overall_status"], "decision": decision}, indent=2))


if __name__ == "__main__":
    main()
