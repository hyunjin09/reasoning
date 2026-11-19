# Stage 14C — Cross-Task Evidence-Recovery vs Post-Evidence Bottleneck Analysis

**Research execution plan | Version:** draft for review / **Status:** NOT AUTHORIZED, NOT LAUNCHED  
**Primary model pair:** Qwen3-VL-4B-Instruct and Qwen3-VL-4B-Thinking (pinned Stage 14B revisions/recipes)  
**Inputs:** sealed Stage 14A source cohorts; completed/sealed Stage 14B results; the two accompanying 2026 papers  
**Scope:** cross-task behavioral failure localization first; literature-inspired visual/reasoning signals only as separately approved diagnostics  
**Non-goals:** method deployment, head steering, same-checkpoint Thinking-toggle causal claims, scaling across models, and a causal explanation of semantic addressability

> **Decision required before execution.** Review/freeze the primary task benchmarks, source-only cohort rules, evidence-eligibility rules, score adapters, hypotheses, run budgets, and analysis code. This file specifies the study; it does not authorize model runs.

---

## 0. Central question and why 14C follows 14B

**Central question:**

> **Which visual tasks are limited by failure to obtain usable task-critical evidence, and which retain substantial failure or Thinking–Instruct differences after that evidence is made available?**

The goal is not merely to compare `Thinking - Instruct` across benchmarks. It is to build a **cross-task bottleneck map** that distinguishes:

1. **evidence-supply responsiveness:** whether supplying source-verified task-critical evidence changes answer success;
2. **residual difficulty:** whether incorrect answers remain under correctly supplied evidence;
3. **post-evidence variant advantage:** whether Thinking exceeds Instruct under the same image-free `Q + E*`;
4. **native task selectivity:** how Thinking–Instruct differences change across task families, as an important secondary perspective.

**Stage 14B foundation (completed):**

| Sealed 14B endpoint | Estimate | 95% interval / coverage |
|---|---:|---|
| MATH-Vision native Thinking - Instruct | **+7.20 pp** | +5.67 to +9.08 pp; 2,738/3,040 complete pairs |
| Instruct `E*` rescue among scored native-wrong follow-ups | **55.98%** | 51.08 to 60.80%; 234/418; 31 unresolved |
| MATH-Vision equal-evidence Thinking - Instruct | **+14.69 pp** | +12.10 to +17.39 pp; 926/1,000 complete pairs |
| MathVerse prespecified modality-profile contrast | **+9.28 pp** | +6.15 to +12.36 pp |

These are **not** measurements of a pure perception/reasoning partition. `E*` supply changes evidence availability, formatting, and potentially binding/representation. Instruct and Thinking are different deployed variants, with different validated output-token caps; neither a same-weights Thinking toggle nor equal-compute intervention has been established. Stage 14C must retain these boundaries.

**Paper-level positioning:**

`14B: Is there a large evidence-supply bottleneck?`  
`14C: Does the bottleneck profile differ across kinds of visual tasks?`  
`14D: Does the profile change with scale and modality?`  
`14E: What are the trace/state correlates of successful evidence resolution?`  
`14F: Can targeted evidence recovery and control improve answers relative to simply thinking longer?`

Stage 14C is **observational across tasks, intervention-based within task through `E*` supply**. Cross-task differences are not themselves causal effects of task type.

---

## 1. Literature inputs: use as baselines, not as assumed mechanisms

### 1A. *When to Think and When to Look: Uncertainty-Guided Lookback* (CVPR 2026)

Source: uploaded `2511.15613v3.pdf`, especially Sections 3.1–3.3 and 4.1–4.5 (pp. 3–8).

The study reports that Thinking's advantage depends on task category and capacity; longer traces can be wrong and poorly grounded. It uses **Real / Noise / No-image** fixed-prefix token-perplexity contrasts:

\[
\Delta_{\rm content}(s)=PPL_{R}(s)-PPL_{N}(s), \qquad
\Delta_{\rm presence}(s)=PPL_{N}(s)-PPL_{\varnothing}(s).
\]

It also finds benefits from uncertainty-guided lookback compared with periodic insertion and tests adaptive lookback on math and broad VQA benchmarks.

**Use for us:** diagnostic comparison between *visual-content sensitivity* and *demonstrated recovery of particular evidence*. A change in next-token likelihood is **not** by itself proof of fresh acquisition or correct task-critical evidence. Uncertainty-guided lookback is a **future method baseline** for 14F, not a 14C primary condition.

### 1B. *Does Reasoning Improve Seeing? Understanding When VLMs Benefit from Thinking* (ICML 2026)

Source: uploaded `30498_Does_Reasoning_Improve_S.pdf`, especially Sections 3–6 (pp. 3–9).

The paper defines empirical per-item reasoning helpfulness with multi-pass outcomes,

\[
r_{\rm help}(x)=\widehat p_T(x)-\widehat p_I(x),
\]

and probes pre-generation final-token hidden states for `r_help` and desired response length. Its “perception-dominant” and “reasoning-dominant” cohorts are constructed from **low/high `r_help`**, rather than a source-validated `E*` rescue assay. It reports partially separated length and reasoning/difficulty head associations and downstream head-scaling effects.

**Use for us:** compare a **reasoning-utility signal** with *bottleneck-specific evidence-supply responsiveness*. Do **not** relabel low `r_help` as demonstrated evidence-acquisition failure. Learning probes and head intervention are not required for the Stage 14C primary result; a separately approved diagnostic pilot may explore feasibility. Head steering belongs downstream.

### Originality constraint

“Thinking is task-selective,” “lookback prompts help,” and “difficulty/length signals are decodable” are not sufficient new claims here. The intended novelty is a **source-controlled, answer-safe `E*` bottleneck decomposition across task families**, with explicit limits when that decomposition is not identifiable.

---

## 2. Proposed task panels and sampling

### 2.1 Primary task-family map

| Task family | Source candidates (confirm official splits/licenses before freeze) | Role |
|---|---|---|
| **Visual math anchor** | MATH-Vision `E*`-1,000 and full native results from Stage 14B; MathVerse 788 paired versions as contextual modality analysis | Sealed large-N reference, not a fresh independent test |
| **Generic multimodal VQA** | MMBench-style or MMStar-style native questions; select **one primary benchmark** prospectively | Evaluate whether evidence-supply responsiveness and residual gaps differ outside math |
| **Fine-grained perception / correspondence** | VLMsAreBlind, and/or a `VLMs Need Words`-style correspondence benchmark; choose **one primary benchmark** prospectively | Test tasks involving precise spatial/visual binding where textual evidence may be hard to express safely |

The named datasets are **candidates**, not declarations that their splits have sufficient sample counts or valid `E*` representations. Confirm exact benchmark versions, answer formats, image licenses, gold integrity, independence units, and source availability before locking the cohorts.

### 2.2 Size and units

- **Budget target:** approximately **1,000 independent source-selected families per new primary benchmark**, or the **entire available eligible split if smaller**. Never pad with duplicates to reach 1,000.
- If the dataset has multiple versions/questions for one underlying scene/problem, group them by a defensible source-family identity before selection; report native items and independent families separately.
- **Math anchor:** reuse the already frozen MATH-Vision `E*`-1,000 (and its existing outcomes) under strict condition-identity checks. MathVerse's six versions are **repeated observations on 788 families**, not six distinct tasks.
- The primary native census uses all prospectively chosen families. The `E*` panel is the **answer-safe, source-valid eligible subset**; its size may be smaller than 1,000 and differs by task.
- Target an outcome-blind **~200–300-family diagnostic reserve** per new benchmark if technically possible, selected by a separate frozen hash. It is for stability/diagnostics, not post-hoc effect search. Do not call it untouched confirmation if source catalogs or prior exposure are documented.

**Key population separation:**

1. **Native evaluation population** (the broad source-selected benchmark slice): estimates `G_img` and task-level accuracy.
2. **Eligible `E*` population** (source-only subsample): estimates rescue and post-evidence gap.
3. **Ineligible/ambiguous source stratum**: count and characterize; no fabricated oracle/rescue numbers.

**Do not** interpret estimates from differently selected `E*`-eligible strata as automatically representative of the full benchmark or directly comparable without composition qualification.

### 2.3 Source-only freeze before generation

Produce immutable task-specific manifests containing:

- dataset, version, official split, file/image hash and native item ID;
- family ID and conservative aliases/repeat groups;
- task category and source-only difficulty proxies if provided;
- native question, answer format and gold provenance;
- eligibility/QC decisions, reviewers, review version and source-validity flags;
- frozen selection seed, strata, ranks, confirmation membership and manifest hashes;
- `E*` source objects/atoms, serialization and exact answer-leakage validation;
- historical exposure/overlap where evidence exists, without conflating catalog exposure with outcome inspection.

No evaluated-model outputs, traces, test accuracy, or previous per-item outcomes may influence new cohort selection or `E*` content.

---

## 3. Critical design gate: is `E*` answer-safe in every task family?

`E*` retains the Stage 14A definition:

> **The smallest answer-safe set of directly image-derived facts that, together with the nonvisual question, makes the task solvable without the original image.**

Rules: directly observed source facts only; no downstream derivation; no final answer, answer-option paraphrase, hidden solution or unrelated facts packed into one atom. A coherent grid/table/adjacency/sequence may be a **structured atom** only if it is one minimal source object; record internal subfact count, unit, and minimality.

### 3.1 Gate outcomes per item

- `ELIGIBLE`: task requires visual facts; a sufficient **and answer-safe** `E*` can be written and source-checked.
- `TEXT_SUFFICIENT`: nonvisual question already suffices; do not count as visual-evidence recovery assay.
- `ANSWER_LEAKAGE_UNAVOIDABLE`: every sufficient evidence statement essentially gives the requested answer.
- `NO_DEFENSIBLE_ESTAR`: no sufficiently faithful, answer-safe image-free representation is available.
- `AMBIGUOUS_SOURCE`, `UNDERSPECIFIED`, `SOURCE_CONTRADICTION`, `GOLD_CONFLICT`, `CORRUPT` or documented additional source-defect codes.

**Illustration:** “What color is the dog?” may be directly answered by its only relevant visual fact, “the dog is brown.” Calling the latter a non-answer-leaking `E*` is not defensible. This item **can remain in native VQA comparisons**, but it should **not** enter the primary `E*`-rescue denominator. In contrast, a table with numerical entries followed by a comparison/calculation may allow a minimal source-faithful `E*` that does not directly state the answer.

### 3.2 Gate at the benchmark level

Before generation, report:

- `% of selected native families with source-valid, answer-safe E*`;
- eligibility by question type, modality, category and source format;
- structured/scalar `E*` composition and internal information volume;
- failure/ambiguity reasons, with no post-outcome rescue of excluded items.

If a proposed generic/fine-grained benchmark produces **too few defensible `E*` items for interpretable analysis**, do **not** weaken the evidence or leakage definition to force `N=1,000`.

**Mandatory decision:** either (a) keep that benchmark for native selectivity only and report `E*` ineligibility as a source finding, or (b) choose a new benchmark **under a documented source-only amendment before any model outcomes**. Do not silently replace an outcome-viewed dataset.

### 3.3 QC and reliability

- Freeze ordered source-only selection and exclusion rules before reviewing candidates.
- Require a second source review for each final `E*`; use an independently selected source reread subset when resources allow.
- Preserve rejected candidates, original decisions, aliases and every correction as revisioned records.
- Use gold only for source integrity checks, never to insert the solution into evidence text.
- Same-agent review does **not** establish independent inter-rater reliability; disclose the limitation.
- No external annotators, downloads or GPU jobs without separate authorization/recording.

---

## 4. Model conditions and execution identities

Primary models: same pinned Qwen3-VL-4B Instruct and Thinking variants as Stage 14B. Freeze **checkpoint revisions, processors, prompts, image transforms, precision, decoding, seed, stopping, model-specific token caps, output extraction and score adapters** before any 14C main runs.

For every selected **native** family:

\[
I_{\rm img},\quad T_{\rm img}.
\]

For every **`E*`-eligible** family:

\[
I_{\rm img},\quad T_{\rm img},\quad I_{E^*},\quad T_{E^*}.
\]

`I_E*` / `T_E*` requirements:

- input is **image-free** `Q + E*`, with the same exact evidence content and a fixed, benchmark-invariant prompt skeleton;
- preserve necessary task instructions, answer choices (if native) and output format without extra hints;
- no per-checkpoint evidence edits, no answer leakage, no solver-derived information;
- domain-specific serialization adapters only to preserve source meaning, and frozen before generation.

**14B reuse rule:** reuse existing math outputs only if the full model/input/seed/recipe/extraction identity matches the new reference condition. If the common protocol differs, keep 14B as a labeled external anchor; do not silently pool non-identical runs or rerun math solely to force apparent comparability without authorization.

**Budget fairness:** the Stage 14B comparison used validated but unequal output-token caps (32,768 / 81,920). Preserve those recipes for direct replication and state that this is **not equal-compute**. A common-cap sensitivity is a separately declared optional analysis, not a retrospective reinterpretation of the existing primary contrast.

---

## 5. Prespecified outcome definitions

Let `Y_{m,c}(i)` be a four-way outcome on item `i`, checkpoint `m` and condition `c`: **correct**, **wrong**, **unscorable/unresolved**, or **technical missing**. Do not collapse the latter two into wrong. `E*`-based outcomes are defined only within the frozen eligible population `\mathcal E_t` of task group `t`.

### 5.1 P1 — Cross-task Instruct evidence-supply rescue (primary)

\[
R_I(t)=P\left(Y_{I,E^*}=+\mid Y_{I,\rm img}=-,\; i\in\mathcal E_t,\;\text{both outcomes scored}\right).
\]

Report numerator, scored native-wrong denominator, unresolved native-wrong followups, and **worst/best bounds** using all identified scored native-wrong items as the reference denominator. A conditional rescue rate cannot by itself establish that the same *fraction of all failures* is evidence-limited across benchmarks with different eligibility or error rates.

### 5.2 P2 — Cross-task equal-evidence variant advantage (primary)

\[
G_{\rm post}(t)=Acc(T_{E^*}\mid t)-Acc(I_{E^*}\mid t),
\]

estimated as **paired within-family correctness differences** on common scored pairs. Display the marginal scored-answer accuracies separately (which may have different denominators) and do not obtain `G_post` by naively subtracting them.

### 5.3 P3 — Net evidence-supply benefit and regressions (mandatory companion)

\[
B_{\rm supply}^{m}(t)=E\left[Y_{m,E^*}-Y_{m,\rm img}\mid i\in\mathcal E_t,\;\text{paired scored}\right].
\]

The transition decomposition, on the same paired denominator, is:

\[
B_{\rm supply}^{m}(t)
=P(-\!\to\!+)-P(+\!\to\!-).
\]

This is critical: supplying `E*` can **rescue** some items and **harm** others through prompt/format changes. Always report the entire `image -> E*` transition table (including stable-correct/stable-wrong), not just rescued items.

### 5.4 P4 — Residual error under correct evidence (mandatory companion)

\[
F_m(t)=P(Y_{m,E^*}=-\mid i\in\mathcal E_t,\;\text{scored}).
\]

Also show `P(native wrong AND E* wrong)` and the four-cell native-to-`E*` outcome table. Call these **evidence-supply-resistant failures**, not automatically “pure reasoning failures”: omissions, insufficient practical representation, binding, scoring, and interface changes may remain.

### 5.5 P5 — Native task selectivity (secondary)

\[
G_{\rm img}(t)=Acc(T_{\rm img}\mid t)-Acc(I_{\rm img}\mid t).
\]

Report native `G_img` for the **entire prospectively selected task benchmark**, and separately for its source-eligible `E*` stratum. Also report baseline accuracy/headroom, question format, answer-option type, and technical/scoring completeness. A raw larger gap on a harder benchmark does not on its own identify a mechanism.

### 5.6 Cross-task hypotheses and contrast freeze

Predeclare a small confirmatory contrast family **before new model outcomes**:

- `C1`: `R_I(math) - R_I(generic VQA)` (where both have identifiable, sufficiently powered `E*` cohorts);
- `C2`: `R_I(math) - R_I(fine-grained/correspondence)` (same eligibility condition);
- `C3`: `G_post(math) - G_post(generic VQA)`;
- `C4`: `G_post(math) - G_post(fine-grained/correspondence)`.

Use **two-sided** inference; no assumed sign is necessary. If a task has invalid/insufficient `E*` coverage, mark its affected contrast **not estimable** and retain native task selectivity as a separate result. Never replace it with an easier post-hoc comparison.

**Important:** do not compare `R_I(t)` (a conditional percentage) with `G_post(t)` (a paired percentage-point difference) and declare one bottleneck “larger.” Their populations/estimands differ. Cross-task task-mix differences are still observational.

---

## 6. Analysis, missingness, and multiplicity

### Primary inferential unit

- Use **independent problem/source family** wherever defensible.
- Cluster known aliases, same scenes, paired versions, and repeats; preserve unknown-dependence limits.
- Use paired model conditions at item/family level; avoid treating all modality versions as independent observations.

### Statistical procedure

- Prespecify e.g. **10,000 clustered/bootstrap resamples** (consistent with Stage 14B), seed, confidence method, and item/family weighting **before** model outcome inspection.
- For cross-task differences, resample independent families **within task** and compute contrast differences from those draws.
- For `C1`–`C4`, either apply **Holm family-wise correction at alpha = 0.05** to prespecified tests or report unadjusted confidence intervals without adjusted-significance wording; **choose and freeze one policy before running**. Default recommendation: Holm-adjusted primary tests plus transparent unadjusted 95% descriptive CIs.
- If grouping by source benchmark creates markedly different baseline correctness/headroom, additionally report outcome-blind source-only difficulty/format strata and descriptive sensitivity. Do not label a post-hoc outcome-matched subset as confirmatory.
- Do not treat seed replicates as independent item/family samples.

### Missing/unscorable

- Preserve `correct / wrong / unscorable / technical missing` separately in every panel.
- Include complete-pair estimates, denominator counts, and conservative missingness bounds for the main contrasts.
- Audit answer extraction using one prespecified versioned procedure (fixed hash audit plus all unresolved cases), preserve original parser outputs and semantic adjudications. Note that same-agent review is not independent human reliability evidence.
- Never change native golds, tolerances, prompt, selected cohorts, or outcome labels to strengthen an effect.

### Important reporting distinctions

- **Native coverage:** selected source population (not automatically 100% scored).
- **`E*` coverage:** subset where source-only, sufficient and answer-safe `E*` exists.
- **Rescue coverage:** scored native-wrong and scored `E*` followup pairs, plus bounds.
- **Variant gap coverage:** common scored Instruct/Thinking pairs.
- **Effect on full source population:** **not identified** by eligible-only rescue unless separately justified.

---

## 7. High-value secondary diagnostics from the two papers

These should **not delay** 14C main results and require separately frozen diagnostic manifests, compute ceilings and scripts. Do not infer a mechanism merely because a signal correlates with final-answer accuracy.

### D1 — Direct evidence-recovery probe (recommended secondary)

On a source-frozen subset (e.g. up to **300–500 eligible families per task**), elicit **visual facts only**, using a fixed request that does not ask for the final answer. Compare emitted facts with frozen `E*` using preregistered atom/structured-subfact scoring.

Report:

- demonstrated `E*` atom precision/recall / exact fact recovery;
- structural-object fidelity as well as atom count (one structured atom may contain many subfacts);
- `E_probe` vs `E*`-rescue outcome cross-tabs; disagreement cases and reviewer audit;
- Instruct vs Thinking evidence-probe performance as descriptive outcomes.

Do **not** equate an extracted fact printed by a separate probe with what the original native solver internally knew. This diagnostic is best used to challenge a **mere reasoning-budget** explanation and to motivate later intervention.

### D2 — Real/Noise/No-image token-sensitivity pilot (optional)

For an outcome-blind selected trace subset with stable technical replay:

\[
\Delta_{\rm content}(s)=PPL_R(s)-PPL_N(s),\quad
\Delta_{\rm presence}(s)=PPL_N(s)-PPL_{\varnothing}(s).
\]

Fix the reasoning prefix and next-token targets; use same-resolution/same-tokenization-safe controls where possible, plus background/irrelevant image controls to characterize noise artifacts. Tag source-grounded first-explicit-evidence events (`E1`) independently of the PPL profiles, then compare **pre-E1** versus **post-E1** and correct/incorrect trajectory strata.

**Interpretation:** PPL benefit/sensitivity is not evidence of specific causal semantic retrieval. Our stronger semantic counterfactual assay (Claim 2) remains distinct. Full acquisition/handoff mechanism inference is reserved for 14E/14F.

### D3 — Pre-generation `r_help` / length probe feasibility (optional)

The ICML paper estimates `r_help` from **K=10** passes under a fixed protocol. Our Stage 14B `confirm-300` has only three seed replicates; its `K=3` outcome frequency is **not an equivalent supervision target** and cannot be labeled a direct replication.

If approved, freeze a training/validation/test split **by source family**, label protocol and K *before* additional calls; keep oracle-label construction strictly separate from evaluation families. Extract final prompt-token representations before generation, then compare prediction of:

1. empirical `r_help`;
2. evidence-supply responsiveness / source-eligible rescue proxy (only where measurable);
3. source-only difficulty (where available).

Report MSE, rank correlation, class balance, calibration, cross-task transfer, and label instability. Only proceed to causal head interventions in a separately authorized later stage.

### D4 — Hypothesis for later method stage (NOT part of 14C)

Test whether **target-specific evidence lookback** repairs evidence-supply-responsive cases better than:

- original Thinking;
- generic uncertainty-guided lookback;
- fixed-period image review;
- additional reasoning tokens;
- `E*` oracle (diagnostic reference, **not** deployable policy).

Any such test must separate **oracle target selection** from **model-selected missing evidence**, and compare actual additional compute. An `E*` rescue does **not** establish that a practical lookback prompt can recover that evidence.

---

## 8. Sequence of work and explicit STOP gates

### Gate G0 — Review and freeze the 14C design (no generation)

- Confirm exact benchmark(s), official split and independent-family IDs for generic VQA and fine-grained/correspondence.
- Freeze model/recipe identity, source eligibility rubric, target family count, metadata, sampling seed, native score protocol, `E*` prompt skeleton, primary contrasts, multiplicity policy and missingness policy.
- Declare whether D1–D3 are included, their budgets and data splits; default is **D1 limited secondary; D2/D3 optional, not automatically launched**.

**STOP for approval before proceeding.**

### Gate G1 — Source-only construction (no evaluated-model calls)

- Run source audit and candidate screening in immutable frozen order.
- Produce native cohort and `E*` eligibility/QC manifests with two-pass review and answer-safe checks.
- Produce summary counts for eligible, ineligible and ambiguous per task; re-evaluate scientific feasibility.

**STOP if the planned cross-task `E*` contrasts are not identifiable.** Do not silently create a new dataset after observing outcomes.

### Gate G2 — Technical preflight (bounded, no science tuning)

- Small fixed technical test covering both model variants and each selected task/condition.
- Validate image decoding, prompt identity, `E*` serialization, scoring, source joins, cap behavior, determinism/seed effects, output logging, recovery supervisor and classification of unresolved outputs.
- Technical fixes require versioned amendments and re-preflight; no choosing prompts by accuracy.

### Phase 1 — Main native runs

- Run `I_img`, `T_img` on the frozen native slices for each **new** benchmark.
- Freeze exact raw generations and condition receipts before scoring.
- Reuse 14B math native outputs only if identity-compatible; no automatic duplication.

### Phase 2 — `E*`-eligible panel

- Run `I_E*`, `T_E*` only for frozen source-valid, answer-safe families.
- Freeze outputs, answer extraction and adjudication receipts.
- Predefined retry policy applies only to technical failures, not wrong answers.

### Phase 3 — Primary analysis and seal

- Score P1/P2 plus P3/P4 companions, compute prespecified contrasts, paired transitions, clustered uncertainty, missingness bounds and task/eligibility coverage.
- Produce **a primary-only result summary** before subgroup exploration or diagnostic interpretation.

### Phase 4 — Secondary/QC/sensitivity

- Source-category and format sensitivity; clean-vs-ambiguous strata; subject/modality/repeats; source exposure; native headroom and coverage.
- Run only the approved D1 evidence probe and/or D2/D3 diagnostics within fixed budgets.
- If planned, run prespecified seed-stability repeats; label **stochastic robustness**, not fresh independent confirmation.

### Gate G3 — Final closure

- Verify all frozen manifests/checksums, outputs, scorer identities and missingness counts.
- Seal final summary, plots, resource accounting, negative results and recommendations.
- **STOP. Do not auto-launch Stage 14D, 14E, 14F or a method.**

---

## 9. Approximate call budget (planning bounds, NOT authorization)

Per new benchmark, for `N_native` frozen families and `N_E*` answer-safe eligible families:

\[
N_{\rm base\;calls}=2N_{\rm native}+2N_{E^*}.
\]

If `N_native = 1,000` and **all** 1,000 have valid `E*`, this is **4,000 calls per benchmark**. If `N_E* = 400`, it is **2,800 calls**. For two new task groups, budget accordingly; do not assume that each group has 1,000 eligible `E*` families.

- Sealed 14B math runs contribute **zero new calls** if the reference conditions can be reused.
- Extra multi-seed calls: `2 × selected_conditions × selected_families × extra_seeds` (calculate exactly in the run specification).
- D1 standalone evidence-probe calls, D2 teacher-forced replay costs, and D3 multi-pass labels/white-box hidden-state extraction are **separate line items**.
- Report generated tokens, timeouts, truncations, model caps, observed GPU allocations and hardware/software hashes; no assumed GPU-hour estimate is scientific evidence.
- Do not start resource-heavy D2/D3 without separate approval and a feasibility pilot.

---

## 10. Figures and tables

**Core Figure 1 — Source-only eligibility map:** native selected vs eligible `E*` vs leakage/ineligible/ambiguous by task. This figure is essential to interpret the other panels.

**Core Figure 2 — Cross-task bottleneck profile:** `R_I(t)` with actual numerators/denominators and conservative missingness bounds, plus companion `B_supply^I(t)` or rescue/regression transition proportions on a common denominator.

**Core Figure 3 — Residual and post-evidence profile:** `Acc(I_E*)`, `Acc(T_E*)`, paired `G_post(t)` and remaining wrong/unresolved cases. No misleading marginal-subtraction effects.

**Core Figure 4 — Native Thinking task selectivity:** native `G_img(t)` with Instruct baseline, T accuracy, eligible-stratum sensitivity, score completeness and source-type labels.

**Core Figure 5 — 2D task map:** x = evidence-supply responsiveness (carefully labeled denominator), y = equal-evidence Thinking gap; uncertainty bars and eligible-set coverage. **Descriptive only**; do not claim absolute upstream-vs-downstream dominance from unlike estimands.

**Optional diagnostics:** evidence-probe precision/recall vs rescue, `real/noise/no-image` event-aligned traces, `r_help` probe correlations (only if approved).

---

## 11. Outcome scenarios and scientific updates

| Finding | Supported conclusion | What NOT to conclude |
|---|---|---|
| Math has high `R_I`; other tasks materially lower | Oracle evidence supply is more helpful in the tested math eligible stratum | Math is intrinsically “more perceptual”; source cohort/eligibility may differ |
| All tasks have substantial `R_I` | Evidence-supply responsiveness is not confined to math | Every failure is a visual misread |
| Some tasks have `R_I` high but `G_post` low | Correct evidence supply often resolves native failures with little remaining variant gap | Extra reasoning can never help there |
| `G_post` remains high beyond math | Equal-evidence Thinking advantage extends to additional task families | Same-weights reasoning mode causally creates the gap |
| Fine-grained tasks have few answer-safe `E*` items | The decomposition is not identifiable for most direct-answer tasks using this assay | These tasks have no evidence bottleneck |
| Negative / uncertain cross-task contrasts | Earlier expectations of math-selectivity must be weakened | Search subgroups until expected ordering appears |

A completed Stage 14C is valuable even if cross-task contrasts are null, source eligibility varies sharply, or some task families cannot be evaluated with a nonleaky oracle.

---

## 12. Causal and conceptual boundaries

1. **Intervening with `E*` establishes the effect of supplying that textual evidence under this protocol.** It does not uniquely isolate perception, retrieval, binding or inference.
2. A native-to-`E*` rescue is an **oracle-supply-responsive failure**, not automatically a directly observed native evidence-acquisition failure.
3. **`E*`-resistant != pure reasoning error**; do not assert the downstream mechanism without further interventions.
4. Separate **native causal visual retrieval** from attention, PPL sensitivity and late-mask necessity (earlier Claim 2).
5. `V -> text-sufficient` functional handoff (earlier Claim 3) is **not** newly demonstrated merely by `E*` cross-task gains. Stage 14C does not itself show a two-phase transition.
6. `I` vs `T` compares distinct deployed checkpoints/recipes. Do not claim `do(Thinking=on)` under constant weights/compute.
7. Benchmark and task class effects are subject to **difficulty, format, source composition, gold reliability, answer leakage, ceiling/floor and eligibility-selection** confounds.
8. Stage 14C does not prove the semantic-addressability hypothesis. Name removal / arbitrary-name rescue remains a *later causal test* if warranted.
9. No choice of post-hoc failed items or outcome-informed prompts may redefine an ostensibly confirmatory cohort.
10. Same-agent grading/review is not independent annotation reliability; all versioned decisions must remain auditable.

---

## 13. Artifact contract (suggested)

```text
outputs/stage14c/
  spec/
    stage14c_plan.md
    source_only_protocol.md
    frozen_sampling_and_contrasts.json
    model_and_recipe_identity.json
    scoring_and_missingness_spec.md
    diagnostic_authorization.json
  source/
    dataset_inventory.json
    cohort_manifest.jsonl
    estar_eligibility_manifest.jsonl
    evidence_atoms.jsonl
    source_qc_log.jsonl
    source_statistics.json
    source_exposure_audit.json
  raw/
    native/
    equal_evidence/
    optional_diagnostics/
  scoring/
    answer_extraction_raw.jsonl
    answer_review_versioned.jsonl
    scored_outcomes.jsonl
    technical_missingness.jsonl
  analysis/
    primary_results.json
    cross_task_contrasts.json
    complete_pair_transitions.json
    eligibility_and_coverage.json
    family_cluster_bootstrap.json
    missingness_bounds.json
    secondary_and_sensitivity.json
    optional_diagnostics.json
  figures/
    figure1_eligibility_map.png
    figure2_rescue_profile.png
    figure3_post_evidence_profile.png
    figure4_native_selectivity.png
    figure5_task_map.png
  audit/
    frozen_source_hashes.json
    preflight_validation.json
    condition_identity_audit.json
    artifact_catalog.json
    final_validation.json
    resource_accounting.json
  summaries/
    stage14c_primary_summary.md
    stage14c_final_summary.md
    next_stage_recommendation.md
```

All receipts must capture parent Stage 14A/14B hashes, code revision, and any amendments.

---

## 14. Suggested downstream continuation (requires new plan + approval)

- **Stage 14D:** compare 2B/4B/8B (and optional 32B) on **the same frozen tasks and valid `E*` subsets**, separately estimating `R_I(s,t)` and `G_post(s,t)`; begin with technical preflight because the prior 2B panel had high technical missingness.
- **Stage 14E:** characterize trace-time `E*` recovery, first-explicit-evidence events, text-state sufficiency, and whether visual content sensitivity truly coincides with acquisition. Compare state construction, derivation, priming, lossy verbalization without assuming the answer.
- **Stage 14F:** controlled causal intervention comparing **target-specific evidence recovery**, generic uncertainty-guided lookback, more reasoning, and fixed-period lookback at an explicitly matched budget. If semantic addressability emerges as a strong candidate, preregister named/unnamed/arbitrary-name-rescue interactions as a **separate** factorial sub-study.
- **Stage 14G:** external-model family replication or same-weights reasoning-toggle design if genuinely available.

**Core design principle for any eventual method:** target the missing **evidence state**, not visual attention magnitude or reasoning length alone. This remains a *hypothesis to test*, not an outcome of Stage 14C.

---

## 15. One-sentence objective

> **Establish, on source-frozen cross-task cohorts, how often supplying correct task-critical visual evidence rescues failures, how often failures and Thinking advantages persist under equal evidence, and whether these bottleneck profiles vary systematically across math, generic VQA and fine-grained visual tasks—without confusing those measurements with a causal explanation.**

**End of plan. STOP before launching Stage 14C.**
