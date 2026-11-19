# Stage10B census execution definitions

Authority: stage10b_recurrent_visual_demand_census_plan.md. Freeze before
semantic review and before revealing any per-event routing/retrieval values.

## Corpus and scope

Use every available native Qwen3-VL-2B-Thinking trajectory in the existing Stage9A
128-family MathVision cohort and Stage8A 96-family main MathVerse cohort. Exclude
Instruct arms, controlled counting, technical/calibration cases and intervention
continuations. Do not select by correctness, detector scores, length or prior
causal effects. Preserve capped/abnormal trajectories as observed-prefix evidence;
report their counts and completion-stratified sensitivity. Verify immutable source
hashes and known image/family identities; retain a single representative per
conservative independent family if a cross-corpus exact image duplicate is found.
The eligible denominator includes missing routing and all semantic negatives.
No new generation or downloads are expected.

## Semantic passes and blinding

Two independent annotation agents review identical question/image/reasoning-only
packets. Each annotates without reading the other's decisions or any detector,
routing, correctness, gold answer or causal outcome. The main agent adjudicates
disagreements using only the same semantic evidence, before opening C5 signals.
The plan expressly requests independent annotation agents/review passes (§10).

To make long traces navigable, packets contain full token-indexed reasoning plus
an exhaustive text-only index of explicit visual-demand cue paragraphs. The index
is navigation, not labels, and has no per-quarter/event cap. Reviewers may search
full prior text and inspect any unindexed passage; exact repeated paragraphs may
be read once with every occurrence retained. Explicit visual demands are the
operational scope. Report this screening limitation; absence of a nominated cue
alone does not certify semantic absence. Require a written trajectory-level
reason and evidence for negatives, and full prior-text verification for positives.

Freeze A resolution, text interval, B onset, B fact/source identity, target ROI
(if localizable), B observation onset (if present), prior-text availability,
C1/C2/C3/C4 and S1/S2/S3. C1 is semantic resolution, not factual/causal certification.
C2 requires a distinct symbolic/logical step, multistep calculation or derived
conclusion, or a ≥24-token interval with no new task-critical visual fact. Record
shorter semantically qualifying intervals explicitly; do not count boilerplate
or unresolved continuous visual inspection as a text-sufficient period.
C4 uses question/options plus all generated text strictly before demand onset:
ABSENT only if the needed B fact is neither stated nor directly inferable;
PARTIAL/AMBIGUOUS secondary, SUFFICIENT excluded. An unresolved uncertainty about
an already-stated B fact is not automatically ABSENT. Demand onset is the first
token of the clause expressing the new information need; an immediate observation
can instantiate an implicit demand only if the requested B fact is unambiguous.
Record verbatim evidence and exact character/token spans.

Retain all reviewed candidate events. Primary trajectory candidate is the earliest
event satisfying C1–C5; E2 counts any C1–C4 event once per trajectory, E3 is the
fraction of those trajectories with any C5-qualified event. Event-level extras are
secondary, never independent observations. S2 requires evidence for a return after
a second text interval; repeated mention alone is insufficient. If an event is
both multiple sequential and return, classify S2 and retain S3 as a secondary flag.

## Re-access pass

Only after both semantic annotation files and adjudication are sealed, expose
routing to two independent passes. Freeze the first32 generated tokens at offsets
0–31 from B-demand onset; routing observations use the historical documented
query-to-generated-token alignment. No post-demand window expansion.

Stage8A's exact frozen detector threshold/features/layers may be used only when
checkpoint/backend/instrumentation compatibility is established. Detector score
alone is not target specificity. For existing per-visual-token focus, map the
semantically frozen B ROI to visual tokens using saved preprocessing/grid metadata.
Define target selectivity as target mean attention per patch exceeding the mean
of the frozen disjoint irrelevant ROI (or all other image patches if no defensible
irrelevant region exists), ratio≥1.5 and target within-image mass≥0.05. Require at
least2 consecutive measured tokens satisfying these thresholds. The thresholds
are prospective operational screening rules, not a validated causal classifier.

C5: within the32-token window, either frozen-detector positive AND target-selective
routing, or target-selective routing plus an explicit B observation in that window.
Record both channels, earliest qualifying token, confidence and compatibility.
Raw image attention alone never qualifies. Image-global detector positives with
missing/unlocalizable B ROI remain ATTENTION_ONLY/TARGET_AMBIGUOUS, not clean.
Uncertain detector compatibility is routing-only. Missing/unobserved routing is
ROUTING_DATA_MISSING, not observed absence. NEW_DEMAND_NO_REACCESS requires usable
measurements showing no qualifying C5. Report known-data and missing-data bounds.

If historical routing is insufficient, freeze at most32 C1–C4 trajectories by
SHA256("stage10b-passive-repair-920260927:"+trajectory_id), stratified by dataset,
for passive teacher-forced forward-only instrumentation, never new generation.
Only repair if it can affect yield/decision, with an estimated hard GPU budget<1h.
No ablations, source edits, detector refitting or outcome-driven target changes.

## Agreement, endpoints and decision

Report raw agreement and Cohen kappa for prior availability and clean yes/no;
onset agreement within±8 native tokens, source agreement by adjudicated semantic
identity, event-detection union/matching discrepancies. Report disagreement reasons.
For nondegenerate labels, acceptable agreement for Strong GO is raw≥0.80 and
kappa≥0.60 on availability and clean status; degenerate kappa is undefined and
cannot independently certify agreement. Onset/source matched-event agreement≥0.80.
Do not improve raw agreement retrospectively using adjudicated labels.

E1: trajectories with C1–C5 / eligible. E2: C1–C4 / eligible.
E3: C1–C5 / C1–C4 trajectories. Wilson95% intervals; zero denominators are null,
not zero. Dataset-specific and pooled independent-family estimates; target-type,
S1/S2/S3, completion and length-quartile descriptive tables. E4 median/IQR and full
0–31-token timing distribution, E5 trajectory counts. No significance search.
Strong GO requires≥24 clean trajectories,≥8 per dataset and no dataset/source-type
share>75%, plus acceptable annotation agreement. Twelve–23 gives Limited GO.
If≥24 but diversity/agreement fails, at most Limited GO with the failed conditions
explicit. Fewer than12 gives No GO; missingness limits interpretation, not thresholds.

## Resources and stop

Primary CPU/annotation only; zero GPUs unless the bounded passive repair is needed.
Use project .venv and Slurm for heavy CPU analysis; up to8 GPUs remain authorized
but do not allocate unused capacity. Preserve old files and all negative cases.
Produce11 required artifacts,4 figures (explicit empty/nearest-miss panels if no
clean example), exactly one plan recommendation and STOP. No causal follow-on.
