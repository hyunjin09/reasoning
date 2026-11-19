# Stage 3C.10 — Reasoning-State Retrieval Trigger

**Technical PASS; O1 — Reasoning-State Retrieval Trigger at both targets. M2 — Routing mediation only.**

Recent reasoning contribution causally changes target-specific current-query visual-source dependence at the two historical retrieval coordinates. The stronger claim that this behavioral effect is mediated by the frozen late Q geometry is **not supported**. All-head native-Q rescue restores routing exactly but does not robustly rescue VSD; the optional late h_pre rescue is also nonrobust.

The approved plan is complete and stopped. The sole recommendation is **GO — Stage 4 Multi-Evidence Retrieval/Refresh**, for review only. No follow-on experiment has started.

## Fixed assay and validity

Exact Stage 3C.3 manifests: 7 validation and 24 primary bases, with M/T and A/B paired within each base. Original O images, model/tokenizer, historical divergent suffixes, ROIs, causal/noncausal heads, and question-text source spans are preserved. A uses upstream layers 0–28 and routing layer 29; B uses 0–27 and layer 28. All 32 query heads receive trigger deletion. T0 suppresses only the current query, all 36 layers/all 32 heads.

Every comparison uses one per-base A6000 BF16 cached partition: native multimodal prefill, maximum 2048 generated-token chunk, and shared before/after barriers at every M/T query. The RDS function is imported unchanged from Stage 3C.3. All causal denominators and controls are newly scored on this same path. Historical A5000 full-path values are descriptive references only.

Validation: 15/15 checks across seven bases, 28 state files and 517 arms. No-op, deterministic replay, self-Q, inherited uninstrumented cached scores and cached T0 are exact. Actual full-past K/V comparisons imply unchanged visual K/V. Artifact audit: 21/21 checks across 412 files, 5121 arms and 207811 source-layer traces. Focused/new plus inherited tests: 45 passed.

R16 excludes the current token and intersects generated history: primary base 119 has 14/13 preceding M tokens for A/B, and base 120 has 6/5. Validation base 128-B-M has 15. No base was excluded. E16 is available on 22/24 T bases and is never shifted to fill missing history. Q is the exact historical question-content span; structural `<|im_start|>` is untouched.

## Primary results

Eight prespecified contrasts per target use two-sided paired Wilcoxon with Holm correction. Unrun rescue slots were p=1 when primary gates froze; those gates never changed afterward. Robust positive means corrected p<.05, positive bootstrap mean CI, median>0 and at least 75% positive bases. Bootstrap uses 10,000 base resamples, seed 12348. E16 comparisons use 22 available paired bases.

| Target | Contrast | n | Median | Mean [bootstrap 95% CI] | Positive | Primary Holm p |
|---|---|---:|---:|---|---:|---:|
| A | rds_T | 24 | 2.04144 | 2.33788 [1.82289, 2.93655] | 24/24 | 9.53674e-07 |
| A | vsd_T | 24 | 0.793223 | 1.0183 [0.547257, 1.50474] | 20/24 | 0.00088954 |
| A | did | 24 | 0.757563 | 1.04765 [0.571577, 1.53494] | 21/24 | 0.00088954 |
| A | r16_minus_e16 | 22 | 0.687228 | 1.03368 [0.550295, 1.54148] | 18/22 | 0.00296926 |
| A | target_minus_irrelevant | 24 | 0.644319 | 1.02899 [0.564635, 1.50667] | 21/24 | 0.00088954 |
| A | r16_minus_q | 24 | 0.987179 | 1.0575 [0.552593, 1.56343] | 19/24 | 0.00296926 |
| B | rds_T | 24 | 2.13173 | 2.53457 [2.04851, 3.06554] | 24/24 | 9.53674e-07 |
| B | vsd_T | 24 | 0.651588 | 0.639786 [0.43061, 0.87697] | 24/24 | 9.53674e-07 |
| B | did | 24 | 0.536315 | 0.615373 [0.411728, 0.84449] | 23/24 | 2.38419e-06 |
| B | r16_minus_e16 | 22 | 0.563036 | 0.575298 [0.364616, 0.822582] | 21/22 | 7.15256e-06 |
| B | target_minus_irrelevant | 24 | 0.545588 | 0.654545 [0.431485, 0.916786] | 24/24 | 9.53674e-07 |
| B | r16_minus_q | 24 | 0.568201 | 0.652992 [0.449281, 0.880519] | 23/24 | 1.78814e-06 |

Both targets pass all five behavioral-trigger gate contrasts. R16 also exceeds the question-source control. Routing changes at all 24 T bases per target; behavioral trigger effects are positive on 20/24 A and24/24 B. Routing alone is not the basis of this conclusion.

## Temporal and layer localization

| Target | R1 | R2 | R4 | R8 | R16 | k80 |
|---|---:|---:|---:|---:|---:|---:|
| A | 0.0475929 | 0.31725 | 0.547215 | 0.626478 | 0.793223 | 16 |
| B | 0.219001 | 0.20698 | 0.51243 | 0.500596 | 0.651588 | 16 |

Entries are median TE_VSD. k80=16 at both targets is a tested threshold descriptor, not a unique 16-token information span: A R8 and B R4 lie just below 80% of the R16 median. The B curve is nonmonotonic. Trigger influence is broader across the tested recent window than the earlier 1–2-token carrier result.

Only layers 16–23 (L2) pass the frozen bin-wise correction at both targets. A median TE_VSD=0.593875; B=0.381186. Other bins are retained as negative evidence; they were not redefined.

## Mediation and its limits

| Target | Rescue | Median VSD gain | Positive | Corrected p | Robust |
|---|---|---:|---:|---:|---|
| A | All 32 Q | -0.000842544 | 12/24 | 0.508766 | False |
| A | Historical 4 Q | -0.00456686 | 11/24 | 1 | False |
| A | h_pre (secondary) | -0.224981 | 9/24 | 0.0460644 | False |
| B | All 32 Q | 0.046476 | 13/24 | 0.725741 | False |
| B | Historical 4 Q | 0.0483628 | 17/24 | 0.258597 | False |
| B | h_pre (secondary) | 0.0678165 | 17/24 | 0.0601797 | False |

All-head and selected-head Q rescues restore the primary routing readout exactly on 24/24 bases per target. This is expected when native Q is reinstated with unchanged visual K; behavioral VSD rescue is the nontrivial test. It fails the robust-positive rule for both targets. Target-A h_pre VSD gain is negative on average, with a two-sided corrected p below .05; it is not a positive rescue. Target-B h_pre gain is positive but nonrobust.

The optional h_pre donor can contain native upstream visual evidence and bypass part of all-layer ROI suppression. Its VSD result is not a guaranteed numerical upper bound. The mediator of the recent-input behavioral effect remains unknown; broader redundancy and earlier/multiple state paths are possible explanations, not established diagnoses. Exact same-path replay, source isolation and recipient-K/V audits pass, so no further diagnostic or rescue search was run.

## Generic computation and secondary content

R16 changes residual/attention-output norms and candidate distributions as well as retrieval. Median original-candidate NLL changes at T are small (A 0.00136392, B -0.00185395), while counterfactual NLL changes are larger (A -1.50332, B -0.667137). Noncausal-head routing also changes, especially A; the trigger is not restricted to the historical four heads. M-state entropy shifts and complete E16/Q controls are saved in `analysis/generic_language_damage.json`. These controls support the bounded retrieval-specific contrast, not a claim of exclusively retrieval-only computation.

All 763 available last-eight single-position effects were scored after primary freeze. Last 16 annotations were copied from the attention-blind Stage 3C.8 taxonomy with exact token/position checks before position scoring. Effects are centered within exact target/state/distance and then aggregated once per base/type. A T-state mean effects are largest at distance 2, whereas B is strongest at distance 1; single-position effects do not by themselves identify the cumulative R16 mechanism. No universal token class is claimed. Historical sink mass is overlaid descriptively for 48 target/base cells; no sink token is manipulated.

## Paper assessment and stop

Recent reasoning input changes target-specific current-query visual dependence at both frozen retrieval coordinates; the tested late Q/h_pre rescues do not establish its behavioral mediator.

The behavioral mediator remains unresolved: late Q rescue restores routing but not VSD, and the optional late h_pre rescue is also nonrobust. Prior stages already document local redundancy and late-state insufficiency. k80=16 is limited to tested windows; natural-generation sufficiency and generality beyond this historical cohort remain open.

Sink release remains observational. These interventions already test the upstream recent-input link; sink manipulation is not necessary to establish the supported link and was not performed.

The paper now has a causal recent-input link in addition to the earlier query-routing and visual-Value/carrier results, but cannot present an end-to-end Q-mediated behavioral chain. The same late-state rescue ambiguity echoes prior routing/behavior dissociation; another unrestricted local search is not authorized. A separately reviewed multi-evidence test offers a larger test of the lifecycle’s scope.

**One recommendation: GO — Stage 4 Multi-Evidence Retrieval/Refresh.** Test whether the local mechanism extends to selecting and refreshing multiple visual facts, subject to a new approved Stage4 plan.

No sink causality, broader-history trigger search, new cohort, Stage 4 or failure experiment was started.

## Evidence and resources

- Primary freeze/statistics: `phase_b_primary/primary_freeze.json`, `primary_statistics.json`.
- Complete traces: `raw/{validation,primary,temporal,layers,mediation,hpre,positions}/`.
- Mechanics/artifact audits: `audit/mechanical_validation.json`, `independent_artifact_validation.json`.
- Mediation: `phase_e_mediation/mediation_statistics.json`, `hpre_statistics.json`.
- Secondary position/type: `phase_f_secondary/recent_position_scan.jsonl`, `token_type_analysis.json`.
- Sixteen standalone PNG/PDF figures: `analysis/figures/index.json`.
- Technical acceptance: `summaries/stage3c10_acceptance.json`.

Only existing Slurm 108548 / tmux 9 / node07 four A6000 GPUs were used. No allocations or packages were added. Maximum saved-condition memory: 9.25 GiB allocated / 9.34 GiB reserved. Per-phase timing and scheduler/log identities are in `audit/resource_summary.json`. All frozen historical input hashes and all primary-score hashes remain unchanged.
