# Stage 7A-Bench v2 — Benchmark Failure-Enrichment, Mirage/Prior Track, and Source-Faithfulness Sweep

## 0. Purpose

Stage 7A established that source-faithful visual reads can be causally certified, but strong unfaithful states were too rare for monitor/intervention work:

```text
FAITHFUL_READ                    181
PRIOR_FILL                         0
WRONG_SOURCE_READ                  3
STALE_SOURCE_READ                  0
SOURCE_COUPLED_EXTRACTION_ERROR    1
DOWNSTREAM_INTEGRATION_ERROR       2
```

The next step is to identify existing benchmarks where Qwen3-VL-4B-Thinking naturally produces enough unfaithful visual reads while the evidence remains localizable and causally testable.

This v2 plan adds a dedicated MIRAGE/prior-dependence benchmark track to the earlier source-confusion benchmark sweep.

The stage asks:

> Which benchmark makes source-faithfulness failures observable, causal, and eventually correctable?

---

# 1. Two Complementary Failure Tracks

## Track A — Source-confusion / wrongful-read

Primary targets:

```text
WRONG_SOURCE_READ
binding error
SOURCE_COUPLED_EXTRACTION_ERROR
stale/wrong field retrieval
```

Likely useful domains:

```text
charts
documents
wild-photo geometry
dense multi-source layouts
```

## Track B — Mirage / prior-filled-demand

Primary targets:

```text
PRIOR_FILL
unsatisfied retrieval demand
image-vs-no-image faithfulness
mirage-mode vs explicit-guess regime
language-prior visual evidence emission
```

These tracks must be analyzed separately before any pooled conclusion.

---

# 2. Primary Benchmark Candidates

## Track A

### A1. MathVision-Wildphoto / MathVision-WP

Hypothesis:

```text
harder photographic presentation
→ more extraction and source-confusion failures
```

Best target states:

```text
WRONG_SOURCE_READ
SOURCE_COUPLED_EXTRACTION_ERROR
PRIOR_FILL under degraded evidence
```

Preserve exact clean↔wildphoto pairing if available.

### A2. MMLongBench-Doc

Hypothesis:

```text
many pages / fields / rows / repeated labels
→ wrong field or wrong page retrieval
```

Best target states:

```text
WRONG_SOURCE_READ
binding error
stale/wrong field retrieval
```

Use only if source localization reaches at least page/field/table-region/header-value level.

### A3. CharXiv reasoning subset / CharXiv-R

Hypothesis:

```text
multiple chart series / legends / axes / nearby values
→ wrong-source visual reads
```

Best target states:

```text
WRONG_SOURCE_READ
binding error
SOURCE_COUPLED_EXTRACTION_ERROR
```

### A4. MathSight

Potential paired variants:

```text
original
hand-drawn
photo
text-only
```

Useful for both extraction/source-confusion and prior dependence.

---

## Track B

### B1. MMMU-Pro

Use as a bridge benchmark.

Desired conditions:

```text
image present
silent no-image / mirage mode
explicit no-image / guess mode
```

Best target states:

```text
PRIOR_FILL
faithful-vs-unfaithful correct answer
image-dependent vs text-solvable behavior
```

### B2. MMMU-Pro B-Clean-style subset

If an official or reproducible cleaning protocol is available, preserve its labels separately.

Also define a later causal analogue:

```text
CAUSAL_VISION_DEPENDENT
CAUSAL_NONVISUAL_CORRECT
UNRESOLVED
```

Do not equate behavioral no-image solvability with causal non-visuality.

### B3. Phantom-0

Use for:

```text
visual demand with no image available
```

Best target state:

```text
PRIOR_FILL / unsatisfied retrieval demand
```

Important limitation:

```text
no true target ROI exists
```

So Phantom-0 is not suitable by itself for WRONG_SOURCE_READ.

### B4. MicroVQA

Purpose:

```text
visual/medical questions with potentially strong textual priors
```

Best target:

```text
PRIOR_FILL
faithful-vs-unfaithful correct answers
```

### B5. MedXpertQA-MM

Purpose:

```text
multimodal medical reasoning under strong domain priors
```

Best target:

```text
PRIOR_FILL
source-faithfulness
```

### B6. VQA-RAD

Use for radiology VQA image/no-image faithfulness if source localization is adequate.

### B7. ReXVQA

Potentially useful for large-scale failure mining, especially:

```text
presence
location
negation
differential diagnosis
geometry
```

First audit whether source localization is possible.

---

## Reserve Candidates

Inspect only if the primary set is insufficient:

```text
VisualPuzzles
VisuLogic
HallusionBench
GQA
POPE
```

---

# 3. Dataset Discovery and Download Policy

Before downloading anything, inspect:

```text
1. project-local datasets link, if present
2. allowed dataset roots from ACCESS_POLICY.md
3. /data/dataset
4. /home/hyunjin/.cache/huggingface/datasets
```

Obey the active machine-local ACCESS_POLICY.md if it differs from the hard-coded examples above.

Create/update:

```text
workspace/dataset_inventory.md
outputs/stage7a_bench_v2/cohort/dataset_inventory.json
outputs/stage7a_bench_v2/cohort/dataset_inventory.md
```

For every benchmark record:

```text
canonical name
local alias
version/revision
split names
sample count
image/document count
local path
annotation path
image path
paired variants available?
source/ROI annotation available?
official evaluation metadata available?
license/readme available?
usable?
reason
```

Search aliases before declaring a dataset absent.

If missing:

1. download exactly one dataset at a time;
2. prefer official Hugging Face or official project release;
3. pin revision/version where possible;
4. download only required split(s);
5. use an allowed external dataset root;
6. do not modify global Python;
7. use the project `.venv`;
8. record provenance/checksums where practical.

Create:

```text
outputs/stage7a_bench_v2/cohort/download_manifest.json
```

---

# 4. Stage Architecture

```text
Phase A — Dataset inventory and structural audit
Phase B — Native 4B-Thinking screen
Phase C — Mirage/prior paired-condition screen
Phase D — Source-identifiability causal pilot
Phase E — Benchmark ranking and freeze
```

Exactly one primary benchmark family is selected at the end.

---

# PHASE A — STRUCTURAL AUDIT

## 5. Audit Sample

For each primary candidate, freeze 64 examples before model generation.

Audit:

```text
task/question
image/document structure
ground-truth answer
candidate demanded source
plausible alternative sources
source annotation availability
ROI localizability
binding readout feasibility
error-oriented readout feasibility
counterfactual editability
paired image/no-image or clean/stress availability
```

No model output is used in this structural audit.

---

## 6. Source-Identifiability Score

Assign:

```text
S0 — source not localizable
S1 — coarse source only
S2 — target localizable, alternatives weak
S3 — target + plausible alternatives localizable
S4 — target + alternatives independently editable
```

Preferred Track A benchmark:

```text
>= 40% S3/S4
```

Preferred:

```text
>= 60% S3/S4
```

Track B may pass with lower S3/S4 if its purpose is no-image/prior-fill identification.

---

## 7. Readout Feasibility

Assign:

```text
R0 — no clean local readout
R1 — final answer only
R2 — value readout
R3 — binding/source readout
R4 — value + binding + error-oriented readout
```

Track A preferred:

```text
>= 40% R3/R4
```

Track B may rely more on R2 plus paired image/no-image evidence if prior-fill remains identifiable.

---

## 8. Structural Stop Rules

For Track A, stop a benchmark before a large native sweep if:

```text
S3/S4 < 20%
and
R3/R4 < 20%
```

For Track B, stop only if both are true:

```text
no reliable visual-demand annotation
and
no paired image/no-image / text-only regime
```

Record such cases as:

```text
hard benchmark but causally under-identifiable
```

---

# PHASE B — NATIVE 4B-THINKING SCREEN

## 9. Primary Model

Use only:

```text
Qwen3-VL-4B-Thinking
```

in the primary sweep.

Do not run 2B/8B yet.

Use the frozen official-style generation protocol.

Do not alter decoding to create more failures.

---

## 10. Sample Size

For each structurally eligible benchmark:

```text
initial native screen = 200 examples
```

Optional extension:

```text
up to 400
```

only if the first 200 produce promising but uncertain failure yield.

Freeze IDs before generation.

---

## 11. Native Semantic Labels

Record separately:

```text
final correctness
local visual claim correctness
visual claim present?
binding/source claim present?
unsupported evidence claim?
correct local read followed by later error?
abstention / caveat?
truncation?
```

Do not infer grounding state from final accuracy.

---

## 12. Semantic Candidate Classes

Before causal scoring:

```text
F0 — locally correct visual read
F1 — wrong visual value
F2 — wrong source/entity binding
F3 — unsupported visual claim
F4 — correct local visual read followed by later error
F5 — uncertainty/abstention
F6 — no local visual claim
```

These are screening labels only.

---

## 13. Native Yield Metrics

Per benchmark report:

```text
final accuracy
local visual-error rate
binding-error candidate rate
unsupported-claim rate
integration-error candidate rate
faithful-control candidate rate
abstention rate
truncation rate
eligible causal events per 100 examples
```

---

# PHASE C — MIRAGE / PRIOR PAIRED-CONDITION SCREEN

## 14. Purpose

Track B benchmarks explicitly test whether a visual evidence claim persists when valid visual evidence is unavailable.

Paired conditions may include:

```text
image-present
silent no-image / mirage mode
explicit no-image / guess mode
text-only
vision-essential filtered subset
```

Use only conditions supported by the benchmark/task.

---

## 15. Mirage-Mode vs Guess-Mode

Where feasible:

### Mirage mode

```text
visual task is presented
image is absent
model is not explicitly told that visual evidence is absent
```

### Guess mode

```text
image is absent
model is explicitly told no image is available
```

Compare:

```text
visual claim rate
abstention/caveat rate
candidate evidence identity
output confidence
```

This is a behavioral comparison until causal source labels are available.

---

## 16. Behavioral B-Clean vs Causal B-Clean

Where a behavioral cleaning protocol exists, preserve it separately.

Do not treat:

```text
image-absent correct
```

as identical to:

```text
causally nonvisual
```

After causal scoring, define:

```text
CAUSAL_VISION_DEPENDENT
CAUSAL_NONVISUAL_CORRECT
UNRESOLVED
```

A particularly interesting secondary finding would be:

> Some items are answered correctly with images present but without causal support from the visual evidence.

---

## 17. Track-B Prior-Fill Candidate

A strong prior-fill candidate requires:

```text
visual retrieval demand present
specific visual evidence emitted
valid visual support absent/insufficient
claim persists across no-image/text-only regime
```

Final causal certification still requires the Stage 7A source criteria where a visual condition exists.

Phantom-style no-image-only tasks can identify strong behavioral candidates but not source-null causality by themselves.

---

# PHASE D — CAUSAL PILOT

## 18. Pilot Entry Gate

A benchmark enters causal pilot if it has at least one of:

```text
>= 16 local source/binding error candidates
>= 16 unsupported/prior-fill candidates
>= 16 paired faithful-vs-no-image disagreement candidates
>= 16 strong faithful controls
```

and passes the structural-identifiability requirement for the relevant failure class.

---

## 19. Pilot Subset

Per promising benchmark:

```text
32 failure candidates
32 faithful controls
```

Minimum:

```text
16 + 16
```

If fewer failure candidates exist, use all.

Freeze before causal scoring.

---

## 20. Exact Causal Assays

Reuse Stage 7A definitions.

Primary:

```text
W2 all-layer/all-head source suppression
```

Sensitivity:

```text
W8 target / primary alternative
```

Where feasible:

```text
target semantic counterfactual
alternative semantic counterfactual
matched sham
error-oriented wrong-token readout
```

Track-B image-present/no-image/text-only conditions are behavioral/context conditions, not replacements for source suppression.

---

## 21. Causal State Labels

Use unchanged Stage 7A definitions:

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

Do not relax definitions to increase yield.

---

## 22. WRONG_SOURCE_READ Gate

Require:

```text
Demand = T
wrong emitted evidence for T
alternative X causally supports wrong evidence
X suppression lowers wrong-token/wrong-claim preference
X semantic edit moves wrong evidence
```

Alternative dominance without error-oriented support remains SOURCE_ANOMALY.

---

## 23. PRIOR_FILL Gate

Require:

```text
visual demand present
visual evidence unavailable/insufficient
no tested visual source semantically controls the claim
behavior resembles no-image/text-only prior
```

No-image similarity alone is insufficient.

---

## 24. Extraction vs Integration

Keep separate:

```text
correct source + wrong local evidence
→ SOURCE_COUPLED_EXTRACTION_ERROR

correct source + correct local evidence + later error
→ DOWNSTREAM_INTEGRATION_ERROR
```

---

## 25. Pilot Efficiency Metrics

Per benchmark:

```text
strong unfaithful states per 100 native examples
strong unfaithful states per 32 causal failure candidates
faithful controls per 100 examples
causal-identifiable events per GPU-hour
annotation minutes per strong failure
```

---

# PHASE E — BENCHMARK RANKING

## 26. Ranking Dimensions

Report raw dimensions:

```text
A. native failure yield
B. source identifiability
C. error-oriented readout availability
D. counterfactual editability
E. faithful-control yield
F. strong causal unfaithful-state yield
G. paired image/no-image or clean/stress advantage
H. dataset/template diversity
I. annotation cost
J. GPU cost
```

Do not rank by accuracy alone.

---

## 27. Track-Specific Ranking

Produce:

```text
Track A ranking — wrong-source/source-confusion
Track B ranking — prior-fill/mirage
```

Then select one primary next-stage benchmark family based on paper value.

Track A and Track B winners may differ.

---

## 28. Expected Benchmark Roles

```text
MMMU-Pro
→ bridge benchmark for image-present vs no-image faithfulness

Phantom-0
→ unsatisfied-demand / prior-fill stress

MathSight
→ visual-vs-text prior and visual interference

MathVision-WP
→ degraded visual extraction / source confusion

MMLongBench-Doc
→ wrong field / wrong page / wrong-source binding

CharXiv-R
→ wrong series / axis / legend source

MicroVQA / MedXpertQA-MM / VQA-RAD
→ medical prior-fill / source-faithfulness

ReXVQA
→ large-scale failure mining if source localization is adequate
```

---

## 29. Primary Benchmark Gate

A benchmark is a strong next-stage candidate if it plausibly supports:

```text
>= 24 strong unfaithful events at feasible scale
>= 24 faithful controls
clean readout orientation
sufficient source identifiability for the target state
counterfactual or paired-condition controls
no catastrophic floor effect
```

For Track B no-image-only benchmarks, source-identifiability may be replaced by:

```text
clean visual-demand semantics
+
paired/controlled evidence-availability condition
```

but such a benchmark is mainly for PRIOR_FILL, not WRONG_SOURCE_READ.

---

# 30. Model-Scale Boundary

Do not run Qwen3-VL-2B-Thinking or 8B in this stage.

At the end, assess whether the winning benchmark is suitable for a later:

```text
2B vs 4B
```

or:

```text
2B vs 4B vs 8B
```

study.

A scale study is justified only after benchmark source structure is validated.

---

# 31. Preferred Natural→Controlled Follow-Up

If a natural benchmark yields wrongful reads:

```text
natural discovery
→ controlled source perturbation
→ causal reproduction
```

If a no-image benchmark yields prior-fill:

```text
behavioral mirage discovery
→ matched image-present source-faithfulness test
```

This natural→controlled sequence is preferred over synthetic stress alone.

---

# 32. Paper-Level Flow

A successful sweep should support:

```text
Reasoning creates visual retrieval demand
        ↓
Demand is usually faithfully satisfied
        ↓
Hard/source-confusable or image-absent regimes expose failures
        ↓
The demanded evidence slot can be filled by:
  correct visual source
  wrong visual source
  language/reasoning prior
        ↓
These states can be causally distinguished
        ↓
They become candidates for monitoring and intervention
```

---

# 33. Output Structure

```text
outputs/stage7a_bench_v2/
  config/
    benchmark_candidates.json
    track_a_candidates.json
    track_b_candidates.json
    benchmark_priority.json
    structural_audit_rules.json
    native_screen_rules.json
    paired_condition_rules.json
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
    visual_demand_feasibility.jsonl
    benchmark_structural_summary.json

  native_screen/
    generations/
    native_labels.jsonl
    local_claims.jsonl
    failure_candidates.jsonl
    faithful_candidates.jsonl
    benchmark_yield.json

  mirage_prior_track/
    paired_conditions.jsonl
    mirage_mode.jsonl
    guess_mode.jsonl
    text_only.jsonl
    behavioral_bclean.jsonl
    causal_bclean.jsonl
    prior_fill_candidates.jsonl

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
    track_a_ranking.json
    track_b_ranking.json
    benchmark_comparison.json
    efficiency.json
    failure_state_yield.json
    source_identifiability_comparison.json
    bclean_comparison.json
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
    stage7a_bench_v2_summary.md
    stage7a_bench_v2_acceptance.json
    next_stage_recommendation.md
```

---

# 34. Required Figures

At minimum:

1. Track A / Track B benchmark map;
2. server dataset availability;
3. structural-identifiability matrix;
4. source-identifiability distribution;
5. readout-feasibility distribution;
6. native accuracy by benchmark;
7. local visual/source-error yield;
8. unsupported visual-claim yield;
9. faithful-control yield;
10. image-present vs no-image behavior;
11. mirage-mode vs guess-mode behavior;
12. Behavioral B-Clean vs Causal B-Clean;
13. causal-pilot state counts;
14. strong unfaithful states per 100 examples;
15. wrong-source yield;
16. prior-fill yield;
17. extraction/integration error yield;
18. causal-identifiable events per GPU-hour;
19. raw accuracy vs causal failure yield;
20. source-identifiability vs failure yield;
21. paired clean/stress transitions;
22. selected benchmark decision table;
23. faithful vs wrongful-read examples;
24. image-present vs prior-filled examples;
25. roadmap to monitor/intervention.

---

# 35. Technical Acceptance Criteria

Stage 7A-Bench v2 passes technically if:

1. access policy is read before dataset operations;
2. allowed dataset roots are checked before download;
3. dataset inventory is written before downloads;
4. missing datasets are downloaded one at a time;
5. download provenance is recorded;
6. primary model remains Qwen3-VL-4B-Thinking;
7. sample IDs freeze before generation;
8. structural audit is model-output blind;
9. native correctness is not used as a causal grounding label;
10. local visual/source errors remain separate from final errors;
11. paired image/no-image conditions are not themselves causal labels;
12. Behavioral B-Clean is not equated with Causal B-Clean;
13. causal pilot subset freezes before scoring;
14. Stage 7A state definitions remain unchanged;
15. WRONG_SOURCE_READ requires error-oriented support;
16. PRIOR_FILL is not defined by no-image/text-only agreement alone;
17. source-identifiability/readout feasibility are explicit ranking dimensions;
18. raw benchmark accuracy is not the sole ranking criterion;
19. no 2B/8B study runs;
20. no online monitor is trained;
21. no rollback/decoding intervention runs;
22. sample size is not extended merely to chase positive causal-state counts after pilot effects are seen;
23. exactly one primary next-stage benchmark recommendation is produced.

---

# 36. Scientific Outcome Map

## O1 — Track A winner found

Recommendation:

```text
GO — Full Source-Confusion Causal Cohort
```

## O2 — Track B winner found

Recommendation:

```text
GO — Full Unsatisfied-Retrieval / Prior-Fill Cohort
```

## O3 — Paired benchmark dominates

Recommendation:

```text
GO — Paired Natural/Stress Causal Study
```

## O4 — Error-rich but causally opaque

Do not select it for source-faithfulness mechanistic work.

## O5 — Mechanistically clean but too easy

Reserve for later model-scale comparison.

## O6 — No benchmark passes

Report the sweep, then consider:

```text
Controlled Confusable-Source Construction
```

rather than immediately weakening the model.

---

# 37. Stop Condition

After:

```text
dataset inventory
→ download missing primary candidates if needed
→ structural audits
→ native 4B screens
→ Track-B paired image/no-image screen
→ causal pilots
→ Track A / Track B ranking
→ select exactly one primary benchmark family
→ paper-value assessment
→ exactly one next-stage recommendation
```

STOP.

Do not automatically start:

```text
2B evaluation
full causal expansion
monitor training
grounding-aware decoding
rollback
```

---

# 38. Final Research Principle

Do not ask only:

```text
Which benchmark makes the model fail most?
```

Ask:

```text
Which benchmark makes the source of visual evidence failure identifiable?
```

Track A seeks:

```text
Demand = T
but Source = X
```

Track B seeks:

```text
Demand = T
but no valid visual source supplies E
```

The selected benchmark should maximize the path:

```text
failure
→ causal diagnosis
→ online detection
→ intervention
```
