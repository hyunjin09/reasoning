# Block3B execution protocol v1

2026-09-22 KST. Implements the user-approved post-read recovery/wandering plan.
Freeze before new lineage labels or outcome/passive contrasts. Original plan,
Block0/1/2 artifacts, native BF16 trajectories and Stage8C FP32 evidence remain
unchanged. No new generation, intervention, detector fitting or cohort expansion.

## Scope and anchors

Retain all256 items,456 original review events and all148 T anchors (120L+,
17L-,11L?). Do not substitute a later error for the original local claim.
Define t0 as claim_end_token-1, the token completing the first committed readout;
retain claim_start_token as a timing sensitivity and tR=start_token. Token indices
are zero-based. Post-read windows are (t0,t0+w]; pre geometry [t0-w,t0] and post
geometry [t0,t0+w] each contain w adjacent transitions. Geometry t0 belongs to
both windows, not a duplicated transition. Use reasoning tokens up to the native
think boundary; retain generation end and final-answer/extraction location when
available. Negative retrieval-to-use latencies remain, never clipped to zero.

Use the frozen source families and add the already documented1707/1245 alias as
an analysis-family overlay. Preserve original IDs. All inference clusters this
conservative family, with first eligible event per item/family sensitivity.

## Semantic review before outcome joining

Packets contain original question/image, frozen local claim/source/label and
later native reasoning, but exclude benchmark truth, final correctness, passive
values and routing values. Hide the post-think final-answer section where present.
The main agent has seen prior aggregate results; this is practical masking, not
independent blinding. One annotator; no inter-rater-reliability claim.

Review original fact identity, later reuse/correction/mutation and explicit
visual-source engagement. Save exact quotes, character/token spans and rationale.
Review may use full text or candidate-reference windows; record what was covered.
Lexical matches retrieve passages but never create semantic labels automatically.
Any inferred relationship that needs unobserved evidence remains unresolved.

P/R/C/M/S/A/U follow the plan. Mere repeated entity names are not fact reuse.
An algebraic transformation of the same fact is not mutation. A tentative idea
immediately rejected is not an adopted change. C requires an adopted correction
of the original L- fact, checked against its source; final correctness is not
recovery evidence. M requires an inconsistent adopted change to the same L+ fact
without a valid new visual basis. No absent match is proof of abandonment or
absence of mutation. For negative incidence, require sufficient whole-remainder
coverage of the same fact; otherwise record null/U, not0. A is explicit abandonment
or well-supported complete lineage loss, not a failed keyword search.

Record each certifiable reuse opportunity, previous use and gap; long-gap primary
threshold128 reasoning tokens, sensitivity64/256. Semantic source engagement and
detector activity are separate. A refresh requires same-source engagement with
an intervening frozen retrieval episode since the previous use (episode may
overlap the engagement span or be within32 tokens). Temporal overlap alone does
not establish source identity. Without adequate semantic source coverage, refresh
is unresolved, not absent. Stale reuse additionally requires a rationale for why
verification was needed; a128-token gap alone is not a failure.

Annotate the first identifiable downstream error without final outcome labels:
D1 arithmetic, D2 binding, D3 mutation, D4 stale reuse, D5 integration, DU unknown.
Seal semantic judgments before joining final outcomes/passive metrics. Then
report taxonomy restricted to L+/final-wrong, preserving DU and causal uncertainty.
No second semantic pass to improve a weak effect after outcomes are opened.

## Passive metrics and censoring

Reuse frozen gap4 episodes and pooled four-feature standardization, without
refitting. Post windows32/64/128/256/512. New retrieval means episode onset>t0;
an episode already active at t0 is not a new return. Report episode count,
within-window incidence, time to next onset and censoring, exposure and full
remaining trajectory. Unobserved tail is not a no-return. Primary within128
contrast requires complete128-token follow-up; short trajectories remain in
census and exposure-aware descriptive reporting. Count gaps/recurrence and
burstiness=(SD-mean)/(SD+mean), requiring at least3 observed intervals.

Pre/post geometry uses standardized R/QK/visual-mass/concentration, float64,
adjacent finite pairs and epsilon1e-12 as in Block0. Report path length,
transition-normalized movement, displacement and tortuosity. Primary symmetric
window256; sensitivities128/512. Full windows required for contrasts; preserve
truncated-window records separately. Primary tortuosity is post minus pre.
Low-displacement sensitivity excludes windows below the pooled (outcome-blind)
fifth percentile, reported rather than retuned. No hidden-state/vSTREAM feature
substitution; these are retrieval-feature trajectories, not a vSTREAM replication.

Same/different-source, target/confuser transitions and entropy are reported only
where semantic identities or comparable existing source inventories support
them. Missing source inventory is not zero switching. Keep semantic and measured
source evidence distinct. New passive replay, if essential, is bounded to at most
12 already annotated transitions and6 items, selected before outcome joins with
exact prefix/source spans and original native precision. No causal perturbation.
No replay is required merely to complete an output file.

## Frozen statistical hierarchy and confounds

Four primary endpoints, wrong-minus-correct among L+:
1. semantic mutation incidence;
2. same-source refresh compliance per anchor (refreshed/identifiable long-gap opportunities);
3. new retrieval within128 tokens;
4. post-minus-pre standardized tortuosity at256.
Movement is a companion secondary endpoint, not a fifth selected primary.
Null/unknown semantic outcomes are excluded metric-wise with denominators and
worst-case missing-label bounds; no automatic missingness imputation.

Use family-equal weighting (events share a family's weight),4000 complete-family
bootstrap draws, seed820260922. Preserve all events from a resampled family.
Report raw mean differences and fully adjusted OLS wrong coefficients (binary
metrics use descriptive linear probability differences). Covariates: normalized
t0, log reasoning length, inherited Block1 subject_group, completion, R at tR,
ROI type when available, and log question length. Pool ROI types with fewer than
10 L+ anchors into OTHER; missing ROI has its own category. Freeze pooling and
continuous scaling without outcomes. Do not include post-read variables as
nuisance controls. Constant columns are removed, redundant dummy columns are
reported; unidentified/rank-deficient outcome coefficients stay null. No interval
with <95% valid bootstrap replicates. Report overlap and sample/design sizes.

Pointwise95% and Bonferroni98.75% percentile intervals across the four primary
endpoints; no primary claim from an isolated secondary interval. Robust primary
support needs the adjusted multiplicity interval excluding0, adequate exposure/
lineage coverage, and consistent first-event/normal-completion directions.
If adjustment is not identifiable, report it; do not drop controls to rescue a
claim. Pair pre/post at the event then cluster by family; for L- contrasts and
recovery, use family counts, exact binomial intervals on first eligible family
events and descriptive bootstrap contrasts. Seventeen failures remain exploratory.
All other windows, retrieval-to-use latency, source switching and downstream
taxonomies are secondary. No causal interpretation of temporal association.

## Ordered implementation and stopping

1. Verify upstream hashes; freeze event IDs, definitions and masked packets.
   Acceptance: exact256/456/148 membership; original anchors/text spans match.
2. Complete semantic lineage review and seal, with coverage/unknowns explicit.
   Acceptance: every T anchor accounted for; every positive claim has a span.
3. Extract existing passive windows; test boundary/censoring/geometry accounting.
   Acceptance: known synthetic cases and frozen geometry parity pass.
4. Join outcomes; run frozen clustered analysis and sensitivities.
   Acceptance: families/denominators preserved; no token/event independence.
5. Produce11 required outputs, six applicable figures and exactly one paper
   emphasis recommendation; preserve nulls, sparse coverage and unresolved causes.
   Stop under plan §28 without new windows, taxonomy, rollouts or another stage.

Start with bounded CPU preparation/review; submit resource-heavy CPU work with
zero GPUs through the project scheduler. If GPU calculation/replay is needed,
inspect live capacity, use only node02/node03/node06, at most4 available GPUs
total, obey host-memory caps and node06 NCCL policy, release on exit. No tmux.
No model or dataset download is expected. Repository lacks Git metadata; keep
new versioned files and checksum checkpoints rather than initialize Git.
