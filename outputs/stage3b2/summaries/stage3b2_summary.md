# Stage 3B.2 summary — Counterfactual future visual-source switching

## Outcome

**Technical status: PASS (16/16 acceptance criteria).**

**Recommendation: GO — Layer-wise visual-to-reasoning transfer analysis.**

Switching only future all-visual-position K/V from the original image to the counterfactual image, while retaining recipient token history and directly replacing no nonvisual state, moved evidence preference toward the donor fact in both directions for 49/49 independent bases at both `E_d−1` and `E_d`. Median unnormalized BRI was 12.0118 at `E_d−1` (95% bootstrap CI 10.7909–13.0429) and 9.0923 at `E_d` (7.5086–10.4388).

This supports causal control by evidence-specific future visual content immediately before, and at, the frozen teacher-forced evidence decision. It does not identify an ROI, layer, module, head, path, or Q/R carrier.

## Frozen cohort and decision coordinate

- Primary unit: 49 unique frozen Stage 3A base problems (45 local numeric-label edits; 4 structural edits).
- `E_d`: first token at which the frozen original and counterfactual evidence continuations diverge after their longest common token prefix.
- All 49 annotations were manually audited before causal scoring; attention and causal scores were not used for acceptance or checkpoint placement.
- Twelve candidate leads exactly follow the baseline trace from E0. Thirty-seven use the already-frozen Stage 3A semantic teacher-forced evidence lead. Therefore, for those 37, `E_d` is a controlled candidate-decision coordinate—not the exact natural free-running decision time.
- Schedule: 588 unique base-checkpoint pairs, spanning generation start, normalized progress, `E_d−64…E_d−1`, and `E_d` where available.

## Intervention and controls

At switch index `k`, the query predicting generated token `y_k` and all later queries use donor post-RoPE visual K and projected V at all visual prompt positions in all 36 language layers. Recipient token identities are fixed, and no nonvisual K/V entry or query is copied from the donor. No query before `k` is switched. States computed after `k` may change downstream as a consequence of the visual-source intervention; that propagation is part of the tested effect, not a direct nonvisual patch.

Every checkpoint includes no-switch O+O/C+C, self O→O/C→C, O-history→C-vision, C-history→O-vision, and O-history→sham-vision controls. Primary scoring is length-normalized teacher-forced evidence preference; unnormalized BRI is primary and the full-gap normalized BRI is secondary.

## Validation

The corrected three-base smoke gate passed all 10 checks, with an `E_d` median absolute sham/target ratio of 0.009146. The earlier custom-attention-name smoke was preserved as invalid evidence: changing the attention implementation name altered causal-mask construction. The validated implementation keeps the model's `eager` configuration and locally overrides only the eager attention operation.

All 588 full-cohort switch audits passed; all self switches were exact; all scores were finite. No-switch divergent-suffix replay was bit-exact for 48/49 bases and within `1e-6` for 49/49. Base 126 was the sole bit-level exception: identical candidate IDs with maximum absolute log-probability difference 2.31e-07.

Seven A5000 primary shards and seven A5000 rollout shards completed. Peak primary allocated GPU memory was 10.21 GiB; rollout peak was 9.91 GiB. Nineteen Stage 3B.2 tests passed, and 9/9 required figures were produced.

## Primary causal results

- Generation start: median BRI 12.1839; median normalized BRI 0.9846; bidirectional 49/49.
- `E_d−1`: O→C median shift 11.7603; C→O median shift 11.8027; median BRI 12.0118; median normalized BRI 0.9703; bidirectional 49/49.
- `E_d`: O→C median shift 9.4049; C→O median shift 8.9801; median BRI 9.0923; median normalized BRI 0.8022; bidirectional 49/49.
- Sham control: median absolute sham/target ratio 0.0107 at `E_d−1` and 0.0115 at `E_d`.
- Frozen timing categories: R1_persistent_late_retrieval=43, R5_complex_nonmonotonic=6. The six R5 curves met the predeclared non-monotonicity rule but still retained late source control; categories are descriptive, not filters.

Both late checkpoints pass every frozen GO condition: the median-BRI bootstrap CI excludes zero, bidirectional consistency is at least 70%, median normalized BRI is at least 0.50, sham is below 20% of target magnitude, and self replacement is transparent.

## Stage 3B.1 cutoff comparison

Exact generated-index matching produced 104 problem-checkpoint pairs covering all 49 bases. At each base's latest exact shared checkpoint, the descriptive 0.50 quadrant split was 44 high-cutoff/high-switch and 5 low-cutoff/high-switch; no base had low identity-specific switch effect.

Across one latest exact match per independent base, cutoff-damage ratio and normalized BRI had Spearman rho=0.803 (N=49). This is a joint descriptive comparison; the switch experiment, not the correlation, provides the causal evidence-specific result.

## Secondary matched-seed rollouts

At `E_d−16`, O→C switched the first discriminative token to the counterfactual identity in 40/46 cases and C→O restored the original identity in 42/46. At `E_d−4` the counts were 42/49 and 44/49; at `E_d` they were 33/49 and 36/49.

These rollouts behaviorally support the teacher-forced result, but each condition uses one matched stochastic seed. The proportions describe this fixed-seed validation set, not repeated-sampling frequencies.

## Evidence strata and secondary attention comparison

Numeric examples (N=45) had median normalized BRI 0.9720 at `E_d−1` and 0.8022 at `E_d`. Structural examples (N=4) had 0.8178 and 0.8214; N=4 is too small for a strong stratum comparison.

The timing result is not confined to semantic teacher-forced leads. In the 12 exact-baseline-token cases, bidirectional source consistency was 12/12 at both late checkpoints, with median normalized BRI 0.9672 at `E_d−1` and 0.6692 at `E_d`. The 37 semantic-lead cases had 0.9720 and 0.8185.

The frozen Stage 2C exact-event overlap contains 9 problems, all mention-centered T2 events; all 9 also showed bidirectional source control at `E_d`. Pre-E0 ROI density versus `E_d` normalized BRI had Spearman rho=-0.400, p=0.286 (N=9). This small overlap cannot establish an attention–causal relationship.

The combined lesson is not that mention-centered attention is itself evidence acquisition. Rather, mention-centered attention can coexist with causal evidence-specific visual-source control; attention alone cannot distinguish semantic alignment from retrieval.

## Limitations and scientific boundary

- The intervention switches all visual positions and all language layers together; it does not identify which ROI, layer, module, head, or path carries the effect.
- Thirty-seven E_d coordinates use controlled semantic teacher-forced candidate leads, limiting exact natural-trajectory timing claims.
- Teacher-forced preference is primary; fixed-seed rollouts are a secondary behavioral check.
- The structural stratum and exact Stage 2C overlap are small.
- Full-gap normalization is secondary and unclipped; unnormalized BRI and bidirectional consistency carry the primary inference.
- This stage does not establish whether Q or prior-reasoning state stores retrieved evidence or whether attention versus MLP computation mediates transfer.

## Scientific conclusion

Within the frozen Stage 3A evidence decisions, future visual-source identity causally controls the upcoming evidence even after the prior reasoning history is fixed. Strong effects at `E_d−1` and `E_d`, reciprocal switching, small sham effects, transparent self controls, and matched-seed fact flips support active evidence-specific visual retrieval immediately before or during evidence expression.

This conclusion is about source identity and timing at the controlled evidence decision. It is not an attention-only claim and it does not localize the transfer mechanism.

## Key artifacts

- `annotations/discriminative_event_annotations.jsonl` and `config/switch_checkpoint_schedule.jsonl`
- `smoke/visual_source_switch_validation.json` and `smoke/cache_integrity_diagnostics.json`
- `scoring/per_problem_switch_results.jsonl`, `scoring/per_checkpoint_statistics.json`, and `scoring/rollout_results.jsonl`
- `analysis/retrieval_timing_curves.json`, `analysis/bidirectional_retrieval_statistics.json`, and `analysis/cutoff_vs_switch_comparison.json`
- `analysis/evidence_type_analysis.json`, `analysis/attention_secondary_comparison.json`, and `analysis/figures/`
- `summaries/stage3b2_acceptance.json` and `summaries/next_stage_recommendation.md`
