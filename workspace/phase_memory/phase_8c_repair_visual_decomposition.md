# Phase 8C-R: visual decomposition repair and revalidation

## Current Objective

Bounded repair action completed at the prescribed V3 failure stop. Scientific
intervention efficacy remains untested; dev128 is not authorized to run under
this failed gate.

## Active Constraints

Preserve the original BF16 model, source definition, post-W_O gain, layers 19–22,
detector, gap-4 onset rule, doses and cohorts. Bounds remain relative L2 <= .02
AND max absolute <= .125. Two node02 GPUs only, via scheduler/Slurm. No Block3B.

## Current State

Updated 2026-09-20T04:21:34.878226+00:00. Both diagnostic jobs completed: 118525 baseline and 118526
full-KV BF16 candidate. Eight fixed cases from four families, three triggered
and five non-trigger anchors, cached indices through 8192, all four layers.
2,064 records per implementation / 4,128 total. GPUs released; approximately
0.397 GPU-hours. No downloads, scientific trajectories or dose selection.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Partition, GQA, concatenation and native full replay exact | outputs/stage8c_repair/v1/stage8c_source_partition_audit.json and stage8c_gqa_audit.json | Excludes observed source/layout mismatch | confirmed |
| Both BF16 source sums reach .25 max abs; 48/2064 rows fail | outputs/stage8c_repair/v1/stage8c_prewo_reconstruction.json | Earliest failure remains pre-W_O | confirmed |
| FP32 diagnostic combined before one BF16 cast passes head bounds | outputs/stage8c_repair/v1/stage8c_dtype_accumulation_audit.json | Supports split reduction/cast localization; cannot certify BF16 intervention | diagnostic only |
| Original and candidate reproduce stored retrieval scores exactly | outputs/stage8c_repair/v1/forensic and candidate item result.json files | Frozen native caller and trigger evidence preserved | confirmed |
| Postprojection .5 / residual 4.0 max abs | outputs/stage8c_repair/v1/stage8c_postwo_reconstruction.json and stage8c_residual_reconstruction.json | Downstream observations, not separate root causes | confirmed |
| All frozen scientific inputs and prior seals preserved | outputs/stage8c_repair/v1/audit/original_scientific_freeze.json | No cohort replacement or historical rewrite | verified |

## Failed Attempts and Lessons

Baseline reproduced both original failures, now saving all metrics before gates.
One supported candidate replaced gathered-source BMMs with full-axis zero-masked
BF16 BMMs; it removes reduction shape/layout differences but still fails .125.
Native replay is exact. Supported diagnosis: separately rounded BF16 reductions
do not reconstruct the joint reduction within the fixed bound. Exact internal
CUDA accumulation remains unknown. No impossibility claim about all conceivable
BF16 implementations. The original failed jobs and source files are preserved.

## Open Candidates

None authorized for execution. Further numerical variants, precision changes,
scientific redesign and other research directions require a new user action.

## Next-Step Decision

- Bottleneck: a valid native BF16 visual contribution remains uncertified.
- Evidence used: both complete eight-case audits and the unchanged absolute gate.
- Chosen action / exactly one recommendation: **stop intervention branch**.
- Why: the sole bounded implementation repair still fails before projection.
- Rejected: dev under uncertainty, wider tolerances, scientific FP32, or defining
  nonvisual contribution as native minus visual merely to force identity.
- Full V1–V6 was not rerun after repair failure; the final bundle explicitly
  marks V3 failed and other fresh gates not run. Historical passes are not reused.
- No dev128, held-out, new intervention or Block3B launch.

### Step Result

Required 13 artifacts and three diagnostic figures are saved under
`outputs/stage8c_repair/v1`. See `outputs/stage8c_repair/v1/stage8c_repair_summary.md`.
Negative technical evidence is preserved; it is not a null efficacy result.
