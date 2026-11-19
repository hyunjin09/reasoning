# Stage6B execution checklist

Approved source: `plan/stage6b_causal_retrieval_dynamics_mirage_analysis_plan.md`.
User authorization: 2026-09-09; use only the two GPUs in tmux session 9 and do
not request additional Slurm resources.

Status: **COMPLETE / STOP, 2026-09-10 KST.** C2, both C1 analyses, exact dynamics,
geometry, C3, C4, sink summaries, all 24 figure categories and final reporting are
complete. Technical acceptance is 21/21 PASS; all 24 CPU tests pass. Only the two
existing GPUs were used. The sole recommendation is Cohort/Assay Repair, and no
next-stage experiment was started. Cache-path exceptions are disclosed in the audit.

## Fixed prerequisites

- [x] Read access/compute policies, the full Stage6B plan, relevant Stage6A state,
  release summary, frozen splits and promoted lessons D-048 through D-056.
- [x] Verify existing Slurm110860/node03/tmux9:1: two RTX A6000 GPUs, four CPUs,
  90G host RAM. No new allocation.
- [x] Recompute the Stage6A release hash and cohort/split counts.
- [x] Verify 2,989 referenced image/mask files and 5,949 raw files for all 1,983
  controlled release events; all 109 C1 native readout boundary records exist.
- [x] Confirm required dataset roots and the model checkpoint are local; no
  dataset download. Cache-path exceptions are recorded in the audit.
- [x] Inspect Stage4A exact source suppression, Stage5A passive telemetry and
  Stage6A input preparation interfaces.
- [x] Updated AGENTS.md resolves the missing-skill issue and directs execution of
  the approved plan. No separate skill or authorization is required.

Evidence: `outputs/stage6b/audit/input_preflight.json` and
`outputs/stage6b/audit/allocation_preflight.txt`.

## Implementation and mechanics

- [x] Add Stage6B-specific preparation and two-rank launchers; do not change the
  historical four-GPU launchers or Stage6A frozen inputs.
- [x] Record scheduler bookkeeping for work inside existing allocation110860;
  never call a launcher that submits a new allocation.
- [x] Freeze source roles, readout orientation, semantic sampling, W2/W8 scope,
  statistical families, and discovery/confirmation execution boundaries.
- [x] Preserve the repaired cached BF16 path: 2,048-token maximum generated
  chunks, fixed allocator release, matched eight single-query barriers, model
  revision and GQA/RoPE semantics.
- [x] Verify source-mask/token maps, fresh-condition prefill, unchanged prefix
  text, no-image interface, unchanged native/no-op replay, suppression arithmetic,
  all36 layers/all32 heads, finite scores and identical repeated scores on both
  assigned devices before primary scoring.
- [x] Store exact commands, runtime code/config hashes, raw candidate scores,
  GPU memory/time, per-event results and restart checks.

Verification: meaningful CPU tests under `scripts/stage6b/tests/`, then bounded
GPU mechanics inside110860. GPU validity must be observed before primary runs.

## Phase A: C2 factorial

- [x] Freeze all31 source-valid families and all124 events, with exclusions only
  for documented mechanical/readout failures.
- [x] Distinguish fixed focal ROI (Stage6A source T) from currently demanded ROI
  (T in AR/R_only; X in A_only/Neither). Every cell requires visual information;
  focal-source non-demand is not global image independence.
- [x] Score focal/demanded/alternative sources with W2, demanded-source W8, and
  validated irrelevant controls where available. Preserve both candidate logPs.
- [x] Extract layers28–29 all-head passive features and descriptive historical
  head summaries; report factorial source-specific contrasts with correct roles.
- [x] Use only12 discovery families to freeze high-attention/matching criteria;
  apply unchanged to19 confirmation families. Preserve insufficient yield.
- [x] Produce statistical contrasts and the five-condition claim assessment.

## Phase B: C1 fixed-prefix stress and native behavior

- [x] Freeze intact target readouts and identical textual prefixes for all109
  retained bases, with separate x/x-prime semantics and wrong-token orientation.
- [x] Score all11 declared fixed-prefix image/no-image conditions. Score target
  W2 for intact, mild, strong, mask and three shams; confirmation W8 for intact,
  strong and mask. Do not invent visual VSD for no-image.
- [x] Save candidate probabilities, margins, entropy and distribution information
  sufficient for declared JS/top-k/no-image comparisons.
- [x] Validate counterfactual followability against render sham. Keep native
  condition features separate from fixed-prefix results.
- [x] Freeze a discovery-only mirage rule, then apply unchanged to confirmation.
  Report continuous sham-controlled divergence before thresholded counts.

- [x] Complete the separate B2 extraction of14,906 native endpoints; completed
  after100 initial controls plus10 long-context exact controls, with all110
  mechanics-to-primary endpoint comparisons exact. V3 changes
  execution order only; all14906endpoint records remain frozen.

## Phase C: C1 causal demand dynamics

- [x] Verify independently localized sources and valid readouts on both sides
  of transitions; freeze first-up-to-two transition/no-change pairs and first
  refresh per eligible base before causal scoring.
- [x] Assess the plan's panel-size gate after full eligibility and matching.
  Preflight candidate counts are not an accepted dynamic panel.
- [x] Score demanded, previous, available plausible alternative and validated
  irrelevant sources; predeclare W8 subset and adjacent-span latency window.
- [x] Freeze effect floor/dominance margin on discovery; retain MIXED, NONE and
  UNRESOLVED. Classify switching, wandering, fixation and refresh causally.
- [x] Audit error-oriented readout eligibility before any error-promoting claim.
  The selected numeric claims are correct; geometric-role errors remain unmeasured
  by that contrast, so no error-promoting source is claimed. Outcome strata follow labels.

Panel outcome:20bases,34transitions,0matched no-change pairs,19refresh pairs.
The minimum gate fails; descriptive exact-anchor reporting only.

## Phase D: trajectory geometry

- [x] Extract predeclared passive vectors at reviewed native endpoints and exact
  causal vectors only where measured; do not impute causal source identity.
- [x] Fit normalization/PCA only on discovery; confirmation projection only.
- [x] Report loadings, explained variance, original-space and PCA-space path
  metrics, and demand coupling. PCA cannot define causal failure states.
- [x] Keep the optional surrogate off. Exact anchors support descriptive overlays;
  a surrogate cannot repair missing semantic/readout eligibility.

## Phases E/F and synthesis

- [x] C3: analyze63 present families across seven conditions and73 absent families;
  no fabricated absent-target ROI, and mask+yes is not automatically hallucination.
- [x] C4: project controlled signatures onto the frozen10 cases/10 controls and
  predeclared wrong-claim anchors, with individual examples and exploratory scope.
- [x] Save passive sink features and descriptive controls; no sink intervention.
- [x] Apply paired/base-level statistics,10,000 base bootstraps, within-family
  Holm correction and the frozen robustness gate. Report dataset/template limits.
- [x] Produce the24 required figure categories, audits, paper-claim assessment,
  rescue-readiness assessment, summary and21 technical acceptance checks.
- [x] Produce exactly one supported next-stage recommendation and STOP. No
  rescue, training, representation substitution or natural-cohort extension.
