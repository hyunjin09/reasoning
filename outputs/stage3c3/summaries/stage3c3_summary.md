# Stage 3C.3 — Query-Side Routing Causality

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
| A necessity | 4.6507 | 24/24 | 8.6351 | -0.001133 | 12/24 |
| A sufficiency | 4.6283 | 24/24 | 8.9669 | 0.002818 | 12/24 |
| B necessity | 3.5826 | 24/24 | 4.9838 | 0.118647 | 20/24 |
| B sufficiency | 3.5834 | 24/24 | 5.1291 | -0.005795 | 10/24 |

The causal head set exceeded its frozen noncausal control in reciprocal mean ΔRDS (Target A median 0.7886; Target B median 1.5040). Target B necessity alone showed a positive evidence effect (median 0.1186, 20/24 positive), but its reciprocal sufficiency direction was negative. This one-sided result does not pass the reciprocal causal-chain gate.

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
