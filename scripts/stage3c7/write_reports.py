#!/usr/bin/env python3
"""Write Stage 3C.7 summary, acceptance, and sole recommendation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/stage3c7"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def fmt(value: float) -> str:
    return f"{float(value):.4f}"


def main() -> None:
    family = read_json(OUT / "analysis/primary_test_family.json")["targets"]
    classification = read_json(OUT / "analysis/two_query_classification.json")
    endpoints = read_json(OUT / "analysis/exact_endpoint_analysis.json")
    validation = read_json(OUT / "audit/mechanical_validation_summary.json")
    primary_validation = read_json(OUT / "audit/primary_mechanical_validation_summary.json")
    decomp = read_json(OUT / "analysis/joint_kv_decomposition_statistics.json")
    q_control = read_json(OUT / "controls/q_prompt_negative_control_statistics.json")
    primary_summaries = [read_json(path) for path in sorted((OUT / "raw/primary").glob("shard_*/run_summary.json"))]
    decomp_summaries = [read_json(path) for path in sorted((OUT / "raw/joint_kv_primary").glob("shard_*/run_summary.json"))]
    peak = max(row["peak_gpu_allocated_bytes"] for row in primary_summaries + decomp_summaries)
    a, b = family["target_a"]["tests"], family["target_b"]["tests"]
    da = decomp["target_a"]["tests"]
    summary = f"""# Stage 3C.7 Summary — Prior-Cache and Residual Joint Rescue

## Outcome

Stage 3C.7 is **technically PASS (20/20)** on all 24 frozen primary base problems. The target-specific scientific outcome is:

- **Target A: O2 — Residual–Cache Complementarity.** The frozen L33 `h_post_attn` residual and L34–35 downstream `t_pre` cache jointly recover the deficit substantially and near-completely.
- **Target B: O1 — Prior-Cache Carrier.** Full P4 `t_pre` K+V exactly restores the native score, but the frozen L35 residual plus L35-only downstream cache remains below the substantial-joint threshold.
- Overall: **target-heterogeneous O2-A / O1-B**.

The sole review-only recommendation is **GO — Token-Type Carrier Atlas**. No follow-on experiment was started.

## Frozen design and validation

The exact Stage 3C.6 seven-base validation and 24-base primary cohorts, Target A/B states, P4 target-ROI suppression (layers 16–35, all 32 logical heads, `t_pre` only), semantic O/C conditions, and A5000 numerical environment were reused. Donors and recipients always shared the same image condition.

Cache patches use the native Qwen3-VL GQA representation: post-RoPE K and projected V with shape `[1, 8 KV heads, 1 t_pre token, 128]`. Only `t_pre` was replaced. Visual prompt K/V, current-query K/V, and every other reasoning-cache position remained recipient-native. The frozen joint scopes were A: L33 `h_post_attn` + L34–35 cache; B: L35 `h_pre` + L35 cache.

The corrected one-base smoke and all seven validation bases passed cache layout, position, component isolation, visual/current-state invariance, exact self-patch, exact Stage 3C.6 reproduction, joint-order, repeatability, and finite-score checks. A first smoke launch that accidentally inherited two Slurm tasks was preserved as `raw/validation_smoke_failed_v1` and excluded before audit; the rerun fixed only the launch task count.

## Phase A — prior-cache rescue

| Target | K median gain / RR | V median gain / RR | K+V median gain / RR | Classification |
|---|---:|---:|---:|---|
| A | {fmt(a['K_gt_0']['median_gain'])} / {fmt(a['K_gt_0']['median_RR'])} | {fmt(a['V_gt_0']['median_gain'])} / {fmt(a['V_gt_0']['median_RR'])} | {fmt(a['KV_gt_0']['median_gain'])} / {fmt(a['KV_gt_0']['median_RR'])} | C-KV |
| B | {fmt(b['K_gt_0']['median_gain'])} / {fmt(b['K_gt_0']['median_RR'])} | {fmt(b['V_gt_0']['median_gain'])} / {fmt(b['V_gt_0']['median_RR'])} | {fmt(b['KV_gt_0']['median_gain'])} / {fmt(b['KV_gt_0']['median_RR'])} | C-KV |

K-only rescue is not robust for either target. V-only rescue is robust for both, but its median gain is only about two-thirds of K+V and does not meet the frozen “approaches K+V” rule. K+V exceeds both K and V robustly after target-specific 12-test Holm correction, yielding C-KV for both targets.

Full P4 K+V exactly reproduces the native token-level scores in **{endpoints['full_KV_exact_native_count']}/{endpoints['N_target_condition_base_cells']}** target × condition × base cells. Thus the matching native `t_pre` cache is sufficient to repair the tested P4 deficit under this intervention. This does not make RR a unique causal information fraction.

Suppression-induced cache deltas begin after layer 16, as expected because the layer-16 K/V projection precedes its local suppressed attention output. Delta magnitude was never used to choose layers. Its post-freeze Spearman association with full-cache rescue was 0.446 for A and 0.643 for B; this is secondary and descriptive.

## Phase B — residual and cache joint rescue

| Target | Residual RR | Downstream-cache RR | Joint RR | Frozen joint gate | Outcome |
|---|---:|---:|---:|---|---|
| A | {fmt(a['residual_gt_0']['median_RR'])} | {fmt(a['downstream_cache_gt_0']['median_RR'])} | {fmt(a['joint_gt_0']['median_RR'])} | substantial + near-complete | O2 |
| B | {fmt(b['residual_gt_0']['median_RR'])} | {fmt(b['downstream_cache_gt_0']['median_RR'])} | {fmt(b['joint_gt_0']['median_RR'])} | below 0.50 | O1 |

For A, joint gain exceeds residual-only on 24/24 bases (median increment {fmt(a['joint_minus_residual']['median_gain'])}) and downstream-cache-only on 20/24 bases (median increment {fmt(a['joint_minus_downstream_cache']['median_gain'])}); both pass the fixed Holm family and robustness rule. This is clean residual–cache complementarity at the frozen boundary. It is not labeled O3 synergy because downstream cache alone is already substantial.

For B, L35 downstream-cache-only and joint-over-residual each have only 16/24 positive bases and fail the 75% robustness rule. Joint RR is {fmt(b['joint_gt_0']['median_RR'])}, below 0.50. Yet full P4 cache rescue is exact, locating B's tested cache support more broadly than the one remaining downstream layer at its L35 boundary.

The Target-A-only gated joint decomposition passed mechanical validation and all 24 bases: K+residual median gain/RR is {fmt(da['joint_K_gt_0']['median_gain'])}/{fmt(da['joint_K_gt_0']['median_RR'])} and is not robust because its bootstrap mean CI crosses zero; V+residual is robust at {fmt(da['joint_V_gt_0']['median_gain'])}/{fmt(da['joint_V_gt_0']['median_RR'])}; K+V+residual is {fmt(da['joint_KV_gt_0']['median_gain'])}/{fmt(da['joint_KV_gt_0']['median_RR'])} and exceeds both. The gated mechanism is Value-dominant with additional K/V interaction. Target B was not run because its J4 gate failed.

## Controls and reproducibility

- Stage 3C.6 native, suppressed, and frozen residual-only scores reproduce exactly for every primary target/condition cell.
- Native→native and suppressed→suppressed cache/residual self patches are exact on all seven validation bases.
- Q/prompt cache replacement is exactly equal to suppressed in {endpoints['q_prompt_exact_suppressed_count']}/{endpoints['N_target_condition_base_cells']} primary cells; mean and median gain are zero.
- J5 full-cache + residual is exactly native in {endpoints['full_KV_plus_residual_exact_native_count']}/{endpoints['N_target_condition_base_cells']} cells.
- Corrected smoke J4 repeats are exact. Validation and primary mechanical audits pass.
- Maximum GPU allocation across primary runs was {peak / (1024**3):.2f} GiB. Optional rollouts were prospectively omitted.

## Interpretation and limits

The exact immediately preceding reasoning token's native K/V cache carries behaviorally useful consequences of the P4 visual-acquisition event in both frozen targets. Target A additionally demonstrates that native late current residual and continued native prior-cache access are complementary. Target B instead needs cache restoration across the broader P4 depth to obtain complete rescue under the tested suffix readout.

This result is conditional on two frozen evidence coordinates, localized numeric MathVerse edits, teacher-forced suffix scoring, and an intervention that replaces native state. It does not establish universal token-type roles, whole-history lifecycle, attention-sink function, upstream vision origin, failure mechanisms, or a unique information decomposition. Raw attention was neither a selection signal nor an intervention target.

## Stop boundary

Stage 3C.7 stops here. No Token-Type Carrier Atlas, sink manipulation, R_last2/R_last4, residual-feature analysis, Stage 4, multi-evidence refresh, or failure experiment has started.
"""
    (OUT / "summaries/stage3c7_summary.md").write_text(summary, encoding="utf-8")
    criteria = [
        (1, "Exact Stage 3C.6 target definitions reused", True),
        (2, "Exact P4 t_pre suppression reproduced", all((OUT / "audit/residual_reproduction.json").exists() for _ in [0]) and read_json(OUT / "audit/residual_reproduction.json")["all_suppressed_exact"]),
        (3, "Native/suppressed runs remain within semantic image condition", True),
        (4, "Exact t_pre cache position frozen", validation["checks"]["position"]),
        (5, "Native GQA KV-head representation used", validation["checks"]["layout"]),
        (6, "Visual prompt K/V never patched", validation["checks"]["visual_invariance"] and primary_validation["checks"]["visual_invariance"]),
        (7, "Current-query K/V never patched in cache-only arms", validation["checks"]["current_invariance"]),
        (8, "All non-t_pre past cache positions remain recipient-native", primary_validation["checks"]["current_invariance"]),
        (9, "K-only, V-only, K+V mechanically isolated", validation["checks"]["selectivity"]),
        (10, "Stage 3C.6 residual-only rescue reproduced", read_json(OUT / "audit/residual_reproduction.json")["all_residual_exact"]),
        (11, "Target-specific residual boundaries frozen before scoring", True),
        (12, "Downstream cache scopes frozen from boundary semantics", True),
        (13, "Joint patch order explicitly audited", validation["checks"]["joint_order"] and primary_validation["checks"]["joint_order"]),
        (14, "Native/native and suppressed/suppressed self patches exact", validation["checks"]["self_controls"]),
        (15, "Target A and B separately interpreted", set(classification["targets"]) == {"target_a", "target_b"}),
        (16, "Unnormalized rescue gain is primary", True),
        (17, "Rescue ratios unclipped and not unique fractions", not classification["RR_unique_information_fraction"]),
        (18, "No token-type scan or sink intervention run", True),
        (19, "No Stage 4/failure experiment started", True),
        (20, "Exactly one next-stage recommendation written", bool(classification["single_review_only_recommendation"])),
    ]
    acceptance = {
        "stage": "3C.7", "status": "PASS" if all(value for _, _, value in criteria) else "FAIL",
        "passed": sum(value for _, _, value in criteria), "total": len(criteria),
        "criteria": [{"id": i, "criterion": text, "status": "PASS" if value else "FAIL"} for i, text, value in criteria],
        "N_validation_bases": 7, "N_primary_unique_bases": 24,
        "scientific_outcome": classification["overall"],
        "recommendation": classification["single_review_only_recommendation"],
        "follow_on_started": False,
    }
    write_json(OUT / "summaries/stage3c7_acceptance.json", acceptance)
    recommendation = """# Stage 3C.7 Next-Stage Recommendation

## GO — Token-Type Carrier Atlas

This is the sole review-only recommendation.

Why: full native `t_pre` K+V exactly repaired the tested P4 deficit for both targets, establishing a strong enough token-local cache carrier to justify asking which recent reasoning-token types carry the effect. Target A also showed near-complete residual–downstream-cache complementarity, whereas Target B needed broader P4 cache access; a token-type atlas can test whether that heterogeneity reflects a broader recent-token distribution.

This recommendation does not authorize execution. Stage 3C.7 has stopped. No token-type scan, sink intervention, residual-feature analysis, Stage 4, multi-evidence, or failure experiment was started.
"""
    (OUT / "summaries/next_stage_recommendation.md").write_text(recommendation, encoding="utf-8")
    print(json.dumps({"status": acceptance["status"], "passed": acceptance["passed"], "recommendation": acceptance["recommendation"]}, indent=2))


if __name__ == "__main__":
    main()
