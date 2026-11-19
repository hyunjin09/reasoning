# Stage7A-Bench v2 reduced execution checklist

Updated 2026-09-15T16:05:01.936417+09:00: **COMPLETE / STOP**. Original broad plan and user scope amendment remain preserved. The immediately previous checklist is archived in `outputs/stage7a_bench_v2/audit/pre_final_state_v26/plan/`.

- [x] Phantom: 400 conditions preserved; no rerun or causal relabeling.
- [x] CharXiv: 200 native reviews/64 pilot events preserved; 1 strong wrong-source, 6 strong faithful, 25 weaker faithful, 32 unresolved.
- [x] MathWild: fixed 96-review semantic gate A passed with 19 localizable candidates/12 bases; original 264 conditions reviewed; fixed 48-event causal pilot complete.
- [x] MMMU: 328 native conditions reviewed with image/silent/guess separation; fixed 33-event causal pilot and qualified paired behavioral accounting complete.
- [x] MMLong native: 200 rows accounted, 190 full reviews, 10 exclusions, 7 caps; source/readout/control review complete.
- [x] MMLong scientific selection: 42 events/36 bases/29 families sealed before effects; 11 token-overlap exclusions preserved.
- [x] Authorized node02 replacement: two A6000/16 CPUs/100G, Slurm114451/tmux10; no additional resource request.
- [x] Exact cache-residency repair validated against immutable native backend on both GPUs; dense/document tensor nonparity retained as a qualification.
- [x] Full 42-event MMLong pilot completed, including both approximately 199k-token cases; successful canonical aggregation at 2026-09-15 15:27KST.
- [x] MMLong result: 2 strong wrong-source, 7 strong faithful, 14 weaker faithful, 19 unresolved; both strong wrong-source cases source/effect-reviewed.
- [x] Five-benchmark/three-axis comparison, nested accounting, eligibility/control coverage, measured costs and interpretation limits complete.
- [x] All 25 figure requirements covered by 26 plots/78 PNG/PDF/SVG exports; visual review and export hashes verified.
- [x] All 23 technical criteria accepted with documented limits under the user amendment and plan O6.
- [x] Exactly one recommendation: Controlled Confusable-Source Construction; proposal only, no natural primary frozen, no follow-up executed. STOP.

Deferred: MathSight, MicroVQA, MedXpertQA-MM. No new benchmark, model-scale study, cohort, monitor, rollback or decoding intervention.

Resource completion: 156.03 accounted GPU-hours across the retained sweep, or 160.77 including separately measured MMLong native wrapper/startup/OOM overhead. MMLong causal runtime sums 27,549.97 one-GPU worker seconds (7.653 GPU-hours), not two-worker wall time; initial mechanics and native work are separately accounted. Full overhead/human annotation cost remains unavailable. Remaining authorized experiment compute is zero. Two GPUs remain allocated through the current Slurm limit (2026-09-18 08:35KST), subject to cluster policy; no maintenance workload or follow-up experiment launched.

Final evidence: `outputs/stage7a_bench_v2/summaries/stage7a_bench_v2_acceptance.json`, `analysis/benchmark_comparison.json`, and `audit/resource_summary.json` under the same output root. Earlier preflight failures, original source snapshots, manifests and state histories remain preserved.
