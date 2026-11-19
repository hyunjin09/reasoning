# Phase14C: Cross-task evidence-supply bottlenecks

## Current Objective
Execute Stage14C through its explicit gates; current action is the approved bounded D1 evidence-recovery probe and prespecified source sensitivities after primary sealing. Explicit user “proceed” authorized this gated continuation.

## Active Constraints
- Original plan and sealed Stage14A/14B sources/outcomes remain unchanged.
- Gate G0 approval received as user “proceed”; approval receipt is preserved. G1 source work is authorized; no model generation before G1 and G2 pass.
- New source selection/QC cannot use model outcomes or weaken E* answer safety. Same-agent review is not independent reliability evidence.
- Proposed release: at most8 authorized A6000 GPUs via Slurm/project scheduler;120GPUh hard total, D1<=12GPUh within it. No D2/D3 or follow-on.

## Current State
- Done: primary sources/revisions, localMMStar payload hash, inherited model identity, concrete source/scoring/statistics/gates/budget and13CPUtests.
- Done: G0 package sealed at2026-10-08T15:10:53.901939+00:00; parent hashes and original plan verified unchanged.
- Done: G1 acquisition, identity, source-only E* and final QC seal. Complete: main generation4,588unique calls,42reused from G2; primary sealed, D1running.
- Runtime state: all main workers released. D1 workers139391–139394 active, one bounded4GPU wave; terminal records retained. Pending original139245 was cancelled before allocation and exact shard moved to139246, preserved history.
- G2 repair rerun139215/139216 completed; fixed42sciencecalls reused in main. Original4synthetic replay calls plus2fixed-context replay calls preserved. Main released under version2 PASS. Two earlier CPU source audits completed.
- Native cohorts sealed: MMStar 1,000 families and BlindTest 714 families; MMStar reserve 250 remains unused. Source alias and math-anchor overlap audits are preserved.
- G1 PASS: all1,714 reviewed;580 final-QC E* (MMStar280, BlindTest300), second review complete, fixed172 reread complete. Original reviews remain immutable. All300 line geometry/golds agree. All native gold schemas valid; semantic gold validity not universally certified. BlindTest E* consists only of line intersections.

## Evidence That Matters
| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Three large-scale math phenomena and seed robustness | outputs/stage14b/summaries/stage14b_final_summary.md | Preserved anchor; no new primary math runs | confirmed |
| MMStar local payload matches officialLFS digest | outputs/stage14c/source/dataset_inventory.json | Reuse pinned1500rowval; no replacement download | confirmed |
| BlindTest8016renderedrows, repeated scene/style variants | outputs/stage14c/audit/official_sources/ | Rows are not independent families; consolidate before selection | confirmed |
| Frozen core with13synthetic tests | scripts/stage14c/design_core.py | Pairing, weighting, missingness and tiny-denominator checks | confirmed |
| License/source coverage limits | outputs/stage14c/spec/source_only_protocol.md | Local evaluation only; E*coverage MM280/1000 and Blind300/714, all line intersections | confirmed G1 |

## Failed Attempts and Lessons
G2 startup139200/139201 failed before any model request: GPUenv lackedpyarrow. Engine failure logs support this diagnosis. Installed onlypyarrow24.0.0 (same as sourceCPUenv) viauv in project-localGPUenv;3sourceadaptercontracttests pass in that exact environment. No prompts/seeds/models/recipes/cohorts changed. Repeat unchanged preflight once after this concrete repair; preserve failedjob logs and allocation cost.
A broad metadata-directory walk was interrupted and replaced with bounded conventional-root lookup; do not claim exhaustive dataset absence. PDF readers fitz/pdftotext were unavailable; existing pypdfium2 successfully extracted both papers, with no installation. Expected TDD failures preceded implementation;13finaltests pass. No scientific failure or outcome exists.

## Open Candidates
Selected for G0 approval: MMStar + authorBlindTest release. MMBench and the named correspondence alternative are deferred, not queued. No new benchmark after a G1failure without a source-only amendment.

## Next-Step Decision
- G2 PASS after bounded implementation repairs: pyarrow installed locally; matched-context T replay128/128 identical in fresh engines, preserving original changing-batch divergence. Same model/recipe/prompts/seed unchanged.
- All42sciencepreflight calls have committed finals,0cap hits,0strict repetition pathologies; raw results reusable.4original synthetic+2fixed-context synthetic calls preserved. No correctness gate.
- Exact bit replay is conditional on matching execution context; across-changing-batch token identity is not guaranteed. Cause of original numerical divergence remains not uniquely isolated.
- Next authorized action: finish the existing finite main native/equal-evidence queues,4,588unique calls total (4,546 launched after42preflight reuses), up to8GPUs, within120GPUh total and12D1reserve. Then raw seal, arm-separated scoring/review, primary analysis before approvedD1.
- Active scoring entrypoint is scoring_v5 (v4 conservative parser; completed-arm review guard), review_packets_v4, cpu_steps_v3. Originals preserved. I seal complete; T review still gated on global raw seal. D1 uses d1_review_v2 and source-frozen common unit maps. No automatic semantic adjudication.

## Execution checkpoint — 2026-10-09T04:45UTC
3,567/4,588main calls complete (I2,054/T1,513); no main technical failures/OOMs. Remaining generation estimate roughly1–2h, sensitive to long tails. No correctness opened. Active main scorer:scoring_v3; D1 reviewer:d1_review_v2 with the common source-only300-family unit map. Primary reporter, D1 macro/micro/crosstab analysis and resource accounting prepared; no D1 launch before primary summary/seal.

CPU continuation:139301requests0GPUs and is verified PENDING Dependency on the seven remaining main jobs. It will seal raw outputs and extract I finals only. InitialCPU139299 lacked the requested environment-specified dependency and was cancelled; raw_freeze rejected unfinished tasks, no seal/extraction was written. Direct explicit --dependency resubmission is verified. Raw GPU science unaffected.

## Prospective extraction implementation repair — 2026-10-09T05:07UTC
Synthetic malformed numeric strings (5*,{5*},boxed2 followed by*,unbalanced$2) exposed destructive delimiter stripping. Scorer v4 adds a conservative review guard;13synthetic tests pass. On the existing42G2responses, automatic extraction39(previous40), manual review3(previous2); the previously reviewed committed finals remain unchanged. No main extraction/grade existed. Active entrypoints:scoring_v4 andreview_packets_v3. CPU139301was cancelled whilepending and replaced by139308(0GPUs), explicitly verified dependency on all7remaining mainGPUjobs; command cpu_steps_v2 raw_I. GPU generation unchanged. Evidence: audit/terminal_normalization_repair_v4.json.

## Next-Step Decision — completed-arm review overlap
All2294I calls are complete and I GPUjobs have exited. Seal/verify that complete arm, then review I while fixed T queues continue; no T input/queue can change based on grades. This satisfies raw freeze before scoring and I-before-T review. Global raw seal + I scoring seal still gate T; both scoring seals gate primary. Execution-only implementation: scoring_v5 (same v4 parser), review_packets_v4, cpu_steps_v3. Guard test passes; audit/completed_arm_review_overlap_v1.json.

## Next-Step Decision — Instruct extraction complete
All2294I raw receipts sealed. Response-only review resolved437flagged outputs in12immutable batches; no gold or T outcomes used during extraction. Gold-aware first scores now materialized. Continue the frozen10%+allambiguity/cap/sourceflag scoring QC, then seal I; only afterward open T extraction. At2026-10-09T05:25UTC:2172/2294Tcalls complete; no main technical failures observed. Entry points remain scoring_v5/review_packets_v4/cpu_steps_v3. D1 remains gated on primary seal.

## Scoring checkpoint — 2026-10-09T05:30:53.097490+00:00
I scoring sealed:2294scores,437explicit extraction reviews,673QCcases,10immutable QC batches. Three first-score REVIEW cases resolved explicitly (native row/column pair2, invalid completed option1); original receipts preserved. CPU139325verified0GPUs/PENDING afterok:139312 for T extraction only. All171G0/G1/G2/D1-source/code/parent hash entries match; evidence audit/preserved_identity_check_before_primary_v1.json. No paired correctness or D1 outputs opened.

## Main generation complete — 2026-10-09T05:52:33.244530+00:00
All4588unique main calls have valid completion receipts (2294per model),0technical missingness observed. CPU139312 global raw validation/seal then139325 T extraction are queued automatically. I scoring remains sealed; T response-only review, scoringQC and primary analysis next. Final-validator scope/resource synthetic checks2PASS; code audit records v1/v2 preserved.

## Thinking extraction complete — 2026-10-09T05:58:04.182074+00:00
All2294T generations extracted;669response-only flags resolved in9immutable batches, before gold grading. Preserve one repeated/retracted cap final asUNSCORABLE and explicit out-of-option answers for separate grading review. Continue the frozen10%+allambiguity/cap/sourceflag QC, then sealT and runprimary. AllmainGPUsreleased. No paired analysis opened.

## Next-Step Decision — primary sealed, bounded secondary release
2026-10-09T06:03:28.088942+00:00
Main4588 complete and raw/arm-scoring/primary-analysis/primary-summary sealed;0technical missing. T669response-only reviews and866QCcases complete. Confirmed post-E* T-I:math14.69pp,MMStar1.81pp,BlindTest1.33pp. Negative companion: BlindTest eligible line E* causes104I regressions vs39rescues (net-21.67pp); retain it, do not interpret conditional84.78%rescue as overall benefit. G1 independently computed source geometry already agrees with300native golds; no source/prompt/outcome revision. Cause of regression remains unknown; no unapproved diagnosis or rerun.
Proceed with exactly frozenD1:100families eachmath/MMStar/BlindTest,bothmodels600calls,onewave1I+3TsingleGPUworkers×3h<=12GPUh; existing recipes/caps/seeds/targets unchanged. Then two-pass semantic review, sensitivities, final figures/accounting/one recommendation/STOP. D1 elicitation cannot establish what original native solver internally knew. Current stage cost13.272observed/proxyGPUh; no active allocation.
Technical check: math native8.50pp here is frozenfamily-equal estimand;item-weighted7.195pp exactly matchesStage14B7.20headline, andStage14Bfamily-equal sensitivity also8.501046568984615. No new math outcome/regrade.

## Reporting checkpoint — 2026-10-09T06:12:35.102572+00:00
All89prespecified source strata complete. MMStar nonmath164eligible:postgap+1.86pp[-3.11,6.83]. Final figure display selection:fig1original,fig2v2,fig3–5v3; inspection passes and hashes sealed. D1 source-only300-image sheets generated viaCPU139404; pending139402cancelled before allocation because node02CPU/hostmemoryfull. CPU139408 waits explicitly afterok on allfourD1workers, then strict raw seal and technical summary. No scientific queue change.

## Next-Step Decision — bounded D1 review overlap — 2026-10-09T06:19:37.398341+00:00
All600D1 inputs alreadyfrozen/launched; I294/300 andT231/300complete, with longtails. Enable completed-arm raw sealing/review forI whileTcontinues; no cohort/condition/recipe/score change and no D1outcome read beforethisimplementation. Active d1_review_v3 preservesoriginal v1/v2;4gate/schema testsPASS afterexpectedred. Global600rawseal andall1200reviews remain requiredbeforepairedD1analysis. Revieweachsource/responseexplicitly; noautomaticsemanticgrading.

## D1generation complete; semanticreview checkpoint — 2026-10-09T06:42:31.942333+00:00
All600D1calls completed: I220209tokens,T1151442tokens. AllGPUandCPUjobsreleased; finalcontrollerrecords retained. Stagecost14.69363441779195GPUh observed/proxy; no unknowndurations. GlobalD1rawseal, Iarmrawseal andtechnicalsummarycomplete. Active D1reviewentrypointv3; Ipass1indices0–47complete(8six-rowbatches000–007); Ipass2andallTreviewsremain. Source-onlyoriginalimages available in source/D1_source_sheets,6persheet. Exact source-unit match requiresvalue/binding; correctpartial assertions stayaccurate-unmatched with subtype, documentednotesv2. NoD1aggregatecomparisonsopened. Continue review, thenD1analysis/finalsummary/one recommendation/finalvalidation/STOP.

## D1 semantic review checkpoint — 2026-10-09T07:13:35.470510+00:00
All600D1calls complete, all compute released, stage14.693634GPUh. I first+secondpass300/300 each complete. Tfirstpass12/300 complete, secondpass0. Continue frozen semantic reviews, then D1seal/analysis/finalclosure. Late sourceQC conflict MMStar997 confirmed on second original-image reread: plant-to-horse arrow was frozen backwards. Preserve E* and primary; mark both D1counterparts unresolved and disclose limitation. Evidence audit/D1_source_conflict_MMStar997_v1.json and second_reread_v1. No diagnostic rerun or new GPU work.

## Next-Step Decision — D1 review complete — 2026-10-09T07:38:53.628806+00:00
All600D1calls now have two explicit source/response reviews (1200records). Frozen unit maps and raw outputs remain unchanged; MMStar997 remains unresolved in both D1arms because of confirmed frozen-source arrow error. CPU139573 will seal reviews and compute descriptive D1tables; no newGPUwork. Complete finalreport, disclose sourceQC and elicitation/granularity limitations, include one explicitly posthoc single-family exclusion robustness check for MMStar997 without replacing primary, then finalhash/resourcevalidation and exactlyone recommendation/STOP. This bounded check addresses whether the discovered source error changes the reported MMStar point estimates; no outcome-based selection or protocol tuning.
