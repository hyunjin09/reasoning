# Stage 14D-0 Extension v2 — Visual Evidence Difficulty → Acquisition-Method Design

**Status:** REVISED PROPOSAL / retrospective source-image audit; **not executed by this document**  
**Primary task:** MATH-Vision visual-math reasoning  
**Primary purpose:** Find *which properties and visual operations* make **task-critical evidence difficult to acquire**, then nominate targeted acquisition methods for Claim 3.  
**Primary comparison:** frozen source-derived `E*` vs existing **Qwen3-VL-4B-Instruct native** and **Qwen3-VL-4B-Thinking native** observable visual-evidence statements.  
**Hard boundary:** No new evaluated-model inference or GPU jobs. Old Stage14D 1,674 continuations / proposed 375 GPU-hour main run remain **HOLD**; Stage14C-V closure is **not waived**.

> **Central question:** *What makes task-critical visual evidence difficult to acquire, and which visual acquisition operation is a plausible remedy?*
>
> This is **method-selection research**, not a claim that the proposed interventions work or that all wrong answers are caused by acquisition failure.

## 0. Paper claims and scientific scope

Keep this claim set and do not expand C3 into general-purpose reasoning repair:

- **C1 — Evidence handoff:** Some successful trajectories move from visual-access-dependent resolution to text-sufficient continuation. This is a functional observation, **not** a universal, fully separated two-phase sequence.
- **C2 — Evidence bottleneck:** Providing source-derived, task-critical *textual* `E*` repairs a substantial subset of native visual-math failures. This intervention changes representation/binding as well as source access; it does **not** quantify pure perception/acquisition failure.
- **C3 — Better visual evidence acquisition (future method):** During reasoning, identify task-critical evidence demands and retrieve them from the **actual image** more accurately, without oracle `E*` as an inference input; measure both acquired-evidence accuracy and task-accuracy gain. More Thinking is a later baseline, not the central methodology question.

**Important interpretation:** The existing audit measures *what visual evidence is explicitly expressed in observable native model output*, not the complete latent acquisition state. `Not stated`, vague, and temporally unanchored statements must **never** be labeled as proven non-acquisition. The main source-only visual features below are **potential predictors**, not proven causes. Acquisition accuracy after an actual intervention is a *future* experiment.

### Decision this study should inform

Do we prioritize, for Stage14D-1/14E: (a) targeted high-resolution rereading, (b) entity-grounded disambiguation, (c) multi-ROI/global-local reading, (d) count/trace/diagram-operation-specific acquisition, or (e) reasoning-subgoal-conditioned sequential visual lookup? Make this choice from **observed error patterns plus source properties**, not intuition alone. A null result is an acceptable outcome.

## 1. Fixed resources, counts and provenance

Use the completed Stage14D-0 retrospective assets; **do not multiply the old 414 reviews or count `E*` as a third model**.

| Resource | Fixed inventory | Role |
|---|---:|---|
| MATH-Vision families / source images | **300 / 300** | Paired source review and annotation |
| Native r0 model outputs | **300 Instruct + 300 Thinking = 600** | Existing model-side evidence statuses; no regeneration |
| `E*` parent evidence atoms | **437** | Source-derived reference and parent grouping |
| Source-defined subfacts | **1,887** | Candidate fine-grained annotation units |
| Source-adjudicable subfacts | **1,883** | Primary valid denominator; check QC by subfact |
| Withheld source-invalid subfacts | **4 in families 276, 604, 2869** | Exclude from applicable fact denominators; do not silently repair |
| **R**, source-stratified cohort | **150 families** | Primary descriptive/weighted analysis within `E*`-eligible source frame |
| **F**, outcome-enriched cohort | **150 additional families** | Discovery, detailed examples, **no prevalence inference** |
| Earlier prepared native trace reviews | **414** | Overlapping historical reviews, not extra cases |

The prior Stage14D-0 audit and answer × evidence supplement are fixed historical analyses, including the source hashes, family IDs, raw runs, trace quotes, model/checkpoint/seed/decoding configuration, selection strata/inclusion probabilities, native-answer scoreability and archived `E*` rescue *status metadata*. Retain those exact join keys. The previous semantic evidence audit was produced by a **single AI reviewer** with no independent human validation; this study must preserve that limitation.

**Primary unit:** `(family_id, e_parent_id, source_valid_subfact_id)` — paired I/T for the **same** image/subfact. Difficulty labels are **source-only** and therefore **shared across models**. Families with multiple subfacts are clusters, not independent benchmark samples. Record the exact subset size for R and F after validating joins; **do not invent a per-panel subfact count**.

## 2. Research questions — expanded taxonomy

### A. Seven SOURCE-ONLY difficulty dimensions (predictor annotations)

These are the **seven substantive predictors**. Dimensions may correlate; do not combine into one opaque overall “difficulty” score.

| ID | Dimension | Research question | Candidate future acquisition operation |
|---|---|---|---|
| **A** | **Granularity & visual clarity** | Are tiny labels, thin marks, low contrast, occlusions or dense clutter associated with more explicit errors? | Crop/upscale, high-resolution patching, marker-aware reread |
| **B** | **Spatial scope / ROI dispersion** | Is evidence spanning distant ROIs or the entire diagram harder than one local fact? | Multiple ROI queries with global image retained |
| **C** | **Entity/relational complexity** | Are value-to-entity binding, spatial relations, correspondence or topology harder than direct reading? | Entity-grounded queries and structural visual inspection |
| **D** | **Minimal visual-acquisition chain depth** | Does the source fact demand one, two or three-plus **visual** operations? | Sequential acquisition during decoding |
| **E** | **Visual operation type** **[NEW]** | Is the hard part reading, counting, comparing, matching/binding, tracing, relation decoding, pattern analysis or spatial transform? | Choose an evidence-type-specific acquisition operation |
| **F** | **Distractors / source ambiguity** **[EXPANDED]** | Are repeated labels, similar candidate objects, crowded references or visually ambiguous matches associated with failures? | Target-aware disambiguation and contrastive ROI selection |
| **G** | **Global context dependence** **[NEW]** | Does a crop alone plausibly lose the entity identity, relation or diagram frame needed to identify the fact? | Local + full-image conditioned reread, not crop-only |

**Do not treat “shared failure” as an image difficulty attribute.** It is an **outcome comparison** between the two model outputs, analyzed conditional on A–G. Likewise, native correctness and archived `E*` rescue are outcome metadata, never source-only predictors.

### B. Source/eligibility metadata — NOT extra difficulty hypotheses

Record separately: (1) source format (`printed_text`, `diagram_symbol`, `geometry_lines`, `grid_pattern`, `chart_axes`, `table_structure`, etc.; multi-label); (2) structured/scalar parent class; (3) source QC/fidelity and annotation certainty; (4) acquisition **eligibility class**:

- `direct_visual_fact`: printed value, marker, depicted relation, graph axis, label, visible connection.
- `visual_computation`: source-grounded count, pattern trace, visual matching, figure rotation/folding **whose target fact requires visual operations**. Retain and identify separately.
- `math_derived_fact`: obtained only after arithmetic/algebra/geometric deduction from already acquired visual facts. **Exclude from the primary *acquisition* estimand** or report separately; do not count symbolic deductions as visual-operation steps.
- `mixed_or_uncertain`: visual and mathematical steps cannot be disentangled reliably; defer source adjudication or report separately.

**Evidence `E*` is source-derived and can be minimal, imperfect or task-transforming.** A source-visible fact is not necessarily easily readable, and error-type counts in prior audit do not yet establish these source properties' effects.

## 3. Source-only annotation codebook — operational rules

Before matching to I/T outcomes, the annotator gets **image + original question + target source-valid subfact/reference meaning as necessary**, without model outputs, previous error labels, final-answer status, `E*` rescue or any model-inference outcome. If the annotator has historically seen the data, note that masking does **not** create independent blindness.

Provide a short rationale and source span/ROI(s) for every applicable label. `unknown` / `not_applicable` are valid answers; never force a difficult case into a convenient bin. Freeze codebook after pilot and **before** outcome reveal.

### A. Granularity & visual clarity (split into observable subfields)

- `feature_kind`: `text_glyph`, `diagram_symbol`, `thin_line_marker`, `non_text_pattern`, `mixed`, `na`, `unknown`.
- `source_size_class`: `readable_normal`, `small_fine`, `extremely_small`, `na`, `unknown` — defined relative to **actual raster pixels**, with threshold calibration in pilot; don't pretend size classes correspond to a fixed effective VLM scale.
- `visibility_issues`: multi-label `low_contrast`, `blur`, `occlusion`, `overlap`, `dense_clutter`, `none`, `unknown`.
- When measurable: record `source_raster_width_px`, `source_raster_height_px`, ROI coordinates and `glyph_height_source_px` / marker dimension. Preserve metric definition (smallest required glyph, median, etc.). **Never invent effective patch/token sizes.** If pinned preprocessing can be reproduced CPU-only, add a separately flagged processed-view measurement and exact config/hash. If not, report source-image-only results.

### B. Spatial scope

- `scope`: `one_local`, `two_separated`, `three_plus_separated`, `global_configuration`, `unknown`.
- `roi_count`, `normalized_roi_boxes`, `roi_roles` (e.g., `AB_label`, `BC_segment`, `right_angle_marker`) where bounding is defensible. Multiple targets in a contiguous patch can count as one local ROI. Entire diagram/global structure requires `global_configuration`, not a fabricated tight box.
- `distance_proxy` only if ROI coordinates reliably defined; exploratory, never required.

### C. Entity/relational complexity

- `relation_level`: `direct_attribute`, `single_entity_binding`, `two_entity_relation`, `multi_relation_or_correspondence`, `unknown`.
- `binding_targets` and `relationship_type` (examples: `adjacency`, `perpendicular`, `tangent`, `fold_overlap`, `grid_coordinate`, `legend_to_series`) as applicable. Define relation **from the source and question**, not from whatever the model got wrong.

### D. Minimal visual-acquisition chain depth

- `chain_depth`: `one_visual_operation`, `two_visual_operations`, `three_plus_visual_operations`, `unknown`.
- `minimal_visual_operations`: ordered short sequence using the vocabulary in E (e.g., `locate target -> read label -> bind label to AB`). If the depth assignment is arbitrary, use `unknown`. Pilot should specify whether routine target-localization counts as one operation for all examples, or only when genuine search/disambiguation is needed; apply rule consistently.
- **Do not count** equation solving, Pythagoras, answer checking or abstract mathematics as acquisition operations. Visual counting/shape tracing **can** count as visual computation if source-constrained and not just algebra.

### E. Visual operation type — new key dimension

Choose **one `primary_operation`** (the main discriminating visual task), plus optional multi-label `all_operations`; retain `uncertain` if underdetermined:

| Label | Operational meaning | Example |
|---|---|---|
| `read` | Read explicit text/numeral/symbol in the source | Read the `3` printed beside a segment |
| `count` | Enumerate visually distinguished cells/objects/edges | Count shaded grid squares |
| `compare` | Compare size, orientation, pattern or magnitude between targets | Compare two marked lengths/shapes |
| `match_bind` | Associate an observed value/symbol with a named source entity | Decide whether `3` labels AB or AC |
| `trace_follow` | Visually follow path, boundary, connectivity or sequence | Follow arrows around a polygon/grid |
| `relation_decode` | Determine a spatial relation or diagram convention | Read a perpendicular/tangency marker |
| `pattern_structure` | Resolve grid/layout/alternation, grouping or topology | Determine row–column layout in a checkerboard |
| `spatial_transform` | Track geometric fold/rotation/reflection/overlay visual correspondence | Determine which region overlaps after folding |
| `other` / `unknown` | Document why none applies | — |

Where the target is a composite fact, select the **dominant bottleneck candidate from source-only structure** without using model outcomes. Never assert that this label is the actual error *cause*. Distinguish `count` in visually enumerated objects from later arithmetic on counted quantities.

### F. Distractors & ambiguity — new detail

Store independently:

- `competitor_class`: `none`, `same_or_similar_labels`, `similar_shapes_entities`, `repeated_pattern_elements`, `multiple_candidate_regions`, `occlusion_overlap`, `unknown` (multi-label allowed).
- `competitor_count`: actual visible candidates when defensible, otherwise `unknown`; **do not infer perceived distractors from model error**.
- `target_uniqueness`: `visually_unique`, `resolvable_with_local_context`, `requires_global_disambiguation`, `source_ambiguous`, `unknown`.
- `wrong_value_elsewhere_on_source`: **post-unmask only**, evaluated for explicit wrong numerical/label claims, with an exact source location. This is an *outcome-derived diagnostic*, so do **not** add it to pre-outcome source predictors or use it to define distractor class.

This axis asks whether a source contains plausible competing candidates, **not** whether a model necessarily attended to them.

### G. Global-context dependence — new key dimension

This annotation is a **source-only *predicted sufficiency* judgment**, not a validated crop experiment:

- `context_need`: `local_sufficient`, `global_required`, `local_plus_global`, `uncertain`.
  - `local_sufficient`: image patch around target plausibly determines its source fact, with the question's entity reference intact.
  - `global_required`: required fact intrinsically concerns the full structure or relationships which a tight crop cannot retain.
  - `local_plus_global`: local detail is needed **and** global entity identity/diagram context is needed to avoid a binding mistake.
- `context_loss_if_cropped`: `target_identity`, `relation_topology`, `coordinate_frame`, `legend_mapping`, `multi_entity_correspondence`, `none`, `unknown` (multi-label).
- Record the **minimal context rationale**: what the reader would need beyond the local crop. Do not construct a fictitious crop or empirically assert crop-only failure unless a later authorized intervention actually tests it.

**Important G vs B distinction:** B measures **where necessary source information lies**; G measures **whether preserving the broader scene is necessary to interpret an otherwise readable local fact**. They can correlate but should not be treated as interchangeable.

### Source annotation, QC and reproducibility

- `reference_validity`: `source_valid_high`, `source_uncertain`, `withheld_invalid` with precise reason. Keep historical `E*` immutable.
- `difficulty_label_confidence`: `high`, `medium`, `low`; annotator/reviewer identity, revision, timestamp, source hash, question ID.
- ROI coordinate system: `(xmin,ymin,xmax,ymax)` **normalized [0,1]** to archived image width/height; name panel/frame if multi-panel images. Validate range, ordering and image hashes deterministically. Global facts may have no ROI.
- Preserve original Stage14A structured/scalar, Stage14D-0 error taxonomy **in separate downstream tables**, not as new source-only error evidence.
- If target subfact is ambiguous, sourced by an incorrect `E*` reference or requires ungrounded reconstruction, **withhold**, do not replace or silently guess.

#### Hypothetical record (schema illustration, NOT a real annotated finding)

```json
{
  "family_id": "EXAMPLE_ONLY",
  "parent_evidence_id": "p1",
  "subfact_id": "s1",
  "reference_validity": "source_valid_high",
  "acquisition_eligibility": "direct_visual_fact",
  "source_raster_size_px": [1024, 768],
  "roi_boxes_normalized": [[0.2, 0.3, 0.4, 0.46]],
  "A": {"feature_kind": "text_glyph", "source_size_class": "small_fine", "visibility_issues": ["none"]},
  "B": {"scope": "one_local"},
  "C": {"relation_level": "single_entity_binding"},
  "D": {"chain_depth": "two_visual_operations", "minimal_visual_operations": ["read", "match_bind"]},
  "E": {"primary_operation": "match_bind", "all_operations": ["read", "match_bind"]},
  "F": {"competitor_class": ["same_or_similar_labels"], "target_uniqueness": "resolvable_with_local_context"},
  "G": {"context_need": "local_sufficient", "context_loss_if_cropped": ["none"]},
  "confidence": "medium",
  "rationale": "Illustrative only; replace with exact source-grounded image observations"
}
```

## 4. Workflow, gates and sample allocation

### P0 — Read-only inventory + eligibility QC (no inference)

1. Resolve actual repo paths for source images, 1,887 source subfacts, `E*` source wording, existing I/T native classifications, R/F manifest, outcome scores, processor metadata and user-visible local audit viewer. Verify hashes/IDs and **exact** R/F composition.
2. Confirm 300 unique families, 600 original native raws and 1,883 valid + four withheld subfacts; refuse inconsistent joins. Capture prior reviewer limitations and source-invalid entries.
3. Build a **source-only display/export** without I/T raw trace, answer, prior error type, rescue label or model name. Give only the necessary target `E*` meaning, not outcome-conditioned text.
4. Make an integrity report. **Stop** if source/ID provenance is untrustworthy or original images are unavailable. Do not reconstruct images from text.

### P1 — Source-only rubric pilot (**30–40 families**, from R without outcome peeking)

1. Sample frozen IDs for coverage of source formats/structured and scalar parents (record pilot rule/seed/hash). Review **all eligible subfacts** in these families, including those models later state correctly, incorrectly or not at all; **do not select just native errors**.
2. Annotate A–G, source-mode metadata and acquisition eligibility, with ROI and minimal operation sequence. Check whether operation type vs depth, ROI dispersion vs global necessity, and clarity vs distractors are distinguishable.
3. Double-code an overlap of ~10–20 families with **an independent reviewer/human** if available. Report disagreement by axis and adjudication; a same-agent second pass is *not* independent reliability. If independent review is unavailable, disclose this explicitly.
4. Resolve edge cases and freeze **rubric `v2` before unmasking outcomes**. When classes are unstable, merge or demote them before analysis, with documented reason. Maintain unknown/NAs rather than forced labels.
5. Gate: if fewer than a reasonable portion of eligible subfacts have interpretable labels or independent conflicts are pervasive, reduce to supported dimensions and document limitation; do not post-hoc hunt for positives.

### P2 — Main source-only annotation (R primary, F secondary)

1. Under frozen codebook, annotate **all eligible source-valid subfacts of R's 150 families**, reusing valid pilot records. Primary estimate pertains to R's *source-eligible 1,000-family frame*, **not** all 3,040 MATH-Vision problems.
2. Optionally expand to **F's 150 outcome-enriched families** for mechanism sketches/examples and subgroup descriptive follow-up, using the **same** codebook. Never mix unweighted F into R prevalence.
3. Add independent QC to ≥10% if feasible; report actual human vs AI reviewer credentials without inflating reliability. Record unknown/NAs and source exclusions by axis; if F cannot be completed, R is a legitimate finished deliverable.

### P3 — Freeze source predictions and JOIN archived outcomes

Only once the source-only records and rubric are immutable, attach existing **subfact-matched** Instruct/Thinking observable labels and native-answer status/archived `E*` rescue metadata.

**Per-subfact outcome states (reuse, do not reannotate):**

- `explicit_correct`: the required source-valid fact was last stated correctly in the model's full native output.
- `explicit_incorrect_or_misbound`: a final explicitly stated claim is incorrect/misbound.
- `unobserved_or_ambiguous`: unstated/vague/uncertain/temporally unsupported; **not a failure of acquisition**.
- `source_withheld`: source fact cannot be judged; excluded from source-valid denominators with a transparent count.

Keep `ever_wrong`, first-claim and pre-answer analyses only as **limited sensitivities supported by existing annotated spans**. Do not infer precise first-use timing, or treat Thinking's `<think>` boundary and Instruct's expository boundary as equivalent measurements.

#### Primary outcomes and comparisons

For each A–G source axis / model / relevant stratum, report:

1. **Explicit-correct coverage:** `# required valid subfacts explicit_correct / # required valid subfacts`.
2. **Explicit-error coverage:** `# required valid subfacts explicit_incorrect_or_misbound / # required valid subfacts`.
3. **Unobserved / ambiguous coverage:** separate third category, **never added to errors**.
4. **Conditional explicit error:** `# wrong or misbound / # (correct + wrong)` **only alongside** the first three, because speech/trace length differ.
5. **Paired I/T matrix** on identical valid subfacts: both correct, I-only wrong, T-only wrong, both wrong same/different, one or both unobservable. Report both explicit-comparable and full-denominator representations.
6. **Family-level burden:** any explicit error, all-source-facts-explicit-correct, count/fraction source facts explicitly correct, native correct/wrong/unscorable (strictly separate), archived `E*` rescue transition for native wrong when archived scores allow it.

**Priority targeted contrasts (exploratory):**

- A: tiny/fine text or mark vs clearly readable comparator, **within corresponding source-feature class**; keep `na` and blur separate.
- E: `read` vs `count` / `trace_follow` / `pattern_structure` / `match_bind`; report denominators and possible overlap of `all_operations`.
- F: repeated/similar competing targets vs visually unique targets; additionally test whether post-unmask wrong label/value appears *elsewhere in source* as a bounded qualitative diagnostic with exact image location.
- G: `local_sufficient` vs `local_plus_global` / `global_required` (predicted only), **not** an experimentally tested crop effect.
- B/C/D: one local vs multiple ROI/global; direct attribute vs relational; 1 visual operation vs 2 vs 3+.
- Outcome cross-tabs: shared vs model-specific explicit errors, and native-answer correct/wrong by difficulty, plus archived `E*` rescue as secondary association. All comparisons use **matched correct controls**, not errors alone.

### P4 — Statistical analysis, checks and result interpretation

- **R is primary**: use sealed source-stratum inclusion/inverse-probability weights, show **raw numerator/denominator** in all tables, and family-level/family-equal estimates. Suggested 4,000 shared-seed family-cluster bootstrap repetitions **within original source strata**; do not resample subfacts independently. Clearly state denominators where family and subfact aggregation differ.
- **F is discovery**: descriptive counts and within-F summaries only. A pooled 300-family raw bar plot may appear for visualization if marked **diagnostic nonprevalence**, not for a population claim.
- Source properties correlate: operation count and type, relation complexity, ROI spread, distractor and global dependence may share mechanisms. Start with single-axis profiles and small, prespecified multivariable sensitivity *only if* supported by cell counts and coverage. Do not call coefficients causal effects or manufacture a risk-adjusted causal predictor.
- Report every `unknown`, `na`, withhold and unscorable denominator. Disclose selected-verbalization bias, different I/T checkpoints/decoding/trace length, same-agent annotation dependence and source-image vs model-processed input uncertainty.
- Family-level correctness vs source-fact explicit status is **associational**; source-selected R is not an untouched confirmatory test, and error patterns from the audit have already motivated the hypotheses. No multiplicity-adjusted claim unless actually preregistered and reported.
- **Null findings matter.** If tiny text, multi-step acquisition, operation type, competitors or crop-context predictions do not distinguish errors, report this directly and do not post-hoc change thresholds to create an effect.

### P5 — Required outputs and STOP

Write **new** versioned artifacts under e.g. `outputs/stage14d0_visual_difficulty/v2/` (adapt to repository layout). **Do not overwrite historical outputs**.

| File | Required content |
|---|---|
| `README.md` | Scope, fixed sample and non-execution disclaimer |
| `inventory_and_provenance.json` | Exact file paths, hashes, model IDs/seeds, R/F manifests and QC gaps |
| `rubric_v2.md`, `pilot_annotation_and_adjudication.md` | Frozen labels, ROI rule, source-only masking, pilot decisions, annotator reliability limitations |
| `source_difficulty_subfacts_v2.jsonl` | A–G source labels, eligibility type, ROI/provenance, confidence, rationale, **no model outcome labels** |
| `difficulty_by_model_error.csv` | A–G per-model explicit correct/error/unobserved, actual denominators and R weights |
| `operation_type_and_depth.csv` | Primary/multilabel visual operations × visual-depth × error states |
| `distractor_and_wrong_source_location.csv` | Source-only distractor labels + **separate post-outcome** wrong-value-elsewhere diagnostics |
| `roi_scope_vs_context_need.csv` | B × G cross-tab and error associations; `context_need` explicitly hypothetical |
| `paired_I_T_shared_failure.csv` | Same-fact both-correct/I-only/T-only/both-wrong with same/different wrong where existing audit supports |
| `difficulty_by_answer_and_rescue.csv` | R/F separated, native correct/wrong/unscorable, archived rescue status metadata |
| `cluster_bootstrap_and_sensitivities.json`, `analysis.py`, `tests/` | Reproducible weighting, cluster CIs, exclusions, join and count verification |
| `casebook_source_images.md` (or local HTML viewer) | At least 3 *error* and 3 **matched success** examples; source images/IDs, exact source-visible reason, verified trace excerpt provenance |
| `report.md` | Observations, negative findings, QC constraints and paper-safe claims |
| `method_design_implications.md` | **Specific weakness → appropriate candidate visual acquisition operation → testable Stage14D-1 idea**, not downstream solver repair |

**Acceptance gates:** output count reconciliation with 300 families/600 native records/1,887 subfacts/4 withheld; exact R/F provenance; no outcome leakage into source-only labels; explicit missing/unknown; no incorrectly claimed reliability; no extra GPU/evaluated-model generations; proof that old main run remains HOLD. If a required join/source image is missing, STOP and report without inventing data.

**Stop after report.** No Stage14D-1, Stage14E, training, visual tool calls to evaluated models, RL or GPU execution without explicit separate approval. No waiver of Stage14C-V closure or 375-GPUh Stage14D main run budget.

## 5. How findings inform—but do not prove—Claim 3

| Source-only difficulty × observed evidence error | Plausible C3 acquisition idea to test later | Important control |
|---|---|---|
| Tiny glyphs, thin markers, low clarity | Source-targeted crop/upscale at evidence query | Same checkpoint, full-image context retained; compare generic zoom |
| Several distant regions or high B | Joint multi-ROI reread, original image + target regions | Same token/image budget; irrelevant/adjacent-ROI controls |
| `match_bind` with similar candidates (E+F) | Entity-anchored matching and visually marked source candidates | Correct target ID without leaking value; wrong-target controls |
| `count` / `pattern_structure` | Region decomposition, count-specific visual acquisition | Extra generic computation budget control |
| `trace_follow` / `spatial_transform` | Sequential visual tracing or structural interrogation | Global-only vs local-only vs global+local |
| G=`local_plus_global` | Crop with preserved full-scene entity/coordinate context | Direct crop-only vs global+local; G label was predicted, not measured |
| D=`three_plus_visual_operations` | Reasoning-subgoal-driven *sequential* evidence query during decoding | Parallel one-shot extraction at matched compute |
| No stable source difficulty association | Reconsider source proxies or triggering rather than claim visual source cause | Null result explicitly recorded |

**Success criterion for a *future* C3 method:** evidence recovery on actual images improves (with source-verified evidence atoms/visible facts) **and** downstream MATH-Vision native accuracy improves, with wrong→correct and correct→wrong transitions and cost accounted for. `E*` is **never supplied at method inference**. Stage14D-0 v2 is **not** that validation.

## 6. Execution instruction

The companion copy/paste Agent prompt is: `stage14d0_visual_evidence_difficulty_agent_prompt_v2.md`.

**Agent instruction:** read this entire plan first, then perform P0→P5 using source-only annotation and immutable outcome joins, or STOP at the first unmet gate. Do not start old 375-GPUh main run.
