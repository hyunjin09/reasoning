**Superseding active checkpoint — 2026-09-18T00:43:40.517336+00:00:** Stage8B.1a now authorizes the next224 in the existing order, for256 total. The32-item v2 audit below remains complete/preserved. Active continuation state: [Phase8B.1a](phase_8b1a_bounded_mathvision_discovery.md); no immediate full census or paired/causal launch.

# Phase8B: retrieval-aligned MathVision success/failure

## Current Objective

Execute the user-approved Stage8B v2 plan: T=1.0 MathVision generation and cap-independent benchmark scoring, frozen2B retrieval detection, completion-controlled local success/failure comparisons, same-item confirmation and bounded causal validation; stop with an intervention decision.

## Active Constraints

- ACCESS_POLICY first; local .venv/uv; no global installs or credential access.
- Latest resource amendment2026-09-17: exactly four GPUs on node02, scheduler-managed sbatch. Cancel116487 single-GPU job; preserve completed samples and interrupted evidence. No tmux allocation. Release at batch completion; no idle keepalive.
- Frozen Stage8A detector and native protocol; no outcome-based refit or threshold changes. No intervention or automatic strategic pivot.

## Current State

- Slurm116610 completed all32 T=1.0 audit outputs at2026-09-18 00:46:57KST; wrapper exit0 and empty live user queue verified. Allfour GPUs released. All160 artifact/45 frozen source hashes pass; no code/environment changes during result review. Earlier allfour actual-device parity and26 CPU checks remain valid.
- User-cancelled116487 ran43m12s. Completed item2579 reused byte-for-byte with explicit provenance; interrupted2433 preserved and restarted with original seed.31 unfinished items split8/8/8/7. All32 identities and scientific settings unchanged.
- Fresh32 semantic reviews sealed before detector/outcomes:38 T (33 L+,4 L−,1 unresolved),32 M,30 nonvisual;49,152/623,719 reasoning tokens reviewed (7.88%). Gate1 PASS:23/23 demanding items,35/38 T alignment,6/62 false alarms. One annotator/prefix scope; no causal labels.
- Gate0 operationally passes for the frozen local adapter. Reviewed outcomes12 correct/16 wrong/4 unresolved,28/32 scorable (42.9% accuracy on scorable responses).28 normal EOS;3 no-final caps;1 cap during the final section. Both formatting-only manual extractions were frozen without their ground truths. Initial census feasibility condition met; Gate2 and later analyses pending. No large census/paired/causal/intervention launch.
- Extraction limitation remains frozen: official response scope/MCQ rules/1e-6 arithmetic, explicit local box/answer extraction and blind manual fallback; no external GPT-4o/API credentials. Do not claim exact upstream judge replication.

### Historical v1 pilot (preserved, excluded from v2 primary outcomes)

- Done: approved plan/policies read; full local MathVision Arrow has3,040 rows and embedded images; model/probe artifacts present. No download required.
- Done: Slurm115741 produced32/32 native traces; all160 artifact hashes verified. Both GPUs released, wrapper exit0 and empty live queue verified. Historical Slurm job record is purged; no terminal accounting certificate is available.
- Done: all32 semantic prefix reviews sealed before opening detector/final-answer scores. Gate1 PASS:23/23 demanding items,34/38 T queries aligned,1/60 control false alarms.
- Pending: census continuation/feasibility, whole-trajectory comparisons, same-item confirmation and causal validation. No continuation job is running.
- Most recent useful observation:7 correct,3 wrong,22 capped at40,960 tokens without a final-answer section. Outcome yield and compute are now the bottleneck; remaining3,008 items project to30–33 days on two GPUs before later analyses. This is a small-sample projection, not a whole-stage ETA.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Stage8A detector passes heldout, but transport gate fails | `outputs/stage8a/summaries/stage8a_summary.md`, D-071 | Reuse R without assuming intervention readiness | confirmed |
| Prior node03 launch socket timeout | phase8A memory | Validate actual launch before census | confirmed historical; current cause/status unknown |
| Full MathVision locally available | `outputs/stage7a/cohort/dataset_inventory.json` and current Arrow read | Avoid unnecessary download | confirmed |
| Frozen detector transfer passes within first1,536-token audit | `outputs/stage8b/analysis/transfer_gate_v1.json` | Technical parity is now supplemented by sealed semantic transfer evidence | confirmed; single annotator/prefix scope |
| Only10/32 usable final outcomes;22 caps have no final section | `outputs/stage8b/audit/capped_no_final_answer_verified_v1.json`, `outputs/stage8b/analysis/census_snapshot_v1.json` | Do not treat incomplete traces as wrong or formatting-adjudication cases | confirmed |
| RevisedT=1.0 protocol yields28/32 scorable outcomes and passes frozen transfer | `outputs/stage8b/v2/summaries/transfer32_results.md`, `analysis/census_snapshot_reviewed_v2.json`, `analysis/transfer_gate_v1.json` under the v2 root | Initial census feasibility is met; later cohort/cost gates remain | confirmed, local-adapter/prefix limits |

## Failed Attempts and Lessons

None for Stage8B. Broad allowed-root lookup encountered unrelated permission-denied subdirectories; use the verified exact Arrow path rather than repeat that search.

Historicalv1 output limitation:22/32 traces exhaust the budget without a final answer. Cause unknown. The direct cap/end-marker check ruled out a missing final-section extraction under the old definitions; it did not diagnose model behavior. No v1 retry/refit was performed.

V2 residual limitation:4/32 capped responses remain unresolved after local extraction review. Three no-think traces contain competing/revised proposals;2433 ends during the prescribed post-think scope. These are extraction observations, not cap-implies-invalid. The full upstream GPT-4o fallback is not reproduced, and bounded candidate/tail review does not prove that no alternative extraction could succeed. Do not change the detector or rerun these cases solely to improve the pilot yield.

## Open Candidates

F0 activation, F1 routing, F2 extraction, F3 altered influence, F4 downstream and F5 instability remain hypotheses, not selected diagnoses. FU is the default absent sufficient evidence.

## Next-Step Decision

- Current bottleneck: v2 protocol/transfer revalidation is complete; affordable collection of the larger correct/wrong and local-read cohorts now limits progress.
- Relevant memory: D-068 actual-backend parity; D-071 passive retrieval is not causal grounding. Prior22 caps are a completion observation, not proof of benchmark unscorability under v2.
- Chosen action2026-09-18: verify the completed32-itemT=1.0 batch and GPU release, then seal all32 fresh score-blind semantic reviews before opening detector/final-answer scores. Produce the revised protocol/transfer and outcome-completion result check. Use D-073: cap status is independent of benchmark correctness, and local extraction differs from upstream GPT-4o. No new GPU job during this result check.
- Why: the revised plan explicitly changes temperature, preprocessing/prompt and answer extraction; do not pool the historicalT=0.6 pilot into the main cohort.
- What not to repeat: no cap-implies-unscorable shortcut, unsafe eval, correctness-label detector refit or silent substitution for the upstream GPT-4o extraction fallback.
- Stop/checkpoint condition reached: v2 result check complete and reported. Initial census feasibility passes (87.5% outcomes, both classes, transfer PASS). Next task is a bounded census continuation frozen from the existing order, with the current local-scorer limits preserved. It has not been frozen/submitted in this result-check action. Checklist: `plan/stage8b_v2_execution_checklist.md`.

### Step Result

2026-09-18 v2 result: all32 outputs/reviews verified; Gate0 qualified operational PASS, Gate1 PASS, initial census feasibility met. Gate2 currently12 correct/16 wrong against250/250; Gates3–5 unassessed. Four-GPU wall3h02m,9.01 native GPUh including the reused item;12.13 allocatedGPUh plus0.72 from the cancelled single attempt. Remaining full3,008 census projects8.8–12.3 days on4 comparable GPUs, excluding queue/review/paired/causal work; not a whole-stage ETA. Exactly the result check is complete, not Stage8B. Report: `outputs/stage8b/v2/summaries/transfer32_results.md`.

Historical v1 result:

2026-09-17: technical and scientific Gate1 PASS. Final outcomes7 correct/3 wrong/22 no-final capped;70% among10 completed answers only. The32 reviews cover49,152/988,116 reasoning tokens (4.97%), with38 fixed T events:29 L+,1 L-,8 unresolved. This is not whole-trajectory failure prevalence or a causal label. Gate0 target250 per outcome is not yet met; Gates2–4 are unassessed. Batch wall8h24m, native15.55 GPUh, allocated approximately16.80 GPUh. See `outputs/stage8b/summaries/transfer32_results.md`. The result changes the next decision from transfer validity to affordable usable-outcome collection; high-cap cause remains unknown.

### Submitted — 2026-09-16T14:13:08.679394+00:00

Full3,040 rows/3,028 exact-image families and32-item random audit order frozen. Four CPU tests pass; native observational recorder and source/config snapshot frozen. Submitted Slurm115741 directly through scheduler:node03,2GPUs,16CPUs,100G,1day, no tmux. Technical128-token native/logit and per-head feature parity on both devices precedes science. Batch stops/releases after32items for semantic transfer review.

### Execution checkpoint — 2026-09-16T14:30:46.209760+00:00

Fourteen focused CPU checks pass across passive features, answer scoring and transfer-gate logic. Input-only review of all32 images is sealed:23 visually required,8 text-sufficient,1 uncertain. Annotation window/membership rules and numeric grading are frozen before native outcomes. GPU technical validation is complete; full native traces remain in progress. Do not open scientific scores until the32 semantic reviews are sealed. No causal work, paired seeds or full-census continuation launched. Source snapshot remains unchanged.
