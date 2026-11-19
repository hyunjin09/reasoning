# Stage 3C.9 — Dedicated Long-Horizon Causal Checkpoints

## Outcome

Stage 3C.9 technical status: **PASS (20/20)**. Mechanical validation: **16/16**. The primary independent unit is `base_problem_id`.

## Prospective cohort

- Raw trajectories attempted: 600 (correct 391, wrong 207, truncated 2, invalid 0).
- Frozen primary cohort: 48 unique bases; disjoint mechanical validation: 8 bases.
- Every retained base has exactly three score-blind semantic events (first, midpoint-nearest, and last in annotation order), at least two separated by 24 tokens, frozen local/final readouts, a validated semantic edit quartet, and a manually validated ROI mapping.
- Evidence types: localized_angle_label=27, localized_formula_label=2, localized_length_label=16, localized_radius_label=3.

## Event-local visual-source sensitivity

Both W8 and W16 were prospectively evaluated across all 36 language layers and all 32 logical heads. 29 frozen events were source-sensitive under at least one tested window. A non-sensitive result means only “source-insensitive under the tested W8/W16 target-ROI windows”; it does not establish non-visual reasoning.

## Causal checkpoint rescue

There were 2 C2/C3 event spans. C2/C3 required a same-window visual-source deficit, positive sign-aligned native K+V span rescue in both O and C, mean rescue at least 0.05 nats/candidate-token, median unclipped rescue ratio at least 0.25, and event-span rescue greater than its predeclared matched neighbor. Constituent-token scores were secondary and never redefined a span.

## Repeated formation and lifetime

0/48 bases met `REPEATED_CHECKPOINT` (at least two non-overlapping C2/C3 spans separated by at least 24 reasoning tokens). Lifetime phenotypes among confirmed checkpoints: {'L-Short': 2}; same-evidence pairs classified as L-Replaced: 0. Only independently annotated semantic readouts were used; no arbitrary pseudo-readouts were introduced.

## Route decomposition

Phase D did not run: 0 bases met the two-checkpoint pair gate versus 16 required. This is a gated feasibility result, not evidence that direct or inherited routes are absent.

## Enrichment and heterogeneity

Checkpoint lexical/reasoning-role summaries were computed only after causal classes froze. Raw token-type counts are not treated as enrichment evidence; matched controls preserve progress, span length, local density, and boundary context where available. Event and target heterogeneity remains visible in `analysis/target_heterogeneity.json`.

## Scientific boundaries and limitations

- Attention did not select cohorts, events, spans, windows, or route pairs, and no attention/sink intervention was run.
- Source suppression is a necessity assay under a specific ROI/window, so redundancy can mask relevance.
- Span rescue identifies sufficiency of the tested frozen K/V checkpoint representation, not a unique carrier or exclusive route.
- Rescue ratios are descriptive, unclipped, and are not unique information fractions.
- A post-hoc validity audit found material Phase-A-versus-Phase-B source-score instability for the 33 rescored event-windows (median absolute per-condition difference 0.12363; 24/33 source gates changed at the frozen 0.05 threshold). Same-path replay remains exact, but the exact nominal checkpoint count is path-sensitive.
- The stable sensitivity result is 0 repeated-checkpoint bases at effect floors 0.025, 0.05, 0.10, and 0.15. Base 38 supplies direct long-horizon evidence for a short-lived checkpoint; base 149 has no distinct downstream/final readout, so its automated `L-Short` label is right-censored.
- Stages 2A–3C.8 must be considered jointly before acting on the single recommendation below.

## Recommendation

**EXPAND_CONFIRMED_CHECKPOINT_PAIR_YIELD:** Review the confirmed local checkpoints and resolve the documented cross-phase score-stability issue before designing any score-blind cohort expansion intended to increase independent separated checkpoint pairs.

Stage 3C.9 stops here. No sink-causality, residual-feature, unconstrained-history, Stage 4, multi-evidence, or failure-analysis experiment was started.
