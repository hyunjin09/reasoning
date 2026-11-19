# Stage 3B.3-R Plan — Restoration-Control Redesign Before Layer-Wise Localization

## 0. Status and Decision

Previous Stage 3B.3 attempt:

- Technical result: STOPPED AT SMOKE GATE / FAIL
- Scientific decision: REDESIGN
- 11/12 smoke criteria passed.
- All-layer source switching reproduced Stage 3B.2 exactly.
- No-switch, self-switch, selective-window switching, cache surgery, indexing, and current-position residual patching were mechanically valid.
- The only failed criterion was the frozen coarse-window restoration sham/target ratio:

all-layer switching      sham/target = 0.003517   PASS
selective-window switch  sham/target = 0.170285   PASS
window restoration       sham/target = 0.314949   FAIL (threshold 0.25)

No 49-base layer atlas was run.

This redesign changes only the restoration-control logic. It does not alter the established Stage 3B.2 causal result or the mechanically validated selective-switch / residual-patch implementations.

---

## 1. Key Diagnosis

The original restoration sham criterion was conceptually too strict and may be mis-specified.

The existing Stage 3A sham image is a semantic-preserving rerender of the original fact.

Example:

Original:          AB = 3
Original-sham:     AB = 3, rerendered
Counterfactual:    AB = 5

In a restoration experiment, the starting condition is approximately:

O reasoning history + counterfactual visual source at all layers

Then one layer window is restored to an original-semantic source.

If the restored window truly carries evidence identity, then restoring either:

Original AB=3

or:

Original-sham AB=3

may legitimately rescue the model toward 3.

Therefore:

A semantic-preserving original sham is not an appropriate "should have zero restoration effect" control.

For restoration, original and original-sham share the same semantic evidence identity.

The previous rule:

sham restoration << original restoration

can therefore incorrectly penalize a genuinely semantic restoration effect.

This does not invalidate the selective-window sham control.

In selective switching from an original baseline, replacing a window with an original-semantic sham should remain near the original baseline, so the previously passed selective-window sham test remains meaningful.

---

## 2. Revised Control Principle

Restoration must separate:

1. semantic evidence identity
2. render/edit-pipeline variation

Use paired render controls for both semantic classes.

For each base define:

O      = original semantic fact
O_sham = independently rerendered original fact
C      = counterfactual semantic fact
C_sham = independently rerendered counterfactual fact

Example:

O:       AB = 3
O_sham:  AB = 3, rerendered

C:       AB = 5
C_sham:  AB = 5, rerendered

The causal layer test should compare semantic class O versus semantic class C, while controlling over rendering variants.

---

## 3. Counterfactual-Sham Construction

Create a new C_sham for every primary item used in restoration validation.

Requirements:

- preserves the counterfactual semantic fact exactly;
- uses the same editing/rendering pipeline family as the existing edits;
- remains localized to the same target region;
- preserves all unrelated task-relevant content;
- has the same dimensions, crop, preprocessing, and visual-token count;
- passes manual inspection.

For numeric-label examples:

O      = original number
O_sham = rerender same original number
C      = changed number
C_sham = rerender same changed number

For structural examples, only include restoration analysis if a genuinely semantics-preserving C_sham can be produced cleanly.

---

## 4. Manual Four-Image Validation

For every validation base inspect O, O_sham, C, C_sham.

Verify:

1. O and O_sham have identical target semantics;
2. C and C_sham have identical target semantics;
3. O-class and C-class differ only in intended evidence identity;
4. all four are readable;
5. no unrelated evidence changes;
6. target ROI/token layout aligns;
7. dimensions/token counts are identical.

---

## 5. Independent Method-Validation Split

Prospectively freeze a method-validation set of 8 bases.

Suggested:
- 6 numeric-label
- 2 structural if clean paired C_sham is feasible

Otherwise:
- 8 numeric-label

Use fixed seed 20260901.

Where feasible, include at least two exact-baseline-token E_d cases.

The remaining 41 bases stay untouched as the primary scientific test set.

Validation-set results are method-validation evidence, not primary localization evidence.

---

## 6. Freeze the Revised Restoration Estimand

For original-history recipient, begin with full C-semantic visual source.

For layer window W evaluate:

C_all
C_all + O_W
C_all + O_sham_W
C_all + C_sham_W

Let D be evidence preference, larger meaning stronger original-fact preference.

Define O-semantic restoration:

R_O(W) = [D(C_all+O_W) + D(C_all+O_sham_W)] / 2

Define C-semantic control:

R_C(W) = [D(C_all+C_W) + D(C_all+C_sham_W)] / 2

Primary semantic restoration contrast:

SRC_O(W) = R_O(W) - R_C(W)

Positive SRC_O means changing only the restored window's semantic evidence class from C to O rescues original evidence preference.

---

## 7. Reciprocal Restoration

Run reciprocal experiment beginning with O_all.

Restore C or C_sham in W versus O or O_sham.

Define source-oriented reciprocal SRC_C(W).

Primary bidirectional restoration contrast:

BSRC(W) = [SRC_O(W) + SRC_C(W)] / 2

Unnormalized BSRC is primary.

---

## 8. Within-Semantic Rendering Artifact Metrics

Rendering artifacts are assessed within semantic class.

Define:

A_O(W) = |D(C_all+O_W) - D(C_all+O_sham_W)|

A_C(W) = |D(C_all+C_W) - D(C_all+C_sham_W)|

and reciprocal analogues.

These measure render sensitivity while semantics remain fixed.

---

## 9. Revised Restoration Validation Gate

Freeze before running the 8-base validation set.

### Gate A — Semantic Direction

Across validation bases/windows with active restoration:

- median BSRC is source-consistent;
- bidirectional source consistency is clearly above chance.

### Gate B — Absolute Activity Floor

Do not judge artifact ratios in nearly inactive windows.

Define an active window as:

|BSRC(W)| >= 0.10 * |BRI_all-layer|

using each base's validated Stage 3B.2 BRI scale.

### Gate C — Render Artifact Relative to Active Semantic Effect

For active windows:

A_render(W) = [A_O(W) + A_C(W)] / 2

Require cohort median:

A_render(W) / |BSRC(W)| <= 0.25

### Gate D — Absolute Render Artifact Bound

Require median:

A_render(W) <= 0.05 * |BRI_all-layer|

These are method-validation gates, not scientific effect-size claims.

---

## 10. Why This Gate Is Better

The prior ratio alone had two problems:

1. same-semantic sham restoration was incorrectly expected to have near-zero rescue;
2. ratios become unstable when target restoration is small.

The revised design asks whether changing restored-window semantic class O<->C produces source-consistent effect, while separately measuring within-class render sensitivity.

---

## 11. Selective-Window Switching

The previously validated selective-window switching arm remains unchanged.

For O-history:

outside W: O visual
inside W:  C visual

Controls:
inside W: O_sham
inside W: self O

Run reciprocal direction.

No redesign is needed unless the 8-base validation reveals a new failure.

---

## 12. Current-Position Residual Patching

Retain the mechanically validated current-position residual patching unchanged.

Coarse boundaries:

- after layer 5
- after layer 11
- after layer 17
- after layer 23
- after layer 29
- after layer 35

Do not tune these using validation results.

---

## 13. Validation-Phase Experiments

On the 8 held-out method-validation bases, run:

1. no-switch controls;
2. all-layer Stage 3B.2 source switch;
3. selective six-window switch;
4. four-image semantic restoration for six windows;
5. self controls;
6. paired render controls;
7. current-position residual-patching smoke.

Do not run fine localization during validation.

---

## 14. Validation Decision

### PASS

Proceed to untouched 41-base primary layer-localization only if:

- all mechanical controls pass;
- selective-window controls remain valid;
- revised restoration Gates A-D pass;
- no unexpected semantic/render confound appears.

### RESTORATION-DROP

If selective switching and activation patching remain valid but restoration still fails the redesigned controls:

Drop restoration from the primary scientific design.

Proceed only with:
- selective-window source switching;
- cumulative source switching;
- current-position activation patching.

In this branch, make sufficiency/causal-routing claims only. Do not make necessity claims.

### STOP / REDESIGN

If paired semantic controls reveal broad edit sensitivity even in selective switching or all-layer source switching, stop layer localization and revisit the counterfactual pipeline.

---

## 15. Primary 41-Base Scientific Test

After method validation, freeze the final protocol.

Run on untouched 41 bases:

- six coarse selective layer-window switches;
- redesigned paired-semantic restoration if validated;
- lower-prefix cumulative switching;
- upper-suffix cumulative switching;
- current-position activation patching;
- sham/self/render controls.

Do not alter windows or gates after inspecting primary results.

---

## 16. Primary Scientific Quantities

Selective window sufficiency:
BWS(W)

Revised restoration:
BSRC(W)

Do not compare original restoration vs original-sham restoration as if sham should be zero.

Cumulative transfer:
lower-prefix and upper-suffix source-switch curves

Current-state transfer:
BAP(layer)

---

## 17. Layer-Mechanism Interpretation

Use all validated arms jointly.

### Narrow causal hotspot
- high BWS in narrow window
- high BSRC if restoration validated
- BAP rises immediately after same region

### Sequential transfer
- cumulative lower-prefix curve rises progressively
- selective windows show stage-specific effects
- BAP becomes strong after transfer region

### Redundant transfer
- multiple windows have high BWS
- BSRC relatively weak
- cumulative effect saturates early

### Distributed synergy
- individual BWS weak
- multi-window cumulative effect strong
- BAP transition broad

If restoration is dropped, do not infer necessity/redundancy solely from selective switching.

---

## 18. Fine Localization

Retain the original prospectively frozen fine-localization rule for the primary 41-base test.

Do not use method-validation results to choose scientific hotspots.

After coarse primary results are frozen, refine qualifying regions with 2-layer windows.

Optional single-layer refinement remains exploratory.

---

## 19. Exact-Baseline Robustness

Preserve the exact-baseline-token robustness stratum.

Report:
1. exact-baseline subset inside untouched 41 primary bases;
2. pooled 12-case secondary robustness only after all decisions are frozen.

Natural-trace claims must remain qualified.

---

## 20. Reporting the Failed Original Smoke

Preserve and report the original failure.

Suggested methodological statement:

> The initial restoration control incorrectly treated a semantic-preserving sham as a zero-effect restoration control. A prospective smoke gate exposed this mismatch before cohort-scale analysis. The restoration estimand was redesigned to contrast semantic evidence classes while measuring render sensitivity within class.

---

## 21. Outputs

Create:

outputs/stage3b3_redesign/
  config/
    redesign_config.json
    validation_split.json
    semantic_restoration_estimand.json
    revised_gates.json

  counterfactual_shams/
    <base_problem_id>/
      O/
      O_sham/
      C/
      C_sham/
      validation.md

  validation/
    paired_semantic_restoration_results.jsonl
    render_artifact_metrics.jsonl
    selective_switch_validation.jsonl
    validation_summary.md
    validation_decision.json

  primary/
    primary_41_manifest.jsonl
    coarse_window_switch_results.jsonl
    semantic_restoration_results.jsonl
    cumulative_layer_results.jsonl
    activation_patch_results.jsonl
    fine_layer_results.jsonl

  analysis/
    layer_statistics.json
    semantic_restoration_statistics.json
    render_control_statistics.json
    exact_baseline_robustness.json
    figures/

  summaries/
    stage3b3_redesign_summary.md
    stage3b3_redesign_acceptance.json
    next_stage_recommendation.md

Preserve all original failed-smoke artifacts.

---

## 22. Acceptance Criteria

The redesigned Stage 3B.3 technically passes only if:

1. original smoke failure is preserved/documented;
2. O/O_sham/C/C_sham semantics are manually validated;
3. 8-base method-validation split is frozen before new scoring;
4. remaining 41 bases stay untouched until validation passes;
5. semantic restoration estimand is frozen prospectively;
6. artifact gates use within-semantic render differences;
7. activity floor is used before ratio judgments;
8. selective-window switching remains valid;
9. current-position activation patching remains surgical;
10. restoration passes Gates A-D, or is explicitly dropped under RESTORATION-DROP;
11. no necessity claim is made if restoration is dropped;
12. primary 41-base protocol is frozen before scoring;
13. fine localization follows the prospective rule;
14. base_problem_id remains independent unit;
15. attention is not used for layer selection;
16. a clear next-stage recommendation is written.

---

## 23. Stop Condition

After:

- four-image control construction/validation;
- 8-base independent method validation;
- PASS / RESTORATION-DROP / STOP decision;
- if authorized, untouched 41-base primary analysis;
- prospective fine localization;
- exact-baseline robustness;
- final interpretation;

STOP.

Do not begin:
- attention-vs-MLP decomposition;
- head/path analysis;
- ROI-specific switching;
- Q/R long-term carrier tracing;
- multi-evidence A/B analysis;
- correct-vs-wrong failure analysis.

Return the full redesigned Stage 3B.3 result for review.
