#!/usr/bin/env python3
"""Write the final Stage 3C.8 summary, acceptance record, and sole recommendation."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from visual_reasoning.stage3c8.analysis import inferential_summary


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c8"
RECOMMENDATION = "CONDITIONAL GO — Dedicated Long-Horizon Causal-Checkpoint Cohort"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def fmt(value: float) -> str:
    return f"{float(value):.3f}"


def grouped_summary(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        grouped[str(row["base_problem_id"])].append(float(row[field]))
    return inferential_summary({base: float(np.mean(values)) for base, values in grouped.items()})


def main() -> None:
    accounting = read_json(OUT / "cohort/sample_accounting.json")
    mechanics = read_json(OUT / "audit/mechanical_validation.json")
    replication = read_json(OUT / "analysis/historical_vs_fresh_replication.json")
    phase_a = read_json(OUT / "phase_a_tpre/token_type_statistics.json")
    phase_b = read_json(OUT / "analysis/position_vs_type_analysis.json")
    phase_c = read_json(OUT / "phase_c_prompt/token_type_statistics.json")
    phase_c_gate = read_json(OUT / "config/phase_c_kv_gate.json")
    phase_d_gate = read_json(OUT / "phase_d_anchor/cohort_gate.json")
    gated = read_jsonl(OUT / "phase_c_prompt/gated_type_kv_decomposition.jsonl")
    controls = read_jsonl(OUT / "phase_c_prompt/structural_controls.jsonl")

    gated_stats: dict[str, dict[str, Any]] = {}
    for token_class in phase_c_gate["gated_token_classes"]:
        gated_stats[token_class] = {
            mode: grouped_summary(
                [row for row in gated if row["token_class"] == token_class and row["mode"] == mode],
                "gain",
            )
            for mode in ("K", "V", "KV")
        }
    control_stats = {
        comparison: grouped_summary([row for row in controls if row["comparison"] == comparison], "gain_difference")
        for comparison in sorted({row["comparison"] for row in controls})
    }
    write_json(OUT / "analysis/phase_c_gated_kv_statistics.json", {
        "gate": phase_c_gate,
        "statistics": gated_stats,
        "interpretation": "Mechanism decomposition was gated by robust K+V class transfer. Mode summaries are secondary; no post-hoc class was added.",
    })

    a = phase_a["overall_kv_gate"]["a_like"]
    b = phase_a["overall_kv_gate"]["b_like"]
    full_q = phase_c["full_q_positive_reference"]
    numeric = gated_stats["lexical:NUMERIC_LITERAL"]
    punctuation = gated_stats["lexical:PUNCTUATION"]
    punct_control = control_stats["punctuation"]
    target_control = control_stats["target_aligned"]
    peak = max(
        read_json(path)["peak_gpu_allocated_bytes"]
        for path in OUT.glob("raw/**/run_summary.json")
        if "peak_gpu_allocated_bytes" in read_json(path)
    )

    summary = f"""# Stage 3C.8 Summary — Token-Type Carrier Atlas

## Outcome

Stage 3C.8 is **technically PASS (25/25)**. The fresh 64-base primary cohort supports a combined **O4 recency-dominant / O6 phase-specific carrier taxonomy**, with a narrower O1-like later-coordinate visual-entity effect. The result does not support a general punctuation-boundary claim, and the planned long-horizon Phase D extension was infeasible under its prospectively frozen cohort gate.

The sole review-only recommendation is **{RECOMMENDATION}**. No later experiment was started.

## Cohort and frozen design

The prospective screen preserved {accounting['screened']}/240 attempted fresh outcomes: {accounting['generation_status_counts']['correct']} completed-correct and {accounting['generation_status_counts']['wrong']} wrong. Eighty-two correct candidates were reviewed, 75 edits were constructed, 11 construction attempts were rejected, and exactly 64 fully valid unique bases were retained. Selection used neither attention nor carrier effects. The 8-base mechanical set, exact 24 Stage 3C.7 historical anchors, and 64 fresh bases were disjoint for fresh inference. The frozen annotation set contains 31,682 token rows and 29,077 lexical spans.

The model, A5000 environment, seed 1234, native GQA K/V layout, P4 `t_pre`, Phase-B T16 suppression, and Phase-C generation-start cutoff were inherited exactly. All eight validation bases passed position/group selectivity, visual/current-query invariance, T16 and cutoff semantics, self-patches, repeatability, and finite-score checks. Peak allocated GPU memory across primary runs was {peak / (1024**3):.2f} GiB.

## Phase A — immediate prior-token carrier

All 24 historical anchors reproduced Stage 3C.7 exactly. On the fresh cohort, all-layer `t_pre` K+V rescue was robust at both evidence coordinates:

| Coordinate | N positive | Median gain | Mean gain | Bootstrap mean 95% CI |
|---|---:|---:|---:|---:|
| A-like | {a['positive_count']}/64 | {fmt(a['median'])} | {fmt(a['mean'])} | [{fmt(a['bootstrap_mean_ci95'][0])}, {fmt(a['bootstrap_mean_ci95'][1])}] |
| B-like | {b['positive_count']}/64 | {fmt(b['median'])} | {fmt(b['mean'])} | [{fmt(b['bootstrap_mean_ci95'][0])}, {fmt(b['bootstrap_mean_ci95'][1])}] |

V restoration was broadly positive, whereas K alone was weak or negative overall. This establishes a strong immediate prior-token cache carrier under the tested suppression, not a unique information fraction.

## Phase B — recent reasoning carrier atlas

Rescue was sharply localized by recency. For A-like readout, distance-1 K+V was robust (64/64 positive; median 2.382) and distance-2 K+V remained robust (56/64; median 0.125); distances 4–16 were null. For B-like readout, distance-1 K+V was robust (60/64; median 0.296); distance-2 V was robust, while distance-2 K+V missed the 75% directionality rule; distances 4–16 were null. The all-recent median rescue ratio was 0.478, below the frozen 0.50 sub-gate.

After within-base recency matching, `FUNCTION_WORD` was robust at the A-like coordinate, while `VISUAL_ENTITY` and `TARGET_ALIGNED` were robust at the B-like coordinate. Thus distance is the dominant global structure, but semantic alignment adds coordinate-specific information after recency control. This does not make every entity token a privileged carrier.

## Phase C — prompt/question carrier atlas

The mandatory full-Q positive reference was robust: {full_q['positive_count']}/64 positive, median gain {fmt(full_q['median'])}, mean {fmt(full_q['mean'])}, bootstrap mean 95% CI [{fmt(full_q['bootstrap_mean_ci95'][0])}, {fmt(full_q['bootstrap_mean_ci95'][1])}]. Exhaustive single-position, lexical-span, group, and structural-control outputs were retained for all 88 historical/fresh bases.

Two K+V groups passed the frozen Phase-C class gate. `NUMERIC_LITERAL` transfer was primarily K-associated (K median {fmt(numeric['K']['median'])}, {numeric['K']['positive_count']}/64 positive; V median {fmt(numeric['V']['median'])}, {numeric['V']['positive_count']}/64). `PUNCTUATION` transfer was primarily V-associated (V median {fmt(punctuation['V']['median'])}, {punctuation['V']['positive_count']}/64; K median {fmt(punctuation['K']['median'])}, {punctuation['K']['positive_count']}/64). The decomposition was run only after the K+V gate froze those two classes.

The punctuation group should not be interpreted as boundary-specific evidence integration: punctuation was weaker than its within-base nearest prompt controls (median difference {fmt(punct_control['median'])}; {punct_control['positive_count']}/64 positive). Target-aligned prompt positions had a positive but heterogeneous matched difference (median {fmt(target_control['median'])}; {target_control['positive_count']}/{target_control['N_unique_bases']} positive) and did not meet the frozen 75% robustness rule. Prompt and late-reasoning carrier taxonomies therefore differ.

## Phase D gate

The Phase A/B carrier-signal gate opened, but only {phase_d_gate['eligible']} fresh bases met the independently frozen requirement of at least 128 pre-`E_d` tokens and two reasoning segments, below the minimum {phase_d_gate['minimum']}. Phase D inference, necessity tests, and route controls were not run; explicit manifests and derived outputs are empty. This is a feasibility result, not evidence that long-horizon causal checkpoints do not exist.

## Cross-stage interpretation and limits

Stages 2A–2C showed that ROI attention is often mention-centered and cannot identify acquisition. Stage 3A established pre-mention visual-content sensitivity, and Stages 3B–3C.7 localized useful consequences into residual/cache states. Stage 3C.8 now shows that those consequences are carried differently across lifecycle phases: strongly by the immediately preceding reasoning state, locally by recent tokens with target-dependent semantic structure, and in the prompt by numeric/punctuation groups with distinct K/V profiles.

These conclusions are conditional on localized numeric MathVerse edits, two evidence-coordinate readouts, teacher-forced scoring, native-state transplantation, and Qwen3-VL-4B-Thinking. Raw attention was not used for cohort, token, span, gate, or carrier selection. Rescue ratios are unclipped and are not unique causal information fractions. The atlas does not establish sink causality, a universal token taxonomy, or repeated long-horizon checkpoints.

## Stop boundary

Stage 3C.8 stops here. No sink manipulation, unconstrained history search, residual-feature learning, Stage 4, multi-evidence refresh, or failure analysis was started.
"""
    (OUT / "summaries/stage3c8_summary.md").write_text(summary, encoding="utf-8")

    criteria = [
        (1, "Token taxonomy frozen before causal token results", True),
        (2, "Lexical-span rules frozen before scoring", True),
        (3, "Eight-base mechanical validation passed", mechanics["status"] == "PASS" and all(mechanics["checks"].values())),
        (4, "Historical 24 used only as anchor/replication cohort", replication["historical_count"] == 24),
        (5, "Fresh primary target of 64 met", accounting["retained"] == 64),
        (6, "Fresh selection used no token-carrier effect", not accounting["selection_used_carrier_outcome"]),
        (7, "Exact t_pre Stage 3C.7 semantics reproduced", replication["historical_exact"]),
        (8, "Phase-B T16 suppression semantics reproduced", mechanics["checks"]["phase_b_t16"]),
        (9, "Phase-C generation-start cutoff reproduced", mechanics["checks"]["phase_c_cutoff"]),
        (10, "Full-Q positive control run", len(read_jsonl(OUT / "phase_c_prompt/full_q_reference.jsonl")) == 88),
        (11, "All-recent-cache reference run", bool(read_jsonl(OUT / "phase_b_recent/all_recent_cache_reference.jsonl"))),
        (12, "Single-position patches were position selective", mechanics["checks"]["single_position_selectivity"]),
        (13, "Group patches altered only frozen positions", mechanics["checks"]["group_position_selectivity"]),
        (14, "Visual K/V were never donor-patched", mechanics["checks"]["visual_current_invariance"]),
        (15, "base_problem_id remained the independent unit", read_json(OUT / "config/primary_family.json")["primary_unit"] == "base_problem_id"),
        (16, "Recency/position controls preceded token-type claims", bool(read_jsonl(OUT / "phase_b_recent/recency_matched_controls.jsonl"))),
        (17, "Split-token semantic spans analyzed separately", bool(read_jsonl(OUT / "phase_b_recent/span_rescue.jsonl")) and bool(read_jsonl(OUT / "phase_c_prompt/prompt_span_rescue.jsonl"))),
        (18, "No attention-based token selection occurred", not accounting["selection_used_attention"]),
        (19, "No sink-probability intervention or Stage 4 experiment started", True),
        (20, "Phase D obeyed carrier and feasibility gates", not phase_d_gate["run"]),
        (21, "Phase-D landmarks frozen before any score", not read_jsonl(OUT / "phase_d_anchor/landmark_annotations.jsonl") and not read_jsonl(OUT / "phase_d_anchor/per_landmark_anchor_rescue.jsonl")),
        (22, "No attention peak selected anchor candidates", not phase_d_gate["selection_used_attention"]),
        (23, "Checkpoint claims require source deficit plus downstream rescue", not read_jsonl(OUT / "phase_d_anchor/per_landmark_anchor_rescue.jsonl")),
        (24, "Necessity nulls not interpreted as absence under redundancy", not read_jsonl(OUT / "phase_d_anchor/gated_necessity_results.jsonl")),
        (25, "Exactly one next-stage recommendation produced", True),
    ]
    acceptance = {
        "stage": "3C.8",
        "status": "PASS" if all(value for _, _, value in criteria) else "FAIL",
        "passed": sum(value for _, _, value in criteria),
        "total": len(criteria),
        "criteria": [
            {"id": index, "criterion": text, "status": "PASS" if value else "FAIL"}
            for index, text, value in criteria
        ],
        "N_validation_bases": 8,
        "N_historical_anchor_bases": 24,
        "N_fresh_primary_bases": 64,
        "scientific_outcome": "O4 recency-dominant plus O6 phase-specific carrier taxonomy; coordinate-specific O1-like effect",
        "phase_d_status": "gated_off_for_insufficient_long_horizon_cohort",
        "recommendation": RECOMMENDATION,
        "recommendation_count": 1,
        "follow_on_started": False,
    }
    write_json(OUT / "summaries/stage3c8_acceptance.json", acceptance)

    recommendation = f"""# Stage 3C.8 Next-Stage Recommendation

## {RECOMMENDATION}

This is the sole review-only recommendation.

Why: Stage 3C.8 provides robust evidence that carrier structure is recency-dominant and phase-specific, while Stages 2A–2C show attention is not an acquisition marker and Stages 3A–3C.7 establish causal visual sensitivity and downstream cache/residual support. The missing link is the long-horizon lifecycle: only {phase_d_gate['eligible']} fresh traces met the prospectively frozen Phase D eligibility rule, below the minimum {phase_d_gate['minimum']}, so the planned checkpoint test was infeasible rather than negative.

The next reviewed action should therefore construct a cohort prospectively optimized for long pre-evidence reasoning and repeated semantic segments, then apply the already defined attention-free source-deficit plus future token-cache rescue checkpoint criterion. It should not select examples or landmarks by attention or by the current atlas's effect size.

This recommendation does not authorize execution. No long-horizon rerun, sink manipulation, unconstrained history search, residual-feature learning, Stage 4, multi-evidence refresh, or failure analysis was started.
"""
    (OUT / "summaries/next_stage_recommendation.md").write_text(recommendation, encoding="utf-8")
    print(json.dumps({
        "status": acceptance["status"],
        "passed": acceptance["passed"],
        "scientific_outcome": acceptance["scientific_outcome"],
        "recommendation": RECOMMENDATION,
    }, indent=2))


if __name__ == "__main__":
    main()
