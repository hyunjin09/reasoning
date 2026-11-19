# Phase14C-V: BlindTest representation and evidence contract validation

## Current Objective
Execute Stage14C-V through G1–G6 under the approved recovery amendment: 2,642 physical calls and 32 GPU-hours; stop at closure or a genuine gate failure.

## Active Constraints
- Preserve all Stage14C source, output, scoring and closure artifacts.
- Approved R: all300 historical eligible families, R0/R1/R2 × two checkpoints. Approved C: old D1 100 plus100 source-hash-selected remaining families, C0/C1 × two checkpoints.
- 2,600 planned scientific results; total physical-call ceiling 2,642 including interrupted attempts, 24 preflight calls, and eight recovery context replays. Approved 32 GPU-hours; max8 concurrent authorized GPUs via scheduler/Slurm.
- Source-equivalent content only; no gold, derived crossing counts, new coordinates or solutions in R1/R2. C1 only deletes the conflicting answer-only clause.
- Same-agent checks do not establish independent reliability. Cohort previously outcome-observed; selection uses sources only.

## Current State
- Done: read plan, parent phase, policy, historical builders and exact source schema.
- Done: G0 package prepared; 300 image hashes, 1,400 historical receipts and 1,300 review prompts verified; seven CPU design tests pass.
- G3 complete: all1,800R outputs,198response-only/scoreQC reviews, primary andcompanionanalysis sealed. G4 C800calls submitted140186/140188/140190/140192; C0 runningnode07, others pending at launch.
- Approved recovery: exact66 calls (58 missing primary responses +8 context-only replays), automatic between-wave deadline guard, 3h allocation. No changes to scientific inputs. Existing1742 responses extracted;192 response-only reviews recorded; no aggregate correctness analysis yet.
- Observation: historical E* is one five-subfact polyline atom. D1 places the evidence request before the native question/answer-only clause; the plan's later/appended wording is schematic, not the historical order.

## Evidence That Matters
| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Negative net supply, limited D1 elicitation | outputs/stage14c/summaries/stage14c_final_summary.md | Motivates separate R and C tests; does not prove their causes | confirmed |
| Five source units and old100 IDs | outputs/stage14c/source/D1_shared_unit_map_v1.jsonl; manifests/D1_source_membership_v1.json | Preserve granularity and membership | confirmed |
| Exact prompt builder | scripts/stage14c/input_adapter.py; materialize.py; materialize_d1.py | Recover original bytes and input order | confirmed |

## Failed Attempts and Lessons
| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Parent changing-batch replay | Token divergence | supported by parent replay receipts | Match fresh engine and batching context | Do not assume universal cross-batch reproducibility |

## Open Candidates
| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Equivalent field structure changes solving | Parent net regressions unresolved | R1/R2 versus fresh R0 | proposed |
| Contradictory instruction suppresses evidence output | Historical request contains both contracts | C1 deletion versus fresh C0 | proposed |

## Next-Step Decision
- Current bottleneck: execution-ready exact manipulations and explicit Gate G0 release.
- Relevant memory: D175 requires net regressions alongside rescue and keeps probe recovery separate from native knowledge.
- Chosen action: prepare G0 review package with original-identity audit, source-only proposed formats and deterministic C membership, CPU invariance tests, frozen inference proposal and resource ceiling.
- Why: this is the mechanically specified next action; no scientific outcome needed for design.
- Stop condition: concrete package validated; request G0 approval as required by plan section8. No generation or new dataset download.

### Step Result
- Original design preparation started 2026-10-09T08:10:53.500825+00:00.

- Action complete 2026-10-09T08:21:34.050969+00:00: `outputs/stage14c_v_blindtest_validation/summaries/stage14c_v_g0_review_package.md`.
- Two historical question templates confirmed (146/154 among all300,49/51 among old100); C1 deletes each matching native answer clause only. Exact source/model/input identity audit passed; no new generation, GPU allocation, download or installation.
- Seven CPU tests and300-family round-trip checks pass. Model shard rehash, source/serialization reread and fresh-engine replay remain G1/G2 requirements.
- Proposed max2,624 calls/24 GPU-hours; approximate7.42 GPU-hour parent-throughput proxy is not a measured ETA.
- Next implication: STOP at G0. Await user approval of concrete package and24 GPU-hour ceiling before G1–G6. Preserve parent evidence and both negative hypotheses.

## Approved continuation — 2026-10-09T08:26:24.374795+00:00

User: “approved”. Exact48-file G0 package verified before release. Approval receipt `outputs/stage14c_v_blindtest_validation/spec/g0_user_approval_v1.json`.

### Next-Step Decision
- Bottleneck: source-equivalent R formats and fixed C contract must pass source/QC freeze before any new generation.
- Relevant memory: parent cross-batch replay diverged; all new model calls must use frozen matching context and bounded technical replay.
- Selected action: complete all300 source/serialization rereads, freeze2600 scientific tasks and20 planned technical calls with24-call ceiling, test fail/stop/budget logic, then run G2.
- Stop condition: G2 passes and releases the already approved R experiment, or any invariance/technical/budget gate fails. No scientific tuning.

## G1 completed / G2 queued — 2026-10-09T08:48:03.627798+00:00

- All300 sources visually reread on15 source-only sheets; all300 pixel-order checks agree. No source/evidence/prompt changes. One inherited unit-metadata label preserved verbatim after a materialization guard caught normalization; no model outcomes existed.
- Frozen1,800 R +800 C scientific tasks;20 planned technical calls,24 technical ceiling.20CPUtests pass, including paired missingness statistics, wave-preserving resume, OOM attribution and atomic global2624attempt cap.
- G1 v1 and execution-only v2 seals preserved; v2 adds an attempt budget shared across workers without changing scientific inputs. Original code snapshots are retained.
- GPU jobs139667I/139668T pending Priority; one GPU/one allocation-hour each,2GPUh conservative reservation and0GPUh observed. CPU139674 has `afterok:139667:139668` dependency. No available start estimate.
- CPU gate automatically checks20technical receipts and10 repeated-prefix comparisons without answer correctness; PASS alone submits six fixed R queues (I1h andT3h per condition;12 requested GPUh maximum before unused time is released). Maximum6 R GPUs within approved8; only authorized A6000 nodes.
- C remains gated on R response reviews, paired analysis and primary seal. No automatic follow-on.

### Next-Step Decision
Wait for Slurm capacity and inspect G2 evidence. The exact bounded continuation is already queued; do not duplicate jobs or alter prompts/conditions/recipes. If preflight passes, review the finite R outputs and complete its seal before C. Any G2 failure holds release for a bounded diagnosis within24technical and2624total attempts/24GPUh.

## Progress check — 2026-10-09T12:44:53.799614+00:00

G2 PASS:20calls and10 exact repeat comparisons. R Instruct900/900complete; ThinkingR0 62/300, R1 54/300, R2 pendingPriority (139760). Active139758node03/139759node02; no recordedOOM/failure/missingness. C0/800, still gated on R primary seal. Raw operational snapshot: `outputs/stage14c_v_blindtest_validation/audit/progress_20261009T124453Z.json`. No scientific outcome aggregation.

### Next-Step Decision
Observed Thinking wave throughput exceeds initial3h job envelopes: R0 approx5–6h more; R1 approx4h more; R2 proxy5–7h from unknown start. Before23:07KST earliest timeout, repair allocation-time scheduling within approved24GPUh, or use existing between-wave checkpoint before timeout. Do not allow a batch timeout then blindly retry: only4 surplus physical attempts remain beyond the2620 planned calls. Preserve all inputs/recipes/wave membership. No scheduler mutation performed in this progress-only check.

## Next-Step Decision — 2026-10-09T13:02:16.768032+00:00
User requested extended limits. First try extending current Slurm allocations in place; requested totals7h R0,6h R1,6h R2 fit conservative23.532777777777778GPUh stage reservation. Preserve engines, all completed outputs and sealed scientific protocol. If Slurm denies extension, drain at existing between-wave boundary and resume unfinished full waves with longer allocations; never cancel active samples. Evidence: audit/time_limit_extension_proposal_v1.json.

## Extended-limit handoff — 2026-10-09T13:07:00.978920+00:00

- In-place `scontrol update JobId=139758 TimeLimit=07:00:00` denied by Slurm. Receipt preserved in `audit/time_limit_extension_attempt_139758_v1.json`; no other in-place retries or privilege changes.
- Existing global `STOP_BETWEEN_WAVES` set. R2 job139760 exited cleanly at checkpoint before any R2 scientific call; actual0.056111GPUh cached. R0/R1 finish their current original18-item waves before exit. No forced cancellation.
- CPU coordinator139879 RUNNING onnode07,0GPUs,30min maximum. It caches terminal allocation durations every15s (sacct disabled), waits at most25min for all three oldjobs, rejects incompleteattempts/partialwaves, verifies hashes, and checks aggregate24GPUh bound.
- After all jobs exit, it archives the drain sentinel and submits only unfinished R queues with limitsR0=5.25h,R1=4h,R2=6h. These are allocation limits based on remaining waves, not token-cap or recipe changes. If checkpoint or budget verification fails, coordinator records HOLD instead of launching. C still requires R primary seal.
- New resume adapter and4regressiontests sealed;13targeted tests passed. Original G1 execution/scientific seal entirely unchanged; no generation preflight rerun is needed because inference code and recipe are unchanged. No Git metadata available in this workspace; new files and versioned hashes preserve this additive adapter.

### Next-Step Decision
Check `audit/time_limit_resume_release_v1.json` and replacementjob heartbeats after the bounded handoff. If `time_limit_resume_failure_v1.json` exists, inspect the direct failure before any resubmission. Never rerun completed calls or allow incompletewave retries to exhaust the2624call limit. Longer allocations remain within24GPUh; no automatic budget increase or new scientific phase.

## Result check / resource gate — 2026-10-10T03:05:47.028251+00:00

- Safe handoff succeeded: old R0/R1 each stopped with90completed, R2with0calls; coordinator139879 then launched139883/139884/139885. No interruption at that first handoff.
- R0T andR1T finished300each; all Instruct conditions300each. R2T saved242/300 then Slurm killed139885 onnode06 at2026-10-10 05:09KST for its6-hour allocation limit. Last heartbeat shows10active calls in wave13;48later calls untouched. NoOOM recorded.
- Supported operational cause: replacementR2 time allocation remained insufficient; existingworker only supported externally signalled between-wave draining and lacked an automatic advance time-limit guard. Do not repeat an unattended finite-time job without that guard.
- Verified all1,742completed input/generation/result receipt triples and originalG1 hashes. Evidence: `outputs/stage14c_v_blindtest_validation/audit/R_partial_receipt_validation_20261010T030319Z.json`. No scientific outcome aggregation, score selection or final comparison. No active/pending Slurm jobs.
- Actual/proxy worker-time sum19.3057GPUh excludes Slurm gaps; conservative allocation charge23.5283GPUh includes full original limits where terminal scheduler records expired. sacct is disabled. Do not present23.5283as measured consumption or replace it with the lower proxy for launch authorization.
-1,772physical attempts already reserved. Minimal10retry+48untouched+800C =>2,630attempts, beyond2,624approved. Requested recovery retains original18-member batch:10needed plus8technical context replays (old8remain primary), then48untouched; expected2,638total. Proposed2,642total cap preserves4spares; proposed32GPUh covers3R+4C new reservations (30.5283conservative combined). ExactIDs/provenance frozen in `audit/time_limit_recovery_proposal_v1.json`; readable proposal `outputs/stage14c_v_blindtest_validation/summaries/time_limit_recovery_amendment_proposed_v1.md`. Not authorized/launched.

### Next-Step Decision
STOP under plansection7 and request this concrete resource/call amendment. After approval, add/test deadline draining before any new GPUjob, version operational repair, preserve completed primary outputs, recover exact missingR, then originalR seal→C→closure. No cohort/prompt/recipe/metric changes and no follow-on.

## Recovery amendment approved — 2026-10-10T03:07:43.219763+00:00
User approved the concrete2,642call/32GPUh amendment. Next action: additive versioned deadline-safe worker and exact66-call R2recovery (8context replays kept separate); CPUtests and bounded four-call technical repair preflight before recovery. Preserve all original seals and scientific inputs; then completeR→C→closure.

## Repair preflight / recovery queued — 2026-10-10T03:25:28.954488+00:00

- Four-call preflight PASS on the frozen prefix criterion. Instruct repeats match fully; Thinking first128tokens match but full continuations differ (10,125/17,649tokens). Do not claim full-sequence bitwise replay. All original prompt IDs, sampling settings, seeds and visual-token counts match. Evidence: `audit/operational_repair_preflight_v1.json`.
- 140105/140107 completed; 140109 released R2 job140116 (3h), now pending Resources. CPU140117 caches terminal accounting. All are finite Slurm jobs; no follow-on coordinator.
- Additive operational source sealed;17 targeted CPUtests passed. Original G1 source/input seals preserved. Automatic guard admits new waves only with prospective time margin; active requests retain original token caps. Margin is throughput-based, not a mathematical bound on stochastic length.
- Existing1742 R outputs extracted,192 fixed/flagged response-only reviews recorded. Two truncated ambiguous outputs remain unscorable. No gold-based protocol choice or scientific aggregation.

### Next-Step Decision
Wait for140116, verify original8primary receipts remain untouched, then extract remaining58 and complete response review, fixedQC, and R primary seal. Only then launch800C calls and finish approved synthesis/closure. No new authorization is required within32GPUh/2642calls. A checkpoint or failure must be inspected before any duplicate submission.

## Recovery startup — 2026-10-10T03:28:49.409427+00:00

140116 RUNNING onnode06 from12:25:53KST,3hlimit to15:25:53KST. CPU140117 caches terminal accounting;140119 follows successful job exit to verify all1800primary responses, extract58new responses, seal raw receipts and prepare the remaining response-only review packet. If worker exits at an incomplete safe checkpoint,140119 writes HOLD instead; it never submitsC.

Scoring/QC/analysis adapters now hash-sealed before any aggregate correctness analysis;13 focused analysis/review/deadline tests passed. Two-passCsource review and fixed80+flaggedQC require explicit review decisions. Current conservative charge plus live reservation26.85194GPUh; adding the originally proposed4GPUhCenvelopes totals30.85194<32. Expected finalphysicalcalls2642 leaves no call headroom for further retries.

## Active generation verified — 2026-10-10T03:34:15.471008+00:00

Recovery140116 ready,18active requests with2,565–2,711generatedtokens each at03:33:33UTC; nofailure receipt. Canonical primary coverage remains1,742before the first recovery response finishes. Receipt: `audit/recovery_active_generation_snapshot_v1.json`. ProvisionalR2recoveryETA2–3hfrom12:25:53KSTstartup, not whole-stageETA. Worker stops at finite queue end or safe between-wave checkpoint; active calls retain their original caps. CPU140119 performs only completeness/hash checks, extraction and review-packet preparation. Remaining semantic review, R seal, C launch/reviews and closure are not yet completed or delegated to that CPU job.

## Next-Step Decision — parallel recovery — 2026-10-10T03:57:17.539415+00:00

User requests more GPUs. Current140116 has9/66recovery calls complete,18-memberwave13stillactive,48futurecalls untouched. One additionalA6000currentlyavailable onnode06. Select safe between-wave stop, then split frozenwaves14/15/16 across two disjoint workers (30/18calls). Retain original wave membership, task order within waves, unchanged sealedv2inference, all completed primary receipts and8context-only replay rule. Newcapremains2642calls/32GPUh. Replace pendingCPU140119 with a dependency on both newworkers. No model calls added and no scientific results inspected. Plan: `audit/parallel_recovery_amendment_v1.json`.

## Parallel handoff queued — 2026-10-10T04:00:40.718049+00:00

Dispatcher-only adapter sealed;20 CPUtests pass, original inference and analysis hashes unchanged. Globalbetween-wave drain signal applies to140116; no active call cancelled. PendingCPU140119cancelled because its old dependency would prepare an incomplete R panel. NewCPU140130 waits for140117 accounting after the oldjob ends; verifies fullwave13including8separatecontextreplays, ensures all48futurecalls untouched, archivesstopmarker, then submits two sealed-v2queues (waves14+16=30calls;wave15=18calls),1.5heach. Eachlaunch checks32GPUh and taskownership. New response-packet job will depend on bothGPUjobs. `audit/parallel_recovery_release_v1.json` or `parallel_recovery_hold_v1.json` records the outcome. Extra scientific/technical calls=0.

Latestheartbeat:15/66recovery calls complete,3active; currentwavecompletiontime uncertain. ExtraGPUcannot shorten those active single-GPUrequests. Parallelization reduces subsequent48-call wait while retainingbatchmembership. Review/analysis/C gates unchanged.

## Next-Step Decision — R review and analysis — 2026-10-10T06:24:02.252500+00:00

Verified all1800R receipt triples; finalparalleljobs140131/140133completed30/18calls with0technicalmissingness, allallocationsreleased. RawRseal and remaining6reviewpacket prepared14:04KST. Same-agentresponse-only review nowcomplete198fixed/flaggedtasks; all6remaining terminalanswers explicitlyadjudicated, includingescaped-braceboxed2. No score-dependent protocolchange. Next mechanicallyspecifiedaction: frozen answer scoring→fixedQC→paired R-P1/R-P2seal, then retain approval forCunder32GPUh. CPU140184prepares scoringQC; do not launchCbeforeRprimaryseal.

## R primary sealed / Next-Step Decision — 2026-10-10T06:27:33.380149+00:00

R1,800complete,198response-only andfixed/flaggedscoreQCrecords;2I_R2capsunscorable,0technicalmissingness. Rprimaryseal `audit/R_primary_seal_v1.json` verified. Instruct R0=190/300(63.33%),R1=123/300(41.00%): primary−22.33pp[−30.33,−14.33], oppositepredictedbenefit. SecondaryR2=245/298(82.21%),paired+18.46pp[13.76,23.49],300-familybounds[18.33,19.00]. ThinkingR0=191/300,R1=177/300,R2=277/300;R2−R0+28.67pp[23.00,34.33]. R1thereforedoesnotrepairregression;prespecifiedR2helps,bothmustbereported.

Native-reference Instruct rescues/regressions: R0=39/103,R1=16/147,R2=39/46with2unresolvednativecorrectcases. Thinking49/68,47/80,82/15. R0historicaloutcomedrift I1changedfamily(+1correct),T62changedfamilies(net−2correct). Do notclaimrepairingexacthistorical104errors orisolatewhichformatcomponentcausesimprovement.

Selectednextaction: exactlythe800frozenCcalls, fourdisjointmodel/conditionqueues (I.5heach;T1.5heach), sameimages/prompts/seeds/recipes/scoringandold/new100strata. C isseparatelyauthorizedandnowunblockedbyRseal. No scientifictuningbasedonR. Currentconservativecharge25.7553GPUh;4Creservationhoursyield29.7553<32. Calls1842+800=2642ceiling;noneadded. NoavailableA6000now, submittoSlurmpendingwithinexistingauthorization.

## C released — 2026-10-10T06:29:21.119517+00:00

R primary andcompanions sealed before C submission. Four200-call queues:140186I_C0(.5h),140188I_C1(.5h),140190T_C0(1.5h),140192T_C1(1.5h). Each has dependent terminal-accounting CPUjob.140186runningnode07at15:28KST, otherspendingPriority; no startETA. CPU140195depends on allfour and prepares rawseal/response-modepacket only; explicitmode review then two-passsourcefidelity andfixedQC remain. Noautomaticsemanticlabels orfollow-on. Totalconservativechargeplusfourreservations29.7553/32GPUh. Allscientific inputsunchanged byRresults. [R report](../../outputs/stage14c_v_blindtest_validation/summaries/stage14c_v_R_primary_summary.md).
