# Stage8C v3 — completed at development no-go

Updated 2026-09-22T01:43:33.280822+00:00. **Stop the intervention branch under plan §18.** All 512 trajectories
(128 frozen items and 128 visual families × four doses) completed in FP32. Every
non-native dose has lower accuracy than baseline and W→C ≤ C→W. No dose is selected.
Held-out512, timing256, semantic128 and the optional extension were not run.

| Gain | Correct / 128 | Accuracy | Δ pp | W→C | C→W | Unresolved answers / pairs | EOS | Cap | Mean / median reasoning tokens | Episodes / interventions | GPU-h |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.0 | 61 | 47.66% | +0.00 | — | — | 12 / — | 90.62% | 9.38% | 17435.7 / 14673.0 | 1017 / 0 | 41.98 |
| 1.25 | 60 | 46.88% | -0.78 | 4 | 4 | 13 / 13 | 89.84% | 10.16% | 17548.6 / 13740.0 | 979 / 979 | 39.25 |
| 1.5 | 59 | 46.09% | -1.56 | 3 | 4 | 14 / 14 | 89.06% | 10.94% | 17702.9 / 14910.5 | 978 / 978 | 39.87 |
| 2.0 | 57 | 44.53% | -3.12 | 3 | 7 | 14 / 14 | 88.28% | 11.72% | 18150.9 / 15108.5 | 972 / 972 | 41.06 |

Accuracy uses all 128 items; unresolved answers receive no correct credit but remain
unresolved in paired transitions. W→C−C→W therefore need not equal the change in
total correct answers. Reviewed data: [dose results](stage8c_v3_dev_dose_results_reviewed_v1.json).
The originally named `stage8c_v3_dev_dose_results.json` and original runtime file
remain immutable automatic-stage evidence; use the reviewed/final versions here.

The gain trajectory is descriptively negative. At 2×, algebra falls 12.5pp (n=16);
the two other major subjects change by −4pp (area, n=25) and +4.55pp (length, n=22).
These development subgroup results are descriptive. No held-out confirmation,
confidence interval, timing-specificity or local-read improvement is established.
The mechanism behind answer changes remains unknown. The fixed inherited detector
was not recalibrated or validated for FP32 transfer; no BF16 equivalence claim is made.

All 78 automatic extraction/equivalence exceptions were reviewed with gold/dose
masked, then sealed before gold comparison. 28 literal answers were retained:
15 correct, 10 wrong and 3 unsupported/non-unique under the unchanged equivalence
adapter. Another 50 remained unresolved at extraction. The resulting 53 unresolved
arm outcomes are reported explicitly. This was a single main-agent review with
previously visible aggregate scores, not independent blinding. Quotes, character
spans and reasons are preserved in [the extraction seal](annotations/dev_extraction_v1/manual_extraction_seal.json).
The local scorer does not reproduce an upstream external-judge fallback.

The reporting helper required a versioned repair to distinguish completed review
from unresolved answers; the original helper, generation code, scoring tolerance,
dose ordering and scientific guards remain unchanged. Five focused CPU tests pass.
All 512 completion receipts, 4,608 referenced output artifacts, 171 historical
hashes and frozen execution sources passed verification. Ordinary inference
receipts show FP32 attention/logits/cache/observed activations, TF32 off and no
autocast. No OOM or worker failure was found in the completed-run log.

Slurm118545 exited0 after about42h03m; four node02 GPUs are released. Active
inference consumed 162.17 GPU-h; approximate allocated compute was
168.17 GPU-h plus 0.71 GPU-h for the user-cancelled initial run.
Peak allocated/reserved memory was 17.54/
47.10 GiB. Throughput was 15.45–16.64 tokens/s per GPU.
Remaining authorized compute: **0 GPU-h**. [Final runtime](stage8c_v3_runtime_overhead_final_v1.json).

Reviewed figures: [dose response](figures/reviewed_v1/figure1_dev_dose_response.png),
[major-subject effects](figures/reviewed_v1/figure4_dev_subtype_heterogeneity.png),
[rescues and collateral damage](figures/reviewed_v1/figure6_dev_rescue_collateral.png).
Figures 2/3/5/7 are not applicable because their held-out stages were not run.
Not-run artifacts and an empty status-tagged semantic Parquet preserve that boundary.

**One recommendation:** close this visual-gain branch and return Block3B
post-read recovery/wandering dynamics for the user's next-action decision, as
specified by the plan. Block3B has not been launched or implemented by this action.
