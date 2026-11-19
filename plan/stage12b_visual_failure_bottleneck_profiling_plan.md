# Stage 12B — Visual Failure Bottleneck Profiling in a Modern VLM

## 0. One-line objective

Determine **where a modern VLM fails on multimodal reasoning** by separating native task errors into:

\[
\boxed{
\text{perceptual / evidence-availability}
\;\;vs\;\;
\text{task-context evidence access/use}
\;\;vs\;\;
\text{downstream reasoning}
}
\]

using a frozen task-critical visual evidence set \(E^*\) and a causal **Equal-Evidence Oracle**.

The primary question is:

\[
\boxed{
\textbf{Among native VLM failures, what fraction are explained by failure to recover
task-critical visual evidence, failure to use recoverable evidence in the task context,
or downstream reasoning failure after correct evidence is supplied?}
}
\]

This stage deliberately **drops the Answer-Only condition**.

Prompted CoT and native Thinking are not the primary intervention here. They become the next-stage **selective-rescue analysis** after the failure taxonomy is established.

---

# 1. Why this experiment is necessary for the paper

The paper is being reorganized around a top-level question:

\[
\boxed{
\textbf{Where and why do modern VLMs fail, and what does additional reasoning recover?}
}
\]

A final wrong answer alone does not identify the bottleneck.

A model can fail because:

1. it cannot reliably recover the required visual evidence from the image;
2. the evidence is recoverable under explicit demand, but native task solving fails to access/use it effectively;
3. correct visual evidence is available, but downstream reasoning still fails.

These are scientifically different failure modes.

The existing mechanistic results already explain **how reasoning can control visual retrieval** and **how retrieved evidence is carried forward**. What is missing is a clean behavioral decomposition showing **which bottleneck actually accounts for native errors**.

Stage 12B provides that behavioral front door.

---

# 2. Paper claim first

## Candidate Claim 1 — outcome-neutral form

> **Multimodal reasoning failures can be localized into visual-evidence availability, task-context evidence access/use, and downstream reasoning bottlenecks by combining direct evidence probes with an equal-evidence causal bypass.**

If one bottleneck clearly dominates, the final wording may become stronger.

Examples:

### Access/use-dominant outcome

> **Many VLM errors occur despite recoverable task-critical visual evidence and disappear when the same evidence is explicitly supplied, identifying task-context evidence access/use as a major bottleneck.**

### Perceptual-dominant outcome

> **A substantial share of VLM errors originate before reasoning, because the required task-critical visual evidence itself is not reliably recoverable from the image.**

### Downstream-dominant outcome

> **Many VLM errors persist even after correct task-critical visual evidence is supplied, showing that downstream reasoning rather than perception is the dominant bottleneck.**

Do not choose among these claims before observing the data.

---

# 3. Connection to the Empty-Shelves / Lost-Keys logic

The conceptual structure is:

## Parametric factuality

\[
\text{information available?}
\rightarrow
\text{directly accessible?}
\rightarrow
\text{recoverable with additional reasoning?}
\]

## Our multimodal setting

\[
\boxed{
\text{task-critical visual evidence recoverable?}
\rightarrow
\text{native task succeeds?}
\rightarrow
\text{does supplying correct evidence rescue the task?}
}
\]

The crucial multimodal extension is the Equal-Evidence Oracle:

\[
\boxed{
\text{question} + E^*_{\text{correct}}
}
\]

with the image removed.

This directly bypasses the visual evidence-acquisition stage and helps separate upstream visual bottlenecks from downstream reasoning bottlenecks.

Important terminology:

- use `recoverable` / `not recoverable`;
- do **not** use `encoded` / `not encoded`.

The image is external input, and direct probing changes task demand.

---

# 4. Model

Use:

\[
\boxed{
\textbf{Qwen3-VL-4B-Instruct}
}
\]

as the primary behavioral model.

Rationale:

- the goal is failure localization, not decoding-pathology analysis;
- prior 2B work repeatedly encountered prompt/completion instability;
- the 4B regime has been substantially more usable for long-form reasoning experiments in this project.

Pin:

- exact model revision;
- processor/tokenizer revision;
- runtime backend;
- image preprocessing;
- generation recipe.

Do not substitute another checkpoint after seeing outcomes.

---

# 5. Dataset

Reuse the existing frozen Stage 11A / Stage 12A cohort:

\[
\boxed{
61 \text{ independent MathVision families}
}
\]

Composition:

- 24 multiple-choice;
- 37 open-ended.

All 61 already have:

- original image/question;
- source answer;
- frozen image hash;
- frozen \(E^*\);
- reviewed \(E^*\) sufficiency.

This avoids new annotation and makes Stage 12B a bounded first profiling study.

The 61-family cohort is a **developmental main analysis**, not yet a broad benchmark-prevalence claim across all modern VLMs.

If the taxonomy is informative, later confirmation should use a fresh held-out cohort and, ideally, another model scale/family.

---

# 6. Frozen task-critical visual evidence \(E^*\)

For each family:

\[
\boxed{
E^*=\{e_1,\dots,e_k\},
\quad 1\le k\le4
}
\]

where \(E^*\) is the minimal set of image-derived facts judged sufficient, together with the nonvisual question text, to solve the task.

Preserve all existing \(E^*\) facts exactly.

Do not:

- add facts after observing model failures;
- remove facts after observing oracle failures;
- rewrite facts to make the oracle easier;
- include the final answer itself as \(E^*\);
- leak downstream derivations that are not directly image-derived.

---

# 7. Three primary conditions

Each family receives exactly three conditions:

\[
\boxed{
E,\quad N,\quad O
}
\]

---

# 8. Condition E — Direct Evidence Probe

Purpose:

> test whether the frozen task-critical visual evidence is directly recoverable from the image when explicitly requested.

Input:

- original image;
- a short request for the frozen \(E^*\) facts only.

Do not ask the model to solve the original problem.

For one fact:

> Inspect the image and report only the requested visual fact.  
> Do not solve the original problem.  
> Requested fact: [frozen fact request]

For multiple facts, request them in a structured list.

Output should be short and structured.

Generation cap:

\[
\boxed{
256 \text{ tokens}
}
\]

to allow 1–4 facts without encouraging long reasoning.

---

# 9. Condition N — Native Instruct Task Solving

Purpose:

> measure the model's native task behavior without imposing Answer-Only or explicit CoT.

Use the exact original image and original MathVision question.

Do **not** append:

- “answer only”;
- “do not reason”;
- “think step by step.”

Use the benchmark-native Instruct generation protocol.

This condition may spontaneously reason.

That is intended.

Call it:

\[
\boxed{
\texttt{Native Instruct}
}
\]

not `Direct` and not `Answer-Only`.

---

# 10. Condition O — Equal-Evidence Oracle

Purpose:

> causally bypass image-based evidence acquisition by supplying the correct frozen \(E^*\) as text.

Input:

- **no image**;
- original nonvisual question text;
- exact correct \(E^*\) rendered as a compact factual block.

Template:

> Use the following facts from the image as given.  
> Do not question or reinterpret them.  
>  
> Visual facts:  
> - E1: [frozen correct fact]  
> - E2: [frozen correct fact]  
> ...  
>  
> Original question:  
> [exact original question]

Do not add:

- the final answer;
- hidden derivations;
- extra geometric/algebraic facts;
- explanatory hints.

The oracle may reason freely.

Use the same Instruct checkpoint and base generation recipe as N.

The only intended difference is:

\[
\boxed{
\text{image}
\rightarrow
\text{explicit correct }E^*
}
\]

---

# 11. Generation protocol

Use the Qwen benchmark-specific Instruct recipe as the default:

- temperature = 0.7
- top-p = 0.8
- top-k = 20
- repetition penalty = 1.0
- presence penalty = 1.5

Use:

\[
\boxed{
32768 \text{ output-token cap}
}
\]

for both N and O.

The purpose is to avoid reintroducing the 2B short-cap pathology.

A cap hit remains a real unresolved task outcome, but if cap/repetition is widespread the assay becomes technically compromised.

E uses the short evidence-probe cap defined above.

Freeze one seed policy prospectively and apply it consistently.

---

# 12. Minimal technical sanity check

Before opening scientific correctness, run:

\[
\boxed{
12 \text{ fixed technical families}
}
\]

selected deterministically from the 61.

This is not a prompt-search stage.

No alternative prompt wording may be selected based on correctness.

Check only:

## E

- request/input matches frozen family and fact;
- parseable evidence response in at least 10/12;
- no severe repetition in more than 1/12.

## N

- committed/extractable final answer in at least 10/12;
- cap hits \(\le1/12\);
- severe repetition \(\le1/12\).

## O

- committed/extractable final answer in at least 10/12;
- cap hits \(\le1/12\);
- severe repetition \(\le1/12\).

If N or O fails badly, STOP for technical diagnosis.

Do not perform iterative prompt search.

---

# 13. Scoring

## Evidence probe

Each frozen evidence atom \(e_i\) is scored:

- `CORRECT`
- `INCORRECT`
- `UNRESOLVED`

Define:

\[
E^+=1
\]

iff **all task-critical frozen evidence atoms are correct**.

Otherwise:

\[
E^-=1
\]

Retain partial atom-level correctness for secondary analysis.

---

## Native / Oracle task correctness

For multiple choice:

- score by the benchmark option answer.

For open-ended:

- use the existing frozen MathVision mathematical-equivalence scoring policy.

Preserve:

- correct;
- wrong;
- unresolved/no committed final;
- technical failure

as separate raw labels.

For primary behavioral analysis, unresolved native/oracle outputs count as task failure only if the technical sanity gate passed globally.

---

# 14. Primary failure taxonomy

Only classify items where:

\[
N^-=\text{Native Instruct task failure}.
\]

For each native failure, combine evidence recoverability and oracle outcome.

---

## B1 — Perceptual / evidence-availability bottleneck candidate

\[
\boxed{
E^- \land O^+
}
\]

Interpretation:

> the task fails natively, the required visual evidence is not fully recoverable under direct probing, but the task becomes solvable when correct \(E^*\) is supplied.

This is the strongest operational evidence for an upstream perceptual/evidence-availability bottleneck.

Do not claim hidden-state absence.

---

## B2 — Task-context evidence access/use bottleneck candidate

\[
\boxed{
E^+ \land O^+
}
\]

with \(N^-\).

Interpretation:

> the model can recover the required evidence under explicit demand and can solve the problem when that evidence is supplied, yet native task solving fails.

This is the multimodal `Lost Keys` analogue.

It indicates a failure of task-context evidence access/use, not a lack of raw visual recoverability.

Do not claim that the model had the correct evidence internally during the failed native trajectory.

---

## B3 — Downstream reasoning bottleneck candidate

\[
\boxed{
E^+ \land O^-
}
\]

with \(N^-\).

Interpretation:

> the required visual evidence is directly recoverable, but even explicitly supplying the correct evidence does not solve the task.

This localizes the failure downstream of basic visual evidence recovery.

Possible causes include:

- integration;
- transformation;
- algebra/geometry;
- multi-step inference;
- convergence;
- answer extraction.

---

## B4 — Mixed / unresolved bottleneck

\[
\boxed{
E^- \land O^-
}
\]

with \(N^-\).

Interpretation:

> both direct evidence recovery and downstream solution remain unsuccessful.

This does not identify a unique bottleneck.

Do not force these items into B1 or B3.

---

# 15. Primary endpoints

Freeze the following primary endpoints.

Let:

\[
\mathcal F=\{i:N_i^-=1\}
\]

be the native-failure set.

---

## P1 — Native failure prevalence

\[
\boxed{
P1=P(N^-)
}
\]

Descriptive only.

---

## P2 — Upstream-rescuable failure fraction

\[
\boxed{
P2=P(O^+\mid N^-)
}
\]

Question:

> among native failures, how many disappear when correct visual evidence is supplied?

This is the broadest upstream-vs-downstream localization endpoint.

---

## P3 — Perceptual bottleneck fraction

\[
\boxed{
P3=P(E^-,O^+\mid N^-)
}
\]

---

## P4 — Task-context evidence access/use bottleneck fraction

\[
\boxed{
P4=P(E^+,O^+\mid N^-)
}
\]

This is the most direct multimodal Lost-Keys quantity.

---

## P5 — Downstream bottleneck fraction

\[
\boxed{
P5=P(E^+,O^-\mid N^-)
}
\]

---

## P6 — Mixed/unresolved fraction

\[
\boxed{
P6=P(E^-,O^-\mid N^-)
}
\]

The four B1–B4 fractions must sum to 1 over native failures, modulo technical exclusions.

---

# 16. Secondary evidence-resolution analysis

For native failures, report:

\[
P(O^+\mid E^+,N^-)
\]

and

\[
P(O^+\mid E^-,N^-).
\]

This asks whether explicit correct evidence disproportionately rescues items where the model can already recover \(E^*\) under direct demand.

Do not overinterpret this as a causal effect of direct probing.

---

# 17. Competing mechanisms this stage distinguishes

## Mechanism A — Perception/evidence acquisition is the main bottleneck

Prediction:

- many native failures are \(E^-O^+\);
- supplying correct \(E^*\) sharply repairs them.

---

## Mechanism B — Task-conditioned access/use is the main bottleneck

Prediction:

- many native failures are \(E^+O^+\);
- the evidence is recoverable and sufficient, but native task solving fails to exploit it.

This is the strongest behavioral bridge to the existing reasoning-conditioned causal retrieval result.

---

## Mechanism C — Downstream reasoning is the main bottleneck

Prediction:

- many native failures are \(E^+O^-\);
- correcting/equalizing visual evidence does not repair the task.

This would shift the paper emphasis toward post-retrieval reasoning.

---

## Mechanism D — Failures are heterogeneous

Prediction:

- B1, B2, and B3 are all substantially populated.

This still supports the profiling claim, but the paper should emphasize a **multi-stage failure decomposition** rather than one dominant bottleneck.

---

# 18. Identifiability limits

The experiment is designed to localize bottlenecks, but each label is operational.

### \(E^-\) does not prove visual information is absent internally

The direct evidence probe changes retrieval demand.

### \(E^+\) does not prove native task solving actually retrieved the correct evidence

It only shows that the evidence is recoverable under explicit demand.

### \(O^+\) does not prove the exact native failure was caused solely by retrieval

Supplying \(E^*\) changes the input representation from image-derived to text-derived evidence.

### \(O^-\) does not prove perception was perfect

It shows that correct \(E^*\) alone is not sufficient for the model to solve the task under the oracle condition.

Use `bottleneck candidate` language in analysis until converging evidence from later stages supports a stronger causal interpretation.

---

# 19. Oracle validity checks

Because the oracle is the central causal bypass, validate it carefully.

For each family verify:

1. the image is absent;
2. only frozen \(E^*\) is supplied;
3. no final answer is leaked;
4. no nonvisual reasoning step is included;
5. units, symbols, and entity identities are preserved faithfully;
6. the original question is otherwise unchanged.

Randomly double-review at least:

\[
\boxed{
20\%
}
\]

of oracle prompts before generation.

Any oracle prompt with answer leakage is excluded and repaired before outcome scoring.

---

# 20. Statistical unit and intervals

Independent unit:

\[
\boxed{
\text{problem/image family}
}
\]

Report:

- exact counts;
- proportions;
- Wilson 95% intervals for P1–P6;
- bootstrap 95% intervals for selected contrasts.

Use:

\[
\boxed{
4000
}
\]

family-level bootstrap draws with a frozen seed.

Do not treat:

- evidence atoms;
- generated tokens;
- reasoning steps

as independent observations.

---

# 21. GO / NO-GO logic

This stage is exploratory localization, not a binary mechanism test.

Still define prospective decision states.

---

## PROFILE_INFORMATIVE

Declare if:

1. at least:
   \[
   \boxed{
   20
   }
   \]
   native failures are observed;

2. at least two bottleneck categories among B1–B3 contain:
   \[
   \boxed{
   \ge5
   }
   \]
   independent families, **or** one category alone contains:
   \[
   \boxed{
   \ge10
   }
   \]
   families;

3. technical sanity gates pass;

4. oracle prompts pass integrity review.

Interpretation:

> the failure decomposition has enough yield to support a selective CoT/Thinking rescue study.

---

## PROFILE_SPARSE

If fewer than 20 native failures occur, or the categories are too sparse for conditional rescue analysis:

> the 61-family cohort is insufficient for Claim 1 profiling.

Do not infer that the failure taxonomy is wrong.

The next step would be a harder/fresh cohort, not more analysis of the same sparse cells.

---

## TECHNICAL_STOP

If N/O completion pathologies or oracle-integrity failures make the assay unreliable:

> no scientific profiling conclusion.

---

# 22. What a successful Stage 12B may claim

Supported:

> **Native multimodal reasoning errors can be decomposed into failures of visual-evidence recovery, task-context evidence access/use, and downstream reasoning by combining direct evidence probes with an equal-evidence bypass.**

Potentially supported, depending on counts:

> **A substantial subset of failures occur despite directly recoverable and behaviorally sufficient visual evidence.**

Not yet supported:

> CoT fixes access failures.

Not yet supported:

> Thinking is better because it retrieves better.

Not yet supported:

> a particular attention/KV mechanism caused an individual behavioral failure.

Those belong to the next stages.

---

# 23. Next stage after PROFILE_INFORMATIVE

Freeze the Stage 12B taxonomy before adding new conditions.

Then run, on the **same frozen families**:

\[
\boxed{
C=\text{Qwen3-VL-4B-Instruct + prompted CoT}
}
\]

and

\[
\boxed{
T=\text{Qwen3-VL-4B-Thinking}
}
\]

Primary rescue questions:

\[
P(C^+\mid N^-,B_j)
\]

and:

\[
P(T^+\mid N^-,B_j)
\]

for each bottleneck class \(B_j\).

The central question becomes:

\[
\boxed{
\textbf{Which failure states are selectively reduced by prompted CoT and native Thinking?}
}
\]

Do not launch C/T automatically in Stage 12B.

---

# 24. Connection to Claims 2 and 3

If B2 (`task-context evidence access/use`) is substantially populated and selectively rescued later, then the existing mechanistic results become a natural explanation.

## Claim 2 — Reasoning controls visual retrieval

Existing causal result:

\[
\boxed{
\text{recent reasoning context}
\rightarrow
\text{target-specific causal visual retrieval}
}
\]

including A→B→A retargeting.

This can explain **how reasoning changes evidence access**.

## Claim 3 — Retrieved evidence becomes a reasoning state

Existing lifecycle:

\[
\text{Q/K routing}
\rightarrow
\text{Value-rich transfer}
\rightarrow
\text{local K/V + residual}
\rightarrow
\text{causal generated text}
\rightarrow
\text{text-sufficient reasoning}
\]

This can explain **how successfully retrieved evidence is carried into later computation**.

Thus the intended paper arc becomes:

\[
\boxed{
\textbf{Where does the VLM fail?}
}
\]

\[
\downarrow
\]

\[
\boxed{
\textbf{What does CoT / Thinking recover?}
}
\]

\[
\downarrow
\]

\[
\boxed{
\textbf{How does reasoning causally retrieve visual evidence?}
}
\]

\[
\downarrow
\]

\[
\boxed{
\textbf{How is retrieved evidence propagated into later reasoning?}
}
\]

---

# 25. Required figures

## Figure 1 — Failure-localization schematic

Show:

\[
\text{Image}
\rightarrow
E^*
\rightarrow
\text{task reasoning}
\rightarrow
\text{answer}
\]

with the E probe and O bypass.

---

## Figure 2 — Native failure composition

Among \(N^-\), stacked counts/proportions for:

- B1 perceptual/evidence-availability;
- B2 task-context evidence access/use;
- B3 downstream reasoning;
- B4 mixed/unresolved.

This is the main Stage 12B figure.

---

## Figure 3 — Oracle rescue by evidence recoverability

Compare:

\[
P(O^+\mid E^+,N^-)
\]

vs:

\[
P(O^+\mid E^-,N^-).
\]

---

## Figure 4 — Example trajectories

Show 1–2 representative examples of each populated bottleneck class:

- original question/image summary;
- frozen \(E^*\);
- evidence probe result;
- native outcome;
- oracle outcome.

Do not cherry-pick only unusually dramatic cases.

Use deterministic representative selection, e.g. smallest family ID within each class after freezing labels.

---

# 26. Required artifacts

Produce:

1. `stage12b_visual_failure_bottleneck_spec.md`
2. `stage12b_frozen_manifest.json`
3. `stage12b_evidence_probe_prompts.json`
4. `stage12b_native_prompts.json`
5. `stage12b_oracle_prompts.json`
6. `stage12b_oracle_integrity_review.json`
7. `stage12b_technical_sanity.json`
8. `stage12b_evidence_probe_results.parquet`
9. `stage12b_native_results.parquet`
10. `stage12b_oracle_results.parquet`
11. `stage12b_failure_profiles.parquet`
12. `stage12b_primary_inference.json`
13. `stage12b_profile_decision.json`
14. `stage12b_resource_accounting.json`
15. `stage12b_summary.md`

Preserve all Stage 12A / 12A-R artifacts separately.

---

# 27. Compute budget

Primary logical runs:

\[
61\times3=183
\]

consisting of:

- 61 E probes;
- 61 Native Instruct;
- 61 Equal-Evidence Oracle.

E probes are short.

N and O may be long.

Target:

\[
\boxed{
<6 \text{ GPU-hours}
}
\]

Hard stop:

\[
\boxed{
8 \text{ GPU-hours}
}
\]

unless explicitly approved.

Do not run in this stage:

- prompted CoT;
- native Thinking;
- new benchmark discovery;
- model-family replication;
- mechanistic interventions.

---

# 28. Null discipline

A sparse or mixed Stage 12B result does **not** imply:

- visual access is unimportant;
- the existing retrieval mechanism is false;
- Thinking cannot improve retrieval;
- the lifecycle results are irrelevant.

Possible reasons include:

- this cohort is too easy;
- this cohort contains too few native failures;
- the frozen \(E^*\) is sufficient for humans but not the model's preferred intermediate representation;
- some failures involve multiple interacting bottlenecks;
- direct evidence probing alters retrieval demand.

The correct conclusion is limited to the operational taxonomy in this cohort.

---

# 29. Exactly one recommendation at completion

## If PROFILE_INFORMATIVE

Recommend:

> Freeze the Stage 12B bottleneck labels and run prompted CoT plus native Thinking on the same families to test selective rescue by failure type.

## If PROFILE_SPARSE

Recommend:

> Build a fresh harder \(E^*\)-annotated cohort before testing CoT/Thinking rescue.

## If TECHNICAL_STOP

Recommend:

> Repair the native/oracle assay before any scientific interpretation or additional conditions.

Do not launch the recommendation automatically.

---

# 30. Final decision target

Stage 12B exists to answer:

\[
\boxed{
\textbf{When a modern VLM gets a multimodal reasoning problem wrong,
is the bottleneck primarily failure to recover the needed visual evidence,
failure to deploy recoverable evidence in the native task context,
or failure of downstream reasoning even after the evidence is supplied?}
}
\]

Only after this map is established should prompted CoT and native Thinking be compared as **selective rescue mechanisms** rather than as a simple accuracy ladder.
