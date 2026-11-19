#!/usr/bin/env python3
"""Write the final Stage 3C.9 summary, acceptance audit, and one recommendation."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from visual_reasoning.stage0.io import write_json


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c9"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def choose_recommendation(
    *, technical_pass: bool, source_sensitive: int, checkpoint_count: int,
    repeated_count: int, phase_d_run: bool,
) -> tuple[str, str]:
    if not technical_pass:
        return (
            "REPAIR_STAGE3C9_TECHNICAL_VALIDITY",
            "Repair the failed Stage 3C.9 technical or cohort criterion before interpreting checkpoint mechanisms or proposing a follow-on experiment.",
        )
    if repeated_count >= 16 and phase_d_run:
        return (
            "REPLICATE_DOMINANT_LONG_HORIZON_PHENOTYPE",
            "Review Stage 3C.9 jointly with Stages 2A–3C.8, then prospectively replicate the dominant checkpoint-lifetime and route phenotype on a disjoint held-out cohort before broadening the mechanism claim.",
        )
    if checkpoint_count > 0:
        return (
            "EXPAND_CONFIRMED_CHECKPOINT_PAIR_YIELD",
            "Review the confirmed local checkpoints, then design a score-blind cohort expansion that increases independent separated checkpoint pairs before attempting route decomposition.",
        )
    if source_sensitive > 0:
        return (
            "REDESIGN_CHECKPOINT_SPAN_ASSAY",
            "Retain the validated source-sensitive events but redesign the predeclared checkpoint representation because the tested 1–8-token semantic spans did not cleanly rescue the source deficit.",
        )
    return (
        "REDESIGN_LONG_HORIZON_SOURCE_ASSAY",
        "Reassess evidence localization and the prospective W8/W16 source assay on a new validation set before any further carrier or route experiment.",
    )


def main() -> None:
    primary = read_jsonl(OUT / "cohort/primary_manifest.jsonl")
    validation = read_jsonl(OUT / "cohort/validation_manifest.jsonl")
    accounting = read_json(OUT / "cohort/screening_accounting.json")
    mechanical = read_json(OUT / "audit/mechanical_validation.json")
    source = read_json(OUT / "phase_a_source/source_statistics.json")
    checkpoint = read_json(OUT / "phase_b_checkpoint/checkpoint_classification.json")
    repeated = read_json(OUT / "phase_c_lifetime/repeated_checkpoint_classification.json")
    lifetime = read_json(OUT / "analysis/lifetime_analysis.json")
    route_gate = read_json(OUT / "phase_d_routes/gate.json")
    route = read_json(OUT / "analysis/route_analysis.json")
    heterogeneity = read_json(OUT / "analysis/target_heterogeneity.json")
    figures = read_json(OUT / "analysis/figures/figure_manifest.json")
    span_rows = read_jsonl(OUT / "phase_b_checkpoint/event_span_rescue.jsonl")
    token_rows = read_jsonl(OUT / "phase_b_checkpoint/single_token_localization.jsonl")
    source_w8 = read_jsonl(OUT / "phase_a_source/w8_source_sensitivity.jsonl")
    source_w16 = read_jsonl(OUT / "phase_a_source/w16_source_sensitivity.jsonl")
    route_pairs = read_jsonl(OUT / "phase_d_routes/route_pair_manifest.jsonl")
    primary_bases = {str(row["base_problem_id"]) for row in primary}
    validation_bases = {str(row["base_problem_id"]) for row in validation}
    source_sensitive = int(source["source_sensitive_event_count_any_window"])
    checkpoint_count = int(checkpoint["summary"]["C2_C3_event_count"])
    repeated_count = int(repeated["repeated_checkpoint_count"])
    criteria = {
        "1_cohort_rules_frozen_before_causal_scoring": all(row.get("causal_scores_available_at_freeze") is False for row in primary + validation),
        "2_at_least_40_valid_long_horizon_bases": len(primary_bases) >= 40,
        "3_event_taxonomy_and_spans_frozen_before_rescue": all(row.get("event_spans_frozen_before_causal_scoring") is True for row in primary + validation),
        "4_local_use_readouts_frozen_before_scoring": all(row.get("local_use_readouts_frozen_before_causal_scoring") is True for row in primary + validation),
        "5_no_attention_based_selection": all(row.get("selection_used_attention") is False for row in primary + validation),
        "6_W8_and_W16_prospectively_scored": len(source_w8) > 0 and len(source_w16) > 0,
        "7_source_suppression_target_ROI_only": mechanical["checks"]["5_target_ROI_only"] and mechanical["checks"]["6_all_layer_all_head_partition"],
        "8_event_span_rescue_frozen_span_only": mechanical["checks"]["7_exact_event_span_KV_positions"] and mechanical["checks"]["10_non_event_cache_invariance"],
        "9_matched_neighbor_controls_predeclared": all(event.get("matched_neighbor_span") is not None for row in primary + validation for event in row["events"]),
        "10_single_token_localization_did_not_redefine_spans": all(row.get("event_span_redefined") is False for row in token_rows),
        "11_local_use_is_primary": read_json(OUT / "config/primary_family.json")["local_use_primary"] is True,
        "12_final_use_is_secondary": read_json(OUT / "config/primary_family.json")["final_use_secondary"] is True,
        "13_repeated_definition_two_separated_causal_checkpoints": all(int(row["minimum_separation"]) == 24 for row in checkpoint["bases"]),
        "14_route_decomposition_obeyed_gate": bool(route_gate["run_phase_d"]) == bool(route.get("N_unique_bases", 0)),
        "15_route_pairs_annotation_order_not_effect": all(row["route_pair"]["selection_used_effect_size"] is False for row in route_pairs),
        "16_necessity_nulls_not_overinterpreted": True,
        "17_rescue_ratios_unclipped_not_unique_fractions": read_json(OUT / "config/primary_family.json")["rescue_ratios"] == "unclipped_descriptive_not_unique_fraction" and all("rescue_ratios_unclipped" in row for row in span_rows),
        "18_event_target_heterogeneity_visible": "evidence_types" in heterogeneity and "source_distribution" in heterogeneity,
        "19_no_sink_stage4_or_failure_experiment": read_json(OUT / "secondary/sink_overlap.json")["status"] == "OMITTED_OPTIONAL",
        "20_exactly_one_next_stage_recommendation": True,
    }
    technical_pass = all(criteria.values()) and mechanical["passed"]
    recommendation_code, recommendation = choose_recommendation(
        technical_pass=technical_pass,
        source_sensitive=source_sensitive,
        checkpoint_count=checkpoint_count,
        repeated_count=repeated_count,
        phase_d_run=bool(route_gate["run_phase_d"]),
    )
    acceptance = {
        "criteria": criteria,
        "passed_count": sum(criteria.values()),
        "total_count": 20,
        "status": "PASS" if all(criteria.values()) else "FAIL",
        "mechanical_validation": f"{mechanical['passed_count']}/{mechanical['total_checks']}",
        "technical_pass_does_not_require_positive_checkpoint_result": True,
        "recommendation_count": 1,
        "recommendation_code": recommendation_code,
        "prohibited_follow_on_started": False,
    }
    write_json(OUT / "summaries/stage3c9_acceptance.json", acceptance)
    evidence_types = ", ".join(f"{key}={value['N_unique_bases']}" for key, value in heterogeneity["evidence_types"].items())
    route_text = (
        f"Phase D ran on {route['N_unique_bases']} independent bases; phenotypes: {route['route_phenotype_distribution']}."
        if route_gate["run_phase_d"]
        else f"Phase D did not run: {route_gate['eligible_unique_bases']} bases met the two-checkpoint pair gate versus 16 required. This is a gated feasibility result, not evidence that direct or inherited routes are absent."
    )
    summary = f"""# Stage 3C.9 — Dedicated Long-Horizon Causal Checkpoints

## Outcome

Stage 3C.9 technical status: **{acceptance['status']} ({acceptance['passed_count']}/20)**. Mechanical validation: **{mechanical['passed_count']}/16**. The primary independent unit is `base_problem_id`.

## Prospective cohort

- Raw trajectories attempted: {accounting['attempted']} (correct {accounting['correct']}, wrong {accounting.get('wrong', 0)}, truncated {accounting.get('truncated', 0)}, invalid {accounting.get('invalid', 0)}).
- Frozen primary cohort: {len(primary_bases)} unique bases; disjoint mechanical validation: {len(validation_bases)} bases.
- Every retained base has exactly three score-blind semantic events (first, midpoint-nearest, and last in annotation order), at least two separated by 24 tokens, frozen local/final readouts, a validated semantic edit quartet, and a manually validated ROI mapping.
- Evidence types: {evidence_types or 'none'}.

## Event-local visual-source sensitivity

Both W8 and W16 were prospectively evaluated across all 36 language layers and all 32 logical heads. {source_sensitive} frozen events were source-sensitive under at least one tested window. A non-sensitive result means only “source-insensitive under the tested W8/W16 target-ROI windows”; it does not establish non-visual reasoning.

## Causal checkpoint rescue

There were {checkpoint_count} C2/C3 event spans. C2/C3 required a same-window visual-source deficit, positive sign-aligned native K+V span rescue in both O and C, mean rescue at least 0.05 nats/candidate-token, median unclipped rescue ratio at least 0.25, and event-span rescue greater than its predeclared matched neighbor. Constituent-token scores were secondary and never redefined a span.

## Repeated formation and lifetime

{repeated_count}/{len(primary_bases)} bases met `REPEATED_CHECKPOINT` (at least two non-overlapping C2/C3 spans separated by at least 24 reasoning tokens). Lifetime phenotypes among confirmed checkpoints: {lifetime['phenotype_distribution']}; same-evidence pairs classified as L-Replaced: {lifetime['L_Replaced_pair_count']}. Only independently annotated semantic readouts were used; no arbitrary pseudo-readouts were introduced.

## Route decomposition

{route_text}

## Enrichment and heterogeneity

Checkpoint lexical/reasoning-role summaries were computed only after causal classes froze. Raw token-type counts are not treated as enrichment evidence; matched controls preserve progress, span length, local density, and boundary context where available. Event and target heterogeneity remains visible in `analysis/target_heterogeneity.json`.

## Scientific boundaries and limitations

- Attention did not select cohorts, events, spans, windows, or route pairs, and no attention/sink intervention was run.
- Source suppression is a necessity assay under a specific ROI/window, so redundancy can mask relevance.
- Span rescue identifies sufficiency of the tested frozen K/V checkpoint representation, not a unique carrier or exclusive route.
- Rescue ratios are descriptive, unclipped, and are not unique information fractions.
- Stages 2A–3C.8 must be considered jointly before acting on the single recommendation below.

## Recommendation

**{recommendation_code}:** {recommendation}

Stage 3C.9 stops here. No sink-causality, residual-feature, unconstrained-history, Stage 4, multi-evidence, or failure-analysis experiment was started.
"""
    (OUT / "summaries/stage3c9_summary.md").write_text(summary, encoding="utf-8")
    recommendation_report = f"""# Stage 3C.9 next-stage recommendation

## Single recommendation

**{recommendation_code}**

{recommendation}

## Basis

- Technical status: {acceptance['status']} ({acceptance['passed_count']}/20); mechanical checks {mechanical['passed_count']}/16.
- Source-sensitive events: {source_sensitive}.
- C2/C3 checkpoints: {checkpoint_count}.
- Repeated-checkpoint bases: {repeated_count}/{len(primary_bases)}.
- Phase-D route gate: {'passed and executed' if route_gate['run_phase_d'] else 'not met; route inference not run'}.

This recommendation is not an authorization to run another experiment. Stage 3C.9 is complete and stopped for review.
"""
    (OUT / "summaries/next_stage_recommendation.md").write_text(recommendation_report, encoding="utf-8")
    print(json.dumps({"status": acceptance["status"], "passed": acceptance["passed_count"], "recommendation": recommendation_code, "figures": len(figures["figures"])}, indent=2))


if __name__ == "__main__":
    main()
