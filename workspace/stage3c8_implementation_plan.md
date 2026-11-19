# Stage 3C.8 Implementation Plan — Token-Type Carrier Atlas

## Scope and observable success

Execute `plan/stage3c8_plan.md` as one bounded research action. Success means the frozen 8-base validation passes, at least 56 fresh bases survive the prospective screen, Phases A--C complete on the frozen cohorts, Phase D follows its predeclared gate, all required artifacts and figures validate independently, exactly one recommendation is written, and no prohibited follow-on is started.

## Frozen design decisions

- Runtime: Qwen3-VL-4B-Thinking, seed 1234, eager attention, project `.venv`, NVIDIA RTX A5000 through the project scheduler and Slurm. A5000 is retained to avoid hardware-generation confounding with Stages 3C.3--3C.7.
- Validation cohort: the seven Stage 3C.7 validation bases plus base 3, used only for mechanics and annotation audit.
- Historical cohort: the exact 24 Stage 3C.7 primary bases, reported only as historical replication anchors.
- Fresh screening budget: 240 unique Vision Dominant bases selected without outcomes or attention. Exclude every base in the Stage 1 attempt manifest, Stage 3A candidate screen, Stage 3B.9 prospective-generation manifest, and Stage 3C.7 cohorts. Prioritize all remaining GeoQA and GEOS bases, then Geometry3K in ascending base order until 240.
- Fresh retention: completed-correct, manually valid localized numeric edit quartet, strict meaningful `E_d`, reliable ROI/layout, exact prompt tokenization, and adequate reasoning history. Retain the first 64 qualifying bases in the frozen screening order; stop at the attained cohort only if 56--63 survive all 240 attempts; fail before primary inference if fewer than 56 survive.
- Edits and annotations may be constructed after baseline correctness is known, because completed-correct is an explicit inclusion criterion, but they are frozen before any Stage 3C.8 carrier score is computed.
- Phase A: P4 layers 16--35, exact `t_pre`, K/V/K+V, A-like and B-like coordinates separately.
- Phase B: all-layer T16 suppression over `[t*-16,t*]`; all-recent K+V reference; exhaustive 16-position K+V; fixed K/V/K+V at distances 1, 2, 4, 8, 16; semantic-span and token-type group rescue; within-base recency-matched controls.
- Phase C: exact Stage 3B.0 generation-start cutoff; bidirectional single-position K+V; full-Q reference; semantic-span/type-group patches and structural controls. Type-group K/V decomposition runs only for a fresh class with at least 12 bases and robust K+V transfer.
- Robust positive rule: two-sided Wilcoxon Holm-adjusted p < 0.05 within the frozen phase family, bootstrap 95% mean CI lower bound > 0, and at least 75% positive base-level effects. Ratios are unclipped and never interpreted as unique information fractions.
- Phase D gate: run if Phase-A fresh K+V rescue is robust for either coordinate, or Phase-B all-recent rescue has median RR >= 0.50 plus a robust individual/type-group effect. Select 32 (minimum 28) longest annotation-valid fresh traces before Phase-D scores, without using Phase-A/B effect size. Landmark and semantic labels freeze first.
- Phase-D route ablation gate: run only if at least one predeclared landmark category has at least 12 base-level observations and robust future-use rescue; otherwise save an explicit gated-off artifact.
- Attention is not used for selection, annotation, intervention, ranking, or gating. Any post-freeze attention comparison is optional and secondary; it is prospectively omitted to keep this action causal and bounded.

## Ordered implementation tasks

### Task 1 — Freeze prospective cohorts and taxonomy

Create the Stage 3C.8 config, disjoint 240-base screening manifest, validation/historical manifests, token taxonomy, span rules, phase families, and sample-accounting schema.

Acceptance: hashes and IDs are immutable; cohort overlaps are zero; taxonomy precedes all carrier outputs.

Verification: deterministic manifest regeneration test and independent overlap/count audit.

### Task 2 — Generate and qualify the fresh pool

Run the 240 frozen baselines with the locked official Thinking protocol, preserve every raw outcome, construct and manually validate clean localized numeric edit quartets for completed-correct candidates, and freeze strict `E_d`, ROI, layout, token/span, visual-alignment, and reasoning-role annotations.

Acceptance: 64 target / 56 minimum unique qualifying fresh bases; all exclusions and sample-accounting stages preserved; no carrier scores exist before freeze.

Verification: raw-outcome completeness, image/pixel/layout checks, exact prefix/token hashes, and manual audit records.

### Task 3 — Implement atlas primitives test-first

Add generalized multi-position native-GQA cache rescue, deterministic token/span taxonomy helpers, recency matching, phase-specific metrics, and gated-decision helpers by extending validated Stage 3B.0/3C.4/3C.7 semantics.

Acceptance: RED tests precede implementation; position/group isolation, K/V modes, and gate rules are unit tested.

Verification: focused Stage 3C.8 plus inherited runtime regression suites pass.

### Task 4 — Mechanical validation

Run all 15 specified checks on eight held-out validation bases, including Phase-A, T16, cutoff, full-Q, all-recent, self patches, repeatability, and finite scores.

Acceptance: every mechanical check passes before fresh primary scoring; otherwise stop and repair only the failed mechanism.

Verification: independently parsed validation summary and raw audits.

### Task 5 — Phase A historical replication and fresh atlas

Reproduce the 24 historical anchors separately, then score fresh A-like/B-like `t_pre` K/V/K+V rescue and type/alignment/position summaries.

Acceptance: historical/fresh labels remain separate; no sparse class is promoted inferentially below N=12.

Verification: raw score recomputation and frozen Holm-family check.

### Task 6 — Phase B recent-reasoning atlas

Score all-recent reference, exhaustive positions, fixed K/V decomposition, span/group rescue, and recency-matched controls.

Acceptance: all eligible 16-position profiles complete; token-type claims use matched controls.

Verification: patch-selectivity audit and base-level aggregation recomputation.

### Task 7 — Phase C prompt atlas

Score full-Q reference, every eligible prompt/question position bidirectionally, spans/groups, structural controls, and only gated type K/V families.

Acceptance: cutoff and full-Q controls validate before individual-token interpretation.

Verification: cache-layout/self-patch/cutoff audit and base-level aggregation recomputation.

### Task 8 — Apply Phase D gate and run only authorized extension

Freeze the long-horizon cohort/landmarks, then run local acquisition, future use, gated necessity, and gated route controls only if the frozen gates pass.

Acceptance: non-evaluable local deficits are not counted as negative anchors; checkpoint labels require source deficit plus downstream rescue.

Verification: gate file precedes causal output and all landmark definitions hash-match the freeze.

### Task 9 — Analyze, visualize, validate, report, stop

Produce all required analyses/figures, an independent raw-artifact validator, acceptance report, one recommendation, and compact-state updates.

Acceptance: 25/25 criteria explicitly PASS/FAIL; required files are present; no sink, Stage 4, unconstrained search, residual-feature, or failure output exists.

Verification: repository-owned tests, compilation, required-file audit, and independent metric recomputation.

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Fewer than 56 clean fresh bases | Primary stage cannot pass | Use 240 prospectively frozen attempts; do not relax criteria; stop transparently if still short. |
| Manual edit/annotation load | Annotation mistakes | Generate only first, audit completed-correct candidates in frozen order, retain image sheets and per-base review records. |
| Single-token patch confounded by tokenization | False lexical null | Preserve lexical spans and run separate span/group assays. |
| Position confounds token type | Invalid taxonomy claim | Require within-base recency-matched controls before class claims. |
| Phase-C residual absent | Individual-token null uninterpretable | Mandatory full-Q positive-control gate. |
| Phase-D narrative overreach | Unsupported checkpoint claim | Require both evaluable causal source deficit and downstream cache rescue; retain necessity as supportive only. |
| Compute exceeds current allocation | Incomplete action | Use resumable shards and submit subsequent A5000 jobs through the project scheduler/Slurm. |

## Stop boundary

Stop after the Stage 3C.8 recommendation. Do not start sink manipulation, residual feature learning, Stage 4, multi-evidence refresh, failure analysis, or any experiment selected recursively from the result.
