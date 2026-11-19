# Stage 13B — Cross-Scale Role of Thinking in VLM Math Reasoning
## 2B / 4B / 8B Native-Image vs Equal-Evidence Comparison

## 0. Objective

Test **why Thinking is useful even at small VLM scale** by measuring, across Qwen3-VL 2B / 4B / 8B, how much of the Thinking-vs-Instruct advantage remains after task-critical visual evidence is explicitly equalized.

Primary question:

\[
\boxed{
\textbf{How does the functional role of Thinking change with VLM scale?}
}
\]

For each scale \(s\),

\[
G_{\mathrm{img}}(s)
=
Acc(T_{\mathrm{img}},s)-Acc(I_{\mathrm{img}},s)
\]

and

\[
G_{E^*}(s)
=
Acc(T_{E^*},s)-Acc(I_{E^*},s).
\]

Interpretation:

- \(G_{\mathrm{img}}\): deployed Thinking advantage on the original multimodal task;
- \(G_{E^*}\): deployed Thinking advantage after the required visual evidence has already been supplied textually;
- their difference describes how the native-image advantage changes when evidence uncertainty is removed.

This is a **cross-scale VLM study**. It does not yet establish a matched text-only LLM/VLM contrast.

---

## 1. Why this is next

Stage 13A confirmed at 4B:

\[
\Delta_{E^*}=+11.11\text{ percentage points}
\]

with:

\[
95\%\ \mathrm{CI}=[+5.56,+17.06].
\]

The result also persisted among outputs reaching a scoreable result before 32k generated tokens:

\[
+11.38\text{ pp}.
\]

Thus:

\[
\boxed{
\textbf{Thinking's 4B advantage is not reducible to visual evidence recovery.}
}
\]

The next question is:

\[
\boxed{
\textbf{Does the same post-evidence advantage already exist in a small 2B VLM,
and how does it evolve by 8B?}
}
\]

---

## 2. Paper claim first

### Strong positive small-model claim

If 2B shows a robust equal-evidence Thinking advantage:

> **Even a 2B VLM benefits from Thinking after task-critical visual evidence has already been made explicit, showing that the small-model Thinking gain is not purely a visual-access effect.**

### Cross-scale persistence claim

If post-evidence Thinking gain remains positive across 2B/4B/8B:

> **Post-evidence Thinking benefits are present across VLM scale rather than emerging only at larger models.**

### Role-shift claim

If the image-vs-equal-evidence contrast changes systematically with scale:

> **The functional contribution of Thinking shifts with model scale: the relative importance of image-side versus post-evidence computation differs between small and larger VLMs.**

This claim requires the preregistered scale interaction.

---

## 3. What this stage can and cannot establish

### It can establish

- whether 2B has a post-evidence Thinking advantage;
- whether \(G_{E^*}(s)\) changes with scale;
- whether native-image and equal-evidence Thinking gaps differ within scale;
- whether that difference itself changes with scale.

### It cannot establish

- that classical text-only LLM Thinking behaves differently under a matched setup;
- a pure causal effect of "Thinking mode";
- a unique neural mechanism;
- direct visual access from image-gap attenuation alone.

A positive Stage 13B motivates a later **matched text-only scaling experiment** if the paper wants a strong LLM-vs-VLM contrast.

---

## 4. Model family

Study paired Instruct and Thinking variants at:

\[
\boxed{
s\in\{2B,4B,8B\}.
}
\]

Expected model family:

- Qwen3-VL-2B-Instruct
- Qwen3-VL-2B-Thinking
- Qwen3-VL-4B-Instruct
- Qwen3-VL-4B-Thinking
- Qwen3-VL-8B-Instruct
- Qwen3-VL-8B-Thinking

Do not assume repository names or revisions from memory.

Before science:

1. locate the exact local checkpoint for each required variant;
2. record model identifier;
3. record exact revision / immutable snapshot hash;
4. verify tokenizer/chat-template compatibility;
5. verify vision preprocessing configuration;
6. verify context/output limits.

If either 2B or 8B lacks a valid paired Instruct/Thinking checkpoint:

\[
\boxed{
\texttt{CROSS\_SCALE\_CHECKPOINT\_BLOCKED}
}
\]

and stop before scientific generation.

No download or substitution without explicit approval.

---

## 5. Scientific cohort

Reuse the Stage 12X/13A frozen 96-family source cohort, but prospectively define a **48-family cross-scale subset** to control compute.

Selection must be outcome-independent.

Even though prior 4B outcomes are known, the Stage 13B subset may use only:

- family ID;
- answer type;
- source difficulty metadata;
- broad source category;
- \(E^*\) atom count;
- source/input hashes.

Do not use:

- any Instruct/Thinking correctness;
- B1/B2/B3/B4 label;
- Stage 13A family effect;
- response length;
- transfer result;
- model pathology.

---

## 6. Frozen 48-family subset construction

Stratify using source-only fields:

1. answer type:
   - multiple-choice;
   - open-ended;
2. available MathVision difficulty stratum;
3. \(E^*\) atom-count bin:
   - 1 atom;
   - 2+ atoms.

Within strata order by:

`SHA256(stage13b-v1|family_id)`.

Select proportionally until exactly:

\[
\boxed{
48\text{ families}
}
\]

are frozen.

If a stratum cannot satisfy its target, fill using the next globally hashed family while preserving source-only selection.

Archive the selection code, ordering, and hash before any 2B/8B model call.

---

## 7. Technical validation set

Choose 4 additional families from the remaining 48 Stage 12X/13A cohort members using a separate source-only hash.

These 4 are technical only and never included in Stage 13B scientific inference.

Validate all six checkpoints on:

- native-image input;
- equal-evidence image-free input.

Check:

- prompt rendering;
- image tokenization;
- no image leakage in equal-evidence condition;
- scoreable output;
- expected control tokens;
- output cap behavior.

Do not use technical-set correctness for scientific selection.

---

## 8. Core conditions

For each scale \(s\in\{2B,4B,8B\}\) and each frozen family:

### Native image — Instruct

\[
\boxed{
I_{\mathrm{img}}(s)
}
\]

Input: original image + original question, no CoT suffix.

### Native image — Thinking

\[
\boxed{
T_{\mathrm{img}}(s)
}
\]

Input: exact same original image + question, no added reasoning instruction.

### Equal evidence — Instruct

\[
\boxed{
I_{E^*}(s)
}
\]

Input: no image; exact frozen Stage 12X/13A \(Q+E^*\).

### Equal evidence — Thinking

\[
\boxed{
T_{E^*}(s)
}
\]

Input: no image; exact same \(Q+E^*\).

---

## 9. Reuse of existing 4B data

For the frozen 48 families, reuse the three Stage 13A fresh replicates for:

\[
I_{E^*}(4B)
\]

and:

\[
T_{E^*}(4B).
\]

Do not regenerate them.

Generate new 3-replicate native-image conditions for:

\[
I_{\mathrm{img}}(4B),\quad T_{\mathrm{img}}(4B).
\]

---

## 10. Replicates and seeds

For all newly generated scientific cells use:

\[
\boxed{
3\text{ frozen replicates per family-condition}.
}
\]

For 2B and 8B:

`SHA256(stage13b-v1|scale|family_id|condition|replicate)`

For new 4B native-image cells use the same Stage 13B namespace.

Use the same replicate indices across Instruct/Thinking within scale/condition.

No best-of-three selection.

---

## 11. Generation recipes

Use the same mode-level recipes across scales unless a checkpoint is technically incompatible.

### Instruct

- temperature = 0.7
- top-p = 0.8
- top-k = 20
- repetition penalty = 1.0
- presence penalty = 1.5
- max new tokens = 32,768

### Thinking

- temperature = 1.0
- top-p = 0.95
- top-k = 20
- repetition penalty = 1.0
- presence penalty = 0
- max new tokens = 81,920

If one scale requires a recipe change for technical validity, stop and request amendment rather than silently changing the cross-scale protocol.

---

## 12. New scientific-call count

### 2B

\[
48\times4\times3=576
\]

### 8B

\[
48\times4\times3=576
\]

### 4B

Only native-image cells are new:

\[
48\times2\times3=288
\]

Total:

\[
\boxed{
1440\text{ new scientific calls}
}
\]

plus technical validation.

---

## 13. Technical validity

Use:

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
- a clear unretracted answer before cap is scoreable;
- pre-outcome truncation is technical missingness;
- normal-stop refusal/no answer is a scientific failure.

Do not count technical missingness as incorrect in primary accuracy estimates.

---

## 14. Scoring

Score each scale-condition arm separately before paired comparisons are opened.

Use the frozen MathVision equivalence policy.

Labels:

- `CORRECT`
- `INCORRECT`
- `UNSCOREABLE_TECHNICAL`

Run:

- all ambiguity-triggered second reviews;
- deterministic 20% random second-pass audit at each scale;
- exact extraction receipts.

Same-agent QC is not independent-rater reliability.

---

## 15. Family-level replicate score

For family \(i\), scale \(s\), model \(M\), condition \(c\in\{\mathrm{img},E^*\}\):

\[
\bar y_{i,s,M,c}
=
\frac{\#\text{ correct resolved replicates}}
{\#\text{ resolved replicates}}.
\]

Primary paired inference at a scale-condition uses families where all 3 replicates for both Instruct and Thinking are resolved.

Also report conservative missingness bounds.

---

## 16. Scale-specific gaps

For each scale:

\[
\boxed{
G_{\mathrm{img}}(s)
=
\frac{1}{N_s}
\sum_i
\left(
\bar y_{i,s,T,\mathrm{img}}
-
\bar y_{i,s,I,\mathrm{img}}
\right)
}
\]

and:

\[
\boxed{
G_{E^*}(s)
=
\frac{1}{N_s}
\sum_i
\left(
\bar y_{i,s,T,E^*}
-
\bar y_{i,s,I,E^*}
\right).
}
\]

Use the maximum common complete-family set for within-scale image-vs-evidence contrasts when possible.

Report percentage points.

---

## 17. Primary endpoint — 2B post-evidence gain

The most important endpoint is:

\[
\boxed{
G_{E^*}(2B).
}
\]

Declare:

\[
\boxed{
\texttt{SMALL\_VLM\_POST\_EVIDENCE\_GAIN}
}
\]

iff:

1. at least 40/48 families are complete paired cases at 2B equal evidence;
2. point estimate:
   \[
   G_{E^*}(2B)\ge+5\text{ pp};
   \]
3. 95% paired family-bootstrap lower bound \(>0\).

Interpretation:

> Thinking already provides a robust post-evidence reasoning benefit at 2B scale.

This is the critical result for the small-VLM story.

---

## 18. Evidence-equalization contrast

Define:

\[
\boxed{
A(s)
=
G_{\mathrm{img}}(s)
-
G_{E^*}(s).
}
\]

Interpret only descriptively.

### \(A(s)>0\)

Thinking advantage is larger on native-image input than after evidence equalization.

Compatible with an additional image-side contribution.

Do not call it formal mediation or direct visual-access proof.

### \(A(s)\approx0\)

Thinking gain is similar before and after evidence equalization.

### \(A(s)<0\)

Thinking advantage is larger after visual evidence is already explicit.

This argues against a purely visual-access account.

---

## 19. Cross-scale role-shift endpoint

Define:

\[
\boxed{
R_{\mathrm{shift}}
=
A(2B)-A(8B).
}
\]

Use the same-family paired bootstrap.

Declare:

\[
\boxed{
\texttt{SCALE\_ROLE\_SHIFT}
}
\]

iff:

1. at least 36 families are complete across all 2B/8B image/equal-evidence cells;
2. \(|R_{\mathrm{shift}}|\ge5\) pp;
3. 95% family-bootstrap interval excludes 0.

Interpretation:

> the relative image-side versus post-evidence contribution of Thinking changes with VLM scale.

---

## 20. Cross-scale post-evidence persistence

Report:

\[
G_{E^*}(2B),\quad
G_{E^*}(4B),\quad
G_{E^*}(8B).
\]

Declare:

\[
\boxed{
\texttt{POST\_EVIDENCE\_GAIN\_ACROSS\_SCALES}
}
\]

iff:

- all three point estimates are positive;
- at least two scales have bootstrap lower bound \(>0\);
- one confirmed scale is 2B.

Allowed interpretation:

> post-evidence Thinking benefit is not restricted to the larger VLMs tested.

---

## 21. Optional scale-trend summary

Fit a descriptive family-clustered or bootstrap regression:

\[
G_{E^*}(s)
=
\alpha+\beta\log_2(\text{parameter scale})
\]

and similarly for \(A(s)\).

Treat slopes as descriptive because only three scales are observed.

Do not use regression as the primary decision rule.

---

## 22. Majority-transition analysis

At each scale-condition define family majority correctness as at least 2/3 resolved replicates correct.

Report:

- both correct;
- Thinking-only;
- Instruct-only;
- both wrong;
- unresolved.

For equal evidence especially report:

\[
N_{\mathrm{T-only}}(s)
\quad\text{vs}\quad
N_{\mathrm{I-only}}(s).
\]

Secondary only.

---

## 23. 32k outcome sensitivity

Because Thinking has a larger output budget, compute a no-new-call sensitivity at each scale.

Define the subset where all relevant Thinking outputs produce a scoreable answer before 32,768 generated tokens.

Recompute:

\[
G_{E^*}^{32k}(s)
\]

and:

\[
G_{\mathrm{img}}^{32k}(s).
\]

If the 2B post-evidence gain remains positive in the 32k-comparable subset, this weakens the explanation that the small-model gain is solely due to a larger token budget.

Do not call this fully decoding-matched.

---

## 24. Ceiling/floor reporting

For each scale-condition report absolute accuracies for Instruct and Thinking.

Also report fraction of families:

- both near floor;
- both near ceiling;
- discordant.

Do not exclude floor/ceiling families post hoc.

---

## 25. Interpretation matrix

### Pattern A — 2B post-evidence gain is strong

\[
G_{E^*}(2B)>0
\]

with the primary gate passed.

Interpretation:

\[
\boxed{
\textbf{small VLM Thinking benefit survives after evidence is already available.}
}
\]

### Pattern B — 2B native-image gain is much larger than equal-evidence gain

\[
A(2B)\gg0.
\]

Interpretation:

> small-scale Thinking has an additional image-side contribution.

### Pattern C — 2B equal-evidence gain is comparable to or larger than image gain

\[
A(2B)\le0.
\]

Interpretation:

> the small-model Thinking advantage is primarily compatible with post-evidence computation rather than a purely perceptual account.

### Pattern D — post-evidence gain appears only at larger scale

For example:

\[
G_{E^*}(2B)\approx0,
\quad
G_{E^*}(4B),G_{E^*}(8B)>0.
\]

Interpretation:

> post-evidence Thinking benefit itself shows a scale threshold.

---

## 26. Main decision states

### `SMALL_VLM_POST_EVIDENCE_GAIN`

Defined in Section 17.

### `POST_EVIDENCE_GAIN_ACROSS_SCALES`

Defined in Section 20.

### `SCALE_ROLE_SHIFT`

Defined in Section 19.

May coexist with either positive state above.

### `IMAGE_SIDE_SMALL_SCALE_SIGNAL`

Declare if:

1. \(G_{\mathrm{img}}(2B)>0\);
2. \(A(2B)\ge+5\) pp;
3. bootstrap interval for \(A(2B)\) excludes 0.

Interpretation:

> the 2B Thinking advantage has a substantial additional component present on native-image input but attenuated after evidence equalization.

Do not label this direct visual access without an evidence-probe experiment.

### `CROSS_SCALE_ROLE_UNRESOLVED`

Declare if:

- 2B equal-evidence result is inconclusive;
- and no scale-role interaction meets its gate.

Preserve Stage 13A's confirmed 4B result.

---

## 27. Relation to the motivating LLM-vs-VLM question

A positive 2B result establishes:

\[
\boxed{
\textbf{post-evidence Thinking gains already occur at small VLM scale.}
}
\]

It does **not** establish:

> small VLMs differ from small text-only LLMs.

That broader statement requires a later matched text-only experiment with:

- comparable model family;
- matched problem structure;
- all required facts supplied textually;
- Instruct vs Thinking across scale.

Stage 13B should motivate, not substitute for, that comparison.

---

## 28. Paper-level claim if 2B is positive

Allowed:

> **Thinking's benefit is not confined to large VLMs or to visual-evidence recovery: even at 2B scale, the Thinking variant can retain an advantage after the task-critical evidence is explicitly supplied.**

If the gain persists across scales:

> **Post-evidence Thinking benefits are present across the tested VLM scales.**

If role shift is also identified:

> **The balance between image-side and post-evidence contributions changes with model scale.**

---

## 29. Null discipline

If 2B is null, do not conclude small VLM Thinking is useless.

Alternatives include:

- benefit primarily on image-side computation;
- subset-specific benefit;
- floor effects;
- limited power.

If 8B is null but 4B is positive, do not assume monotonic scaling; inspect ceiling and missingness.

If \(A(s)\) is null, do not conclude visual processing is irrelevant.

---

## 30. Execution phases

### Phase 0 — Seal and technical validation

- freeze 48-family subset;
- freeze 4-family technical set;
- pin all six checkpoints/revisions;
- validate templates and inputs;
- freeze seeds.

### Phase 1 — Equal-evidence cross-scale

Run new 2B and 8B:

\[
I_{E^*},\quad T_{E^*}.
\]

Reuse 4B Stage 13A equal-evidence data.

This is the highest-priority phase.

### Phase 2 — Native-image cross-scale

Run new 2B/4B/8B:

\[
I_{\mathrm{img}},\quad T_{\mathrm{img}}.
\]

### Phase 3 — Scoring and paired inference

No outcome-adaptive model calls.

### Phase 4 — 32k-comparable sensitivity

No new calls.

---

## 31. Technical stop gates

Stop before continuing if:

- a required paired checkpoint is unavailable;
- a checkpoint cannot accept the frozen input format;
- equal-evidence rendering differs semantically across scales;
- image preprocessing fails systematic validation;
- >20% technical missingness appears in any scale-mode arm during an initial frozen 8-family tranche.

If the tranche hits the missingness gate, stop and report technical failure rather than modifying caps or prompts.

---

## 32. Compute budget

Expected new scientific calls:

\[
\boxed{
1440
}
\]

plus technical validation.

Target:

\[
\boxed{
<24\text{ GPU-hours}
}
\]

Hard stop:

\[
\boxed{
32\text{ GPU-hours}
}
\]

unless separately approved.

If projected use exceeds the hard stop before Phase 2:

- finish already-submitted calls;
- stop;
- report Phase 1 equal-evidence results only;
- do not silently reduce replicates or cohort size.

---

## 33. Required figures

### Figure 13B-1 — Thinking gain vs scale

For each scale:

\[
G_{\mathrm{img}}(s)
\]

and:

\[
G_{E^*}(s)
\]

with paired family-bootstrap intervals.

### Figure 13B-2 — Equal-evidence accuracy by scale

Show absolute:

\[
Acc(I_{E^*},s)
\]

and:

\[
Acc(T_{E^*},s).
\]

### Figure 13B-3 — Evidence-equalization contrast

Show:

\[
A(s)=G_{\mathrm{img}}(s)-G_{E^*}(s).
\]

### Figure 13B-4 — Majority transitions

Per scale, equal evidence:

- both correct;
- Thinking-only;
- Instruct-only;
- both wrong;
- unresolved.

### Figure 13B-5 — 32k-comparable sensitivity

Show:

\[
G_{E^*}(s)
\]

vs:

\[
G_{E^*}^{32k}(s).
\]

---

## 34. Required artifacts

Produce:

1. `stage13b_cross_scale_role_spec.md`
2. `stage13b_frozen48_manifest.json`
3. `stage13b_technical4_manifest.json`
4. `stage13b_checkpoint_manifest.json`
5. `stage13b_input_hashes.json`
6. `stage13b_seed_manifest.json`
7. `stage13b_2b_image_results.parquet`
8. `stage13b_2b_equal_evidence_results.parquet`
9. `stage13b_4b_image_results.parquet`
10. `stage13b_4b_equal_evidence_reuse.json`
11. `stage13b_8b_image_results.parquet`
12. `stage13b_8b_equal_evidence_results.parquet`
13. `stage13b_scoring_audit.json`
14. `stage13b_family_level_results.parquet`
15. `stage13b_scale_effects.json`
16. `stage13b_missingness_bounds.json`
17. `stage13b_32k_sensitivity.json`
18. `stage13b_primary_inference.json`
19. `stage13b_decision.json`
20. `stage13b_resource_accounting.json`
21. `stage13b_summary.md`

Preserve all Stage 12 and Stage 13A artifacts unchanged.

---

## 35. Exactly one recommendation at completion

### If `SMALL_VLM_POST_EVIDENCE_GAIN`

Recommend:

> Run a matched text-only cross-scale control to test whether the small-model post-evidence Thinking gain is specifically stronger in VLMs than in text-only reasoning.

### If `IMAGE_SIDE_SMALL_SCALE_SIGNAL` without 2B post-evidence gain

Recommend:

> Run a cross-scale direct visual-evidence probe to test whether small-VLM Thinking primarily improves demonstrated evidence recovery.

### If post-evidence gain emerges only at 4B/8B

Recommend:

> Compare the observed VLM scale threshold against a matched text-only reasoning family before claiming a modality-specific difference.

### If `CROSS_SCALE_ROLE_UNRESOLVED`

Recommend:

> Retain the confirmed 4B post-evidence result as the strongest claim and stop scaling-based role interpretation.

Do not launch automatically.

---

## 36. Final decision target

Stage 13B exists to answer:

\[
\boxed{
\textbf{Why can Thinking help even small VLMs?}
}
\]

The most important test is whether:

\[
\boxed{
G_{E^*}(2B)>0
}
\]

under identical task-critical evidence.

If yes, then the small-VLM Thinking benefit cannot be explained only as better inspection of the image.

The cross-scale comparison then asks whether:

\[
\boxed{
G_{\mathrm{img}}(s)
\quad\text{and}\quad
G_{E^*}(s)
}
\]

change differently with scale.

The strongest positive interpretation is:

> **Even small VLMs retain a Thinking advantage after the necessary visual evidence is already available, suggesting that Thinking supports post-evidence sequential computation/state construction rather than serving only as a perceptual-access mechanism.**

A later matched text-only study would be required to establish the stronger LLM-vs-VLM contrast.
