# Stage10A prospective execution definitions

Authority: stage10a_causal_perceptual_to_textual_handoff_plan.md and the user's
subsequent authorization of up to8 GPUs. Freeze before any Stage10A outcome.

## Inputs and event selection

Reuse only the32 Stage9A.5 primary images and their64 FULL native4B Thinking
traces. No FULL regeneration, final-correctness filter, or intervention-outcome
selection. Native final validity is an explicit approved eligibility criterion.
Read the gold-free native review packet, task/image and semantic evidence only.

Define the task-critical fact as the first explicit aggregate count of the asked
attribute, not a question, an ordinal object index, or an unfinished subtotal.
An asserted singleton/only-one statement is an explicit count. The pre anchor is
immediately before that minimal evidence clause; emit is immediately after it.
Post is the earliest clearly identifiable subsequent verification, arithmetic
use or option-binding step selected in semantic review, before the native final
response channel. Option binding inside the scratchpad is allowed but flagged;
it can make post replay easy and does not by itself prove a new reasoning step
without answer information. Do not move pre earlier to remove implicit inventory
information already in the trace. Recounts and repeated facts remain unchanged.

Review parity-preferred queries (even image ID: color; odd: shape); use the other
query only if the preferred one fails semantic/completion eligibility. If either
is eligible, retain one. No query replacement after outcomes. Choose12 color and
12 shape images from eligible records by SHA256("stage10a-v1-920260927:"+image_id)
order within attribute; remaining8 images are the reserve. If exactly balanced
primary selection is infeasible, record the nearest balanced24 before inference.
If24 eligible independent images cannot be established, stop rather than expand.
Freeze every available reserve record even if fewer than8 prove eligible; never
manufacture an anchor or count an ineligible reserve as executable.

Record fact truth separately after membership freeze by comparison to the
synthetic source. It does not replace members. Text-causality analysis reports
the predeclared correct-emitted-fact stratum as well as all selected items, so an
incorrect emitted count is not silently called a correct visual handoff.

## Execution semantics

Native Qwen3-VL-4B-Thinking revision1de27d8c51f12e819435303b9e84c4e25ba8401e;
same Stage9A.5 task, options, processor, BF16, TF32 off, greedy, native EOS,
eager language/SDPA vision and native DeepStack. No extra CoT instruction.
Retain512 total generated-token budget, including replayed native reasoning
tokens. Each continuation receives512 minus its prefix token count. Edits use
their actual retokenized prefix count. No after-outcome cap change. All-example
accuracy includes missing finals as failures; completion and valid-wrong answers
are reported separately. Stage9A.5 D-106 does not justify retrospective rescue.

10A.1: fresh text-only chat contains original task/options and native assistant
reasoning prefix. No image placeholder/pixels, original KV, residual/hidden state,
or multimodal rope state is copied. Recompute a fresh text-only prefill. Preserve
native prefix token IDs for the unedited condition and native <think> template.

10A.2: reproduce each original native prefix exactly, preserve its cache, then
mask all36 decoder layers' future generated-query→image-key attention. If n
native output tokens have been emitted, cache length is prompt+n−1; the first
future prediction processes the last prefix token at absolute prompt+n−1.
Use AccessMask token_cutoff=n−1 so that this first future query is blocked.
Earlier prefix queries and their image-derived cache remain unchanged. This is
an anchor-conditioned continuation, not an image-free or latent-state erasure.
Use the validated standard mask; no new null-sink grid is authorized here.

Before science: CPU anchor/gate tests plus8 disjoint old technical queries verify
native prefix replay, cache branching/no-op, exact first masked query/all36
layers, original prefill unchanged, clean text-only inputs/cache, deterministic
text replay and native final-channel extraction. No scientific result selects
conditions. Each frozen selected prefix must also match saved native token IDs.

## Sequential inference and gates

Independent unit=image; one selected query/image; equal weights, paired anchors
and conditions,4,000 percentile bootstrap draws, seed920260927,95% intervals.
No anchor/token is an independent replicate. Report color and shape separately.

H2 point = text-only post accuracy minus pre accuracy.
H1 point = image-off post accuracy minus pre accuracy (equivalently pre damage
minus post damage against the same selected native FULL accuracy).
Operationalize "substantial" prospectively as at least10 percentage points.
For a supported H1/H2 component require this point threshold and95% lower>0.
Gate A permits the next block if either H1 or H2 has a point>=10pp; it does not
itself establish either component. If neither does, STOP with OutcomeD, preserve
all results and produce explicit not-run text-edit/2x2 artifacts. This follows
the plan's "if neither" stop; do not tighten it to require both for execution.

10A.3 uses emit, before later repetitions/option binding. Original can exactly
reuse10A.1 emit. Freeze original/counterfactual/delete/sham prefixes before this
block's outcomes: edit only the selected fact value to the next valid1–5 count
(wrap5→1), delete the minimal fact clause, and change the number's spelling
between equivalent word/digit as a token-sized semantics-preserving sham.
For explicit singleton clauses expressed with "only", a documented minimal
singular/plural clause edit supplies the counterfactual and "single"/"exactly one"
supplies the semantics-preserving sham; do not change the attribute/source.
Keep the task/options unchanged. Any required singular/plural agreement is
documented, without changing source identity or other propositions.
Semantic score = I(answer follows counterfactual count)−I(answer follows emitted
original count); unscorable/other counts score0. Primary directional differences
CF−original and CF−sham must each be>=.25 with95% lower>0; CF−delete must be>=.10
with95% lower>0 to exceed deletion-independent perturbation noise. Correct-fact
stratum and both attribute directions must agree. Deletion vs sham accuracy must
be harmful or have a two-sided95% interval excluding0. Gate B for2x2 requires
the directional CF−original and CF−sham criteria; full handoff also requires
the deletion/noise, attribute and H1/H2 criteria. No expanded edit/window search.

10A.4 only if Gate B opens: freeze12 highest semantic/source-edit confidence
primary events before2x2 outcomes (not ranked by prior intervention effect).
Fresh original/counterfactual image × original/counterfactual prefix, recomputed
consistent caches; effects measured on the same directional answer score.
Post text dominance requires E_text−E_image>=.10 with95% lower>0. A smaller pre
comparison is optional only if the same fact intervention has a valid meaning
before emission; never inject a fictitious self-generated pre fact. If that is
infeasible, report post dominance without claiming a measured dominance reversal.

Reserve only if all measured required primary point criteria favor handoff and
an associated interval includes its null/decision threshold, no technical/control
failure, and the result is not a null. Exactly the same frozen conditions; no
new cutoff/anchor. Freeze any extension manifest before execution. The optional
MathVision bridge opens only after full controlled handoff support and must use
12–16 already reviewed4B Thinking events. No Stage10B/CoT comparison.

## Compute and stop

Up to8 available authorized A6000 GPUs on nodes02/03/06/07, one worker/GPU,
4CPU/30G each, through project scheduler/Slurm. Finite queues release GPUs.
Primary144 Gate-A continuations and up to96 edit/96 dominance continuations;
reuse exact originals. Conservative .06s/token at512 gives<3 GPUh generation
plus bounded startup/validation, within7 GPUh target. Projected>10 GPUh before
optional bridge stops for simplification/approval. No long benchmark generation.

At every stop, retain raw evidence, completion accounting, explicit missing/not-run
artifacts, four figures (unmeasured panels labeled), phase/workflow/resource state
and a concise supported interpretation. No further research action is automatic.
