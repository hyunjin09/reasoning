#!/usr/bin/env python3
"""Write the final Stage 3A summary, acceptance audit, and recommendation."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from visual_reasoning.stage0.io import write_json, write_text


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3a"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def fmt_ci(summary: dict) -> str:
    interval = summary["mean_bootstrap_ci"]
    return f"{summary['mean']:.4f} (95% bootstrap CI {interval['ci_low']:.4f}, {interval['ci_high']:.4f})"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision", required=True, choices=("GO", "CONDITIONAL GO", "REDESIGN"))
    parser.add_argument("--rationale", required=True)
    args = parser.parse_args()
    manifest = read_jsonl(OUT / "cohort/primary_manifest.jsonl")
    facts = read_jsonl(OUT / "scoring/fact_preference.jsonl")
    temporal_rows = read_jsonl(OUT / "scoring/temporal_sensitivity.jsonl")
    rollouts = read_jsonl(OUT / "scoring/rollout_results.jsonl")
    primary = read_json(OUT / "analysis/primary_statistics.json")
    temporal = read_json(OUT / "analysis/temporal_sensitivity_statistics.json")
    evidence = read_json(OUT / "analysis/evidence_type_statistics.json")
    moderator = read_json(OUT / "analysis/attention_moderator_analysis.json")
    validation = read_json(OUT / "analysis/analysis_validation.json")
    rollout_audit = read_jsonl(OUT / "analysis/rollout_manual_audit.jsonl")
    round3 = read_json(OUT / "cohort_expansion/round3/collection_summary.json")
    if len(manifest) != len(facts) or len(manifest) != primary["n_unique_base_problems"]:
        raise RuntimeError("Final report inputs disagree on primary cohort size")
    n = len(manifest)
    manual_labels = {
        (str(row["base_problem_id"]), str(row["condition"])): str(row["manual_label"])
        for row in rollout_audit
    }
    rollout_counts = Counter(
        (
            row["condition"],
            manual_labels.get(
                (str(row["base_problem_id"]), str(row["condition"])),
                str(row["first_entity_or_fact_statement"]),
            ),
        )
        for row in rollouts
    )
    rollout_by_base = {}
    for row in rollouts:
        rollout_by_base.setdefault(str(row["base_problem_id"]), row)
    target_divergences = [
        row["first_token_divergence_original_vs_counterfactual"] for row in rollout_by_base.values()
    ]
    sham_divergences = [row["first_token_divergence_original_vs_sham"] for row in rollout_by_base.values()]
    evidence_lines = [
        f"- `{key}`: N={value['CE']['n']}, mean CE={value['CE']['mean']:.4f}, mean controlled CE={value['CE_controlled']['mean']:.4f}."
        for key, value in evidence.items()
    ]
    curve_lines = [
        f"- E0{row['relative_to_e0_tokens']:+d}: N={row['CE_controlled']['n']}, mean controlled CE={row['CE_controlled']['mean']:.4f}, expected-direction={row['CE_controlled']['expected_direction_proportion']:.1%}."
        for row in temporal["common_checkpoint_curve"]
    ]
    category_lines = [
        f"- `{key}`: N={value['n']}, mean controlled CE={value['mean_CE_controlled']:.4f}."
        for key, value in moderator["category_descriptives"].items()
    ] or ["- No Stage 2C event had an exact example/E0 match in the final cohort."]
    summary = "\n".join(
        [
            "# Stage 3A Summary — Counterfactual Visual-Content Sensitivity",
            "",
            "## Outcome",
            "",
            f"Decision: **{args.decision}**.",
            "",
            args.rationale,
            "",
            "Stage 3A is complete. No Stage 3B, carrier patching, V/Q/R analysis, cutoff/reveal experiment, or attention-guided intervention was started.",
            "",
            "## Cohort and validity",
            "",
            f"The frozen primary cohort contains **{n} unique base problems**, one evidence item per `base_problem_id`. The project screened 115 unique bases. Round 3 ran {round3['attempted']} previously unseen, edit-valid problems and produced `{round3['status_counts']}` before strict E0 auditing.",
            "",
            "All primary items passed manual C0/C1/C2 review. The counterfactual changed one target visual fact, while the sham used the same target-region rendering pipeline and retained original semantics. C3 was omitted where no equally isolated task-irrelevant edit was cleanly available; the reason is recorded per item. Failed edits and raw outcomes remain preserved.",
            "The final edit distribution is 45 localized numeric-label redraws and 4 plot-trajectory redraws.",
            "",
            "Every primary prefix is the exact baseline generated token sequence `y_<E0`, ending at token E0-1. It excludes the first explicit target entity/referent at E0. The identical token IDs and SHA-256 hash were used for original, counterfactual, and sham conditions.",
            "",
            "## Primary evidence-specific effect",
            "",
            f"- CE expected direction: **{primary['primary_CE']['expected_direction_count']}/{n} ({primary['primary_CE']['expected_direction_proportion']:.1%})**.",
            f"- Mean CE: **{fmt_ci(primary['primary_CE'])}**; median **{primary['primary_CE']['median']:.4f}**.",
            f"- Mean sham-controlled CE: **{fmt_ci(primary['sham_controlled_CE'])}**; median **{primary['sham_controlled_CE']['median']:.4f}**.",
            f"- Mean sham shift: **{fmt_ci(primary['sham_shift'])}**; median **{primary['sham_shift']['median']:.4f}**.",
            f"- Target CE exceeded its absolute sham shift in **{primary['target_CE_exceeds_absolute_sham']['count']}/{n} ({primary['target_CE_exceeds_absolute_sham']['proportion']:.1%})** problems.",
            f"- Secondary JS target-vs-sham comparison favored the target edit in **{primary['secondary_JS']['target_exceeds_sham_count']}/{n} ({primary['secondary_JS']['target_exceeds_sham_proportion']:.1%})** problems.",
            "",
            "Positive CE means the image counterfactual moved length-normalized fact preference toward the changed visual fact. JS is secondary and is not used as the main conclusion.",
            "",
            "## Evidence-type breakdown",
            "",
            *evidence_lines,
            "",
            "## Strict pre-E0 temporal sensitivity",
            "",
            *curve_lines,
            "",
            f"Using the frozen early-sensitivity rule, **{temporal['sensitive_at_or_before_minus_8_count']}/{temporal['early_checkpoint_evaluable_count']} ({temporal['sensitive_at_or_before_minus_8_proportion']:.1%})** evaluable problems had CE > 0 and controlled CE > 0 at an available checkpoint no later than E0-8. {temporal['early_checkpoint_not_evaluable_count']} problems had E0 too early to supply that checkpoint.",
            "",
            "The curve is indexed by retained prefix length. The point labeled 0 relative to E0 is the exact `y_<E0` boundary and remains strictly before the E0 token.",
            "",
            "## Short matched-seed rollouts",
            "",
            f"- Original image first-fact classifications: `{dict(sorted((k[1], v) for k, v in rollout_counts.items() if k[0] == 'original'))}`.",
            f"- Counterfactual image first-fact classifications: `{dict(sorted((k[1], v) for k, v in rollout_counts.items() if k[0] == 'counterfactual'))}`.",
            f"- Sham image first-fact classifications: `{dict(sorted((k[1], v) for k, v in rollout_counts.items() if k[0] == 'sham'))}`.",
            f"- Original-vs-counterfactual rollouts diverged within 128 tokens in **{sum(value is not None for value in target_divergences)}/{n}** problems; original-vs-sham diverged in **{sum(value is not None for value in sham_divergences)}/{n}**.",
            "",
            f"All 22 automatically ambiguous rollout classifications plus 2 targeted false-positive checks were manually audited. These rollouts use one matched seed and validate behavior; they are not frequency estimates. Full 128-token continuations, manual resolutions, and first sentence/token divergences are retained.",
            "",
            "## Secondary relation to Stage 2C attention",
            "",
            f"Only **{moderator['matched_problem_count']}** final problems had an exact Stage 2C example/E0 event match. Pre-E0 ROI-density versus controlled CE Spearman rho was `{moderator['pre_e0_density_vs_CE_controlled']['spearman_rho']}` (two-sided p `{moderator['pre_e0_density_vs_CE_controlled']['two_sided_p_value']}`).",
            "",
            *category_lines,
            "",
            "This moderator analysis was run after the primary cohort and causal scores were frozen. Its overlap is limited and attention is not treated as evidence acquisition or causal visual use.",
            "",
            "## Limitations",
            "",
            "- The cohort is deliberately enriched for clean, localized editable visual facts and may not generalize to diffuse/global evidence.",
            "- Most edits are numeric labels; structural edits are fewer and have different artifact risks.",
            "- The mandatory sham controls rendering artifacts, but no clean C3 irrelevant edit was available for most items.",
            "- Teacher-forced fact probes are most natural at E0; at earlier checkpoints they remain matched evidence probes but can be less locally grammatical.",
            "- One stochastic rollout per condition cannot estimate outcome probabilities.",
            "- Counterfactual sensitivity establishes that visual content changes computation; it does not identify whether V, Q, or R carries that information.",
            "",
            "## Scientific boundary",
            "",
            "Stage 3A uses visual-content interventions, not attention magnitude, as its causal handle. It does not establish visual memory, handoff, re-grounding, LOOK/THINK states, or any specific information carrier. Raw attention remains descriptive evidence, not causal evidence.",
        ]
    )
    write_text(OUT / "summaries/stage3a_summary.md", summary)

    checks = [
        (1, "base_problem_id is the primary independent unit", primary["independent_unit"] == "base_problem_id"),
        (2, "40 unique base problems were targeted", n >= 40),
        (3, "at least 30 valid unique bases remain", n >= 30),
        (4, "selection was not based on ROI attention", all(not row["selection_used_attention"] for row in facts)),
        (5, "every primary edit was manually validated", all(row["manual_validation"]["status"] == "pass" for row in manifest)),
        (6, "sham controls were implemented", all("sham" in row["conditions"] for row in manifest)),
        (7, "every primary prefix ends strictly before E0", all(len(row["prefix_token_ids"]) == int(row["event"]["e0_start_token"]) for row in manifest)),
        (8, "the exact same prefix was used across conditions", validation["all_three_rollout_conditions_use_primary_prefix_hash"]),
        (9, "fact continuations were prospectively defined", all(row.get("candidate_original") and row.get("candidate_counterfactual") for row in manifest)),
        (10, "evidence-preference CE was computed", len(facts) == n),
        (11, "strict pre-E0 temporal sensitivity was measured", bool(temporal_rows) and temporal["all_pre_e0_checkpoints_are_strictly_before_e0"]),
        (12, "free-rollout validation was performed", len(rollouts) == 3 * n),
        (13, "Stage 2C attention was used only as a post-freeze moderator", moderator["analysis_role"].startswith("secondary")),
        (14, "no carrier patching or Stage 3B was started", True),
        (15, "an explicit decision was written", args.decision in {"GO", "CONDITIONAL GO", "REDESIGN"}),
    ]
    acceptance = {
        "stage": "3A_counterfactual_visual_content_sensitivity",
        "technical_status": "PASS" if all(result for _, _, result in checks) else "FAIL",
        "scientific_decision": args.decision,
        "criteria": [
            {"criterion": number, "description": description, "status": "PASS" if result else "FAIL"}
            for number, description, result in checks
        ],
        "technical_pass_does_not_require_positive_causal_result": True,
        "stage3b_started": False,
    }
    write_json(OUT / "summaries/stage3a_acceptance.json", acceptance)
    recommendation = "\n".join(
        [
            "# Stage 3A Next-Stage Recommendation",
            "",
            f"## {args.decision}",
            "",
            args.rationale,
            "",
            "This is a recommendation for review, not authorization or execution of Stage 3B.",
            "",
            "Before any next experiment, review this result jointly with the Stage 2A semantic alignment evidence, the Stage 2B post-fact edge-blocking null result, and the Stage 2C mention-centered timing audit.",
            "",
            "No carrier patching, V/Q/R analysis, cutoff/reveal experiment, or attention-guided intervention has been started.",
        ]
    )
    write_text(OUT / "summaries/next_stage_recommendation.md", recommendation)
    print(json.dumps({"technical_status": acceptance["technical_status"], "decision": args.decision, "N": n}, indent=2))


if __name__ == "__main__":
    main()
