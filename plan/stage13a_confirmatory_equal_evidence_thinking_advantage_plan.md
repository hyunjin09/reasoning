# Stage 13A — Confirmatory Equal-Evidence Thinking Advantage
## Outcome-Independent Full-Cohort Test of Post-Evidence Reasoning

## 0. Objective

Confirm, on the entire frozen 96-family Stage 12X/12Y cohort, whether the Qwen3-VL-4B Thinking variant retains a reliable advantage over the 4B Instruct variant **after task-critical visual evidence has been explicitly equalized and the image removed**.

Primary question:

\[
\boxed{
\textbf{Does Thinking still improve multimodal math reasoning when both checkpoints receive the exact same correct }E^*\textbf{?}
}
\]

This stage resolves the main remaining Claim 1C uncertainty from Stage 12Y-S. It is **not** a new mechanism-discovery stage.

---

## 1. Why this is necessary

Current evidence already supports:

1. **Visual evidence bottleneck.** Correct \(E^*\) rescues a substantial fraction of Native Instruct failures in both developmental and held-out cohorts.
2. **Generic CoT is insufficient.** Same-checkpoint prompted CoT does not reliably repair B1/B4.
3. **Selected-case state portability exists.** In some cases, Thinking-generated reasoning text is sufficient for Instruct to solve an otherwise failed task.
4. **Broad downstream Thinking role remains unresolved.** Stage 12Y-S showed a descriptive equal-evidence gap of about +14 pp, but its preregistered confirmation gate was not met.

Therefore the highest-value remaining Claim 1 experiment is an outcome-independent, full-cohort, multi-seed comparison:

\[
\boxed{
T_{E^*}\text{ vs }I_{E^*}
}
\]

under identical image-free evidence.

---

## 2. Paper claim first

### If positive

> **The Thinking variant remains more accurate even when both models receive the same correct task-critical visual evidence without the image, showing that its advantage is not reducible to visual evidence recovery.**

Allowed shorthand:

\[
\boxed{
\textbf{Thinking exhibits a post-evidence reasoning advantage in multimodal math reasoning.}
}
\]

This is a deployed-variant comparison, not a pure causal Thinking switch.

### If negative

> **The visual-evidence bottleneck remains robust, but the apparent downstream Thinking advantage from Stage 12Y does not survive full-cohort multi-seed confirmation.**

Do not rescue a negative result by subgroup or prompt search.

---

## 3. Competing explanations

### H1 — Evidence-side explanation

If:

\[
T_{E^*}\approx I_{E^*},
\]

then the broad native Thinking gain is compatible with being primarily upstream of or at evidence acquisition.

### H2 — Post-evidence reasoning advantage

If:

\[
T_{E^*}>I_{E^*},
\]

under identical \(Q+E^*\), then:

\[
\boxed{
\textbf{Thinking's advantage cannot be explained solely by better visual evidence recovery.}
}
\]

Possible downstream sources include state construction, multi-step derivation, error correction, or other checkpoint/post-training differences. Stage 13A does not distinguish among them.

---

## 4. Frozen cohort

Reuse exactly the Stage 12X-S final-QC-passed cohort:

\[
\boxed{N=96\text{ independent MathVision families}.}
\]

Do not add, remove, replace, or re-annotate families.

Reuse unchanged:

- original question;
- frozen \(E^*\);
- exact frozen equal-evidence rendering;
- gold answer;
- answer-equivalence policy;
- source/QC hashes.

No image is used in Stage 13A.

---

## 5. Primary conditions

For every family run:

### I-EQ

\[
Q+E^*\rightarrow I
\]

- Qwen3-VL-4B-Instruct
- no image
- exact frozen \(Q+E^*\)
- no CoT suffix

### T-EQ

\[
Q+E^*\rightarrow T
\]

- Qwen3-VL-4B-Thinking
- no image
- exact same frozen \(Q+E^*\)
- no extra reasoning instruction

The semantic user input must be identical across checkpoints.

---

## 6. Fresh replicates

Use:

\[
\boxed{3\text{ fresh frozen replicates per family per checkpoint}.}
\]

Total:

\[
96\times2\times3=\boxed{576\text{ primary calls}.}
\]

Freeze all seeds before generation.

Seed derivation:

`SHA256(stage13a-v1|family_id|checkpoint|replicate)`

Do not reuse Stage 12Y seeds. No best-of-three selection.

---

## 7. Frozen model recipes

### Instruct

- temperature 0.7
- top-p 0.8
- top-k 20
- repetition penalty 1.0
- presence penalty 1.5
- max new tokens 32,768

### Thinking

Pinned revision:

`1de27d8c51f12e819435303b9e84c4e25ba8401e`

- temperature 1.0
- top-p 0.95
- top-k 20
- repetition penalty 1.0
- presence penalty 0
- max new tokens 81,920

Primary estimand:

\[
\boxed{
\textbf{deployed Thinking-variant advantage under equal evidence}
}
\]

not a checkpoint-only or decoding-only causal effect.

---

## 8. Technical validity

Reuse:

\[
\texttt{TECHNICALLY\_VALID}
=
\texttt{INPUT\_VALID}
\land
\texttt{SCOREABLE}
\land
\neg\texttt{TRUNCATED\_BEFORE\_OUTCOME}.
\]

Rules:

- repetition is scientific behavior;
- long reasoning is scientific behavior;
- a cap hit is valid if a clear unretracted answer is already scoreable;
- pre-outcome truncation is technical missingness;
- normal-stop refusal/no-answer is scientific failure.

Never count technical missingness as incorrect in the primary estimate.

---

## 9. Blind scoring

Score all I-EQ outputs before exposing paired T-EQ outcomes.

Then score all T-EQ outputs.

Labels:

- `CORRECT`
- `INCORRECT`
- `UNSCOREABLE_TECHNICAL`

Use the frozen MathVision equivalence policy.

Perform:

- all ambiguity-triggered second reviews;
- deterministic 20% random second-pass audit.

Same-agent QC is not independent-rater reliability.

---

## 10. Primary family-level estimand

For checkpoint \(M\in\{I,T\}\) and family \(i\):

\[
\bar y_{Mi}
=
\frac{\#\text{ correct resolved replicates}}
{\#\text{ resolved replicates}}.
\]

Primary complete paired set:

\[
\mathcal F_{complete}
=
\{i:\text{all 3 I-EQ and all 3 T-EQ replicates are resolved}\}.
\]

Define:

\[
d_i=\bar y_{Ti}-\bar y_{Ii}.
\]

Primary endpoint:

\[
\boxed{
\Delta_{E^*}
=
\frac{1}{|\mathcal F_{complete}|}
\sum_i d_i.
}
\]

Report in percentage points.

---

## 11. Primary uncertainty

Use a paired nonparametric family bootstrap:

- resampling unit = family;
- 10,000 bootstrap samples;
- resample \(d_i\);
- report percentile 95% interval.

Seeds are not population-independent samples.

Also report:

- mean \(d_i\);
- median \(d_i\);
- count of positive/zero/negative family differences.

---

## 12. Confirmatory decision gate

Declare:

`EQUAL_EVIDENCE_THINKING_ADVANTAGE_CONFIRMED`

iff all hold:

1. at least 80 families are in the complete paired set;
2. \(\Delta_{E^*}\ge+5.0\) pp;
3. 95% family-bootstrap CI lower bound \(>0\);
4. checkpoint scoreability differs by no more than 10 pp, unless conservative missingness bounds preserve the conclusion.

The +5 pp threshold is a prospective minimum effect-size gate.

---

## 13. Other decision states

### `EQUAL_EVIDENCE_SIGNAL_PARTIAL`

Use if:

- \(\Delta_{E^*}>0\),
- but CI includes zero or point estimate is below +5 pp.

### `EQUAL_EVIDENCE_NO_ADVANTAGE`

Use if:

\[
\Delta_{E^*}\le0
\]

with adequate paired coverage.

### `EQUAL_EVIDENCE_TECHNICALLY_UNRESOLVED`

Use if:

- fewer than 80 paired families are fully resolved;
- or missingness/scoreability prevents a bounded conclusion.

---

## 14. Secondary majority transitions

For each checkpoint define family majority success:

\[
M_i^+=1
\]

iff at least 2/3 resolved replicates are correct.

If missingness prevents a guaranteed majority, label `UNRESOLVED`.

Report:

- `BOTH_CORRECT`
- `THINKING_ONLY`
- `INSTRUCT_ONLY`
- `BOTH_WRONG`
- `UNRESOLVED`

Key descriptive contrast:

\[
N_{T\text{-only}}-N_{I\text{-only}}.
\]

Also report an exact McNemar-style discordant-family comparison descriptively.

---

## 15. Missingness bounds

For unresolved replicate slots compute conservative lower/upper bounds on the cohort-level paired effect by assigning missing outcomes in the most unfavorable/favorable way for Thinking.

Report:

\[
\boxed{
\Delta_{E^*}^{lower},
\quad
\Delta_{E^*}^{upper}.
}
\]

Do not probabilistically impute missing outputs.

---

## 16. Output-budget sensitivity without new calls

Primary caps differ across checkpoints.

Define a `32k-comparable` subset containing families where:

- all six primary outputs are resolved;
- every Thinking output reaches a scoreable result before 32,768 generated tokens;
- no Instruct output is truncated before outcome.

Recompute:

\[
\boxed{
\Delta_{E^*}^{32k}.
}
\]

If the advantage persists, it is not explained solely by Thinking's larger 81,920-token cap.

This is not a decoding-matched comparison.

---

## 17. Optional cap-matched sensitivity

Before generation, freeze a source-only hash subset of 24 families.

Run this only if:

- the primary advantage is confirmed;
- but the 32k-comparable subset is too small or inconclusive.

Additional condition:

\[
T_{E^*}^{32k}
\]

using the Thinking checkpoint and its frozen sampling recipe but max new tokens = 32,768.

Use 3 frozen seeds.

Compare against the already-run I-EQ 32,768-cap outputs on the same subset.

This tests whether the result requires the larger Thinking token budget. It still does not isolate checkpoint from decoding.

---

## 18. Relationship to Stage 12Y

After Stage 13A inference is sealed, compare against the Stage 12Y descriptive single-run estimate:

\[
+13.98\text{ pp}.
\]

Report both, but do not pool them as independent datasets because the same 96 families are reused.

Stage 13A supersedes Stage 12Y for the cohort-level Claim 1C estimate.

---

## 19. Allowed positive claim

If confirmed:

> **Thinking's advantage in multimodal math reasoning persists even when task-critical visual evidence is explicitly equalized, showing that its benefit is not reducible to evidence recovery.**

More cautious:

> **The Thinking variant exhibits a post-evidence reasoning advantage under identical task-critical evidence.**

Do **not** conclude that state construction is the universal mechanism.

---

## 20. Relation to state-portability evidence

If Stage 13A is positive, the paper can combine:

### Broad result

\[
T_{E^*}>I_{E^*}
\]

### Selected-case existence proof

\[
R_{T,E^*}\rightarrow I^+
\]

Allowed synthesis:

> **Thinking has a broad post-evidence advantage, and in selected cases that advantage is carried by a portable intermediate reasoning state.**

Do not generalize portability to all families.

---

## 21. What a null does not rule out

A null does not rule out:

- selected-case state construction;
- item-specific downstream Thinking gains;
- evidence-side Thinking gains;
- scale-dependent effects;
- stronger downstream effects on harder task distributions.

It only rules out a sufficiently robust cohort-level equal-evidence advantage in this frozen 4B assay.

---

## 22. Why this should be the final 4B Claim 1C test

If positive, stop 4B role decomposition.

If negative or partial, do not search the same 96 families for new prompts or post-hoc subgroups.

The next question should move to scale/generalization.

---

## 23. Compute budget

Primary:

\[
576
\]

logical calls.

Optional cap-matched sensitivity:

\[
24\times3=72
\]

additional Thinking calls maximum.

Target:

\[
\boxed{<10\text{ GPU-hours}}
\]

Hard stop:

\[
\boxed{14\text{ GPU-hours}}
\]

unless separately approved.

Release all allocations before stage closure.

---

## 24. Required figures

### Figure 13A-1 — Paired equal-evidence comparison

Family-level:

\[
\bar y_{Ii}\text{ vs }\bar y_{Ti}.
\]

### Figure 13A-2 — Majority transition matrix

- both correct
- Thinking-only
- Instruct-only
- both wrong
- unresolved

### Figure 13A-3 — Stage 12Y vs Stage 13A effect

Show:

- Stage 12Y single-run descriptive estimate
- Stage 13A multi-seed confirmatory estimate
- 95% family-bootstrap interval

Do not visually imply independent cohorts.

### Figure 13A-4 — Output-budget sensitivity

Show:

\[
\Delta_{E^*}
\]

and:

\[
\Delta_{E^*}^{32k}.
\]

Include optional 32k cap-matched result only if executed.

---

## 25. Required artifacts

Produce:

1. `stage13a_equal_evidence_confirmation_spec.md`
2. `stage13a_frozen96_manifest.json`
3. `stage13a_input_hashes.json`
4. `stage13a_seed_manifest.json`
5. `stage13a_instruct_equal_evidence_results.parquet`
6. `stage13a_thinking_equal_evidence_results.parquet`
7. `stage13a_scoring_audit.json`
8. `stage13a_family_level_results.parquet`
9. `stage13a_missingness_bounds.json`
10. `stage13a_32k_comparable_sensitivity.json`
11. optional `stage13a_capmatched24_manifest.json`
12. optional `stage13a_capmatched24_results.parquet`
13. `stage13a_primary_inference.json`
14. `stage13a_decision.json`
15. `stage13a_resource_accounting.json`
16. `stage13a_summary.md`

Preserve all previous Stage 12 artifacts and source/input seals unchanged.

---

## 26. Exactly one recommendation at completion

### If `EQUAL_EVIDENCE_THINKING_ADVANTAGE_CONFIRMED`

Recommend:

> Run a cross-scale image-vs-equal-evidence study at 2B/4B/8B to test whether the functional role of Thinking changes with model size.

### If `EQUAL_EVIDENCE_SIGNAL_PARTIAL`

Recommend:

> Treat the post-evidence advantage as suggestive rather than central, and let the next cross-scale study determine whether it strengthens or disappears with scale.

### If `EQUAL_EVIDENCE_NO_ADVANTAGE`

Recommend:

> Restrict Claim 1 to the robust visual-evidence bottleneck and selected-case portability findings; do not claim a broad post-evidence Thinking advantage.

### If `EQUAL_EVIDENCE_TECHNICALLY_UNRESOLVED`

Recommend:

> Repair only the technical missingness needed to reach the frozen paired-coverage gate, without changing prompts, checkpoints, or the cohort.

Do not launch automatically.

---

## 27. Final decision target

Stage 13A exists to resolve one claim:

\[
\boxed{
\textbf{Does Thinking retain a robust advantage after visual evidence is made explicit and identical?}
}
\]

The decisive quantity is:

\[
\boxed{
\Delta_{E^*}
=
Acc(T_{E^*})-Acc(I_{E^*}).
}
\]

A positive result establishes:

\[
\boxed{
\textbf{Thinking's benefit is not reducible to visual evidence recovery.}
}
\]

and motivates the next cross-scale question:

\[
\boxed{
\textbf{Why does this post-evidence Thinking benefit appear at small VLM scale?}
}
\]
