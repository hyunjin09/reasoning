# Stage12Y-S complete

Closed 2026-10-02T19:43:43.211610+00:00. Decision: **ROLE_DECOMPOSITION_UNRESOLVED**.

The frozen 96-family study completed all three phases: 288 new Thinking screens, 192 fresh-seed confirmation calls and 160 state-transfer/control calls. The 288 historical Instruct screens were reused unchanged.

| Role | Supported families | Frozen stage threshold | Result |
|---|---:|---|---|
| Visual evidence recovery | 1/5 | At least 3 and 60% | Not met |
| Equal-evidence downstream reasoning | 8/15; one unresolved | At least 3 and 60% | Not met |
| State construction | 2/6 with resolved controls; eight entered | At least 2 and 60% | Not met |

These gates do not negate the positive families. Downstream support is 8/14 among resolved families; retaining all 15 gives missingness bounds 53.3%–60.0%, so the unresolved family could change that gate. No missing response was counted as incorrect.

The paired single-run screen shows a Thinking advantage of 3.45 percentage points with images (95% family bootstrap −5.75 to 12.64; n=87) and 13.98 points under identical textual evidence (6.45 to 22.58; n=93). Demonstrated evidence recovery differs by 5.32 points (−3.19 to 13.83; n=94). These are descriptive comparisons of intended deployed variants, not formal mediation or a pure Thinking-switch effect.

## Phase C family results

Each cell is correct/five frozen replicates; NA counts are technical missingness, not errors. A family succeeds with at least three correct replicates. A negative majority must remain negative even if every missing replicate succeeded.

| Family | Thinking replay | Instruct replay | Fresh Instruct baseline | Shuffled state → Instruct | Full support |
|---|---:|---:|---:|---:|---|
| 907 | 5/5 | 5/5 | 4/5 | 5/5 | No |
| 2888 | 5/5 | 5/5 | 1/5 | 0/5 | Yes |
| 381 | 5/5 | 5/5 | 2/5 | 1/5; 3 NA | Unresolved |
| 2472 | 5/5 | 1/5 | 0/5 | 0/5; 2 NA | No |
| 1694 | 3/5 | 1/5; 1 NA | 0/5; 4 NA | 0/5; 3 NA | No |
| 1876 | 5/5 | 5/5 | 5/5 | 4/5; 1 NA | No |
| 2066 | 5/5 | 5/5 | 0/5; 2 NA | 1/5; 1 NA | Yes |
| 468 | 5/5 | 5/5 | 0/5 | 5/5 | No |

Families 2888 and 2066 satisfy the complete state-construction signature. Family 381 remains unresolved because the shuffled-control majority is unknown. Family 1694 lacks resolved baseline/shuffle controls but already fails the cross-checkpoint replay criterion. Three other families fail the fresh-baseline or shuffle specificity check; family 2472 fails Instruct replay. Thus 2/8 entered families are supported, and the preregistered resolved-control denominator is 2/6.

All Phase C prompts use the same target Q+E* without images. Source prefixes and the deterministic cyclic shuffle were frozen before replay. Some shuffled responses answer the source task instead of the target: clear committed off-task answers remain scientific errors. Capped responses without an unretracted outcome remain missing.

## Validity, resources and preserved evidence

Phase A had zero cap hits or missing outputs. Phase B had eight cap hits, seven technically missing; Phase C had 18 cap hits, 17 technically missing. A cap alone did not invalidate a clear final. The 640 new responses received first-pass review and 177 ambiguity/random second reviews by the same agent; this is not independent human reliability.

All 20 Slurm GPU jobs finished and released their allocations. Total allocation accounting is 10.915 GPU-hours, below the 12-hour target and 16-hour hard limit. No additional model or dataset downloads were needed. All 18 required artifacts, five PNG/PDF figure pairs, raw outputs, input receipts and scoring records are saved. Hash verification preserved 11,478 historical artifacts and all source/input seals.

Historical Instruct evidence probes retained their 256-token cap; fresh Instruct probes use 32,768 and Thinking uses 81,920. Model checkpoints, intended decoding settings and budgets differ. The source-eligible MathVision cohort and selected transfer families do not establish benchmark-wide prevalence or the full neural mechanism.

## Exactly one recommendation

Stop role-mechanism expansion and retain the narrower supported claims about evidence bottlenecks and developmental state portability.

**STOP. No follow-on launched.**

[Required summary](../../../outputs/stage12ys/v1/stage12ys_summary.md) · [Inference](../../../outputs/stage12ys/v1/stage12ys_primary_inference.json) · [Decision](../../../outputs/stage12ys/v1/stage12ys_decision.json) · [Accounting](../../../outputs/stage12ys/v1/stage12ys_resource_accounting.json) · [Figures](../../../outputs/stage12ys/v1/figures/) · [Technical status](status.md)
