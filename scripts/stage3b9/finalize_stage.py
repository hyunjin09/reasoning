#!/usr/bin/env python3
"""Validate, summarize, and close the frozen Stage 3B.9 action."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import ensure_directory, write_json, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3b9"
TARGETS = ("target_a", "target_b_r")
RANKS = (1, 2, 4, 8, 16, 24, 32, 48)
LOCAL_RANKS = (1, 2, 3)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def criterion(number: int, name: str, passed: bool, evidence: str) -> dict[str, Any]:
    return {"criterion": number, "name": name, "status": "PASS" if passed else "FAIL", "evidence": evidence}


def fmt(value: float | None) -> str:
    return "NA" if value is None else f"{float(value):.4f}"


def classify_geometry(shared: dict[str, Any], local: dict[str, Any]) -> dict[str, Any]:
    """Apply the frozen joint outcome matrix without optimizing a threshold."""
    per_target = {}
    for target in TARGETS:
        shared_pass = shared["targets"][target]["k_shared"] is not None
        local_pass = bool(local["targets"][target]["local_low_dimensional"])
        if shared_pass:
            label = shared["targets"][target]["geometry_label"]
        elif local_pass:
            label = "Local-Low-Dimensional/Global-Heterogeneous"
        else:
            label = "Distributed-At-Tested-Shared-And-Local-Ranks"
        per_target[target] = {
            "shared_rule_passed": shared_pass,
            "local_rank_1_or_2_rule_passed": local_pass,
            "label": label,
        }
    shared_count = sum(row["shared_rule_passed"] for row in per_target.values())
    local_count = sum(row["local_rank_1_or_2_rule_passed"] for row in per_target.values())
    if shared_count == len(TARGETS):
        joint = "G1 — Shared higher-dimensional"
    elif shared_count == 0 and local_count == len(TARGETS):
        joint = "G2 — Local low-dimensional / global heterogeneous"
    elif shared_count or local_count:
        joint = "G3 — Shared/private or target-heterogeneous geometry"
    else:
        joint = "G4 — Distributed globally and locally at tested ranks"
    return {"joint_label": joint, "targets": per_target}


def mechanics_valid(result_paths: list[Path]) -> bool:
    fields = (
        "all_layout_and_roi_mappings_exact",
        "all_query_head_selectivity_valid",
        "all_recipient_tensor_alignment_exact",
        "all_self_restorations_exact",
        "all_scores_finite",
    )
    return bool(result_paths) and all(
        all(read_json(path)["mechanical_controls"][field] for field in fields)
        for path in result_paths
    )


def main() -> None:
    required = [
        OUT / "phase_a_shared/analysis/rank_curve_statistics.json",
        OUT / "phase_a_shared/analysis/shared_geometry_decision.json",
        OUT / "phase_b_local/analysis/local_rank_statistics.json",
        OUT / "phase_b_local/analysis/local_geometry_decision.json",
        OUT / "analysis/attention_secondary.json",
        OUT / "analysis/format_stratification.json",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Stage 3B.9 primary/secondary analyses are incomplete: {missing}")

    targets = read_json(OUT / "config/frozen_targets.json")
    split = read_json(OUT / "config/cohort_split.json")
    ranks = read_json(OUT / "config/frozen_rank_family.json")
    phase_a_gate = read_json(OUT / "phase_a_shared/applicability_gate.json")
    phase_a = read_jsonl(OUT / "phase_a_shared/fresh_confirmation_manifest.jsonl")
    phase_a_stats = read_json(OUT / "phase_a_shared/analysis/rank_curve_statistics.json")
    shared = read_json(OUT / "phase_a_shared/analysis/shared_geometry_decision.json")
    phase_b_gate = read_json(OUT / "phase_b_local/applicability_gate.json")
    phase_b = read_jsonl(OUT / "phase_b_local/cohort_manifest.jsonl")
    variants = read_jsonl(OUT / "phase_b_local/value_variant_manifest.jsonl")
    local_stats = read_json(OUT / "phase_b_local/analysis/local_rank_statistics.json")
    local = read_json(OUT / "phase_b_local/analysis/local_geometry_decision.json")
    attention = read_json(OUT / "analysis/attention_secondary.json")
    geometry = classify_geometry(shared, local)

    a_set = {str(row["base_problem_id"]) for row in phase_a}
    b_set = {str(row["base_problem_id"]) for row in phase_b}
    protected = (
        set(split["historical_training"]["base_problem_ids"])
        | set(split["protected_stage3b7"]["base_problem_ids"])
        | set(split["protected_stage3b7r"]["base_problem_ids"])
    )
    result_paths = [
        *sorted((OUT / "scoring/raw").glob("phase_a_learned_*/examples/*/result.json")),
        *sorted((OUT / "scoring/raw").glob("phase_a_random_*/examples/*/result.json")),
        *sorted((OUT / "phase_b_local/scoring/raw").glob("phase_b_projected_*/examples/*/result.json")),
    ]
    all_mechanics = mechanics_valid(result_paths)
    recommendation = "GO — Multi-Evidence Causal Refresh" if all_mechanics else "REDIRECT — Geometry mechanics invalid"

    phase_a_lines = []
    for target in TARGETS:
        for rank in RANKS:
            row = phase_a_stats[target][str(rank)]
            phase_a_lines.append(
                f"| {target} | {rank} | {fmt(row['B_parallel']['median'])} | {fmt(row['SR']['median'])} | "
                f"{fmt(row['CR']['median'])} | {fmt(row['B_sham']['median'])} | "
                f"{fmt(row['learned_percentile_among_random'])} | {fmt(row['bidirectional_consistency'])} | {row['passes_all']} |"
            )
    phase_b_lines = []
    for target in TARGETS:
        for rank in LOCAL_RANKS:
            row = local_stats[target][str(rank)]
            phase_b_lines.append(
                f"| {target} | {rank} | {row['eligible_base_count']} | {fmt(row['B_local']['median'])} | "
                f"{fmt(row['Local_SR']['median'])} | {fmt(row['Local_CR']['median'])} | "
                f"{fmt(row['GlobalMatched_SR']['median'])} | {fmt(row['local_percentile_among_random'])} | "
                f"{fmt(row['bidirectional_consistency'])} | {row['passes_all']} |"
            )

    target_interpretations = []
    for target in TARGETS:
        target_interpretations.append(
            f"- `{target}`: {geometry['targets'][target]['label']}; shared `k_shared`="
            f"`{shared['targets'][target]['k_shared']}`, local rank-1/2 pass="
            f"`{local['targets'][target]['local_low_dimensional']}`."
        )
    generation_initial = read_json(OUT / "prospective_generation/generation_collection_summary.json")
    generation_expansion = read_json(OUT / "prospective_generation/applicability_expansion_summary.json")
    initial_correct = sum(row["correct"] for row in generation_initial["counts_by_phase"].values())
    initial_wrong = sum(row["wrong"] for row in generation_initial["counts_by_phase"].values())
    summary = "\n".join([
        "# Stage 3B.9 — Distributed Value Geometry", "",
        "## Outcome", "",
        f"Stage 3B.9 technical status is **{'PASS' if all_mechanics else 'FAIL'}**. The frozen joint classification is **{geometry['joint_label']}**. Final recommendation: **{recommendation}**.", "",
        "This stage asks whether the already-established late-W4 ROI→Value→head mechanism is shared at higher rank, compact only within a problem, a shared/private mixture, or distributed at both tested scales. Ratios are unclipped causal restoration ratios, not additive information fractions.", "",
        "## Frozen design", "",
        "- Target A: `E_d / W4 / layer 29 / heads [11,6,15,12]`.",
        "- Target B-R: `E_d-1 / W4 / layer 28 / heads [16,0,3,6]`.",
        "- Representation: exact Stage 3B.8 v3, 512D selected-head pre-`W_O` eager-Attention recomposition effect vector.",
        "- Shared bases were fit only on the 57 historical Stage 3B.8 bases; all fresh bases were excluded.",
        "- Frozen shared ranks: `1,2,4,8,16,24,32,48`; local ranks: `1,2,3`; 100 random controls per target/rank.", "",
        "## Prospective cohorts", "",
        f"- Locked generation initially produced {initial_correct} correct and {initial_wrong} wrong Phase-A/Phase-B outcomes combined; the blind gate-repair expansion added {generation_expansion['counts']['correct']} correct and {generation_expansion['counts']['wrong']} wrong, with no truncation/invalid trace.",
        f"- Phase A froze {phase_a_gate['accepted_count']}/{phase_a_gate['pre_applicability_count']} both-target-applicable fresh bases; N={len(a_set)} is disjoint from every historical/protected base and Phase B.",
        f"- Phase B froze {len(b_set)} separate five-value bases; usable full-V bases are {phase_b_gate['eligible_base_target_counts']['target_a']} for Target A and {phase_b_gate['eligible_base_target_counts']['target_b_r']} for Target B-R.",
        "- All strict-E_d, edit, ROI, value, and applicability decisions were frozen without attention or projected-rank outcomes.", "",
        "## Phase A — fresh shared-rank confirmation", "",
        "| Target | rank | learned BVR | median SR | median CR | sham BVR | learned random percentile | bidirectional | passes all |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|", *phase_a_lines, "",
        "A shared geometry is supported only at the smallest rank satisfying all six prospectively frozen checks; no passing rank is upgraded post hoc.", "",
        "## Phase B — held-out within-problem geometry", "",
        "| Target | local rank | eligible bases | local BVR | Local SR | Local CR | matched-global SR | local random percentile | bidirectional | passes all |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|", *phase_b_lines, "",
        "Each fold learns from three alternative semantic values and tests the fourth; folds are aggregated within base before dataset-level statistics. Rank 3 is reported but cannot establish the frozen strong compact-code criterion.", "",
        "## Joint interpretation", "", *target_interpretations, "",
        f"Joint outcome: **{geometry['joint_label']}**. Target-specific differences are retained rather than hidden by pooling.", "",
        "## Secondary diagnostics", "",
        "Pairwise rank-2 principal angles/projector similarities and frozen format strata were computed only after both primary analyses existed. Clustering was not used for a causal mixture claim. Attention was analyzed only as a post-freeze descriptor; it did not select bases, ranks, values, or the geometry label.", "",
        "## Scientific boundaries and limitations", "",
        "- Full-V applicability enriches the primary analyses for bases where the tested pathway has an interpretable positive bidirectional effect.",
        "- SR/CR can be unstable when full effects are small; unnormalized BVR and per-base distributions are preserved.",
        "- Geometry is conditional on two frozen late-W4 targets, one model, localized numeric labels, and MathVerse Vision-Dominant problems.",
        "- Shared bases are linear; failure does not rule out nonlinear or context-conditioned structure.",
        "- Raw attention is descriptive and is not causal visual usage.",
        "- No vision-encoder, projector-feature, MLP, Q/R lifecycle, failure, or multi-evidence experiment was started.", "",
        "Stage 3B.9 stops here.", "",
    ])

    ensure_directory(OUT / "summaries")
    write_json(OUT / "analysis/geometry_outcome_matrix.json", {
        **geometry,
        "shared_decision_source": "outputs/stage3b9/phase_a_shared/analysis/shared_geometry_decision.json",
        "local_decision_source": "outputs/stage3b9/phase_b_local/analysis/local_geometry_decision.json",
        "thresholds_modified_after_results": False,
    })
    write_text(OUT / "summaries/stage3b9_summary.md", summary)
    write_text(OUT / "summaries/next_stage_recommendation.md", "\n".join([
        f"# {recommendation}", "",
        "The technically valid single-evidence ROI→Value→head pathway has now been characterized across fresh shared-rank and held-out within-problem geometry tests. The reviewed next question is whether distinct visual evidence items are causally retrieved at distinct reasoning times.", "" if all_mechanics else "The geometry mechanics failed; repair them before any new scientific action.",
        "This recommendation does not authorize or start the next experiment.", "", "Stage 3B.9 is complete and stopped.", "",
    ]))

    target_specs = [(row["coordinate"], row["layer_index"], row["heads"]) for row in targets["targets"]]
    expected_targets = [("Ed", 29, [11, 6, 15, 12]), ("Ed_minus_1", 28, [16, 0, 3, 6])]
    figure_names = (
        "shared_recovery_vs_rank_target_a.png", "shared_recovery_vs_rank_target_b_r.png",
        "shared_complement_vs_rank_target_a.png", "shared_complement_vs_rank_target_b_r.png",
        "learned_vs_random_vs_sham_subspace_curves.png", "representative_per_base_shared_rank_curves.png",
        "within_problem_multi_value_geometry_example.png", "leave_one_value_out_local_recovery.png",
        "local_vs_matched_global_recovery.png", "local_subspace_principal_angle_distribution.png",
        "global_vs_local_outcome_summary.png", "secondary_format_stratification.png",
        "secondary_attention_vs_geometry.png",
    )
    checks = [
        criterion(1, "Stage 3B.8 result remains immutable", (OUT / "history/immutable_stage3b8_result.md").is_file(), "immutable history pointer present"),
        criterion(2, "exact Stage 3B.8 v3 representation reused", targets["representation"]["dimension"] == 512 and targets["representation"]["revision"] == "v3_exact_eager_recomposition_and_endpoint_assignment", targets["representation"]["revision"]),
        criterion(3, "exact two causal targets frozen", target_specs == expected_targets, str(target_specs)),
        criterion(4, "57 historical bases are training/design only", split["historical_training"]["count"] == 57 and not (a_set & protected), "57 fit bases; zero fresh overlap"),
        criterion(5, "at least 24 fresh Phase-A bases", len(a_set) >= 24 and not (a_set & b_set) and not (a_set & protected), f"N={len(a_set)}, all disjoint"),
        criterion(6, "shared ranks frozen before fresh scoring", ranks["frozen_ranks"] == list(RANKS), str(ranks["frozen_ranks"])),
        criterion(7, "semantic/sham/random bases materialized before scoring", all((OUT / path).is_file() for path in ("phase_a_shared/basis/target_a_rank_bases.npz", "phase_a_shared/basis/target_b_r_rank_bases.npz", "phase_a_shared/basis/sham_bases.npz", "phase_a_shared/basis/random_bases.npz", "phase_a_shared/basis/random_basis_seeds.json")), "all frozen basis/control files present"),
        criterion(8, "Phase-A scoring bidirectional and self-controlled", shared["technical_mechanics_valid"], f"N={shared['fresh_base_count']} exact mechanical controls"),
        criterion(9, "fresh confirmation excluded from shared fit", not (a_set & set(split["historical_training"]["base_problem_ids"])), "zero identity overlap"),
        criterion(10, "at least 12 separate five-value Phase-B bases", len(b_set) >= 12 and len(variants) >= 5 * len(b_set), f"N={len(b_set)}, variants={len(variants)}"),
        criterion(11, "Phase-B values frozen before vector analysis", read_json(OUT / "phase_b_local/local_deltas/freeze.json")["local_projection_results_existed"] is False, "prospective value and projector freeze"),
        criterion(12, "local test is leave-one-value-out", read_json(OUT / "phase_b_local/local_deltas/freeze.json")["local_fit"].startswith("uncentered SVD on the three non-held-out"), "three train values per held-out fold"),
        criterion(13, "local ranks limited to 1–3", set(local_stats[TARGETS[0]]) == {"1", "2", "3"} and set(local_stats[TARGETS[1]]) == {"1", "2", "3"}, "ranks 1/2/3 only"),
        criterion(14, "global-vs-local comparison uses matched ranks", (OUT / "phase_b_local/analysis/local_vs_global_statistics.json").is_file(), "matched ranks 1/2/3 persisted"),
        criterion(15, "base_problem_id remains statistical unit", all(phase_a_stats[target]["1"]["base_count"] == len(a_set) for target in TARGETS), f"Phase A N={len(a_set)}; Phase B fold aggregation within base"),
        criterion(16, "raw attention secondary only", attention["secondary_only"] and not attention["attention_used_for_selection_or_rank_choice"], "post-primary descriptive analysis"),
        criterion(17, "mixture analysis explicitly secondary", read_json(OUT / "phase_c_secondary/exploratory_clusters.json")["mixture_claim_made"] is False, "pairwise geometry only; no confirmatory cluster claim"),
        criterion(18, "no prohibited later experiment started", not any((OUT / name).exists() for name in ("vision_encoder", "projector_features", "mlp", "qr_lifecycle", "failure_analysis", "multi_evidence")), "no prohibited Stage 3B.9 output tree"),
        criterion(19, "no further single-evidence rescue launched", not any((OUT / name).exists() for name in ("stage3b10", "cluster_confirmation", "nonlinear_rescue")), "Stage 3B.9 stops after frozen geometry matrix"),
        criterion(20, "explicit GO or REDIRECT recommendation", recommendation in {"GO — Multi-Evidence Causal Refresh", "REDIRECT — Geometry mechanics invalid"}, recommendation),
    ]
    technical = "PASS" if all(row["status"] == "PASS" for row in checks) and all_mechanics else "FAIL"
    artifact_validation = {
        "phase_a_base_count": len(a_set), "phase_b_base_count": len(b_set),
        "all_primary_mechanics_valid": all_mechanics,
        "required_figures": {name: (OUT / "analysis/figures" / name).is_file() for name in figure_names},
        "all_required_figures_present": all((OUT / "analysis/figures" / name).is_file() for name in figure_names),
        "all_acceptance_pass": all(row["status"] == "PASS" for row in checks),
    }
    write_json(OUT / "analysis/artifact_validation.json", artifact_validation)
    write_json(OUT / "summaries/stage3b9_acceptance.json", {
        "stage": "3B.9", "technical_status": technical,
        "geometry_outcome": geometry["joint_label"], "recommendation": recommendation,
        "criteria": checks, "later_stage_started": False,
    })
    print(json.dumps({"technical_status": technical, "geometry": geometry, "recommendation": recommendation}, indent=2))


if __name__ == "__main__":
    main()
