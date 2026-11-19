# Phase 13B: cross-scale Thinking role

## Current Objective

Close the approved Stage13B action at its mandatory technical stop. Cross-scale scientific inference remains unresolved; no follow-on experiment.

## Active Constraints

- Exact source-only 48-family subset of the sealed96; separate technical4; no outcome-adaptive selection.
- Reuse all three Stage13A 4B EQ replicates; 1,440 new scientific calls plus48 technical calls.
- All six local checkpoints pinned; no downloads/substitutions. Preserve historical outputs.
- Fixed mode-specific recipes/caps; initial8 >20% technical-missingness stop; no cap/prompt tuning.
- Target<24/hard32 allocatedGPUh, maximum8 concurrent GPUs, project scheduler/Slurm on nodes02/03/06/07.
- Stop before Phase2 if projected total exceeds32; report completed Phase1 only. Exactly one recommendation, not launched.

## Current State

- Done: source-only seals and 48 technical calls; initial 2B-Instruct gate reviewed and failed with 14/24 pre-outcome truncations. Three other capped answers remain scoreable.
- In progress: None. All 120 outputs reviewed for validity, final report sealed and all allocations released. Pending 8B-Thinking work was cancelled before execution.
- Blocked: further scientific execution is prohibited by plan Section 31.
- Most recent useful observation: the failure remains above the gate after retaining cap-after-answer outputs; it is not an accuracy comparison.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Confirmed 4B EQ gain with three replicates | `outputs/stage13a/v1/stage13a_summary.md` | Reuse, never regenerate | confirmed |
|96 final-QC source families | `outputs/stage12xs/v2/audit/final_source_seal.json` | Source-only subset frame | confirmed |
| All six local variants pinned | `outputs/stage13b/v1/stage13b_checkpoint_manifest.json` | No download or substitution | confirmed |
| Initial 2B-Instruct technical gate failed | `outputs/stage13b/v1/audit/gates/2B_I_EQ_initial8.json` | 14/24 missing; Section 31 requires STOP | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Stage13A execution |13 requests interrupted by wall limit | scheduler TIMEOUT | Finite shards with adequate reservation; immutable receipt recovery | Do not extend running Slurm limit or rerun completed outputs |
| Stage13A bootstrap implementation | numerical zero can appear tiny-positive | supported by integer regression tests | Integer replicate-count bootstrap | Do not use floating residual as evidence |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Small-model post-evidence benefit | confirmed 4B result motivates specified2B contrast | frozen primary2B EQ gate | unresolved; not tested to completion |
| Scale role shift | image/EQ attenuation may change with scale | common-family2B-vs8B interaction | unresolved; not tested to completion |

## Next-Step Decision

- Current bottleneck: initial 2B-Instruct missingness exceeds the frozen 20% gate.
- Relevant memory item used: immutable five-call stop-trigger proof and completed 14/24 gate; preserve D157's confirmed 4B result.
- Chosen next action: STOP. Validity review, accounting and CROSS_SCALE_ROLE_UNRESOLVED report are complete.
- Why this action: Section 31 explicitly requires a technical stop rather than cap or prompt modification.
- What not to repeat: no tuning, reruns, remaining 40-family cells, native scientific phase or inference from this incomplete study.
- Stop condition: all started calls archived, allocations released and final report verified; no follow-on.

### Step Result

- Action taken: source-only seal, 48 technical calls, frozen initial-eight EQ tranche and mandatory-stop closure.
- Result: 2B-Instruct missing 14/24, 2B-Thinking 1/24, 8B-Instruct 2/24. New scientific correctness was not graded.
- Evidence saved: `outputs/stage13b/v1/stage13b_summary.md`, `stage13b_decision.json`, and `audit/final_verification.json`.
- Failure or issue: pre-outcome truncation under the frozen protocol. Cause unknown; no runtime repair or protocol tuning attempted.
- Lesson learned: cap hits and technical missingness differ; retain the three 2B-Instruct cap-after-answer calls.
- Next implication: retain Stage13A's confirmed 4B result; no cross-scale scientific conclusion. All GPUs released (3.269722 GPU-hours).

## Phase0 launch receipt

2026-10-04T02:35:42.529881+00:00: all six local checkpoint hashes and48 CPU-rendered inputs verified. Scientific48/technical4/initial8 and1488fresh seeds frozen.19,705 historical files hashed. Seven CPU tests pass. Technicaljobs134496–134501 RUNNING (node02/06/07),150-minute maximum each;15GPUh conservative reservation, actual finite execution releases early. Reused4B initial8 reviewed for technical status only. No new scientific or paired correctness outcomes opened.

## Phase0 result and Phase1 decision — 2026-10-04T02:54:25.247450+00:00

48/48 technical calls saved; input/checkpoint/backend checks pass.44 scoreable,4 pre-outcome caps; all4missing and one additional cap-after-final are2B Instruct. Otherfive checkpoints normal-stopped all8calls. Repetition is retained as behavior; cap-after-unretracted21 is scoreable. Full distinct-paragraph review supports four missing decisions; cause unknown, no runtime failure, GPU94percent utilization observed. Technical allocation1.113889GPUh; all released.

Next-Step Decision: the plan specifies the numerical missingness gate on the frozen scientific8, not these technical4. Proceed unchanged with96 initial EQ calls (24 per2B/8B mode); do not launch remaining40 until all four arm gates pass. More than4/24missing triggers STOP. Reused4B initial8 passes22/24I and24/24T. No scientific correctness opened. Eight120-minute maximum jobs reserve16GPUh; total committed17.114 withinhard32.

## Mandatory technical STOP — 2026-10-04T03:17:08.736551+00:00

At least5/24initial2B-Instruct calls have individually reviewed pre-outcome truncation (2790r0/r2,964r0,945r1,2045r1), so the20percent gate cannot pass even if every remaining slot is scoreable. `audit/stop_trigger.json` freezes exact response-only evidence; no correctness or paired result used. Pending8BThinking jobs134553/134554 cancelled before execution. Already-running2BThinking and8BInstruct batches finish unchanged;2BInstruct jobs have completed. No remaining40 or native scientific phase authorized after this gate.

Next-Step Decision: complete own-response technical review of all already-started calls, capture all terminal resource receipts, preserve historical outputs, publish mandatory-stop report and exactlyone plan-prescribed recommendation. Do not tune prompts/caps, retry model behavior, launch a repair or infer a cross-scale accuracy effect. Cause of repetition remains unknown.

## Closure — 2026-10-04T03:41:11.757219+00:00

All 21 named artifacts are present, with unavailable inference/figures explicitly marked not estimable. 120 full-response pages are indexed. 19,705 historical files, frozen inputs and generation code are unchanged. Twelve GPU jobs completed and two pending jobs were cancelled; all allocations released. Phase 3 correctness/QC and Phase 4 sensitivity were not reached. Exactly one plan-prescribed recommendation is recorded, not launched. Scientific completion is false; the authorized technical-stop action is complete.
