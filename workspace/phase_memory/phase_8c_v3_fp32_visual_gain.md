# Phase 8C v3: direct FP32 retrieval-triggered visual gain

## Current Objective

Complete the user-approved FP32 intervention plan at its development no-go
boundary. The 512 development trajectories and extraction review are complete;
conditional held-out/timing/local-read stages were not run under plan §18.

## Active Constraints

Full model FP32, TF32 disabled, no autocast or BF16 fallback. Frozen detector,
threshold, layers19–22, source/head scope and gap4 onset rule unchanged. Existing
cohorts/seeds/prompt/pixels/scorer preserved. No pre-efficacy V1–V6, transfer
cohort, detector recalibration or BF16 comparison. User amendment: four node02 GPUs via
scheduler/Slurm, one worker per GPU; finite five-day ceiling, release on exit.

## Current State

Updated 2026-09-22 KST. **Completed: development no-go.** Slurm118545 exited0,
512/512 trajectories complete, four node02 GPUs released. Reviewed correct counts
are 61/60/59/57 of128 for gains1/1.25/1.5/2. W→C/C→W are4/4,3/4,3/7;
unresolved answers12/13/14/14 and unresolved pairs13/14/14. All doses fail both
positive-accuracy and rescue-balance guards. No dose frozen for continuation.
78 masked extraction cases sealed:28 emitted answers,50 extraction-unresolvable;
3 of28 remain unsupported under frozen equivalence. Single main-agent review,
aggregate automatic outcomes previously visible; no independent blinding claim.
All512 receipts/4608 artifact hashes,171 prior hashes and frozen execution sources
verified. Five focused CPU tests pass for the versioned reporting fix. Remaining
compute0GPU-h. Canonical reviewed report: outputs/stage8c_v3/v1/stage8c_v3_summary.md.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| User explicitly supersedes BF16 path and technical gates | plan/stage8c_v3_fp32_direct_retrieval_gain_plan.md | Authorizes FP32 efficacy directly | confirmed |
| BF16 source split fails .125 bound | outputs/stage8c_repair/v1/stage8c_repair_summary.md | Preserve negative history; do not rerun repairs | confirmed |
| Original dev128/test512 and subsets remain sealed | outputs/stage8c_v2/v1/audit/completion_seal.json | Precision change does not justify replacement | verified during preparation |
| Existing runner hard-coded BF16 / technical prerequisite | scripts/stage8c/run_arm.py | Requires additive FP32 entry point | confirmed |
| All three non-native doses fail accuracy and rescue guards | outputs/stage8c_v3/v1/stage8c_v3_dose_freeze.json | Requires stop before test512 | confirmed |
| Reviewed extractions and unresolved labels sealed | outputs/stage8c_v3/v1/annotations/dev_extraction_v1/manual_extraction_seal.json | No gold-conditioned answer selection; limitations explicit | confirmed |
| Complete artifacts and original sources preserved | outputs/stage8c_v3/v1/audit/dev_completion_verification_v1.json | Separates scientific no-go from execution failure | confirmed |

## Failed Attempts and Lessons

No v3 OOM/worker failure. User-cancelled118529 preserved two interrupted attempts;
resume118545 completed. FP32 development efficacy is negative under this fixed
policy; the mechanism is unknown. Previous BF16 failure is separate evidence.
The original analysis helper conflated unresolved outcomes with pending review
and used int(None) for subtype accuracy. Additive analysis_fp32_reviewed.py fixes
review closure and no-credit accounting; original code/scorer/gates preserved.

## Open Candidates

None within this action. No further gain, head, threshold, model or cohort search.

## Next-Step Decision

- Bottleneck resolved: the fixed FP32 gain policy does not improve dev128 accuracy.
- Evidence used: sealed reviewed results and plan §18, not the old BF16 gate.
- Chosen action: stop this branch and preserve development evidence; no test512.
- Alternative rejected: launching held-out despite all three doses failing would
  violate the approved no-go rule. No diagnostic would alter that frozen decision.
- Diagnosis of answer changes: unknown; no semantic/causal inference from accuracy.
- One recommendation: return Block3B recovery/wandering dynamics for user selection.
- Stop here. No automatic Block3B or another research action.

### Step Result

The authorized action is complete at development no-go. Active inference162.17GPU-h;
approximate allocation168.17GPU-h plus0.71GPU-h cancelled. All GPUs released.
Required downstream artifacts explicitly say not-run; local-read Parquet is empty
with status metadata. No confirmatory/timing/local-read claims. Automatic summaries
remain preserved; reviewed results and final runtime have versioned filenames.
Execution definitions: `plan/stage8c_v3_execution_protocol_v1.md`.

### Historical execution notes (superseded by Current State above)


Startup checkpoint 2026-09-20T04:52:26.295778+00:00: 0/512 complete; rank0: 658_g1.00 at 10752 tokens, rank1: 658_g1.25 at 10752 tokens. Both GPU workers stable, no failures. Live throughput about26–28tokens/sec/GPU; provisional dev ETA30–50h, based on prior lengths, not a measured FP32 mean. Source/config hashes remain intact. Job automatically scores the completed development queue and releases GPUs; blind extraction and conditional downstream stages remain. Startup receipt: outputs/stage8c_v3/v1/audit/startup_receipt.json.


Resource amendment 2026-09-20T05:07:29.862968+00:00: cancelled118529 at user request. Zero complete, two
interrupted attempts preserved under original dev/. Frozen512 tasks restart in
dev_four_v1 on four node02 GPUs, one worker/GPU. No scientific change.
Evidence: outputs/stage8c_v3/v1/audit/resume_four_v1/resume_manifest.json.

Submitted Slurm118545 at 2026-09-20T05:09:09.078330+00:00: four node02 GPUs/16CPUs/160G, five-day ceiling. Startup verification pending.

Startup confirmed 2026-09-20T05:10:45.069560+00:00: Slurm118545 has four distinct node02 A6000 GPUs;
all workers >1024 tokens, FP32 logits/cache/activations, no errors. Cancellation
and prior-file hashes verified. Operational resize complete; full scientific
plan still in development. Startup evidence: audit/resume_four_v1/startup_receipt.json.


Development completion action:512 trajectories completed, job118545 exited0 and GPUs released.
78 extraction/equivalence cases remain. Selected next action under the approved plan:
verify all receipts, review emitted answers with gold/dose hidden, seal extractions,
then compare to gold and apply the frozen dev decision. Do not launch test before
this review; unresolved final answers retain no credit and explicit unresolved transitions.
