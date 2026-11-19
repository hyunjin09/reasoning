# Stage9A execution protocol v1

Frozen before native outcomes, 2026-09-23. Implements the approved
`stage9a_thinking_vs_cot_visual_access_regimes_plan.md`; no Stage9 follow-on is
authorized by this implementation. Earlier Stage8 results remain immutable.

## Inputs and inference

Select 128 distinct conservative image families from Stage8C v2's **unused
reserve** (1507 representatives), using its frozen largest-remainder sampler
over subject × difficulty × answer format, seed 920260923. Exclude its dev128,
held-out512, and all inherited prior-development families. These are input-only
strata: generated reasoning length is measured afterward, never selected for.
Question-derived subtype proxies are explicitly proxies, with unknowns retained.

A1 uses the official question/options without an extra instruction. A2 appends
exactly `\n\nThink step by step before answering.` A3 uses the same question as A1.
Each checkpoint uses its own packaged chat template: Instruct ends the prompt
with the assistant header; Thinking additionally opens `<think>`. Preserve this
native difference. Use the existing MathVision min/max pixels 602112/4014080,
BF16 weights, vision SDPA / language eager attention and cache. All arms share
temperature 1, top_p .95, top_k 20, repetition penalty 1, presence penalty 0,
max_new_tokens 40960, normal EOS, and the same hash-derived seed per item.
No gold answers are passed to inference; the reused preparer receives null gold.

## Measurements and boundaries

Keep full generated IDs, text, token coordinates, native inputs and passive
features. Reuse the unchanged Stage8A detector, threshold .5478025980771918,
layers 19–22, all query heads, its original max aggregation and feature order.
Also retain the raw attention/QK/concentration/entropy and per-token visual
focus. Report continuous detector scores as well as episodes. AlphaV is deferred
to bounded event replay if available; collecting full transport tensors on every
token is not required for this validation stage. Spatial token concentration is
not called semantic-source selectivity without a reviewed source inventory.

Primary reasoning span: A3 stops immediately before the first `</think>`;
Instruct stops before the first explicit final-answer declaration (`Final
answer`, `The answer is`, `Answer:`, or `\\boxed{`), unless that marker is inside
a sentence containing a subsequent reasoning paragraph. The executable rule
uses only markers in the last paragraph or a standalone final-answer heading;
ambiguous spans use all non-EOS assistant tokens and are flagged. No-marker
Instruct is an operational assistant-reasoning span, not certified hidden CoT.
Report the **common full-assistant, non-EOS span** sensitivity in all three arms,
and stratify by boundary certainty. Zero-length spans remain missing for rates;
do not divide by an artificial one-token span. Special tokens are not reasoning.
The first generated prediction has undefined reasoning-QK and detector score;
exclude it from valid-score denominators. Feature row t predicts generated token
t; no arbitrary one-token shift.

An episode is a maximal contiguous run of valid score > frozen threshold.
P1: fraction of reviewed demands with any episode-active prediction ±16 tokens
(±32 secondary), per trajectory then equal family weight. Also report onset-only
alignment. Events at edges use their observed window and flag truncation; full
window sensitivity is mandatory. P2: fraction of episode onsets strictly after
.5 normalized reasoning position (no episodes = missing, not zero). P3: number
of episodes / reasoning tokens ×1000. P4: among episodes with at least128 observed
tokens remaining after their final active token, fraction followed by another
episode whose onset is ≥128 tokens after that final active token. No subsequent
episode within the observed trace counts zero; edge-censored episodes excluded.
Report onset-to-onset gaps separately, so a long active burst cannot manufacture
a long inactive gap. Also report .25/.75 late fractions, active fraction,
duration, median/max gaps and the fully specified at-risk denominator.

## Semantic demand and causal validation

Generate outcome-masked review packets from text and source images only; do not
display correctness, detector/raw routing, or causal scores. A deterministic
explicit visual-demand phrase finder nominates at most one candidate per
normalized quarter (earliest qualifying mention), at most4 per trajectory.
Review the surrounding paragraph and source to accept/reject visual object/value
identification, comparison, revisit or source switch. Implicit/unobserved demands
remain outside this bounded sample; no-demand-candidate is not proof of absence.
Store verbatim evidence, coordinates, source identity/ROI and local readout
eligibility. Freeze these annotations before opening the measurement panel.
Analyze alignment against predeclared circular-shift controls (quarter-trajectory
offsets .25/.5/.75) and text-reviewed non-demand controls where feasible, to
distinguish demand specificity from diffuse elevation.

Select up to32 source-identifiable, locally scoreable events per arm by stable
hash order, max1 per family/arm. Aim for at least24; report any feasibility
shortfall without weakening eligibility. Prefer an existing different-value
source region as a semantically interpretable counterfactual donor. Require a
matched irrelevant ROI and sham/self donor. Reuse fixed-history source replay;
score native-vs-counterfactual local evidence strings, length-normalized,
with original, target substitution, irrelevant substitution, sham. Freeze the
event/ROI/donor/readout manifest before any causal scoring. Maintain native-prefix
and sham parity checks. Never use final-answer correctness as the local readout.
Unknown source identity/readout means ineligible, not a negative causal effect.

## Inference and go/no-go

Primary contrasts are A3−A2 for P1–P4. Same-item paired effects, equal conservative
family weights; resample entire families4000 times (seed920260924), never tokens.
Use98.75% intervals for the four primary effects; secondary95% intervals labeled
exploratory. Undefined values retain denominators and paired overlap counts.
Require at least20 contributing independent families and95% valid bootstrap
replicates for an inferential interval; otherwise descriptive/inconclusive.
Same-item A2/A3 length matching uses |log L2−log L3|≤.15; no caliper change or
outcome-selected replacement matching. Report all pair attrition.
Length-adjusted family-clustered bootstrap regression includes arm, log reasoning
length, completion, subject, difficulty, answer format and question length.
Report rank deficiency and support limits. Use both matched and adjusted results;
do not call a difference length-robust from raw counts alone. Secondary A2−A1
and subtype/leave-one-subject-out diagnostics assess heterogeneity.

Advancement requires all five approved criteria: ≥2 positive primary contrasts,
≥1 positive under length control, demand specificity, supporting local causal
source sensitivity, and evidence beyond a single subtype. Wide intervals or
causal-eligibility shortfalls are inconclusive, not equivalence. No detector-only
positive conclusion. Accuracy follows the existing MathVision adapter plus
outcome-masked extraction review and stays secondary. Complete the13 requested
artifacts and5 figures; give one recommendation and stop without launching it.

## Resource and execution bounds

Use scheduler/Slurm only, node02/node03/node06, at most4 GPUs concurrently and
only currently available capacity. Start with two available node02 GPUs if still
free. One independent worker/GPU; do not assume double-worker gains transfer
between checkpoints. Preserve all completed outputs; atomic task claims prevent
duplicate generation. Interrupted attempts are retained and require explicit
validated continuation, never silently counted as complete. Model/template and
observer token/logit parity preflight gates production. Release jobs at queue
completion; no keepalive. Initial rough budget25–55 GPU-hours for384 trajectories,
plus2–6 GPU-hours bounded causal replay; replace with measured throughput.
Store scheduler IDs, exact commands/config/source hashes, environment, GPU/node,
runtime/memory and failures. Automatic export may build text-only annotation
packets after generation; annotation and causal work are still required before
scientific completion.
