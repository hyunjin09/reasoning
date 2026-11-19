# Stage 3C.7 Implementation Plan

## Objective

Execute `plan/stage3c7_plan.md` as one bounded prior-cache and residual-joint rescue action, preserving the exact Stage 3C.6 cohorts, targets, P4 deficit, and causal boundaries.

## Ordered tasks

1. Freeze protocol artifacts and state transition.
   - Acceptance: exact 7/24 split, target A/B definitions, P4 scope, downstream cache scopes, 12-test target-specific family, effect-independent exclusions, and recommendation rules are persisted before scoring.
   - Verify: deterministic config-preparation tests and hashes of inherited manifests/configs.
2. Implement cache and joint intervention mechanics test-first.
   - Acceptance: post-RoPE K/projected-V capture uses native 8-KV-head layout; K, V, and K+V patches change only `t_pre`; joint ordering is correct at A `L33 h_post_attn` and B `L35 h_pre`.
   - Verify: focused unit tests fail before implementation and pass afterward; full existing suite remains green.
3. Run smoke and seven-base validation on the policy-compliant A5000 allocation.
   - Acceptance: exact position/layout/selectivity/visual/current-state/self/repeat audits pass, exact P4 and residual baselines reproduce, all scores are finite.
   - Verify: independent validation report over the seven frozen bases.
4. Run the untouched 24-base primary cohort.
   - Acceptance: at least 20 mechanically valid bases; O/C are reported separately then sign-aligned within base; C2/C3/C4 and J0--J5 are complete.
   - Verify: raw-row cardinality, cohort identity, hashes, and finite-score audit.
5. Apply the frozen joint-decomposition gate.
   - Acceptance: downstream K/V joint decomposition is run only for targets with substantial J4 rescue; otherwise a frozen not-run record is saved.
   - Verify: gate inputs and decision are persisted before any gated scoring.
6. Analyze, visualize, independently validate, report, and stop.
   - Acceptance: fixed Holm families, bootstrap summaries, 14 figures, 20 acceptance criteria, one outcome and one review-only recommendation; no prohibited follow-on is started.
   - Verify: independent artifact validator and full test suite pass.

## Prospective operational definitions

- Robust positive effect: Holm-adjusted one-sided `p < 0.05`, bootstrap mean-gain CI lower bound `> 0`, and positive gain on at least 75% of valid bases.
- Strong cache rescue: robust K+V rescue with median unclipped RR at least 0.50.
- A component “approaches K+V” when it is robust and its median gain is at least 80% of the K+V median gain.
- C-KV requires robust K+V-minus-K and K+V-minus-V increments; otherwise a robust K+V result is reported without forcing a component label.
- Substantial/near-complete joint rescue follows the plan exactly: robust J4 with median RR at least 0.50/0.80.
- O3 requires near-complete J4 while neither residual-only nor downstream-cache-only is substantial. O2 requires substantial J4 plus robust positive increments over both singles. O1 requires strong full-cache rescue without O2/O3. O4 requires robust residual-only rescue with no robust cache addition over residual. Otherwise O5.
- Recommendation order: O1 -> Token-Type Carrier Atlas; O2/O3 -> Broader Recent-Cache Interaction only if J4 remains below near-complete, otherwise Token-Type Carrier Atlas; O4 -> Residual Feature Mechanism; O5 with nonzero robust cache contribution -> Broader Recent-Cache Interaction; otherwise Residual Feature Mechanism. Attention Sink Causality is ineligible while cache/residual ambiguity remains.
- Optional rollouts are omitted prospectively to limit compute/storage and because teacher-forced evidence preference is primary.

## Risks and mitigations

- Hook composition: use one explicit per-layer attention intervention for simultaneous suppression and cache replacement, plus the established boundary hook; audit event order.
- Candidate-specific suffix state: retain separate donor K/V and residual tensors for original/counterfactual candidates.
- BF16 drift: require exact self patches and exact historical reproduction; perform contribution bookkeeping in validated FP32 code.
- Selection leakage: never inspect primary effect magnitudes before all configs and gates are frozen.

