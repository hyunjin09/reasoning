# Stage12U-S — Reasoning-state production versus utilization

Completed 2026-09-30T12:33:22.219114+00:00. **STATE_PRODUCTION_SIGNAL**. Authorized stage ends here; no follow-on launched.

Five frozen B4 C−T+ families are the primary targeted cohort; two B1 families are descriptive. Exactly156 scientific calls comprise84 core transfers,42 question-only controls and30 deterministic cyclic shuffled controls. Every family-condition has three fixed seeds; majority success requires at least2/3. Twelve disjoint technical calls passed input/prefix/scoreability checks before science; their correctness was not used.

All source traces are reused unchanged. Each canonical prefix ends before its first explicit task-answer candidate, including tentative wrong candidates; only Thinking wrappers are removed. Targets receive the original question plus native assistant prefill without images or extra instructions. Model-specific4B recipes and32768/81920 new-token caps remain frozen.

## Primary B4 transfer outcomes

| Item | R_T→T | R_T→I | R_C→I | R_C→T | Q→I | Q→T | Shuffled R_T→I | Shuffled R_C→T |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2975 | 3/3 | 3/3 | 2/3 | 3/3 | 0/3 | 0/3 | 0/3 (1 missing) | 0/3 |
| 798 | 3/3 | 2/3 | 0/3 | 3/3 | 1/3 | 3/3 | 0/3 | 0/3 |
| 750 | 3/3 | 3/3 | 0/3 | 1/3 | 0/3 | 0/3 | 1/3 | 0/3 |
| 2908 | 3/3 | 3/3 | 0/3 | 0/3 | 1/3 | 2/3 | 0/3 (1 missing) | 1/3 |
| 991 | 2/3 | 1/3 | 0/3 | 0/3 | 0/3 | 1/3 (2 missing) | 0/3 | 1/3 |

Entries are all-seed correct counts, not best-of-three selection. Normal-stop refusals/no answers remain observed unsuccessful continuations; unfinished pre-answer caps remain technical missingness. Family-majority uncertainty is bounded rather than filled in.

## Primary endpoints

| Endpoint | Success / resolved families | Exact descriptive95% interval | Frozen / missing |
|---|---:|---:|---:|
| U_P1_S_TT | 5/5 | [0.478, 1.000] | 5 / 0 |
| U_P2_S_TI_given_TT | 4/5 | [0.284, 0.995] | 5 / 0 |
| U_P3_S_CT | 2/5 | [0.053, 0.853] | 5 / 0 |
| U_P3_S_CI | 1/5 | [0.005, 0.716] | 5 / 0 |
| U_P4_production_trace_dependence | 4/5 | [0.284, 0.995] | 5 / 0 |
| U_P4_utilization_repair_trace_dependence | 1/5 | [0.005, 0.716] | 5 / 0 |

Exact intervals are descriptive. The independent unit is family; this n5 outcome-selected cohort cannot estimate population prevalence or support asymptotic significance claims.

## Interpretation and controls

Same-model Thinking-prefix sufficiency: **5/5**. Production support: **4/5**; utilization support: **0/5**; repair support: **0/5**. Text-insufficient items: **0/5**.

Source quality is fixed independently of transfer outcomes. Utilization requires no material evidence error and a valid derivation; repair requires flawed evidence and/or derivation. Question-only success weakens trace-specific interpretation. Shuffled success tests whether relevant content, rather than simply a long prefix, matters; all such outcomes above remain part of the interpretation.

Only 0/5 primary CoT prefixes meet the source-quality prerequisite for strong utilization. Thus zero utilization support is not evidence that the checkpoints are equally capable of using an adequate state. Production support establishes useful portability under this transfer assay; it does not certify every intermediate deduction or establish that production is the sole cause of the native advantage.

- Q_I: majority success 0/5 resolved families; 0 missing.
- Q_T: majority success 2/4 resolved families; 1 missing.
- ST_I: majority success 0/5 resolved families; 0 missing.
- SC_T: majority success 0/5 resolved families; 0 missing.

These are checkpoint-specific operating regimes: checkpoint, sampling and output budget differ. No direct hidden-state mechanism or pure Thinking-on/off cause is identified. Failed R_T→T replay does not distinguish omitted multimodal state, early answer-safe cutoff, or stochastic continuation. Historical E*→Instruct failures are preserved single trials, not a newly replicated content-ablation control.

## Secondary B1 (descriptive)

| Item | R_T→T | R_T→I | R_C→I | R_C→T | Q→I | Q→T |
|---|---:|---:|---:|---:|---:|---:|
| 2363 | 3/3 | 3/3 | 0/3 | 1/3 | 0/3 | 1/3 |
| 2007 | 3/3 | 3/3 | 0/3 | 0/3 | 0/3 | 0/3 |

## Audit and resources

Input/prefix receipts verified for all168 calls. Scientific first scoring156; separate-pass QC44, agreement44/44. This is same-agent QC, not independent human reliability. Long source-prefix audits combine whole-prefix lexical scanning and targeted semantic/content reading; they are not an exhaustive independent sentence-by-sentence audit. Exact quotes, offsets, candidate scans and full source/target text are preserved.

Scientific continuations: 152/156 scoreable; 4 cap hits and 4 missing. Capped unfinished outputs are not relabeled incorrect. Shuffled continuations sometimes answer the unrelated source task; their emitted final values are scored against the assigned target by the frozen equivalence rule, not credited for source-task correctness. Numeric matches alone do not certify target-directed reasoning.

Allocated compute **4.261389 GPU-hours** including technical validation/startup (target<5, hard7). All stage allocations released. No retries, downloads, source regeneration, hidden-state intervention or next experiment.

Figures: figures/U1_transfer_assay.png; U2_primary_transfer_matrix.png; U3_interpretation_classes.png; U4_source_content_audit.png (PDF companions). Full response reading index: reports/stage12us/v1/index.md. Machine-readable evidence:16 required named artifacts plus immutable audit/generation receipts.

## Exactly one recommendation

Localize which Thinking-derived intermediate deductions make the state portable to Instruct using prefix-position and content ablations.

Not launched. STOP.
