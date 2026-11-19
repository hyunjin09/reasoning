# Stage8B Block1: whole-trajectory success/failure — complete

Frozen 2026-09-19T07:25:53.341356+00:00. **Selected interpretation: no broad outcome-level retrieval difference established under the full prespecified controls (Outcome D).** This is a failure to establish a robust broad difference, not evidence of equivalence or absence of local retrieval failures.

Wrong answers have more raw retrieval episodes and greater raw tortuosity. Length/completion adjustment alone retains several retrieval effects, so those effects cannot all be described as explained by length/capping. Adding the prespecified input controls attenuates count, density and mean movement; all eleven fully adjusted primary intervals and all within-family simultaneous intervals include zero. No primary family meets the frozen joint-evidence criterion. The recommendation below follows the already approved Block2 direction; no new research action is launched.

## Cohort and frozen method

Exactly256 unique MathVision items/families from Block0:134 correct,105 wrong,17 unresolved. Scorable accuracy is134/239=56.07%; known-correct fraction of all256 is52.34%. No unresolved item is silently classified as wrong. Normal completions:133 correct/105 wrong (238); capped:1 correct/0 wrong/17 unresolved (18). Mean reasoning length is11,695 tokens for correct and16,705 for wrong; medians9,132 and14,690.

The native Qwen3-VL-2B-Thinking T=1.0/BF16 generations, local deterministic/blind-manual benchmark outcomes, detector threshold0.5478025980771918, gap4 episodes and pooled passive-feature scaling are unchanged. The local outcome adapter does not reproduce upstream GPT-4o extraction. All contrasts use items,4000 stratified item-bootstrap resamples,seed1234 and float64 statistics. No token/episode pseudoreplication, local L labels, new model run or causal intervention.

Effects below are wrong minus correct. Full controls are log reasoning length, completion, pooled subject/subtype, answer format, log question length and categorical difficulty. These are descriptive adjustments; reasoning length/completion may themselves follow reasoning dynamics. Raw standardized effects are Hedges g; adjusted standardized effects and all additional intervals are in the JSON/CSV artifacts.

## Primary results

Raw means and medians, with pointwise95% bootstrap intervals for Hedges g:

| Metric | n correct/wrong | Correct mean / median | Wrong mean / median | Hedges g [95% CI] |
|---|---:|---:|---:|---:|
| Episode count | 134/105 | 7.851 / 3.5 | 11.3 / 9 | 0.3175 [0.0515, 0.6129] |
| Episodes / 1,000 tokens | 134/105 | 1.727 / 0.4505 | 1.258 / 0.5266 | -0.1562 [-0.3409, 0.0879] |
| Active-token fraction | 134/105 | 0.007969 / 0.001294 | 0.004815 / 0.002101 | -0.1996 [-0.3686, 0.02732] |
| First retrieval token | 102/100 | 412.5 / 44 | 319 / 47.5 | -0.04933 [-0.2893, 0.223] |
| First retrieval fraction | 102/100 | 0.03686 / 0.006621 | 0.01697 / 0.003795 | -0.251 [-0.4613, 0.003869] |
| Median inter-episode gap | 89/90 | 175.1 / 23 | 82.17 / 30 | -0.2411 [-0.4078, 0.01877] |
| Recurrence count | 134/105 | 7.09 / 2.5 | 10.34 / 8 | 0.3031 [0.03903, 0.5998] |
| Episode fraction after .5 | 102/100 | 0.07114 / 0 | 0.04318 / 0 | -0.1913 [-0.442, 0.08355] |
| Episode fraction after .75 | 102/100 | 0.01692 / 0 | 0.01847 / 0 | 0.02822 [-0.2696, 0.2754] |
| Mean standardized movement | 134/105 | 1.027 / 0.9425 | 1.053 / 0.9907 | 0.116 [-0.1279, 0.3778] |
| Standardized tortuosity | 134/105 | 3699 / 3490 | 4854 / 4780 | 0.4549 [0.2062, 0.7203] |

Adjusted coefficients in original metric units. The first two intervals are pointwise; the last is simultaneous within the metric's frozen primary family:

| Metric | Length + completion [95% CI] | Full controls [95% CI] | Full family95% CI |
|---|---:|---:|---:|
| Episode count | 3.643 [0.6558, 6.563] | 1.095 [-1.948, 4.148] | [-2.545, 4.736] |
| Episodes / 1,000 tokens | 0.491 [0.05356, 0.9354] | 0.1472 [-0.3678, 0.6375] | [-0.4332, 0.7276] |
| Active-token fraction | 0.002028 [0.0001312, 0.004035] | 0.001167 [-0.001279, 0.003409] | [-0.001592, 0.003926] |
| First retrieval token | -245.9 [-848.1, 234.6] | -225.9 [-931.3, 360] | [-1091, 639.2] |
| First retrieval fraction | -0.01575 [-0.04109, 0.00488] | -0.01379 [-0.04437, 0.01152] | [-0.05133, 0.02375] |
| Median inter-episode gap | -117.3 [-262.3, -3.828] | -117.1 [-281.2, 5.537] | [-309.9, 75.63] |
| Recurrence count | 3.457 [0.5173, 6.349] | 0.9476 [-2.065, 3.958] | [-3.095, 4.99] |
| Episode fraction after .5 | -0.01624 [-0.06484, 0.02901] | -0.03058 [-0.08896, 0.0175] | [-0.1023, 0.04112] |
| Episode fraction after .75 | 0.00938 [-0.007859, 0.02745] | 0.007021 [-0.01312, 0.02667] | [-0.01955, 0.0336] |
| Mean standardized movement | 0.08331 [0.0346, 0.1324] | 0.02271 [-0.02178, 0.06904] | [-0.02935, 0.07476] |
| Standardized tortuosity | 49.72 [-372.1, 464.2] | -131 [-591.9, 357.2] | [-680.5, 418.4] |

**Amount:** raw count difference is+3.44 episodes (95% CI0.63–6.20). It persists after length/completion controls (+3.64,0.66–6.56), but falls to+1.10 (−1.95–4.15) with full controls. Raw density and active fraction point in the opposite direction from count; they turn positive after length control. The full family does not establish a coherent amount difference.

**Timing/recurrence:** count and recurrence are algebraically related and cannot count as independent confirming constructs. Full recurrence is+0.95 (−2.06–3.96); first timing and late fractions do not provide a robust complementary contrast. The median-gap estimate remains negative (−117 tokens), but its full pointwise interval is−281 to+6 and its family interval is−310 to+76. Loss of precision alone does not establish that covariates explain this estimate.

**Geometry:** raw tortuosity differs by+1,155 (522–1,794), but length/completion-adjusted difference is+50 (−372–464). Transition-normalized movement is higher after length/completion controls (+0.0833,0.0346–0.1324) and attenuates with full controls (+0.0227,−0.0218–0.0690). There is no joint adjusted geometry finding to support a retrieval-instability or source-routing claim.

Thus H1 is not established under the complete control set; H2 has narrower length-only evidence for some metrics but not a robust full-adjustment phenotype; H3 is not established. Outcome E (all apparent differences explained by length/completion) is too strong for the observed count and movement results. Neither a causal explanation nor equivalence is established.

## Robustness and limitations

Normal-completion raw differences remain: episode count+3.54 [0.70,6.19], tortuosity+1,177 [542,1,826]. Full normal-subset effects have the same point estimates as full all-scorable effects, up to numerical precision, and all their family intervals include zero. This is not independent confirmation: the only scorable capped item is correct, and its cap indicator isolates its contribution. There are no scored capped wrong items, so a within-cap outcome contrast is unavailable.

The frozen matching procedure yields64 correct/wrong pairs (128/239 scorable items). Standardized log-length imbalance decreases from0.580 to0.035; question-length imbalance from0.109 to−0.063. Matched count difference is+1.38 [−2.27,4.48], movement+0.00108 [−0.0529,0.0534], and tortuosity−33.6 [−625,498]. All primary matched intervals include zero. Matching conditions on selected pairs, with49 usable pairs for first/late timing and34 for median gap; it does not cover the entire cohort.

At gap0 and gap8, fully adjusted episode-count differences remain uncertain (+1.36 [−3.19,6.06] and+1.38 [−1.18,3.92]); recurrence and density are likewise uncertain. Gap0 median gap alone has a pointwise interval below zero (−110 [−266,−2.35]); gap4 and gap8 do not. Preserve this sensitivity result without promoting it into a broad finding. Removing the frozen low-displacement tail leaves tortuosity uncertain (+43.6 [−365,470]).

Timing is conditional on having enough detected episodes.32/134 correct and5/105 wrong items have no detected episode; first/late timing uses102/100 items, while median gap uses89/90. Missingness is reported, not imputed as no delay or no failure. Different group coverage, skewed distributions, heterogeneous inputs and finite sample uncertainty limit generalization. The detector measures passive retrieval activation, not a causal certificate of faithful reading.

## Completion and phase analyses

Completion comparisons retain all17 unresolved items. Capped versus normal raw episode count is7.83 versus9.32; density0.191 versus1.525 per1000 tokens; active fraction0.000703 versus0.006604; mean movement0.905 versus1.039; tortuosity7,391 versus4,196. Capped lengths span40,179–40,960 tokens and normal lengths211–38,876: **there is no length-range overlap**. Full adjusted cap coefficients are retained for transparency, but reversal of density/active-fraction signs is model-dependent extrapolation, not evidence of a cap-specific mechanism or outcome effect. Small n=18 and outcome/completion imbalance are central limitations.

Both outcome groups concentrate retrieval early. Phase1 density averages4.323 correct versus3.971 wrong; phase4 averages0.280 versus0.240. All four fully adjusted density and active-fraction intervals cross zero. Some secondary pointwise mean-R effects are positive (phases1,2,4); early movement is+0.0610 [0.00250,0.1231]. Late-minus-early movement is−0.0568 [−0.0980,−0.0152]. These remain descriptive phase comparisons without multiplicity confirmation or causal-onset inference. Secondary global net displacement and the fraction after0.25 also have pointwise differences; neither replaces the primary family decision.

## Exactly one recommendation for Block2

**Emphasize local-read success versus failure (L+ versus L−) at active task-required retrieval events in Block2, across both final-outcome groups, while retaining frozen event membership and eligibility.** Final-answer grouping did not yield a robust fully controlled phenotype and must not serve as a proxy for local visual-read correctness. This recommendation changes emphasis only; it does not select new events based on these contrasts. The Block2 protocol and local-read execution are not started in this action.

## Artifacts and verification

- [Outcome census](stage8b_block1_outcome_census.json), [unchanged episodes](stage8b_block1_retrieval_episode_table.parquet), [trajectory metrics](stage8b_block1_trajectory_metrics.csv).
- [Raw contrasts](stage8b_block1_correct_wrong_raw.json), [adjusted contrasts/robustness](stage8b_block1_correct_wrong_adjusted.json), [primary-effects CSV](stage8b_block1_primary_effects.csv).
- [Completion analysis](stage8b_block1_completion_analysis.json), [phase analysis](stage8b_block1_phase_analysis.json).
- Figures: [density](figures/figure1_density.png), [cumulative episodes](figures/figure2_cumulative.png), [intervals/recurrence](figures/figure3_intervals_recurrence.png), [geometry](figures/figure4_geometry.png), [adjusted effects](figures/figure5_adjusted_effects.png); each also has a same-name PDF. Distribution figures use a symmetric-log y-axis; curve bands and effect bars are pointwise item intervals.
- [Analysis checks](audit/analysis_acceptance_checks.json):71/71 tasks; all frozen source/input/Block0 hashes valid; original episode table byte-identical;44 independent NumPy OLS point estimates agree within1.46e−10;22 group mean/median checks pass;4000 valid replicates for every full/normal primary family; five figures visually inspected. Both Slurm workers passed actual-device CPU/GPU parity. Six pre-execution unit tests are retained in `audit/unit_tests.log`.
- [Execution provenance](audit/node06_result_provenance_v3.json), [resource receipt](audit/resource_completion_v3.json). Rank1 job118035 completed35 tasks on node06 in29s and was preserved. Node03 pending job118034 was cancelled at zero runtime. Rank0 replacement118038 completed36 tasks on node06 in11s. Both GPUs released at their own shard exits:40 allocated GPU-seconds, approximately0.0111 GPU-hours. CPU-only assembly118039 completed in17s. Original pending job118016 and prior placement freezes remain historical evidence. No active allocation, tmux session or additional job remains.

Block1 is complete. The frozen recommendation is the handoff; no Block2 analysis, local L inspection, cohort expansion or intervention was performed.
