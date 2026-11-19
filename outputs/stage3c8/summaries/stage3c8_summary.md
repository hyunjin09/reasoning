# Stage 3C.8 Summary — Token-Type Carrier Atlas

## Outcome

Stage 3C.8 is **technically PASS (25/25)**. The fresh 64-base primary cohort supports a combined **O4 recency-dominant / O6 phase-specific carrier taxonomy**, with a narrower O1-like later-coordinate visual-entity effect. The result does not support a general punctuation-boundary claim, and the planned long-horizon Phase D extension was infeasible under its prospectively frozen cohort gate.

The sole review-only recommendation is **CONDITIONAL GO — Dedicated Long-Horizon Causal-Checkpoint Cohort**. No later experiment was started.

## Cohort and frozen design

The prospective screen preserved 105/240 attempted fresh outcomes: 82 completed-correct and 23 wrong. Eighty-two correct candidates were reviewed, 75 edits were constructed, 11 construction attempts were rejected, and exactly 64 fully valid unique bases were retained. Selection used neither attention nor carrier effects. The 8-base mechanical set, exact 24 Stage 3C.7 historical anchors, and 64 fresh bases were disjoint for fresh inference. The frozen annotation set contains 31,682 token rows and 29,077 lexical spans.

The model, A5000 environment, seed 1234, native GQA K/V layout, P4 `t_pre`, Phase-B T16 suppression, and Phase-C generation-start cutoff were inherited exactly. All eight validation bases passed position/group selectivity, visual/current-query invariance, T16 and cutoff semantics, self-patches, repeatability, and finite-score checks. Peak allocated GPU memory across primary runs was 9.03 GiB.

## Phase A — immediate prior-token carrier

All 24 historical anchors reproduced Stage 3C.7 exactly. On the fresh cohort, all-layer `t_pre` K+V rescue was robust at both evidence coordinates:

| Coordinate | N positive | Median gain | Mean gain | Bootstrap mean 95% CI |
|---|---:|---:|---:|---:|
| A-like | 64/64 | 1.125 | 1.669 | [1.225, 2.171] |
| B-like | 57/64 | 0.151 | 0.278 | [0.190, 0.381] |

V restoration was broadly positive, whereas K alone was weak or negative overall. This establishes a strong immediate prior-token cache carrier under the tested suppression, not a unique information fraction.

## Phase B — recent reasoning carrier atlas

Rescue was sharply localized by recency. For A-like readout, distance-1 K+V was robust (64/64 positive; median 2.382) and distance-2 K+V remained robust (56/64; median 0.125); distances 4–16 were null. For B-like readout, distance-1 K+V was robust (60/64; median 0.296); distance-2 V was robust, while distance-2 K+V missed the 75% directionality rule; distances 4–16 were null. The all-recent median rescue ratio was 0.478, below the frozen 0.50 sub-gate.

After within-base recency matching, `FUNCTION_WORD` was robust at the A-like coordinate, while `VISUAL_ENTITY` and `TARGET_ALIGNED` were robust at the B-like coordinate. Thus distance is the dominant global structure, but semantic alignment adds coordinate-specific information after recency control. This does not make every entity token a privileged carrier.

## Phase C — prompt/question carrier atlas

The mandatory full-Q positive reference was robust: 61/64 positive, median gain 0.624, mean 1.514, bootstrap mean 95% CI [1.111, 1.949]. Exhaustive single-position, lexical-span, group, and structural-control outputs were retained for all 88 historical/fresh bases.

Two K+V groups passed the frozen Phase-C class gate. `NUMERIC_LITERAL` transfer was primarily K-associated (K median 0.156, 55/64 positive; V median 0.064, 45/64). `PUNCTUATION` transfer was primarily V-associated (V median 0.062, 49/64; K median 0.021, 37/64). The decomposition was run only after the K+V gate froze those two classes.

The punctuation group should not be interpreted as boundary-specific evidence integration: punctuation was weaker than its within-base nearest prompt controls (median difference -0.016; 21/64 positive). Target-aligned prompt positions had a positive but heterogeneous matched difference (median 0.010; 29/51 positive) and did not meet the frozen 75% robustness rule. Prompt and late-reasoning carrier taxonomies therefore differ.

## Phase D gate

The Phase A/B carrier-signal gate opened, but only 15 fresh bases met the independently frozen requirement of at least 128 pre-`E_d` tokens and two reasoning segments, below the minimum 28. Phase D inference, necessity tests, and route controls were not run; explicit manifests and derived outputs are empty. This is a feasibility result, not evidence that long-horizon causal checkpoints do not exist.

## Cross-stage interpretation and limits

Stages 2A–2C showed that ROI attention is often mention-centered and cannot identify acquisition. Stage 3A established pre-mention visual-content sensitivity, and Stages 3B–3C.7 localized useful consequences into residual/cache states. Stage 3C.8 now shows that those consequences are carried differently across lifecycle phases: strongly by the immediately preceding reasoning state, locally by recent tokens with target-dependent semantic structure, and in the prompt by numeric/punctuation groups with distinct K/V profiles.

These conclusions are conditional on localized numeric MathVerse edits, two evidence-coordinate readouts, teacher-forced scoring, native-state transplantation, and Qwen3-VL-4B-Thinking. Raw attention was not used for cohort, token, span, gate, or carrier selection. Rescue ratios are unclipped and are not unique causal information fractions. The atlas does not establish sink causality, a universal token taxonomy, or repeated long-horizon checkpoints.

## Stop boundary

Stage 3C.8 stops here. No sink manipulation, unconstrained history search, residual-feature learning, Stage 4, multi-evidence refresh, or failure analysis was started.
