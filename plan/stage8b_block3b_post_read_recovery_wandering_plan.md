# Stage 8B.3B — Post-Read Recovery, Evidence Persistence, and Wandering Dynamics

## 0. One-line objective

Determine what happens **after** a local visual read succeeds or fails, and identify which post-read dynamics distinguish eventual success from failure.

The central question is:

**After visual evidence is read, what determines recovery, wandering, evidence corruption, or final success?**

This stage uses the frozen Stage 8B cohort and annotations. It does **not** introduce a new intervention.

---

## 1. Why this experiment is necessary for the paper

The previous blocks established:

1. **Block 1:** final-answer correctness alone does not define a robust global retrieval phenotype.
2. **Block 2:** local visual-read failures are not characterized by a clear retrieval-activation deficit; reduced target-selective routing is the earliest coherent descriptive candidate, but the failure cohort is too small for confirmation.
3. **Block 3A / Stage 8C:** routing causality could not be identified with natural same-item switching, and visual-gain intervention did not improve development accuracy.

The strongest remaining scientific question is downstream:

**How does a local visual read propagate through later reasoning?**

The Block 2 crossing table makes this especially important:

| Local read | Final correct | Final wrong | Final unresolved |
|---|---:|---:|---:|
| L+ | 58 | 62 | 0 |
| L− | 9 | 7 | 1 |
| L? | 3 | 8 | 0 |

A correct local visual read does **not** guarantee final correctness, and an incorrect local read does **not** guarantee final failure.

Therefore visual reasoning should be analyzed as a lifecycle:

**read → preserve / revise / refresh → reuse → integrate → final outcome**

---

## 2. Main paper claims this stage may support

The stage must not choose the mechanism in advance.

### Claim A — Successful recovery after a wrong local read

> Some locally incorrect visual reads are repaired by targeted visual re-retrieval and evidence correction before the final answer.

### Claim B — Failed recovery / wandering

> Locally incorrect reads that remain unresolved are followed by repeated or unstable visual re-query, producing a wandering trajectory rather than effective correction.

### Claim C — Correct-read downstream failure

> Many final errors occur despite a correct local visual read; failure emerges later through evidence mutation, stale reuse, binding/integration error, or nonvisual reasoning.

### Claim D — Wandering is a consequence, not a precursor

> Increased trajectory tortuosity arises primarily after a local visual failure rather than before it.

### Claim E — Refresh distinguishes robust reasoning

> Successful reasoning re-engages visual evidence when a previously read fact becomes relevant again, whereas failed reasoning more often relies on stale or mutated evidence.

A null on one claim does not invalidate the others.

---

## 3. Primary and secondary contrasts

### Primary, better-powered downstream contrast

**L+ / final correct vs L+ / final wrong**

Current counts:
- L+ / final correct: 58
- L+ / final wrong: 62

Question:

> Given that the model read the local visual evidence correctly, what later dynamics distinguish final success from final failure?

This is the main inferential analysis.

### Secondary / exploratory recovery contrast

**L− / final correct vs L− / final wrong**

Current counts:
- L− / final correct: 9
- L− / final wrong: 7

Question:

> After an incorrect visual read, what dynamics are associated with recovery versus persistent failure?

Because this cohort is small, treat it as descriptive/existence-level unless family-level yield is unexpectedly stronger after deduplication.

Do not expand the natural cohort merely to force significance.

---

## 4. Frozen data scope

Use the frozen Stage 8B artifacts and annotations.

Preserve:
- 256 MathVision items
- Block 0 trajectory representation
- Block 1 retrieval episodes / geometry
- Block 2 T/M/U labels
- Block 2 L+/L−/L? labels
- Block 2 demanded-source / confuser annotations
- existing source-localizable replay measurements
- frozen Stage 8A retrieval detector and threshold

No detector refit.
No event reselection based on post-read outcomes.
No new benchmark generation in the primary analysis.

---

## 5. Read anchor

For every eligible T event define:

**t0 = first committed local visual claim/readout**

not retrieval onset.

The post-read analysis begins after the model has committed to the local visual claim.

Also retain:
- retrieval onset tR
- evidence-use token/span t0
- final-answer time tF

where available.

---

## 6. Evidence-lineage annotation

Track the same visual fact through later reasoning.

Assign later states:

### P — preserved
The same fact is reused consistently with the original local read.

### R — refreshed
The model re-engages the relevant visual source before reusing or revising the fact.

### C — corrected
An earlier L− fact is replaced by the correct visual fact.

### M — mutated
An earlier L+ fact later changes to an inconsistent value/relation without supporting visual evidence.

### S — stale reuse
The model reuses an old visual fact after a long reasoning gap without an intervening refresh when refresh would be expected.

### A — abandoned
The fact is no longer used.

### U — unresolved lineage
Later references cannot be confidently linked to the same visual fact.

These are semantic trajectory labels, not hidden-state certificates.

---

## 7. Post-read retrieval windows

For each anchor t0, measure retrieval activity in fixed windows:

- 0–32 tokens
- 0–64 tokens
- 0–128 tokens
- 0–256 tokens
- 0–512 tokens

Primary local window:

**128 tokens**

Secondary robustness:

64 and 256 tokens.

Also record the full trajectory until:
- next semantic subgoal,
- final answer,
- or generation end.

---

## 8. Analysis family 1 — Re-retrieval after a local read

For L+ and L− separately measure:

- probability of a new retrieval episode within 64/128/256 tokens
- time to next retrieval
- number of retrieval episodes in next 128/256 tokens
- same-source re-retrieval
- different-source retrieval
- retrieval burstiness after the read

Key questions:

1. Does L− trigger more immediate re-retrieval than L+?
2. Is re-retrieval associated with correction or unresolved wandering?
3. Does L+ / final wrong show unnecessary re-retrieval despite a correct read?

---

## 9. Analysis family 2 — Recovery after L−

For each L− event determine whether the wrong visual claim is later:

- corrected,
- contradicted,
- ignored,
- or persistently reused.

Define `Recovery = 1` if the trajectory later adopts the correct visual fact before the final answer.

Measure:
- correction latency
- number of retrieval episodes before correction
- same-source refresh before correction
- source switch before correction
- whether corrected evidence is subsequently preserved

Compare descriptively:

**L− / final correct vs L− / final wrong**

Primary recovery phenotype candidate:

**targeted re-retrieval → corrected evidence → successful reasoning**

versus:

**repeated unresolved retrieval → no correction → final failure**

Because of small n, emphasize family counts, exact intervals, and case-consistent patterns.

---

## 10. Analysis family 3 — Evidence mutation after L+

For every L+ event, track whether the correct visual fact remains stable.

Define `Mutation = 1` if the same visual fact later changes to an inconsistent value/relation without a valid new visual basis.

Measure:
- mutation incidence
- latency to mutation
- whether mutation follows a new retrieval episode
- whether mutation precedes final failure
- whether mutated content comes from another visible source/confuser
- whether the original correct value is later recovered

Primary comparison:

**L+ / final correct vs L+ / final wrong**

A strong result would be:

`P(Mutation | L+, final wrong) > P(Mutation | L+, final correct)`

---

## 11. Analysis family 4 — Stale evidence reuse / refresh compliance

When a previously read visual fact becomes relevant again after a substantial gap, determine whether the model refreshes it.

Define a reuse opportunity when the same fact is needed again after at least:

**128 reasoning tokens**

Primary quantity:

`RefreshCompliance = P(same-source retrieval before reuse | long-gap reuse opportunity)`

Robustness thresholds:
- 64 tokens
- 256 tokens

Compare:
- L+ / final correct
- L+ / final wrong

and descriptively recovery/failure after L−.

Possible high-value result:

> successful reasoning refreshes visual evidence before long-gap reuse, while failed reasoning more often reuses stale or mutated evidence.

---

## 12. Analysis family 5 — Retrieval-to-use latency

For each T event compute:

`Delta_RU = t0 - tR`

Compare:
- L+ vs L−
- L+ / final correct vs L+ / final wrong

This connects to the earlier finding that the visual carrier is highly local.

Question:

> Is successful evidence use more tightly coupled in time to active retrieval?

Treat as secondary because some read anchors precede detector episode onset due to annotation/detector timing uncertainty.

---

## 13. Analysis family 6 — Pre-read vs post-read wandering

This is the main vSTREAM bridge.

For every eligible anchor t0, compute retrieval-feature movement/tortuosity in symmetric windows:

- pre: [t0-w, t0]
- post: [t0, t0+w]

Primary:

**w = 256 tokens**

Secondary:
- 128
- 512

Measure:
- normalized path length
- tortuosity
- retrieval episode recurrence
- source switching where available

Define:

`DeltaWandering = Wandering_post - Wandering_pre`

Key question:

**Is trajectory wandering a precursor of local failure, or a consequence of it?**

---

## 14. Precursor vs consequence interpretation

### Pattern A — Pre-error difference
If L− trajectories are already more unstable before t0:

> wandering is a candidate precursor / risk state.

Do not call it causal.

### Pattern B — Post-error difference only
If divergence emerges mainly after L−:

> wandering is more consistent with a consequence of failed visual reading / unsuccessful correction.

This is a strong reinterpretation of vSTREAM-style trajectory differences.

### Pattern C — No local pre/post difference
Broad tortuosity may arise from other long-range reasoning dynamics.

---

## 15. Analysis family 7 — Source switching after the read

For source-localizable events track later retrieval source identities.

Measure:
- same-source return
- target→confuser switch
- confuser→target recovery
- number of source switches
- source entropy over later retrieval episodes

For L− recovery cases ask:
> does successful correction involve returning to the demanded target?

For L+ final-wrong cases ask:
> does later source switching introduce conflicting evidence?

Secondary because complete source inventories are sparse.

---

## 16. Analysis family 8 — Downstream integration after correct reads

For L+ events classify the first downstream failure, where possible:

### D1 — arithmetic/calculation
Correct visual fact retained, but arithmetic fails.

### D2 — binding/reference
Correct fact later attached to wrong object/variable.

### D3 — evidence mutation
Correct fact changes.

### D4 — stale reuse
Old fact reused without refresh when later reasoning requires verification.

### D5 — logical/integration failure
Correct local fact remains intact but later reasoning combines it incorrectly.

### DU — unresolved downstream failure

Do not force every final-wrong trajectory into a class.

This analysis supports the claim that not all multimodal reasoning failure is visual-retrieval failure.

---

## 17. Primary statistical hierarchy

### Primary family A — Correct-read downstream outcome

**L+ / final correct vs L+ / final wrong**

Primary metrics:
1. evidence mutation
2. refresh compliance
3. post-read re-retrieval within 128 tokens
4. post-minus-pre wandering

This is the main inferential family.

### Primary family B — Recovery after L−

Exploratory due to sample size:
- correction rate
- targeted re-retrieval
- correction latency
- post-read recurrence

### Secondary family C — Evidence lifecycle
- retrieval-to-use latency
- source switching
- downstream failure subtype
- same-source refresh

---

## 18. Confound controls

For the primary L+ final-correct vs final-wrong analysis, control or match by:

- reasoning position of t0
- total trajectory length
- MathVision subtype/category
- completion status
- retrieval score at corresponding T event
- local source/ROI type where available
- question length

Do not control for post-read variables that are outcomes of interest.

---

## 19. Statistical unit

Primary independent unit:

**MathVision image family/item**

If multiple eligible L+ events occur in one item:
- cluster by family
- use first eligible event as sensitivity analysis
- do not treat all events as independent

Use:
- family-level bootstrap
- clustered models where appropriate
- paired pre/post tests for within-event wandering

---

## 20. Multiplicity discipline

Freeze before opening results.

### Primary metrics
1. evidence mutation
2. refresh compliance
3. re-retrieval within 128 tokens
4. post-minus-pre tortuosity/movement

### Secondary
- correction latency
- source switching
- retrieval-to-use latency
- downstream subtype counts
- alternate time windows

Do not elevate isolated secondary significance if primary metrics disagree.

---

## 21. Annotation protocol

Semantic reviewers should be blinded where practical to:
- final benchmark correctness during evidence-lineage annotation
- passive trajectory metrics
- source-routing replay values

Recommended order:
1. annotate evidence lineage / correction / mutation / reuse;
2. seal;
3. then join final outcome labels and passive metrics.

Record rationale and text spans for every correction/mutation/stale-reuse judgment.

Report single-annotator limitation if no second reviewer is used.

---

## 22. No new generation by default

Primary Block 3B uses existing data.

Do not launch new stochastic rollouts or benchmark expansion merely to increase L− yield.

The L− recovery comparison remains exploratory under the current finite cohort.

Only consider new data after the main L+ downstream analysis is complete and only under a separate approved plan.

---

## 23. Bounded observational replay

No new replay is required for the primary analysis.

Use existing source-specific replay when available.

A small bounded replay is permitted only if needed to classify a specific post-read source switch or refresh event already selected by the frozen annotation protocol.

No causal perturbation is allowed in Block 3B.

---

## 24. Main decision tree

### Outcome A — L+ final-wrong has more mutation / stale reuse

Interpretation:

**visual read succeeds, but evidence preservation/use fails downstream**

This becomes a major failure-mechanism result.

### Outcome B — L+ final-wrong has similar evidence stability but more arithmetic/integration failures

Interpretation:

> the visual retrieval system often functions correctly; final failure is downstream reasoning.

### Outcome C — L− recovery is associated with targeted same-source refresh

Interpretation:

> re-retrieval can be healthy and corrective rather than a failure signal.

### Outcome D — L− final-wrong shows repeated unresolved retrieval / switching

Interpretation:

> failed correction produces wandering.

### Outcome E — wandering appears only after local error

Interpretation:

> trajectory wandering is more likely a consequence of local failure than its precursor.

### Outcome F — wandering is elevated before local error

Interpretation:

> unstable retrieval dynamics may precede and predict local failure.

---

## 25. Relation to vSTREAM

The intended contribution is not:

> wrong trajectories are more tortuous.

The intended contribution is:

**identify whether tortuous visual trajectories precede local visual failure or emerge from unsuccessful recovery after that failure**

This distinguishes:

- failure precursor
- failure consequence

and grounds trajectory geometry in the retrieval lifecycle.

---

## 26. Relation to intervention results

Stage 8C showed that globally amplifying visual contribution at detected retrieval moments did not improve development accuracy.

Block 3B therefore tests the alternative explanation:

**the bottleneck may not be insufficient visual signal, but what happens to evidence after it is read**

A positive post-read result would help explain why indiscriminate visual gain failed.

---

## 27. Success criteria

Block 3B is successful if at least one of the following is established robustly:

1. L+ final-wrong trajectories show a reproducible post-read evidence-use failure relative to L+ final-correct trajectories;
2. post-read wandering differs meaningfully after local success/failure;
3. recovery after L− is consistently associated with targeted refresh/correction;
4. vSTREAM-style trajectory instability can be temporally localized as pre-error or post-error.

The strongest paper result should come from the better-powered L+ comparison.

---

## 28. Stop conditions

Stop without further expansion if:

- evidence lineage cannot be reliably annotated;
- post-read events are too sparse for the primary L+ comparison;
- apparent effects disappear under family/length/position controls;
- only tiny exploratory L− patterns remain;
- no stable pre/post wandering or evidence-use difference emerges.

Do not respond by adding arbitrary windows or new taxonomies after results are opened.

---

## 29. Required outputs

Produce:

1. `stage8b_block3b_evidence_lineage.parquet`
2. `stage8b_block3b_retrieval_after_read.json`
3. `stage8b_block3b_recovery_Lminus.json`
4. `stage8b_block3b_mutation_Lplus.json`
5. `stage8b_block3b_refresh_compliance.json`
6. `stage8b_block3b_retrieval_use_latency.json`
7. `stage8b_block3b_pre_post_wandering.json`
8. `stage8b_block3b_source_switching.json`
9. `stage8b_block3b_downstream_failure_taxonomy.json`
10. `stage8b_block3b_primary_effects.csv`
11. `stage8b_block3b_summary.md`
12. exactly one final recommendation for paper emphasis

---

## 30. Key figures

### Figure 1 — Evidence lifecycle after L+
Read → preserve / refresh / mutate → final correct/wrong.

### Figure 2 — L+ final-correct vs L+ final-wrong
Compare:
- mutation
- refresh compliance
- post-read retrieval
- post-minus-pre wandering

### Figure 3 — Recovery after L−
Case/family trajectories:
L− → re-retrieve → correct/unresolved → final outcome.

### Figure 4 — Pre-error vs post-error wandering
Retrieval-feature path length/tortuosity around t0.

### Figure 5 — vSTREAM bridge
Compare:
- stable correct read
- correct read + downstream failure
- wrong read + recovery
- wrong read + persistent failure

### Figure 6 — Downstream failure taxonomy after correct visual reads
Counts:
- arithmetic
- binding
- mutation
- stale reuse
- integration
- unresolved

---

## 31. Final decision criterion

The stage succeeds if it moves the project from:

**local visual reads can succeed or fail**

to:

**the downstream fate of visual evidence explains recovery, wandering, and final reasoning success/failure**

The most valuable outcome would be a lifecycle such as:

**correct read → preserved/refreshed evidence → success**

versus:

**correct read → mutation/stale reuse/integration failure → final error**

and/or:

**wrong read → targeted refresh → correction**

versus:

**wrong read → repeated unresolved re-query → wandering → failure**

This is the intended mechanistic extension beyond descriptive success/failure trajectory geometry.
