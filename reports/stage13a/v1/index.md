# Stage 13A complete: equal-evidence Thinking advantage confirmed

Both pinned Qwen3-VL 4B variants received the exact same frozen question and task-critical evidence, without an image or added reasoning instruction. All 96 families received three fresh replicates per variant.

| Analysis | Complete families | Thinking minus Instruct | 95% family-bootstrap interval |
|---|---:|---:|---:|
| Primary | 84 | +11.11 percentage points | +5.56 to +17.06 |
| Result reached before 32k tokens | 82 | +11.38 percentage points | +6.10 to +17.48 |

On the primary complete paired set, Instruct accuracy was 70.63% and Thinking accuracy was 81.75%. The frozen confirmation gate passes. Full-cohort missingness bounds are +9.72 to +15.28 points; these are assignment bounds, not a confidence interval. The optional 24-family cap-matched assay was not triggered.

Thinking therefore retains an advantage after the supplied evidence is equalized. This compares deployed model variants under their intended recipes; checkpoint, sampling and budget effects are not separately identified. It does not establish a universal state-construction mechanism.

| All primary calls | Correct | Incorrect | Technical missing |
|---|---:|---:|---:|
| Instruct | 182 | 91 | 15 |
| Thinking | 225 | 62 | 1 |

All Instruct scoring closed before Thinking outputs were opened. All flagged cases and the frozen 20% random sample received second review: 111 Instruct and 74 Thinking responses, with no label disagreements. This is same-agent QC, not independent-rater reliability. Missing outputs are excluded from the primary accuracy estimate.

Family-majority transitions: 61 both correct, 10 Thinking-only, 1 Instruct-only, 18 both wrong, 6 unresolved. The exact discordant-family p-value is 0.01171875, descriptive only.

Stage 12Y's single-run estimate was +13.98 points. The same cohort was reused; estimates were not pooled. Stage 13A supersedes that descriptive estimate for the cohort-level claim.

Completed 576 logical calls with 589 submitted attempts: one Slurm timeout interrupted 13 calls, which were recovered with unchanged prompts, seeds and recipes. All completed outputs and interrupted input records are preserved. All nine allocations are released; total cost is 8.5686 GPU-hours. All 15,807 sealed historical files and source/input seals verified unchanged.

Exactly one recommendation: Run a cross-scale image-vs-equal-evidence study at 2B/4B/8B to test whether the functional role of Thinking changes with model size.

**STOP. The recommendation was not launched.**

## Evidence

- [Required summary](../../../outputs/stage13a/v1/stage13a_summary.md)
- [Primary inference](../../../outputs/stage13a/v1/stage13a_primary_inference.json)
- [32k sensitivity](../../../outputs/stage13a/v1/stage13a_32k_comparable_sensitivity.json)
- [Missingness bounds](../../../outputs/stage13a/v1/stage13a_missingness_bounds.json)
- [Scoring audit](../../../outputs/stage13a/v1/stage13a_scoring_audit.json)
- [Allocation and attempt accounting](../../../outputs/stage13a/v1/stage13a_resource_accounting.json)
- [All answers and reasoning](responses.md)
- [Independent table/bootstrap recalculation](../../../outputs/stage13a/v1/audit/independent_table_recalculation.json)

## Figures

![Paired family outcomes](../../../outputs/stage13a/v1/figures/13A_1_paired_equal_evidence.png)

![Majority transitions](../../../outputs/stage13a/v1/figures/13A_2_majority_transitions.png)

![Historical comparison on the same cohort](../../../outputs/stage13a/v1/figures/13A_3_stage12y_vs_stage13a.png)

![Output-budget sensitivity](../../../outputs/stage13a/v1/figures/13A_4_budget_sensitivity.png)
