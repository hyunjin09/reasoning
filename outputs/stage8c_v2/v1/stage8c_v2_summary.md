# Stage8C v2 — STOP at technical validation

Updated 2026-09-20T03:10:30.815974+00:00.

**The required V3 visual-decomposition validation failed. No development,
held-out, timing-control or intervention efficacy experiment was launched.**
This is an implementation-validity stop, not a null or harmful scientific result.

## Completed preparation

- User-approved plan and machine policies read; original plan preserved.
- Existing3040-item MathVision test data/images and pinned Qwen3-VL-2B-Thinking
  reused; no dataset/model download, no environment installation.
- Conservative input-only family audit:575 prior MathVision item IDs excluded,
  then full connected-family exclusion including prior external images.
  2147 eligible independent representatives.
- Frozen128 development and512 test items; one item per identified family;
  disjoint from each other and identified prior-use families. Frozen256 timing
  and128 local-read subsets selected before outcomes.
- Both cohorts cover15 subjects, all5 difficulty levels and choice/free-response
  formats. Topology has4 eligible representatives and was not sampled under
  proportional allocation. Fine problem type, visual density/entity counts are
  missing; they were not invented.
- Family rules combine exact/rescaled image signatures, conservative perceptual
  candidates, specific repeated templates and known1707/1245 alias. They may
  overmerge; independent redraws may still escape. This is not exhaustive
  semantic family certification.
- Online gain/cache wrapper, CPU tests and guarded execution/scoring scaffolding
  written. The scientific runner remains unvalidated and must not be launched.

## Technical evidence and stop

Three short two-A6000 node02 jobs, with no tmux allocation:

| Slurm job | Duration | Result |
|---|---:|---|
|118514|81s|Harness incorrectly required every prefix to contain an onset. Existing native traces distinguished triggered and nontriggered audit prefixes.|
|118515|57s|Manual independent cache-validation call omitted suffix position IDs. Source inspection and a CPU regression reproduced the shape error; existing repository helper reused.|
|118518|57s|V3 reconstruction exceeded the frozen BF16 tolerance on both audited initial items2579 and2433. **STOP.**|

The first two repairs changed validation callers only; gain/detector/cohorts and
numerical bounds remained unchanged. The final V3 bounds were relative L2<=.02
and max absolute error<=.125. The failing assertion did **not** save individual
error magnitudes or which bound failed. Cause remains **unknown**. Do not
attribute the failure to BF16 rounding or to the intervention formula without
additional evidence.

Control-flow evidence shows preceding gain1 and non-trigger token/logit/RNG
equalities, detector comparisons and independent cache replay assertions passed
on those two prefixes. Their complete metric records and the remaining two
prefixes were not finalized. Formal V6 was not reached. Thus the six-check gate
has **not** passed.

Raw evidence: [final validation](stage8c_v2_technical_validation.json),
[worker0 failure](technical_v3/worker0/failure.json),
[worker1 failure](technical_v3/worker1/failure.json),
[original coverage diagnostic](audit/technical_coverage_diagnostic.json),
[resource record](stage8c_v2_runtime_overhead.json).

## Scientific work not run

Dev512 dose trajectories, dose selection, test1024 paired trajectories, random
timing256, semantic audit128, rescue/collateral review and optional extension
are all unmeasured. Required downstream JSON/Parquet files explicitly record
not-run status; the annotation table has zero rows. Seven scientific figures
are not generated because no corresponding data exist. There is no accuracy,
dose-response, timing or generality conclusion, and no chosen dose.

## Resources and next decision

All three allocations are released: approximately0.1083
GPU-hours total. No current stage GPU work remains allowed past the failed gate.
The earlier compute ranges are provisional estimates, **not a current ETA**.

Exactly one recommendation: **diagnose and repair visual-contribution
decomposition, preserving these cohorts and the failed attempts, then revalidate
V1–V6 before resuming Stage8C.** This report does not launch that follow-up or
Block3B. No tolerance relaxation, dose change or cohort replacement was made.
