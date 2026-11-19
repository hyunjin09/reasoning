# Stage9A direct visual-access dynamics: execution protocol v1

Frozen2026-09-24 before new masking outcomes. Implements the user-approved
`stage9a_direct_cot_thinking_visual_access_dynamics_plan.md` and supersedes the
cancelled VAB reimplementation action. New evidence: `outputs/stage9a_dynamics/v1`.
Prior pilot and stopped VAB preparation are preserved; no synthetic main task,
full layer/time grid, prompt change or automatic later-stage launch.

## Execution steps and acceptance

1. Preserve/cross-check existing128-family,384-trajectory inputs and annotations;
   freeze interventions, controls, analysis family and readout inventory.
2. CPU mask/window tests then12 bounded actual-model examples (four families ×
   three arms) for V1–V6. Require exact full-access logits/tokens and sampled
   native-prefix identity; inspect reopened access and null-sink probabilities.
3. Execute only the frozen cumulative/local/demand/control conditions on the
   validated path, recording complete continuations, extraction and failures.
4. Freeze outcome-masked extraction decisions, aggregate with4000 family
   bootstraps, run preselected redistribution controls and heterogeneity checks.
5. Produce12 required artifacts and five figures, one gated recommendation,
   release resources and STOP. A positive result alone permits the bounded
   optional query-text control; it does not authorize Stage9B.

## Native baseline and sampling

Reuse exact pilot cohort, D/C/T prompts, model snapshots, preprocessing and
annotations. Preserve539 accepted explicit demand events and the50 reviewed
local source/readout events. No selection by previous causal effect size.
Primary model protocol remains pilot BF16, language eager/visionSDPA, temperature1,
top_p.95, top_k20, repetition penalty1, presence penalty0, native EOS, cap40960,
same item seed. The new plan does not require changing sampling to greedy;
retaining the approved native protocol permits baseline reuse. Greedy checks
are technical no-op checks, not a replacement scientific cohort.
The mask-disabled/full path must be bit-identical in bounded tests. Every reused
native artifact retains its original hashes. If compatibility fails, diagnose
the implementation before choosing any new baseline; no cross-backend contrast.

## Layer and time coordinates

Use **repository decoder indices19,20,21,22**, exactly the established Stage8A/
pilot window (one-based decoder layers20–23). No conversion to a different
window. All query heads in those layers are treated.

Let P be prompt length. Absolute query positionP is the first already-generated
token; it predicts zero-based generated token1. Define its intervention-time
coordinate t=absolute_query−P+1. The last prefill query predicts generated token0
and is always unchanged. Existing demand/logit coordinates index the predicted
token, so a mask centered on demand d modifies the query predicting token d.
Document this one-token autoregressive distinction in results; no silent shift.

Cumulative cutoff c masks all generated queries with t>c; FULL never masks.
Cutoffs0,16,32,64,128,256,512,1024,2048,4096,FULL.

Local windows use the **frozen native primary reasoning span**, not the length
of the perturbed rollout. Map each of its non-special token indices into ten
equal bins using floor(kL/10), floor((k+1)L/10). Store native-coordinate half-open
intervals; empty/unmaskable windows have explicit zero exposure. Window boundaries
stay fixed after divergence. Intervened generation continues naturally to EOS/
the original total cap, even after the native span ends. This estimates the
effect of scheduled removal relative to native reasoning, not a dynamically
reidentified semantic phase. Report uncertain boundaries and capped baselines;
stratify normal-completed/certain-boundary support as sensitivity.

Demand windows are [d−r,d+r+1), r16 primary and32 secondary, intersected with
the native reasoning span and generated-query positions≥1. For each radius,
choose a same-width control within that span, using cyclic half-length shift,
then quarter/three-quarter shifts, then nearest valid center in stable order.
Exclude overlap with every accepted demand's ±32 neighborhood. This control is
called **shifted-time without an annotated demand**, not certified demand-free.
Reuse reviewed rejected-event centers first when they satisfy width/exclusion.
If no control exists, preserve the event as unpaired; exclude it from the paired
demand-minus-control endpoint and report attrition. Do not convert unknown to0.
All accepted events remain in the inventory, independent of source-readout
availability. Average events within a trajectory/family before arm comparisons.

## Attention operation and controls

For active queries in selected layers, set image-key attention logits to negative
infinity before softmax. Preserve causal masking, all prior K/V and prefill.
Later generated caches evolve naturally under the intervention; no history
reset after a knockout. No removal of image-derived residual/text information.

The matched null-sink control uses unchanged probabilities on real non-image
keys and sends removed image probability to a zero-Value virtual sink. It is
algebraically equivalent to a dummy nonvisual sink without adding a cached
position. Do not renormalize remaining real keys. Run on32 preselected families
(stable hash), all three arms, local windows0and7, cumulative128 and earliest
accepted paired demand16 where available. Preserve unavailable demand controls.
No effect-size-based representative selection.

Optional query-text bypass control only after a positive primary late effect:
use the same preselected families and predeclared late windows showing support;
add image-key masking to user question-text queries in the same four layers.
This changes prefill deliberately and is separate from the primary assay.

## Technical and continuation validation

CPU tests verify selected layers, prefill invariance, interval starts/stops,
cutoff exclusivity, zero probabilities and null-sink mass behavior. Actual-model
preflight uses four stable-hash families across three arms, at most128 generated
tokens per comparison. Disabled/full greedy and sampled outputs/logits must
match exactly; sampled prefix must match archived native tokens. Full sentinel
and disabled paths use the same backend and raw-logit tolerance0.
Fixed teacher-forced cached/chunked transition tests verify mask activation and
reopening; cached/native no-mask readouts must be exact. Full-sequence BF16
comparison is diagnostic with predeclared absolute tolerance.25 and identical
top token; it does not replace the exact production-path no-op gate.

Reuse FULL and any condition with no masked query before native termination by
an explicit identity proof. Reuse identical intervals within a trajectory with
an alias record. No interpolation, extrapolation or assumed scientific nulls.
Prefix sharing is allowed only after same-cache/RNG continuation identity is
verified. Sampling seeds and total generation budget remain unchanged.

## Scoring and local evidence

Preserve reviewed native correctness and raw adapter scores. New outputs use the
unchanged MathVision adapter plus literal outcome-masked extraction review;
byte-identical native outputs inherit the exact prior extraction. Save raw and
reviewed versions, missing as unscorable/no credit, not known wrong. Full128 per
arm is the primary no-credit denominator; scorable-only is sensitivity. No gold
is passed to inference or extraction review. First divergence compares token IDs.

For the previously frozen50 local readout events, run teacher-forced original
continuations under the same demand/control masks and score original local
evidence log probability; baseline and perturbed paths share observed text.
Also retain donor-counterfactual oriented preference where feasible using the
existing fixed strings. These are secondary local readouts, not substitutes for
free-rollout final accuracy. Other events remain explicitly without a validated
local evidence assay. No prior effect sizes determine inclusion.

## Primary inference frozen before execution

Independent unit is family; all128 are present in each arm.4000 paired family
bootstrap draws, seed920260924. Damage is native correctness minus intervened
correctness, equal family weighting. Cluster all events/windows together.
Minimum20 paired families and95% valid draws for inferential intervals.

Primary simultaneous family comprises12 contrasts:
- C1: Thinking−CoT cumulative damage at512,1024,2048,4096 (4).
- C2: Thinking−CoT local-window damage in bins5–9 (5).
- C3: Thinking−CoT mean damage over bins5–9 (1).
- C4: Thinking−CoT demand-minus-control damage at radius16 (1).
- P4 semantic late support: Thinking demand-minus-control damage among native
  demands at normalized position≥.5, radius16 (1).

Use Bonferroni two-sided confidence1−.05/12 for the primary family, plus labeled
exploratory95% intervals for full profiles and all other summaries. Undefined
support remains missing; event-only counts do not become independent n.
Radius32, local evidence probability, completion/length/divergence, Direct
ordering, common-generation exposure and normal/certain-boundary subsets are
secondary. Report all subject counts and leave-one-subject-out contrasts;
unknown fine subtypes stay unknown.

Advance recommendation requires supported positive late Thinking damage and a
Thinking−CoT difference, semantic demand support, preserved null-sink direction
with adequate support, and no single-subject dependence, as plan §34. Isolated
positive bins without multiplicity control do not qualify. Null/negative or
insufficient support is valid; do not tune prompts, masks, doses or cohorts.

## Resource limits

Reuse local data and models, no downloads. Scheduler/Slurm only; up to4 available
GPUs on node02/node03/node06/node07. Prefer healthy node06 while node07 startup
I/O remains unvalidated. Every job is bounded and releases at exit. No tmux or
keepalive. Estimate compute from observed rollout lengths and prefix reuse, not
from GPU count alone; the full MathVision continuations may take substantially
longer than the usage pilot. No additional GPU allocation beyond this ceiling.
