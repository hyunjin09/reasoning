# Stage 8B.0 — Compute Once / Shared Analysis Dataset Construction

## 0. Purpose

Prepare a single frozen analysis dataset from the completed **256-example MathVision bounded census** so that Blocks 1–3 can reuse the same outcome labels, retrieval events, trajectory coordinates, and passive features without recomputation or outcome-conditioned preprocessing.

This stage is **data construction / preprocessing**, not a scientific comparison stage.

The output of Block 0 should make later analyses deterministic:

\[
\boxed{
\text{Block 0 shared dataset}
\rightarrow
\text{Block 1: correct vs wrong whole trajectory}
\rightarrow
\text{Block 2: retrieval event / L+ vs L-}
\rightarrow
\text{Block 3: recovery / refresh / wandering}
}
\]

---

# 1. Why Block 0 is necessary

The 256 native generations are already complete.

However, analysis-side preparation is not yet fully frozen. The remaining shared work includes:

- benchmark outcome scoring for all 256 examples,
- completion-state normalization,
- frozen retrieval-score reconstruction,
- token-level active-retrieval flags,
- retrieval-episode construction,
- normalized trajectory coordinates,
- passive global QK/attention features,
- reusable trajectory/event tables,
- outcome-independent review membership for later semantic annotation.

Without a shared frozen dataset, later blocks risk:

- recomputing events differently,
- changing episode definitions after seeing outcomes,
- inconsistent trajectory normalization,
- outcome-conditioned event selection,
- duplicated GPU/CPU work.

Therefore Block 0 should be completed before Block 1.

---

# 2. What Block 0 must NOT do

Block 0 must not answer:

- whether correct and wrong trajectories differ,
- whether L+ and L− differ,
- whether wrong trajectories wander more,
- whether routing fails,
- whether Value transport differs,
- whether an intervention is justified.

Block 0 must also not:

- refit the Stage 8A detector,
- change \(\tau_R\),
- inspect outcome-stratified retrieval statistics for scientific interpretation,
- run source-specific causal interventions,
- run Value patching or reinjection,
- launch paired rollouts,
- expand beyond the frozen 256-item cohort.

The role is only to construct and freeze reusable analysis artifacts.

---

# 3. Frozen cohort

Use exactly the completed Stage 8B.1a cohort:

\[
\boxed{256 \text{ MathVision examples}}
\]

consisting of:

- 32 original T=1.0 audit examples,
- 224 additional bounded-census examples.

Require exact reconciliation of:

- 256 item IDs,
- 256 image-family IDs,
- native artifact paths,
- generation receipts,
- frozen cohort order.

No item may be added, dropped, or replaced based on outcome or retrieval behavior.

---

# 4. Model / generation provenance

Preserve the canonical Stage 8B v2 generation metadata:

- Qwen3-VL-2B-Thinking
- BF16
- temperature = 1.0
- top-p = 0.95
- top-k = 20
- repetition penalty = 1.0
- presence penalty = 0.0
- max_new_tokens = 40960
- normal EOS stopping
- frozen MathVision prompt/chat preprocessing
- frozen image preprocessing / pixel handling

Block 0 performs no new native generation.

---

# 5. Benchmark outcome scoring

For every example produce a frozen label:

\[
Y^{bench}
\in
\{
\text{correct},
\text{wrong},
\text{unresolved}
\}
\]

using the frozen Qwen-compatible MathVision scoring adapter.

Important:

\[
\text{cap} \not\Rightarrow \text{wrong}
\]

and:

\[
\text{missing } </think> \not\Rightarrow \text{invalid}.
\]

For ambiguous answer extraction:

1. review the response without using ground truth where required;
2. freeze the adopted extraction;
3. only then compare to ground truth;
4. preserve automatic and manual extraction provenance separately.

Store:

- extracted answer,
- extraction method,
- source span / answer location,
- correctness,
- ambiguity flag,
- unresolved reason.

---

# 6. Completion-state normalization

For every example produce:

\[
C
\in
\{
\text{normal completed},
\text{capped},
\text{other abnormal stop}
\}
\]

and store raw flags:

- EOS present,
- `</think>` present,
- token cap reached,
- generated token count,
- final-answer section present,
- abnormal-stop subtype.

Correctness and completion remain independent axes.

---

# 7. Frozen retrieval detector

Use the Stage 8A detector unchanged.

Frozen threshold:

\[
\boxed{
\tau_R = 0.5478025980771918
}
\]

For every reasoning token \(t\), reconstruct or load:

- retrieval score \(R_t\),
- active-retrieval flag:

\[
A_t = \mathbb{1}[R_t > \tau_R].
\]

Also preserve the passive detector inputs available from native artifacts:

- visual QK competitiveness,
- visual attention mass,
- attention concentration,
- any frozen shallow/passive features actually used by the detector.

No new feature is allowed into the detector.

---

# 8. Retrieval-episode construction

Token-level active flags must be converted once into reusable retrieval episodes.

Primary episode rule:

- merge active tokens separated by at most **4 tokens**.

Secondary robustness definitions may also be materialized now:

- gap = 0,
- gap = 8.

But all later primary analyses use the frozen primary gap = 4 definition.

For every episode store:

- trajectory ID,
- episode index,
- start token,
- end token,
- duration,
- midpoint,
- normalized start position,
- normalized midpoint,
- peak retrieval score,
- mean retrieval score,
- AUC above threshold,
- preceding gap,
- following gap.

---

# 9. Normalized trajectory coordinates

For every reasoning token and episode compute:

\[
p_t = \frac{t}{L_i}
\]

where \(L_i\) is the generated reasoning-token length for trajectory \(i\).

Store standard phase bins:

- Phase 1: 0–25%
- Phase 2: 25–50%
- Phase 3: 50–75%
- Phase 4: 75–100%

Also preserve absolute token indices.

This allows later analyses to compare both:

- absolute reasoning time,
- normalized reasoning progress.

---

# 10. Shared trajectory-level base metrics

Compute and freeze the following for every trajectory.

These are descriptive base quantities only; Block 0 does not compare outcomes.

## T1 — Reasoning length

- total generated tokens,
- reasoning tokens,
- post-think/final-answer tokens where applicable.

## T2 — Retrieval episode count

\[
N_i^R
\]

## T3 — Retrieval density

Episodes per 1,000 reasoning tokens.

## T4 — Active-token fraction

\[
F_i^R
=
\frac{\#\{t:R_t>\tau_R\}}{L_i}
\]

## T5 — First retrieval timing

- absolute,
- normalized.

## T6 — Retrieval duration statistics

- mean,
- median,
- max.

## T7 — Retrieval intensity statistics

- mean peak,
- max peak,
- mean AUC.

## T8 — Inter-retrieval statistics

- median gap,
- minimum gap,
- mean gap,
- coefficient of variation where defined.

## T9 — Recurrence

- episodes after first,
- returns after >32-token gap,
- returns after >64-token gap,
- returns after >128-token gap.

## T10 — Late retrieval fractions

After:

- 25%,
- 50%,
- 75%,
- 90%

of normalized reasoning time.

These quantities are later reused by Block 1.

---

# 11. Shared phase-level table

Create a trajectory × phase table.

For each of the four normalized reasoning phases store:

- token count,
- retrieval episode count,
- retrieval density,
- active-token fraction,
- mean retrieval score,
- max retrieval score,
- mean visual QK competitiveness,
- mean visual attention mass,
- mean attention concentration,
- passive feature movement if available.

Do not compare correct vs wrong in Block 0.

---

# 12. Passive feature trajectory representation

Construct a reusable passive feature vector:

\[
z_t
\]

from frozen Stage 8A-compatible passive quantities.

Recommended components:

- retrieval score,
- visual QK competitiveness,
- visual attention mass,
- visual concentration.

Rules:

- no outcome-conditioned feature selection;
- no supervised dimensionality reduction using correctness;
- no source-specific ROI features yet;
- standardization parameters must be frozen without using correctness labels.

Store both:

- raw features,
- standardized features.

---

# 13. Shared trajectory-geometry quantities

Compute generic feature-space geometry for each trajectory.

These are cached now for later Block 1 / Block 3 use.

## G1 — Path length

\[
PL_i
=
\sum_t
\|z_t-z_{t-1}\|_2
\]

Store:

- raw path length,
- transition-normalized path length.

## G2 — Net displacement

\[
Disp_i
=
\|z_{end}-z_{start}\|_2
\]

## G3 — Tortuosity

\[
Tort_i
=
\frac{PL_i}{Disp_i+\epsilon}
\]

Freeze \(\epsilon\) before outcome comparison.

## G4 — Local angular instability

Optional exploratory cache:

- mean angular change,
- median angular change.

Block 0 computes these but does not interpret them.

---

# 14. Retrieval-event base table

Create one row per frozen primary retrieval episode.

Required columns:

- item ID,
- image-family ID,
- episode index,
- start/end/midpoint,
- normalized position,
- phase,
- peak/mean/AUC retrieval score,
- duration,
- preceding/following gap,
- global QK feature,
- global attention feature,
- concentration feature,
- benchmark outcome label,
- completion label.

The benchmark/completion labels may be attached for convenience, but Block 0 must not use them to alter event construction.

---

# 15. Outcome-independent semantic-review membership

Before Block 2, freeze which retrieval episodes will receive human/semantic review.

This selection must be made **without using**:

- benchmark correctness,
- L+/L− status,
- future causal effects.

Recommended deterministic strategy:

For each trajectory, select up to three retrieval episodes:

1. earliest eligible episode,
2. one middle episode nearest normalized position 0.5,
3. latest eligible episode.

If fewer exist, retain all available episodes.

Optional constraints:

- minimum episode duration,
- minimum separation between selected episodes.

Any constraints must be frozen before opening outcome-stratified analyses.

Purpose:

- ensure early/mid/late coverage,
- avoid reviewing only the first 1,536 tokens,
- make Block 2 review membership reproducible.

---

# 16. Semantic annotation placeholders

Block 0 should create empty frozen columns for later annotation:

- `event_semantic_type` ∈ {T, M, U}
- `local_read_outcome` ∈ {L+, L−, L?}
- `demanded_source_id`
- `alternative_source_id`
- `roi_available`
- `local_claim_span`
- `evidence_use_token`
- `same_fact_reused_later`
- `review_status`

Do not fill these using scientific interpretation during Block 0 unless the project explicitly chooses to complete annotation immediately after membership freeze.

The key requirement is that **membership is frozen before outcome-based interpretation**.

---

# 17. Source/ROI preparation metadata

For selected review episodes only, prepare metadata indicating whether source-specific follow-up is feasible.

Store:

- image source type,
- ROI localizability,
- target region available?,
- plausible alternative region available?,
- candidate label/value available?,
- source-specific replay feasible?,
- counterfactual edit feasible?

Do not yet run source-specific QK/Value replay.

---

# 18. What is intentionally deferred

The following should **not** be computed for all 256 examples in Block 0:

- source-specific QK margins,
- target-vs-alternative attention,
- target \(\alpha V\),
- post-\(W_O\) target contribution,
- visual-off causal effects,
- source suppression/switching,
- semantic Value patches,
- reinjection.

These require bounded replay or causal work and should be run later only on informative matched subsets.

---

# 19. Data integrity checks

Before freezing Block 0 outputs verify:

1. exactly 256 trajectories;
2. item IDs match frozen cohort;
3. image-family IDs match frozen cohort;
4. no duplicate native example;
5. generation metadata matches canonical T=1.0 protocol;
6. retrieval detector version/hash matches Stage 8A freeze;
7. \(\tau_R\) exact equality;
8. token indexing is consistent across native trace and retrieval features;
9. episode construction is deterministic;
10. benchmark outcome extraction provenance is preserved;
11. completion-state mapping is deterministic;
12. no scientific subset was selected using benchmark outcome.

---

# 20. Required Block 0 artifacts

Produce at minimum:

1. `stage8b_block0_cohort_manifest.json`
2. `stage8b_block0_outcome_table.csv`
3. `stage8b_block0_completion_table.csv`
4. `stage8b_block0_token_retrieval_features.parquet`
5. `stage8b_block0_retrieval_episode_table.parquet`
6. `stage8b_block0_trajectory_metrics.csv`
7. `stage8b_block0_phase_metrics.parquet`
8. `stage8b_block0_trajectory_geometry.csv`
9. `stage8b_block0_review_membership.json`
10. `stage8b_block0_roi_feasibility_table.csv`
11. `stage8b_block0_freeze.json`
12. `stage8b_block0_summary.md`

---

# 21. Block 0 freeze file

The final freeze artifact must record:

- cohort hash,
- detector hash/version,
- retrieval threshold,
- episode gap rule,
- trajectory normalization rule,
- phase boundaries,
- passive feature definitions,
- standardization parameters,
- geometry definitions,
- review membership selection rule,
- selected review event IDs,
- outcome extraction adapter version,
- completion-state rule.

After this freeze, Blocks 1–3 must reuse these definitions.

---

# 22. Block 0 completion criterion

Block 0 is complete when:

\[
\boxed{
\text{all 256 examples have a consistent outcome/completion label,
retrieval time series, retrieval episodes, trajectory coordinates,
shared passive features, and frozen review membership}
}
\]

with all required artifacts hashed and verified.

No scientific success/failure conclusion is required.

---

# 23. Immediate next step after Block 0

Proceed directly to:

\[
\boxed{
\textbf{Stage 8B.1b — Block 1: Whole-Trajectory Success/Failure Analysis}
}
\]

using the already-written Block 1 plan.

Block 1 should consume Block 0 artifacts without changing:

- cohort,
- detector,
- threshold,
- episode definition,
- normalized phases,
- trajectory geometry,
- outcome labels.

---

# 24. Scientific discipline

Block 0 is successful if it prevents analysis drift.

The goal is not to discover an effect.

The goal is to create a **single, outcome-independent computational substrate** so that later claims about:

- correct vs wrong trajectories,
- L+ vs L− retrieval,
- recovery,
- refresh,
- wandering,

all refer to exactly the same frozen trajectory representation.
