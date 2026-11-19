# Stage 3B.1 Plan — Post-Prefill Acquisition and Visual-Sufficiency Timing

## 0. Purpose

Stage 3B.1 is the next causal timing stage after Stage 3B.0.

Stage 3B.0 established:

- a real prefill-carried visual residual;
- generation-start visual cutoff preserved positive CE in many problems;
- but only 14.5% mean / 6.1% median of Stage 3A's full-vision effect was retained;
- broad post-image prefix patching transferred the residual;
- Q-only patching captured nearly all of that residual at the median.

Therefore prefill Q carriage exists, but it explains only a small fraction of the full causal visual effect.

Stage 3B.1 asks:

> **When during reasoning does task-relevant visual information become sufficiently encoded into non-visual computation such that future direct visual access can be removed without losing the original-vs-counterfactual evidence distinction?**

This stage is about **WHEN**, not yet **WHERE**.

Do not perform Q/R carrier localization, layer-wise patching, module analysis, or path analysis in Stage 3B.1.

---

## 1. Scientific Context

### Stage 2C

ROI attention was predominantly mention/verbalization-centered:

- 58/70 evidence events were mention-centered;
- only 3/70 were pre-mention leads;
- later semantic references reactivated matching ROIs.

Therefore:

\[
	ext{attention timing} 
eq 	ext{evidence-acquisition timing}
\]

Attention is secondary only in Stage 3B.1.

### Stage 3A

Localized visual counterfactuals robustly changed upcoming evidence preference before E0:

- 49/49 CE in expected direction;
- mean CE 3.2256 nats/token;
- mean sham-controlled CE 3.1864;
- 46/46 evaluable problems had positive early sensitivity by at least E0-8.

Thus visual content causally matters before explicit evidence verbalization.

### Stage 3B.0

Generation-start visual cutoff:

- positive raw CE in 42/49;
- positive sham-controlled CE in 44/49;
- only 14.5% mean / 6.1% median of full Stage 3A effect retained.

Broad post-image prefix patching transferred the surviving residual exactly.

Q-only patching recovered nearly all of the residual at the median.

Therefore:

> **Q carries a real prefill visual residual, but most evidence-specific visual influence depends on post-prefill processing and/or continued direct visual access.**

---

## 2. Main Research Question

For each Stage 3A base problem, choose a reasoning checkpoint \(	au\).

Allow normal multimodal processing up to \(	au\).

From \(	au\) onward block:

\[
oxed{
	ext{all generated-query} ightarrow 	ext{all visual-token keys}
}
\]

Then test whether the original/counterfactual evidence distinction remains.

If the model still preserves:

\[
I_o ightarrow f_o
\]

and:

\[
I_c ightarrow f_c
\]

after cutoff at \(	au\), then enough image-dependent information must already be available through non-future-visual computation by \(	au\).

This is a **causal visual-sufficiency timing test**.

---

## 3. Primary Cohort

Use the exact same frozen cohort:

- 49 unique base problems
- 45 numeric-label edits
- 4 structural edits

Primary statistical unit:

```text
base_problem_id
```

Do not create a new attention-enriched or hypothesis-enriched cohort.

All 49 should be attempted.

---

## 4. Core Intervention

For each original, counterfactual, and sham condition:

1. multimodal prefill normally;
2. teacher-force the exact frozen baseline reasoning prefix normally until checkpoint \(	au\);
3. starting with the next generated query after \(	au\), block every generated query from attending to every visual key;
4. maintain cutoff through the remainder of the strict pre-E0 reasoning prefix and through the evidence probe;
5. keep non-visual prefix and previous-reasoning attention intact.

Conceptually:

```text
PREFILL
V -> language-side states       allowed

REASONING BEFORE tau
R_t -> V                        allowed

REASONING AFTER tau
R_t -> V                        BLOCKED
R_t -> Q/P                      allowed
R_t -> R_<t                     allowed
```

Apply cutoff across all 36 language layers and all 32 logical query heads.

Do not alter:

- model weights,
- visual embeddings,
- prompt token IDs,
- reasoning token IDs,
- MLP computation,
- non-visual KV cache,
- decoding protocol.

---

## 5. Difference From Stage 2B

Stage 2B blocked selected ROIs during semantic reasoning windows that were often post-E1.

Stage 3B.1 instead:

- blocks **all future visual access**;
- begins at prospectively frozen pre-E0 reasoning checkpoints;
- keeps cutoff active through the evidence probe;
- asks when future vision becomes dispensable.

This is a different causal question.

---

## 6. Checkpoint Design

Use two complementary coordinate systems.

### A. E0-relative checkpoints

Primary set:

```text
E0 - 128
E0 - 64
E0 - 32
E0 - 16
E0 - 8
E0 - 4
E0 - 1
```

Only use checkpoints that exist for that problem.

All must remain strictly before E0.

### B. Normalized reasoning-progress checkpoints

Define the interval from the first generated reasoning token to E0.

Evaluate cutoff at approximately:

```text
0%
25%
50%
75%
90%
```

where:

- 0% = generation start and should reproduce Stage 3B.0;
- 100% = E0 and is not used as a primary checkpoint.

This captures long trajectories where acquisition may happen much earlier than E0-128.

---

## 7. Checkpoint Deduplication

Absolute and normalized checkpoints may map to the same token index.

For every problem:

1. map all requested checkpoints to exact token indices;
2. deduplicate identical token indices;
3. retain metadata showing all labels associated with each actual cutoff index.

Freeze checkpoint schedules before cohort-scale scoring.

---

## 8. Primary Causal Metric

Reuse the Stage 3A evidence-specific preference score.

For image condition \(I\):

\[
D(I)=L_o(I)-L_c(I)
\]

where \(L_o\) and \(L_c\) are length-normalized log probabilities of original and counterfactual evidence continuations.

Full-vision effect:

\[
CE_{	ext{full}}=D(I_o)-D(I_c)
\]

Cutoff effect at \(	au\):

\[
CE_{	au}=D_{	au}(I_o)-D_{	au}(I_c)
\]

Define retention:

\[
ho(	au)=rac{CE_{	au}}{CE_{	ext{full}}}
\]

Do not clip \(ho\).

Also compute sham-controlled versions.

---

## 9. Continuous Retention Is Primary

Do not define a single arbitrary handoff threshold as the primary result.

Primary analysis should use:

\[
ho_i(	au)
\]

for every problem.

The main cohort-level object is:

\[
oxed{ho(	au)	ext{ as a function of reasoning time}}
\]

This measures how much of the visual-content causal effect has become independent of future direct visual access.

---

## 10. Secondary Sufficiency Thresholds

After continuous curves are frozen, report descriptive threshold times:

```text
rho >= 0.50
rho >= 0.80
rho >= 0.90
```

Define:

\[
	au_{50}, 	au_{80}, 	au_{90}
\]

if they exist.

Also define a stricter stable sufficiency time:

> earliest checkpoint after which retention remains above the chosen threshold at every later checkpoint.

Because effects may be non-monotonic, report both first-crossing and stable-crossing times.

Do not rely on one threshold alone.

---

## 11. Monotonicity Audit

A simple handoff story predicts later cutoff should usually preserve at least as much information as earlier cutoff.

But nonlinear/redundant computation may violate monotonicity.

For each problem report:

- number of local decreases in \(ho(	au)\);
- maximum downward step;
- monotonic vs non-monotonic classification;
- whether deviations exceed numerical/control noise.

Do not force smoothing in the primary analysis.

---

## 12. Sham Controls

Evaluate sham-image cutoff scoring at the same checkpoint schedule.

Questions:

- does original-vs-sham remain stable?
- is original-vs-counterfactual retention much larger than sham perturbation?
- do late cutoffs create generic numerical instability?

Compute sham-controlled \(CE_	au\) as in Stage 3A.

---

## 13. Technical Smoke Validation

Before all 49 problems, use 3 representative numeric-label bases spanning short, medium, and long pre-E0 reasoning.

Verify:

1. no-cutoff reproduces Stage 3A full-vision CE;
2. generation-start cutoff reproduces Stage 3B.0;
3. cutoff begins at the intended next-query position;
4. no visual edge is blocked before \(	au\);
5. all generated-query→visual-key edges are blocked after \(	au\);
6. cutoff persists through the evidence probe;
7. duplicate checkpoint labels map to identical results;
8. cached/eager scoring path is fixed and validated;
9. no-op hooks are transparent;
10. no NaNs/infs occur.

Stop if smoke fails.

---

## 14. Primary Analysis A — Cohort Visual-Sufficiency Curve

For every E0-relative checkpoint report:

- N available;
- mean \(ho\);
- median \(ho\);
- bootstrap CI over base problems;
- proportion with positive sham-controlled CE;
- proportion with \(ho \ge 0.5\);
- proportion with \(ho \ge 0.8\);
- proportion with \(ho \ge 0.9\).

Do the same for normalized-progress checkpoints.

Use base_problem_id as the bootstrap unit.

---

## 15. Primary Analysis B — Sufficiency-Time Distribution

For each problem derive:

- \(	au_{50}\)
- \(	au_{80}\)
- \(	au_{90}\)
- stable versions when present

Express each in:

1. tokens before E0;
2. normalized progress from generation start to E0.

This distinguishes:

- very early sufficiency;
- mid-reasoning sufficiency;
- late pre-verbalization sufficiency;
- no pre-E0 sufficiency.

---

## 16. Primary Analysis C — Prefill Residual vs Post-Prefill Gain

Stage 3B.0 generation-start retention is the prefill-carried residual.

For each problem define:

\[
ho_{	ext{prefill}}
\]

and compute:

\[
ho(	au)-ho_{	ext{prefill}}
\]

This summarizes additional visual sufficiency established during post-prefill reasoning.

Questions:

- does the gain happen abruptly or gradually?
- is it concentrated near E0?
- are some problems almost fully prefill-sufficient?

Do not interpret this as a unique information fraction.

---

## 17. Timing-Pattern Categories

After continuous analysis, classify curves descriptively:

### S1 — Prefill-sufficient
High retention already at generation start.

### S2 — Early post-prefill acquisition
Retention rises to high levels early.

### S3 — Gradual accumulation
Retention grows progressively.

### S4 — Late acquisition
Retention stays low until near E0.

### S5 — Persistent direct-vision dependence
Retention stays low even at E0-1.

### S6 — Non-monotonic / complex
Irregular curve.

Do not exclude any category.

---

## 18. Stage 2C Attention-Timing Comparison

Only after Stage 3B.1 causal results are frozen:

1. retrieve Stage 2C ROI-attention timing for exact matching evidence events;
2. compute attention peak time relative to E0;
3. compare with \(	au_{50}\), \(	au_{80}\), and \(	au_{90}\).

Define:

\[
\Delta t=t_{	ext{attention peak}}-t_{	ext{sufficiency}}
\]

Questions:

- does causal sufficiency precede attention peak?
- does attention remain mention-centered after direct vision has become dispensable?
- does attention timing predict sufficiency timing?

This is secondary only.

---

## 19. Potential Major Finding

A particularly important result would be:

\[
t_{	ext{sufficiency}} < t_{	ext{ROI-attention peak}}
\]

for many examples.

That would support:

> **The model often becomes causally independent of future visual access before its evidence-aligned visual attention peak.**

Combined with Stage 2C, this would strengthen the methodological conclusion that attention can reflect semantic alignment after the relevant visual information has already become available elsewhere.

Do not claim this unless supported.

---

## 20. Secondary Evidence-Type Analysis

Compare:

- numeric-label edits (N=45)
- structural edits (N=4)

Structural N is too small for strong claims.

If metadata permits, numeric labels may be further described by single-token vs multi-token values, but avoid excessive subgroup testing.

---

## 21. Optional Short Free-Rollout Validation

Teacher-forced evidence preference is primary.

Optionally run matched-seed short rollouts from selected checkpoints:

- generation start;
- one mid-reasoning point;
- one late pre-E0 point.

Keep vision blocked after cutoff.

Record:

- first target-fact statement;
- original/counterfactual fact classification;
- first semantic divergence.

Use only as behavioral validation.

---

## 22. What Stage 3B.1 May Establish

If supported:

> **Most evidence-specific visual information is not fully carried at prefill but becomes progressively or abruptly sufficient during post-prefill reasoning.**

and:

> **There is a measurable reasoning-time boundary after which future direct visual access is no longer required to preserve visual-fact identity.**

and, if supported:

> **Causal visual sufficiency emerges before the later evidence-aligned attention peak.**

---

## 23. What Stage 3B.1 Cannot Establish

Do not claim:

- where post-prefill evidence is stored;
- that R is the carrier;
- that Q is updated during generation;
- Q→R handoff;
- which layer performs transfer;
- attention vs MLP mechanism;
- ROI-specific transfer;
- retrieval of evidence B from Q/R;
- LOOK/THINK states.

---

## 24. Decision After Stage 3B.1

### GO — Stage 3B.2 carrier localization

Use if:

- a substantial fraction of examples reach high visual-sufficiency retention before E0;
- timing curves are stable;
- post-prefill gain over the prefill residual is clear.

Then Stage 3B.2 should ask:

> **Where does newly sufficient post-prefill evidence live — previous reasoning states R, persistent prefix states Q/P, or distributed combinations?**

### CONDITIONAL GO — Timing refinement

Use if:

- clear post-prefill gain exists;
- but checkpoints are too sparse to localize transitions.

Then perform a finer sweep around empirical transition windows before carrier patching.

### REDIRECT — Persistent direct-vision dependence

Use if:

- most examples remain low-retention until E0-1;
- or cutoff never preserves the Stage 3A effect.

Then investigate continued direct visual-access mechanisms instead of non-visual handoff.

---

## 25. Output Structure

Create:

```text
outputs/stage3b1/
  config/
    stage3b1_config.json
    checkpoint_schedule.jsonl
    cohort_manifest.jsonl

  smoke/
    cutoff_timing_validation.md
    cutoff_timing_validation.json

  scoring/
    per_problem_timing_results.jsonl
    per_checkpoint_statistics.json
    rollout_results.jsonl

  analysis/
    retention_curves.json
    sufficiency_times.jsonl
    monotonicity_audit.jsonl
    prefill_vs_postprefill_gain.json
    evidence_type_analysis.json
    attention_timing_comparison.json
    figures/

  summaries/
    stage3b1_summary.md
    stage3b1_acceptance.json
    stage3b2_recommendation.md
```

Do not overwrite earlier artifacts.

---

## 26. Required Figures

At minimum:

1. cohort mean/median retention vs E0-relative cutoff time;
2. retention vs normalized reasoning progress;
3. per-problem retention curves;
4. distributions of \(	au_{50}\), \(	au_{80}\), \(	au_{90}\);
5. prefill residual vs maximum pre-E0 retention;
6. representative S1–S6 curves;
7. numeric vs structural evidence curves;
8. attention-peak timing vs causal sufficiency timing for the exact-overlap subset.

---

## 27. Acceptance Criteria

Stage 3B.1 technically passes if:

1. all 49 frozen bases are attempted;
2. checkpoint schedules are frozen before cohort scoring;
3. both E0-relative and normalized-progress coordinates are used;
4. generation-start results reproduce Stage 3B.0;
5. no-cutoff results reproduce Stage 3A;
6. post-\(	au\) generated-query→visual access is correctly blocked;
7. sham controls are evaluated;
8. continuous retention curves are produced;
9. threshold times are secondary to continuous analysis;
10. monotonicity is audited rather than assumed;
11. base_problem_id remains the statistical unit;
12. attention is used only in the frozen secondary comparison;
13. no Q/R patching is performed;
14. no layer/module/head/path analysis is performed;
15. a GO / CONDITIONAL GO / REDIRECT decision is written.

Technical PASS does not require a handoff-like result.

---

## 28. Stop Condition

After:

- checkpoint scheduling,
- smoke validation,
- full 49-base timing sweep,
- retention analysis,
- sufficiency-time analysis,
- prefill-vs-postprefill gain analysis,
- secondary attention-timing comparison,
- final recommendation,

**STOP.**

Do not start:

- Stage 3B.2 Q/R carrier patching;
- layer-wise localization;
- attention-vs-MLP analysis;
- head/path patching;
- multi-evidence refresh;
- correct-vs-wrong failure analysis.

Return the full Stage 3B.1 results for review.

The next stage must be designed only after jointly considering Stage 3B.1 with all prior Stage 2A–3B.0 findings.
