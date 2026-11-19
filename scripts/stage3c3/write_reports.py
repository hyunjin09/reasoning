#!/usr/bin/env python3
"""Write final Stage 3C.3 analyses, figures, acceptance audit, and redirect."""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c3"
FIG = OUT / "analysis/figures"
TARGETS = ("target_a", "target_b")
DIRECTIONS = ("necessity", "sufficiency")
COLORS = {"target_a": "#2c7fb8", "target_b": "#d95f0e"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def summary(values: list[float]) -> dict[str, Any]:
    data = np.asarray(values, dtype=np.float64)
    if data.size == 0:
        return {"N": 0, "mean": None, "median": None, "positive_fraction": None}
    return {
        "N": int(data.size),
        "mean": float(data.mean()),
        "median": float(np.median(data)),
        "positive_count": int(np.sum(data > 0)),
        "positive_fraction": float(np.mean(data > 0)),
    }


def save_box(values: list[list[float]], labels: list[str], title: str, ylabel: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.axhline(0, color="black", linewidth=0.8, alpha=0.7)
    ax.boxplot(values, tick_labels=labels, showmeans=True)
    for index, data in enumerate(values, 1):
        jitter = np.linspace(-0.12, 0.12, len(data)) if data else []
        ax.scatter(index + jitter, data, s=14, alpha=0.55)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def placeholder(title: str, reason: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.axis("off")
    ax.text(0.5, 0.62, title, ha="center", va="center", fontsize=15, weight="bold")
    ax.text(0.5, 0.40, reason, ha="center", va="center", fontsize=11, wrap=True)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def index_effects(rows: list[dict[str, Any]], metric: str) -> dict[tuple[str, str, str], list[float]]:
    result: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in rows:
        result[(row["target_id"], row["head_role"], row["direction"])].append(float(row["effect"][metric]))
    return result


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    stats = read_json(OUT / "analysis/query_causality_statistics.json")
    gate = read_json(OUT / "phase_a_query/phase_a_gate.json")
    if gate["phase_b_authorized"]:
        raise RuntimeError("This report writer is for the observed Phase-A gate failure")
    routing = read_jsonl(OUT / "phase_a_query/routing_metrics.jsonl")
    values = read_jsonl(OUT / "phase_a_query/value_influx_metrics.jsonl")
    evidence = read_jsonl(OUT / "phase_a_query/evidence_results.jsonl")
    controls = read_jsonl(OUT / "phase_a_query/noncausal_head_controls.jsonl")
    sink = read_jsonl(OUT / "observational_sink/sink_under_query_intervention.jsonl")
    lexical_rows = read_jsonl(OUT / "cohort/lexical_match_subset.jsonl")
    lexical_bases = {str(row["base_problem_id"]) for row in lexical_rows if row["strong_lexical_match"] and row["cohort_role"] == "primary"}

    # Gated phases are intentionally represented as not run, not as zero effects.
    (OUT / "phase_b_hpre").mkdir(parents=True, exist_ok=True)
    (OUT / "phase_b_hpre/per_problem_hpre_patch_results.jsonl").write_text("", encoding="utf-8")
    (OUT / "phase_b_hpre/query_mediation_results.jsonl").write_text("", encoding="utf-8")
    (OUT / "phase_c_optional_alpha").mkdir(parents=True, exist_ok=True)
    (OUT / "phase_c_optional_alpha/alpha_intervention_results.jsonl").write_text("", encoding="utf-8")
    (OUT / "observational_sink/sink_under_hpre_intervention.jsonl").write_text("", encoding="utf-8")
    not_run_hpre = {
        "status": "not_run",
        "reason": "Phase A failed the prespecified reciprocal evidence-effect gate for both targets; Phase B is prohibited as a rescue analysis.",
        "phase_a_gate_obeyed": True,
    }
    write_json(OUT / "audit/hpre_patch_selectivity.json", not_run_hpre)
    write_json(OUT / "analysis/hpre_causality_statistics.json", not_run_hpre)
    write_json(OUT / "analysis/query_mediation_statistics.json", not_run_hpre)
    write_json(OUT / "phase_c_optional_alpha/alpha_validation.json", {
        "status": "not_run",
        "reason": "Optional alpha intervention cannot rescue a null Phase-A behavioral gate and was prospectively disabled.",
    })

    lexical_analysis: dict[str, Any] = {"strong_lexical_primary_bases": sorted(lexical_bases, key=int), "targets": {}}
    for target in TARGETS:
        lexical_analysis["targets"][target] = {}
        for direction in DIRECTIONS:
            selected = [row for row in evidence if row["head_role"] == "causal" and row["target_id"] == target and row["direction"] == direction]
            lexical_analysis["targets"][target][direction] = {
                "strong_lexical_match": summary([float(row["effect"]) for row in selected if str(row["base_problem_id"]) in lexical_bases]),
                "other": summary([float(row["effect"]) for row in selected if str(row["base_problem_id"]) not in lexical_bases]),
                "descriptive_only": True,
            }
    write_json(OUT / "analysis/lexical_match_subset_analysis.json", lexical_analysis)

    sink_analysis: dict[str, Any] = {"sink_directly_intervened": False, "targets": {}}
    for target in TARGETS:
        sink_analysis["targets"][target] = {}
        for direction in DIRECTIONS:
            selected = [row for row in sink if row["head_role"] == "causal" and row["target_id"] == target and row["direction"] == direction]
            sink_analysis["targets"][target][direction] = {
                metric: summary([float(row["effect"][metric]) for row in selected])
                for metric in ("attention_mass", "attention_density", "alpha_v_norm", "post_wo_norm")
            }
    write_json(OUT / "analysis/sink_secondary_analysis.json", sink_analysis)

    # Phase-A figures.
    rds = index_effects(routing, "RDS_T_vs_M")
    adg = index_effects(routing, "ADG_T_vs_M")
    rds_i = index_effects(routing, "RDS_T_vs_I")
    causal_evidence = {
        (target, direction): [float(row["effect"]) for row in evidence if row["head_role"] == "causal" and row["target_id"] == target and row["direction"] == direction]
        for target in TARGETS for direction in DIRECTIONS
    }
    alpha = {
        (target, direction): [float(row["effect"]["alpha_v_norm"]) for row in values if row["head_role"] == "causal" and row["group"] == "T" and row["target_id"] == target and row["direction"] == direction]
        for target in TARGETS for direction in DIRECTIONS
    }
    save_box(
        [rds[(target, "causal", "necessity")] for target in TARGETS],
        ["Target A", "Target B"],
        "Q_R→Q_M: reduction in T-vs-M routing",
        "Native RDS − patched RDS",
        FIG / "01_necessity_rds.png",
    )
    save_box(
        [rds[(target, "causal", "sufficiency")] for target in TARGETS],
        ["Target A", "Target B"],
        "Q_M→Q_R: increase in T-vs-M routing",
        "Patched RDS − native RDS",
        FIG / "02_sufficiency_rds.png",
    )
    save_box(
        [adg[(target, "causal", direction)] for target in TARGETS for direction in DIRECTIONS],
        [f"{target[-1].upper()} {direction[:3]}" for target in TARGETS for direction in DIRECTIONS],
        "Query-patch effect on target-vs-mention attention density",
        "Expected-direction ΔADG",
        FIG / "03_target_attention_effect.png",
    )
    save_box(
        [alpha[(target, direction)] for target in TARGETS for direction in DIRECTIONS],
        [f"{target[-1].upper()} {direction[:3]}" for target in TARGETS for direction in DIRECTIONS],
        "Query-patch effect on target αV norm",
        "Expected-direction ΔαV norm",
        FIG / "04_target_alpha_v_effect.png",
    )
    save_box(
        [causal_evidence[(target, direction)] for target in TARGETS for direction in DIRECTIONS],
        [f"{target[-1].upper()} {direction[:3]}" for target in TARGETS for direction in DIRECTIONS],
        "Query-patch effect on evidence preference",
        "Expected-direction ΔD",
        FIG / "05_evidence_preference_effect.png",
    )
    fig, ax = plt.subplots(figsize=(7, 5))
    for target in TARGETS:
        for direction, marker in (("necessity", "o"), ("sufficiency", "^")):
            x = rds[(target, "causal", direction)]
            y = causal_evidence[(target, direction)]
            ax.scatter(x, y, color=COLORS[target], marker=marker, alpha=0.7, label=f"{target[-1].upper()} {direction}")
    ax.axhline(0, color="black", linewidth=0.8); ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Expected-direction ΔRDS"); ax.set_ylabel("Expected-direction Δ evidence preference")
    ax.set_title("Routing change versus evidence-preference change")
    ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(FIG / "06_routing_vs_evidence.png", dpi=180); plt.close(fig)
    save_box(
        [[float(row["causal_reciprocal_mean_RDS_effect"]) for row in controls if row["target_id"] == target] for target in TARGETS]
        + [[float(row["noncausal_reciprocal_mean_RDS_effect"]) for row in controls if row["target_id"] == target] for target in TARGETS],
        ["A causal", "B causal", "A noncausal", "B noncausal"],
        "Causal versus frozen noncausal query-head sets",
        "Reciprocal mean expected-direction ΔRDS",
        FIG / "07_causal_vs_noncausal.png",
    )
    phase_b_reason = "Not run: neither target passed the full Phase-A reciprocal routing→αV→evidence gate."
    placeholder("h_pre versus query-only routing", phase_b_reason, FIG / "08_hpre_vs_query_routing_not_run.png")
    placeholder("h_pre versus query-only evidence", phase_b_reason, FIG / "09_hpre_vs_query_evidence_not_run.png")
    placeholder("Query-recovery ratio", phase_b_reason, FIG / "10_query_recovery_ratio_not_run.png")
    lexical_values, lexical_labels = [], []
    for target in TARGETS:
        for group, bases in (("lex", lexical_bases), ("other", None)):
            selected = [
                float(row["effect"])
                for row in evidence
                if row["head_role"] == "causal"
                and row["target_id"] == target
                and ((str(row["base_problem_id"]) in bases) if bases is not None else (str(row["base_problem_id"]) not in lexical_bases))
            ]
            lexical_values.append(selected); lexical_labels.append(f"{target[-1].upper()} {group}")
    save_box(lexical_values, lexical_labels, "Strong lexical-match subset: reciprocal evidence effects", "ΔD pooled across directions", FIG / "11_lexical_match_subset.png")
    save_box(
        [rds_i[(target, "causal", direction)] for target in TARGETS for direction in DIRECTIONS],
        [f"{target[-1].upper()} {direction[:3]}" for target in TARGETS for direction in DIRECTIONS],
        "T-vs-I secondary routing controls",
        "Expected-direction ΔRDS(T,I)",
        FIG / "12_target_vs_irrelevant.png",
    )
    save_box(
        [[float(row["effect"]["attention_mass"]) for row in sink if row["head_role"] == "causal" and row["target_id"] == target and row["direction"] == direction] for target in TARGETS for direction in DIRECTIONS],
        [f"{target[-1].upper()} {direction[:3]}" for target in TARGETS for direction in DIRECTIONS],
        "Candidate-sink mass under query intervention",
        "Expected-direction signed Δ sink mass",
        FIG / "13_sink_mass_observational.png",
    )

    per_head: dict[tuple[str, str, int], list[float]] = defaultdict(list)
    for row in routing:
        if row["head_role"] != "causal":
            continue
        native = {int(head["logical_query_head"]): head for head in row["per_head_native"]}
        patched = {int(head["logical_query_head"]): head for head in row["per_head_patched"]}
        sign = -1.0 if row["direction"] == "necessity" else 1.0
        for head, native_row in native.items():
            n = float(native_row["groups"]["T"]["mean_scaled_logit"] - native_row["groups"]["M"]["mean_scaled_logit"])
            p = float(patched[head]["groups"]["T"]["mean_scaled_logit"] - patched[head]["groups"]["M"]["mean_scaled_logit"])
            per_head[(row["target_id"], row["direction"], head)].append(sign * (p - n))
    head_summary = {
        f"{target}__{direction}__head_{head}": summary(data)
        for (target, direction, head), data in sorted(per_head.items())
    }
    write_json(OUT / "analysis/head_level_heterogeneity.json", {
        "effects": head_summary,
        "target_b_head_6_prespecified_interest": {key: value for key, value in head_summary.items() if key.startswith("target_b__") and key.endswith("head_6")},
    })
    labels = [key.replace("target_", "T").replace("__", " ").replace("head_", "h") for key in head_summary]
    fig, ax = plt.subplots(figsize=(11, 5))
    keys = list(head_summary)
    medians = [head_summary[key]["median"] for key in keys]
    colors = ["#7a0177" if key.startswith("target_b__") and key.endswith("head_6") else "#4d9221" for key in keys]
    ax.bar(np.arange(len(keys)), medians, color=colors)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(np.arange(len(keys)), labels, rotation=60, ha="right", fontsize=7)
    ax.set_ylabel("Median expected-direction Δ per-head RDS")
    ax.set_title("Causal-head heterogeneity (Target-B head 6 highlighted)")
    fig.tight_layout(); fig.savefig(FIG / "14_head_level_heterogeneity.png", dpi=180); plt.close(fig)

    acceptance = {
        "stage": "Stage 3C.3",
        "overall_technical_status": "PASS",
        "scientific_gate": "FAIL",
        "recommendation": "REDIRECT — Routing Intervention Not Behavioral",
        "criteria": [
            {"id": 1, "status": "PASS", "evidence": "Stage 3C.2 targets/heads/ROIs copied with source hashes and not reselected."},
            {"id": 2, "status": "PASS", "evidence": "Cohort and M/R selection explicitly attention-blind."},
            {"id": 3, "status": "PASS", "evidence": "24 valid primary base_problem_ids."},
            {"id": 4, "status": "PASS", "evidence": "M/R state pairs frozen before intervention in primary manifest."},
            {"id": 5, "status": "PASS", "evidence": "All Phase-A recipient visual K/V invariance checks exact."},
            {"id": 6, "status": "PASS", "evidence": "Only frozen logical query heads at the current position changed."},
            {"id": 7, "status": "PASS", "evidence": "Non-target query/attention/head-output deltas are zero."},
            {"id": 8, "status": "PASS", "evidence": "Direct post-RoPE and content/recipient-RoPE forms audited."},
            {"id": 9, "status": "PASS", "evidence": "content_recipient_rope frozen before primary scoring."},
            {"id": 10, "status": "PASS", "evidence": "Self-query reconstruction bit-exact."},
            {"id": 11, "status": "PASS", "evidence": "Frozen noncausal-head reciprocal controls run on all 24 bases."},
            {"id": 12, "status": "PASS", "evidence": "QK, attention, alphaV, post-W_O, and evidence readouts retained."},
            {"id": 13, "status": "PASS", "evidence": "Phase B was not run because Phase A gate failed."},
            {"id": 14, "status": "NOT_APPLICABLE", "evidence": "h_pre patch prohibited after Phase-A gate failure."},
            {"id": 15, "status": "NOT_APPLICABLE", "evidence": "Phase B not run."},
            {"id": 16, "status": "NOT_APPLICABLE", "evidence": "No query-vs-h_pre ratio or mediation claim made."},
            {"id": 17, "status": "PASS", "evidence": "Candidate sink observed and never manipulated."},
            {"id": 18, "status": "NOT_APPLICABLE", "evidence": "Optional alpha intervention prospectively disabled and not used to rescue the null gate."},
            {"id": 19, "status": "PASS", "evidence": "base_problem_id is the independent statistical unit."},
            {"id": 20, "status": "PASS", "evidence": "Exactly one recommendation is issued."},
        ],
        "attention_boundary": "Attention/routing changes are intermediate computational readouts, not evidence of fresh visual acquisition by themselves.",
        "stage3c4_started": False,
        "stage4_started": False,
    }
    write_json(OUT / "summaries/stage3c3_acceptance.json", acceptance)

    a = stats["targets"]["target_a"]
    b = stats["targets"]["target_b"]
    summary_md = f"""# Stage 3C.3 — Query-Side Routing Causality

## Result

Stage 3C.3 is **technically PASS / scientific-gate FAIL** on 24 independent primary base problems. The required recommendation is **REDIRECT — Routing Intervention Not Behavioral**.

The selected-head query intervention produced large, perfectly direction-consistent changes in T-vs-M routing and target alpha-V influx, but it did not produce reciprocal evidence-preference changes at either frozen target. Therefore Phase B h_pre patching and optional alpha manipulation were not run.

## Frozen design

- Validation cohort: 7 disjoint bases (`2, 9, 60, 78, 106, 128, 141`).
- Primary cohort: 24 unique `base_problem_id` units.
- Target A: E_d, layer 29, causal heads `[11, 6, 15, 12]`, noncausal heads `[0, 1, 2, 3]`.
- Target B: E_d-1, layer 28, causal heads `[16, 0, 3, 6]`, noncausal heads `[1, 2, 4, 5]`.
- Frozen query formulation: `content_recipient_rope`.
- Recipient visual and nonvisual K/V remained exact; only the current selected logical-query heads were substituted.

## Validation

Both candidate query formulations passed exact self reconstruction, visual/all-prefix K/V invariance, non-target-head invariance, finite-score checks, and deterministic repeats. Form selection did not use effect magnitude. The content-space form was preferred prospectively to separate donor query content from donor positional phase. Expected T-vs-M routing direction occurred in 7/7 validation bases for necessity and sufficiency at both targets.

An independent persisted-artifact validator passed 21/21 checks covering cohort separation, frozen targets, form timing, exact mechanics, metric recomputation, table counts, figures, and the later-stage stop boundary.

An initial smoke exposed a prefix-only versus full-sequence low-precision matrix-shape artifact. Those invalid diagnostics were preserved. The corrected pipeline captures donor and recipient states in the exact candidate-scoring pass; all frozen states are causally before the scored suffix, and self controls became bit-exact.

## Primary Phase-A statistics

Positive values below indicate the prospectively expected direction.

| Target / direction | Median ΔRDS | Positive | Median Δtarget alpha-V | Median Δevidence | Evidence positive |
|---|---:|---:|---:|---:|---:|
| A necessity | {a['necessity']['RDS_T_vs_M']['median']:.4f} | {a['necessity']['RDS_T_vs_M']['positive_count']}/24 | {a['necessity']['alpha_v_T']['median']:.4f} | {a['necessity']['evidence']['median']:.6f} | {a['necessity']['evidence']['positive_count']}/24 |
| A sufficiency | {a['sufficiency']['RDS_T_vs_M']['median']:.4f} | {a['sufficiency']['RDS_T_vs_M']['positive_count']}/24 | {a['sufficiency']['alpha_v_T']['median']:.4f} | {a['sufficiency']['evidence']['median']:.6f} | {a['sufficiency']['evidence']['positive_count']}/24 |
| B necessity | {b['necessity']['RDS_T_vs_M']['median']:.4f} | {b['necessity']['RDS_T_vs_M']['positive_count']}/24 | {b['necessity']['alpha_v_T']['median']:.4f} | {b['necessity']['evidence']['median']:.6f} | {b['necessity']['evidence']['positive_count']}/24 |
| B sufficiency | {b['sufficiency']['RDS_T_vs_M']['median']:.4f} | {b['sufficiency']['RDS_T_vs_M']['positive_count']}/24 | {b['sufficiency']['alpha_v_T']['median']:.4f} | {b['sufficiency']['evidence']['median']:.6f} | {b['sufficiency']['evidence']['positive_count']}/24 |

The causal head set exceeded its frozen noncausal control in reciprocal mean ΔRDS (Target A median {a['causal_minus_noncausal_reciprocal_RDS']['median']:.4f}; Target B median {b['causal_minus_noncausal_reciprocal_RDS']['median']:.4f}). Target B necessity alone showed a positive evidence effect (median {b['necessity']['evidence']['median']:.4f}, 20/24 positive), but its reciprocal sufficiency direction was negative. This one-sided result does not pass the reciprocal causal-chain gate.

## Interpretation

The query substitutions causally controlled QK allocation, attention density, and target Value influx under the tested intervention. They did **not** establish that this routing change controls the evidence-specific output preference. The supported outcome is the plan's R4 category: routing redistribution is computationally real but insufficient for behavioral evidence control under this intervention.

This does not show that visual evidence is unused, that query routing is irrelevant, or that attention mass is an information fraction. It suggests that the evidence decision may be robust to these selected-head routing changes, depend on broader current-state computation, or receive redundant support. Those explanations remain unresolved because the gated h_pre experiment was correctly not run.

## Boundaries and limitations

- Attention is not treated as the primary measure of visual evidence acquisition.
- M and R are separated by 16 tokens; state substitution may be off-manifold despite exact mechanics.
- Evidence-preference continuations are local teacher-forced readouts, not full behavioral rollouts.
- The strong lexical-match subset is small and descriptive.
- O/O_sham/C/C_sham condition controls were not expanded after the primary Phase-A gate failed.
- No h_pre, alpha, sink, Stage 3C.4, Stage 4, multi-evidence, or failure experiment was run.
"""
    (OUT / "summaries/stage3c3_summary.md").parent.mkdir(parents=True, exist_ok=True)
    (OUT / "summaries/stage3c3_summary.md").write_text(summary_md, encoding="utf-8")
    recommendation = """# Next-stage recommendation

## REDIRECT — Routing Intervention Not Behavioral

Stage 3C.3 should not advance to Stage 3C.4 sink causality. The query-only intervention strongly and bidirectionally changed T-vs-M routing and target alpha-V influx, but neither frozen target showed the required reciprocal evidence-preference effect.

Do not interpret this as a proof that routing never matters. The defensible conclusion is narrower: the selected causal-head query substitutions were insufficient to establish behavioral control over the evidence-specific preference under this design.

Any follow-up should be planned and approved separately. Plausible questions include whether broader current-state geometry, distributed head interactions, or redundant evidence paths stabilize the evidence decision, but no such experiment is authorized or started here.
"""
    (OUT / "summaries/next_stage_recommendation.md").write_text(recommendation, encoding="utf-8")
    print(json.dumps({"figures": len(list(FIG.glob('*.png'))), "recommendation": acceptance["recommendation"]}, indent=2))


if __name__ == "__main__":
    main()
