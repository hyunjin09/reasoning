# Phase12B-R: pathology-aware validity repair

## Current Objective
Validate input integrity and scoreability on12 fresh families, preserving reasoning pathology as data.

## Active Constraints
- Preserve all Stage12B artifacts,61families/157facts,model/runtime/prompts/seeds/caps.
- Select12 from remaining49 using identity/answer type only; exclude original12 development cases.
- E/N/O each: inputs12/12,scoreable>=10/12,truncated-before-outcome<=1/12; no repetition threshold.
- No correctness or B1–B4/P1–P6 inference; no CoT/Thinking.36calls only,target<0.6/hard1.0 allocatedGPUh.
- Section21 explicitly requires separate authorization for full profiling despite conditional discussion in sections14/24.

## Current State
- Done: policies,active plan,Stage12B memory/evidence/runtime read; old artifact hashes preserved.
- Done:5MC/7open fresh families frozen;36requests exact Stage12B copies; prospective rules/guide sealed,4CPU protocol tests pass.
- Done: all 36 E/N/O calls and output-only annotations; all 9 required artifacts sealed. Decision VALIDITY_REPAIRED.
- Done: Slurm127673/node03 and127674/node02 completed exit0 and released both GPUs; 0.602778 allocated GPU-hours (10 GPU-seconds above target, below 1.0 hard maximum).
- In progress: none. Full scientific profiling not launched; stop at the section21 boundary.
- Blocked: none.

## Evidence That Matters
| Evidence | Source | Relevance | Status |
|---|---|---|---|
|All36development calls normal stop; N12/O11finals but N4/O3 severe cycles|outputs/stage12b/v1/stage12b_summary.md|Repetition exclusion censors scoreable behavior|confirmed|
|Old repeated-generation cause unknown|same|Do not claim cause or tune recipe|unknown|
|All arms inputs12/12; E scoreable12, N/O11 each; N/O pre-outcome truncation1 each|outputs/stage12br/v1/stage12br_validation_decision.json|All frozen technical gates pass|confirmed|
|N R1–R5=8/7/7/4/0; O=7/5/5/3/1, each out of12|outputs/stage12br/v1/stage12br_pathology_labels.parquet|Pathology persists and is retained independently of scoreability; no correctness inference|confirmed|
|O2214/O991 cap after still-committed answers; N2013 no task answer, O1974 unresolved terminal ratios|outputs/stage12br/v1/audit/manual_validation_decisions.json|Four caps include two scoreable outcomes and two pre-outcome truncations|confirmed by one-agent semantic review|
|192 historical artifacts and prospective hashes unchanged; 36 receipt/input checks pass|outputs/stage12br/v1/audit/closure_validation.json|Preservation and implementation integrity|confirmed|

## Failed Attempts and Lessons
No failed execution attempts in Stage12B-R. Prior repetition-based gate remains historical; the prospective repair passed untouched validation. Scoreability is not correctness. Two capped oracle traces retain explicit forced commitments despite nonconvergent support; the other capped oracle trace lacks a settled terminal ratio. Causes of repetition remain unknown, and there is no independent inter-rater reliability estimate.

## Open Candidates
Approved fresh validation is complete. Full scientific profile requires separate authorization; no new action selected.

## Next-Step Decision
- Current bottleneck: assay scoreability after removing pathology from exclusion criteria.
- Relevant memory: D132 — eventual commitment and normal stopping can coexist with severe cycles.
- Chosen next action: freeze identity-only12/36calls and new rules,run unchanged E/N/O,review without gold,seal decision.
- Why: user-approved smallest discriminating validity action; no protocol search.
- Do not repeat: use development cases as fresh validation,select by outcomes,exclude R1–R4 automatically.
- Stop condition: validated36calls and decision,any input failure,or1.0GPUh; do not resume full profiling automatically.

### Step Result
VALIDITY_REPAIRED on all three arms. No task/evidence correctness opened, no B1–B4/P1–P6 estimates, and no CoT/Thinking runs. Exact prompts/model/runtime/caps/seeds and all61 families/157facts preserved. Raw responses are readable at reports/stage12br/v1/index.md. Validation changes the next decision from assay repair to eligibility for separately authorized original Stage12B profiling; it does not authorize that launch. STOP.
