# Stage11A — Visual-evidence bottleneck census

Decision: **NO_GO**. Eligible evidence sets: 61/128 (47.7%; 95% CI 39.1–56.2%). The primary Thinking-correct / CoT-failed subset contains 12 independently matched families; 4 have a unique nonmixed localization.

This is a descriptive census of explicit-demand evidence recovery and observable native text. It does not establish why Thinking succeeds or identify hidden-state encoding. All128 original families and384 native trajectories were preserved.

## Design and review

Two independent model-agent passes inspected all128 image/question packets before mode correctness was opened. A common evidence proposal received two sufficiency checks; corrections and exclusions were resolved prospectively. Only1–4 image-derived facts sufficient with the original question were eligible. The original proposal, raw reviews and repair history remain available.

Eligibility counts: `{'NO_VISUAL_BOTTLENECK': 33, 'E_STAR_ELIGIBLE': 61, 'E_STAR_TOO_LARGE': 32, 'E_STAR_AMBIGUOUS': 1, 'ANNOTATION_UNRESOLVED': 1}`. All eligible native trajectories were annotated. Explicit probes cover 61 families ×3 modes, capped at512 new tokens. The same image, semantic request, item seed, preprocessing and Stage9A mode templates were used with the pinned Qwen3-VL-2B BF16 checkpoints. No benchmark baselines were regenerated.

Native annotation saw one anonymized reasoning trace at a time, with final correctness, other modes and probe output withheld. Writing style can reveal the mode, and prior reviewer project exposure cannot be erased. Probe annotations were sealed before joining the existing reviewed native answer labels. These are independent model-agent passes, not independent human reliability measurements. A versioned workload amendment assigned 101/103/75 reviews to the two independent reviewers and main reviewer while preserving all 96 shared agreement reviews. Historical assignments and raw reviews remain unchanged.

## Primary endpoints

| Mode | Explicit probe: all facts | Native text: sufficient facts | Native final correct | Failure given sufficient native facts |
|---|---|---|---|---|
| instruct_direct | 18/61 (29.5%; 95% CI 18.0–41.0%) | 10/61 (16.4%; 95% CI 8.2–26.2%) | 14/61 (23.0%; 95% CI 13.1–34.4%) | 4/10 (40.0%; 95% CI 10.0–70.0%) |
| instruct_cot | 18/61 (29.5%; 95% CI 18.0–41.0%) | 11/61 (18.0%; 95% CI 8.2–27.9%) | 17/61 (27.9%; 95% CI 16.4–39.3%) | 3/11 (27.3%; 95% CI 0.0–54.5%) |
| thinking | 16/61 (26.2%; 95% CI 16.4–37.7%) | 13/61 (21.3%; 95% CI 11.5–31.2%) | 25/61 (41.0%; 95% CI 29.5–52.5%) | 1/13 (7.7%; 95% CI 0.0–23.1%) |

Probe rates use only probed eligible families; native rates use all eligible families. Figure2 and the matched-subset inference use the same probed-family denominator for all three measurements. Error intervals use4000 family bootstrap draws, fixed seed1120260928. Families, not atoms or tokens, are independent units.

The primary failed-answer endpoint includes valid wrong answers and no valid final; both are preserved separately. No valid final is never itself labeled a visual error. Wrong-only rates given sufficient native evidence: instruct_direct: 4/10 (40.0%; 95% CI 10.0–70.0%); instruct_cot: 2/11 (18.2%; 95% CI 0.0–45.5%); thinking: 0/13 (0.0%; 95% CI 0.0–0.0%).

Fixed512-token probe cap reached: instruct_cot: 24/61; instruct_direct: 0/61; thinking: 57/61. All visible response text, including Thinking reasoning, was scored. These unequal cap-hit rates materially limit any claim about relative evidence-recovery capability beyond this exact prompt and token budget.

## Matched Thinking–CoT localization

| Direction | Families | Availability gain A | Native-access gain B | Downstream gain C | Mixed D |
|---|---:|---:|---:|---:|---:|
| Thinking correct / CoT failed | 12 | 1 | 1 | 2 | 8 |
| CoT correct / Thinking failed | 4 | 0 | 0 | 0 | 4 |

Overlapping localization predicates stay mixed, with all underlying flags retained. A probe-inaccessible result plus correct sufficient native evidence is not forced into a single bottleneck. N5 (not externalized) stays distinct from observable absence N0.

Paired Thinking minus CoT differences on matched families:
- probe: -0.0328, 95% CI [-0.14754098360655737, 0.08196721311475409]; paired positive/negative directions 6/8; descriptive exact McNemar p=0.7905.
- native: 0.0328, 95% CI [-0.03278688524590164, 0.11475409836065574]; paired positive/negative directions 4/2; descriptive exact McNemar p=0.6875.
- final: 0.1311, 95% CI [0.0, 0.2459016393442623]; paired positive/negative directions 12/4; descriptive exact McNemar p=0.07681.

Subject, evidence type, atom count, reasoning length and evidence timing are descriptive secondary summaries in the inference/discordance artifacts. They do not introduce additional primary hypotheses. Evidence timings are quote-based annotation positions where available, not causal read times. A first-sufficient time assembled from correct quotes does not certify a consistently correct evidence state later in a conflicting N4 trace.

## Agreement and feasibility

Native fine-state agreement: `{'n': 96, 'raw': 0.9270833333333334, 'kappa': 0.8859276863011374, 'annotator_a_counts': {'N4': 48, 'N1': 2, 'N3': 29, 'N2': 17}, 'annotator_b_counts': {'N4': 45, 'N1': 3, 'N3': 30, 'N2': 17, 'N0': 1}, 'chance_agreement': 0.3607855902777778}`. Coarse agreement (sufficient / observable insufficient / not externalized): `{'n': 96, 'raw': 1.0, 'kappa': 1.0, 'annotator_a_counts': {'OBSERVABLE_INSUFFICIENT': 79, 'CORRECT_SUFFICIENT': 17}, 'annotator_b_counts': {'OBSERVABLE_INSUFFICIENT': 79, 'CORRECT_SUFFICIENT': 17}, 'chance_agreement': 0.7085503472222222}`. Fine-grained proportions promotable: **True**.

Sufficiency on the fixed agreement families: `{'n': 32, 'raw': 0.90625, 'kappa': 0.6129032258064516, 'annotator_a_counts': {'SUFFICIENT': 27, 'INSUFFICIENT': 5}, 'annotator_b_counts': {'SUFFICIENT': 28, 'INSUFFICIENT': 4}, 'chance_agreement': 0.7578125}`. Localization rule agreement: `{'n': 32, 'raw': 1.0, 'kappa': 1.0, 'annotator_a_counts': {'CONCORDANT:NOT_DISCORDANT': 23, 'THINKING_GAIN:D': 4, 'COT_GAIN:D': 3, 'THINKING_GAIN:B': 1, 'THINKING_GAIN:C': 1}, 'annotator_b_counts': {'CONCORDANT:NOT_DISCORDANT': 23, 'THINKING_GAIN:D': 4, 'COT_GAIN:D': 3, 'THINKING_GAIN:B': 1, 'THINKING_GAIN:C': 1}, 'chance_agreement': 0.54296875}`. Raw disagreements and their adjudication remain preserved.

Feasibility components: eligible=61; forward discordant=12; informative=4; CoT candidate failure profile counts={'P1': 34, 'P2': 7, 'P3': 1}; mixed fraction=0.667; native gate kappa=0.8859276863011374.

The frozen thresholds were not relaxed after outcomes. The decision incorporates independent-family support, category spread, agreement and mixed-state burden.

The decisive minimum-support gate fails: only4 uniquely informative Thinking-gain families versus the required8. Eligibility and annotation agreement pass. Strong GO also lacks16 forward discordances and a second CoT failure category with8 families. This is insufficient clean localization, not evidence that Thinking has no performance advantage or that no bottleneck mechanism exists.

## Interpretation limits

Explicit probing changes demand and is limited to512 generated tokens. Probe failure may reflect that prompt/budget; it does not establish that evidence was not encoded. Correct native text does not prove all relevant hidden states are equivalent, and missing text does not prove missing internal access. Results apply to the exact Stage9A CoT prompt and selected evidence-identifiable MathVision families. E* exclusions constrain generalization. Native final correctness is not a substitute for evidence fidelity.

## Optional pilot and resources

No optional Equal-Evidence pilot was run because the frozen feasibility gate did not authorize it.

Total allocated GPU-hours: **0.4503**, including startup and failures; peak simultaneous GPUs: 2. All GPU jobs are terminal. The hard2.5GPU-hour cap was respected. 183 short probes generated 54393 tokens; 81 hit the fixed cap. Annotation workload is recorded as passes/traces, not invented human-hour estimates.

## Exactly one recommendation

Stop the bottleneck branch and finalize the paper around the already-established causal retrieval and visual-to-text lifecycle claims.

Stage11B and every new research stage remain unlaunched. Required tables, manifests, annotation reviews, inference and four PNG/PDF figures are stored in this directory.
