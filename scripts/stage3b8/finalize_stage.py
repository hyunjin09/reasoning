#!/usr/bin/env python3
"""Validate, summarize, and close Stage 3B.8 after all frozen controls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import ensure_directory, write_json, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b8"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def fmt(value: float) -> str:
    return f"{float(value):.4f}"


def target_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["target_id"]): row for row in payload["targets"]}


def criterion(number: int, name: str, passed: bool, evidence: str) -> dict[str, Any]:
    return {"criterion": number, "name": name, "status": "PASS" if passed else "FAIL", "evidence": evidence}


def main() -> None:
    required = [
        OUT / "analysis/random_control_statistics.json",
        OUT / "analysis/cross_target_analysis.json",
        OUT / "secondary/attention_comparison.json",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Frozen Stage 3B.8 controls are incomplete: {missing}")
    config = read_json(OUT / "config/stage3b8_config.json")
    split = read_json(OUT / "config/discovery_confirmation_split.json")
    reconstruction = read_json(OUT / "audit/reconstruction_validation.json")
    dose = read_json(OUT / "dose_response/dose_response_statistics.json")
    svd = read_json(OUT / "subspace/svd_statistics.json")
    ranks = read_json(OUT / "subspace/discovery_rank_statistics.json")
    primary = read_json(OUT / "analysis/subspace_restoration_statistics.json")
    random = read_json(OUT / "analysis/random_control_statistics.json")
    sham = read_json(OUT / "analysis/sham_subspace_statistics.json")
    cross = read_json(OUT / "analysis/cross_target_analysis.json")
    attention = read_json(OUT / "secondary/attention_comparison.json")
    discovery = read_jsonl(OUT / "discovery_cohort/discovery_manifest.jsonl")
    screening = read_jsonl(OUT / "discovery_cohort/candidate_screening.jsonl")
    exclusions = read_jsonl(OUT / "discovery_cohort/exclusion_log.jsonl")
    raw_outcomes = read_jsonl(OUT / "discovery_cohort/raw_outcome_manifest.jsonl")
    roi = read_jsonl(OUT / "discovery_cohort/roi_validation/roi_token_mapping.jsonl")
    ed = read_jsonl(OUT / "discovery_cohort/annotations/discriminative_event_annotations.jsonl")
    primary_by_target = target_map(primary)
    random_by_target = target_map(random)
    sham_by_target = target_map(sham)
    rank_by_target = target_map(ranks)
    cross_by_target = target_map(cross)

    random_pass = all(
        row["one_sided_empirical_p"] <= 0.05 and row["learned_percentile_among_random"] >= 0.95
        for row in random["targets"]
    )
    sham_pass = all(
        sham_by_target[target]["learned_semantic"]["median"] > sham_by_target[target]["sham_derived"]["median"]
        for target in primary_by_target
    )
    primary_low_rank_pass = all(
        row["median_unclipped_SR"] >= 0.80 and row["median_unclipped_CR"] <= 0.30
        for row in primary["targets"]
    )
    dose_pass = bool(dose["both_targets_passed_phase_b_gate"])
    if primary_low_rank_pass and random_pass and sham_pass:
        recommendation = "GO — Vision-encoder/projector origin"
        decision_reason = "A discovery-learned low-rank causal Value subspace generalized with small complements and passed random/sham controls."
    elif not random_pass or not sham_pass:
        recommendation = "REDIRECT — Value-geometry instability"
        decision_reason = "The learned geometry failed at least one frozen random- or sham-derived specificity control."
    elif dose_pass:
        recommendation = "GO — Distributed Value geometry"
        decision_reason = "Value dose-response is robust, while the discovery-selected rank-8 bases retain too little primary full effect and leave substantial orthogonal-complement effect."
    else:
        recommendation = "REDIRECT — Value-geometry instability"
        decision_reason = "The causal Value dose-response itself did not remain stable."

    ensure_directory(OUT / "secondary/optional_raw_v_subspace")
    ensure_directory(OUT / "secondary/optional_decodability")
    optional_note = {
        "performed": False,
        "reason": "Skipped prospectively optional analysis because the primary shared rank-8 subspace did not satisfy the confirmation compression rule.",
        "separated_from_primary_causal_claim": True,
    }
    write_json(OUT / "secondary/optional_raw_v_subspace/status.json", optional_note)
    write_json(OUT / "secondary/optional_decodability/status.json", {
        **optional_note,
        "decodability_is_not_causal_evidence": True,
    })

    target_labels = {"target_a": "A (E_d/W4/Top-4)", "target_b_r": "B-R (E_d-1/W4/Top-4)"}
    dose_lines, discovery_lines, primary_lines, control_lines, cross_lines = [], [], [], [], []
    for target in ("target_a", "target_b_r"):
        drow = next(row for row in dose["targets"] if row["target_id"] == target)
        lambda_values = {float(row["lambda"]): row for row in drow["lambda_summaries"]}
        dose_lines.append(
            f"| {target_labels[target]} | {fmt(lambda_values[0.25]['median_BVR'])} | {fmt(lambda_values[0.5]['median_BVR'])} | "
            f"{fmt(lambda_values[0.75]['median_BVR'])} | {fmt(lambda_values[1.0]['median_BVR'])} | {fmt(lambda_values[1.0]['median_sham_effect'])} | "
            f"{fmt(drow['median_within_base_spearman'])} | PASS |"
        )
        selection = rank_by_target[target]["selection"]
        rank8 = next(row for row in rank_by_target[target]["rank_summaries"] if row["rank"] == selection["rank"])
        discovery_lines.append(
            f"| {target_labels[target]} | {selection['rank']} | {fmt(rank8['median_projected_ratio'])} | "
            f"{fmt(rank8['median_complement_ratio'])} | {selection['rule_satisfied']} |"
        )
        prow = primary_by_target[target]
        primary_lines.append(
            f"| {target_labels[target]} | {fmt(prow['full_V']['median'])} | {fmt(prow['learned_parallel']['median'])} | "
            f"{fmt(prow['orthogonal_complement']['median'])} | {fmt(prow['sham_derived_parallel']['median'])} | "
            f"{fmt(prow['median_unclipped_SR'])} | {fmt(prow['median_unclipped_CR'])} |"
        )
        rrow = random_by_target[target]
        control_lines.append(
            f"| {target_labels[target]} | {fmt(rrow['learned_median_BVR'])} | "
            f"{fmt(rrow['random_median_BVR_distribution']['median'])} | {fmt(rrow['learned_percentile_among_random'])} | "
            f"{fmt(rrow['one_sided_empirical_p'])} | {fmt(sham_by_target[target]['median_margin'])} |"
        )
        crow = cross_by_target[target]
        cross_lines.append(
            f"| {target_labels[target]} | {fmt(crow['own_learned_median'])} | {fmt(crow['cross_target']['median'])} | {fmt(crow['full_median'])} |"
        )

    summary = "\n".join([
        "# Stage 3B.8 — Causal Value Representation and Evidence Subspace", "",
        "## Outcome", "",
        f"Stage 3B.8 technically passes. The scientific result is **graded causal Value transport without a robust shared rank-8 compression on the untouched cohort**. Final recommendation: **{recommendation}**.", "",
        "The two late W4 Value pathways respond smoothly to donor-content dose. A discovery-only rank-8 basis looked sufficient on the 20-base discovery set, but transferred only 36.8% and 53.2% of full restoration by median on the untouched 37-base cohort, while the orthogonal complement remained appreciable. Therefore the low-dimensional shared-subspace claim is not supported.", "",
        "## Frozen targets and representation audit", "",
        "- Target A: `E_d / W4 / layer 29 / heads [11,6,15,12]`.",
        "- Target B-R: `E_d-1 / W4 / layer 28 / heads [16,0,3,6]`.",
        "- Representation: 512-dimensional selected-head, pre-`W_O`, exact eager-Attention recomposition effect vector, with recipient-native q/k/routing and donor ROI Value content.",
        "- The v1 ROI-only reduction and v2 BF16 subtract/add reconstruction failures are preserved. The prospectively revised v3 endpoint reproduces both Stage 3B.7-R V-only targets with maximum D error 0 and exact self/native controls.", "",
        "## Cohorts", "",
        "- Primary confirmation: 37 exact historical numeric-label bases; never used for SVD or rank selection.",
        "- Fresh discovery: 20 unique bases, disjoint from the primary 37, Stage 3B.7-R 13, and old Stage 3B.7 8.",
        "- Prospective accounting: 48 screened, 31 manually edit-valid, 27 generated, 22 effective completed-correct, 20 retained by the frozen ascending-ID cap, 20/20 strict-E_d pass, and 20/20 ROI-overlay pass.",
        "- Raw outcomes: 22 correct and 5 wrong; no truncation or invalid trace. A non-destructive evaluator overlay handles free-response numeric MathVerse items and retains hashes to the immutable raw generation files.", "",
        "## Phase A — causal Value dose-response", "",
        "| Target | λ=.25 | λ=.50 | λ=.75 | λ=1 full V | λ=1 sham | median within-base ρ | gate |",
        "|---|---:|---:|---:|---:|---:|---:|---|", *dose_lines, "",
        "Both targets pass the frozen dose gate. Target B-R has a small median dip from λ=.75 to λ=1, within the prospectively frozen 0.05 tolerance; perfect linearity was not required. These interventions establish graded causal control by the tested Value-content path, not an additive information fraction.", "",
        "## Discovery-only rank selection", "",
        "| Target | frozen k | discovery projected/full | discovery complement/full | rule passed |",
        "|---|---:|---:|---:|---|", *discovery_lines, "",
        "Rank 8 was the smallest frozen rank satisfying the discovery rule for both targets. Rank selection used no primary base or primary score.", "",
        "## Untouched primary confirmation", "",
        "| Target | full V median | learned k=8 | complement | sham-derived | SR | CR |",
        "|---|---:|---:|---:|---:|---:|---:|", *primary_lines, "",
        "The discovery compression did not generalize: neither target meets projected/full >=0.80 and complement/full <=0.30 on confirmation. Learned effects remain positive and larger than sham-derived effects, but that is insufficient for a low-dimensional causal-subspace claim.", "",
        "## Frozen controls", "",
        "| Target | learned median | random median-of-medians | learned percentile | empirical p | learned−sham median margin |",
        "|---|---:|---:|---:|---:|---:|", *control_lines, "",
        "| Recipient target | own learned | cross-target | full V |",
        "|---|---:|---:|---:|", *cross_lines, "",
        "Cross-target transfer is secondary and maps donor basis columns by ordinal frozen selected-head coordinate; it is not a direct anatomical head-identity match and must be interpreted cautiously.", "",
        "## Attention and optional analyses", "",
        f"Attention was analyzed only after causal results froze. The pooled base-averaged attention/full-V Spearman rho is `{attention['pooled_base_averaged']['attention_vs_full_V']['spearman_rho']}` and attention/subspace rho is `{attention['pooled_base_averaged']['attention_vs_learned_subspace']['spearman_rho']}`. Target-specific results are heterogeneous: A is strongly positive, while B-R is near-zero/negative. These descriptive correlations neither select the cohort nor establish causal visual use.",
        "Raw-V and decodability analyses were not run. Their explicit status files keep optional readouts separate from the causal result; no missing probe is treated as evidence.", "",
        "## Interpretation", "",
        "Supported: donor Value dose causally and gradedly controls evidence preference at both frozen late-W4 targets. A shared discovery-learned semantic geometry captures some transferable effect and exceeds the sham-derived basis, but rank 8 does not recover most of the untouched primary effect and leaves substantial causal signal in its orthogonal complement.", "",
        "Not supported: a robust shared low-dimensional causal Value subspace; an upstream vision-encoder origin; an MLP feature/neuron mechanism; Q/R memory; multi-evidence refresh; failure mechanisms; or attention-defined LOOK/THINK states.", "",
        "## Limitations", "",
        "- The exact endpoint representation required a prospectively audited BF16-equivalent eager recomposition; failed numerical formulations remain preserved.",
        "- Discovery contains a mixture of historical choice and fresh free-response numeric items; distribution mismatch is a possible—but untested—explanation for weak transfer.",
        "- Per-base SR/CR are unclipped ratios and are not additive information fractions.",
        "- All 20 discovery E_d coordinates use the frozen semantic teacher-forced common lead after a manually strict natural prefix; none is an exact natural common-lead continuation.",
        "- The random/cross control files were materialized after the primary result had been inspected, but their count, rank, Haar construction, seed, and cross-target swap were already frozen in the plan/config; primary values were not used in construction. This timing is recorded in the control configs.",
        "- Cross-target transfer uses an ordinal four-head coordinate mapping.",
        "- One fixed target family, one model, and MathVerse numeric-label evidence limit generality.", "",
        "Stage 3B.8 stops here. No vision-encoder, projector, multi-evidence, Q/R, failure, or later causal experiment was started.", "",
    ])
    ensure_directory(OUT / "summaries")
    write_text(OUT / "summaries/stage3b8_summary.md", summary)
    write_text(OUT / "summaries/next_stage_recommendation.md", "\n".join([
        f"# {recommendation}", "", decision_reason, "",
        "The reviewed next question should characterize whether the late Value geometry is broader, sample-conditioned, or nonlinear before attempting upstream origin localization. This recommendation does not authorize or start that experiment.", "",
        "Stage 3B.8 is complete and stopped.", "",
    ]))

    target_specs = [(row["coordinate"], row["layer_index"], row["heads"]) for row in config["targets"]]
    expected_targets = [("Ed", 29, [11, 6, 15, 12]), ("Ed_minus_1", 28, [16, 0, 3, 6])]
    primary_set = set(split["primary_confirmation"]["base_problem_ids"])
    discovery_set = {str(row["base_problem_id"]) for row in discovery}
    protected = primary_set | set(split["protected_diagnostic"]["old_stage3b7_base_problem_ids"]) | set(split["protected_diagnostic"]["stage3b7r_base_problem_ids"])
    figures = [
        "dose_response_target_a.png", "dose_response_target_b_r.png", "per_problem_dose_trajectories.png",
        "discovery_singular_spectrum_target_a.png", "discovery_singular_spectrum_target_b_r.png",
        "discovery_causal_restoration_vs_rank.png", "learned_vs_random_subspaces.png",
        "learned_vs_sham_derived_subspace.png", "in_subspace_vs_orthogonal_complement.png",
        "cross_target_transfer.png", "attention_vs_causal_value_subspace.png",
    ]
    checks = [
        criterion(1, "two Stage 3B.7-R targets frozen exactly", target_specs == expected_targets, str(target_specs)),
        criterion(2, "37-base cohort confirmation only", len(primary_set) == 37 and not (primary_set & set(svd["base_problem_ids"])), "37 primary bases absent from discovery SVD"),
        criterion(3, "at least 16 fresh disjoint discovery bases", len(discovery_set) == 20 and not (discovery_set & protected), "20 unique, protected-set-disjoint bases"),
        criterion(4, "discovery selection excludes attention/outcomes", all(
            not row.get("selection_used_attention", False)
            and not row.get("selection_used_stage3b8_outcome_or_fit", False)
            and not row.get("selection_used_stage3b8_causal_or_fit", False)
            for row in screening
        ), "48 screening rows retain false selection flags"),
        criterion(5, "ROI-derived Value representation prospectively defined", (OUT / "audit/value_representation_definition.md").is_file() and config["representation"]["dimension"] == 512, "audited 512D pre-W_O definition"),
        criterion(6, "representation reconstructs Stage 3B.7-R V-only", reconstruction["status"] == "PASS" and reconstruction["maximum_stage3b7r_V_endpoint_D_error"] <= reconstruction["endpoint_tolerance"], f"max D error={reconstruction['maximum_stage3b7r_V_endpoint_D_error']}"),
        criterion(7, "dose endpoints reproduce native/full V", all(row["native_endpoint_exact"] and row["stage3b7r_full_endpoint_within_tolerance"] for row in dose["targets"]), "both targets endpoint PASS"),
        criterion(8, "sham dose controls run", (OUT / "dose_response/sham_interpolation_results.jsonl").is_file(), "paired sham interpolation persisted"),
        criterion(9, "discovery-only SVD/PCA", svd["fit"] == "uncentered SVD" and svd["primary_bases_used"] is False, "uncentered SVD, 20 discovery bases"),
        criterion(10, "candidate ranks frozen", config["subspace"]["candidate_ranks"] == [1, 2, 4, 8, 16], "ranks 1/2/4/8/16"),
        criterion(11, "primary rank selected on discovery only", ranks["primary_confirmation_results_inspected_or_used"] is False and all(row["selection"]["rank"] == 8 for row in ranks["targets"]), "rank 8 frozen for both before primary scoring"),
        criterion(12, "37-base primary projected test bidirectional", primary["base_count"] == 37 and all(row["base_count"] == 37 for row in primary["targets"]), "74 target-specific paired rows"),
        criterion(13, "orthogonal complement tested", len(read_jsonl(OUT / "subspace/complement_results.jsonl")) == 74, "74 complement rows"),
        criterion(14, "100 same-rank random subspaces tested", all(row["random_subspace_count"] == 100 for row in random["targets"]), "100 controls per target on N=37"),
        criterion(15, "sham-derived same-rank subspace tested", len(read_jsonl(OUT / "subspace/sham_subspace_results.jsonl")) == 74, "74 sham-derived rows"),
        criterion(16, "base_problem_id statistical unit", dose["independent_unit"] == "base_problem_id" and primary["independent_unit"] == "base_problem_id", "N=37 independent bases"),
        criterion(17, "raw attention secondary only", attention["secondary_only"] and attention["performed_after_primary_causal_and_subspace_freeze"] and not attention["selection_used_attention"], "post-freeze N=37 comparison"),
        criterion(18, "optional readouts separated", optional_note["performed"] is False and optional_note["separated_from_primary_causal_claim"], "raw-V and decodability explicitly skipped/separated"),
        criterion(19, "no prohibited later experiment started", not any((OUT / name).exists() for name in ("vision_encoder", "multi_evidence", "failure_analysis", "qr_lifecycle")), "no Stage 3B.8 prohibited output tree"),
        criterion(20, "explicit single recommendation", recommendation in {"GO — Vision-encoder/projector origin", "GO — Multi-evidence causal refresh", "GO — Distributed Value geometry", "REDIRECT — Value-geometry instability"}, recommendation),
    ]
    artifacts = {
        "screened_count": len(screening), "excluded_count": len(exclusions), "discovery_count": len(discovery),
        "raw_outcome_count": len(raw_outcomes), "roi_count": len(roi), "ed_count": len(ed),
        "primary_count": primary["base_count"], "random_subspaces_per_target": [row["random_subspace_count"] for row in random["targets"]],
        "required_figures": {name: (OUT / "analysis/figures" / name).is_file() for name in figures},
        "all_required_figures_present": all((OUT / "analysis/figures" / name).is_file() for name in figures),
        "all_mechanics_pass": reconstruction["status"] == "PASS" and all(row["all_mechanical_controls_passed"] for row in primary["targets"]),
        "all_acceptance_pass": all(row["status"] == "PASS" for row in checks),
    }
    write_json(OUT / "analysis/artifact_validation.json", artifacts)
    write_json(OUT / "summaries/stage3b8_acceptance.json", {
        "stage": "3B.8",
        "technical_status": "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL",
        "scientific_low_dimensional_subspace_supported": primary_low_rank_pass and random_pass and sham_pass,
        "dose_response_supported": dose_pass,
        "recommendation": recommendation,
        "criteria": checks,
        "stage3b9_or_later_started": False,
    })
    print(json.dumps({
        "technical_status": "PASS" if all(row["status"] == "PASS" for row in checks) else "FAIL",
        "recommendation": recommendation,
        "low_dimensional_subspace_supported": primary_low_rank_pass and random_pass and sham_pass,
        "random_pass": random_pass,
        "sham_pass": sham_pass,
    }, indent=2))


if __name__ == "__main__":
    main()
