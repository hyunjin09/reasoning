# Stage14B — COMPLETE / STOP

Completed 2026-10-08T13:50:33.598109+00:00.

All 17,536 main and 9,600 fresh confirmation calls are complete, reviewed and sealed; zero technical missingness. Primary, secondary and three-seed robustness analyses, five PNG/PDF figures, resource accounting and final validation are complete. All GPU allocations and CPU jobs are released. No follow-on stage was launched.

Main paired native Thinking gain +7.20 pp (95% CI 5.67–9.08); Instruct evidence rescue 234/418 scored failures =55.98% (31 unresolved); post-evidence Thinking gain +14.69 pp (12.10–17.39). All three frozen criteria pass. Native and post-evidence gains remain positive in all three frozen confirmation seeds; this is decoding robustness, not untouched independent replication.

Validated native model recipes differ; this is not a causal mode toggle or equal-compute comparison. E* rescue does not isolate pure perception, and the post-evidence gain identifies no downstream mechanism. Source/gold defects, unresolved answers, same-agent review and dependence limits remain explicit.

- [Final report](../../outputs/stage14b/summaries/stage14b_final_summary.md)
- [Primary results](../../outputs/stage14b/analysis/primary_results.json)
- [Secondary/source sensitivities](../../outputs/stage14b/analysis/secondary_results.json)
- [Three-seed robustness](../../outputs/stage14b/analysis/confirmatory_results.json)
- [Completion validation](../../outputs/stage14b/audit/completion_validation.json)
- [Artifact catalog](../../outputs/stage14b/audit/artifact_catalog.json)
- [Resources:193.218 observed/proxy GPU-hours](../../outputs/stage14b/audit/resource_accounting.json)
- [Execution checklist](../../plan/stage14b_execution_checklist.md)

## Figures

- [figure1_mathvision_native_gain (PNG)](../../outputs/stage14b/figures/figure1_mathvision_native_gain.png) · [PDF](../../outputs/stage14b/figures/figure1_mathvision_native_gain.pdf)
- [figure2_evidence_rescue (PNG)](../../outputs/stage14b/figures/figure2_evidence_rescue.png) · [PDF](../../outputs/stage14b/figures/figure2_evidence_rescue.pdf)
- [figure3_post_evidence_gain (PNG)](../../outputs/stage14b/figures/figure3_post_evidence_gain.png) · [PDF](../../outputs/stage14b/figures/figure3_post_evidence_gain.pdf)
- [figure4_mathverse_modality_profile (PNG)](../../outputs/stage14b/figures/figure4_mathverse_modality_profile.png) · [PDF](../../outputs/stage14b/figures/figure4_mathverse_modality_profile.pdf)
- [figure5_confirmatory_stability (PNG)](../../outputs/stage14b/figures/figure5_confirmatory_stability.png) · [PDF](../../outputs/stage14b/figures/figure5_confirmatory_stability.pdf)

Exactly one recommendation: Review and authorize Stage14C task-selectivity testing, taking seed robustness and source limitations into account. NOT_LAUNCHED.

## Preserved execution history

The following are superseded historical snapshots, not current job status.

# Current confirmation status — 2026-10-06T13:14:57.111344+00:00

648/9,600 complete; all8GPUsrunning,0OOM/failures. GenerationETA7–10h (~05:00–08:00KST07Oct), thenreview/analysis/report. CPU137183waitsforGPUcompletion. [ETA evidence](../../outputs/stage14b/audit/confirmation_eta_summary_20261006T1314.json).

# Current status — 2026-10-06T09:29:52.964150+00:00

Main runs, scoring/QC, primary and secondary analyses are sealed. Confirmation jobs137175–137182 are queued (9,600calls;2I+6T;max8A6000GPUs). No OOM watcher active. [Main results, still awaiting confirmation](../../outputs/stage14b/summaries/stage14b_main_results_v1.md). Stage14B is not complete.

## Preserved execution history

# Stage14B — main generation complete; scoring in progress

The full approved stage is in progress, not complete. Frozen scope:17536 main calls +9600 additional confirmation calls.

- [Frozen specification](../../outputs/stage14b/spec/frozen_run_config.json)
- [Scoring/statistics](../../outputs/stage14b/spec/scoring_spec.md)
- [Prospective seal](../../outputs/stage14b/audit/prospective_seal.json)
- [Technical source IDs](../../outputs/stage14b/audit/technical_selection.json)
- [Resource estimate](../../outputs/stage14b/audit/resource_estimate_initial.json)
- [Coordinator contract](../../outputs/stage14b/audit/coordinator_prospective_contract.json)
- [Execution checklist](../../plan/stage14b_execution_checklist.md)

Preflight136015/136016 completed24/24. Coordinator136019 held on unsupported two-letter answers; the source explicitly requests two answers. [Manual technical review](../../outputs/stage14b/audit/preflight_response_review_v2.json) resolved the format hold; [gatePASS](../../outputs/stage14b/audit/preflight_validation.json). One Instruct cap-before-final output is preserved unscorable. No correctness scored, protocol tuned, or output rerun.

Main16,966/17,536 complete at15:25KST06Oct (96.75%). Native/equal-evidence and allInstruct calls complete. Only570ThinkingMathVerse calls remain on twoGPUs; sixjobs finished/released. RemainingmainETA~1.5–3hours including final-request allowance. Confirmation9600newcalls remains gated on scored/sealed primary and secondary analyses.

Initial startup jobs136000/136001 failed before any model requests due to a local module shadowing stdlib statistics. Original logs preserved; import regression reproduces and verifies the rename repair. No scientific setting changed.

Once main queues finish: freeze raws, perform arm-separated response/score review and QC, seal primary before secondary, then launch two additional seeds on the fixed confirmation subsets, publish five figures and final summary.

User-approved [OOM skip/continue amendment](../../plan/stage14b_oom_skip_amendment_v1.md): versioned recovery implementation and42CPUtests complete. CPU-only supervisor136212 RUNNING onnode07 and confirmed all8workers. Pending136205/136206 cancelled/preserved. Original healthy workers continue unchanged.

Upcoming03:00KST cleanup: CPU-only standby136370 is queued withafterany:136212, eligible no earlier than03:05KST06Oct. No GPU added. [Launch receipt](../../outputs/stage14b/audit/oom_watch_standby_launch_v1.json).

Latest watcher state:136370 took over03:05KST06Oct and remainsRUNNING. Next-night0GPUstandby136898 queued after136370, notbefore03:05KST07Oct.

Current 2026-10-06T09:00:50.390849+00:00: main17,536receipts raw-sealed,0technical failures; mainGPUsreleased. Watcher136370 terminal, standby136898 cancelled. Instruct response extraction and initial equivalence review finished; supplemental QC before seal. Thinking and paired inference unopened. Confirmation9,600calls remain gated. [Gold-format repair](../../outputs/stage14b/audit/gold_choice_format_repair_v5.md).
