# Stage 14B Plan — Large-Scale Math Phenomenon

## 0. Scope

Stage 14A is complete and sealed. Stage 14B starts from the frozen source-only cohorts and must not modify Stage 14A inclusion/exclusion decisions based on model outcomes.

Primary model pair:

- Qwen3-VL-4B-Instruct
- Qwen3-VL-4B-Thinking

Stage 14B is a **phenomenon-establishment stage**, not a mechanism-discovery stage.

The goals are to test at large scale whether:

1. the Thinking variant outperforms the matched-size Instruct variant on visual math;
2. incomplete recovery of task-critical visual evidence is a substantial failure bottleneck;
3. a Thinking advantage remains after correct task-critical evidence is equalized.

Do not use Stage 14B to explain *why* Thinking helps.

---

# 1. Primary scientific questions

## Q1 — Large-scale native-image Thinking gain

On all 3,040 MATH-Vision native problems:

\[
G_{\rm img}=Acc(T_{\rm img})-Acc(I_{\rm img})
\]

Question:

> Does the Qwen3-VL-4B Thinking variant outperform the matched-size Instruct variant on visual math at benchmark scale?

---

## Q2 — Large-scale evidence-recovery bottleneck

On the frozen MATH-Vision \(E^*\)-1,000 cohort:

\[
R_I=P(I_{E^*}^{+}\mid I_{\rm img}^{-})
\]

Secondary:

\[
R_T=P(T_{E^*}^{+}\mid T_{\rm img}^{-})
\]

Question:

> How often does supplying correct task-critical visual evidence rescue a native-image failure?

Interpretation boundary:

\(E^*\) rescue should be described as rescue from **incomplete demonstrated recovery of task-critical visual evidence**, not as pure perceptual failure. Supplying \(E^*\) may alter accessibility, representation, and binding.

---

## Q3 — Large-scale post-evidence Thinking advantage

On the same \(E^*\)-1,000 cohort:

\[
G_{\rm post}=Acc(T_{E^*})-Acc(I_{E^*})
\]

Question:

> Does a Thinking advantage remain when both variants receive the same correct task-critical evidence without the image?

If positive, the allowed conclusion is:

\[
\boxed{\text{Thinking advantage is not reducible to visual evidence recovery alone}}
\]

This does not identify the downstream mechanism.

---

## Q4 — MathVerse modality profile

Across the frozen 788 MathVerse families, for each native modality version \(v\):

\[
\Delta_T(v)=Acc(T_v)-Acc(I_v)
\]

Question:

> Does the Thinking–Instruct gap vary with how visual versus textual the available evidence is?

This is descriptive in Stage 14B. Task selectivity and causal explanation belong to later stages.

---

# 2. Frozen evaluation populations

## 2.1 MATH-Vision broad census

Use all 3,040 frozen native problem IDs.

Preserve:

- native records;
- native golds;
- conservative family / alias metadata;
- Stage 14A provenance.

Report:

1. raw problem-level accuracy;
2. family-aware uncertainty / sensitivity where applicable.

Do not describe the 3,040 items as 3,040 verified independent tasks.

---

## 2.2 MATH-Vision \(E^*\)-1,000

Use exactly the frozen 1,000 eligible families.

Stage 14A metadata remain source covariates only:

- structured vs scalar evidence;
- evidence atom count;
- structured-object size;
- open-ended vs multiple choice;
- source difficulty;
- subject;
- evidence type.

These may not be used to redefine the primary cohort after outcomes are observed.

---

## 2.3 MathVerse 788

Use all 788 frozen families and all 4,728 native versions in the census.

Keep Stage 14A source-validity fields immutable.

Recommended reporting layers:

### Census layer
Report all 788 families / native versions.

### Predeclared semantically clean paired layer
Before outcome inspection, freeze a source-only rule for stronger paired-modality interpretation using Stage 14A fields such as:

- `same_task`
- `gold_consistency`
- `text_only_sufficient`
- `visual_versions_sufficient`
- `answer_safe`

### Sensitivity layer
Report source-failure and ambiguity strata separately.

Do not create new source-validity judgments after inspecting model performance.

---

## 2.4 Confirmation subsets

Use the frozen:

- MATH-Vision confirm-300
- MathVerse confirm-300

only for preregistered multi-seed robustness.

Do not use them for prompt tuning, subgroup discovery, or model selection.

---

# 3. Required model conditions

## 3.1 MATH-Vision 3,040

Run:

\[
I_{\rm img}
\]

\[
T_{\rm img}
\]

under identical native-image evaluation conventions.

---

## 3.2 MATH-Vision \(E^*\)-1,000

Required four-condition panel:

\[
I_{\rm img},\quad
T_{\rm img},\quad
I_{E^*},\quad
T_{E^*}
\]

For \(I_{E^*}\) and \(T_{E^*}\):

- remove the image;
- provide the same frozen \(E^*\);
- use one fixed evidence serialization policy;
- do not customize evidence wording by model;
- do not add model-specific hints;
- do not leak the answer;
- preserve Stage 14A evidence semantics.

Freeze the evidence prompt format before the full run.

---

## 3.3 Optional evidence-recovery scoring

If a reliable preregistered scorer can assess native recovery of frozen \(E^*\), optionally measure:

\[
E_I,\quad E_T
\]

and:

\[
G_{\rm access}=Acc(E_T)-Acc(E_I)
\]

Do not force this endpoint if scoring validity is weak.

---

# 4. Execution controls

Freeze before the main run:

- exact checkpoint revisions;
- precision;
- image preprocessing;
- chat template;
- system / user prompts;
- \(E^*\) serialization;
- temperature;
- top-p / top-k if used;
- max new tokens;
- stop criteria;
- seed policy;
- answer extraction;
- scoring;
- timeout policy;
- retry policy;
- OOM handling;
- technical-failure handling.

Reuse validated Stage 12/13 conventions wherever compatible.

No condition should receive a different decoding budget solely because it is Instruct or Thinking unless explicitly preregistered.

Technical missingness must remain distinct from wrong answers.

---

# 5. Primary endpoints

## P1 — Broad native-image Thinking difference

MATH-Vision 3,040:

\[
G_{\rm img}=Acc(T_{\rm img})-Acc(I_{\rm img})
\]

Report:

- Instruct accuracy;
- Thinking accuracy;
- paired percentage-point difference;
- confidence interval;
- family-aware sensitivity / clustered interval;
- correct / wrong / unscorable / technical-missing counts.

---

## P2 — Evidence rescue in Instruct

On \(E^*\)-1,000:

\[
R_I=P(I_{E^*}^{+}\mid I_{\rm img}^{-})
\]

Also report the full paired transition table:

| Native image | Equal evidence | Interpretation |
|---|---|---|
| wrong | correct | rescue |
| correct | wrong | regression |
| correct | correct | stable correct |
| wrong | wrong | persistent failure |

Keep unscorable and technical missingness separate.

---

## P3 — Post-evidence Thinking difference

On \(E^*\)-1,000:

\[
G_{\rm post}=Acc(T_{E^*})-Acc(I_{E^*})
\]

This is the large-scale replication of the earlier targeted equal-evidence result.

---

## P4 — MathVerse modality profile

For each native modality version \(v\):

\[
\Delta_T(v)=Acc(T_v)-Acc(I_v)
\]

Use family-paired inference.

Report the profile without treating it as a mechanism.

---

# 6. Secondary endpoints

Predeclared secondary analyses may include:

- \(R_T=P(T_{E^*}^{+}\mid T_{\rm img}^{-})\);
- native-vs-equal-evidence transitions for Thinking;
- Instruct↔Thinking paired outcome transitions;
- open-ended vs multiple choice;
- source difficulty 1–5;
- structured vs scalar \(E^*\);
- evidence atom count;
- subject;
- evidence type;
- answer length;
- reasoning length;
- truncation / cap rates;
- unscorable rate;
- technical missingness.

These cannot redefine the primary result.

Avoid subgroup fishing in Stage 14B. Explanatory heterogeneity belongs mainly to Stages 14C–14E.

---

# 7. Statistical plan

## 7.1 Paired contrasts

Use paired analyses whenever the same problem/family is evaluated under both model conditions.

Recommended:

- paired bootstrap confidence intervals;
- cluster / family bootstrap where multiple records share a conservative family;
- McNemar-style paired transition analysis for binary correctness where appropriate.

Report absolute percentage-point differences.

---

## 7.2 MATH-Vision dependence structure

Because MATH-Vision contains known conservative aliases/families:

- report raw 3,040-item benchmark accuracy;
- perform family-clustered inference or sensitivity;
- do not treat known aliases as independent evidence in uncertainty estimation.

Unknown dependence may remain and should be stated as a limitation.

---

## 7.3 MathVerse inference unit

Use the family as the primary inferential unit for modality comparisons.

Do not count six versions of one family as six independent tasks.

---

## 7.4 Primary hypothesis family

Keep the primary family small:

1. \(G_{\rm img}\) on MATH-Vision 3,040;
2. \(R_I\) on \(E^*\)-1,000;
3. \(G_{\rm post}\) on \(E^*\)-1,000;
4. predeclared MathVerse modality-profile contrast(s).

If formal multiplicity correction is used, freeze it before outcome inspection.

---

# 8. Confirmatory multi-seed analysis

Run the frozen 300 + 300 confirmation subsets after the main specification is frozen.

Purpose:

- sign stability;
- effect-size stability;
- item/family transition stability;
- stochastic decoding robustness.

Report:

- per-seed accuracy;
- per-seed \(\Delta_T\);
- mean and dispersion across seeds;
- fraction of seeds preserving the primary sign;
- item/family transition stability.

Do not use these subsets for effect discovery and then call the same analysis independent confirmation.

---

# 9. Interpretation rules

## Allowed if supported

### If P1 is positive
> The Qwen3-VL-4B Thinking variant outperforms the matched-size Instruct variant on large-scale native visual math.

### If P2 shows substantial rescue
> Incomplete demonstrated recovery of task-critical visual evidence is a substantial failure bottleneck.

### If P3 is positive
> The Thinking advantage persists when correct task-critical evidence is equalized, so the advantage is not reducible to visual evidence recovery alone.

### If MathVerse varies by modality
> The Thinking advantage is heterogeneous across modality realizations of the same underlying tasks.

---

## Not allowed in Stage 14B

Do not conclude:

- Thinking mode causally causes the performance difference;
- semantic addressability explains the difference;
- Thinking works because it builds symbolic state;
- Thinking works because it retrieves vision longer or more often;
- one critical deduction explains the gap;
- one distributed visible-text block explains the gap;
- computational buffering explains the gap;
- derived-state priming explains the gap;
- small models benefit more or less;
- the effect generalizes across model families;
- math is uniquely selective for Thinking.

Those belong to later stages.

---

# 10. Outcome logic

## Outcome A — all three main phenomena replicate

If:

\[
G_{\rm img}>0,
\]

\[
R_I \text{ is substantial},
\]

and

\[
G_{\rm post}>0,
\]

then Stage 14B establishes the large-N behavioral backbone:

\[
\boxed{\text{Thinking helps visual math at scale}}
\]

\[
\boxed{\text{visual evidence recovery is a major failure bottleneck}}
\]

\[
\boxed{\text{post-evidence Thinking advantage exists at scale}}
\]

Proceed to Stage 14C.

---

## Outcome B — native gain replicates, post-evidence gap disappears

Interpretation:

> The large-scale Thinking advantage may be primarily upstream of evidence equalization.

Revise the broad post-evidence claim.

---

## Outcome C — post-evidence gap persists, native gain is small

Interpretation:

> A downstream Thinking advantage exists, but its expression under native visual input may be offset by other factors.

Do not alter the cohort.

---

## Outcome D — evidence rescue is weak

Interpretation:

> The earlier evidence-recovery bottleneck may have been cohort-specific or overestimated.

Revise Claim 1 accordingly.

---

## Outcome E — no robust large-scale effect

This is a valid negative result.

Do not rescue the hypothesis through post-hoc subgroup selection.

Frozen metadata may be used only for clearly labeled exploratory diagnosis after the primary analysis is sealed.

---

# 11. Recommended execution order

## Phase 1 — Technical preflight

Use a tiny non-tuning technical set to verify:

- checkpoint loading;
- image preprocessing;
- prompt identity;
- \(E^*\) serialization;
- answer extraction;
- scoring;
- token cap;
- seed reproducibility;
- missingness handling;
- output logging.

Preflight is for implementation correctness only.

---

## Phase 2 — MATH-Vision broad census

Run:

\[
I_{\rm img},\ T_{\rm img}
\]

on all 3,040 native problems.

Freeze raw outputs before analysis.

---

## Phase 3 — \(E^*\)-1,000 equal-evidence panel

Run:

\[
I_{\rm img},\
T_{\rm img},\
I_{E^*},\
T_{E^*}
\]

with exact condition receipts.

If native outputs from Phase 2 are specification-identical, reuse them rather than recompute.

---

## Phase 4 — MathVerse 788

Run Instruct and Thinking across all native versions under frozen native prompts.

Preserve exact family/version mapping.

---

## Phase 5 — Primary analysis freeze

Compute only preregistered primary endpoints first.

Seal:

- raw scores;
- transition tables;
- confidence intervals;
- technical missingness;
- source-validity joins.

Do not inspect subgroup narratives before the primary results are sealed.

---

## Phase 6 — Secondary / sensitivity analyses

After the primary freeze:

- source-validity strata;
- evidence metadata;
- format / difficulty;
- reasoning-length diagnostics;
- failure transitions.

---

## Phase 7 — Confirm-300 multi-seed

Run the frozen confirmation subsets under the same specification.

---

# 12. Required artifacts

Suggested structure:

```text
outputs/stage14b/
  spec/
    stage14b_plan.md
    frozen_run_config.json
    prompt_templates/
    model_revisions.json
    scoring_spec.md

  manifests/
    mathvision_3040_eval_manifest.jsonl
    mathvision_e1000_eval_manifest.jsonl
    mathverse_788_eval_manifest.jsonl
    confirm300_mathvision.jsonl
    confirm300_mathverse.jsonl

  raw/
    mathvision_native/
    mathvision_e1000/
    mathverse/
    confirmatory/

  scoring/
    answer_extraction.jsonl
    scored_outputs.jsonl
    technical_missingness.jsonl

  analysis/
    primary_results.json
    transition_tables.json
    bootstrap_results.json
    family_cluster_sensitivity.json
    mathverse_modality_profile.json
    secondary_results.json

  figures/
    figure1_mathvision_native_gain.png
    figure2_evidence_rescue.png
    figure3_post_evidence_gain.png
    figure4_mathverse_modality_profile.png
    figure5_confirmatory_stability.png

  audit/
    completion_validation.json
    condition_identity_audit.json
    source_manifest_hashes.json
    resource_accounting.json
    artifact_catalog.json

  summaries/
    stage14b_primary_summary.md
    stage14b_final_summary.md
    next_stage_recommendation.md
```

---

# 13. Minimum figures

## Figure 1 — Broad MATH-Vision native performance

Instruct vs Thinking accuracy on all 3,040 problems with uncertainty.

## Figure 2 — Evidence rescue

Native Instruct outcome → equal-evidence Instruct outcome on \(E^*\)-1,000.

## Figure 3 — Equal-evidence Thinking gap

\[
I_{E^*}\quad\text{vs}\quad T_{E^*}
\]

with paired effect and confidence interval.

## Figure 4 — MathVerse modality profile

\[
\Delta_T(v)
\]

across native modality versions using family-paired analysis.

## Figure 5 — Confirmatory stability

Multi-seed effect magnitude / sign on the frozen 300 + 300 subsets.

---

# 14. Stage boundary

Stage 14B ends after the large-scale phenomenon results, robustness checks, and source-validity sensitivities are sealed.

Do not include:

- generic VQA comparison;
- fine-grained / correspondence comparison;
- 2B / 8B / 32B scale comparison;
- trace taxonomy;
- semantic-addressability manipulation;
- second-model-family replication.

These belong to:

- **14C — Task selectivity**
- **14D — Scale × Task × Modality**
- **14E — Trace characterization**
- **14F — Causal semantic-addressability test**
- **14G — External model replication**

---

# 15. One-sentence objective

\[
\boxed{
\textbf{Establish at large scale whether Qwen3-VL-4B Thinking improves visual math,
whether task-critical visual-evidence recovery is a major failure bottleneck,
and whether a Thinking advantage persists after correct evidence is equalized.}
}
\]
