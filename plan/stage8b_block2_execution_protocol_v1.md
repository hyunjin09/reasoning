# Block2 execution protocol v1

2026-09-19. Execute the approved Block2 plan on the exact Block0 membership;
freeze these operational definitions before semantic labels or L-group effects.
Block0/1 scientific artifacts remain immutable. User requests two GPUs/node06
through the project scheduler and Slurm; no tmux, generation or intervention.

## 1. Annotation and alignment

Review exactly456 selected gap4 episodes in cohort/token order. All256 items
remain in census, including items without selected episodes. Packets contain
question, original image, native token context and episode coordinates, omitting
final answer/ground truth, final grade and feature values. The main annotator
has prior Block1 context; packet masking is not a claim of independent blinding.
Retain one signed review row per selected episode and its evidence/rationale.

T requires an immediate image-dependent claim whose evidence is not sufficiently
provided by question/prior reasoning. Image mention, restatement or purely
symbolic calculation is M (record mention-only or nonvisual subtype). Uncertain
demand is U. For T, independently assign L+/L−/L? from image evidence, never
from final correctness. Review the original image for every proposed T/local
verdict. Non-textbook geometric inference is not a read error merely because
its subsequent conclusion is wrong. Ambiguous image facts remain L?.

Initial context:256 tokens before onset through192 after episode end. The
immediate claim association interval is onset−16 through end+128 tokens; a
sentence crossing that boundary can be read in full, but no distant error is
substituted. Review additional earlier context/antecedents whenever needed to
certify T; if reacquisition cannot be certified, use U. Exact quote offsets,
claim start/end tokens and prior-context check notes are stored. When multiple
new claims occur, choose the earliest certifiable claim, independent of its
correctness; later claims may be mentioned but do not replace that anchor.

Define target source identity and pixel-coordinate ROI from semantics, not
attention. When possible identify the strongest semantically plausible confuser
X and an irrelevant I; missing X/I stays missing. Source sets are nonoverlapping
and mapped to native visual tokens with the existing spatial mapping. Coarse
whole-image relations may be T but not source-localizable. ROI validity and
source identifiability do not imply causal identifiability. Seal T/M/U, local
outcomes, anchors and source geometry for every member before source replay.

## 2. Frozen measurement hierarchy

P1 activation: R at episode onset; episode AUC; native episode mean visual QK
competitiveness and visual attention mass. Secondary: peak/mean R, duration,
concentration, onset R minus median of the32 strictly preceding available
R tokens (at least4 valid), and source-claim-aligned native features at the query
predicting the first evidence token. Onset/episode features are concurrent
retrieval descriptions, not automatically pre-read predictors. Event plots use
onset−32 through onset+32 and explicitly identify observed/missing support.

P2 routing, at the query predicting the first local evidence token: target−X
log-mean-exp QK and attention-share margins, target rank and target visual
attention share. Report T−I, target−rest and source identities secondarily.
Area-normalized QK prevents ROI token count masquerading as strength; include
raw summed attention and per-token attention density. Candidate source identity
sets/overlap are fixed semantically before replay; rankings are only among these
identified candidates, not an exhaustive segmentation of the image.

P3 ambiguity: normalized candidate-source attention entropy, top2 candidate
attention margin and target consensus across the frozen64 heads (layers19–22,
heads0–15). Missing confusers/candidate multiplicity cannot be replaced with
zeros. Head-margin variance, per-layer source agreement and head entropy are
secondary. Use equal head/layer averaging; no post-result head selection.

Transport is saved during the same observational pass but not compared or
interpreted until activation, routing and ambiguity analyses are written in
that order. Descriptive features: target alphaV norm and target−X norm margin,
visual alphaV norm, post-W_O target/visual contribution, visual/residual norm
ratio, head cancellation and target−X Value direction cosine. These are
observational vector contributions, never a grounding/causal score.

## 3. Replay selection and validity

Prefer every source-localizable L− T event and one matched L+ per L− without
replacement. Match subtype and ROI type exactly when available; completion
exact if feasible. Minimize absolute normalized-position difference plus
absolute R difference plus0.25 absolute log-trajectory-length difference plus
0.25 absolute log-question-length difference; deterministic event-order ties.
If exact strata lack a control, retain the L− descriptively and record the
unmatched reason; no favorable-routing selection. Matching uses only sealed
semantics and frozen native covariates. If no L− is localizable, routing contrast
is unavailable; do not manufacture controls or an alternate causal cohort.

Use original input/prompt/pixel configuration and native generated token IDs;
BF16 model, evaluation mode, exact one-token cached prefix replay, frozen layers
and heads. No sampling, off/suppression/switch/patch branches. Test passive
capture against an untouched reference query on the same prefix; verify native
metadata/image/token hashes and numerical alignment of global native features.
Record numerical parity, source token membership and actual GPU resources.
Only bounded source-localizable selected events are replayed. No rerun of native
trajectories. Two independent Slurm workers share the fixed replay manifest.

## 4. Inference and yield gate

Before inference report T/M/U, L+/L−/L?, unique family yields, source-localizable
L+/L−, completion and local×final outcome counts. Preferred64 L+ and24 L−,
stretch32 L−; report unique-family counts explicitly. If L−<24, all comparisons
remain descriptive and no robust earliest-divergence claim is made. Do not
loosen annotations, add events or expand the cohort to pass the gate.

Effects are L− minus L+. Primary means are over reviewed T events, with4000
bootstrap resamples of whole item/family clusters, seed1234, retaining all
within-item rows. Report event and independent-family denominators, means,
medians, pooled-SD standardized effects and95% intervals. Include a sensitivity
using within-family/class means to limit influence of multiple selected events.
Use fixed maximum-standardized-deviation joint intervals within the three
primary families; do not promote isolated secondary differences.

Activation adjustment includes normalized reasoning position, pooled subject,
ROI type, log question length, log reasoning length and completion when
estimable; do not control R/duration for their own activation comparisons.
Routing/ambiguity emphasize the frozen matched subset, with cluster inference
and descriptive controls for position/R/subtype/ROI/input lengths/completion.
Episode-duration control is a labeled sensitivity, not a causal adjustment.
Report rank deficiency, sparse cells, absent overlap and unidentified contrasts.
With insufficient L− families for a stable full model, report unavailable
adjustment instead of implying that covariates were controlled.

## 5. Secondary analyses and stopping

Retain L+/L− × final correct/wrong four cells; final-unresolved is a separate
column, not dropped from primary L inference. No subgroup-size-driven claims.

Demand coverage P(active|T) over all required moments is not identifiable from
retrieval-selected membership alone. Report observed local-window coverage in
the selected set as conditional/selection-induced and the population estimand
as unavailable, unless an already frozen independent semantic denominator is
explicitly present. No new review events may be added to create that denominator.
M/nonvisual frequency estimates apply to selected reviewed episodes only.

Source sequences use only replayed, source-labeled T events within a trajectory.
Report sparse-observation sequence agreement/edit distance, observed transitions,
oscillation and stale-source indicators where≥2 comparable events exist.
Continuous lag/onset timing cannot be inferred between unmeasured events; mark
unavailable. Do not call sparse sequence mismatches causal misrouting.

Write all12 required outputs and five figures, including explicit unavailable
panels/estimands when evidence is insufficient. Freeze one defensible earliest
stage or an inconclusive/no-established-passive-divergence result with yield
limits. Record one bounded handoff emphasis for Block3; do not execute it.

## 6. Implementation checkpoints

1. Input/membership/source hashes and masked packets; verify456 unique events.
2. Complete456 evidence-backed semantic reviews; validate exact alignment and
   ROI bounds; seal annotations and report the fixed yield gate.
3. Freeze replay selection/statistical definitions; test clustered sampling,
   alignment and ROI aggregation on CPU; submit twoGPU/node06 via scheduler.
4. Validate actual devices/passive parity and initial replay samples; record ETA.
5. Complete ordered comparisons, secondary limits, five figures, final freeze,
   state/handoff and resource release. No keepalive or unapproved next study.
