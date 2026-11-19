# Stage12T-R Thinking completion validation

**THINKING_REGIME_VALIDATED**. 2026-09-29T17:21:38.014606+00:00

Technical-only cap intervention40960→81920. Same checkpoint, original image/question, BF16/vLLM runtime, per-family seed, temperature1/top-p.95/top-k20/repetition1/presence0. No task correctness or rescue analysis.

| Phase | Input valid | Scoreable | Pre-outcome caps | Normal stops | Closed think | Decision |
|---|---:|---:|---:|---:|---:|---|
| same12 | 12/12 | 12/12 | 0 | 12 | 12 | CAP_EXTENSION_PROMISING |
| fresh12 | 12/12 | 11/12 | 1 | 11 | 11 | THINKING_REGIME_VALIDATED |

| Phase | All cap hits | Token median | Token Q1–Q3 | Token max | R1/R2/R3/R4/R5 counts |
|---|---:|---:|---|---:|---|
| same12 | 0 | 23577 | 10477.8–31258.8 | 77825 | 12/12/11/7/0 |
| fresh12 | 1 | 13253 | 4719–24310.8 | 81920 | 10/9/9/9/0 |

Per-case technical behavior; extracted answer values are retained in the technical result files, without correctness labels.

| Phase | Item | Tokens | Scoreable | Pre-outcome cap | Closed think | Final channel | R1–R5 positive |
|---|---|---:|---|---|---|---|---|
| same12 | 2864 | 77825 | True | False | True | True | R1,R2,R3,R4 |
| same12 | 1789 | 6358 | True | False | True | True | R1,R2,R3 |
| same12 | 653 | 4531 | True | False | True | True | R1,R2,R4 |
| same12 | 2448 | 23693 | True | False | True | True | R1,R2,R3,R4 |
| same12 | 57 | 11397 | True | False | True | True | R1,R2,R3 |
| same12 | 2198 | 43246 | True | False | True | True | R1,R2,R3,R4 |
| same12 | 257 | 23461 | True | False | True | True | R1,R2,R3 |
| same12 | 2007 | 27263 | True | False | True | True | R1,R2,R3,R4 |
| same12 | 3011 | 53624 | True | False | True | True | R1,R2,R3,R4 |
| same12 | 1568 | 13721 | True | False | True | True | R1,R2,R3 |
| same12 | 2013 | 24766 | True | False | True | True | R1,R2,R3,R4 |
| same12 | 725 | 7720 | True | False | True | True | R1,R2,R3 |
| fresh12 | 2214 | 33271 | True | False | True | True | R1,R2,R3,R4 |
| fresh12 | 1022 | 3675 | True | False | True | True | R1,R2,R3 |
| fresh12 | 1430 | 5273 | True | False | True | True | R1,R2,R3,R4 |
| fresh12 | 2975 | 14828 | True | False | True | True | R1,R3,R4 |
| fresh12 | 1974 | 17579 | True | False | True | True | R1,R2,R3,R4 |
| fresh12 | 1237 | 81920 | False | True | False | False | R1,R3,R4 |
| fresh12 | 798 | 5067 | True | False | True | True | R1,R2,R3,R4 |
| fresh12 | 2359 | 3524 | True | False | True | True | R2 |
| fresh12 | 974 | 21324 | True | False | True | True | R1,R2,R4 |
| fresh12 | 2553 | 1057 | True | False | True | True | none |
| fresh12 | 2981 | 11678 | True | False | True | True | R1,R2,R3,R4 |
| fresh12 | 2143 | 68885 | True | False | True | True | R1,R2,R3,R4 |

Original capped trajectories:

| Item | Original tokens | Extended tokens | Prefix match | Scoreable final | New cap |
|---|---:|---:|---|---|---|
| 2198 | 40960 | 43246 | False (LCP 37338) | True | False |
| 3011 | 40960 | 53624 | False (LCP 37768) | True | False |

9/12 old trajectories are exact token prefixes of the longer-cap rerun. Prefix divergence limits attribution to a pure cap change; it does not change the technical completion gate.

Both previously capped items2198 and3011 now finalize, but their common prefixes end at37338 and37768 tokens, respectively, before the old40960 cap. Item2864 also diverges (52-token common prefix). Thus this check validates observed completion under the extended recipe without establishing a pure budget cause for the earlier failures.

Pathology review is semantic, with per-case reasons and review coverage retained in audit/technical_annotations. Exact prior traces reuse preserved annotations; items2864 and2143 use documented positive-witness sections plus the complete final channel. This is single-agent review, not independent inter-rater reliability.

The cause of any prefix divergence is not established. It was not used to tune the runtime, sampling settings, cohort, or completion gates.

Prefix-matching capped trajectories that later finalize support a budget limitation for those trajectories; prefix-matching trajectories still uncommitted at81920 support persistent nonconvergence under this recipe. Neither result is a task-performance conclusion.

Fresh validation was frozen before phase1 using SHA256(stage12tr-fresh-validation-v1|family_id),5MC/7open, excluding original12. It was run only after the same12 gate passed.

No repetition threshold, third cap, decoding search, full61-family T study or correctness scoring. Raw outputs/token IDs and R1–R5 labels are retained. Resource accounting includes startup, hard2.5GPUh per phase; all released at closure.

Final allocated compute: 1.718611 GPU-hours, 24 new calls, 0 reused calls. All allocations completed exit0 and were released. No retries or downloads.

Fresh-job engine teardown emitted a client/NCCL warning after all12 output and worker-exit receipts were saved; Slurm completed exit0. No generation was retried.

Section27 deliverable: [Stage12T-S draft](../../../plan/stage12ts_thinking_scientific_rescue_plan.md) created for separate user authorization; not launched.

[Full responses](../../../reports/stage12cr/v1/index.md).

Technical authorization only: The81920 recipe is validated for a later separately authorized Thinking scientific study; no such study launched.

THINKING_REGIME_VALIDATED
