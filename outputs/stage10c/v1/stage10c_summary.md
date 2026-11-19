# Stage10C — causal visual reopening

**Outcome D; full causal reopening + source-specificity gate: False.**

## Design and validity

16 independent natural problem/image trajectories were tested. The original16-case primary split contains8 MathVision and8 MathVerse cases; reserve executed: False. Selection reused the exact24-event Stage10B anchor-gap sensitivity; no native-correctness or intervention-effect selection. All gold B facts, matched equal-count controls and scoring rules were sealed before interventions. Exactly three fixed reserve-compatible technical cases passed all10 checks.

The model is pinned Qwen3-VL-2B-Thinking, BF16/TF32-off, eager language/SDPA vision, native preprocessing. Historical traces were sampled; the local Stage10C branches are greedy. Fresh unmasked greedy baselines were therefore generated, and no-op equality was checked against the corresponding unmasked greedy path, not against sampled historical suffixes. All branches share the original teacher-forced native prefix. PRE masks predict tokens[B−24,B); POST masks predict[B,B+24). All28 decoder layers use the previously validated standard image-key operator, with access restored at the24-token boundary. Earlier image-derived cache remains intact.

The behavioral endpoint scores the first atomic source-local B assertion represented by the frozen native evidence span in the64-token window[B,B+64). It does not require complete solution of a broad inventory or final benchmark answer. The broader B demand and complete native evidence span remain in the gold artifact. Scores were assigned from condition-blinded local text and frozen image-grounded rules; no independent human-rater claim is made. Teacher forcing measures mean NLL of the entire native B-evidence span, including wrong native assertions and spans extending beyond64 tokens. Thus NLL measures support for the native assertion and is interpreted with correctness strata.

## Primary paired endpoints

Equal trajectory weighting;4,000 paired bootstrap draws, seed920260927. Behavioral units are proportion differences; mechanistic units are nats/token. Adjusted intervals are98.75% marginal percentile intervals (Bonferroni family-wise95% across four endpoints).

| Endpoint | Point | Ordinary95% CI | Adjusted CI | Positive / negative / tied pairs |
|---|---:|---|---|---|
| P1 | 0.125000 | [-0.125, 0.375] | [-0.1875, 0.4375] | 3 / 1 / 12 |
| P2 | 0.399568 | [0.18758158813799694, 0.6451715175961457] | [0.1447122950033303, 0.7075964947749352] | 15 / 1 / 0 |
| P3 | 0.062500 | [-0.125, 0.25] | [-0.1875, 0.3125] | 2 / 1 / 13 |
| P4 | 0.177179 | [0.007899855353459447, 0.40493724480225357] | [-0.013300302934244316, 0.47188989148210186] | 13 / 3 / 0 |

P1=PRE accuracy−POST-all accuracy; P2=POST-all NLL−PRE NLL; P3=irrelevant accuracy−target accuracy; P4=target NLL−irrelevant NLL.

Frozen gate components: {'all_four_positive': True, 'both_dataset_reopening_positive': False, 'historical_faithful_specificity_positive': False, 'no_one_or_pair_dominance': False, 'technical_pass': True, 'precision_limited': True}. The plan's main gate uses positive directions with dataset, faithful-stratum, deletion and technical checks; intervals describe uncertainty. A point-direction pass is not an assertion that all adjusted intervals exclude zero.

| Dataset | n | P1 | P2 | P3 | P4 |
|---|---:|---:|---:|---:|---:|
| MathVision | 8 | 0.375000 | 0.220141 | 0.250000 | 0.096180 |
| MathVerse | 8 | -0.125000 | 0.578995 | -0.125000 | 0.258178 |

## Native strata and robustness

The preregistered source-faithful stratum uses the original sampled native64-token continuation, assessed before interventions. Fresh greedy baseline correctness is a separate sensitivity.

| Stratum | n | P1 | P2 | P3 | P4 |
|---|---:|---:|---:|---:|---:|
| historical_native | 8 | 0.250000 | 0.423326 | 0.000000 | 0.253119 |
| historical_wrong | 4 | -0.250000 | 0.513598 | 0.000000 | 0.170235 |
| historical_unresolved | 4 | 0.250000 | 0.238021 | 0.250000 | 0.032243 |
| fresh_greedy | 3 | 0.666667 | 0.185689 | 0.333333 | -0.042806 |

Minimum P1–P4 after deleting any one or any pair: [0.0, 0.2635282055070901, -0.07142857142857142, 0.044975504603173885]. Full deletion tables and target-type strata are in the inference JSON.

| Condition | Correct | Wrong | Unresolved | No local read | Reached64-token cap | EOS |
|---|---:|---:|---:|---:|---:|---:|
| NATIVE | 3 | 5 | 8 | 0 | 16 | 0 |
| PRE_ALL_OFF | 3 | 4 | 9 | 0 | 16 | 0 |
| POST_ALL_OFF | 1 | 3 | 12 | 0 | 16 | 0 |
| POST_TARGET_OFF | 2 | 5 | 9 | 0 | 16 | 0 |
| POST_IRRELEVANT_OFF | 3 | 5 | 8 | 0 | 16 | 0 |

The64-token cap is the intended local assay endpoint, not a claim that a final benchmark answer was completed. Free branches retain frozen absolute scoring coordinates even when content diverges.

## Interpretation and limits

Neither robust component passes. Do not promote causal reopening from this tested candidate cohort.

Read the endpoints separately: a positive native-span NLL effect indicates reduced support for the frozen native text, not necessarily loss of a correct local visual read. The dataset and faithful-stratum tables determine whether the behavioral evidence converges with that effect. The fresh unmasked greedy continuation resolves B correctly in 3/16 cases, whereas 8/16 original sampled native spans were source-faithful. This limited behavioral resolution under the fixed window constrains the interpretation of a failed gate; it is not evidence that causal reopening is impossible.

The result applies to this selected natural candidate cohort, model, fixed local budget and intervention. PRE is a reviewed terminal text suffix; the original paragraph annotations are coarse, and semantic reasoning status is not an independently established low-necessity state. Prior image-derived state and redundant pathways remain available. A null does not establish mechanism impossibility or diagnose its cause. No full A→B→A return cycle or universal alternation is tested. Stage10AR controlled4B transition, Stage4A source retargeting and Stage10B natural passive census remain separately supported evidence.

Reserve executed: False. Demand-swap executed: False. Conditional decisions: All four aggregate points are positive, but MathVerse behavioral reopening/source effects are negative, historically faithful behavioral specificity is zero, and one/pair deletion does not retain positive behavioral directions. This is directionally inconsistent across required checks, not a precision-only shortfall. Frozen reserve gate fails. Demand-swap and null-sink controls are ineligible. Preserve positive P2 NLL evidence, stop without new anchors, windows, models or trajectories.. No post-null anchor/window or model search.

## Resources and artifacts

Allocated GPU-hours: **0.1208**; peak simultaneous GPUs:2; all GPU jobs terminal. Accounting includes validation/startup/failures. No new benchmark-scale generation, download or tmux allocation. Eleven mandatory artifacts and four figure pairs are saved here; optional outputs appear only if executed, and the integrated fifth figure appears only for OutcomeA. Native evidence, raw blinded ratings, manifests, source hashes and Slurm receipts remain preserved. CPU collector125320 started without its intended dependency and failed an incomplete-queue assertion before review or analysis. Its evidence was preserved; bounded collection ran only after both GPU workers were verified complete. The scientific runs were unaffected.

## Exactly one recommendation

Stop the reopening branch and finalize the paper around the already-established visual-to-text transition plus dynamic source retargeting as a separate causal phenomenon.

**STOP:** no follow-on experiment launched.
