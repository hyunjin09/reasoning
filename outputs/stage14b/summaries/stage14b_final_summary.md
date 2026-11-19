# Stage14B large-scale math phenomenon

Stage14B is complete: 17,536 main calls and 9,600 fresh confirmation calls, plus 24 technical preflight calls. All scoring, prescribed reviews, primary/secondary/confirmation analyses and five figures are sealed. No follow-on stage was launched.

All three frozen main-study phenomenon criteria pass.

## Primary effects

| Endpoint | Estimate | 95% interval | Paired/scored coverage |
|---|---:|---:|---|
| Native Thinking − Instruct | 7.20 pp | 5.67 to 9.08 pp | 2738/3040 complete pairs |
| Instruct E* rescue | 55.98% | 51.08 to 60.80% | 234/418 scored native-wrong followups; 31 unresolved |
| Equal-evidence Thinking − Instruct | 14.69 pp | 12.10 to 17.39 pp | 926/1000 complete pairs |

Worst/best missingness bounds: native gap 0.66 to 10.89 pp; post-evidence gap 11.10 to 18.60 pp. Rescue bounds over all 449 native-wrong families: 52.12 to 59.02%. Missing/unscorable is never relabelled wrong.

Intervals use 10,000 bootstrap draws with the frozen seed; known conservative family clusters are preserved. Intervals are unadjusted, without a multiplicity-adjusted significance claim. The 3,040 native problems are not 3,040 verified independent tasks.

## Accuracy and completion

| Population/arm | Correct | Wrong | Unscorable | Technical missing | Scored-answer accuracy | Correct/N lower coverage bound |
|---|---:|---:|---:|---:|---:|---:|
| I_image | 1612 | 1143 | 285 | 0 | 58.51% | 53.03% |
| T_image | 1917 | 1097 | 26 | 0 | 63.60% | 63.06% |
| I_evidence | 671 | 259 | 70 | 0 | 72.15% | 67.10% |
| T_evidence | 852 | 143 | 5 | 0 | 85.63% | 85.20% |
| I_native | 2196 | 2523 | 9 | 0 | 46.54% | 46.45% |
| T_native | 3522 | 1206 | 0 | 0 | 74.49% | 74.49% |

Image/evidence rows refer to MATH-Vision; native rows refer to all six MathVerse versions. Marginal scored-answer accuracies can use different denominators, so subtracting them is not the complete-pair effect. Full paired transition tables, including unresolved states, are in `analysis/transition_tables.json` and `analysis/primary_results.json`.

## MathVerse modality profile

| Version | Instruct scored accuracy | Thinking scored accuracy | Paired gap | Family 95% interval |
|---|---:|---:|---:|---:|
| Text Dominant | 60.46% | 82.99% | 22.83 pp | 19.52 to 26.28 pp |
| Text Lite | 50.95% | 77.03% | 26.18 pp | 22.49 to 29.86 pp |
| Text Only | 43.27% | 69.92% | 26.65 pp | 23.10 to 30.20 pp |
| Vision Intensive | 47.96% | 73.35% | 25.57 pp | 21.76 to 29.26 pp |
| Vision Dominant | 45.93% | 72.21% | 26.46 pp | 22.65 to 30.28 pp |
| Vision Only | 30.71% | 71.45% | 40.74 pp | 36.80 to 44.67 pp |

The preregistered contrast, mean gap(VD, VO) − mean gap(TD, TL), is 9.28 pp, 95% interval 6.15 to 12.36; 781/788 fully scored families. The frozen source-clean layer gives 9.46 pp, interval 4.73 to 14.18, using 349 complete families. The clean layer and repeat-cluster/source-defect sensitivities do not redefine the census.

## Frozen multi-seed robustness

The source-selected 300 MATH-Vision and 300 MathVerse subsets use main replicate0 and fresh replicates1/2. This is stochastic-decoding robustness, not untouched independent confirmation.

| Replicate | Native I/T scored accuracy | Native gap | Instruct rescue | Evidence I/T scored accuracy | Post-evidence gap | MathVerse profile contrast |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 51.27% / 58.53% | 8.39 pp | 56.45% | 71.79% / 86.33% | 15.00 pp | 11.28 pp |
| 1 | 50.91% / 59.12% | 9.23 pp | 52.07% | 70.40% / 85.52% | 15.27 pp | 6.19 pp |
| 2 | 50.76% / 59.46% | 9.58 pp | 49.57% | 68.46% / 85.57% | 17.33 pp | 9.49 pp |

| Endpoint | Seed mean | Sample SD | Fraction retaining main sign |
|---|---:|---:|---:|
| G_img | 9.07 | 0.61 | 1.00 |
| G_post | 15.87 | 1.27 | 1.00 |
| R_I | 52.70 | 3.48 | 1.00 |
| MathVerse_profile | 8.99 | 2.58 | 1.00 |
| MathVerse_Text Dominant | 20.89 | 3.20 | 1.00 |
| MathVerse_Text Lite | 27.51 | 1.25 | 1.00 |
| MathVerse_Text Only | 25.67 | 0.88 | 1.00 |
| MathVerse_Vision Intensive | 23.36 | 2.06 | 1.00 |
| MathVerse_Vision Dominant | 27.50 | 1.46 | 1.00 |
| MathVerse_Vision Only | 38.60 | 3.32 | 1.00 |

Item/condition/model outcomes are identical across all three seeds in 4019/4674 fully scored slots; 126 slots contain an unresolved seed. Paired I/T outcome patterns are identical across seeds in 1732/2279 fully scored item/condition pairs. Full per-seed counts, modality estimates and intervals are preserved in `analysis/confirmatory_results.json`.

## Validity and interpretation limits

- This compares pinned Qwen3-VL-4B variants under their validated native recipes, with preregistered 32,768/81,920 output-token caps. It is neither a causal Thinking-toggle nor an equal-compute comparison.
- E* rescue concerns incomplete demonstrated recovery of task-critical visual evidence. Evidence supply can change accessibility, representation and binding. A post-evidence advantage does not identify its downstream mechanism.
- All unresolved parser/equivalence records, the fixed 10% hash audit, caps and native nonletter-option golds were reviewed by the same agent. This is not independent human reliability evidence. Versioned presentation repairs and second adjudications preserve original outputs, golds and records. Some initial extraction strings remain parser artifacts; semantic grading uses documented terminal-response review.
- Native source/gold defects remain. The frozen absolute numeric tolerance of 1e-6 can reject rounded responses when native gold is exact, even where source wording permits rounding. No outcome-based gold, tolerance, cohort or recipe adjustment was made.
- Conservative aliases and prior source-catalog exposure are disclosed. Unknown dependence may remain. Source strata are secondary and do not replace the primary cohort.

## Resources and artifacts

Observed allocation intervals or worker-exit proxies total 193.218 GPU-hours, including failed startup jobs. Retained exact Slurm intervals are used where available; otherwise shutdown/release tails are not observed. The Slurm accounting service is unavailable. CPU preprocessing/watchers contribute zero GPU-hours. No GPU allocation remains active. Parent-process CUDA counters do not measure vLLM child peak VRAM; those counters are not presented as peak device usage.

Raw responses and input/seed receipts: `raw/`. Reviewed scores: `scoring/`. Main, secondary and seed analyses: `analysis/`. Five PNG/PDF figures: `figures/`. Source/condition/code seals, job records and accounting: `audit/`. Main seed0 is reused exactly, with no unnecessary regeneration.

Exactly one recommendation: Review and authorize Stage14C task-selectivity testing, taking the reported seed robustness and source limitations into account; Stage14B does not identify a mechanism.

Stage14B complete. STOP.
