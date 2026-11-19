# Phase 14B: Large-scale math phenomenon

## Current Objective
Execute the approved large-scale 4B native-image and equal-evidence comparison, MathVerse modality profile and frozen confirm-300 robustness; stop at Stage14B closure.

## Active Constraints
- Stage14A artifacts, cohorts, golds, evidence and source judgments remain immutable.
- Phenomenon establishment only; no mechanism, scale, new benchmark or next-stage experiment.
- Project scheduler/Slurm, existing project-local environments; up to eight available A6000 GPUs on node02/03/06/07. Finite jobs release immediately after queues finish.
- Freeze prompts, recipes, seeds, scoring, technical handling and inferential rules before new outcomes. Missingness never silently becomes wrong.

## Current State
All 17,536 main and 9,600 fresh confirmation calls are complete, reviewed and sealed; zero technical missingness. Primary, secondary and three-seed robustness analyses, five PNG/PDF figures, resource accounting and final validation are complete. All GPU allocations and CPU jobs are released. No follow-on stage was launched.

Main paired native Thinking gain +7.20 pp (95% CI 5.67–9.08); Instruct evidence rescue 234/418 scored failures =55.98% (31 unresolved); post-evidence Thinking gain +14.69 pp (12.10–17.39). All three frozen criteria pass. Native and post-evidence gains remain positive in all three frozen confirmation seeds; this is decoding robustness, not untouched independent replication.

Final report: `outputs/stage14b/summaries/stage14b_final_summary.md`. Resource total: 193.218 observed/proxy GPU-hours; no active allocations. Stage complete / STOP.

## Evidence That Matters
| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| 3040 native MATH-Vision, 1000 final-QC E*, 788×6 MathVerse | outputs/stage14a/v1/stage14a_summary.md | Exact frozen populations | confirmed |
| MathVerse 350 all-checks-pass families; known source defects remain | outputs/stage14a/v1/stage14a_mathverse788_family_manifest.json | Freeze source-only clean and sensitivity layers | confirmed |
| Validated 4B BF16/vLLM model-specific recipes | outputs/stage13a/v1/config.json | Reuse checkpoints/runtime, explicitly preregister caps | confirmed |
| Alias components and complete catalog exposure | workspace/decision_log.md D166 | Family clustering and no untouched claim | confirmed |

## Failed Attempts and Lessons
Initial preflight imports failed before requests due to local statistics.py shadowing stdlib; renamed with regression evidence, original logs preserved. Formatting/grading defects are repaired with versioned receipts and same-agent review; a second adjudication layer preserves prior automatic records. Historical scoring distinguishes cap-before-final from an incorrect committed answer. No protocol tuning by accuracy.

## Open Candidates
No remaining authorized action in Stage14B. Exactly one recommendation: Review and authorize Stage14C task-selectivity testing, taking seed robustness and source limitations into account. NOT_LAUNCHED.

## Next-Step Decision
- 2026-10-08T13:50:33.598109+00:00: Completion criteria met; STOP at Stage14B.
- Evidence: `audit/completion_validation.json`, `audit/artifact_catalog.json`, three analysis seals, arm scoring/QC seals and `audit/final_cpu_exit_v1.json` under `outputs/stage14b/`.
- Selected action: close documentation and preserve all evidence. No generation, tuning or follow-on experiment.
- Validated native model recipes differ; this is not a causal mode toggle or equal-compute comparison. E* rescue does not isolate pure perception, and the post-evidence gain identifies no downstream mechanism. Source/gold defects, unresolved answers, same-agent review and dependence limits remain explicit.

### Step Result
Main paired native Thinking gain +7.20 pp (95% CI 5.67–9.08); Instruct evidence rescue 234/418 scored failures =55.98% (31 unresolved); post-evidence Thinking gain +14.69 pp (12.10–17.39). All three frozen criteria pass. Native and post-evidence gains remain positive in all three frozen confirmation seeds; this is decoding robustness, not untouched independent replication.

Validated native model recipes differ; this is not a causal mode toggle or equal-compute comparison. E* rescue does not isolate pure perception, and the post-evidence gain identifies no downstream mechanism. Source/gold defects, unresolved answers, same-agent review and dependence limits remain explicit.

The following entries preserve historical execution decisions and status snapshots.

## Technical startup repair boundary — 2026-10-05T07:00:09.095545+00:00
136000 and136001 failed before submitting model requests. Supported cause: unsealed analysis filename statistics.py shadowed stdlib statistics.median in vLLM child imports. Regression reproduced failure, renamed to inference_math.py, six import/statistical tests PASS. Original source/logs preserved. Config, worker, prompts, seeds and cohorts unchanged. Retry24preflight calls once with node-agnostic scheduler routing; no scientific retry/tuning.

## Queued execution handoff
- Latest technical jobs:136015(I),136016(T),2h/oneGPU each, node-agnostic a6000 authorizednodes only. Initial jobs136000/136001 terminalFAILED;0model calls,0.085278GPUh total.
- CPU coordinator136019 is bounded48h after allocation (49h Slurm time),0GPUs. `scripts/stage14b/coordinator.py` waits for the24repaired technical receipts, performs explicitly automatic response-only extraction/format coverage (not human annotation), validates hashes/seed replay, and launches main3I+5T workers only onPASS. No tuning/retry/newstage/confirmation. Stops on failure or after all main workers have at least3completed samples.
- Snapshot Slurm expectations: GPU preflight starts~2026-10-06 11:47/13:47KST; coordinator~02:50KST. Predictions are unstable and queue wait excluded from estimates.
- Main17536 +confirmation9600scientificcalls; historical throughput reference~404GPUh, range400–600GPUh excluding manual scoring.50–75hours if8GPUs remain simultaneously usable; current capacity does not establish that wall-clockETA. Continuous refill may improve throughput; update from observed main work.
- No main/confirmation outputs or scientific findings. Full source/spec/code hashes and25CPUtests saved. `analysis_implementation_seal.json` complements original prospective seal.
- After main completion: raw freeze, all response-only ambiguities and10%hash scoreQC, primary seal, secondary sensitivities, then confirmationseeds1/2, figures/finalreport and STOP. See executionchecklist/report.

## Preflight resolution / main launch — 2026-10-05T08:39:35.579592+00:00
All24technicalcalls complete. Manual reviewv2 resolves the6Instruct MathVerse normal-stop pair outputs (source explicitly Choose2) and common markdown/LaTeX final formats. No native gold/accuracy assessed. One Instruct native32768cap output has unresolved conflicting final candidates and remainsUNSCORABLE. Both synthetic shortseed replays exact. GatePASS; originalautomaticFAIL/holdimmutable. No generation/selection/recipe changes.
Eightmainjobs136129–136136 submitted,0/17536complete atthisboundary, allpending. CPU-only observer136145 verifies≥3finishedrequests perworker thenexits; no newlaunch/scoring. Confirmatory9600pendinglaterprimary/secondaryseals. TechnicalGPUallocation0.759444h. Evidence:preflight_response_review_v2.json,preflight_validation.json,technical_gate_release.json,main_monitor_launch.json.

## Progress check — 2026-10-05T09:08:02+00:00
All eight main GPU jobs 136129–136136 are RUNNING (five node02, two node06, one node07); no pending GPU job or worker/request failure receipt. Main generation 459/17,536 (2.62%): native Instruct 249/3,040 and Thinking 210/3,040. Equal-evidence and MathVerse queues have not yet started. All workers have 18 active requests. Startup observer 136145 completed successfully. Preflight remains 24/24 complete. Early main-only ETA approximately 20–40 hours, provisional: recent 10-minute throughput is about 989 calls/hour combined, but fixed shard imbalance projects the slowest worker at about 32 hours (about 40 hours over its last five minutes). Later panel lengths remain unmeasured. The 9,600 confirmation calls and scoring/analysis are additional and remain gated. No scientific outcomes inspected. ETA evidence: outputs/stage14b/audit/eta_20261005T090504.json.

## Progress / OOM handling check — 2026-10-05T09:31:06.445276+00:00
692/17,536 main calls complete (native I373, T319); eight workers running with18 active requests each. No OOM/error log matches or failure receipts. Fatal OOM stops the affected worker; completed outputs survive and other workers continue. Singleton retry is preregistered but requires a versioned relaunch; no automatic recovery supervisor currently runs. Evidence: outputs/stage14b/audit/oom_handling_check_20261005T093106.json. No execution or protocol changes.

## OOM implementation and deployment complete — 2026-10-05T09:53:51.544333+00:00
OOM skip/continue implementation and deployment complete.42CPUtests PASS, including subprocess OOM-to-next-sample recovery. CPU-only supervisor136212 is RUNNING onnode07 and has confirmed all8current main workers. Identifiable GPU OOM samples become final TECHNICAL_MISSING and are skipped; a fresh engine continues. When a batched crash cannot identify a culprit, interrupted requests resume once at singleton concurrency. Healthy workers are not restarted; all8remain RUNNING with no failure receipts. Original specification/source/code seals are unchanged. At most one replacement allocation per original, maximum8GPUs. No scientific outcomes used or further phase launched.
Pending CPU submissions136205/136206 were cancelled and preserved; no GPU job was cancelled. Evidence:outputs/stage14b/audit/oom_recovery_deployment_v1.json and oom_recovery_validation_v1.json.

## Progress and revised ETA — 2026-10-05T12:28:50+00:00
Main generation2,750/17,536 (15.68%): native Instruct1,465/3,040 and Thinking1,285/3,040; native combined2,750/6,080 (45.23%). Equal-evidence0/2,000 and MathVerse0/9,456. All eight workers136129–136136 RUNNING with18active requests each; no current worker/request failures or OOM skips. CPU OOM supervisor136212 RUNNING with fresh heartbeats. Recent combined throughput~623calls/hour over both60and120minutes. Native tail projection8–13hours; main-only remaining estimate~30–55hours, provisional because later panels are unmeasured. Slowest-shard main projections:31.7h using120minutes,42.3h using60minutes,53.9h using30minutes. Long Thinking generations now dominate the tail; active requests reach~81.5k tokens under the frozen81,920cap. Additional9,600confirmation calls and scoring/review/analysis are excluded from these estimates. No scientific outcomes inspected.
Evidence: outputs/stage14b/audit/eta_20261005T122921.json.

## User-requested03:00 watcher continuity — 2026-10-05T12:47:37.457118+00:00
User reports site may cancel CPU-only watcher for lowGPUutilization at03:00KST. Queue one0GPUdependent replacement after136212terminates, not before2026-10-06T03:05:00+09:00, reusing unchanged watcher and original deadline. Existing running jobs stay untouched. This is execution continuity only; no scientific outcomes inspected.

### Nightly watcher continuity result — 2026-10-05T12:48:47.957547+00:00
User-authorized nightly watcher continuity configured: CPU-only standby136370 is PENDING with verifiedafterany:136212 dependency and not-before2026-10-06 03:05KST. Current watcher136212 remains RUNNING. Standby requests1CPU/2G/0GPUs onnode07; it reuses the sealed implementation, persistent skip/recovery state and original2026-10-08T09:42:40UTC deadline. If current watcher survives, standby remains dependent. If it terminates, standby can run after03:05 subject to Slurm scheduling. If all watched queues are terminal, it exits without further GPU work. One standby for the upcoming cleanup; it is not protection against cancellation of pending jobs or an indefinite restart chain. No healthy job cancelled and no GPU added.
Evidence:outputs/stage14b/audit/oom_watch_standby_launch_v1.json.

## Progress / nightly watcher handoff — 2026-10-06T00:46:22+00:00
Main generation12,381/17,536 (70.60%). NativeMATH-Vision I3,040/3,040 and T3,040/3,040 complete; equal-evidence I1,000/1,000,T573/1,000; MathVerse I4,728/4,728,T0/4,728. All8,768Instruct calls complete; jobs136129/136130/136131 have complete=true exits with0technical failures and released GPUs. Five Thinking jobs136132–136136 remain RUNNING with18active requests each, noOOM/error matches or technical-failure receipts. CPU backup136370 started03:05:10KST06Oct and is healthy; original136212ended around the cleanup window, but Slurmaccounting is disabled and its exact terminal reason is not recoverable here. Recent Thinking throughput~189calls/hour over60minutes and204/hour over120minutes. Equal-evidence remaining~2–4hours; main-only remaining~25–35hours, extrapolated from current Thinking throughput. ThinkingMathVerse throughput is not measured yet, so ETA may change materially. The9,600confirmation calls plus scoring/review/analysis are additional. Next-night CPU standby136898 queued after136370, notbefore03:05KST07Oct, under the same original deadline;0newGPUs. No scientific outcomes inspected.
Evidence:outputs/stage14b/audit/eta_20261006T004656.json; worker exit receipts136129–136131; oom_watch/136370/started.json; oom_watch_standby_launch_v2.json.

## Main nearing completion — 2026-10-06T06:25:00.939643+00:00
Main generation16,966/17,536 (96.75%),570remaining. NativeMATH-Vision6,080/6,080 and equal-evidence2,000/2,000 complete. MathVerse Instruct4,728/4,728,Thinking4,158/4,728. Six main GPU workers completed successfully and released allocations; only136133(node02) and136136(node06) remain RUNNING. No main worker failures, technical missingness or OOM skips. CPUwatcher136370RUNNING; backup136898pendingdependency. Remaining main ETA~1.5–3hours, including allowance for final long requests. Recent per-worker30/60/120-minute projections for slower136133 are1.19/1.37/1.63hours, and faster136136~0.41/0.51/0.65hours. MathVerse throughput is much faster than the prior equal-evidence extrapolation. Scoring/review,9,600confirmation generations and finalanalysis remain outside this ETA. No scientific outcomes inspected.
Evidence:outputs/stage14b/audit/progress_20261006T062500_compact.json and eta_20261006T062418.json.

## Main seals / confirmation launch — 2026-10-06T09:29:52.898304+00:00
Main native paired gap+7.20pp, Instruct rescue234/418resolved (31unresolved), post-evidence gap+14.69pp. All three frozen main criteria pass; confirmation remains. Eight finite1GPU confirmation jobs137175–137182 queued on authorized A6000nodes; no separate OOM watcher. Exact same frozen9600calls,2I+6Tworkers. Technical-only token/call projections55–80GPUh (~8–12h simultaneous, excludes queue/review). No Slurm start estimate. Use scoring_v6 wrapper for all closing/analysis to preserve immutable adjudication precedence; new5-test accounting_v2 prevents stale purged-job/CPU GPU-hour inflation. Primary/secondary results and same-agent review provenance preserved. Next: confirm startup and completion, close confirmation scoring/QC, analyses/figures/report, STOP.

### Queue boundary / closure preparation — 2026-10-06T09:35:58.017425+00:00
Slurm estimates firstconfirmation137175 start07:47:55KST07Oct, othersunknown. All eight currentlyPENDING Priority,0allocatedGPUs. Pendingwalltime lowered72h→24h based on measured<12hperworker forecast, preservinginitialreceipts; no scientificchange. Dependency-bound CPU137183 runs rawvalidation+Instructgold-blind extraction once workers terminate; noGPUlaunches/manualreviewclaims. Final closure script finish_v2.py prepared and gateverified torejectmissingconfirmation; resource accounting_v2.py has5passingtests. Stage remains incomplete until queuedGPUwork and actualconfirmationreview finish. No follow-on.

## Confirmation progress — 2026-10-06T13:14:56.949524+00:00
Confirmation progress at 22:14 KST, 6 October: 648/9,600 calls complete (6.75%): Instruct358/4,800, Thinking290/4,800. All completed calls are MATH-Vision native; equal-evidence and MathVerse follow. All eight GPUjobs137175–137182 RUNNING (sixnode03, twonode06),18active requests each, fresh heartbeats,0failure receipts/OOMskips/technical missing records and no OOM/error log matches. OnlyCPU137183isPENDING Dependency, correctly waiting for allGPUjobs; noGPUjob is pending. Token-weighted projection uses same-source main-seed lengths and current250–292outputtokens/second perGPU: slowest nominal remaining6.6h. Allow7–10h remaining generation for batching/prefill/seed-length/tail variation, approximately05:00–08:00KST07Oct. Review/scoring, stability analysis, fivefigures and finalreport remain afterward. No scientific confirmation outcomes inspected; nojob/protocolchanges. Evidence: outputs/stage14b/audit/confirmation_progress_20261006T131211.json and confirmation_eta_20261006T131335.json.

## Final closure — 2026-10-08T13:50:33.598109+00:00
All 17,536 main and 9,600 fresh confirmation calls are complete, reviewed and sealed; zero technical missingness. Primary, secondary and three-seed robustness analyses, five PNG/PDF figures, resource accounting and final validation are complete. All GPU allocations and CPU jobs are released. No follow-on stage was launched.

Confirmation scoring: Instruct 2,408 correct /2,281 wrong /111 unscorable; Thinking 3,586 /1,200 /14, each out of4,800. All prescribed ambiguity, fixed hash-QC and supplemental cap/nonletter-gold reviews sealed. CPU138468 analysis/figures and CPU138485 final verification completed. Original source, scientific protocol and closure code hashes unchanged. Same-agent review disclosed. Exactly one recommendation: Review and authorize Stage14C task-selectivity testing, taking seed robustness and source limitations into account. NOT_LAUNCHED.
