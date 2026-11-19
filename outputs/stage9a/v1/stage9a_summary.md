# Stage 9A — completed; stop at the regime-validation gate

The proposed Thinking-specific recurrent visual-access regime is **not supported** in this 128-family native comparison. None of the four predeclared Thinking−CoT primary contrasts is positive at the required confidence. Thinking has fewer frozen-proxy episodes per 1,000 reasoning tokens; the other primary intervals include zero. Sparse matched-length and causal support prevents an equivalence conclusion. The secondary accuracy advantage does not establish the proposed mechanism.

**Exactly one recommendation:** Stop the Stage 9 bottleneck/bypass branch here and retain the existing reasoning-conditioned dynamic visual-retrieval framing. Execution stopped after the approved Stage 9A validation; no Stage 9B/C or other follow-on experiment was launched.

## Execution and measurement

All 384 native trajectories are preserved: 128 per arm, 128 distinct conservative families from the unused MathVision reserve, 15 subjects, difficulty 1–5, 60 multiple-choice and 68 free-response items. The 2B Instruct/Thinking checkpoints used BF16, temperature 1, top_p 0.95, top_k 20, unchanged image preprocessing, and the 40,960-token cap. Direct and CoT share the Instruct template; only CoT appends the frozen instruction. Thinking retains its native `<think>` template. “Direct” means no added CoT instruction; it did not force short answers or suppress spontaneous reasoning.

All native artifact hashes were reverified. The detector, threshold 0.5478025980771918, layers 19–22 and max-over-head/layer aggregation were unchanged. First-token undefined detector/QK values are excluded. Primary native reasoning spans and common non-special full-assistant sensitivity are both reported. Bootstrap units are whole families, 4000 resamples; four primary 98.75% intervals, secondary 95%, minimum 20 contributing families.

| Arm | Mean / median reasoning tokens | Capped | Uncertain span boundaries | Reviewed demands / covered trajectories |
|---|---:|---:|---:|---:|
| Direct | 15334 / 8553 | 34/128 | 52/128 | 176 / 77 |
| Prompted CoT | 11746 / 6188 | 24/128 | 51/128 | 181 / 74 |
| Thinking | 18493 / 14492 | 14/128 | 11/128 | 182 / 77 |

The frozen CoT instruction did not increase mean or median trace length relative to Direct in this cohort. This is a comparison of one approved prompting protocol with native Thinking, not evidence about every possible CoT elicitation method.

## Primary paired contrasts

Effects below are Thinking minus prompted CoT. Each metric uses its actual paired overlap; missing demand annotations and no-episode denominators are not zero.

| Endpoint | Paired families | Thinking / CoT mean on paired support | Effect | 98.75% CI |
|---|---:|---:|---:|---:|
| Demand alignment ±16 | 55 | 0.330 / 0.362 | -0.032 | [-0.203, 0.142] |
| Late episode fraction | 94 | 0.041 / 0.050 | -0.008 | [-0.055, 0.030] |
| Episodes / 1,000 tokens | 128 | 2.437 / 5.122 | -2.685 | [-4.533, -1.097] |
| Long-gap re-engagement | 94 | 0.140 / 0.113 | 0.027 | [-0.019, 0.069] |

The exploratory raw episode-count contrast is positive, while episodes per 1,000 tokens is negative. A greater total count in a longer trace is therefore insufficient evidence for the proposed recurrent regime. The common-assistant and normal-completion sensitivities preserve the negative density result. CoT−Direct primary-endpoint 95% intervals all include zero.

## Length, demand specificity and raw routing controls

Only **9/128** same-item pairs satisfy the unchanged |Δlog length|≤.15 caliper. The matched endpoint supports are 4/7/9/7 families; no matched inferential interval is issued. No caliper widening or replacement pairing was used. Family-clustered OLS adjusts for arm, log length, completion, subject, difficulty, answer format and question length. These are adjusted associations: generated length/completion are post-checkpoint variables, not randomized controls.

| Adjusted Thinking−CoT coefficient | Effect | 98.75% CI | Families |
|---|---:|---:|---:|
| Demand alignment ±16 | 0.163 | [-0.032, 0.343] | 102 |
| Late episode fraction | 0.005 | [-0.032, 0.040] | 123 |
| Episodes / 1,000 tokens | 2.130 | [-0.437, 4.605] | 128 |
| Long-gap re-engagement | -0.014 | [-0.065, 0.037] | 123 |

All original regression designs have full column rank, and all 4000 bootstraps yield an identifiable Thinking−CoT coefficient; resampled category-rank losses are recorded. No adjusted primary interval is wholly positive.

539/700 explicit-demand nominations were accepted, 126 rejected and 35 unknown, after review of source images and local text. The 539 accepted events cover 102 distinct families and 228 trajectories; 114 trajectories had no nominated phrase. This is bounded explicit-phrase coverage, not an exhaustive demand census. All annotations were completed by the main Codex annotator, not independent human reviewers. Arm IDs, gold/correctness, routing and causal effects were masked; prose style can still reveal the arm.

| Arm | Demand ±16 | Circular-shift control | Demand minus shift, 95% CI |
|---|---:|---:|---:|
| Direct | 0.355 | 0.054 | 0.301 [0.205, 0.405] |
| Prompted CoT | 0.316 | 0.092 | 0.225 [0.137, 0.318] |
| Thinking | 0.368 | 0.039 | 0.329 [0.242, 0.418] |

Demand-associated retrieval exceeds circular-shift controls in all three arms, but its paired Thinking−CoT difference is 0.041, 95% CI [-0.101, 0.183]. It does not establish Thinking-specific demand alignment. Unpaired arm means above and paired P1 means differ because annotation overlap differs. Reviewed non-demand controls, onset-only alignment, ±32 windows and full-window edge sensitivities are retained. Non-demand paired support is particularly sparse; unknowns are never used as negative controls.

Raw visual attention/QK channels and continuous detector score are also lower for Thinking on the unadjusted family comparison. For example, the mean of the frozen max-aggregated visual-mass channel is 0.0787 versus 0.1134, and mean R is 0.2188 versus 0.2537 (Thinking/CoT). These are aggregation-specific observations, not calibrated probabilities of visual causality. Per-token spatial focus/entropy and reviewed target/donor/residual source-partition diagnostics accompany the detector. Spatial entropy is not labeled semantic-source entropy.

The negative density contrast persists in both answer formats and in every leave-one-subject-out mean (range −3.076 to −2.210 episodes/1,000). Fine problem-type, visual-density and entity-count metadata are unknown for all 128 items; those fields cannot establish robustness. Subject/category is the available problem-subtype proxy. Most individual subjects lack 20-family support.

## Frozen causal validation

All **50/50** eligible events were replayed: Direct 16, CoT 16, Thinking 18, at most one event per family/arm. Selection used only reviewed demand, local source/readout eligibility and stable hashes before any measurements. All 610 source/readout nominations were reviewed; the final bounded inventory yielded 86 eligible demands before the one-family/arm selection. Numeric-boundary and ROI-coordinate repairs, and the rejection of an article mistaken for a vertex label, were preserved before the freeze.

Tests use the exact native token prefix and next local evidence string, with same-image different-content Values copied into either the demanded or irrelevant region at layers 19–22 under native selected-layer routing. Original versus donor-counterfactual strings are scored by mean token log probability. Positive effect means a donor-semantic preference shift. Self/sham must reproduce native logits exactly. This is source-local Value validation, not a pixel counterfactual or an all-path visual-causality test.

| Arm | Events | Target effect | Irrelevant effect | Target−irrelevant | Positive target−irrelevant events |
|---|---:|---:|---:|---:|---:|
| Direct | 16 | 3.15488 | 0.00510 | 3.14978 | 16 |
| Prompted CoT | 16 | 2.25032 | -0.01097 | 2.26129 | 15 |
| Thinking | 18 | 3.11974 | 0.03282 | 3.08692 | 18 |

The paired Thinking−CoT target-minus-irrelevant effect is 0.74995 across 12 overlapping families; CI: not estimable (<20 families). All arm-specific samples fall below both the 24-event feasibility aim and 20-family inference threshold. These results cannot establish a robust causal arm difference. Eligibility is limited to the implemented clear discrete-content assay, not all possible visual events.

Pooling arms with equal family weight gives target-minus-irrelevant 2.85239, 95% CI [2.06815, 3.65862], across 26 families. This pooled validation does not test Thinking specificity. Native-prefix passive features are exact in 50/50 events; maximum absolute difference 0.0. Capture and self/sham logits are exact at every scored query; sham semantic effects are exactly zero. The raw FP64 JS expression leaves at most 5.50e-17 signed roundoff; raw values are preserved, with a 64-machine-epsilon aggregation tolerance and unchanged mandatory exact-logit/score checks. Optional alphaV/post-WO and source-selectivity measurements are saved on these 50 first queries only.

Donors retain their native positional/contextual information. Irrelevant controls match token shape/cardinality and minimize ink; they are not Value-norm or visual-content matched. Original and counterfactual strings are teacher-forced from the same original prefix. At each query, every intervention uses the same unperturbed history for that candidate; intervention-altered caches do not propagate. Final-answer accuracy never substitutes for the local readout.

## Secondary accuracy

All 384 extractions received masked review. The unchanged local Qwen/MathVision adapter uses bounded numeric equivalence at 1e−6 and no external judge. Formatting/units and superseded intermediate answers were corrected by literal text review before gold comparison. Raw-adapter scores remain available. Unscorable cases receive no credit in the all 128 denominator and remain distinct from known wrong answers.

| Arm | Reviewed correct / wrong / unscorable | All-example accuracy | Scorable-only accuracy | Raw-adapter all-example accuracy |
|---|---:|---:|---:|---:|
| Direct | 32 / 66 / 30 | 25.00% | 32.65% | 13.28% |
| Prompted CoT | 38 / 68 / 22 | 29.69% | 35.85% | 19.53% |
| Thinking | 58 / 57 / 13 | 45.31% | 50.43% | 40.62% |

Thinking−CoT reviewed no-credit accuracy is +15.63 percentage points (secondary 95% paired CI +7.03 to +23.44). Accuracy is a separate outcome and does not override the failed primary regime gate.

## Decision gates and stopping boundary

| Required criterion | Result |
|---|---|
| At least two positive primary Thinking−CoT effects | Not met: 0/4 |
| At least one survives length control | Not established; 9 matched pairs, all adjusted primary CIs include zero |
| Demand-specific re-engagement | Supported within arms; Thinking-specific advantage not established |
| Causal support for part of the arm difference | Insufficient eligible independent support |
| Not driven by one subtype | No positive primary phenotype to certify; negative density broad across available categories |

This is a negative result for advancing the proposed native-regime story, with unresolved matching/causal precision and incomplete fine-subtype coverage. It does not show computational equivalence, absence of visual retrieval, absence of all Thinking advantages, or the cause of the accuracy difference. No additional benchmark, prompt, threshold or model was tried to rescue the hypothesis.

## Resources and evidence

Native trajectories contain 5,976,205 generated tokens and 70.24 measured inference GPU-hours. Causal event execution adds 1.40 GPU-hours, excluding model startup, with peak allocated VRAM 19.60 GiB. GPU workers 121562/121563/121564 used one A6000 each on node06. CPU-only 121568 ran on node03 for 9m 02s; pending CPU-only 121566 was cancelled before work and moved due host-memory capacity. Slurm accounting storage is disabled, so measured runtimes and captured job/worker receipts are retained instead of an invented billing total. Annotation burden: 700 semantic nominations, 610 local source/readout nominations, 128 source images, 50 sets of source/donor/control crops, and 384 answer extractions; no human annotation-hour estimate.

The native generation config is preserved. `stage9a_generation_config_node07.json` is the actual execution-config identity after the documented resource amendment; its scientific settings match the original. All workers release allocations when their bounded queues end; final release status is in `audit/final_validation.json`.

The 13 plan-required artifacts are in this directory. Supporting evidence includes:

- [All raw hashes verified](audit/all_native_hashes_verified.json)
- [Frozen semantic review](annotations/semantic_review_complete.json)
- [Frozen source/readout selection](annotations/causal_selection_frozen.json)
- [Masked extraction review](annotations/answer_extraction_review_frozen.json)
- [Time/source/support diagnostics](audit/sensitivity_diagnostics.json)
- [Primary and controlled effects](stage9a_primary_effects.json)
- [Causal validation](stage9a_causal_validation.json)
- [Secondary accuracy](stage9a_accuracy_secondary.json)

Figures (PNG and PDF):

1. [All-family access trajectories](figures/figure1_visual_access_trajectories.png)
2. [Recurrence and late access](figures/figure2_recurrence_and_late_access.png)
3. [Demand alignment](figures/figure3_demand_alignment.png)
4. [Length controls](figures/figure4_length_controls.png)
5. [Causal source validation](figures/figure5_causal_source_validation.png)

**STOP.** The authorized Stage 9A action is complete; the recommendation is not a new experiment authorization.
