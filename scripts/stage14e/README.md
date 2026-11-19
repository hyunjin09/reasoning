# Stage14E — COMPLETE / STOP (2026-10-23T01:05:50.094588+00:00)

Completed the authorized bounded research cycle: all72 SAVA postmortem,24-family diagnostic, one24-family revision and one32-family evaluation;96logical/77physical solvers,19native aliases. Acquisition M0/32 versus S1/32; M−S−3.125pp,95%CI[−9.375,0]. Final answers: N 19/32, S 20/32, M 20/32; unscorable N=0, S=0, M=0. All allocations released; new7.148889/24GPUh, historical21.365278GPUh separate. No demonstrated acquisition improvement. No further tuning or follow-on launch. OldStage14D375GPUh remains HOLD; Stage14C-V remains unfinished.

This is the terminal state; execution notes below document the earlier recovery and reproduction steps. Saved artifacts are write-once. Do not rerun generators into existing roots.

# Stage14E bounded acquisition development

Output root: `outputs/stage14e_acquisition_development/v1` (P below). New GPU budget24hours including startup/failures/idle; historical SAVA21.365278hours is separate. All GPU work uses project scheduler+Slurm,48hour requested limits, finite queues. Use `.venv/official_eval/bin/python` on allocated GPUs via `run.sh`; CPU analysis uses `.venv/bin/python` and `PYTHONPATH=code:.` where inherited scoring is imported.

## Current immutable method

`ledger_v2.py`: obligation-first ledger, coverage last, host firstUNKNOWN/TENTATIVE, legitimateNONE permitted. `contracts_v2.py`: source-reference/numeric transport and compact reader. These validators do not certify semantic relevance or source truth. The full original image and unverified prefix reach the selected reader. No offline E* or gold enters any runtime payload. `evaluation_contracts.py` records aliases and unverified solver suffixes. `engine_runtime.py` preserves exact image/prompt reconstruction, family seed, BF16 and model-specific sampling; MP0/cacheoff. Helpercap2048; solvercap81920.

Model/processor/environment hashes and recipe: P/protocol/runtime_v1.json. Frozen family input: P/inference/evaluation_families.jsonl. Offline references are under P/offline and never imported by a GPU worker. Exact source spans and raw token/request/output hashes are stored for every physical call.

## Execution status and recovery

Final acquisition150382 completed32families/130physical calls. CPU dispatcher150404 failed after submitting rank0 because Slurm accounting was temporarily absent. Its log is preserved. A bounded accounting retry in accounting_retry.py and launch_flexible_v2.py repaired only submission;6CPUregressions pass. Frozen worker code and scientific manifests were unchanged.

Rank0job150713 completed19physical/24logical continuations. Jobs150791/150792/150793 execute the other three fixed shards, with2/2native repeat gates each. Registry: P/manifests/final_execution_registry_v1.json;77physical/96logicalsolvers including19nativealiases. Never duplicate a completed receipt. Check live Slurm and result.json rather than inferring completion from this operational note.

The32source review and96logicalacquisition judgments are sealed. M0/32useful acquisitions versusS1/32; final accuracy is not yet computed. Response-only review proceeds on immutable completed receipts while queues run, via response_packets_ready.py; full scoring remains gated on complete reviewed coverage. No gold or final correctness is used for extraction QA. No further method revision or family selection.

All final arms use matched A6000hardware; the earlier prospective hardware addendum and cancelledA4000pending job are preserved. DevelopmentA4000results are not pooled with finalA6000comparisons.

## Review and analysis order after acquisition

1. Verify P/audit/evaluation_acquisition_freeze_v1.json and source-only packets `analysis/evaluation_acquisition_packet_0..3.txt`. Inspect original source images and frozen prefixes/offline source atoms. **Do not open new longsolverfinals yet.**
2. Create exactly32rows in `annotations/evaluation_labels_v1.tsv`: item_id,S,M,M_noimage,target_S,target_M,notes. LabelsU=new useful sourcefact;R=valid useful reinspection;K=already correctly known;W=explicit wrong taskcritical claim;?=unknown/ambiguous;I=irrelevant/derivednotvisual;A=noattempt;X=invalidreadout. PrimaryU/Rrequires noexplicitlywrongtaskcriticalclaim inrecord. Keep partial/complete binding, queryrelevance, sourceuncertainty and noimage distinction innotes/additionalannotation. Noautofillfromfinalcorrectness.
3. Run `.venv/bin/python -m scripts.stage14e.score_acquisition evaluation_acquisition_a6000_v2`. This seals96logical source reviews and computes primary M−S acquisition yield. M_noimage is not genuine visualacquisition. No annotations are supplied to solvers.
4. Check allfour solver roots listed in final_execution_registry, all96logical rows, physical receipt hashes, aliases, runtime matches and budget. If infrastructureinterrupts, preservecompletions and version a repair/resume; never erase failures or shorten scientificcaps.
5. After sourceannotationsealed and generatorscompleted: `PYTHONPATH=code:. .venv/bin/python -m scripts.stage14e.final_extract`. Review exact finalbodies/options/parser outputs withoutgold; do notinferfinalsfromunclosedthink.
6. Seal `annotations/response_review_v1.json`: gold_hidden:true, aggregate_correctness_not_opened:true, one record per physical path withgeneration_path,generation_sha256,reviewed_answer,note. No finalbody→reviewed_answer:null.
7. Run `PYTHONPATH=code:. .venv/bin/python -m scripts.stage14e.final_score`. Uses inheritedMathVisionequivalence and frozen4000family/source-stratifiedbootstrapseed20261022. Report missing/unscorable separately, correct/assigned andcorrect/scorable, pairedchanges/rescue/regression, uncertainty andmissingnessbounds.
8. Finish exact-provenance32casebook, source-evidence/downstreamcross-tabs, perconditiontokens/latency/imagecost, actualallocationaccounting, historical5357filesealverification and finalreport. Answer sixresearchquestions withnegative/inconclusiveevidencevisible. No furtheroptimization on32ornewstage.

## Completed analysis and validation

All72historicalpostmortem: postmortem.py, summarize_postmortem.py, postmortem_casebook.py; outputreports/sava_all72_casebook_v1.md andstage_matrix_v2.csv. Old52source labels/new20supplement remain distinct, not silently pooled.

Initial24diagnostic and sole24ledgerrevision are complete and source-reviewed. Selectionfile P/protocol/final_method_selection_v1.json is frozen. Development3partialreinspections versus0matchedcandidateA is not established efficacy;0complete newstructures.

51CPUprelaunchtests passed; supplementary18tests include6independent checks on exactfinalledger and3automaticdispatcher checks (some existing tests repeated). LogsunderP/audit. Numeric repair compiles48saveddevelopmenttargets to identicaltransports. Actual native64tokenrepeat gates precedeeachworker'sscience. Runtime/code manifests freezehashes; do noteditsealedruntimefiles whilejobsarequeued/running.

## Resource tracking

`.venv/bin/python -m scripts.stage14e.accounting` updates mutable resourceledger with prior snapshots. Admissionrequires actualcharges+exclusiveoutstandingreservations≤86400GPU-sec. CPUdispatcher uses0GPUs. Finalsolver reservations4hours each can be transferred fromfinishedjobs through versionedbudgetgrants if needed; updateledger and grant consistently beforeenlargement, never exceed24actualGPU-hours. RequestedSlurmlimit48hours is distinctfromexplicitresearchbudget.

No arbitrary shortrolloutdeadline or helper-sizedcontext is used for longsolvers. Keep full81920cap andvalidated128000context. Pendingqueue delay is not chargedGPUtime and is not an experimental result.
