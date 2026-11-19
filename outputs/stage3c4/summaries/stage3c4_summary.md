# Stage 3C.4 summary

## Result

Stage 3C.4 is a **technical PASS (20/20)** with joint scientific outcome **O2 — Temporal Redundancy** and one next-stage recommendation:

> **GO — Behaviorally Necessary Visual Window Mechanism**

At the base-aggregated level, removing the target-ROI Value contribution from every head in every language layer at only the current query retained median evidence preference `0.8436`. Extending that same exact intervention by one earlier query reduced median retention to `0.6515`; it reached `0.5952` at T2 and then plateaued near `0.55` through T16. Thus, under the frozen decision rule, evidence support is not confined to the current query: behaviorally relevant target-ROI contributions are redundantly supplied across immediately preceding reasoning time.

This does not identify an exact retrieval token or a Q/R/current-residual carrier. It does not establish sink causality.

## Frozen design and validation

- Model/condition: Qwen3-VL-4B-Thinking, original image condition O, seed 1234.
- Validation cohort: the exact seven Stage 3C.3-R validation bases, disjoint from primary.
- Primary cohort: the exact 24 Stage 3C.3/3C.3-R primary `base_problem_id` values.
- Targets: Target A at `E_d`, historical W4 layer 29 and heads `[11,6,15,12]`; Target B at `E_d-1`, historical W4 layer 28 and heads `[16,0,3,6]`.
- Source: the frozen, attention-independent Stage 3B.7-R target ROI T. Mention M and irrelevant I were retained only as controls.
- Intervention: set `c_T(t,l,h)=sum_{j in T} alpha(t,l,h,j)V(l,h,j)` to zero after Attention and before `W_O`, using the validated FP32 contribution partition. Locally computed Q/K/V, attention probabilities, non-target source contribution, and unselected queries remained directly untouched. Downstream layers recomputed naturally.
- Exact prospective families: L0–L4, T0/T1/T2/T4/T8/T16, C1–C4, and M/I at all-layer T0/T4.
- All primary examples supported every T16 window; there were no exclusions.

The seven-base validation passed exact layer/head/query/source enumeration, lambda-one native reconstruction, zero-gain source isolation, outside-window invariance, finite scores, and deterministic repeats. Independent validation then rederived all primary schedules and statistics from raw results and passed 20/20 checks across `51,072` patched layer/candidate audits. Maximum FP32 partition error was `9.54e-7`, within the frozen `1e-6` tolerance.

## Phase A — same-time layer redundancy

Base-aggregated median unclipped evidence retention was:

| Scope | Layers | Median retention | Median unnormalized loss from native |
|---|---:|---:|---:|
| L0 | 28–29 | 0.9859 | 0.0931 |
| L1 | 28–33 | 0.9571 | 0.2895 |
| L2 | 24–35 | 0.8875 | 0.8439 |
| L3 | 16–35 | 0.8451 | 1.2486 |
| L4 | 0–35 | 0.8436 | 1.3096 |

Every one of the 48 target/base L0 scores exactly reproduced the historical Stage 3C.3-R R3 score. Every frozen L1–L4 incremental-loss contrast over L0 was positive on 24/24 bases and Holm-significant. This establishes a graded same-time layer contribution, but the joint L4 median remained above the frozen 0.80 substantial-retention boundary. Target heterogeneity was material: Target A L4 median retention was `0.7819`, whereas Target B retained `0.8971`.

## Phase B — temporal redundancy

With all 36 language layers suppressed, base-aggregated median retention was:

| Window | Inclusive queries | Median retention | Median unnormalized loss from native | Fraction retaining ≥0.80 | Fraction retaining ≥0.50 |
|---|---|---:|---:|---:|---:|
| T0 | `[t*,t*]` | 0.8436 | 1.3096 | 0.583 | 1.000 |
| T1 | `[t*-1,t*]` | 0.6515 | 2.4658 | 0.167 | 0.750 |
| T2 | `[t*-2,t*]` | 0.5952 | 2.7370 | 0.125 | 0.708 |
| T4 | `[t*-4,t*]` | 0.5653 | 2.9037 | 0.125 | 0.667 |
| T8 | `[t*-8,t*]` | 0.5588 | 2.9404 | 0.125 | 0.667 |
| T16 | `[t*-16,t*]` | 0.5519 | 2.9496 | 0.125 | 0.667 |

The largest added loss occurred when expanding from T0 to T1: median incremental loss `1.3069`, positive on 24/24 bases. Every T1–T16 contrast against T0 and the frozen temporal trend survived Holm correction. The base-aggregated tested `w_80` is T1; no tested base-aggregated `w_50` exists. These sparse windows do not identify an exact token boundary.

Target A was again more sensitive: median retention was `0.7819` at T0, `0.4638` at T1, and `0.3683` at T16, with tested `w_80=T0` and `w_50=T1`. Target B retained `0.8971`, `0.8122`, and `0.7650`, with `w_80=T2` and no tested `w_50`.

## Phase C — layer × time interaction

Median base-aggregated retention was `0.7597` for layers 24–35 × last 4 queries (C1), `0.7485` for the same layers × last 8 (C2), `0.5653` for all layers × last 4 (C3), and `0.5588` for all layers × last 8 (C4). The frozen all-layer-minus-late-layer interaction had median unnormalized loss `1.3455`, was positive on 23/24 bases, and survived Holm correction. C3 and C4 exactly reproduced the independently executed Phase-B T4 and T8 scores on all 96 target/base comparisons.

Because C1 itself fell below 0.80, the prospective joint rule does not reserve the result for O3: temporal expansion within late layers is already sufficient for a substantial descriptive loss, while adding earlier/mid layers increases it further. The joint classification is therefore O2, with a significant layer-depth component.

## Target specificity and confirmatory family

Target suppression exceeded mention-ROI suppression on all 24 base-aggregated comparisons (median T-minus-M loss `1.9417`) and exceeded irrelevant-ROI suppression on all 24 (median `2.0332`). Both control tests passed the frozen gate and Holm correction. All 14 prospectively frozen tests were Holm-significant (`adjusted p = 8.34e-7` for every row).

This supports evidence-specific intervention semantics; it does not imply that M or I are behaviorally inert in every individual head or example.

## Stage 3B.2 comparison

Across the same 24 bases and two target coordinates (48 target/base events), the Stage 3B.2 all-visual semantic source switch had median BRI `10.5245`, whereas Stage 3C.4 median unnormalized loss was `0.8885` at T0 and `2.4819` at T16. Stage 3B.2 BRI correlated weakly with Stage 3C.4 T0 loss (`rho=0.143`, `p=0.334`) and T16 loss (`rho=0.119`, `p=0.422`).

These magnitudes are not interchangeable: Stage 3B.2 replaces future all-visual semantic identity, while Stage 3C.4 deletes only the target-ROI Value contribution. The weak correlation is descriptive and does not show that one mechanism causes the other.

## Compute and artifacts

GPU work ran inside Slurm allocation `106936` on node04 with two NVIDIA RTX A5000 GPUs through tmux session 8. The maximum peak allocation was `8.75 GiB` and maximum reservation `8.87 GiB`. The slower shard took approximately `36.7s`, `83.8s`, and `87.1s` after model load for Phases A, B, and C respectively. All raw per-base results, audits, base-level tables, statistics, controls, comparisons, and 13 required figures are under `outputs/stage3c4/`.

## Scientific boundary

The primary result is an evidence-preference change caused by target-ROI contribution deletion, not raw attention magnitude. Attention appears only inside the precisely defined contribution `alpha V`; it is not interpreted as a behavioral importance fraction.

Stage 3C.4 localizes necessity across late reasoning time and layer breadth. It does **not** identify which Q/R/residual state carries evidence, prove one exact earlier acquisition token, establish a sink function, or justify windows earlier than 16 tokens. No state patching, sink manipulation, Stage 4, multi-evidence refresh, or failure analysis was run.

## Recommendation

**GO — Behaviorally Necessary Visual Window Mechanism**, for review only. The strongest bounded result is the sharp additional loss from including the immediately preceding query, plus a significant layer-depth interaction. Any follow-up must be separately reviewed and authorized.
