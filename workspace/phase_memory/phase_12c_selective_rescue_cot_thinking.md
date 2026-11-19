# Phase12C: selective rescue by prompted CoT and native Thinking

## Current Objective
Execute the approved Stage12C plan on the frozen61 MathVision families, estimating C/T rescue of B1 and B4 without altering Stage12B-S labels.

## Active Constraints
- Same61 families/157 E* facts and all previous E/N/O/technical/pathology labels remain immutable.
- Identity-only12-family sanity subset; both arms need12/12 valid inputs,>=10/12 scoreable,<=1/12 pre-outcome truncation. No repetition exclusion.
- C is exact original image/question plus ` Let's think step by step.` on the same4B Instruct checkpoint and32768-token recipe.
- T uses pinned4B Thinking; user prospectively approves sampled40960,temperature1.0/top-p.95/top-k20/repetition1/presence0; synthetic greedy512 is not inherited.
- No correctness before technical validation; separate-arm correctness and trace-evidence packets; mandatory ambiguity reviews and deterministic20% audit.
-122 total calls maximum, sanity included; target<6/hard8 new allocatedGPUh. Scheduler/Slurm only, standing maximum8 GPUs.
- No E/N/O regeneration, C/T oracle, interventions, new benchmarks or automatic follow-on.

## Current State
- COMPLETE / TECHNICAL_STOP at the prescribed sanity gate. All24 calls saved and technically reviewed; correctness unopened.
- C:12 valid inputs,11 scoreable,0 pre-outcome caps; PASS. T:12 valid inputs,10 scoreable,2 pre-outcome caps; FAIL (maximum1).
- T2198/T3011 hit40960 while still in the native Thinking channel, without final responses. C2013 ends ambiguously after3767 tokens. Repetition is not an exclusion.
- All1742 historical files,14 frozen specification files and13 generation-source hashes unchanged. Same61 families/157 E* facts and sealed labels.
-17 required artifact paths produced. Scientific scoring/transitions/trace tables empty and explicitly NOT_RUN_TECHNICAL_STOP; P1–P4 null. Five scientific figures not applicable after failed gate.
- Slurm128009/node02 and128010/node03 COMPLETED0:0 and released.0.703611 allocated GPUh; no retries, downloads or environment mutation.
- Remaining98 calls, scientific scoring, and recommended follow-on NOT_LAUNCHED.

## Evidence That Matters
| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
|B1=11,B4=11; main profile informative|outputs/stage12bs/v1/stage12bs_profile_decision.json|Approved primary rescue strata|confirmed|
|Prior4B Thinking greedy512 and native think template|outputs/stage9a5/v1/config.json; stage9a5_qwen3_4b_thinking_spec.md|Differs from Stage12C default; clarify before outcomes|confirmed|
|B1 E− is not synonymous with proven visual misread|D136|Keep evidence-recovery wording and subtype split|confirmed|

## Failed Attempts and Lessons
No failed Stage12C execution attempts. Do not resolve the historical-recipe mismatch by outcome-guided tuning.

## Open Candidates
Only execution of the approved Stage12C study, under the approved prospective T-recipe clarification. No new research direction.

## Next-Step Decision
- Current bottleneck: the frozen sanity gate failed because Thinking has2/12 pre-outcome caps, above the maximum1/12.
- Confirmed: C valid12/scoreable11/caps0; T valid12/scoreable10/pre-outcome caps2. All24 outputs exist; both Slurm jobs COMPLETED0:0 and released.
- Relevant memory: D134 separates pathology from validity. Repetition does not drive this stop; no scratchpad guess is promoted because a cap was reached.
- Chosen action: close Stage12C at its prescribed TECHNICAL_STOP boundary, preserving all evidence and documenting scientific endpoints as not evaluated.
- Do not launch:98 remaining calls, scoring, prompt/decoding variants, or a follow-on study.
- Diagnosis: unknown. Successful input/receipt checks do not explain the noncompletion behavior.

### Step Result
Closed at the approved sanity stop boundary. Evidence: outputs/stage12c/v1/stage12c_technical_sanity.json; stage12c_summary.md; audit/technical_behavior_summary.json. Input checks and completion receipts are valid; cause of noncompletion remains unknown. A teardown warning follows saved complete outputs and is documented separately in audit/shutdown_warning_review.json. Exactly one recommendation: separately approved technical validation of the4B Thinking MathVision completion regime before any rerun. Recommendation not executed. Closure timestamp: 2026-09-29T14:56:56.684411+00:00.
