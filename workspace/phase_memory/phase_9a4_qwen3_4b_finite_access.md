# Phase9A.4: Qwen3-4B baseline repair and finite access

## Current Objective
Execute the approved bounded4B/512-token repair, then test finite access only
after FULL validity. Preserve the calibrated Qwen2.5 reference.

## Active Constraints
- Original Stage9A.4 plan and plan/stage9a4_execution_protocol_v1.md.
- Frozen32 primary images/64queries; conditional16 reserve; no prompt/task search.
- Native DeepStack, greedy BF16,512cap, model-wide temporal masks only.
- Scheduler/Slurm only, at most4 available authorized A6000 GPUs; no next study.

## Current State
- Complete / STOP: Outcome B; valid4B FULL baseline, selected128.
- FULL45/64; ZERO28/64, token6437/64, token12846/64.
- Null-sink ZERO21/64;12843/64, point-preserving but95% interval crosses5pp.
- No256/reserve triggered.341 scientific generations;0.562GPUh; all GPUs released.
- Nine CPU tests, seven final audit groups and four figure pairs complete.
- No blocker and no further authorized work remains.

## Evidence That Matters
| Evidence | Source | Why it matters | Status |
|---|---|---|---|
| Valid instrument cannot rescue invalid comparator | D-102 / Stage9A.3 summary | FULL gates precede science | confirmed |
| 4B checkpoint present,36 decoder layers | local pinned config | Validate actual layer count; no download | confirmed |

## Failed Attempts and Lessons
No Stage9A.4 failures. Preserve Stage9A.3 EOS-safe technical probe lesson.

## Open Candidates
None active. The next experiment requires a new user instruction.

## Next-Step Decision
- Bottleneck resolved:4B/512 FULL is valid and a finite cutoff is selected.
- Evidence: primary128 damage−1.5625pp CI[−4.6875,0];64 damage12.5pp.
- Chosen action: complete the bounded comparison and STOP.
- Recommendation only: characterize the Qwen2.5→Qwen3 regime shift before Thinking attribution.
- Do not infer a DeepStack cause or exact boundary. Null-sink128 CI[0,7.8125] leaves uncertainty around5pp preservation.
- No next experiment launched.

### Step Result
R0 complete 2026-09-27T03:28:29.099205+00:00:45/64 correct,64/64 CoT,60/64 valid/EOS,4 capped;G1-G5 pass. Eight FULL no-op examples exact. All FULL workers released.


## Historical boundary — R0 passed
Bottleneck: exact4B temporal-mask validity. Use verified36-layer checkpoint and prior EOS-safe validator lesson. Run eight fixed technical examples at0/64/128/256 with unchanged native DeepStack; then exactly ZERO and64. No R2 until its outcome gate.


## Historical boundary — R1 sequential gate
R1 complete: ZERO28/64 (damage26.5625pp, CI10.9375–42.1875);token6437/64 (damage12.5pp, CI3.125–21.875). Exactly the approved R1-B branch applies: run128 only. No reserve selected and no control yet. All prior outputs retained.


## Historical boundary — selected128
Token12846/64 (71.875%), damage−1.5625pp CI[−4.6875,0], all bootstrap draws within5pp. Select128 prospectively for bounded control. No token256; reserve gate false (not uncertainty-limited). Run only primary FULL/ZERO/128 null-sink, then final comparison/audit/report and STOP. Exact standard FULL reuse remains valid.


## Final closeout
Report: outputs/stage9a4/v1/stage9a4_summary.md. Required/conditional artifacts and figure hashes: stage9a4_artifact_index.json. Independent audit: audit/final_validation.json. Native image/query/prompt/scoring inputs and reused Stage9A.3 evidence verified unchanged. The standard64 effect is larger than Qwen2.5 on paired32 images by15.625pp [4.6875,26.5625]. No architecture attribution.
