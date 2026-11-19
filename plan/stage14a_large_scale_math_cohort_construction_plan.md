# Stage 14A — Large-Scale Multimodal Math Cohort Construction
## MATH-Vision 3,040 Broad Census + 1,000 \(E^*\)-Annotated Families + MathVerse 788-Family Paired-Modality Cohort

## 0. Objective

Construct and freeze the **large-scale empirical backbone** for the paper before any new model generation.

This stage is source-only.

\[
\boxed{\textbf{NO model inference, NO correctness inspection, NO outcome-adaptive selection}}
\]

Build two complementary cohorts:

1. **MATH-Vision**
   - all 3,040 problems for a broad Thinking-vs-Instruct census;
   - exactly 1,000 final-QC-passed \(E^*\)-eligible families for task-critical visual-evidence profiling.
2. **MathVerse testmini**
   - all 788 unique underlying problem families;
   - verified mapping across available modality variants for paired within-family analysis.

The purpose is to move the paper from a small mechanistic-development study to a large-scale phenomenon study.

---

## 1. Paper-level purpose

Stage 14A prepares the data needed to support three broad empirical claims at scale.

### Claim A — Visual-evidence bottleneck

\[
\boxed{\textbf{A substantial fraction of multimodal math failures occur before successful usable recovery of task-critical visual evidence.}}
\]

### Claim B — Post-evidence Thinking advantage

\[
\boxed{\textbf{The Thinking variant can remain better even after task-critical evidence is explicitly equalized.}}
\]

### Claim C — Role of linguistic accessibility

MathVerse provides benchmark-native paired modality variants that can test whether Thinking benefit changes as the same problem becomes more or less visually dependent.

---

## 2. Why this stage is source-only

Do not run any evaluated model in Stage 14A.

If model outcomes are inspected before \(E^*\) eligibility, source inclusion, difficulty balancing, or MathVerse family/version validity are frozen, later large-scale claims become vulnerable to selection bias.

Stage 14A ends only when all source-side decisions are sealed.

---

## 3. MATH-Vision broad census

Create an immutable manifest containing all 3,040 MATH-Vision problems.

For every problem record:

- canonical problem/family ID;
- image path/hash;
- question text/hash;
- gold answer;
- answer type;
- subject/category if available;
- difficulty if available;
- source metadata;
- historical exposure status;
- alias/duplicate mapping.

No exclusions are made from the 3,040-problem broad census except true dataset corruption or duplication, which must be documented.

This full manifest will later support:

\[
I_{\mathrm{img}}\quad\text{vs}\quad T_{\mathrm{img}}.
\]

---

## 4. Historical-exposure audit

Scan all prior project manifests/artifacts for MATH-Vision IDs.

For each family record:

- `HISTORICALLY_EXPOSED`
- `HISTORICALLY_UNTOUCHED`
- stages where the family appeared;
- whether exposure was technical, source-only, scientific, or outcome-inspected.

Do not remove exposed families from the broad census. Preserve the field so later analyses can report both the full census and an untouched-only sensitivity analysis.

---

## 5. Definition of \(E^*\)

For a MATH-Vision family define:

\[
\boxed{E^*=\text{minimal task-critical visual evidence}}
\]

as the smallest set of **directly image-derived facts** that, together with the nonvisual question text, makes the problem solvable without the original image.

A valid atom must be directly image-grounded, task-relevant, answer-safe, minimally sufficient as part of the set, and free of downstream mathematical derivation.

Valid examples include:

- a point lies on a circle;
- two lines are parallel;
- an angle is \(60^\circ\);
- a segment length is 5;
- a displayed coordinate is \((3,4)\);
- a graph shows a particular intersection relation.

Invalid content includes:

- the final answer;
- a solved equation not directly shown in the image;
- theorem application;
- derived intermediate relation;
- human inference requiring mathematical reasoning beyond reading the image.

---

## 6. \(E^*\)-eligibility criterion

A family is `E_STAR_ELIGIBLE` only if all hold:

1. at least one task-critical fact must come from the image;
2. question text alone is insufficient;
3. required visual evidence can be stated unambiguously;
4. evidence can be rendered answer-safely;
5. image/question are not materially contradictory;
6. the problem is sufficiently specified;
7. evidence can be represented as at most four primary atoms without embedding downstream reasoning.

Record one explicit exclusion reason whenever a criterion fails.

---

## 7. Prospective MATH-Vision \(E^*\) sampling

Target:

\[
\boxed{1,000\text{ final-QC-passed }E^*\text{-eligible families}}
\]

Before screening:

1. create source-only strata from subject/category, difficulty, and answer type;
2. generate deterministic within-stratum ordering using `SHA256(stage14a-v1|mathvision|family_id)`;
3. freeze the complete candidate order.

Review candidates in this order until exactly 1,000 pass final QC.

Do not inspect model correctness or trace behavior during selection. Historical exposure may be recorded but must not determine eligibility.

---

## 8. Replacement rule

The entire remaining MATH-Vision pool acts as a prospective reserve under the sealed ordering.

Procedure:

1. review the next family;
2. determine source-only eligibility;
3. if eligible, annotate and QC;
4. if final-QC-passed, increment accepted count;
5. stop immediately when \(N_{\mathrm{accepted}}=1000\).

Preserve every reviewed exclusion. Do not rewrite the original ordering.

---

## 9. MATH-Vision annotation schema

For each accepted family record:

### Source fields
- `family_id`
- `question`
- `gold_answer`
- `answer_type`
- `subject`
- `difficulty`
- `image_hash`
- `question_hash`

### Evidence fields
- `e_star_atoms`
- `num_e_star_atoms`
- `evidence_request_per_atom`
- `equal_evidence_rendering`
- `entity_references`
- `units`
- `direct_image_grounding_rationale`

### Structural fields
- `task_critical_entities`
- `task_critical_relations`
- `requires_entity_binding`
- `requires_quantity_reading`
- `requires_spatial_relation`
- `requires_diagram_label_reading`
- `requires_graph_table_reading`

### Exposure/QC fields
- `historically_exposed`
- `historical_stages`
- `primary_annotation_status`
- `second_review_status`
- `final_qc_status`
- `exclusion_reason_if_any`

---

## 10. Equal-evidence rendering contract

For every accepted family create one frozen textual oracle rendering:

\[
\boxed{Q+E^*}
\]

The rendering must preserve the original question verbatim, provide only frozen \(E^*\) atoms, add no solution steps/commentary, and preserve symbols and units exactly.

Recommended fixed wrapper:

> `Task-critical visual evidence:`
>
> `- [atom 1]`
> `- [atom 2]`
>
> `[original question]`

Freeze exact formatting before model generation.

---

## 11. Evidence-probe request contract

Create one source-grounded request for each atom. The request must identify the target evidence without revealing its value.

Example:

> `What is the marked angle at vertex B?`

not:

> `Is the marked angle at B equal to 60 degrees?`

For relational atoms:

> `What is the geometric relation between line AB and line CD?`

not:

> `Are AB and CD parallel?`

Freeze all requests now.

---

## 12. MATH-Vision QC

Every screened candidate receives source-only primary review.

All accepted 1,000 families receive mandatory second review of eligibility, every \(E^*\) atom, answer leakage, and equal-evidence rendering.

Freeze 250 accepted families using `SHA256(stage14a-v1|mv-qc|family_id)` for a complete source reread.

If the same agent performs both passes, report same-agent QC rather than independent inter-rater reliability.

Resolve all source-only disagreements before final seal. Never use model behavior to adjudicate \(E^*\).

---

## 13. MATH-Vision source report

At close report:

- total screened;
- final accepted = exactly 1,000;
- exclusion counts by reason;
- subject distribution;
- difficulty distribution;
- answer type;
- \(E^*\) atom count;
- evidence-type categories;
- historical-exposure rate;
- untouched-only subset size.

No performance result is produced.

---

## 14. MathVerse testmini family manifest

Create a complete source manifest for:

\[
\boxed{788\text{ unique MathVerse problem families}}
\]

using the benchmark's underlying problem/family identifier.

The analysis unit is the underlying family, not each modality version independently.

---

## 15. MathVerse modality mapping

For every family verify/map all available versions, expected to include:

- Text Dominant;
- Text Lite;
- Text Only;
- Vision Intensive;
- Vision Dominant;
- Vision Only.

Record for each version:

- canonical version name;
- prompt/question;
- image presence;
- image hash if present;
- gold answer;
- answer type;
- source ID;
- missing/corrupt flag.

Do not silently drop incomplete families.

---

## 16. MathVerse consistency audit

Verify for every family:

1. versions correspond to the same underlying mathematical task;
2. gold answer is consistent across versions;
3. Text Only truly requires no image;
4. Vision Only / Vision Dominant retain essential visual information;
5. no version accidentally reveals the final answer;
6. IDs are not duplicated across families.

Create one final family-level mapping object. Families lacking the expected full set remain with explicit completeness flags.

---

## 17. MathVerse source metadata

For each version record:

- `image_present`
- `textual_information_level`
- `visual_information_level`
- `requires_visual_binding`
- `requires_symbolic_reasoning`
- `contains_explicit_entity_labels`
- `contains_explicit_quantities`
- `requires_low_level_visual_detail`

Use only source content. Do not infer model difficulty.

---

## 18. MathVerse historical-exposure audit

Scan prior project artifacts for MathVerse IDs.

Record exposed vs untouched, stages, and source-only vs outcome-inspected exposure.

Do not remove exposed families from the 788-family corpus. Later analyses can report untouched-only sensitivity.

---

## 19. MathVerse QC

Freeze a deterministic 25% family audit:

\[
\boxed{197\text{ families}}
\]

using `SHA256(stage14a-v1|mathverse-qc|family_id)`.

Second-pass review verifies family-version mapping, answer consistency, modality classification, and source integrity.

Resolve errors before final seal.

---

## 20. Combined empirical architecture

After Stage 14A, the paper's large-N backbone will be:

### Broad native math census

\[
\boxed{3040\text{ MATH-Vision}+788\text{ MathVerse families}=3828\text{ unique math problems}}
\]

### Task-critical visual-evidence profiling

\[
\boxed{1000\text{ MATH-Vision }E^*\text{-annotated families}}
\]

### Benchmark-native modality intervention

\[
\boxed{788\text{ MathVerse paired-modality families}}
\]

This separates breadth, custom evidence equalization, and benchmark-native modality variation.

---

## 21. Future experiments enabled by this stage

Stage 14A does not run them.

### MATH-Vision 3,040
Later run:

\[
I_{\mathrm{img}},\quad T_{\mathrm{img}}.
\]

### MATH-Vision \(E^*\)-1,000
Later run:

\[
E_I,\quad I_{\mathrm{img}},\quad I_{E^*},\quad T_{E^*}
\]

and optionally \(T_{\mathrm{img}}\).

Primary later outputs:

\[
P(I_{E^*}^+\mid I_{\mathrm{img}}^-)
\]

and:

\[
Acc(T_{E^*})-Acc(I_{E^*}).
\]

### MathVerse 788
Later run paired Instruct/Thinking across modality versions.

Primary later output:

\[
\Delta_T(v)=Acc(T_v)-Acc(I_v).
\]

Key comparison:

\[
\boxed{\Delta_T(\text{Text Only})\quad\text{vs}\quad\Delta_T(\text{Vision Dominant / Vision Only})}
\]

---

## 22. Broad census vs multi-seed confirmation

Freeze future confirmation subsets now.

### Broad single-run layer
All 3,040 MATH-Vision and 788 MathVerse families.

### Multi-seed confirmation layer
Freeze:

\[
\boxed{300\text{ MATH-Vision families}}
\]

from the final \(E^*\)-1,000 and:

\[
\boxed{300\text{ MathVerse families}}
\]

using source-only stratified sampling.

These 600 families later receive multi-seed confirmation.

---

## 23. MATH-Vision confirm-300

From the final 1,000, stratify by subject, difficulty, answer type, and \(E^*\) atom count.

Within strata order by `SHA256(stage14a-v1|mv-confirm|family_id)` and select exactly 300.

---

## 24. MathVerse confirm-300

From the 788 families, stratify by answer type, modality completeness, and broad math category if available.

Within strata order by `SHA256(stage14a-v1|mathverse-confirm|family_id)` and select exactly 300.

---

## 25. Reviewer-facing rationale

### Concern: central result uses too few problems
Response enabled by this stage:
- 3,828 unique-problem broad census;
- 1,000 \(E^*\)-annotated MATH-Vision families;
- 600 source-frozen multi-seed confirmation families.

### Concern: \(E^*\) is hand-constructed
Response:
- MATH-Vision custom \(E^*\);
- independent MathVerse human-authored paired modality variants.

### Concern: examples were previously inspected
Response:
- full historical exposure audit;
- untouched-only sensitivity.

### Concern: source selection is outcome-adaptive
Response:
- complete source-only ordering;
- immutable exclusion log;
- zero evaluated-model inference before cohort seal.

---

## 26. Logical boundary of later claims

If:

\[
I_{\mathrm{img}}^-\rightarrow I_{E^*}^+,
\]

allowed wording:

> **Failure occurred before successful usable recovery of task-critical visual evidence.**

Do not automatically call it a pure perception error because textual \(E^*\) also changes representation/binding format.

If:

\[
T_{E^*}>I_{E^*},
\]

allowed wording:

> **The Thinking variant retains an advantage after evidence equalization.**

Do not call this a pure causal effect of Thinking mode unless a same-checkpoint toggle exists.

---

## 27. Stop conditions

Stop without model generation if:

1. MATH-Vision raw data does not contain the expected source set;
2. MathVerse family/version mapping cannot be reconstructed deterministically;
3. fewer than 1,000 MATH-Vision families satisfy the frozen \(E^*\)-eligibility definition;
4. source corruption prevents valid reconstruction for more than 5% of either dataset;
5. a required source field is discovered to depend on model outcomes.

Do not relax eligibility after screening.

If fewer than 1,000 valid families exist, report the maximum eligible cohort and stop.

---

## 28. No-model-call rule

Stage 14A must close with:

\[
\boxed{0\text{ new evaluated-model inference calls}.}
\]

If an external annotator model is proposed for source annotation, stop and request approval because that changes the methodology.

---

## 29. Source preservation

Before review:

- snapshot manifests;
- hash all dataset files;
- hash annotation code;
- freeze sampling code;
- freeze exclusion taxonomy.

After completion:

- verify hashes;
- preserve every reviewed candidate;
- preserve all exclusions;
- never rewrite the ordering to hide failures.

---

## 30. Required source-report figures

### Figure 14A-1 — MATH-Vision screening flow
Show 3,040 → screened → 1,000 final \(E^*\)-eligible.

### Figure 14A-2 — \(E^*\) cohort composition
Subject, difficulty, answer type, atom count.

### Figure 14A-3 — Evidence-type composition
Entity binding, quantity reading, spatial relation, label reading, graph/table reading.

### Figure 14A-4 — MathVerse modality map
Counts under each modality version and complete-family count.

### Figure 14A-5 — Historical exposure composition
Untouched / source-only exposed / outcome-inspected.

These are source statistics, not model results.

---

## 31. Required artifacts

Produce:

1. `stage14a_large_scale_math_cohort_spec.md`
2. `stage14a_mathvision3040_manifest.json`
3. `stage14a_mathvision_historical_exposure.json`
4. `stage14a_mathvision_candidate_order.json`
5. `stage14a_e_star_eligibility_log.jsonl`
6. `stage14a_mathvision_e_star1000_manifest.json`
7. `stage14a_mathvision_e_star_annotations.json`
8. `stage14a_mathvision_equal_evidence_renderings.json`
9. `stage14a_mathvision_evidence_probe_requests.json`
10. `stage14a_mathvision_qc_records.json`
11. `stage14a_mathvision_confirm300_manifest.json`
12. `stage14a_mathverse788_family_manifest.json`
13. `stage14a_mathverse_variant_mapping.json`
14. `stage14a_mathverse_source_metadata.json`
15. `stage14a_mathverse_historical_exposure.json`
16. `stage14a_mathverse_qc_records.json`
17. `stage14a_mathverse_confirm300_manifest.json`
18. `stage14a_source_statistics.json`
19. `stage14a_preservation_manifest.json`
20. `stage14a_resource_accounting.json`
21. `stage14a_summary.md`

Preserve every prior Stage 12/13 artifact unchanged.

---

## 32. Completion criteria

### MATH-Vision
- full 3,040 manifest sealed;
- exposure audit complete;
- exactly 1,000 final-QC-passed \(E^*\)-eligible families;
- all 1,000 have frozen \(E^*\);
- all 1,000 have frozen equal-evidence rendering;
- all 1,000 have frozen evidence-probe requests;
- confirm-300 frozen.

### MathVerse
- all 788 underlying families mapped;
- modality availability documented;
- consistency audit complete;
- confirm-300 frozen.

### Preservation
- no scientific model outcomes inspected;
- all exclusions preserved;
- all hashes verified;
- zero new evaluated-model inference calls.

---

## 33. Exactly one recommendation at completion

If Stage 14A completes successfully:

> **Launch the preregistered large-scale math phenomenon study: broad Instruct-vs-Thinking census on all 3,828 unique problems, plus visual-evidence/equal-evidence profiling on the 1,000-family MATH-Vision \(E^*\) cohort and paired-modality analysis on MathVerse.**

Do not launch automatically.

If 1,000 valid \(E^*\) families cannot be obtained under the frozen rule:

> **Stop and report the maximum source-valid \(E^*\) cohort size before changing any scientific target.**

---

## 34. Final decision target

Stage 14A answers no performance question.

It creates a reviewer-resistant source foundation:

\[
\boxed{\textbf{3828 unique multimodal math problems}}
\]

with:

\[
\boxed{\textbf{1000 prospectively selected task-critical visual-evidence annotations}}
\]

and:

\[
\boxed{\textbf{788 benchmark-native paired-modality MathVerse families}.}
\]

The next stage can then ask, at scale:

\[
\boxed{\textbf{Where does multimodal mathematical reasoning fail, and when does Thinking help?}}
\]

without relying on a small development cohort or outcome-adaptive selection.
