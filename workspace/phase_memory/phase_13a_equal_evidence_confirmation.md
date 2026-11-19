# Phase13A: Confirmatory equal-evidence Thinking advantage

## Current Objective
Execute the approved full-cohort, three-seed I-EQ/T-EQ comparison, apply its frozen decision gate, give exactly one recommendation and stop.

## Active Constraints
Exact X-S96, original Q/E*/gold/renderings and source seals. No image or added instruction. Pinned 4B models and model-specific 32768/81920 caps. 576 primary calls; at most72 conditional cap-matched calls. Up to8 GPUs on02/03/06/07 through scheduler/Slurm; target<10/hard14 allocated GPU-hours. No follow-on.

## Current State
- Complete:576 logical calls, all technical/scoring reviews,185 second reviews,11 long-response timing reviews, primary inference, four PNG/PDF figure pairs and final verification.
- Decision: EQUAL_EVIDENCE_THINKING_ADVANTAGE_CONFIRMED. Primary n84,+11.11pp,95% CI[5.56,17.06];32k-comparable n82,+11.38pp,[6.10,17.48].
- Optional cap-matched assay not triggered. All9 allocations released;8.568611 allocatedGPUh,589 submitted attempts including13 interrupted requests.
- Prior15,807 files and frozen source/input seals unchanged. No follow-on launched.

## Evidence That Matters
| Evidence | Source | Why it matters | Status |
|---|---|---|---|
| Selected-panel confirmation insufficient | D155; outputs/stage12ys/v1/stage12ys_summary.md | Authorizes full-cohort confirmation, not favorable subgroup search | confirmed |
| Historical E*/source cohort sealed | outputs/stage12xs/v2/audit/final_source_seal.json | Reuse exact inputs without re-annotation | confirmed |

## Failed Attempts and Lessons
Job133782 hit its90min Slurm time limit with59/72 results preserved;13 input-only partial attempts archived and recovered once in133885 with the original worker/prompts/seeds/recipes. The original TIMEOUT remains visible. Synthetic numerical boundary repair v2 prevents exact-zero bootstrap lower bounds becoming positive through floating-point residuals. Same-agent QC is not independent reliability.

## Open Candidates
None active. Optional cap-matched calls were not triggered; exactly one cross-scale recommendation remains unlaunched.

## Next-Step Decision
- Current bottleneck resolved: the full-cohort repeated-seed equal-evidence confirmation passes its frozen gate.
- Chosen action: STOP Stage13A after verification; no further4B subgroup/prompt search.
- Exactly one recommendation: Run a cross-scale image-vs-equal-evidence study at 2B/4B/8B to test whether the functional role of Thinking changes with model size.
- Recommendation is not authorized for execution; no follow-on launched.
- Evidence: outputs/stage13a/v1/stage13a_primary_inference.json; audit/final_verification.json; audit/independent_table_recalculation.json.

### Primary launch — 2026-10-03T15:55:54.955526+00:00
Exact576 calls/8shards72each;12GPUh maximum primary reservation under14hardstagecap. Source-only optional24 and72tasks frozen,notactivated. Instruct scoring/QC must close before any Thinking response is displayed. No source/model/data changes.

### Runtime verified — 2026-10-03T16:06:40.388525+00:00
First engine BF16 and all package versions match; first10 saved input/token/seed/recipe receipts pass. Seven pending jobs prospectively reduced hostCPUs4to2 viaSlurm plus project-queue reconciliation; no GPU/recipe/task/seed/prompt changes. Evidence audit/pending_cpu_adjustment.json. Now133777/node02 and133778–133780/node07 RUNNING; fourThinking pending.17own-arm technical decisions; no Thinking responses opened.

### Prospective numerical repair — 2026-10-03T16:23:00.562231+00:00
Synthetic bootstrap boundary regression found floating residual +1.11e-15 at an exact-zero lower bound. Versioned inference_v2/analyze_v2/sensitivity_v2 preserve original sealed sources and use integer signed-thirds sums; same seed, draws, gates and estimand. No scientific scores inspected. Use v2 for final inference. All8 GPU workers active; no GPU or input changes.

### Wall-time feasibility — 2026-10-03T16:52:35.867193+00:00
Three Instruct workers completed/released. Observed Thinking batches20–25min prompted one bounded120min wall-time update attempt, prospectively within13.676GPUh maximum including optional2GPUh. Slurm denied running-job extensions for allfour;90min limits remain unchanged. No escalation/retry. Existing jobs continue; preserve every complete output and assess only actual technical interruption if it occurs. Evidence audit/walltime_extension_check_*.json.

### Instruct scoring closed — 2026-10-03T17:02:35.661115+00:00
288/288Instruct calls saved;182correct,91incorrect,15technicalmissing,273scoreable. All111ambiguity/random second reviews agree (sameagent,notindependent). FourInstruct Slurm allocations completed/released. Thinking responses remain unopened up to I_EQ_scoring_closed receipt; proceed withThinking own-response review,scoreability and32k timing, then scoring/QC. Original numerical sources preserved; inference_v2 selected for final analysis.

### Actual scheduler interruption — 2026-10-03T17:41:25.841690+00:00
Job133782 timed out at90min with59/72 saved; total563/576. No engine failure;13 partial input records and allcompleted outputs will be preserved. Next-Step Decision: recover only these13 frozen logical calls with original worker/recipe in one75min GPUjob; totalworstcase including conditional2GPUh =11.545<14. Sameprompts/seeds/caps; no outcome-based selection.
