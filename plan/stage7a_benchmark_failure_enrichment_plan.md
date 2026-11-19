# Stage 7A-Bench Plan — Benchmark Failure-Enrichment and Source-Faithfulness Sweep
## Finding Natural Regimes Where Qwen3-VL-4B-Thinking Produces Causally Diagnosable Unfaithful Visual Reads

## 0. Purpose

Stage 7A established that source-faithful visual reads can be causally certified, but strong unfaithful states were too rare for monitor/intervention work.

Observed strong states:

```text
FAITHFUL_READ                    181
PRIOR_FILL                         0
WRONG_SOURCE_READ                  3
STALE_SOURCE_READ                  0
SOURCE_COUPLED_EXTRACTION_ERROR    1
DOWNSTREAM_INTEGRATION_ERROR       2
```

The next step is therefore not to train a monitor immediately and not to manufacture arbitrary synthetic failures. First identify existing benchmarks where the current primary model:

```text
Qwen3-VL-4B-Thinking
```

naturally makes enough source-faithfulness errors while evidence remains localizable and causally testable.

Central question:

> Which benchmark makes source-faithfulness failures frequent enough to study, while still allowing demanded source, alternative source, emitted evidence, and error direction to be identified?

This is a benchmark-selection / failure-enrichment stage.

---

# 1. Why This Stage Is Necessary

The current paper story is:

```text
reasoning context
→ visual retrieval demand
→ target-specific retrieval
→ dynamic source switching / refresh
→ source-faithful evidence emission
```

The missing practical step is a sufficiently large cohort of:

```text
wrong-source reads
prior-filled reads
stale-source reads
source-coupled extraction errors
```

Current MathVerse/MathVista/DocVQA-style controlled cohorts produced strong faithful reads but too few unfaithful states.

The ideal next benchmark should satisfy:

```text
enough failures
+
enough faithful controls
+
source-localizable evidence
+
clean readouts
+
counterfactual/editable sources
```

---

# 2. Paper Claim Enabled by a Positive Result

A positive sweep would support:

> Source-faithfulness failures become more common in visually difficult or source-confusable regimes while retaining the same causal grounding framework observed in easier tasks.

A stronger result would be:

> Increasing task difficulty changes the frequency of grounding states, not necessarily their causal form.

This creates the bridge to:

```text
causal failure cohort
→ source-faithfulness monitor
→ grounding-aware decoding / rollback
```

---

# 3. Important Boundary

A low benchmark score is not automatically a visual-grounding failure.

A benchmark may be difficult because of:

```text
reasoning depth
arithmetic
OCR
long context
layout
planning
integration
```

Therefore benchmark selection is based on causal source-faithfulness yield, not raw accuracy.

The benchmark with the lowest score is not necessarily the best benchmark.

---

# 4. Primary Benchmark Candidates

Inspect these in priority order.

## Tier A

### A1. MathVision-Wildphoto / MathVision-WP

Hypothesis:

```text
harder photographic/degraded presentation
→ more extraction and wrong-source failures
```

Best target states:

```text
WRONG_SOURCE_READ
SOURCE_COUPLED_EXTRACTION_ERROR
PRIOR_FILL under degraded evidence
```

If exact clean↔wildphoto pairing exists, preserve it.

### A2. MathSight

Hypothesis:

```text
original / hand-drawn / photo / text-only variants
```

allow direct comparison of:

```text
visual evidence use
vs
language/text prior
```

Best target state:

```text
PRIOR_FILL / visual interference
```

Important:

```text
text-only success != PRIOR_FILL
```

unless visual demand is present and causal visual support is absent.

### A3. MMLongBench-Doc

Hypothesis:

```text
many similar pages/fields/rows
→ source confusion
```

Best target states:

```text
WRONG_SOURCE_READ
binding error
wrong field/page retrieval
```

Use only if page/field/ROI localization is sufficiently clean.

### A4. CharXiv reasoning subset / CharXiv-R

Hypothesis:

```text
multiple chart series / axes / legends / nearby values
→ source confusion
```

Best target states:

```text
WRONG_SOURCE_READ
binding error
SOURCE_COUPLED_EXTRACTION_ERROR
```

Use the official reasoning subset if naming differs.

---

## Tier B

Inspect only if Tier A is insufficient.

```text
VisualPuzzles
VisuLogic
HallusionBench
```

These may be failure-rich but source identity may be difficult to localize.

---

# 5. Dataset Discovery Policy

Before downloading anything, inspect:

```text
project-local datasets link, if present
/data/dataset
/home/hyunjin/.cache/huggingface/datasets
```

Also obey machine-local:

```text
ACCESS_POLICY.md
```

If the active machine policy exposes additional allowed dataset roots, include them.

Do not assume a dataset is absent after checking only one directory.

---

# 6. Required Dataset Inventory

Create:

```text
workspace/dataset_inventory.md
outputs/stage7a_bench/cohort/dataset_inventory.json
outputs/stage7a_bench/cohort/dataset_inventory.md
```

For each candidate record:

```text
canonical name
local alias
version/revision
available splits
row count
image/document count
annotation path
image path
source/ROI annotations available?
paired variants available?
license/readme available?
usable?
reason
```

Search common aliases and release naming differences.

---

# 7. Download Policy

If a Tier A dataset is missing:

1. download exactly one dataset at a time;
2. prefer official Hugging Face or official project release;
3. download only required split(s);
4. store raw assets under an allowed external dataset root;
5. do not write large raw datasets into Git;
6. do not modify global Python;
7. use the project `.venv`;
8. record source/revision/files/timestamps/checksums where practical.

Create:

```text
outputs/stage7a_bench/cohort/download_manifest.json
```

If authentication or access-policy issues block one dataset:

```text
record the blocker
skip only that dataset
continue with other authorized candidates
```

Do not silently substitute an unrelated benchmark.

---

# 8. Stage Structure

```text
Phase A — Dataset inventory and structural audit
Phase B — Native Qwen3-VL-4B-Thinking failure-yield screen
Phase C — Source-identifiability causal pilot
Phase D — Benchmark ranking and freeze
```

The stage selects exactly one primary benchmark family for the next full causal failure study.

---

# PHASE A — STRUCTURAL AUDIT

## 9. Audit Sample

Before large model execution, freeze:

```text
64 examples per Tier A benchmark
```

Inspect without model outputs:

```text
task/question
image/document structure
ground-truth answer
candidate demanded source
plausible alternative sources
source annotations
ROI localization
counterfactual editability
local evidence readout feasibility
```

---

## 10. Source-Identifiability Score

Assign each example:

```text
S0 — source not localizable
S1 — coarse source only
S2 — localizable target but weak alternative identity
S3 — target + plausible alternatives localizable
S4 — target + alternatives independently editable
```

Desired benchmark yield:

```text
>= 40% S3/S4
```

Preferred:

```text
>= 60% S3/S4
```

---

## 11. Readout Feasibility

Assign:

```text
R0 — no clean local readout
R1 — final-answer only
R2 — value readout
R3 — binding/source readout
R4 — value + binding + error-oriented readout
```

Preferred:

```text
>= 40% R3/R4
```

---

## 12. Structural Stop Rule

Do not run a large native sweep if:

```text
S3/S4 < 20%
and
R3/R4 < 20%
```

unless the benchmark has a unique paired property such as:

```text
clean↔wildphoto
image↔text-only
```

Record such a benchmark as:

```text
error-relevant but causally under-identifiable
```

---

# PHASE B — NATIVE 4B-THINKING SCREEN

## 13. Model

Keep the primary model fixed:

```text
Qwen3-VL-4B-Thinking
```

Do not run 2B yet.

Use the established Qwen3-VL Thinking generation protocol.

Do not alter decoding merely to increase failures.

---

## 14. Sample Size

For each structurally eligible Tier A benchmark:

```text
initial = 200 examples
```

Prospective extension:

```text
up to 400
```

only if the first 200 show promising but uncertain failure yield.

Freeze IDs before generation.

---

## 15. Native Labels

Record separately:

```text
final correctness
local visual claim correctness
visual claim present?
source-binding claim present?
abstention/caveat
completion/truncation
```

Do not treat final-answer wrongness as a grounding label.

---

## 16. Semantic Failure Candidates

Before causal scoring assign:

```text
F0 — locally correct visual read
F1 — wrong visual value
F2 — wrong source/entity binding
F3 — unsupported visual claim
F4 — correct local visual read followed by later error
F5 — explicit uncertainty / abstention
F6 — no local visual claim
```

These are screening labels only.

---

## 17. Native Yield Metrics

Report per benchmark:

```text
final accuracy
local visual-claim error rate
binding-error candidate rate
unsupported-claim candidate rate
integration-error candidate rate
abstention rate
truncation rate
eligible causal events per 100 examples
```

The last metric is more important than raw accuracy.

---

## 18. Desired Difficulty Regime

Preferred:

```text
final accuracy roughly 25%–75%
```

or more importantly:

```text
>= 15% local visual/source error candidates
>= 25% clean faithful-control candidates
```

These are screening heuristics, not paper claims.

---

# PHASE C — CAUSAL PILOT

## 19. Purpose

A benchmark can be error-rich but mechanistically opaque.

The causal pilot asks whether its native failures actually map to Stage 7A grounding states.

---

## 20. Pilot Subset

Per promising benchmark freeze:

```text
32 failure-candidate events
32 faithful-control events
```

Minimum:

```text
16 + 16
```

If fewer failures exist, use all eligible failures.

Selection may use semantic/native error status but not attention or causal effects.

---

## 21. Exact Causal Assays

Reuse Stage 7A definitions.

Primary:

```text
W2 all-layer/all-head source suppression
```

Sensitivity:

```text
W8 on target and primary alternative
```

Where feasible:

```text
target semantic counterfactual
alternative semantic counterfactual
matched sham
error-oriented wrong-token readout
```

For text-only / image-variant benchmarks, use native paired conditions where scientifically valid.

---

## 22. Pilot State Labels

Assign only under the existing Stage 7A criteria:

```text
FAITHFUL_READ
PRIOR_FILL
WRONG_SOURCE_READ
STALE_SOURCE_READ
SOURCE_COUPLED_EXTRACTION_ERROR
DOWNSTREAM_INTEGRATION_ERROR
SOURCE_ANOMALY
UNRESOLVED
```

Do not weaken definitions to increase yield.

---

## 23. Wrong-Source Requirement

Strict WRONG_SOURCE_READ requires:

```text
Demand = T
wrong emitted evidence for T
alternative X causally supports wrong evidence
X suppression reduces wrong-token/wrong-claim preference
X semantic edit moves wrong evidence in the X-consistent direction
```

Alternative dominance without error-oriented support remains:

```text
SOURCE_ANOMALY
```

---

## 24. Prior-Fill Requirement

Strict PRIOR_FILL requires:

```text
visual demand is present
valid visual support is weak/unavailable
no visual source semantically controls the claim
behavior moves toward text-only/no-image prior
```

Text-only success alone is not PRIOR_FILL.

---

## 25. Efficiency Metrics

For each benchmark report:

```text
strong unfaithful states per 100 native examples
strong unfaithful states per 32 causal-scored failures
causal-identifiable events per GPU-hour
```

This prevents selecting an error-rich but causally opaque benchmark.

---

# PHASE D — BENCHMARK RANKING

## 26. Ranking Dimensions

Report raw dimensions:

```text
A. native failure yield
B. source identifiability
C. binding-readout availability
D. counterfactual editability
E. faithful-control yield
F. strong causal unfaithful-state yield
G. dataset/template diversity
H. GPU/annotation cost
I. paired clean/stress or image/text advantage
```

Do not choose by benchmark accuracy alone.

---

## 27. Primary Benchmark Gate

A benchmark is a strong next-stage candidate if it plausibly supports:

```text
>= 24 strong unfaithful events at feasible scale
>= 24 faithful controls
substantial S3/S4 yield
error-oriented readouts
counterfactual source edits
no severe floor/ceiling
no single-template domination
```

Projection must come from the frozen native + causal pilot yield.

Avoid extrapolation from fewer than 8 strong failures.

---

## 28. Role-Specific Winners Are Allowed

Different benchmarks may be best for different states:

```text
MathSight
→ PRIOR_FILL / language-prior regime

MathVision-WP
→ degraded extraction / source confusion

MMLongBench-Doc
→ wrong field / wrong-source binding

CharXiv-R
→ wrong series / legend / axis
```

Still select exactly one primary next-stage benchmark family.

Reserve others for later replication.

---

# 29. Paired Benchmark Opportunities

## MathVision clean ↔ wildphoto

If exact pair mapping exists, freeze:

```text
same problem
same reasoning demand
different visual presentation
```

Later compare:

```text
faithful → unfaithful transition
source identity changes
extraction-error increase
```

Do not assume every wildphoto error is perceptual.

## MathSight image variants ↔ text-only

If paired variants exist:

```text
original
hand-drawn
photo
text-only
```

analyze:

```text
visual benefit
visual interference
language-prior solvability
```

Again, text-only correctness is not automatically prior-fill.

---

# 30. Model-Scale Boundary

Do not run Qwen3-VL-2B-Thinking yet.

At stage end, assess whether the selected benchmark is suitable for:

```text
2B vs 4B
```

or:

```text
2B vs 4B vs 8B
```

Only recommend scale comparison if benchmark source structure is already validated.

Do not use a weaker model merely to manufacture errors before benchmark validation.

---

# 31. What the Selected Benchmark Should Let Us Ask

At least one of:

```text
Q1. Does the model satisfy a visual demand using a wrong causal source?
Q2. Does missing/weak visual evidence get filled by language prior?
Q3. Does the model select the correct source but extract it incorrectly?
Q4. Does grounding remain faithful while downstream reasoning fails?
```

The goal is not just more wrong answers.

---

# 32. Preferred Natural→Controlled Flow

If natural wrongful reads are found:

```text
natural discovery
→ controlled causal reproduction
```

Example:

```text
natural wrong field in MMLongBench
→ matched T/X field perturbation
→ source-specific confirmation
```

This is stronger than natural correlation or synthetic stress alone.

---

# 33. Paper-Level Interpretation

A successful sweep strengthens the paper arc:

```text
Reasoning creates visual retrieval demand
        ↓
Demand is usually satisfied by the correct source
        ↓
Hard/source-confusable regimes expose failures
        ↓
The same demand may be satisfied by:
  correct source
  wrong source
  insufficient visual support
        ↓
Source-faithfulness can be monitored and corrected
```

---

# 34. Output Structure

```text
outputs/stage7a_bench/
  config/
    benchmark_candidates.json
    benchmark_priority.json
    structural_audit_rules.json
    native_screen_rules.json
    causal_pilot_rules.json
    ranking_rules.json

  cohort/
    dataset_inventory.json
    dataset_inventory.md
    download_manifest.json
    sample_freeze.json
    benchmark_manifests/
    exclusions.jsonl
    screening_accounting.json

  structural_audit/
    source_identifiability.jsonl
    readout_feasibility.jsonl
    paired_variant_mapping.jsonl
    benchmark_structural_summary.json

  native_screen/
    generations/
    native_labels.jsonl
    local_claims.jsonl
    failure_candidates.jsonl
    faithful_candidates.jsonl
    benchmark_yield.json

  causal_pilot/
    pilot_manifest.jsonl
    source_roles.jsonl
    readouts.jsonl
    w2_scores.jsonl
    w8_scores.jsonl
    error_oriented_scores.jsonl
    target_counterfactuals.jsonl
    alternative_counterfactuals.jsonl
    state_labels.jsonl
    pilot_yield.json

  analysis/
    benchmark_comparison.json
    efficiency.json
    failure_state_yield.json
    source_identifiability_comparison.json
    paper_value_assessment.json
    selected_benchmark.json
    figures/

  audit/
    dataset_integrity.json
    split_integrity.json
    deterministic_generation.json
    source_mapping_audit.json
    readout_orientation_audit.json
    canonical_path_audit.json
    resource_summary.json

  summaries/
    stage7a_bench_summary.md
    stage7a_bench_acceptance.json
    next_stage_recommendation.md
```

---

# 35. Required Figures

At minimum:

1. benchmark candidate map;
2. server dataset availability;
3. source-identifiability by benchmark;
4. readout feasibility;
5. native final accuracy;
6. local visual-error yield;
7. binding-error candidate yield;
8. faithful-control yield;
9. causal-pilot state counts;
10. strong unfaithful states per 100 examples;
11. wrong-source yield;
12. prior-fill yield;
13. extraction/integration error yield;
14. causal-identifiable events per GPU-hour;
15. raw score vs causal failure yield;
16. source-identifiability vs failure yield;
17. paired clean/stress transitions where available;
18. selected benchmark decision table;
19. representative faithful vs wrongful-read examples;
20. final roadmap:
    ```text
    benchmark selection
      → full causal failure cohort
      → online monitor
      → grounding-aware intervention
    ```

---

# 36. Technical Acceptance Criteria

Stage 7A-Bench passes technically if:

1. allowed dataset roots are checked before downloading;
2. dataset inventory is written first;
3. missing datasets are downloaded one at a time;
4. download provenance is recorded;
5. primary model stays Qwen3-VL-4B-Thinking;
6. sample IDs freeze before generation;
7. structural audit is model-output blind;
8. native correctness is not used as a causal grounding label;
9. local visual/source errors are separate from final errors;
10. causal pilot subset freezes before scoring;
11. Stage 7A state definitions remain unchanged;
12. wrong-source requires error-oriented support;
13. prior-fill is not defined by no-image/text-only agreement alone;
14. source-identifiability/readout feasibility are explicit;
15. raw accuracy is not the sole ranking criterion;
16. no 2B/8B study runs;
17. no monitor is trained;
18. no rollback/decoding intervention runs;
19. benchmark sample size is not extended post hoc to chase positive causal effects;
20. exactly one primary next-stage benchmark recommendation is produced.

---

# 37. Scientific Outcome Map

## O1 — Natural failure-rich benchmark found

Outcome:

```text
enough faithful reads
+
enough causally identifiable unfaithful reads
```

Recommendation:

> GO — Full causal failure cohort on selected benchmark.

## O2 — Error-rich but causally opaque

Recommendation:

```text
do not select for source-faithfulness mechanistic work
```

## O3 — Mechanistically clean but too easy

Recommendation:

```text
reserve for model-scale comparison or controlled stress
```

## O4 — Paired benchmark is best

Recommendation:

> GO — Paired natural/stress causal study.

## O5 — No existing benchmark passes

Recommendation:

```text
report sweep
then decide whether controlled confusable-source construction is more defensible
```

Do not immediately weaken the model merely to get more errors.

---

# 38. Next-Stage Decision

Produce exactly one recommendation.

Possible outcomes:

```text
GO — Full Causal Failure Cohort
GO — Paired Natural/Stress Causal Study
GO — Model-Scale Failure Amplification
GO — Controlled Confusable-Source Construction
```

Model-scale failure amplification is only allowed if benchmark source structure is already excellent but 4B is too accurate.

---

# 39. Stop Condition

After:

```text
dataset inventory
→ download missing Tier A datasets if needed
→ structural audits
→ native 4B screens
→ causal pilots on promising benchmarks
→ benchmark ranking
→ select exactly one primary benchmark family
→ paper-value assessment
→ exactly one next-stage recommendation
```

STOP.

Do not automatically start:

```text
2B evaluation
full benchmark expansion
monitor training
grounding-aware decoding
rollback
```

---

# 40. Final Research Principle

Do not ask:

```text
Which benchmark makes the model look worst?
```

Ask:

\[
oxed{
	ext{Which benchmark makes source-faithfulness failures observable, causal, and correctable?}
\]

The best benchmark maximizes scientific identifiability, not error rate alone.
