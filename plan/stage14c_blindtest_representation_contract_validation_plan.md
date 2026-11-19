# Stage 14C-V — Bounded Validation of BlindTest Evidence Representation and Elicitation Contract

**Status:** PROPOSED PLAN / NOT AUTHORIZED / NOT STARTED  
**Parent:** Stage 14C, completed and sealed  
**Scope:** BlindTest line-intersection `E*`-eligible families only; Qwen3-VL-4B Instruct/Thinking  
**Purpose:** Test two **separate** explanations for the Stage 14C anomaly without altering its main results.

> **Central question:** Does the unexpectedly harmful net effect of supplying correct line-intersection evidence reflect how the information is presented to the solver? Separately, did the contradictory answer-only/evidence-only instructions suppress *demonstrated* evidence recovery in the D1 probe?

This is a **prospective intervention on a previously outcome-observed cohort**, not an untouched independent replication. The hypotheses are motivated by Stage 14C outcomes, but all new manipulations, inference rules, prompt text, source-equivalence checks and sample IDs must be frozen **before any Stage 14C-V model outputs**.

---

## 0. Findings motivating the study — fixed historical reference

Stage 14C found the following on **300 BlindTest line-intersection `E*` families**:

| Historical Stage 14C outcome | Instruct | Thinking | Interpretation boundary |
|---|---:|---:|---|
| Wrong native → correct `E*` | 39 | 56 | A rescue event, not proof of pure perceptual failure |
| Correct native → wrong `E*` | **104** | **73** | Important supply-induced regression |
| Correct → correct | 150 | 137 | Stable correct |
| Wrong → wrong | 7 | 34 | Supply-resistant within this assay |
| Net `E*` minus native | **−21.67 pp** | −5.67 pp | Must be reported alongside rescue |
| Post-`E*` Thinking − Instruct | +1.33 pp paired gap | 95% CI [−7.67, +10.33] | Gap not established as zero or positive |

For Instruct, **39/46 = 84.78%** of scored native failures were rescued, but the 104 correct-to-wrong regressions outweighed the rescues. The supply effect for Instruct was **−21.67 pp**, 95% CI [−29.33, −14.00]. All 300 supplied-evidence outputs per model were scored; there were no technical missing outcomes.

The separately prompted D1 visual-evidence probe showed:

- **0/100 complete frozen source-unit recoveries for each model**;
- **100/100 Instruct** responses were bare answers rather than evidence;
- **91/100 Thinking** responses were bare answers;
- the original native **answer-only** instruction remained present after the evidence-probe instruction;
- the few Thinking prose responses contained partial correct observations and contradictions, but not a complete frozen source unit.

**These are distinct phenomena.** The D1 instruction conflict is an observable candidate explanation for D1 elicitation failure. It has **not** been shown to cause the main `E*`-supply regressions. The cause of the main regression is unresolved. The original 300 line-geometry source checks agreed with benchmark golds, but that is not independent certification of all golds or serializations.

**Immutable historical references:** Stage 14C primary-only report and seal; transition tables; BlindTest source/`E*` manifests; D1 prompt/output/review receipts; model and recipe identity; late source-QC log. None may be overwritten, rescored in place, or retroactively relabelled.

---

## 1. Hypotheses and competing explanations

### H-R — Solver-facing representation/interface sensitivity

The **same task-critical visual evidence**, with its factual content held fixed, can yield different image-free solving performance when its textual serialization changes.

**Prediction:** a source-equivalent, clearer representation will reduce Instruct's **correct-native → wrong-supplied-evidence** events and improve net performance relative to a **fresh, concurrently generated original-format control**.

**Alternatives:**

1. all equivalent text formats remain harmful: the native image may supply affordances or information that an answer-safe `E*` text cannot preserve sufficiently for this task;
2. the original `E*` may be under-specified/ambiguous: a formatting-only intervention cannot repair missing information;
3. longer or more formal text itself induces interference or answer-format errors;
4. stochastic decoding or parser handling produces some transitions independent of format;
5. part of the regression is caused by genuine solver limitations even with the available information.

**Important:** `E*` must remain unchanged *semantically*. Adding a solution step, the target intersection/count, the benchmark answer, new source facts, or a gold-derived inference would invalidate this causal comparison.

### H-C — Probe-facing output-contract conflict

The native **answer-only** instruction suppresses the model's visible response to a later instruction to **report visual evidence**, so the original D1 `0/100` complete-unit result underestimates what can be *elicited* under a coherent evidence-only contract.

**Prediction:** removing the contradictory answer-only instruction, while holding image, question, evidence-request wording, model recipe, and scoring fixed, increases **evidence-output compliance** and potentially increases valid evidence-unit/subfact recall.

**Alternatives:**

1. compliance improves but exact evidence recovery stays low (granularity, visual recovery, or scoring limitation);
2. neither compliance nor evidence recovery improves;
3. apparent improvement comes from a changed task request or more forgiving scoring, not the conflict resolution;
4. source representation cannot be expressed accurately under the frozen full-unit criterion.

**Do not infer:** the D1 result establishes what the original native solver internally perceived, or explains the main `E*` regressions.

---

## 2. Populations and selection discipline

### 2.1 Representation experiment — R panel

- **Population:** all **300** previously source-frozen BlindTest `E*`-eligible line-intersection families.
- **Independent unit:** native source family. Retain exact existing family IDs, hashes, gold provenance and `E*` content.
- **No eligibility changes** based on old or new model accuracy. No replacing troublesome items.
- **No new benchmarks or task labels**. The 714-item broad BlindTest native panel remains contextual only.

This 300-family group was selected source-only during Stage 14C, but the current study is prompted by observed negative results on it. Treat external generality as limited to this **selected line-intersection representation**, not to all BlindTest task categories, all visual correspondence, or all valid `E*` constructions.

### 2.2 Evidence-probe experiment — C panel

- **Primary fixed D1 strata:** the **original Stage 14C D1 100** families, with identities unchanged.
- **Prospectively selected expansion:** **100 of the other 200** `E*` families, selected by a hash of source family ID and a predeclared salt, **without consulting per-item model outcomes**.
- Analyze the 100 historical D1 families and the 100 fresh-to-D1 families separately before any pooled summary.
- The expansion is *fresh to the old D1 probe*, **not untouched relative to the Stage 14C solver study**.

The precise hash salt, ordering, IDs, and manifest hashes must be frozen in the execution specification before any new scientific call. If existing D1 IDs or original prompt receipts cannot be reconstructed, **STOP**; do not silently substitute another cohort or reconstruct a prompt from memory.

---

## 3. Required source and interface audit before model calls

**G0-A: Historical artifact load / identity audit (CPU only)**

Verify the exact Stage 14C:

1. 300-family canonical `E*` payloads, per-family source images and questions;
2. original image-free solver input builder, wrapper, evidence serializer, answer-format request and gold scoring;
3. native answer-only instruction and complete D1 evidence-probe prompt order/content;
4. model weights/revisions, processor, vLLM/backend version, BF16, decoding settings, seeds, caps, tokenizer, parsers;
5. original native and `E*` outcomes, provenance and immutable seals;
6. whether all conditions are technically replayable under a **fixed batch/engine context**.

The Stage 14C summary does **not** contain the exact line-geometry evidence schema or complete prompt text. Those **must be recovered from the original artifacts**. Do not invent them, and do not claim this plan alone provides execution-ready exact prompts.

**G0-B: Canonical semantic ledger (outcome-blind)**

For each of the 300 families, construct a representation-independent, immutable ledger of **exactly the source-grounded units already contained in the frozen `E*`**, including units, orientation/ordering, topology, labels and precision **only where those were present in the original `E*`**. The ledger is for **semantic equivalence auditing**, not an expanded oracle. Preserve all structured-source subfacts and their count.

Validation of each candidate serialization must check:

- no evidence omission or new source facts;
- no answer leakage, intersection-count answer, inferred solution or gold-derived relations;
- no silently changed coordinate systems, units, numerical precision, entity binding, scope, ordering or direction;
- no contradicting interpretations of image-derived facts;
- identical semantic content across models;
- record text/token length and field order for later description.

Use two source checks where feasible and retain disagreements and revisions. Same-agent second review **does not** establish independent inter-rater reliability. If semantic equivalence cannot be defended for a family, record it as a **pre-generation representation-invariance failure** and STOP or amend the prospective design *before outcomes*, rather than quietly excluding it after scores.

---

## 4. Experiment R — Content-preserving `E*` representation intervention

### 4.1 Conditions

All conditions are **image-free**, with the same native nonvisual question, answer format, model-specific validated recipe, and **the same factual content**. Only the frozen `E*` serialization changes. Preserve a byte-identical **outer prompt wrapper** where possible.

| Code | Evidence presentation | Purpose | New calls |
|---|---|---|---:|
| **R0** | **Exact original Stage 14C `E*` serialization** | Concurrent baseline; protects against seed/backend drift | 300 × 2 = **600** |
| **R1** | **Canonical typed/field-structured serialization** of the same ledger units | Primary clarity/structure intervention | 300 × 2 = **600** |
| **R2** | **Plain-language, entity-explicit serialization** of the same ledger units | Secondary representation robustness | 300 × 2 = **600** |
| | **Total R** | | **1,800** |

R1 and R2 are **format-package interventions**, not isolated manipulations of naming or token count. They must not add facts or solve the geometry. Specific syntax is to be drafted **after original payload inspection**, then frozen at G1. Schematic labels like `entity_id`, `field`, `value`, `unit` are placeholders, **not claims about the current `E*` schema**.

Do not use gold answers to produce R1/R2. Do not alter the native question to make one condition easier. Preserve model and answer-output contracts across R0–R2. If a necessary format cannot preserve content, do **not** create that condition merely to fill the factorial table; document a gate failure and seek approval.

### 4.2 Primary endpoint R-P1 — Net format benefit for Instruct

For all 300 families, under one fixed replicate and paired scoring:

\[
\Delta_{R, I}=\operatorname{Acc}(I_{R1})-\operatorname{Acc}(I_{R0}).
\]

Define accuracy on a *common set of scored pairs* as the primary paired estimand; report all-four-state counts and worst/best unresolved-outcome bounds separately. Report absolute percentage points and a family-paired bootstrap interval.

### 4.3 Mandatory companion R-P2 — Regression-versus-rescue balance

Using the **frozen Stage 14C native outcome as an immutable contextual reference**, report for each R format and model:

- native correct → format correct;
- native correct → format wrong;
- native wrong → format correct;
- native wrong → format wrong;
- unscorable / technical missing explicitly.

The crucial quantity is **regression reduction** (not rescue percentage alone):

\[
\Delta_{\mathrm{reg},I}
= P(I_{R1}^{-}\mid I_{\mathrm{native}}^{+})
- P(I_{R0}^{-}\mid I_{\mathrm{native}}^{+}).
\]

A negative value means fewer regressions. Also report the change in **rescue**, net correct count and accuracy. Historical 104 regressions/39 rescues are context, **not** a fresh contemporaneous R0 baseline. If R0 replay diverges materially from historical Stage 14C, describe it and **do not** claim to have repaired exactly 104 historical errors.

### 4.4 Secondary R endpoints

- R2 vs R0 in Instruct; R1/R2 vs R0 in Thinking;
- paired Instruct–Thinking gap under each new format;
- overlap of regressed families between formats;
- answer-format adherence, parser ambiguity, cap rate, token length and evidence-context footprint;
- source-only stratification by original `E*` object size/format *if already recorded*.

Do not treat changes in text length or wrapper salience as separately identified mechanisms. A genuinely pure unit-of-information vs format effect would require another carefully controlled intervention.

---

## 5. Experiment C — D1 evidence-elicitation output-contract validation

### 5.1 Matched-contract conditions

Use the **same original source image and question** per family and the exact historical D1 visual-fact request. The only planned primary difference is whether the conflicting *native answer-only instruction* is retained.

| Code | Prompt construction | Purpose | New calls |
|---|---|---|---:|
| **C0** | Exact Stage 14C D1 prompt, including answer-only/evidence request conflict | Fresh concurrent control | 200 × 2 = **400** |
| **C1** | Same D1 visual-evidence request, with the conflicting native answer-only instruction **removed**, not replaced with a new helpful hint | Contract-conflict intervention | 200 × 2 = **400** |
| | **Total C** | | **800** |

The original D1 outputs are preserved as historical context; **C0 must be freshly generated** under the same matched setup as C1, rather than using historical D1 responses as the sole control. Freeze the exact edit diff, token lengths, system/user precedence and output parsing before execution.

No additional source evidence, gold, correctness label or frozen `E*` content is inserted into either prompt. The appended evidence-probe request in both conditions does **not** ask for the final answer. C0 nevertheless retains the conflicting historical native answer-only instruction by design.

### 5.2 Primary endpoint C-P1 — Evidence-output contract compliance

For each model separately:

\[
\Delta_{C,m}=P(\mathrm{evidence\ output}\mid C1,m)
-P(\mathrm{evidence\ output}\mid C0,m).
\]

Record mutually exclusive response modes, e.g. `BARE_ANSWER`, `EVIDENCE_ONLY`, `MIXED`, `REFUSAL_OR_OTHER`, `UNRESOLVED`. Define these from the rendered response **before** looking at gold facts. An evidence-only response is a format outcome; it is not automatically correct evidence.

### 5.3 Mandatory companion C-P2 — Actual demonstrated evidence quality

On each C0/C1 response, with exactly the **same frozen `E*` full-unit requirements and scoring thresholds**:

- complete `E*` source-unit recovery, with numerator/denominator;
- exact required-unit recall and source-object subfact recall;
- contradiction/hallucination counts;
- precision with its exact definition (including penalties for unmatched but true facts);
- source-location / identity binding accuracy where applicable;
- answer leakage or accidental final-answer-only behavior;
- unscorable and cap events.

Report compliance and fidelity side by side. For example, a large compliance gain with persistently zero complete-unit recall supports an **elicitation-contract problem**, but not complete resolution of visual-evidence recovery.

### 5.4 Independence and claims

The probe asks the model to expose visual facts under a **different prompt**. Success or failure cannot establish what the historical native solver internally acquired during its answer generation. C experiments and R experiments have **different input conditions and endpoints**; do not infer that a C1 recovery gain causally mediates an R1 answer gain.

---

## 6. Controlled execution, scoring and statistical analysis

### 6.1 Model identity

Reuse the Stage 14C pinned Qwen3-VL-4B pair and validated recipes, subject to exact artifact check:

| Parameter | Instruct | Thinking |
|---|---|---|
| Temperature | 0.7 | 1.0 |
| Top-p | 0.8 | 0.95 |
| Top-k | 20 | 20 |
| Repetition penalty | 1.0 | 1.0 |
| Presence penalty | 1.5 | 0.0 |
| Max output tokens | 32,768 | 81,920 |
| Precision / execution | BF16 / matched vLLM | BF16 / matched vLLM |

Recover *all* other parameters, exact model revisions and stop conventions from `spec/model_and_recipe_identity.json`; this table does not supersede it. The comparison is **not** equal-compute or a same-weights Thinking switch.

Use one preregistered seed/replicate per family/condition/model, with stable family-linked seeds. Batch size, engine startup, request scheduling and response identity should be held matched as closely as possible. The Stage 14C fixed-context replay issue requires a bounded technical identity check; never assert universal cross-batch bitwise reproducibility.

### 6.2 Scoring / reviews

- Freeze answer adapters and tolerances from Stage 14C. No outcome-based change to line-intersection scoring.
- Preserve response-only review of ambiguous terminal outputs; keep reviewers blinded to condition/model/gold where compatible with the task.
- Freeze D1 required-atom and structured-unit scoring **before** seeing new responses; no relaxing full-unit granularity because the original score was zero.
- Review all unresolved records and a fixed hash-selected QC sample. If independent human review is available **and separately authorized**, measure agreement; otherwise disclose same-agent review honestly.
- Record original parser output, revised adjudication and justification as append-only revisions. Wrong ≠ unscorable ≠ technical missing.

### 6.3 Inference

- Family is the statistical unit; use paired, family-equal comparisons.
- Prespecify 10,000 paired family-bootstrap draws with a frozen seed (suggested `20261009`; freeze in spec before runs).
- Report unadjusted 95% CIs and, if testing R-P1 and C-P1 together as a family, prespecify Holm correction for their two primary p-values. Do not report unadjusted intervals as simultaneously adjusted.
- Analyze Instruct R-P1 first as the main solver-regression question; Thinking format effects are secondary.
- C-P1 tests **elicitation contract**; C-P2 evidence correctness is a distinct companion, not an alternative way to declare the contract hypothesis successful.
- Publish all paired transition counts, common scored denominators, missingness bounds and exact family coverage.
- For C, report the historical-100 and newly-selected-100 strata separately; pooling is secondary.
- No item-level selection by old rescue/regression outcome for primary inference. Old outcomes may be used only after the new primary analysis is sealed for clearly labeled diagnostic case narratives.

### 6.4 Decision criteria

A result is considered informative—not automatically a general mechanism—under the following patterns:

| Observed prospective pattern | Supported conclusion | Still **not** established |
|---|---|---|
| R1 improves paired accuracy and reduces regressions vs R0; evidence truly equivalent | This textual presentation improves this solver interface on the chosen lines cohort | Which formatting component caused it; broad cross-task generalization |
| R1 changes little and R2 changes little | These particular equivalent formatting changes did not repair the regression | Correctness or sufficiency of the original `E*`; impossibility of all textual representations |
| R1 improves but rescue falls or other regressions grow | Format changes trade off failure modes; report **net** and transition tables | Uniformly better recovery |
| C1 improves evidence-output compliance and full-unit recall | The answer-only conflict constrained demonstrated evidence elicitation | Native solver's latent visual knowledge; cause of main supply regressions |
| C1 improves compliance only | Original zero-recall was at least partly an elicitation-format issue; evidence fidelity remains unresolved | Successful visual acquisition |
| C1 remains answer-only / zero recall | This prompt edit did not resolve the assay | Absence of internal visual evidence |

**No arbitrary efficacy threshold is chosen after outcomes.** Report effect sizes and uncertainty even when directions do not support the hypotheses.

---

## 7. Bounded call and resource ceilings (planning only)

| Workstream | Planned new generation calls |
|---|---:|
| Representation R: 300 families × 2 checkpoints × 3 conditions | **1,800** |
| D1 contract C: 200 families × 2 checkpoints × 2 conditions | **800** |
| **Total primary scientific calls** | **2,600** |
| Technical preflight | **At most 24** |
| **Maximum proposed new calls** | **2,624** |

- This table is a **proposed ceiling**, **not authorization to execute**.
- No full 714 native rerun, no 14B/14C math rerun, no extra models/scales, no new unrelated task benchmark.
- If source equivalence/audit fails or projected calls cannot be kept within this bound, **STOP and request an amended plan**. Do not shrink the cohort based on observed effects.
- Suggest **24 GPU-hours** as a *tentative budget to be explicitly approved*, with live observed-allocation accounting and an automatic STOP at the approved limit. This is a planning bound, not an estimated actual cost. Record generation tokens, batch/engine logs, scheduler allocation, worker-exit proxies, and unmetered gaps separately.
- Any additional seeds, D1 response-schema optimization, evidence-enriched `E*`, true semantic-image interventions or external annotators require **separate approval and newly frozen analysis**.

---

## 8. Staged approvals and STOP gates

**Gate G0 — Authorize design only.**  
Review hypotheses, old artifact access, cohort identities, proposed R0/R1/R2 formats, exact C0→C1 prompt diff, budget and endpoints. No generation. **STOP for user approval.**

**Gate G1 — Source-only construction.**  
Freeze the canonical ledger, exact 300×3 prompt strings, 200-family C set, condition hashes, semantic-equivalence checks, answer-leakage QC and all source/score policy files. If equivalent formats cannot be constructed, **STOP** rather than adding facts or changing eligibility.

**Gate G2 — Technical preflight (≤24 calls).**  
Check tokenizer/prompts, rendered images for C, truly image-free R inputs, gold/answer adapters, BF16 vLLM identity, family-linked seeds, engine-context replay, return-format detection, resume/retry/technical-missing logic. Corrections are technical-only, append-only and trigger re-preflight. No scientific tuning using accuracy.

**Gate G3 — R experiment.**  
Run the complete 1,800-call preregistered R grid; freeze response hashes, review and seal R-P1/R-P2 **before** exploring case-level improvements.

**Gate G4 — C experiment.**  
Run 800 calls, freeze output-contract classification and evidence scoring, seal C-P1/C-P2. Where possible, maintain reviewer blindness to condition labels. Neither R results nor historical correct→wrong membership may change C prompts or scores.

**Gate G5 — Cross-experiment synthesis.**  
Present both results side by side. Discuss correspondence between patterns only as hypothesis; do not claim mediation without a separate cross-condition causal test.

**Gate G6 — Final validation and closure.**  
Verify all manifest hashes, source semantic-equivalence records, raw output receipts, scoring versions, review audits, paired denominators, figures and resource accounting. State all negative findings and unresolved explanations. **STOP. No Stage 14D/E/F, new model or method is automatically launched.**

A prior stage is not modified or invalidated simply because a newer condition behaves differently.

---

## 9. Required artifacts

Suggested repository layout:

```text
outputs/stage14c_v_blindtest_validation/
  spec/
    stage14c_v_plan.md
    approval_receipt.md
    inherited_stage14c_identities.json
    frozen_model_recipe.json
    primary_endpoints_and_seed.json
    exact_prompts_and_diffs/
  cohorts/
    blindtest_e300_frozen_reference.jsonl
    d1_old100_identity.jsonl
    d1_new100_source_hash.jsonl
    cohort_and_condition_hashes.json
  source_qc/
    original_evidence_ledger.jsonl
    r0_r1_r2_semantic_equivalence.jsonl
    answer_leakage_and_precision_audit.jsonl
    rejected_revision_history.jsonl
  raw/
    representation_r0_r1_r2/
    elicitation_c0_c1/
    technical_preflight/
  scoring/
    terminal_answer_adjudication.jsonl
    evidence_output_contract.jsonl
    complete_unit_and_subfact_scores.jsonl
    unresolved_and_missingness.jsonl
    fixed_hash_review_qc.jsonl
  analysis/
    representation_primary.json
    r_native_transition_tables.json
    contract_primary.json
    d1_fidelity_companions.json
    paired_family_bootstrap.json
    historical_reference_comparison.json
    interpretation_boundaries.md
  figures/
    figure1_design_and_scope.png
    figure2_representation_net_and_regression.png
    figure3_evidence_output_contract.png
    figure4_contract_vs_evidence_fidelity.png
  audit/
    stage14c_original_seal_reference.json
    source_and_code_hashes.json
    condition_identity_validation.json
    scheduler_and_gpu_accounting.json
    final_validation.json
  summaries/
    stage14c_v_primary_only_summary.md
    stage14c_v_final_summary.md
    next_stage_recommendation.md
```

**Minimum reporting plots:** (1) source/condition schematic; (2) original-format vs equivalent-format accuracy with full rescue/regression transitions; (3) C0→C1 answer-only/evidence-only response mixture; (4) full-unit and subfact recall beside contract compliance. Report paired denominators and CIs in the figure captions. Do not use a single rescue bar as the only visual for the BlindTest result.

---

## 10. Interpretation boundaries and follow-on decision

**If R works:** we have a causal **format/interface sensitivity** finding for this frozen BlindTest line-intersection cohort. This supports, but does not by itself prove, a general account of *evidence usability* across tasks or across model families. A subsequent experiment might isolate entity naming, geometry serialization, evidence completeness or answer interference individually.

**If C works:** the original D1 zero complete-unit recall should be interpreted as compromised evidence elicitation under a contradictory output contract. It does **not** revise the native failure decomposition or prove that visual facts were already available in the historical reasoning states.

**If both work:** do **not** conclude the output-contract conflict caused the old solver regressions. R and C manipulate different conditions; their causal links have not been tested.

**If neither works:** preserve the negative results and revisit alternate explanations without weakening `E*`, changing golds, or selectively excluding failures.

### Hard boundaries

- **Correct `E*`** does not guarantee that a textual interface is sufficient or computationally usable.
- **Conditional rescue** can be high while **net evidence supply** is harmful; always report regressions.
- `E*` rescue is not proof of a pure image-perception error; D1 elicitation is not a readout of native internal evidence.
- Qwen3-VL-4B Instruct vs Thinking is distinct-checkpoint/different-recipe, **not** a causal Thinking-mode toggle.
- This study **does not** establish a universal two-phase mechanism, explain math post-evidence advantage, test semantic addressability, or demonstrate an evidence-aware LOOK/THINK method.
- Stage 14C primary findings, the 104 original Instruct regressions, and the D1 0/100 original results remain exactly as reported, with revisioned context only.

### One allowed next-step recommendation after sealing

Use R/C results to decide **whether** to propose a new source-equivalent evidence-interface study, resume the already planned 14D/E bottleneck analysis, or explicitly close this branch. Any follow-on requires a new plan and user authorization.

**STOP AT STAGE 14C-V.**
