# Phase 14D: Causal evidence acquisition localization

## Current Objective
Complete the approved source/anchor preparation and bounded calibration, then present the frozen main experiment at the explicit budget/prerequisite gate. Preparation finished 2026-10-11T12:06:20.261717+00:00; scientific execution remains unapproved.

## Active Constraints
- Active plan: `plan/stage14d_causal_evidence_acquisition_localization_plan.md`; unchanged hypothesis/300Thinking(100S1/100S2/100S3)/120Instruct overlap.
- User's “approved” released source/anchor work and at most24 technical calls/2 allocatedGPU-hours/2 concurrent GPUs, not the main run or C-V waiver. Approval receipt: `outputs/stage14d/spec/technical_release_approved_v1.json`.
- Preserve original Stage14A/B/C/C-V images, evidence, scores, prompts and trajectories. This is an outcome-stratified diagnostic panel, not held-out/prevalence evidence.
- Main requires explicit numeric budget/spec approval and C-V closure or waiver. Proposed1674 scientific calls/375 total allocatedGPU-hours/up to8 concurrent GPUs;0 nested/readout calls. No Stage14E/F.
- All CUDA through local scheduler/Slurm. CPU `.venv`; calibrated GPU `.venv/official_eval`; no new packages or downloads.

## Current State
- Done:300 source reviews,296 valid and4 explicit inapplicabilities;12 valid irrelevant-source families.
- Done:414 full native traces and414 second-pass whole-prefix/source/event QC receipts;6 source-inapplicable model slots. Active native indexv68; source override2473v2. Same-agent reviews, no independent reliability claim.
- Done:24/24 technical calls pass; all allocations released;0.36305556 allocatedGPU-hours including startup failures. No main outputs.
- Done:1674 exact CPU input contracts pass;29 current CPU tests; G1/G2 source/anchor seal and main-release review package. Original48-entry G0 seal unchanged.
- Gate: Stage14C-V800C raw calls complete but5 required review/primary/final seals remain absent. No waiver. Main budget unapproved.
- Main inventory:1196Thinking+478Instruct;2100 original slots preserved,396 irrelevant-control inapplicable and30 source-inapplicable. No context-budget exclusions.
- No certified same-layout semantic CF in reused source inventory:300-entry screen,0valid/0nested/0short readouts. Main prompting effects alone cannot certify fresh acquisition.

## Evidence That Matters
| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Completed source/anchor package | `outputs/stage14d/audit/source_anchor_preparation_seal_v1.json` | G1/G2 complete with explicit inapplicability | confirmed |
| Exact1674 inputs and fixed family seeds | `outputs/stage14d/spec/main_condition_manifest_v1.jsonl` | No oracle values in generation payload; preserves2100 slots | CPU verified |
|24 bounded calibration calls | `outputs/stage14d/audit/technical_preflight_validation_v1.json` | Prefix/backend/cache contract valid on disjoint technical sources | confirmed, limited512-token scope |
| Measured resource revision | `outputs/stage14d/audit/main_resource_estimate_v2.json` |178.20linear/362.76stress GPU-hours;375proposed ceiling | estimate, not guarantee |
| C-V missing closure | `outputs/stage14d/audit/stage14cv_prerequisite_status_v2.json` | Separate launch prerequisite remains | confirmed |
|158 second-pass changed records;4state changes | `outputs/stage14d/audit/native_second_pass_changes_v1.json` | Exact timing and earlier partial facts matter; no outcome-driven edits | confirmed |

## Failed Attempts and Lessons
| Attempt | Observation | Diagnosis | Lesson / Guardrail |
|---|---|---|---|
| Technical140568/140569 | RPC setup failed before model generation | named-worker transport repair supported by140574/140575 success | Preserve failed cost; no insecure pickle workaround |
| Earlier long native anchors | Whole-prefix QC found partial/unordered/distributed evidence before first explicit statement | supported by exact quoted versioned corrections | Check entire prefix, not only last sentence; rejected hypotheses remain distinct from resolved state |
| Old42.54GPUh batch projection | New validated serial512-token rates imply178.20GPUh even after exclusions | measured context/throughput mismatch | Do not extrapolate18-way throughput or guarantee long tails |

Source findings:276 frozen7 vs visible?;2869 frozen dot inventory discrepancy;725 structured-complex;2473 target already given by options. None repaired or silently replaced. Native local state is not whole-answer correctness or proof of image acquisition.

## Open Candidates
Only the fixed main intervention panel awaits the original approval gate. No alternate method, extra benchmark, counterfactual construction or oracle arm chosen.

## Next-Step Decision
- Current bottleneck: main numeric/spec release plus C-V closure/explicit waiver.
- Relevant evidence:24-call allowance consumed; measured serial resource estimate supersedes unapproved100GPUh proposal; C-V raw completion is not closure.
- Chosen action: present the completed review package and request approval of1674calls/375totalGPU-hours/up to8GPUs, plus explicit predecessor waiver or instruction to finish closure first.
- Why: all authorized preparatory work is complete; main cannot inherit a numeric budget or waiver from bounded technical approval.
- Do not repeat: technical generations, completed native review, original historical runs, or any overwritten seal. Do not manufacture CFs or irrelevant targets.
- Stop condition: hold at G0/G4; no Slurm submission until explicit main release and prerequisite resolution.

### Step Result
Preparation complete. Review: `outputs/stage14d/reports/stage14d_main_release_review_v1.md`. Runtime/input contract: `spec/main_runtime_contract_v1.json`; main payload/release guard: `scripts/stage14d/main_contract_v1.py`; preregistered analysis: `scripts/stage14d/primary_analysis_v1.py`. Mechanical finite scientific worker/coordinator wiring after release must use these sealed inputs and validated adapter; no additional calibration call is authorized. Checklist: `plan/stage14d_execution_checklist_v2.md`.

Earlier detailed checkpoint history is preserved in `outputs/stage14d/audit/phase_memory_before_main_handoff_v1.md` and versioned audit receipts.
