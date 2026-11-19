# Stage 12A — Multimodal “Lost Keys” Pilot: Visual-Evidence Availability and Reasoning Rescue

## 0. One-line objective

Test whether multimodal reasoning contains a **Lost-Keys-like failure state**:

\[
\boxed{
\textbf{the task-critical visual evidence is directly recoverable,
but the model still fails when forced to answer without intermediate reasoning}
}
\]

and whether **explicit inference-time reasoning selectively rescues those failures**.

Primary question:

\[
\boxed{
\textbf{Does prompted reasoning preferentially rescue Answer-Only failures
on items where the required visual evidence }E^*\textbf{ is already directly recoverable?}
}
\]

This is the first gate for the new top-level paper claim:

> **Where do multimodal reasoning failures occur, and which of them are recovered by inference-time reasoning and native Thinking?**

This stage does **not** yet test native Thinking as the main comparison.

It first establishes whether the multimodal analogue of a “Lost Keys” phenotype exists at sufficient yield.

---

# 1. Why this experiment is necessary for the paper

The paper is being reorganized around a higher-level question:

\[
\boxed{
\textbf{Why do multimodal language models fail,
what does inference-time reasoning recover,
and why can Thinking help?}
}
\]

The existing mechanistic results already support two downstream claims:

1. reasoning context causally selects task-relevant visual sources;
2. successfully retrieved evidence enters internal/textual causal carriers and can become sufficient for later text-only reasoning.

What is still missing is the **behavioral failure-state decomposition** that motivates those mechanisms.

A final wrong answer alone cannot distinguish:

- the required visual evidence was unavailable;
- the evidence was available but not successfully accessed/used for the task;
- the evidence was correctly acquired but downstream reasoning failed.

Stage 12A asks whether the second state is common enough to anchor the paper’s main story.

---

# 2. Connection to the “Empty Shelves or Lost Keys?” logic

The conceptual analogue is:

## Parametric factuality setting

\[
\text{fact available?}
\rightarrow
\text{directly recallable?}
\rightarrow
\text{recoverable with thinking?}
\]

## Our multimodal setting

\[
\boxed{
\text{visual evidence }E^*\text{ directly recoverable?}
\rightarrow
\text{Answer-Only task success?}
\rightarrow
\text{recoverable with explicit reasoning?}
}
\]

Important terminology difference:

Do **not** call failed visual evidence probes “not encoded.”

The image is an external input.

Use:

- `EVIDENCE_RECOVERABLE`
- `EVIDENCE_NOT_RECOVERABLE`

rather than:

- encoded / not encoded.

---

# 3. Candidate Claim 1 if this program succeeds

Outcome-neutral form:

> **Visual Evidence Profiling separates multimodal reasoning failures into evidence-availability, evidence-access/use, and downstream-reasoning bottlenecks, revealing which failures are selectively recovered by inference-time reasoning and native Thinking.**

Stronger access-dominant form, only if supported later:

> **Many multimodal reasoning failures reflect recoverable-but-unused visual evidence rather than unavailable perception, and inference-time reasoning selectively rescues these failures.**

Stage 12A tests only the first necessary piece:

\[
\boxed{
\text{recoverable evidence}
+
\text{Answer-Only failure}
+
\text{Reasoning rescue}
}
\]

---

# 4. Dataset and model

## Model

Use only:

\[
\boxed{
\textbf{Qwen3-VL-2B-Instruct}
}
\]

for the primary Stage 12A experiment.

This is deliberate.

The cleanest first contrast is within the **same checkpoint**:

\[
\boxed{
\text{Answer-Only}
\rightarrow
\text{Reasoning+Answer}
}
\]

so model weights remain fixed.

Native Thinking is reserved for the next stage if the Lost-Keys gate passes.

---

## Dataset

Reuse the existing Stage 11A clean \(E^*\)-eligible MathVision set:

\[
\boxed{
61 \text{ independent problem/image families}
}
\]

Advantages:

- \(E^*\) already exists;
- \(E^*\) sufficiency was reviewed;
- no new benchmark mining is needed;
- this stage is a bounded phenotype/yield test.

This is **development/pilot evidence**, not final held-out confirmation for the headline claim.

If Stage 12A passes, a fresh held-out confirmation cohort will be required later.

---

# 5. Frozen task-critical evidence \(E^*\)

For each family reuse the frozen:

\[
\boxed{
E^*=\{e_1,\ldots,e_k\},
\quad 1\le k\le4
}
\]

where \(E^*\) is the minimal set of image-derived propositions sufficient to solve the original question with the nonvisual question text.

Do not:

- repair \(E^*\) after seeing Stage 12A outputs;
- add facts because a model failed;
- remove facts because a model guessed correctly;
- reveal the final answer in an evidence probe.

---

# 6. Three core conditions

Stage 12A runs three conditions on the **same Instruct checkpoint**.

---

## E — Direct visual-evidence probe

Purpose:

> determine whether the required \(E^*\) is directly recoverable when explicitly requested.

The model sees:

- the original image;
- a short request for the frozen task-critical evidence only.

It does **not** solve the original problem.

### Prompt principle

Use strongly constrained output formatting.

Example for one fact:

> Inspect the image and report only the requested visual value.  
> Do not explain or reason.  
> Requested fact: What is the value of angle ABC?  
> Answer only with the value.

For multiple facts:

> Inspect the image and report only the requested visual facts.  
> Do not solve the original problem.  
> Do not explain or show reasoning.  
> Return exactly:
> E1: [value]
> E2: [value]

### Evidence status

\[
E^+=\text{all required }e_i\text{ scored correct}
\]

\[
E^-=\text{otherwise}
\]

Retain partial correctness separately.

---

## D — Instruct Answer-Only

Purpose:

> approximate a minimal-inference task condition.

Prompt:

> Solve the original problem.  
> **Respond only with the correct option letter. Do not provide an explanation or intermediate reasoning.**

For MathVision choices A–E, require exactly one valid option letter after normalization.

This is **not** called “Qwen official Direct.”

Name it:

\[
\boxed{
\texttt{Instruct Answer-Only}
}
\]

because official MathVision Direct permits spontaneous reasoning.

---

## C — Instruct Reasoning+Answer

Purpose:

> allow/explicitly elicit additional inference-time reasoning on the same checkpoint.

Prompt:

> Solve the original problem.  
> **Think step by step. End your response with `Final answer: X`, where X is the correct option letter.**

Use the same image/question content as D.

Only the reasoning instruction/output contract differs.

Name it:

\[
\boxed{
\texttt{Instruct Reasoning+Answer}
}
\]

---

# 7. Runtime discipline

Because D and C use the same checkpoint and are intended as a prompt-level intervention:

- same Qwen3-VL-2B-Instruct revision;
- same image preprocessing;
- same tokenizer/processor;
- same generation backend;
- same stochastic decoding family;
- same random-seed policy.

Use the official benchmark-specific Instruct sampling recipe unless a technical incompatibility exists:

- temperature 0.7;
- top-p 0.8;
- top-k 20;
- repetition penalty 1.0;
- presence penalty 1.5.

Do not use Thinking decoding settings for the Instruct arms.

---

# 8. Output-budget policy

The three conditions intentionally permit different amounts of intermediate computation.

This is part of the experimental manipulation.

## Evidence probe E

Use a short cap:

\[
\boxed{
128 \text{ generated tokens maximum}
}
\]

because only 1–4 atomic facts are requested.

## Answer-Only D

Use a very short cap:

\[
\boxed{
16 \text{ generated tokens maximum}
}
\]

The intended response is one option letter.

If the model violates the instruction and begins reasoning, classify output-format noncompliance separately.

Do not extend the cap.

## Reasoning+Answer C

Use:

\[
\boxed{
8192 \text{ generated tokens maximum}
}
\]

for the pilot.

If >20% of C cases hit the cap without a committed final, STOP and diagnose the reasoning prompt/runtime before interpreting rescue.

Do not increase the cap post hoc.

---

# 9. Technical prompt-validation gate

Before running all 61 families, use exactly:

\[
\boxed{
12 \text{ technical cases}
}
\]

selected deterministically from the 61.

Do not select by correctness.

Validate only output behavior.

## E gate

- at least 10/12 obey the evidence-only schema;
- severe long reasoning in at most 1/12.

## D gate

- at least 10/12 produce a parseable option-only response;
- intermediate reasoning in at most 1/12;
- no repetition pathology.

## C gate

- at least 10/12 produce a committed final answer;
- cap hits at most 2/12;
- no severe repetition pathology in >1/12.

Do not use accuracy to choose prompts.

If a prompt fails the format gate, one bounded wording repair is permitted **before** opening full-cohort correctness.

The repair criterion is output-format compliance only.

---

# 10. Primary failure-state definitions

For each item define:

- \(E^+\): all frozen \(E^*\) facts directly recovered;
- \(E^-\): \(E^*\) not fully recovered;
- \(D^+\): Answer-Only task correct;
- \(D^-\): Answer-Only task failed;
- \(C^+\): Reasoning+Answer task correct;
- \(C^-\): Reasoning+Answer task failed.

Failure includes:

- valid wrong option;
- no valid option;
- format-invalid answer.

Preserve these categories separately in raw artifacts.

---

# 11. The multimodal Lost-Keys phenotype

Define:

\[
\boxed{
L
=
E^+\land D^-
}
\]

Interpretation:

> the task-critical visual evidence is directly recoverable under explicit demand, but the model fails when required to answer the original problem without intermediate reasoning.

This is the primary phenotype whose existence/yield must be established.

Do **not** yet call every \(L\) case a causal retrieval failure.

It is an operational **recoverable-evidence / direct-task-failure state**.

---

# 12. Primary endpoints

Freeze four primary endpoints.

## P1 — Evidence-recoverable rate

\[
\boxed{
P1=P(E^+)
}
\]

Question:

> how often is the required visual evidence directly recoverable?

## P2 — Lost-Keys phenotype rate

\[
\boxed{
P2=P(E^+\land D^-)
}
\]

Question:

> how often does the model fail the original task despite directly recoverable visual evidence?

This is the most important **existence/yield** endpoint.

## P3 — Reasoning rescue among recoverable-evidence failures

\[
\boxed{
R_{\text{avail}}
=
P(C^+\mid D^-,E^+)
}
\]

Question:

> among operational Lost-Keys cases, how often does explicit reasoning rescue the task?

## P4 — Rescue selectivity

Define:

\[
R_{\text{unavail}}
=
P(C^+\mid D^-,E^-)
\]

and:

\[
\boxed{
\Delta R
=
R_{\text{avail}}
-
R_{\text{unavail}}
}
\]

This is the key conceptual endpoint.

Expected Lost-Keys-style signature:

\[
\boxed{
\Delta R>0
}
\]

meaning reasoning rescue is concentrated on failures where the required visual evidence was already directly recoverable.

---

# 13. Why P4 matters more than overall accuracy

The headline is **not**:

\[
Acc_C>Acc_D.
\]

That result alone would only show that CoT prompting helps.

The stronger mechanistic pattern is:

\[
\boxed{
P(C^+\mid D^-,E^+)
>
P(C^+\mid D^-,E^-)
}
\]

This shows **selective recovery of a specific failure state**.

That is the multimodal analogue of asking whether additional reasoning recovers information that was available but inaccessible in the task context.

---

# 14. Secondary outcome taxonomy

Partition Answer-Only failures \(D^-\) into:

## F1 — Evidence-unavailable candidate

\[
E^-\land D^-
\]

## F2 — Recoverable-evidence task failure

\[
E^+\land D^-
\]

## F3 — CoT-recoverable lost key

\[
E^+\land D^-\land C^+
\]

## F4 — Persistent recoverable-evidence failure

\[
E^+\land D^-\land C^-
\]

Report counts and proportions.

Do not force deeper mechanistic labels yet.

---

# 15. Optional trace annotation — secondary only

Only after P1–P4 are frozen, inspect C traces for:

\[
F3 \text{ and } F4
\]

cases.

Annotate whether frozen \(E^*\) becomes:

- `CORRECT_SUFFICIENT`
- `PARTIAL`
- `WRONG`
- `CONFLICTING`
- `NOT_EXTERNALIZED`

in the visible reasoning.

Purpose:

> generate hypotheses about whether CoT rescue occurs through improved evidence access or downstream utilization.

This annotation is **not** required for the Stage 12A gate.

Do not let trace annotation determine the primary phenotype.

---

# 16. Statistical unit and inference

Independent unit:

\[
\boxed{
\text{problem/image family}
}
\]

Use all 61 eligible families.

Report:

- exact counts;
- Wilson 95% intervals for P1/P2;
- bootstrap 95% intervals for \(R_{\text{avail}}\), \(R_{\text{unavail}}\), and \(\Delta R\);
- fixed seed;
- 4,000 bootstrap draws.

Do not treat:

- evidence atoms;
- generated tokens;
- reasoning steps

as independent samples.

---

# 17. Main GO / NO-GO gate

This pilot exists to decide whether the new Claim 1 story has enough natural support to justify a held-out Thinking follow-up.

## Strong GO

Proceed if all are true:

1. at least:
   \[
   \boxed{
   12
   }
   \]
   independent Lost-Keys phenotype cases:
   \[
   E^+\land D^-
   \]

2. at least:
   \[
   \boxed{
   6
   }
   \]
   CoT-recoverable lost-key cases:
   \[
   E^+\land D^-\land C^+
   \]

3. point estimate:
   \[
   \boxed{
   \Delta R\ge15\text{ pp}
   }
   \]

4. rescue selectivity is not driven by a single evidence/problem type;

5. E/D/C technical format gates pass.

If these hold, the multimodal Lost-Keys story is worth developing.

## Limited GO

If:

- 8–11 Lost-Keys cases; or
- 4–5 CoT rescues; or
- \(\Delta R>0\) but below 15pp;

then run only a small held-out confirmation before involving native Thinking.

Do not promote Claim 1 yet.

## NO-GO

If:

- fewer than 8 Lost-Keys cases; or
- fewer than 4 CoT rescues; or
- \(\Delta R\le0\);

then do not build the paper around a Lost-Keys analogy.

Return to the already-supported retrieval/lifecycle Claims.

---

# 18. What a null does NOT mean

A weak Stage 12A result does **not** prove:

- visual evidence access is never a bottleneck;
- Thinking cannot help retrieval;
- the existing reasoning-conditioned retrieval mechanism is unimportant.

Possible reasons include:

- direct \(E^*\) probes change the demand too strongly;
- 61 Stage 11A items are not the right difficulty regime;
- failure is dominated by downstream reasoning;
- \(E^*\) is incomplete at the representational level;
- Answer-Only suppresses useful computation too aggressively.

The correct conclusion would be:

> this operational Lost-Keys profile is not sufficiently prevalent/selectively recoverable in this cohort to support the main headline.

---

# 19. What Stage 12A may claim if successful

Supported:

> **Some multimodal failures occur despite directly recoverable task-critical visual evidence, and explicit inference-time reasoning preferentially rescues these recoverable-evidence failures.**

Not yet supported:

> Thinking is better because it retrieves visual evidence better.

Not yet supported:

> the model had the evidence internally during Answer-Only.

Not yet supported:

> the failure is caused by a specific retrieval head/pathway.

Those require later stages.

---

# 20. Next stage if Strong GO

The next stage should introduce:

\[
\boxed{
T=\text{Native Thinking}
}
\]

on a fresh held-out cohort.

Primary questions:

\[
P(T^+\mid C^-,D^-,E^+)
\]

and whether Thinking-only rescues reflect:

1. improved task-conditioned evidence access; or
2. better downstream reasoning after evidence is already available.

Then use an Equal-Evidence Oracle for causal localization.

Do **not** launch this automatically.

---

# 21. Relation to the paper's later mechanistic claims

If Stage 12A succeeds, the paper can be organized:

## Claim 1 — Why models fail and what reasoning recovers

\[
\text{visual evidence availability}
\rightarrow
\text{Answer-Only failure}
\rightarrow
\text{reasoning rescue}
\]

## Claim 2 — How reasoning recovers task-relevant evidence

Existing result:

\[
\boxed{
\text{reasoning context}
\rightarrow
\text{target-specific causal visual retrieval}
}
\]

including A→B→A retargeting.

## Claim 3 — What happens after evidence is retrieved

Existing lifecycle:

\[
\text{Q/K routing}
\rightarrow
\text{Value-rich transfer}
\rightarrow
\text{local K/V + residual}
\rightarrow
\text{causal reasoning text}
\rightarrow
\text{text-sufficient computation}
\]

Thus Stage 12A is the behavioral front door to the already-supported mechanistic story.

---

# 22. Required figures

## Figure 1 — Visual Evidence Profiling

Flow:

\[
E^* \text{ recoverable?}
\rightarrow
D \text{ success?}
\rightarrow
C \text{ rescue?}
\]

Show counts.

## Figure 2 — Failure-state composition

Among Answer-Only failures:

- \(E^-\);
- \(E^+\);
- \(E^+\) rescued by CoT;
- \(E^+\) persistent.

## Figure 3 — Selective reasoning rescue

Compare:

\[
R_{\text{avail}}
\]

vs:

\[
R_{\text{unavail}}.
\]

This is the centerpiece Stage 12A figure.

## Figure 4 — Optional visible-evidence-state analysis

Only if secondary trace annotation is executed.

Show C-trace \(E^*\) states for rescued vs persistent cases.

---

# 23. Required artifacts

Produce:

1. `stage12a_multimodal_lost_keys_spec.md`
2. `stage12a_frozen_e_star_manifest.json`
3. `stage12a_prompt_templates.md`
4. `stage12a_technical_prompt_validation.json`
5. `stage12a_evidence_probe_results.parquet`
6. `stage12a_answer_only_results.parquet`
7. `stage12a_reasoning_results.parquet`
8. `stage12a_failure_profiles.parquet`
9. `stage12a_primary_inference.json`
10. optional `stage12a_reasoning_trace_evidence_states.parquet`
11. `stage12a_go_nogo_decision.json`
12. `stage12a_resource_accounting.json`
13. `stage12a_summary.md`

---

# 24. Compute budget

Primary new generation:

\[
61\times3=183
\]

logical runs.

Most E and D runs are very short.

Only C runs can be long.

Target:

\[
\boxed{
<2.5 \text{ GPU-hours}
}
\]

Hard stop:

\[
\boxed{
4 \text{ GPU-hours}
}
\]

unless explicitly approved.

Do not run:

- native Thinking;
- Equal-Evidence Oracle;
- new benchmark discovery;
- model-family replication

in this stage.

---

# 25. Exactly one recommendation at completion

## If Strong GO

Recommend:

> Freeze a fresh held-out cohort and test which recoverable-evidence failures are rescued by native Thinking beyond prompted reasoning, followed by Equal-Evidence Oracle localization.

## If Limited GO

Recommend:

> Run only a small held-out confirmation of the Lost-Keys phenotype before adding native Thinking.

## If NO-GO

Recommend:

> Do not promote the Lost-Keys framing; return the paper to the established reasoning-conditioned retrieval and visual-to-text lifecycle claims.

Do not launch the recommendation automatically.

---

# 26. Final decision target

Stage 12A exists to answer one question:

\[
\boxed{
\textbf{Does multimodal reasoning contain a sufficiently common,
selectively reasoning-recoverable state in which the required visual evidence
is directly recoverable but Answer-Only task performance fails?}
}
\]

If yes, this becomes the behavioral foundation of the new main Claim 1.

If no, stop the new headline before involving Thinking.
