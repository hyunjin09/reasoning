# Stage8C-R — bounded repair completed; STOP intervention branch

Updated 2026-09-20T04:19:51.286575+00:00.

**The BF16-preserving candidate failed the unchanged V3 bound. Dev128 was not launched.**

Diagnosis is supported: splitting the native source reduction introduces independent BF16 rounding. Source membership, masks, GQA, concatenation and bias handling pass; the first discrepancy is before W_O. Exact native reconstruction passes, while a higher-precision diagnostic improves agreement. This establishes a technical limitation of the tested implementations, not a null efficacy result.

| Quantity | Original | Full-KV BF16 candidate | Limit |
|---|---:|---:|---:|
|Pre-W_O BF16 source sum max abs|0.25|0.25|0.125|
|Separate BF16 projected contributions max abs|0.5|0.5|0.125|
|Native-order residual reconstruction max abs|4|4|0.125|

Eight fixed cases cover4 independent families,3 triggered/5 nontriggered anchors and short/medium/long cached lengths. Original failing short traces were fully logged through255 decode queries each;4,128 total layer-query records across two implementations are preserved. Every row was written before numerical gating. Relative L2 and maximum absolute bounds are both enforced.

One candidate was tested. No gate or scientific setting changed; the original implementation, failed jobs and all frozen Stage8C cohorts remain byte-identical. The final V1–V6 bundle explicitly records V3 failure and the remaining fresh checks as not run. No false revalidation pass is assembled from historical checks.

**Exactly one recommendation: stop intervention branch.** No dev128, held-out run, precision switch or Block3B was launched. The evidence does not invalidate retrieval observability or Value-rich transport, and it does not prove all possible BF16 decompositions impossible.

Both node02 allocations are released. Resource accounting is in [resources](audit/resources.json). There is no scientific ETA under the failed gate.

[Root-cause evidence](stage8c_repair_root_cause.md) · [Full forensic metrics](stage8c_v3_forensic_metrics.parquet) · [Final gate status](stage8c_v1_v6_revalidation.json) · [Candidate diff](stage8c_repaired_implementation_diff.txt).
