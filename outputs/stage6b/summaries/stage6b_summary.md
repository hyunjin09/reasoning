# Stage6B summary

**Complete: 21/21 technical criteria pass. The broad failure-mechanism claims are not established.** All work used the existing two RTX A6000 GPUs in Slurm 110860/node 03/tmux 9; no new allocation or dataset download.

This stage tests whether visual engagement and movement track task-demanded causal evidence, and whether degraded evidence produces mirage or source-tracking failures.

W2 and W8 suppress source contributions at the last two or eight query positions. VSD measures the resulting change in the predeclared mean candidate log-probability contrast, in nats per token; it measures local source necessity rather than the time of initial acquisition.

| Completed component | Coverage |
|---|---|
| C2 factorial source assay |31 families, 124 events |
| C1 fixed-prefix stress |109 bases, 1199 condition events |
| C1 exact dynamics |20 bases, 78 anchors, 34 primary transitions, 0 matched holds, 19 selected refreshes |
| C1 native passive / geometry |1199 traces, 14906 endpoints; manual and programmatic scopes kept separate |
| C3 object stress |63 present +73 absent families, 660 native readouts |
| C4 natural validation |10 cases +10 controls, 358 endpoints including 45 predeclared wrong-claim anchors |

## Findings

C2 focal-source necessity increases with focal demand: confirmation W2 median 1.426, 18/19 positive, Holm p=.000793; W8 median 1.063, 17/19 positive, p=.001099. The disjoint-ROI sensitivity remains positive 14/14. Expected alignment attention/QK effects and matched high-attention yield fail the full gate (only 1 eligible confirmation match). All four cells demand some visual source; this does not establish global image independence. [Evidence](../c2_alignment_retrieval/claim_assessment.json).

C1 strong and mask grounding losses survive matched sham controls: held-out sham-minus-stress VSD medians 1.688 and 2.719; 57/62 and 58/62 bases are positive. All 62 confirmation bases validate the semantic counterfactual beyond render sham. There are 9 strict mirage candidates across 8/62 bases (7 independent source groups), and all 9 also collapse under W8. The post-label preferences are 4 benign and 5 error-associated; these are fixed-prefix candidate preferences, not newly generated native hallucinations. Continuous divergence does not satisfy the full 75% positive-base robustness rule, so the broad mirage claim remains unsupported. [Evidence](../c1_mirage/claim_assessment.json).

Dynamics provide 9 held-out demand-aligned switches and 7 mixed comparisons in the selected transition/refresh set. The minimum panel gate fails. There is no matched-hold test of wandering, no strictly identified fixation in the selected panel, and no cohort failure-rate estimate. Selected numeric claims are correct even when geometric roles are wrong; the numeric contrast cannot establish causation of geometric errors. First observed dominance is not an acquisition time. [Evidence](../c1_dynamics/demand_coupling.json).

Native geometry uses 666 manually reviewed intact discovery endpoints from 47 bases in 9 source groups. PC1/PC2 explain 36.1%/19.6% of discovery variance. Confirmation is projection-only; original 11-dimensional path metrics are also saved. Extraction covers 1766 manual-prefix, 18 other reviewed and 13122 conservative programmatic endpoints; 125216 unreviewed unresolved spans remain outside the labeled endpoint panel, and 292 traces have zero eligible endpoints. Sparse causal coverage prevents a cohort-level superiority claim for demand coupling. [Evidence](../trajectory/pca_discovery.json).

In the frozen native traces, mask conditions average 8308 generated tokens versus 4738 for intact. 5/109 mask traces and 3/109 sham-mask traces reach the cap; all 109 intact traces finish with EOS. These are descriptive native adaptations, not causal failure-mode labels. [Native condition summary](../c1_mirage/native_condition_summary.json).

C3 does not pass the full replication gate for sham-controlled target-VSD degradation or continuous divergence. There are 4 held-out mirage-like candidates. Across 63 present-object bases, native Yes answers number 61 for intact, 50 for strong, 41 for mask and 0 for no-image. Each condition uses its own native prefix; final-readout W2 does not measure earlier acquisition. Mask+yes is not automatically hallucination. One absent-reference yes remains an unresolved stools/chairs category boundary, and neither tested distractor shows the joint error-promoting direction. [Evidence](../c3_object_stress/replication_assessment.json).

C4 reports matched passive effect sizes and individual cases only. In the 5 confirmation pairs, visual-mass/sink/entropy directions match the frozen controlled descriptor in 1/5, 2/5 and 3/5 pairs; all three mean-effect confidence intervals include zero. Its wrong-claim anchors do not provide the missing truth-oriented causal source contrasts. Global descriptor trends do not establish strict mirage, wandering or fixation replication. No natural cohort extension or new prevalence claim was made. [Cases and controls](../c4_natural_validation/individual_cases.md).

Across 8 strict-candidate bases in 7 source groups, sink mass is lower than intact by a mean 0.0842. The signed candidate-minus-intact 95% bootstrap interval is[-0.1148, -0.0471]. After the declared discovery-only control for global visual mass and entropy, the signed mean is -0.0628, with interval[-0.0883, -0.0316]. These selected-case associations do not identify sink mediation or a causal behavioral prediction; the future-sink gate remains closed. [Sink statistics](../sink/sink_descriptive_statistics.json).

Dataset and leave-one-dataset analyses preserve frozen thresholds. Grounding losses remain robust in every leave-one-dataset-out comparison. Attention divergence passes the secondary MathVision subgroup gate (19/21 positive bases, 13 source groups, Holm p=.0281), but not MathVerse/MathVista or any leave-one-dataset-out gate. Validated template-family labels are absent, so template-family robustness remains unidentified. No surrogate, rescue, training, representation substitution, head search or sink intervention was run.

## Validation and execution limits

Exact native/no-op/passive controls, independent source arithmetic, frozen splits, readout orientation and mechanics-to-primary replay checks pass. BF16 weights and the canonical maximum 2048-token chunk/8-query barrier path are preserved. A long-prefix OOM required CPU residency for inactive caches and expandable allocator segments; the focused allocator comparison matched 18 common-prefix logits, and 10 long-context endpoints matched fresh canonical roots and all cached layers on both GPUs. Failed attempts remain available. [Audit](../audit/causal_score_replay.json) · [Resources](../audit/resource_summary.json).

Two cache-path exceptions are recorded in the resource audit: early Matplotlib imports may have used the default external cache, and pytest updated the project-root cache outside the allowed write list. Later plotting uses the allowed project cache, and the documented test reproduction command specifies an allowed cache directory. The existing pytest cache was left untouched after read-only verification; no external cache path was inspected or cleaned. [Cache audit](../audit/cache_configuration.json).

## Next stage

**GO — Cohort/Assay Repair.** Repair the primary dynamic demand/readout panel on the existing C1 cohort: resolve compound subgoals and obtain valid paired transition/hold and error-oriented readouts. This addresses an identification gap; retain all current negative and mixed findings. No failure class meets the 24-event rescue gate, C2 does not strongly establish alignment/retrieval dissociation, and natural sample size is not the main missing evidence. [One recommendation](next_stage_recommendation.md).

Stage6B stops here. [Technical acceptance](stage6b_acceptance.json) · [All 24 figure categories](../analysis/figures/index.md) · [Paper-claim assessment](../analysis/paper_claim_assessment.json) · [Rescue readiness](../analysis/rescue_readiness.json).
