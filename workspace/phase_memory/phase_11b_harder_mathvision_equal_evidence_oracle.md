# Phase11B: Harder MathVision equal-evidence oracle

## Current Objective
Completed the approved Stage11B action at the discovery NO_GO gate. No held-out oracle or follow-on is authorized by this completion.

## Active Constraints
- Approved stage11b plan and frozen execution spec; preserve all historical stages.
- Fresh conservative families; blinded E* and independent semantic reviews before outcomes.
- No held-out outcome selection, cap adjustment, new benchmark or post-failure pivot.
- Scheduler/Slurm only; up to8 authorized GPUs on nodes02/03/06/07; target<6/hard8 allocated GPUh.

## Current State
- Done: fresh source128, dual sufficiency review and49 eligible; all six frozen strata rejected by source eligibility or logical native-gate impossibility. Required artifacts, conditional NOT_RUN records and five figure pairs complete.
- In progress: none.
- Blocked: none; prescribed stopping branch completed.
- Most recent observation:68 complete outputs reviewed,61 capped/no-final; sole source-feasible stratum27 Thinking and31 CoT reviewed,0 correct each. Maximum possible forward9 (10 allowing flagged extraction ambiguity), below12.
- Resources: 5.499444 allocated GPU-hours; all10 Slurm jobs terminal, no active GPU or coordinator.

## Evidence That Matters
| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Stage11A61 eligible,12 forward discordant,4 uniquely localized; NO_GO | outputs/stage11a/v1/stage11a_summary.md | Need discovery yield gate, not automatic large oracle | confirmed |
|512-token probe cap Thinking57/61 vsCoT24/61 | outputs/stage11a/v1/stage11a_resource_accounting.json | Freeze adequate common cap and completion checks | confirmed |
| Local images/checkpoints available | workspace/dataset_inventory.md | No download required | confirmed |

## Failed Attempts and Lessons
| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Stage11A initial worker | statistics.py shadowed standard library | supported by preserved import failures | Stage-local module names must not shadow stdlib | no generic statistics.py |

## Open Candidates
| Candidate | Result | Status |
|---|---|---|
| Six frozen harder strata | Five fail source eligibility; levels3–4 cannot reach12 forward discordances | closed / NO_GO |
| Held-out equal-evidence oracle | Discovery prerequisite failed | NOT_RUN |

## Next-Step Decision
- Current bottleneck: no remaining authorized research work; causal explanation of Thinking–CoT remains unresolved.
- Relevant evidence:49/128 E*-eligible; logical_stop_decision.json proves forward bound9<12, conservative extraction bound10<12; repeated greedy noncompletion dominates observed runs.
- Chosen action: STOP after completed closeout. Do not launch held-out, oracle, another benchmark, repair experiment or paper edits automatically.
- Exactly one recommendation: Keep Thinking-vs-CoT as a discussion-level open question and finalize the paper around the established causal retrieval and visual-to-text lifecycle claims. Recommendation not executed.
- Validation: final_closure_audit.json verifies frozen hashes, chronology, every valid output review, missingness, gate bounds, conditional artifacts and released GPUs. The initial CPU audit used the wrong hash target; corrected with original preserved. Figure2 presentation was repaired without changing data.

### Step Result
- Source:128 constructions,256 independent initial sufficiency reviews,16 bounded repair reviews;49 eligible,41 unchanged+8 repaired;5 unresolved nonempty proposals excluded.
- Native:68 valid complete output records,58 required comparisons;61 capped/no-final. Missing outcomes remain unknown; no full-stratum accuracy or gap estimated. No held-out or oracle inference and no Claim3 promotion.
- Batch sensitivity:8/8 original batch prefixes reproduced,0/8 single-item prefixes identical. Cause of long noncompletion remains unknown; results apply to frozen batch4/BF16/greedy/16384cap.
- All evidence and partial attempts preserved; actual5.499444GPUh includes failures and cancelled work. All allocations released and finite coordinator stopped.
- Report: outputs/stage11b/v1/stage11b_summary.md.

## Execution History
The dated entries below describe earlier states; the completed state above is authoritative.

### Source-only freshness repair before inference
Reviewer recognized1699/1237 as the same redrawn problem; main image inspection confirmed. Source-only conservative Jaccard family union (>=.45 and>=20 tokens each) identified prior-linked and within-pool possible aliases. Versioned repair replaces12 discovery entries with next identical sampling-stratum hash candidates;128 still frozen,689 untouched conservative reserve families. No outcomes existed. Initial manifests/drafts preserved; active discovery manifest_v2 and packet_v2. Broad source similarity may overmerge and is disclosed.

### First technical preflight
Slurm125676/node07 failed after148s at the strict text-input-key allowlist. All four native batch inputs matched original single-item token/pixel/grid preprocessing before failure. No discovery outputs. A single CPU processor-metadata diagnostic is running; root cause remains unknown until its receipt. Failed allocation0.041111GPUh preserved; GPU released.

Preflight diagnosis SUPPORTED by audit/preflight_text_metadata_diagnostic.json: processor adds all-zero mm_token_type_ids to text-only inputs. No pixels, image tokens or cache. Fixed only technical validator to accept zero text tags and reject nonzero tags/pixels/cache;5focused tests pass. Original preflight source retained; generation/config unchanged. One bounded repaired preflight authorized by unchanged stage.

### Technical gate passed / discovery execution
Slurm125689 completed with ExitCode0; native four-item batches exactly match single-item token/pixel/grid preprocessing for both models. Text-only inputs have0 image tokens, no pixels/grid/cache, all-zero auxiliary modality tags. Both32-token generation checks pass. Proceed unchanged frozen native256 discovery while E* reviews remain blind; no correctness/outputs opened. Both finite worker envelopes90minutes, total reserved+failed/preflight remains below8GPUh.

### Bounded decoding validity/performance check
Confirmed observation: first two4-item batches remain active>15minutes, GPU97–99%, with no completed receipt yet. Cause unknown; no correctness/text inspected. Resolved GenerationConfig audit confirms greedy16384/use_cache/beam1, no score or hidden-state collection. One5minute Slurm old-family diagnostic will inspect forward input lengths/cache growth and256-token throughput; scientific workers unchanged and all8h budget envelopes preserved.

Cache diagnostic completed: incremental cache works (only one input token after prefill; cache grows; image processing only once).256-token old-item batch4 takes4.56s. First discovery batches now complete:8runs,7 length-capped; approximately16–17.5minutes per batch. No correctness/text opened. Slow long greedy trajectories are observed, underlying model noncompletion cause remains unknown. Initial extrapolation exceeds8GPUh; retain finite90minute worker envelopes while semantic eligibility gate is completed, and reassess remaining compute before any further submission. No cap/model/scientific gate changes.

### Source-only semantic review boundary — 2026-09-28T07:07:32.447510+00:00
Both128-row independent sufficiency passes sealed. Raw sufficiency agreement124/128, kappa0.906 overall; among54 proposed nonempty sets,50/54 agreement but kappa-0.029 (prevalence sensitive), quality conjunction kappa0.375.41 nonempty sets pass both quality reviews. One bounded8-item simplification/wording pass is independently re-reviewed;5 unresolved source/linguistic cases remain excluded. No generated text/correctness opened. Next selected action: seal semantic eligibility, then evaluate source-only necessary discovery constraints. Twelve forward discordances plus Thinking accuracy<=75% mathematically require>=16 eligible; this does not add or lower any gate. No new GPU submission until this check.

### Next-Step Decision — source-only pruning
Final49/128 E*-eligible after one8-item independently accepted repair; original raw judgments preserved. Five frozen candidate strata fail40% eligibility; only middle_all survives with36/88. No native answers/correctness opened. Alternative broad256 execution projects~18GPUh and cannot change five failed gates. Chosen smallest action: cancel broad workers, preserve16 completed and any8 in-flight input records, and resume66 unfinished original native tasks needed for sole possible stratum (6 exact results reusable). No cohort/gate/model/cap change, no selected stratum until full native GO. At most remaining8GPUh total; partial resource stop remains explicit if necessary.

### Source pruning executed / native text opened after seal
At2026-09-28T07:19:41.213992+00:00 broad jobs125690/125691 were already cancelled with preserved terminal receipts (2425/2424s).16 complete outputs and8 interrupted input-only attempts preserved.6 completed rows match the remaining72 required comparisons. Versioned source_feasible_tasks.json selects66 required unfinished original tasks plus6 original fillers to preservebatch4; original scientific generation sources/config unchanged. Four90minute envelopes plusused1.4075GPUh bound total7.4075GPUh. One worker125733/node06 active; finite coordinator PID4023379 launches only these four job IDs on allowed available A6000 nodes, never retries/new stages.
Final evidence seal predates partial_answer_review_v1;16 literal answers reviewed before correctness join.14 capped/no-final,2 committed answers; among3 currently reviewed eligible pairs, both modes0correct. This is incomplete—not a scientific NO_GO. Logical forward-discordance upper bound33 still permits12. No full-cohort accuracy or mechanism claim. Next action remains finish needed native gate within resource budget, or stop only on demonstrated impossibility/resource limit.

### Focused technical check after accumulating native completion failures
32 complete outputs reviewed; sole stratum22 required outputs(Thinking7/CoT15),0correct, maximumpossibleforward29. Completion/floor behavior remains unexplained. Input/preprocessing and cache/greedy checks passed. One bounded512-token batch-versus-single check on the entire first frozen resumed batch perarm will test whether batching changes short continuations/prefill distributions. No output substitution or scientific settings change.10minute envelope raises absolute worst-case stage reservation to7.574167GPUh, below8. This is a technical validity check, not a new benchmark/method or another broad performance search.

### Technical batch check result
Slurm125801/node02 COMPLETED0:0 in263s, GPU released. All8 same-batch512-token prefixes reproduce original native prefixes exactly; source IDs/grid match single inputs. Prefillargmax8/8matches, maxKL0.003070. Single-item greedy prefixes differ after16–477tokens inall8, so batch equivalence is NOT established. Record numerical/batch-size sensitivity; complete-trajectory effects and noncompletion cause remain unknown. Continue the prospective batch4 protocol unchanged; do not replace native evidence with diagnostic outputs or run more diagnostics. Final inference must be scoped to this frozen execution regime.

### Logical stopping boundary — 2026-09-28T08:31:47.942587+00:00
Thinking27/36 and CoT31/36 reviewed,0 correct in each; maximum possible forward9<12. Granting flagged extraction ambiguity raises upper bound to10<12, so it cannot change the stop. Other five strata already fail the source gate. Selected action is immediate GPU release and NO_GO closeout, keeping unobserved outcomes unknown. Proof: audit/logical_stop_decision.json.

