# Stage 11B — Harder-MathVision Yield Screen and Held-Out Equal-Evidence Oracle

## 0. One-line objective

Use a **harder MathVision cohort on Qwen3-VL-2B** to obtain enough informative Thinking-vs-CoT separation, then causally test whether the Thinking advantage is explained by **better acquisition/access to task-critical visual evidence** or by **better downstream reasoning after the same evidence is supplied**.

Primary question:

\[
\boxed{
\textbf{If Thinking and prompted CoT receive the same correct task-critical visual evidence, how much of the native Thinking–CoT performance gap remains?}
}
\]

This stage is designed to address the main limitations of Stage 11A:

1. too few clean Thinking-correct / CoT-failed families;
2. low yield of uniquely localizable bottleneck cases;
3. explicit evidence probes were heavily confounded by unequal token-cap behavior;
4. the previous design was primarily observational rather than causal.

---

# 1. Paper-level claim this stage can enable

Current Claims 1 and 2 are already strong:

## Claim 1

\[
\boxed{
\text{reasoning demand}
\rightarrow
\text{target-specific causal visual retrieval}
}
\]

## Claim 2

\[
\boxed{
\text{visual retrieval}
\rightarrow
\text{causal internal/textual carriers}
\rightarrow
\text{text-sufficient reasoning}
}
\]

Stage 11B asks whether a third paper claim can be supported:

> **Thinking's advantage over prompted CoT can be causally localized to visual-evidence acquisition/access, downstream reasoning over already-correct evidence, or both.**

This claim is only promoted if the held-out oracle experiment has adequate support.

---

# 2. Why harder MathVision + Qwen3-VL-2B

Stage 11A used 128 matched MathVision families.

Only:

- 61/128 had clean sufficient \(E^*\);
- 12/61 were Thinking-correct / CoT-failed;
- only 4 of those had a unique nonmixed bottleneck localization.

The limiting factor was **informative sample yield**, not evidence that Thinking has no advantage.

A harder MathVision cohort on Qwen3-VL-2B is attractive because it may move more items into the useful regime:

\[
\boxed{
\text{Thinking succeeds often enough}
\quad\text{while}\quad
\text{CoT fails often enough}
}
\]

The desired cohort is not simply “hard.”

It must jointly maximize:

\[
\boxed{
\text{Thinking–CoT separation}
+
E^*\text{-identifiability}
+
\text{nontrivial downstream reasoning}
}
\]

---

# 3. Core causal quantity

For each held-out \(E^*\)-eligible item, measure two conditions.

## Native multimodal condition

\[
Acc_T^{native},\quad Acc_C^{native}
\]

where:

- \(T\) = native Thinking;
- \(C\) = prompted CoT.

Define:

\[
G_{native}
=
Acc_T^{native}
-
Acc_C^{native}
\]

## Equal-Evidence Oracle condition

Remove the image and supply the **same correct task-critical visual evidence** \(E^*\) to both modes.

\[
Acc_T^{oracle},\quad Acc_C^{oracle}
\]

Define:

\[
G_{oracle}
=
Acc_T^{oracle}
-
Acc_C^{oracle}
\]

The primary causal localization quantity is:

\[
\boxed{
\Delta G
=
G_{native}
-
G_{oracle}
}
\]

Interpretation:

- large positive \(\Delta G\): much of the native Thinking advantage lies upstream of downstream reasoning, in obtaining/accessing the needed visual evidence;
- \(G_{oracle}\approx G_{native}\): Thinking retains its advantage even after visual evidence is equalized, implicating downstream reasoning/integration;
- partial gap reduction: both stages contribute.

---

# 4. Competing mechanisms

## M1 — Visual-evidence acquisition/access advantage

Thinking is better mainly because it obtains the right visual evidence more reliably.

Prediction:

\[
G_{native}>0
\]

but:

\[
G_{oracle}\approx 0
\]

or is substantially smaller.

Thus:

\[
\boxed{
\Delta G>0
}
\]

with strong gap closure.

## M2 — Downstream reasoning advantage

Thinking remains better even when both modes receive the same correct \(E^*\).

Prediction:

\[
G_{oracle}\approx G_{native}>0.
\]

Thus:

\[
\Delta G\approx 0.
\]

## M3 — Mixed advantage

Equal evidence reduces but does not eliminate the gap:

\[
0<G_{oracle}<G_{native}.
\]

Interpretation:

> Thinking benefits both evidence acquisition/access and downstream reasoning.

## M4 — No stable Thinking advantage on the selected cohort

If:

\[
G_{native}
\]

is small or unstable in the held-out cohort, the experiment is not informative about the source of a Thinking advantage.

Do not interpret oracle results as localization if there is little native gap to explain.

---

# 5. Model

Use:

\[
\boxed{
\textbf{Qwen3-VL-2B}
}
\]

with:

- native Thinking;
- exact prompted-CoT protocol used in Stage 9A.

Direct is secondary and not required for the primary causal claim.

Freeze:

- checkpoint revision;
- tokenizer;
- native Thinking template;
- prompted-CoT template;
- BF16;
- TF32 off;
- greedy decoding for the new Stage 11B runs;
- image preprocessing;
- generation cap;
- answer extraction/scoring.

No model-family comparison in this stage.

---

# 6. Overall stage structure

Stage 11B has two strictly separated phases.

## Phase 11B-D — Discovery / yield screen

Goal:

> identify a prospectively defined harder-MathVision stratum with high informative yield.

This phase chooses the **selection rule**, not individual outcome-favorable items.

## Phase 11B-C — Held-out confirmation

Apply the frozen selection rule to unseen MathVision families and run:

- native Thinking;
- native prompted CoT;
- Equal-Evidence Oracle Thinking;
- Equal-Evidence Oracle CoT.

Only Phase 11B-C supports the paper-level causal claim.

---

# 7. Discovery pool

Use a fresh MathVision pool not overlapping the Stage 11A 128-family cohort.

Target:

\[
\boxed{
96\text{–}128 \text{ discovery families}
}
\]

The discovery pool may span harder:

- subjects;
- reasoning-depth categories;
- visual-evidence types;
- official difficulty labels;
- solution-complexity strata,

provided the source metadata are available.

Do not define “hard” by looking at held-out outcomes.

---

# 8. Discovery-stage screening variables

For each discovery family, estimate only the quantities needed to choose a stratum.

## D1 — \(E^*\) eligibility

Can the task be reduced to:

\[
1\text{–}4
\]

human-verifiable image-derived propositions that are sufficient, with the original question text, to solve the problem?

## D2 — Native Thinking correctness

\[
Y_T
\]

## D3 — Native CoT correctness

\[
Y_C
\]

## D4 — Informative discordance

\[
I=
\mathbb{1}[Y_T=1,Y_C=0]
\]

## D5 — Downstream reasoning depth

A coarse, prospectively defined measure such as:

- number of nonvisual reasoning steps after \(E^*\);
- solution-step count;
- category-level reasoning-depth annotation.

This is used descriptively to avoid selecting a purely perceptual task subset.

---

# 9. Discovery selection objective

For candidate strata \(s\), compute:

\[
Y_E(s)
=
P(E^*\text{-eligible}\mid s)
\]

\[
G(s)
=
P(T=1,C=0\mid E^*,s)
\]

and:

\[
Y_I(s)
=
Y_E(s)\times G(s).
\]

The preferred stratum should maximize **informative yield**:

\[
\boxed{
Y_I(s)
}
\]

subject to:

1. adequate \(E^*\) eligibility;
2. nontrivial downstream reasoning;
3. at least two evidence/problem types;
4. no single narrow category dominating the entire cohort;
5. Thinking accuracy not collapsing near zero;
6. CoT accuracy not collapsing near zero.

The target is a **separation sweet spot**, not maximal difficulty.

---

# 10. Discovery-stage candidate strata

Predefine candidate bins before opening discovery outcomes.

Example acceptable axes:

- official MathVision difficulty;
- subject family;
- reasoning-depth category;
- diagram/graph/table/geometry type;
- one vs multi-fact \(E^*\);
- solution length bin.

Do not generate arbitrary post hoc combinations after viewing outcomes.

Maximum number of candidate strata to compare:

\[
\boxed{
12
}
\]

Choose one primary selection rule.

At most one secondary fallback rule may be frozen if the primary rule yields too few held-out items.

---

# 11. Discovery GO gate

Proceed to held-out confirmation only if the selected stratum satisfies all:

1. \(E^*\)-eligible rate:
   \[
   \boxed{\ge 40\%}
   \]

2. Thinking-correct / CoT-failed rate among eligible:
   \[
   \boxed{\ge 20\%}
   \]

3. Thinking native accuracy among eligible:
   \[
   \boxed{20\%\text{–}75\%}
   \]

4. CoT native accuracy among eligible:
   \[
   \boxed{10\%\text{–}65\%}
   \]

5. at least:
   \[
   \boxed{12}
   \]
   informative discordant discovery items.

If these fail, do not launch a large oracle experiment.

The correct interpretation is:

> this benchmark stratum does not generate enough informative Thinking-vs-CoT separation.

---

# 12. Held-out confirmation cohort

After freezing the discovery selection rule, sample a **non-overlapping held-out cohort**.

Target:

\[
\boxed{
200\text{–}300 \text{ MathVision families}
}
\]

before \(E^*\) eligibility filtering.

Goal:

\[
\boxed{
\ge 100
}
\]

clean \(E^*\)-eligible held-out families.

A minimum acceptable primary cohort is:

\[
\boxed{
80
}
\]

eligible held-out families.

If fewer than 80 are obtained, the experiment becomes a limited pilot and cannot support a strong Claim 3.

---

# 13. \(E^*\) definition

For each held-out family:

\[
\boxed{
E^*
=
\text{the minimal set of image-derived propositions
sufficient to solve the task together with the original question text}
}
\]

Constraints:

- 1–4 atomic facts;
- image-derived;
- no final answer;
- no downstream arithmetic consequence;
- no unnecessary facts;
- phrased in a model-neutral textual format.

Examples:

- `AB = 6`
- `∠ABC = 60°`
- `the red curve intersects y=2 at x=1 and x=5`
- `there are 4 shaded triangles`

---

# 14. \(E^*\) construction blinding

Build \(E^*\) before opening held-out model outcomes.

Reviewers may see:

- image;
- question;
- source/gold solution.

They may not see:

- Thinking answer;
- CoT answer;
- native correctness;
- oracle outputs.

Freeze:

- eligibility;
- atomic evidence;
- accepted normalization;
- oracle serialization;
- sufficiency judgment.

This is mandatory.

---

# 15. \(E^*\) sufficiency validation

Use two independent semantic reviews.

For each item:

- `SUFFICIENT`
- `INSUFFICIENT`
- `AMBIGUOUS`

Primary cohort requires:

\[
\boxed{
\texttt{SUFFICIENT}
}
\]

Agreement target:

\[
\kappa\ge0.6
\]

where meaningful.

If agreement is poor, simplify the evidence representation or stop.

Do not silently adjudicate large amounts of ambiguity into eligibility.

---

# 16. Native conditions

For every held-out \(E^*\)-eligible item run:

## N-T — Native Thinking

Original:

- image;
- question;
- native Thinking mode.

## N-C — Native CoT

Original:

- image;
- question;
- exact prompted-CoT protocol.

These runs establish:

\[
G_{native}.
\]

Use the same decoding regime across the Stage 11B confirmation cohort.

---

# 17. Equal-Evidence Oracle condition

For each eligible item, remove the image.

Construct:

> **Task-relevant visual evidence:**  
> [frozen serialized \(E^*\)]  
>  
> **Question:**  
> [original question]

Then run:

## O-T — Oracle Thinking

Text-only question + correct \(E^*\), native Thinking mode.

## O-C — Oracle CoT

Text-only question + correct \(E^*\), prompted CoT mode.

The exact \(E^*\) serialization must be identical across O-T and O-C.

The oracle should not tell the model how to reason.

It should only supply the correct visual facts.

---

# 18. Oracle serialization

Use a fixed template.

Example:

> The following facts have been read correctly from the image and may be used as given:
> - Fact 1: ...
> - Fact 2: ...
> Now solve the original problem.

Do not include:

- final answer;
- derived intermediate calculations;
- chain-of-thought hints;
- mode-specific wording;
- confidence statements.

Keep the oracle evidence semantically identical across modes.

---

# 19. Oracle validity controls

Before primary outcomes, validate the oracle on a small fixed set.

## V1 — Human sufficiency

Question + \(E^*\) is enough to solve the problem.

## V2 — No answer leakage

\(E^*\) does not encode the final answer through wording.

## V3 — Image independence

No image or original multimodal cache is present.

## V4 — Same evidence across modes

Byte/semantic equality of the \(E^*\) block.

## V5 — Prompt-only control

For a small subset, add an equally long neutral factual block that does not solve the visual part.

This checks that any improvement is not just extra textual scaffolding.

Maximum prompt-only control subset:

\[
\boxed{
24 \text{ items}
}
\]

---

# 20. Primary endpoints

Freeze four primary endpoints.

## P1 — Native Thinking advantage

\[
\boxed{
P1
=
G_{native}
=
Acc_T^{native}-Acc_C^{native}
}
\]

The experiment is only interpretable if P1 is meaningfully positive.

## P2 — Oracle Thinking advantage

\[
\boxed{
P2
=
G_{oracle}
=
Acc_T^{oracle}-Acc_C^{oracle}
}
\]

This measures residual downstream advantage after evidence equalization.

## P3 — Gap closure

\[
\boxed{
P3
=
\Delta G
=
G_{native}-G_{oracle}
}
\]

This is the primary causal localization quantity.

## P4 — Mode-specific oracle gain

For each mode:

\[
Gain_T
=
Acc_T^{oracle}-Acc_T^{native}
\]

\[
Gain_C
=
Acc_C^{oracle}-Acc_C^{native}
\]

Primary contrast:

\[
\boxed{
P4
=
Gain_C-Gain_T
}
\]

If CoT benefits more from evidence equalization than Thinking, this supports an upstream evidence-access contribution to the native gap.

---

# 21. Main claim gate

Promote Claim 3 only if:

1. native held-out Thinking advantage P1 is positive and practically meaningful;
2. at least one of P2/P3 is precisely estimated enough to distinguish the major mechanisms;
3. conclusions are not driven by a single subject/evidence type;
4. \(E^*\) sufficiency/serialization validation passes;
5. oracle conditions do not show major completion/pathology imbalance;
6. held-out cohort selection was frozen before outcomes;
7. no outcome-based item filtering is used.

---

# 22. Outcome interpretation

## Outcome A — Native gap largely closes under oracle

Pattern:

\[
G_{native}>0
\]

and:

\[
G_{oracle}\approx 0
\]

with:

\[
\Delta G>0.
\]

Supported claim:

> **Much of the Thinking advantage arises before downstream reasoning over correct evidence, implicating more effective acquisition/access of task-critical visual information.**

Do not claim a specific hidden retrieval mechanism from the oracle alone.

Use prior Claim 1 results to motivate the interpretation.

## Outcome B — Native gap persists under oracle

Pattern:

\[
G_{oracle}\approx G_{native}>0.
\]

Supported claim:

> **Thinking retains a substantial advantage even when both modes receive identical correct visual evidence, localizing much of the gain to downstream reasoning/integration rather than visual evidence acquisition.**

## Outcome C — Partial gap closure

Pattern:

\[
0<G_{oracle}<G_{native}.
\]

Supported claim:

> **Thinking improves both evidence acquisition/access and downstream reasoning.**

Quantify the fraction of the native gap removed by evidence equalization:

\[
\boxed{
ClosureFraction
=
\frac{G_{native}-G_{oracle}}{G_{native}}
}
\]

Report only when \(G_{native}\) is sufficiently above zero.

## Outcome D — No held-out native gap

If:

\[
G_{native}\approx 0,
\]

the selected harder cohort failed to reproduce an informative Thinking advantage.

Do not interpret oracle differences as explaining a nonexistent gap.

Stop Claim 3.

## Outcome E — Oracle degrades both modes

If supplying \(E^*\) reduces accuracy strongly for both modes, the oracle representation itself is invalid or disruptive.

Do not interpret this as evidence about bottleneck location.

Inspect only predeclared validity controls.

---

# 23. Secondary native evidence analysis

Only after primary oracle inference is frozen, inspect native reasoning traces.

Use Stage 11A-style states:

- `CORRECT_SUFFICIENT`
- `PARTIAL`
- `WRONG`
- `CONFLICTING`
- `ABSENT`
- `NOT_EXTERNALIZED`

Purpose:

> explain the causal oracle result, not define it.

Examples:

## If gap closes

Ask whether CoT more often has wrong/partial/absent task-critical evidence.

## If gap persists

Ask whether both modes often already contain sufficient evidence, suggesting downstream divergence.

Do not use these annotations to override the oracle result.

---

# 24. Discordant-item analysis

After primary cohort inference, report:

\[
T\text{-correct}/C\text{-wrong}
\]

and:

\[
C\text{-correct}/T\text{-wrong}
\]

subsets.

For Thinking-gain items, ask whether oracle:

- rescues CoT;
- preserves Thinking-only success;
- causes both to succeed;
- causes neither to succeed.

These are secondary mechanistic descriptions.

Do not define the primary cohort from discordant outcomes.

---

# 25. Difficulty / evidence-type robustness

Report the primary quantities by:

- MathVision subject;
- evidence type;
- 1-fact vs multi-fact \(E^*\);
- reasoning-depth bin;
- native difficulty bin.

These are robustness checks.

Do not make separate headline claims from small subgroups.

---

# 26. Statistics

Independent unit:

\[
\boxed{
\text{problem/image family}
}
\]

Use:

- paired family-level effects;
- equal weighting;
- 4,000 bootstrap draws;
- fixed seed;
- 95% percentile intervals.

Primary paired contrasts:

- P1;
- P2;
- P3;
- P4.

Use multiplicity-aware intervals across the four primary endpoints.

For binary matched mode differences, also report McNemar-style exact summaries as descriptive support.

Do not treat:

- tokens;
- reasoning steps;
- evidence atoms

as independent samples.

---

# 27. Sample-size / precision logic

Target:

\[
\boxed{
100\text{–}150
}
\]

held-out \(E^*\)-eligible families.

Why:

Stage 11A observed approximately a 13pp Thinking-over-CoT final-accuracy difference on eligible items, but with wide uncertainty.

A cohort of 100+ eligible families gives substantially better precision for:

\[
G_{native},\quad G_{oracle},\quad \Delta G.
\]

If the held-out eligible cohort is:

- 100–150: full confirmatory analysis;
- 80–99: acceptable but precision-limited;
- 50–79: limited pilot only;
- <50: stop.

Do not compensate for low eligible yield by post hoc broadening \(E^*\) rules.

---

# 28. Compute strategy

The design is intentionally more efficient than Stage 11A.

## Discovery

Native Thinking + CoT only.

Target:

\[
96\text{–}128\times2
\]

runs.

## Held-out confirmation

For each eligible item:

- native Thinking;
- native CoT;
- oracle Thinking;
- oracle CoT.

Maximum target:

\[
150\times4=600
\]

main runs.

No explicit \(E^*\) probe arm is required for every item.

Direct is optional and secondary.

Target GPU budget:

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

without explicit approval.

---

# 29. Why the explicit evidence probe is no longer primary

Stage 11A showed major mode-dependent cap behavior:

- Direct rarely capped;
- CoT often capped;
- Thinking almost always capped under the explicit probe prompt.

Therefore probe accuracy was difficult to interpret as pure visual evidence accessibility.

Stage 11B instead asks a cleaner causal question:

\[
\boxed{
\textbf{What happens when correct visual evidence is held identical across modes?}
}
\]

Explicit probes may be run only on a small diagnostic subset if needed.

They are not a primary endpoint.

---

# 30. Optional Direct arm

If compute allows, run Direct on a deterministic subset of:

\[
\boxed{
32\text{–}48
}
\]

held-out eligible families under:

- native multimodal Direct;
- text-only Equal-Evidence Direct.

Purpose:

> determine whether the same evidence equalization explains Direct→CoT→Thinking performance progression.

This is secondary.

Do not let Direct increase the primary compute budget substantially.

---

# 31. Required figures

## Figure 1 — Causal bottleneck design

Show:

\[
\text{Image}
\rightarrow
E^*
\rightarrow
\text{downstream reasoning}
\]

and the Equal-Evidence intervention that replaces the upstream visual-evidence stage with identical correct text.

## Figure 2 — Discovery yield map

For candidate harder-MathVision strata plot:

- \(E^*\)-eligibility;
- Thinking accuracy;
- CoT accuracy;
- Thinking-correct / CoT-failed yield.

Show why the frozen stratum was selected.

## Figure 3 — Native vs oracle accuracy

Four paired estimates:

- Native Thinking;
- Native CoT;
- Oracle Thinking;
- Oracle CoT.

## Figure 4 — Gap decomposition

Show:

\[
G_{native}
\]

vs:

\[
G_{oracle}
\]

and:

\[
\Delta G.
\]

This is the centerpiece Claim 3 figure.

## Figure 5 — Secondary native evidence explanation

Only after primary inference.

Show native evidence states by mode and how they relate to oracle rescue/persistent gap.

---

# 32. Required artifacts

Produce:

1. `stage11b_equal_evidence_spec.md`
2. `stage11b_discovery_manifest.json`
3. `stage11b_discovery_e_star_eligibility.parquet`
4. `stage11b_discovery_mode_results.parquet`
5. `stage11b_selection_rule.json`
6. `stage11b_heldout_manifest.json`
7. `stage11b_heldout_e_star_gold.parquet`
8. `stage11b_e_star_sufficiency_review.json`
9. `stage11b_native_results.parquet`
10. `stage11b_oracle_results.parquet`
11. `stage11b_oracle_validity.json`
12. `stage11b_primary_inference.json`
13. `stage11b_discordant_analysis.json`
14. optional `stage11b_native_evidence_states.parquet`
15. optional `stage11b_direct_subset.json`
16. `stage11b_resource_accounting.json`
17. `stage11b_summary.md`

---

# 33. Paper wording by result

## If upstream evidence-access advantage dominates

> **Thinking's advantage over prompted CoT is substantially reduced when both modes receive identical correct visual evidence, indicating that a major component of the gain arises before downstream reasoning, during acquisition or access to task-critical visual information.**

This would connect Claim 3 naturally to Claim 1.

## If downstream reasoning advantage dominates

> **Thinking retains a substantial advantage over prompted CoT even when both receive identical correct visual evidence, indicating that much of the gain arises downstream of visual evidence acquisition.**

This would connect Claim 3 naturally to Claim 2.

## If mixed

> **Equalizing visual evidence narrows but does not eliminate the Thinking–CoT gap, indicating complementary gains in evidence acquisition/access and downstream reasoning.**

---

# 34. Null discipline

A null oracle gap change does not imply visual retrieval is irrelevant.

Possible explanations include:

- both modes already had sufficient evidence on many items;
- downstream reasoning dominates the selected cohort;
- \(E^*\) omits hidden representational differences;
- oracle wording changes reasoning dynamics;
- selection does not isolate the right difficulty regime.

Likewise, strong gap closure does not prove that Thinking's advantage is specifically the Stage 4A retrieval mechanism.

It supports a broader upstream evidence-acquisition/access contribution.

Mechanism-specific attribution must remain grounded in prior causal retrieval results.

---

# 35. Stop rules

Stop Claim 3 if any of the following occurs:

1. discovery cannot identify a stratum meeting the GO gate;
2. held-out \(E^*\)-eligible cohort <50;
3. held-out native Thinking–CoT gap is negligible;
4. oracle validity fails;
5. oracle causes major pathological noncompletion imbalance;
6. results depend on post hoc item filtering.

Do not rescue by:

- changing \(E^*\) after oracle outcomes;
- selecting only Thinking-correct / CoT-wrong items;
- switching to a different benchmark after seeing failed confirmation;
- increasing token caps post hoc for only one mode.

---

# 36. Exactly one recommendation at completion

## If the held-out oracle result is clean and informative

Recommend:

> Promote a third paper claim localizing the Thinking–CoT performance gap to upstream visual evidence access, downstream reasoning, or a quantified mixture of both.

## If the result is inconclusive

Recommend:

> Keep Thinking-vs-CoT as a discussion-level open question and finalize the paper around the established causal retrieval and visual-to-text lifecycle claims.

Do not launch another benchmark search automatically.

---

# 37. Final decision target

This stage exists to answer:

\[
\boxed{
\textbf{Why does native Thinking outperform prompted CoT on harder multimodal reasoning:
because it obtains the right visual evidence more effectively,
because it reasons better once the evidence is known,
or both?}
}
\]

The Equal-Evidence Oracle is the causal test.

The harder-MathVision discovery phase exists only to ensure the held-out cohort contains enough informative cases to answer that question.
