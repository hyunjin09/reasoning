# Stage 3C.3-R summary

## Result

Stage 3C.3-R is a **technical PASS (20/20)** with scientific outcome **O4 — Broad Robustness Beyond W4**.

The selected-head target contribution was not individually necessary: the frozen Phase-B gate passed with median base-aggregated `E(0)/E(1) = 0.996591`, and all 24 bases retained at least 80% of native preference. Removing target-ROI contribution from every logical head in both W4 layers still retained median `E(0)/E(1) = 0.986423` for Target A and `0.990984` for Target B.

## Validation and cohort

- Validation: 7 disjoint bases, 20/20 mechanics checks passed.
- Primary: 24 unique `base_problem_id` values, exactly reused from Stage 3C.3.
- Failed smoke preserved: v1 exposed avoidable BF16 partition bookkeeping; FP32 partition arithmetic was fixed before primary scoring.
- Maximum primary reconstruction error: `1.19e-07`.
- Lambda=1 native scoring, lambda=0 source isolation, Q/K/V/attention invariance, non-target heads, deterministic repeats, and finite outputs passed.
- Compute: existing Slurm allocation 106936 on node04 with two A5000 GPUs. Median per-base times were `4.76s` for Phase A and `3.24s` for Phase B. A validation-only resource replay measured `8.37 GiB` peak allocation and is excluded from scientific analyses.

## Phase A: selected-head dose response

Target A did not show evidence loss as gain decreased. At lambda=0, median unnormalized `D(1)-D(0)` was `-0.033388` and target-level median retained evidence was `1.004658`.

Target B showed a small, graded, target-specific effect: lambda=0 median `D(1)-D(0) = 0.088188` (mean `0.115658`, bootstrap mean 95% CI `[0.05148086886246308, 0.19665440474542736]`, 20/24 positive, Holm `p=0.00779772`). Yet its median retained evidence remained `0.987923`. Target-B monotonic trend, T-vs-M specificity, and causal-vs-noncausal specificity survived Holm correction; Target-A contrasts did not. There are 4 significant rows in the full 26-test family.

## Stage 3C.3 operating point

The Stage 3C.3 necessity patch did not merely leave a large target contribution. Median effective projected gains were `0.001404` for Target A and `0.005919` for Target B. Because direct lambda=0 also preserved approximately 99% of evidence preference, the behavioral null is **not** explained by the query patch remaining above a lower saturation transition. No collapse threshold was observed.

## Phase B: nested W4 scopes

R1 (all heads at the target layer), R2 (frozen causal head identities across layers 28-29), and R3 (all heads across layers 28-29) were frozen before Phase A and run only after the gate passed. No R1/R2/R3 lambda-zero incremental-loss contrast versus R0 survived Holm correction. R3 remained broadly robust at both targets. Therefore the experiment does not localize compensation to same-layer or cross-layer W4 paths.

The bounded conclusion is that evidence preference is supported outside or redundantly with the tested **current-position W4 target-ROI contribution family**. This does not identify whether the support is earlier retrieval, language-side residual state, another layer, or another carrier.

## Scientific boundary

Attention was fixed locally to define `c_T = sum alpha_j V_j`; it was not used as the primary causal readout. The result does not establish sink function, a Q/R carrier, an upstream retrieval trigger, or a universal threshold. No sink, query, `h_pre`, broader-than-W4, Stage 4, multi-evidence, or failure intervention was run.

## Recommendation

**GO — Redundancy Localization Beyond W4**, for review only. R3 robustness satisfies the plan's condition for this recommendation, but no broader experiment is authorized or started here.
