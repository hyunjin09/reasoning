> Completion update,2026-10-22: authorized fixed72×6 SAVA pilot and analysis COMPLETE. [Final report](../outputs/stage14d1_sava_pilot/v1/reports/feasibility_main_v8.md). PrimaryQI−N−4.17pp,95%CI[−12.50,+4.17];no demonstrated accuracy gain. All GPUs released. One recommendation recorded; no follow-on launched. Earlier plan/status text below remains historical.

> Current execution outcome,2026-10-19: bounded technical attempt stopped at failed exact replay (6/8). The72-family pilot was not run. [Full report](../outputs/stage14d1_sava/reports/feasibility_main.md) preserves failures, amendments and resource accounting; no scientific efficacy conclusion.

> Execution update, 2026-10-19: the current user explicitly delegates plan amendments and execution without further permission requests. [Prospective amendment v2](stage14d1_sava_execution_amendment_v2.md) and the frozen SAVA runtime specification govern the bounded execution. The original design-only v1 below is preserved verbatim in `outputs/stage14d1_sava/provenance/original_plan_v1.md`. This does not release the old Stage14D main grid or mark Stage14C-V closed.

# Stage 14D-1 — SAVA: Subgoal-Addressed Visual Acquisition

**Research plan / agent-executable protocol (v1)**  
**Prepared:** 2026-10-19  
**Status:** DESIGN ONLY. No scientific inference, checkpoint modifications, training, or GPU jobs are authorized by this document.  
**Primary system:** pinned Qwen3-VL-4B-Thinking; Qwen3-VL-4B-Instruct is a later within-checkpoint replication, not a causal Thinking toggle.  
**Primary task:** MATH-Vision, particularly visual math items whose required evidence depends on global configuration, entity/coordinate binding, or spatial relationships.

> **Core question:** Can a reasoning VLM acquire task-critical visual evidence more accurately by turning its **current reasoning subgoal** into an explicit, source-addressed visual query, while **preserving the global image context**, and thereby improve final math accuracy?

## 0. Executive summary

Develop **SAVA — Subgoal-Addressed Visual Acquisition**, initially as a *training-free, controlled decoding-time intervention*. When the model needs a new visual fact, it produces a **value-free visual query** specifying which entity, property, and spatial reference frame it needs. It then performs a targeted visual read from the original image, with a global view maintained and an optional anchored local view. The resulting visual fact is supplied to the same solver for continued reasoning. **We are improving visual evidence acquisition—not constructing a general downstream proof checker or trying to solve every reasoning failure.**

**Development sequence:**

1. **Stage 14D-1a — What-to-look-for test:** Does a subgoal-specific visual query improve evidence readout and downstream accuracy relative to generic lookback and matched text-only querying?
2. **Stage 14D-1b — How-to-look test:** Holding the query fixed, does global-context-preserving, source-anchored presentation outperform a plain full-image read or local-only crop?
3. **Stage 14E — When-to-look policy (later):** Only if 14D-1 gives a positive, interpretable signal, automate premise checkpoints during open-ended decoding. Do not conflate 14D-1 feasibility with a fully validated online controller.

**Prior old run:** The 1,674 sealed continuations / proposed 375 GPU-hour Stage14D main run remain **HOLD**. Do not reuse its budget or execute its exhaustive grid. The unfinished Stage14C-V closure prerequisite is **not waived**.

## 1. Scientific motivation and claim boundaries

### Locked paper structure

- **C1 — Functional evidence handoff:** Some successful visual reasoning trajectories move from image-dependent evidence resolution to text-prefix-sufficient continuation. This is **not** a universal two-stage schedule, proof of unique textual storage, or evidence that every later image read is unnecessary.
- **C2 — Evidence-supply-responsive bottleneck:** In Stage14B MATH-Vision, textual source-selected `E*` rescued **234/418 = 55.98%** of scored Instruct-native-wrong cases in the eligible cohort; the Instruct net evidence-supply benefit was **+21.99 pp**. Equal textual evidence still left a Thinking–Instruct paired gap **+14.69 pp**. `E*` changes image access, formatting, representation, and binding, so these numbers **cannot be presented as the fraction of pure acquisition failures** or as attainable SAVA gains.
- **C3 — Visual evidence acquisition methodology (proposed):** Identify and recover missing/uncertain task-critical visual evidence during reasoning; test whether the deployed method increases task accuracy. No method benefit or visual acquisition mediation has yet been established.

### What Stage14D-0 actually adds

The retrospective R-panel difficulty audit source-reviewed **150 families** with **979 acquisition-eligible subfacts** (522 directly visual, 457 visual computations). Global-required source facts had higher *explicitly wrong/misbound output* rates than local-sufficient facts:

| Evidence context | Instruct family-weighted explicit-error rate | Thinking family-weighted explicit-error rate |
|---|---:|---:|
| Local sufficient | 10.94% | 4.16% |
| Global required | 23.27% | 18.88% |
| Difference | +12.33 pp (95% CI +2.49, +21.99) | +14.72 pp (+7.94, +21.76) |

**Interpretation limits:** single AI reviewer; source-selected `E*`-eligible frame rather than all MathVision; source features correlated; last-recorded text claims are not latent acquisitions; no actual crop/lookback treatment tested. Operation-depth and small-text hypotheses were **not established** (small text was not estimable in this frame). Avoid claiming global context *causes* the errors.

The existing **A→B→A** counterfactual work shows reasoning demand can redirect *causal use of visual source* in its tested setting. It does **not** prove SAVA can select correct targets in native MathVision. The two propositions to test are therefore separate: (i) *choose a correct visual target*, and (ii) *read that target accurately*.

### Relevant baselines / novelty gate

- **When to Think and When to Look:** uncertainty-triggered lookback; source-directed acquisition must be distinguished from a generic “look again” trigger.
- **Does Reasoning Improve Seeing?:** reasoning/perception signals and internal interventions; SAVA does not infer direct perception improvements merely from final accuracy.
- **ReGround:** self-diagnosis and image re-injection.
- **DeepEyes / V* / Visual CoT:** active selection, crop/zoom, ROI-aware visual search.
- **Active-Look:** global/highlight plus local-detail methods. **Global+local views alone are not a novelty claim.**
- **PEARL / Perceval:** perception checklist or process-level visual verification. A static evidence list or generic verification call alone is insufficient novelty.

**Candidate contribution to test:** a *dynamic reasoning-subgoal → value-free, semantically source-addressed visual query → context-preserving visual readout* interface. Confirm incremental benefits of (a) query construction and (b) source-anchored presentation separately. A novelty claim is conditional on the experiments and a final up-to-date related-work check.

## 2. Proposed method and implementation contract

### 2.1 Visual query object — `q_t`

For a current reasoning state `s_t` / active subgoal `g_t`, generate exactly one *next needed* query, or `NONE` if no new image fact is needed:

```json
{
  "subgoal": "Determine the color of the cell needed by the next pattern step",
  "entity": "cell",
  "entity_id": "row 3, column 4",
  "predicate": "color",
  "spatial_reference": "full grid; row 1 at top, column 1 at left",
  "query": "What is the color of the cell at row 3, column 4?",
  "answer_value": null
}
```

- Query specifies **entity, predicate, spatial reference, and relation**, but never contains the target value (`black`, `AB=3`, `90°`) obtained from oracle `E*`.
- Coordinate indices that identify the target are allowed; an answer value is forbidden. Record provenance of any number in the query so coordinates and evidence values are not confused.
- Keep a `NONE / no-demand` option. Do **not** force a visual lookback for every instance.
- The model must derive `q_t` from the question and **currently generated** reasoning state, not from `E*`, the benchmark answer, archived wrong/correct status, or retrospective error annotations.
- Record the generated `q_t` and whether it was *source-valid*, *task-relevant*, *underspecified*, *wrong target*, or *unresolvable*; assess this **after** outputs are sealed against the original source. Do not silently repair a bad query in the deployable condition.

### 2.2 `LOCATE` and `READ` are distinct

`LOCATE(I, q_t)` identifies a source address in the **full image**: one ROI, multiple named elements, or a global structural reference. `READ(I, q_t, address)` extracts a minimal visual fact from that source.

- **Global view:** original whole image, possibly with a non-semantic marker/outline identifying the **predicted** source location. Preserve all grid axes, relevant labels, vertices, row/column frame, and global geometry.
- **Local view:** crop/zoom **only when a coherent local ROI exists**. For a cross-figure relation, provide multiple referenced regions or global-only evidence rather than fabricating a misleading single crop.
- **Answer-neutral rendering:** markers, boxes and overlays must not reveal a ground-truth value or hand-coded relation; preserve image readability.
- **Localization provenance:** log the method, predicted box(es), coordinate transformation into the model's image-preprocessing frame, and the number of extra model calls. A human/source-guided box is a **diagnostic oracle-address condition**, not the deployable method.
- **Evidence output:** a compact `{target, read_value, supporting_source, uncertainty}` record. Treat `uncertain` as a valid output rather than forcing guessing. Source readout may be incorrect; do not call it verified without an independent source check.

### 2.3 Decoder integration — progressive implementation

**V0 (14D-1, feasibility):** Generate or select a **single reproducible subgoal checkpoint** and freeze the same image-conditioned prefix for all intervention arms. Run the acquisition call, then resume the **same pinned Thinking solver** with the recovered evidence. This is *interrupted/restarted inference*, not an unchanged continuous decoder. Explicitly document any text reconstruction or cache resetting.

**V1 (14E, contingent):** Add an online visual-premise checkpoint controller with at most `K` queries, no target/answer oracle, and cost-aware fallback; implement only after V0 shows evidence and/or net-answer improvement. The ability to detect every first-use premise is not established by 14D-0, which lacks exhaustive first-use timestamps.

**Out of scope for first pilot:** RL training, rewriting the math solver, universal reasoning verification, using hidden ground-truth `E*` at inference, or decoder-head steering. Independent reading branches may be tested later if prior-text anchoring is demonstrably problematic.

## 3. Hypotheses and falsifiers

- **H1 — Query benefit:** Holding the solver, prefix, image and budget policy fixed, an explicit subgoal-specific query improves target-fact readout versus generic relook and a matched extra-text control.
- **H2 — Context benefit:** Given the *same query*, anchored global-context + local detail improves evidence readout relative to an unanchored full image or crop-only view, especially for pre-labeled global-required facts. **This is not assumed to hold.**
- **H3 — Downstream utility:** Evidence improvements translate into positive **net** final-answer changes, not merely more visual facts being written down.
- **H4 — Target-generation bottleneck (diagnostic):** With an independently supplied *target identity only* (never the correct value), readout is more accurate than with model-generated target identity. This bounds the contribution of query selection; it is not deployable-performance evidence.

**Disconfirming outcomes:** query-only without image re-injection improves just as much; no gain against generic relook; source-anchored images do no better or harm global tasks; target queries routinely select irrelevant entities; evidence correctness rises without net accuracy; repeated reading causes regressions/cost explosion. Report these without post-hoc moving the goalposts.

## 4. Sampling, leakage protection and phases

### 4.1 Development cohort (NOT confirmatory)

Plan a **72-family** bounded pilot from the already analyzed **R=150** source-selected families, aiming to include roughly **36 global-required, 18 local-sufficient, 18 local+global** target opportunities across **72 distinct families**, when feasible. Treat these as **source-feature-stratified target opportunities**, not necessarily mutually exclusive family classes. If quotas are infeasible, document achievable counts **before inference** rather than silently replacing families. Only **one primary target subfact per family** in V0. Select with a fixed recorded seed and source features, **not** by answer outcome, intervention responsiveness, or inspecting candidate outputs. Retain unscorable/wrong native outcomes rather than filtering for oracle rescue.

Use the existing 150 R families strictly for method **development**. The F=150 cohort is outcome-enriched and can support qualitative diagnostics but **must not** be pooled into representative performance rates. The original 14D-0 retrospective sample and facts are not an untouched test set.

### 4.2 Pilot stages

| Phase | Work | Output / stop gate |
|---|---|---|
| P0 — CPU/source preflight | Discover actual repository paths, pinned configs, manifests, source frame, image preprocessing and raw checkpoint conventions; freeze sampler and source-judgment protocol | Inventory + immutable hashes; no model call |
| P1 — technical smoke | **8–12 families**, validate replay parity, query schema, visual-address rendering, image/ROI coordinate transforms, scorer, and absence of hidden `E*` leakage | STOP if model/prefix parity, image provenance or source QA fails |
| P2 — 72-family discovery pilot | Frozen arms below; one target read per family with paired checkpoint | Accuracy, target-readout correctness, relook controls, costs, raw outputs |
| P3 — diagnostic extension (conditional) | At most **24 selected source opportunities**, compare *model-selected target* with **source-designated target identity only**, independently of answer value | Target-selection vs readout diagnostic; exploratory only |
| P4 — method selection | Lock one primary method and at most one alternate, based on development evidence and full controls | Frozen V1 spec + confirmatory cohort/compute proposal; no automatic scaling |

**Important:** P1–P3 involve scientific evaluated-model calls and need an explicit **new bounded GPU budget release** and satisfaction of the existing Stage14C-V closure gate (or a separately documented user waiver). Earlier instruction to proceed without further approval applied to the **CPU-only Stage14D-0 retrospective annotation**, not to this new GPU pilot. The present document is not that release.

### 4.3 Later held-out evaluation

After method choice, freeze a method-unseen evaluation cohort **before** running it—preferably **200–300 families from the remaining 700 `E*`-eligible families not in R/F**, with family/source strata, seeds, thresholds, and budgets fixed. They are *method-unseen*, **not** benchmark-unseen or Stage14B-outcome-unseen (Stage14B already measured them). Do not tune on the held-out results. A further full-MATH-Vision accuracy evaluation (3,040 problems) would assess generalization beyond the `E*`-eligible sample if compute and source handling permit.

## 5. Experimental arms and controlled comparisons

The *same pinned Thinking checkpoint* and pre-intervention prefix are mandatory across arms. Match generation recipe, response contract, number of read attempts, and use common seeds. Track all image/text tokens and actual GPU time. A small matched-budget sensitivity is required wherever extra image views cause substantial cost differences.

| Arm | Acquisition treatment at frozen checkpoint | Purpose |
|---|---|---|
| **N — Matched native** | Continue without special relook or evidence query | Answer-level baseline; does not force evidence verbalization |
| **G — Generic relook** | Neutral instruction to check original image again, plus the same image re-injection interface | Effect of extra vision exposure / generic reminder |
| **Q — Subgoal query; no *new* image** | Generate specific `q_t`, request its value without additional image re-injection | Effect of query text / prompting; original prefix may still encode the initial image, so **not truly vision-absent** |
| **QI — Subgoal query + full image** | Same `q_t`, freshly reinsert original unmodified image | **H1:** extra source access targeted by query |
| **QGL — Subgoal query + anchored global/local** | Same `q_t`, full image with model-predicted source marker + local view if valid | **H2:** source location/context presentation |

**Optional tightly bounded ablations (only if feasible within separately released budget):**

- **QGL-global-only:** anchored full image without crop, to test whether extra crop helps or hurts.
- **QGL-crop-only:** local crop without global image, *diagnostic* and only when source is localizable; image-truncation harms are possible.
- **Localization-cost matched QI:** run the same localization step as QGL but suppress only overlay/crop presentation. This distinguishes presentation benefit from extra localization-time computation.
- **Source-ablated/new-image control:** for a small ethically and technically valid subset, replace or mask the target visual content while keeping neutral query text fixed; if evidence readout does not change, do not attribute gains to fresh acquisition. Never assume masking maintains all task semantics.
- **OQ (oracle target name only):** source-specified entity/predicate/spatial reference, **no value**; P3 *diagnostic ceiling*, separately labelled and excluded from deployable comparisons.

Do **not** compare a manually source-corrected target + perfect human ROI with an unassisted model and call it a deployable SAVA gain. Factorial contrasts must hold query identity fixed where possible, or declare the resulting package intervention.

### 5.1 Standardize the readout without contaminating final-answer baseline

For G/Q/QI/QGL, use the **same short target evidence response schema** followed by a controlled continuation. Score the *read value* against source-adjudicated target evidence. Record `wrong`, `correct`, `unmatched`, `uncertain`, `not emitted` separately. When the target is misidentified by the model, count it as a **targeting failure**, not a successful readout of a different easier fact.

Native arm N does not naturally emit the same explicit evidence readout. Therefore: (i) use native only for the **answer-level** paired baseline, (ii) quantify *target readout* primarily among standardized G/Q/QI/QGL arms, and (iii) any baseline evidence-claim comparison using old traces is **secondary** and affected by verbalization opportunity. Do not report a “recovery rate” inflated merely by forcing models to say more.

### 5.2 Prefix / cache equality

- Generate one parent reasoning prefix per family using the pinned protocol and **freeze its exact bytes + image input**. Select checkpoint using a **prospectively specified** rule available without oracle or answer outcome; record cases where no eligible subgoal appears.
- When the backend can clone a KV state, validate parity. If it instead reconstructs a textual prefix in a new request, **all** arms must use the same reconstruction route; disclose that this changes the inference protocol.
- Ensure no future correct final answer, E* evidence, or post-checkpoint generated text leaks into prefix or query.
- Preserve final response boundaries, input/token counts, prompt templates and caps. An at-cap/unscorable response is neither silently scored wrong nor removed without showing missingness sensitivity.

## 6. Evaluation metrics

### Primary deployment-oriented endpoint

**Paired family-level net final-answer accuracy vs N**, with wrong→correct and correct→wrong transitions explicitly reported. Show exact denominators, unscorable/missing states and worst/best missingness bounds; no scoring post hoc from target evidence truth. Also compare QI vs G and QGL vs QI to isolate added components. P2 is **exploratory** and not powered to certify small differences.

### Supporting acquisition-specific endpoints

- **Target selection:** fraction of generated `q_t` queries that identify a source-valid, currently relevant visual entity/property; failures, `NONE`, and unresolvable queries separately.
- **Evidence readout accuracy:** correct / attempted, including an *all-assigned* denominator that counts query/lookup failure as not recovered; conditional accuracy among explicitly scoreable reads shown separately.
- **Grounding correctness:** whether predicted ROI/source address genuinely refers to the requested entity/relationship; source reviewers see the query and original image but not final answer/outcome if feasible.
- **Context effect:** accuracy by pre-frozen `global_required`, `local_plus_global`, and `local_sufficient` source features; no causal interpretation of retrospective feature labels alone.
- **Visualization ablations:** fresh-image vs no-new-image effect and anchored vs unanchored effect on identical queries, plus small source-perturbation checks.
- **Cost and harm:** image tokens, output tokens, calls, total GPU seconds, latency, % extra image accesses, original correct→wrong regressions, harm per additional visual call.

Use family as the resampling unit (one primary target per family), paired family bootstrap with recorded seed; retain answer format × structured-parent strata. Do not treat target subfacts, repeated seeds, or multiple branches from one family as independent samples. For eventual confirmatory testing, prespecify one primary accuracy contrast and confidence intervals, with multiplicity plan if multiple primary contrasts.

### Source validity / evidence audit

`E*` is **an offline reference only**. Source facts are AI reviewed, not established independently human-perfect or guaranteed answer-safe. For P2 audit at least **20–30 representative target/value judgments**, including disagreement and negative-effect cases, independently where practicable; preserve source images, exact claims, bounding boxes and reviewer disagreements. If independent review cannot be obtained, disclose single-agent limitation instead of pretending independent validation.

## 7. Decision rules after the discovery pilot

**Evidence of promise (not a fixed significance claim):**

1. The proposed arm beats matched native/generic controls in **paired net answer improvement** with regression risk reported, **and/or** has a consistent target-acquisition gain of practical size that motivates a larger test.
2. Query generation is sufficiently source-valid to deploy without oracle target identities; if oracle-target alone works, focus 14E on **target selection**, not on crop engineering.
3. QGL adds value beyond QI in source-defined global-required cases; otherwise **drop costly anchoring**. If QI = Q with no new image, acknowledge that new visual exposure has not been isolated as the cause.
4. Source checks do not reveal substantial target/value leakage or misleading crops; exclude or correct broken **infrastructure** by recorded pre-specified rules, not favorable-outcome filtering.
5. The cost/accuracy tradeoff is credible relative to a simple extra-look baseline. A method that improves only at disproportionate compute should be described accordingly.

**Branching by result:**

| Finding | Action |
|---|---|
| QI > G, QGL ≈ QI | Pursue **subgoal-addressed querying**, drop unnecessary crop/overlay |
| QGL > QI, especially for global-required | Pursue **global/ROI source addressing** and test locator quality |
| OQ >> model-query, readout with OQ accurate | Prioritize **automatic target identification** |
| Model-query correct, readout still wrong | Improve **visual source representation/readout**, not target detection alone |
| Evidence ↑, task accuracy unchanged | Record genuine acquisition gain but **do not claim performance improvement**; downstream remains outside C3 method scope |
| No credible benefit or high regressions | Simplify or stop SAVA; do not rescue story by arbitrary new prompt searches |

## 8. Known technical and scientific risks

1. **Model-generated target ≠ source-correct target.** Good query fluency can mask incorrect grounding. Explicitly score source correctness; don't secretly fix bad queries.
2. **QGL has more compute and more visual input.** Use cost accounting and matched-cost sensitivity. Global+local superiority cannot be assumed from retrospective observational error rates.
3. **Image processing changes evidence visibility.** Preserve full image and record processor resolution, crop boundaries, overlay occlusion, aspect ratios, and token/patch counts. Model-view tiny-text claims require actual processed-view measurement.
4. **Prompt/format confounds.** `E*` was a textual package intervention; SAVA's own query/readout can also alter reasoning behavior. Controls G and Q exist to distinguish text effects from visual rereading.
5. **Checkpoint vs continuous reasoning.** Interruption/restart, altered KV access and new image injection must be documented. A natural-language “look again” statement is not proof of fresh source retrieval.
6. **Model comparisons are not same-weights toggles.** Instruct/Thinking checkpoints and deployed decoding differ; infer method effects **within** a pinned model.
7. **Sample selection / benchmark contamination.** R/F were previously audited; final performance needs method-unseen frozen families. Old Stage14B scores do not confer untouched validation.
8. **Annotation uncertainty.** Single-AI source and trace judgments and incomplete timing prevent causal claims about latent acquisition or event chronology. Keep original evidence/score history immutable.
9. **Premature paper claims.** Stage14D-1 is a small exploratory method pilot, not a definitive demonstration of C3, a universal LOOK↔THINK policy, or causal visual-acquisition mediation.

## 9. Operational gates, resources and preservation

**Gate G0 — CPU-only preparation:** proceed without asking for a separate intermediate approval: inspect actual files, validate provenance, write/freeze protocols and schemas, source-select pilot IDs, unit test non-model transformations, produce a bounded GPU preflight request. Preserve all historical files; do not modify Stage14B/14C/14D-0 receipts.

**Gate G1 — any new evaluated-model/GPU scientific runs:** **STOP until explicit new budget release**, plus resolution of Stage14C-V unfinished closure or explicit user waiver. A previous approval of source review/technical calibration is not approval for SAVA inference. Neither 178/363 estimate nor 375 GPU-hour ceiling of old Stage14D transfers to SAVA.

**Gate G2 — pilot completion:** stop and report all arms, failures, leak checks, budget and substantive findings; **do not automatically launch 14E** or large confirmatory inference. Ask for a new scope/budget decision when required.

Before budget request, estimate worst-case image preprocessing, additional image tokens, per-arm reasoning caps, number of total calls, checkpoint costs, and 1×/2× actual runtime scenarios from technical smoke. No invented GPU-hour estimate should be presented as measured. Keep tool outputs and checkpoint hashes available for reproducibility.

## 10. Required deliverables / directory convention

Do not assume directory names exist; discover the real repository first. Preferred **new, append-only** workspace:

```text
outputs/stage14d1_sava/
  README.md
  provenance/source_inputs_manifest.jsonl
  protocol/frozen_method_spec.md
  protocol/sampler_and_seeds.json
  protocol/arm_manifest.jsonl
  protocol/query_schema.json
  protocol/technical_preflight.md
  data/selected_family_target_manifest.jsonl
  data/query_and_roi_predictions.jsonl
  data/paired_readouts.jsonl
  data/paired_continuations.jsonl
  analysis/target_selection_and_readout.csv
  analysis/answer_transitions_and_costs.csv
  analysis/paired_bootstrap.json
  reports/feasibility_main.md
  reports/source_review_exceptions.md
  reports/method_novelty_and_ablations.md
  reports/next_stage_14e_decision.md
```

Minimum report: sample selection and source strata; exact model revision/decoder/template; same-prefix validation; counts per arm; evidence target validity and readout; answer accuracy and transitions; source-specific global-context comparison; costs; negative findings; independent-review limitations; raw example quotations with provenance; preregistered vs exploratory separation.

## 11. Copy/paste agent kickoff instruction

> Read this plan and audit the actual repository, Stage14B `E*`-eligible inventory and raw outputs, Stage14D-0 native trace audit, and Stage14D-0 source difficulty v2 reports. Treat them as immutable historical data. Produce a **source-provenance audit**, a **frozen 72-family development sampler**, a **value-free subgoal-query schema**, testable LOCATE/READ interface, **matched-prefix five-arm execution manifests (N/G/Q/QI/QGL)**, non-model unit tests for ROI transforms/leakage/scorers, and a realistic GPU budget/preflight request. Explicitly separate model-generated source targeting from oracle target-name/ROI diagnostics, and source-annotated target difficulty from inference-time hints. Do not expose `E*` values or archived answer outcomes to generation. Proceed through CPU-only preparation without intermediate approval; STOP before any new evaluated-model inference/GPU job. Keep the old 1,674 Stage14D continuations and 375 GPU-hour plan on HOLD. Do not waive Stage14C-V closure. Return a concise release-review package and only then request authorization for the separately budgeted SAVA pilot. Do not launch 14E or a confirmatory run by default.

---

**Decision to be learned:** Is the missing performance gain mainly in *forming the right source-specific visual query*, *locating its source while preserving global structure*, or *reading it accurately after location*? First show a deployable, no-oracle improvement in final accuracy if one exists; present evidence-fidelity and source tests as the supporting explanation, with limitations intact.
