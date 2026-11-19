# Stage14E2 matched reader-mode diagnostic

This experiment is complete; further method development and the frozen fresh32 evaluation are paused at the user’s request. These are24 outcome-observed development families, not a fresh confirmation cohort. No downstream solver continuation or final-answer accuracy experiment was run.

## Frozen design

O=original model-selected query; T=source-informed target identity, diagnostic only. C=closed helper thinking boundary; T suffix=open helper thinking boundary. T_N uses the same diagnostic target and open thinking boundary without a fresh image. A correct T_N response is not visual acquisition. All readouts receive the same unverified solver prefix. Same family seed, sampling settings and8192-token cap; no constrained JSON grammar in either reader mode. The original targets are absent on6families, retained as12logical absent O records.

## Acquisition outcomes

Useful=U(new correct task-critical fact) or R(valid reinspection), including partial source coverage. K=already-known/given; W=explicit task-critical source error; ?=uncertain/incomplete; I=irrelevant/derived; A=absent original query; X=capped/malformed/uncommitted. No capped reasoning was mined for a replacement final.

| Condition | Physical / assigned | Useful U+R | U | R | Known K | Wrong W | Unknown ? | Other I | Invalid X | Full task-source coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| O_C | 18/24 | 3 | 0 | 3 | 6 | 3 | 3 | 2 | 1 | 0 |
| O_T | 18/24 | 5 | 0 | 5 | 5 | 2 | 1 | 1 | 4 | 0 |
| T_C | 24/24 | 4 | 1 | 3 | 6 | 7 | 4 | 0 | 3 | 3 |
| T_T | 24/24 | 4 | 1 | 3 | 5 | 6 | 2 | 2 | 5 | 2 |
| T_N | 24/24 | 1 | 1 | 0 | 4 | 2 | 7 | 1 | 9 | 2 |

| Contrast | Difference (pp) |95% family bootstrap CI (pp)| Gains | Losses |
|---|---:|---|---|---|
| T_T-T_C | 0.00 | [-16.67, 12.50] | 487, 1305 | 333, 2471 |
| O_T-O_C | 8.33 | [0.00, 20.83] | 436, 1305 |  |
| T_T-T_N | 12.50 | [0.00, 25.00] | 436, 1305, 2924 |  |

The cube family436 relies on the source’s solid-pile/hidden-support convention. Its partial reinspections do not certify individually visible hidden cubes. A descriptive sensitivity excluding this family is reported below; it was added during source review, does not replace the frozen primary analysis, and has no separate inferential claim.

- Excluding436: T_T−T_C = 0.00pp across23families.
- Excluding436: O_T−O_C = 4.35pp across23families.
- Excluding436: T_T−T_N = 8.70pp across23families.

Primary contrast: T_T−T_C. Secondary: O_T−O_C and T_T−T_N. Family-equal, inherited source-context strata,4000 bootstrap draws, seed20261022. Zero-event degenerate intervals do not prove a zero population rate. One stochastic seed per family; uncertainty does not separately estimate repeated-seed variation.

## Execution and resource use

Completed108physical/120logical scientific reads;4/4 repeated-native gates pass. All matched C/T prompts, token prefixes, image pixels, family seeds and generation settings passed exact transport checks. Prior sealed records are unchanged. Both finite queues exited; no further experiment launched.

This diagnostic: **1.6686charged GPU-hours**. Cumulative authorized cycle: **8.8175/24GPU-hours**, including failed jobs, startup and idle allocation. Historical SAVA expenditure remains separate (21.365278GPU-hours).

| Arm | Generated tokens | Median tokens | Cap hits | Summed request seconds |
|---|---:|---:|---:|---:|
| O_C | 887 | 40.5 | 0 | 15.7 |
| O_T | 68012 | 2990.0 | 4 | 1088.3 |
| T_C | 2340 | 56.0 | 0 | 39.0 |
| T_T | 114501 | 4776.5 | 5 | 1834.8 |
| T_N | 144114 | 6180.5 | 8 | 2291.7 |

Request latency is descriptive and is not substituted for allocation billing.

## Interpretation limits and pause

Source-informed T targets are diagnostic oracle identities, not deployable method outputs. The source review is a single AI review with condition visible, using original pixels and offline source references. Source-reference ambiguity and partial coverage remain explicit in the casebook. A source-correct fact repeated from the prefix is not newly acquired evidence. No final-answer improvement can be inferred from this reader-only experiment. No candidate is selected or evaluated after this diagnostic while paused.

The frozen fresh32 evaluation inputs remain unused. Old Stage14D375GPU-hour work remains HOLD; Stage14C-V remains unfinished.

Provenance: `analysis/source_review_complete_v1.json`, `analysis/diagnostic_results_v1.json`, `audit/completed_execution_audit_v1.json`, `audit/resource_ledger.json`, `protocol/source_review_rubric_v1.json`, and `reports/casebook_v1.md`.
