# Phase14D1: Subgoal-addressed visual acquisition

## Current Objective
Implement and test a bounded no-oracle method: derive the next visual evidence demand from the current reasoning prefix, address its source in the correct global context, read it, and resume the same solver.

## Active Constraints
Original artifacts immutable. No E* value, sampled audit target, answer outcome, retrospective difficulty label or human ROI enters runtime. Pinned 4B Thinking; R72 exploratory; one checkpoint/query per family; no Stage14E, held-out run or old 1,674-continuation grid. Latest user authorizes prospective plan amendments and no further permission requests. Former16GPUh ceiling superseded by2026-10-22user instruction to finish remainder with24–48h joblimits; scope remains fixed72×6, actualcharges tracked; initial smoke history<=2GPUh; live GPUs only, project scheduler/Slurm; no training. Stage14C-V remains unfinished and is not falsely marked closed.

## Current State
COMPLETE: 72 families, 432 logical arm assignments, 345 primary physical continuations. Jobs 149690/149691 completed; no active GPU jobs. Both v8 technical gates and 32 cross-node comparisons pass. Final integrity checks verify 4,129 preserved files and 72 original images.

All 72 query/address reviews and 46 source-readout reviews preceded final-answer inspection; six additional regression/rescue reviews followed it. Final scores: N 39/72, G 41/72, Q 39/72, QI 36/72, QIA 37/71 scorable (one cap/unscorable), QGL 36/72. Primary QI−N: −4.17 pp, 95% CI [−12.50, +4.17], three rescues/six regressions. The three QI rescues lack clearly new task-critical facts in their helper readouts. Actual charge: 21.365278 GPU-hours. Report: `outputs/stage14d1_sava_pilot/v1/reports/feasibility_main_v8.md`.

## Evidence That Matters
D0 source context associates with explicit errors but does not establish crop causality. No stable depth/operation ranking or tiny-text result. One AI reviewer with prior exposure. The original plan confounds offline target selection with runtime query evaluation unless those are separated.

## Failed Attempts and Lessons
v1 query helpers4/4 capped before finalJSON. v2 compact query branch has an established field-order mismatch;8NONE not valid evidence of absent visual demand. v2 replay5/8 exact, identical inputs/seeds; cache sensitivity suspected. See preserved technical gates and CPU grammar witness. No answer-accuracy-based tuning.

## Open Candidates
QI: source-addressed query plus original image. QGL: same query/address with global context and valid local detail. Added localization-matched full-image control distinguishes presentation from localization computation. No oracle correction of bad queries.

## Next-Step Decision
STOP: the authorized pilot and analysis are complete. One recommendation, not executed: before online Stage14E or scale-up, validate an interface that distinguishes unresolved, source-resolvable visual premises from given facts or mathematical unknowns and permits abstention. Preserve the negative estimate and uncertain mechanism; do not automatically start another stage. GPU policy now defaults to 48-hour limits with release after finite work.

### Execution update — 2026-10-19

P0 complete:72distinct source-selected families /432arm slots; all72have valid pre-answer prefixes. Twelve CPU contract/source/ROI tests and three scorer tests pass. Original pending146487/146488 cancelled before allocation; repaired resource-only requests146489/146490 use1CPU each. Slurm whole-core accounting assigns2CPUs, so only146489 initially runs and146490 waits. No scientific input/protocol changes. Related-work check confirms targeted guidance and global/local views are existing ideas; feasibility does not establish novelty. Source-judgment contract freezes distinction between actual dynamic target and offline opportunity.

### Technical failure and one bounded repair

All first4queryhelpers hit4096without closing think;6/8formatgate became impossible, so pending146490cancelled before allocation.146489completed21technicalcalls in548allocatedseconds. Diagnostic trace excerpts show prolonged original-problem reasoning rather than query commitment. V1data/code preserved. One prospective compact-controller repair explicitly closes helper thought and enforcesJSON; nativeThinking solver unchanged. Same8families, sameprefixes/seeds/gates. Job146494,node03,1GPU,<=1h; xgrammarCPUchecks pass. No finalansweraccuracy used. If this contract repair fails, stop boundedattempt rather than promptsearch.

### v3 correction — 2026-10-19

CPU installed-xgrammar witness rejects prompt-order QUERY but accepts schema-order QUERY and NONE. v3 reorders only QUERY properties to match the prompt; four new grammar regression tests pass. v2 repeats5/8exact despite identical token inputs/seed; disable prefix caching prospectively for everyv3request and retest. Job146499 oneGPU node03 <=1h; v1+v2 actual548+580s=0.313333GPUh. Earlier caps and all eight IDs fixed. All eight originalimages inspected for forthcoming source QA, without v3readouts/finals.

### Closure — 2026-10-19

v3 exactpairs6/8; mismatches107at45and33at30(zero-basedtokens). Cache alone not supported as fullcause. Parent cancelled146499at293seconds after gatecheck;8helperrequests already admitted, no committed outputs. Future worker should gate internally beforehelperadmission. No locatorwasrun; source-query/readout ratesunestimable. Mainreport, sourceexceptions, per-requestinventories, not-runCSV/bootstrapJSON,Slurmledger andpreservationvalidation retained. All GPUs released;STOP.

### Recovery closure — 2026-10-20

All5profilescompleted. CPU final verification distinguishes schema/branch success from full contract failure and locatornot-attempted fromobservedfailure.268receipts, original377packagefiles/26codefiles and30recoveryexecutionfiles hashchecked. The automatic report remains preserved; separate finalreport clarifies these denominator issues. Scientific H1–H4 remain untested. No new modelcalls during analysis.

### Autonomous technical continuation — 2026-10-20T07:29:52.571160+00:00

v5completed549s,20/20controlsvalid18/20expectedbranch,7/8queries,4/7LOCATE,all48transportverified. UnchangedqueryREAD receipts retained. v6job147559 repairsLOCALemptyboxschema mismatch withfourmodefirstbranches; nativequery/READpromptsunchanged. Frozenv6spec preservesfailedcomponentthresholds and prospectively separates genuinepoor methodyield fromexecutionvalidity, reflectinglatestuserinstruction tocollectbadqueries/fallbacks as scientificdata ratherthanpromptsearch. Fullmainprepared,awaitv6transport/sourceQA+measuredresourceestimate. Priorcompleted3757GPU seconds; currentjobmax1800; allpriorsealeddataunchanged.

### Result check — 2026-10-22

All six execution/package seals and172completed solver receipts passed;2,492main rawJSONfiles newly hashed without changes. Rank0 completed170physical/216logical in18,864allocatedseconds. Rank1 completed2physical/2logical in21,599seconds, saved8interrupted records (6nonempty) and165unadmitted requests. First two new rank1 requests receivedzero decode tokens. No OOM recorded. Historical8source reviews preserved; no completed-pilot claim or answer analysis. Resource accounting and precise remaining inventory saved in audit/result_check_20261022/.
