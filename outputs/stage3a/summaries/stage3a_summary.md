# Stage 3A Summary — Counterfactual Visual-Content Sensitivity

## Outcome

Decision: **GO**.

The frozen 49-problem pipeline is technically valid and shows strong evidence-specific pre-E0 visual-content sensitivity: CE and sham-controlled CE are positive in 49/49 independent bases; mean controlled CE is 3.1864 nats per candidate token with a 95% bootstrap CI of 2.8688 to 3.4988, while mean sham shift is 0.0392. All 46 problems with an E0-8 checkpoint satisfy the frozen early-sensitivity rule. Manual rollout audit shows the counterfactual fact in 46/49 exact cases plus one directionally changed but inexact reading, while original and sham predominantly retain the original fact. This supports a future carrier-tracing study, but does not identify V, Q, or R and does not authorize Stage 3B execution.

Stage 3A is complete. No Stage 3B, carrier patching, V/Q/R analysis, cutoff/reveal experiment, or attention-guided intervention was started.

## Cohort and validity

The frozen primary cohort contains **49 unique base problems**, one evidence item per `base_problem_id`. The project screened 115 unique bases. Round 3 ran 23 previously unseen, edit-valid problems and produced `{'correct': 19, 'wrong': 4}` before strict E0 auditing.

All primary items passed manual C0/C1/C2 review. The counterfactual changed one target visual fact, while the sham used the same target-region rendering pipeline and retained original semantics. C3 was omitted where no equally isolated task-irrelevant edit was cleanly available; the reason is recorded per item. Failed edits and raw outcomes remain preserved.
The final edit distribution is 45 localized numeric-label redraws and 4 plot-trajectory redraws.

Every primary prefix is the exact baseline generated token sequence `y_<E0`, ending at token E0-1. It excludes the first explicit target entity/referent at E0. The identical token IDs and SHA-256 hash were used for original, counterfactual, and sham conditions.

## Primary evidence-specific effect

- CE expected direction: **49/49 (100.0%)**.
- Mean CE: **3.2256 (95% bootstrap CI 2.9025, 3.5330)**; median **3.2128**.
- Mean sham-controlled CE: **3.1864 (95% bootstrap CI 2.8688, 3.4988)**; median **3.2681**.
- Mean sham shift: **0.0392 (95% bootstrap CI 0.0094, 0.0738)**; median **0.0155**.
- Target CE exceeded its absolute sham shift in **49/49 (100.0%)** problems.
- Secondary JS target-vs-sham comparison favored the target edit in **36/49 (73.5%)** problems.

Positive CE means the image counterfactual moved length-normalized fact preference toward the changed visual fact. JS is secondary and is not used as the main conclusion.

## Evidence-type breakdown

- `tier1_local_numeric_label`: N=45, mean CE=3.3377, mean controlled CE=3.2911.
- `tier3_structural_visual_edit`: N=4, mean CE=1.9644, mean controlled CE=2.0083.

## Strict pre-E0 temporal sensitivity

- E0-64: N=27, mean controlled CE=2.8515, expected-direction=100.0%.
- E0-32: N=40, mean controlled CE=2.6482, expected-direction=100.0%.
- E0-16: N=45, mean controlled CE=2.8756, expected-direction=100.0%.
- E0-8: N=46, mean controlled CE=2.8858, expected-direction=100.0%.
- E0+0: N=49, mean controlled CE=3.1864, expected-direction=100.0%.

Using the frozen early-sensitivity rule, **46/46 (100.0%)** evaluable problems had CE > 0 and controlled CE > 0 at an available checkpoint no later than E0-8. 3 problems had E0 too early to supply that checkpoint.

The curve is indexed by retained prefix length. The point labeled 0 relative to E0 is the exact `y_<E0` boundary and remains strictly before the E0 token.

## Short matched-seed rollouts

- Original image first-fact classifications: `{'neither_detected': 4, 'original_fact': 45}`.
- Counterfactual image first-fact classifications: `{'counterfactual_direction_inexact_value': 1, 'counterfactual_fact': 46, 'neither_detected': 2}`.
- Sham image first-fact classifications: `{'neither_detected': 5, 'original_fact': 44}`.
- Original-vs-counterfactual rollouts diverged within 128 tokens in **47/49** problems; original-vs-sham diverged in **44/49**.

All 22 automatically ambiguous rollout classifications plus 2 targeted false-positive checks were manually audited. These rollouts use one matched seed and validate behavior; they are not frequency estimates. Full 128-token continuations, manual resolutions, and first sentence/token divergences are retained.

## Secondary relation to Stage 2C attention

Only **9** final problems had an exact Stage 2C example/E0 event match. Pre-E0 ROI-density versus controlled CE Spearman rho was `0.5499999999999999` (two-sided p `0.12497678418833194`).

- `T2_mention_centered`: N=9, mean controlled CE=2.7823.

This moderator analysis was run after the primary cohort and causal scores were frozen. Its overlap is limited and attention is not treated as evidence acquisition or causal visual use.

## Limitations

- The cohort is deliberately enriched for clean, localized editable visual facts and may not generalize to diffuse/global evidence.
- Most edits are numeric labels; structural edits are fewer and have different artifact risks.
- The mandatory sham controls rendering artifacts, but no clean C3 irrelevant edit was available for most items.
- Teacher-forced fact probes are most natural at E0; at earlier checkpoints they remain matched evidence probes but can be less locally grammatical.
- One stochastic rollout per condition cannot estimate outcome probabilities.
- Counterfactual sensitivity establishes that visual content changes computation; it does not identify whether V, Q, or R carries that information.

## Scientific boundary

Stage 3A uses visual-content interventions, not attention magnitude, as its causal handle. It does not establish visual memory, handoff, re-grounding, LOOK/THINK states, or any specific information carrier. Raw attention remains descriptive evidence, not causal evidence.
