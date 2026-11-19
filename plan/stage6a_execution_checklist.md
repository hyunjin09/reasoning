# Stage6A execution checklist

Authorized source: stage6a_dedicated_alignment_mirage_retrieval_dynamics_cohort_plan.md.

1. Inventory datasets in policy order, verify usable images/annotations and record
   local revisions, licenses and no-download manifest. Verify existing four GPUs.
2. Freeze config, annotation/manipulation/segmentation/split rules and prospective
   candidate order. C2 uses the explicit alternative target of32 events per cell:
   32 same-image families ×4 semantic-design conditions =128 events.
3. Implement only Stage6A adapters/stimulus builders and meaningful tests for
   masking/sham isolation, object joins, exact span indices and grouped splits.
4. Author and audit12 mechanics families (ideally3 per cohort), then run four GPU
   ranks. Verify replay/routing/no-op/no-image/unrelated state and annotation joins.
5. Run24-family pilot only after mechanics passes. Freeze any repaired rules before
   scaling; pilot/validation families do not enter fresh confirmation.
6. Construct C1 target120/min90, C2 target32/min24 per cell, C3 target160/min120.
   Screen by semantic validity, ROI/editability and native interpretability only.
7. Run600 randomly frozen C4 images. Only if needed for the prescribed hallucination
   yield, extend the prespecified random order up to1000. Freeze balanced atlas
   separately from unbiased prevalence; preserve all failed/truncated outcomes.
8. Complete native/stress traces, semantic demand/local/final/hallucination labels,
   transitions and future anchors. Freeze stimulus-group discovery/confirmation
   splits and audit historical/exact/perceptual duplicates across datasets.
9. Produce required18 tables, provenance/resource/audit artifacts and acceptance
   report. Recommend exactly one permitted next stage and stop.

All model work uses existing Slurm109385/node03/tmux9 four A6000s, registered in
the project scheduler. No new Slurm request and no external dataset writes.
Full causal scoring, PCA trajectories, surrogates and rescue are outside this stage.

Current progress: steps1–9 complete on 2026-09-09. All 70 plan-required output files and 18 tables are present and audited. Controlled gates pass; the natural atlas has 10 pairs against its 60-pair minimum. Sole recommendation: GO — Natural Failure Extension; no next stage executed. Final report: `outputs/stage6a/summaries/stage6a_cohort_summary.md`.
