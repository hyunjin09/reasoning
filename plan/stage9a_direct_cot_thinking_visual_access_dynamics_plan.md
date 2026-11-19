# Stage 9A — Direct vs CoT vs Thinking: Direct Visual-Access Dynamics

## 0. One-line objective

Use a VAB-style direct image-token masking intervention to determine whether **Qwen3-VL-2B Instruct-Direct, Instruct-CoT, and Native Thinking differ in when direct visual access is functionally necessary during reasoning**.

Primary question:

\[
\boxed{
\textbf{Do Direct, prompted CoT, and native Thinking exhibit different temporal profiles
of direct image-token necessity during reasoning?}
}
\]

This plan uses the **VAB intervention as a measurement tool**, but does **not** aim to reproduce VAB as the scientific objective.

The scientific object of interest is the **reasoning-step-wise direct visual-access necessity profile**.

---

# 1. Why this experiment is necessary

The completed Stage 9A native-use characterization showed that Thinking does **not** simply exhibit more retrieval-like episodes than CoT.

That result does not answer the more important causal question:

\[
\boxed{
\textbf{When is direct image-token access actually necessary for the reasoning trajectory?}
}
\]

Native visual-use activity and direct-access necessity can dissociate.

A model may:

- locally use image tokens,
- show source-sensitive causal effects,

yet still tolerate direct visual-access removal because image-derived information has already propagated into internal reasoning state.

Therefore:

\[
\boxed{
\text{visual usage}
\neq
\text{visual necessity}
}
\]

Stage 9A proper tests **necessity dynamics over reasoning time**.

---

# 2. Paper-facing scientific hypothesis

The high-value hypothesis is not:

> Thinking looks at the image more often.

It is:

\[
\boxed{
\textbf{Thinking may depend on direct visual access at different reasoning times than prompted CoT.}
}
\]

Possible strong pattern:

### Instruct-CoT

\[
\text{early visual dependence}
\rightarrow
\text{mostly language-side continuation}
\]

### Native Thinking

\[
\text{visual dependence}
\rightarrow
\text{reasoning}
\rightarrow
\text{late visual dependence reappears}
\]

If supported, this would motivate the concept of a **Visual Access Schedule**:

\[
\boxed{
\textbf{a temporally structured pattern of direct visual necessity tied to evolving reasoning demand}
}
\]

rather than only a single monotonic access boundary.

---

# 3. Relation to VAB

We borrow the VAB intervention:

> block direct self-attention from generated-token queries to image-token keys.

But the scientific goal is different.

## VAB asks

\[
\boxed{
\text{How long must direct visual access remain available?}
}
\]

## Stage 9A asks

\[
\boxed{
\text{How does direct visual-access necessity evolve over reasoning time,
and how does that profile differ across Direct, CoT, and Thinking?}
}
\]

Therefore Stage 9A uses VAB-style masking in three complementary ways:

1. **cumulative cutoff**
2. **local-window knockout**
3. **demand-aligned knockout**

The second and third are the core additions for our question.

---

# 4. Models and arms

Use the same model scale.

## A1 — Instruct Direct

**Qwen3-VL-2B-Instruct**

No additional CoT prompt.

## A2 — Instruct CoT

**Qwen3-VL-2B-Instruct**

Use one frozen CoT prompt.

Recommended:

> Think step by step before answering.

No prompt sweep after scientific outcomes are opened.

## A3 — Native Thinking

**Qwen3-VL-2B-Thinking**

Use the native Thinking template / generation path.

Do not add an additional CoT instruction.

---

# 5. Dataset

## Primary dataset

Use the **same 128-family MathVision cohort already used in the Stage 9A native-use characterization**.

Reasons:

- identical Direct / CoT / Thinking item support;
- existing reviewed trajectories;
- existing semantic demand annotations;
- existing answer extraction/scoring;
- natural long-form multimodal reasoning;
- direct connection to the paper's actual target setting.

Do **not** replace the main experiment with synthetic counting.

---

# 6. Why MathVision is primary

The scientific hypothesis concerns:

\[
\boxed{
\text{long-form reasoning with evolving visual information demand}
}
\]

Synthetic counting is useful for implementation sanity, but it has:

- weak subgoal evolution;
- little delayed reuse;
- little source switching;
- limited A→B→A structure.

Therefore controlled VAB-style counting may be used only as a **technical sanity check / external comparability assay**, not as the main scientific endpoint.

---

# 7. Existing Stage 9A data to reuse

Reuse frozen artifacts where possible:

- 128 MathVision items / families
- Direct trajectories
- CoT trajectories
- Thinking trajectories
- semantic visual-demand annotations
- answer extraction review
- source/readout annotations
- native retrieval features
- causal validation event inventory

Do not regenerate native trajectories unless necessary for the masking execution path.

If masked inference requires a different backend, establish a new full-access baseline on that same backend.

---

# 8. Direct visual-access intervention

Let:

- \(V\) = image-token key positions
- \(G_t\) = generated-token query at reasoning step \(t\)

For selected layers, modify attention logits:

\[
M_{G_t,j}=-\infty
\qquad
\forall j\in V
\]

during the specified masking interval.

Important:

- image K/V remain in cache;
- prompt/text K/V remain unchanged;
- prior image-derived residual/text state remains intact;
- only **direct generated-query → image-key access** is removed.

This is a VAB-style necessity intervention.

---

# 9. Primary execution path

For the main temporal dynamics experiment, block image access in the previously established visual-retrieval-relevant late layer window:

\[
\boxed{
\ell \in 19\text{--}22
}
\]

This keeps the intervention aligned with prior Qwen3-VL-2B causal retrieval findings.

Do **not** start with a full layer × time 2D sweep.

The primary scientific question is **WHEN**, not layer localization.

Layer localization comes only after a temporal difference is established.

---

# 10. Assay A — Cumulative access cutoff

This is the direct VAB-inspired assay.

For cutoff \(t_c\):

\[
\text{visual access ON for }t\le t_c
\]

\[
\text{visual access OFF for }t>t_c
\]

Run cutoffs:

\[
\boxed{
t_c \in
\{0,16,32,64,128,256,512,1024,2048,4096,\text{FULL}\}
}
\]

If native trajectories are shorter, later cutoffs collapse to effective full access.

For each arm estimate:

\[
A_p(t_c)
\]

where \(p\in\{D,C,T\}\).

Define damage:

\[
\Delta_p(t_c)
=
A_p(\text{FULL})-A_p(t_c)
\]

This asks:

> When can direct image access be permanently removed without substantial performance loss?

---

# 11. Assay B — Local-window visual knockout

This is the main temporal-dynamics assay.

Instead of removing vision permanently after a cutoff, remove direct image access only within a local reasoning window.

Use normalized trajectory position.

Primary windows:

\[
[0,.1], [.1,.2], \ldots, [.9,1.0]
\]

of generated reasoning.

For arm \(p\) and window \(w\):

\[
N_p(w)
=
A_p(\text{FULL})
-
A_p(\text{mask only in }w)
\]

This gives a **temporal necessity profile**:

\[
\boxed{
N_D(w),\quad N_C(w),\quad N_T(w)
}
\]

The central scientific object of Stage 9A is this profile.

---

# 12. Why local-window knockout is essential

A cumulative cutoff can only reveal a monotonic boundary.

But a Thinking trajectory may instead require direct visual access at sparse later events:

\[
\text{need A}
\rightarrow
\text{gap}
\rightarrow
\text{need B}
\rightarrow
\text{gap}
\rightarrow
\text{need A again}
\]

A local-window knockout can reveal:

\[
\boxed{
\text{early necessity}
\rightarrow
\text{late re-emergent necessity}
}
\]

which a single cutoff cannot distinguish cleanly.

This is the core test of whether Thinking is better described by a **Visual Access Schedule** than by one access boundary.

---

# 13. Assay C — Demand-aligned local knockout

Use the existing masked semantic visual-demand annotations from Stage 9A.

For each accepted demand event centered at \(d\), block direct image access only in:

\[
\boxed{
[d-16,d+16]
}
\]

generated-token positions.

Secondary robustness:

\[
[d-32,d+32]
\]

Measure:

- final-answer degradation;
- local readout degradation where a local readout is defined;
- next-evidence token log-prob degradation;
- downstream trajectory change if deterministic replay allows it.

Compare:

\[
\boxed{
\text{demand-aligned knockout}
}
\]

against:

\[
\boxed{
\text{matched non-demand / shifted-time knockout}
}
\]

within each arm.

Primary question:

\[
\boxed{
\textbf{Does explicit visual demand coincide with direct visual-access necessity?}
}
\]

Secondary question:

\[
\boxed{
\textbf{Is that coupling stronger or temporally different in Thinking than CoT?}
}
\]

---

# 14. Primary endpoints

Freeze these before scientific execution.

## P1 — Cumulative access damage curve

For each arm:

\[
\Delta_p(t_c)
\]

Primary comparison:

\[
\Delta_T(t_c)
\quad\text{vs}\quad
\Delta_C(t_c)
\]

at late cutoffs.

---

## P2 — Local-window necessity profile

For each normalized window \(w\):

\[
N_D(w), N_C(w), N_T(w)
\]

Primary contrast:

\[
\boxed{
N_T(w)-N_C(w)
}
\]

especially for late reasoning windows.

---

## P3 — Late necessity mass

Define:

\[
\boxed{
L_p
=
\frac{1}{5}
\sum_{w\in[0.5,1.0]}
N_p(w)
}
\]

or equivalent predeclared late-half aggregate.

Primary hypothesis:

\[
\boxed{
L_T > L_C
}
\]

---

## P4 — Demand-aligned necessity

For each arm:

\[
D_p
=
\text{damage}_{\text{demand-window}}
-
\text{damage}_{\text{matched control-window}}
\]

Primary hypothesis:

\[
\boxed{
D_T > D_C
}
\]

or at minimum:

\[
D_T>0
\]

with clear late-event support.

---

# 15. Secondary endpoints

- local evidence log-prob damage
- local claim correctness change
- answer correctness change
- completion/cap rate
- reasoning length change
- first divergence token
- source-specific effects on annotated target regions
- attention redistribution
- post-mask recovery behavior

These are interpretive, not primary.

---

# 16. Direct arm role

Direct is retained for two reasons.

## 16.1 Baseline access profile

It shows the visual-access dynamics of the non-explicit-reasoning regime.

## 16.2 Scientific ordering

The most informative possible pattern is:

\[
\boxed{
\text{Direct: early/front-loaded}
}
\]

\[
\boxed{
\text{CoT: early/front-loaded or weakly extended}
}
\]

\[
\boxed{
\text{Thinking: late/recurrent necessity}
}
\]

Do not assume this ordering before results.

---

# 17. CoT elicitation validity

The previously frozen CoT prompt did not reliably produce longer traces than Direct in the earlier cohort.

For Stage 9A necessity dynamics, **do not tune CoT prompts after outcomes**.

Use one frozen CoT condition.

Interpretation must remain specific:

> Qwen3-VL-2B-Instruct under this frozen CoT elicitation.

Do not generalize to all possible CoT prompting strategies.

---

# 18. Length handling

Because Direct / CoT / Thinking trajectories differ in length:

## For cumulative cutoff
Use absolute token cutoffs.

## For local-window knockout
Use normalized trajectory position.

Report both.

Do not define a Thinking-specific effect solely from longer trajectories.

For local windows, each trajectory contributes equal reasoning-phase coverage independent of total length.

---

# 19. Full-access baseline on masked backend

Before any scientific analysis, establish:

\[
\boxed{
\text{FULL-access masked-capable path}
}
\]

for D/C/T.

Require:

- same generated outputs under greedy decoding where deterministic;
- or same logits within the frozen tolerance;
- same answer extraction.

If the backend change itself alters outputs materially, the masked-backend full-access trajectory becomes the canonical baseline for all Stage 9A contrasts.

Do not compare masked-path interventions to a different native attention backend.

---

# 20. Technical validation

Run 8–16 bounded examples before main execution.

Require:

## V1 — Full-access no-op
Mask-capable full access reproduces baseline.

## V2 — Exact image-key blocking
Masked generated-query → image-key probabilities are zero.

## V3 — Local-window boundaries
Mask begins and ends at the intended reasoning positions.

## V4 — Cumulative cutoff semantics
After \(t_c\), all relevant image-key access remains blocked.

## V5 — Prefill unchanged
Image/question prefill is unaffected.

## V6 — Cache validity
Autoregressive continuation remains valid across mask transitions.

Technical failures are implementation failures, not scientific nulls.

---

# 21. Attention-redistribution control

Because \(-\infty\) masking redistributes softmax mass, run a bounded null-sink or equivalent redistribution control on representative conditions.

Minimum conditions:

- one early local window
- one late local window
- one demand-aligned window
- one cumulative cutoff

The qualitative necessity profile must not be an artifact of attention redistribution.

If exact null-sink implementation is infeasible, report this limitation.

---

# 22. Optional query-text bypass control

If a positive Thinking-specific late-necessity effect appears, test whether prompt/query-text states provide an indirect bypass.

At frozen positive windows:

- keep the generated-query → image-key block;
- additionally block relevant query-text → image-key access in the same late layers.

This is a secondary artifact control.

Do not run a full grid unless the primary effect is positive.

---

# 23. Statistical unit

Primary independent unit:

\[
\boxed{
\text{MathVision item / conservative visual family}
}
\]

Use:

- paired comparisons across arms on the same item;
- family-clustered bootstrap;
- 4000 bootstrap draws;
- family-equal weighting.

Do not treat tokens, windows, or demand events as independent task-level samples.

For demand-event analyses, cluster all events from one family together.

---

# 24. Primary statistical comparisons

## C1 — Late cumulative damage

At each predeclared late cutoff:

\[
\Delta_T(t_c)-\Delta_C(t_c)
\]

## C2 — Late-window necessity

For windows after normalized position 0.5:

\[
N_T(w)-N_C(w)
\]

## C3 — Aggregate late-half necessity

\[
L_T-L_C
\]

## C4 — Demand-aligned necessity difference

\[
D_T-D_C
\]

Use multiplicity control across the predeclared primary family.

---

# 25. Strongest positive outcome

The strongest scientifically valuable pattern is:

### Direct / CoT

\[
\text{necessity concentrated early}
\]

with little damage from late local visual knockout.

### Thinking

\[
\text{late local visual knockout causes reproducible performance/readout damage}
\]

especially near semantic visual-demand events.

This would support:

\[
\boxed{
\textbf{Thinking exhibits recurrent direct visual-access necessity during reasoning.}
}
\]

and motivate:

\[
\boxed{
\textbf{Visual Access Schedule}
}
\]

as a follow-up mechanistic concept.

---

# 26. Outcome matrix

## Outcome A — Thinking shows late/recurrent necessity; CoT does not

Supported:

> **Native Thinking and prompted CoT differ in direct visual-access dynamics: Thinking remains functionally dependent on image tokens at later reasoning stages.**

Proceed to Stage 9B.

Stage 9B question:

\[
\boxed{
\textbf{What creates the late necessity, and is it tied to controlled A→B→A demand retargeting?}
}
\]

---

## Outcome B — Both CoT and Thinking show similar late necessity

Supported:

> Recurrent direct visual-access necessity is not Thinking-specific.

This would still be scientifically important and would connect our dynamic-retrieval story to CoT more broadly.

Do not pursue a Thinking-specific retrieval mechanism.

---

## Outcome C — Both are mostly early-only

Supported:

> Native late visual-use signals are often redundant; long reasoning can proceed mainly over already integrated visual state.

This would strongly reconcile our local causal-use findings with VAB-style necessity.

Stop the Thinking-specific prolonged-access branch.

---

## Outcome D — Thinking is less dependent on late access than CoT

Potential interpretation:

> Thinking may integrate visual information more efficiently or earlier.

Do not reinterpret as evidence for recurrent access.

This would motivate a different hypothesis only under a new plan.

---

# 27. What a null does NOT rule out

A null late-necessity difference does not imply:

- Thinking and CoT are computationally identical;
- visual retrieval is absent;
- source-specific retargeting is false;
- visual information is not used late;
- persistent representations fully explain all behavior.

It only rejects the specific claim that **Thinking has a distinct late direct-access necessity profile**.

---

# 28. Relation to the completed Stage 9A native-use characterization

The completed first assay established:

\[
\boxed{
\text{Thinking does not simply show more retrieval-like events than CoT}
}
\]

This new Stage 9A causal assay asks:

\[
\boxed{
\text{Does Thinking depend on those visual accesses differently over reasoning time?}
}
\]

Together:

### Usage characterization
How often does retrieval-like activity occur?

### Necessity characterization
When does removing direct image access hurt?

Stage 9A is complete only after both are interpreted jointly.

---

# 29. Optional VAB-style synthetic sanity assay

A small controlled counting task may be used only to verify that the implementation can recover a VAB-like early-access phenomenon.

Recommended bounded size:

\[
\boxed{
32\text{–}64 \text{ synthetic images}
}
\]

This assay is:

- technical / external-comparability support;
- not the primary scientific dataset;
- not a prerequisite for MathVision unless the masking implementation is otherwise uncertain.

Do not spend the main compute budget reproducing the full VAB paper.

---

# 30. Why this design is better aligned with our paper

The main paper studies:

\[
\boxed{
\text{how visual evidence enters long-form reasoning over time}
}
\]

Therefore the relevant object is not just a single VAB cutoff.

It is:

\[
\boxed{
\textbf{the temporal causal profile of direct visual access}
}
\]

This design tests whether Direct, CoT, and Thinking differ in:

- early dependence;
- late dependence;
- recurrence;
- demand-aligned necessity.

It uses VAB's intervention while preserving our own scientific question.

---

# 31. Stage 9 roadmap after this experiment

If Outcome A is positive:

## Stage 9B — Controlled recurrent-demand necessity
Test single / delayed / switch / A→B→A tasks and determine whether necessity follows reasoning demand.

## Stage 9C — Same-prefix model × trajectory decomposition
Ask whether the difference comes from reasoning-state content, checkpoint policy, or both.

## Stage 9D — Functional advantage
Ask when Thinking outperforms CoT as visual-demand recurrence increases.

## Stage 9E — Timed re-look bypass
Ask whether CoT fails to self-initiate visual access.

## Stage 9F — JIT vs upfront oracle
Test temporal evidence availability bottleneck.

## Stage 9G — Visual Access Schedule intervention
Test event-gated vs early-only vs random access.

## Stage 9H — Cross-family replication

Do not advance automatically.

---

# 32. Required artifacts

1. `stage9a_visual_access_dynamics_spec.md`
2. `stage9a_mask_backend_validation.json`
3. `stage9a_full_access_baselines.json`
4. `stage9a_cumulative_cutoff_results.parquet`
5. `stage9a_local_window_results.parquet`
6. `stage9a_demand_aligned_knockout.parquet`
7. `stage9a_temporal_necessity_profiles.json`
8. `stage9a_late_half_effects.json`
9. `stage9a_demand_vs_control_effects.json`
10. `stage9a_attention_redistribution_control.json`
11. `stage9a_primary_inference.json`
12. `stage9a_summary.md`

Optional:
13. `stage9a_query_text_bypass_control.json`
14. `stage9a_vab_synthetic_sanity.json`

---

# 33. Key figures

## Figure 1 — Intervention schematic

Generated reasoning over time with direct image-key access selectively removed.

Show both:

- cumulative cutoff;
- local-window knockout.

---

## Figure 2 — Cumulative necessity curves

Plot:

\[
\Delta_D(t_c),\quad
\Delta_C(t_c),\quad
\Delta_T(t_c)
\]

against token cutoff.

---

## Figure 3 — Temporal necessity profiles

Plot normalized reasoning time:

\[
N_D(w),\quad
N_C(w),\quad
N_T(w)
\]

This is the central figure.

---

## Figure 4 — Demand-aligned necessity

For each arm compare:

- demand-window knockout
- shifted/non-demand control knockout

Show:

\[
D_D,\quad D_C,\quad D_T
\]

---

## Figure 5 — Native usage vs causal necessity

Combine the completed Stage 9A native-use result with the new necessity profile.

This figure explicitly tests whether:

\[
\boxed{
\text{usage frequency}
\neq
\text{functional necessity}
}
\]

---

# 34. Go / no-go criterion

Advance to Stage 9B only if:

1. Thinking shows a reproducible late direct-access necessity effect;
2. the effect is larger or temporally more recurrent than CoT;
3. it survives family-clustered inference;
4. demand-aligned knockout supports semantic relevance rather than generic masking sensitivity;
5. the effect survives the attention-redistribution control;
6. it is not driven entirely by one subject/category.

If these criteria are not met, close the Thinking-specific access-dynamics branch.

---

# 35. Final decision target

Stage 9A is designed to answer:

\[
\boxed{
\textbf{Do Direct, prompted CoT, and native Thinking differ in
when direct access to image tokens is functionally necessary during reasoning?}
}
\]

The VAB intervention is the causal instrument.

The scientific target is the **visual-access dynamics**, not VAB reproduction.
