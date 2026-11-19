# Stage14E2 — completed diagnostic / PAUSED (2026-10-23T02:50:35.340469+00:00)

[Final diagnostic report](../outputs/stage14e_readout_mechanism/v1/reports/final_diagnostic_report_v1.md) · [All24casebook](../outputs/stage14e_readout_mechanism/v1/reports/casebook_v1.md). Primary4/24versus4/24; no demonstrated improvement. All allocations released,8.8175/24cumulativeGPUh. User-requested pause; no follow-up. Earlier entries are history.

# Stage14E2 — ACTIVE reader-mode diagnosis

[Plan](../plan/stage14e2_deliberative_source_reading_plan_v1.md) · [Phase](../workspace/phase_memory/phase_14e2_deliberative_source_reading.md). Jobs150977/150978, two single GPUs, same24GPUh ceiling including prior7.148889. Goal remains unachieved. Prior-cycle closure below is preserved history.

# Stage14E — completed bounded acquisition cycle (2026-10-23T01:05:50.094588+00:00)

[Final report](../outputs/stage14e_acquisition_development/v1/reports/final_research_report_v1.md) · [All32 casebook](../outputs/stage14e_acquisition_development/v1/reports/final32_casebook_v1.md). Completed the authorized bounded research cycle: all72 SAVA postmortem,24-family diagnostic, one24-family revision and one32-family evaluation;96logical/77physical solvers,19native aliases. Acquisition M0/32 versus S1/32; M−S−3.125pp,95%CI[−9.375,0]. Final answers: N 19/32, S 20/32, M 20/32; unscorable N=0, S=0, M=0. All allocations released; new7.148889/24GPUh, historical21.365278GPUh separate. No demonstrated acquisition improvement. No further tuning or follow-on launch. OldStage14D375GPUh remains HOLD; Stage14C-V remains unfinished.

Earlier entries are historical.

[Stage14E bounded acquisition development — EVALUATION QUEUED](../outputs/stage14e_acquisition_development/v1/reports/research_progress_v1.md): all72postmortem,24diagnostic and24ledgerrevision complete;32familyevalpending150382/afterok150404. Noefficacyclaim. [All72casebook](../outputs/stage14e_acquisition_development/v1/reports/sava_all72_casebook_v1.md).

- 2026-10-22: [Stage14D-1 SAVA completed72-family pilot](../outputs/stage14d1_sava_pilot/v1/reports/feasibility_main_v8.md) —432logical/345physical;QI−N−4.17pp,CI[−12.50,+4.17];allGPUsreleased;noStage14Elaunch.

- 2026-10-22: [Stage14D-1 SAVA recovery v8 technical findings](../outputs/stage14d1_sava_pilot/v1/reports/resumption_v8_technical_findings.md) — generation active; source reviews sealed; previous HOLD/NO-GO entries below are preserved historical states.

- 2026-10-22: [Stage14D-1 SAVA result check:218/432 outputs, resource-feasibility HOLD](../outputs/stage14d1_sava_pilot/v1/reports/result_check_20261022.md).

- [Stage14D-1 SAVA technical validation and queued72-family pilot](../outputs/stage14d1_sava_pilot/v1/reports/technical_validation_and_execution_status.md) — technicalPASS; scientificexecutionawaitsGPU/hostRAMcapacity; notcomplete.

# Stage14D1 SAVA recovery — complete technical report (2026-10-20T06:36:00.572618+00:00)

[Final report](../outputs/stage14d1_sava_recovery/v1/reports/technical_recovery_final.md): replay validated; query provenance gate still fails; pilot NO-GO.268requests,0.7525cumulativetechnicalGPUh, bothjobscomplete, nofollow-on. Earlier entries are historical.

# Stage14D1 SAVA technical recovery — queued (2026-10-19T13:25:53.638251+00:00)

[Recovery package](../outputs/stage14d1_sava_recovery/v1/README.md) · [CPU diagnosis](../outputs/stage14d1_sava_recovery/v1/reports/cpu_diagnosis.md). Eight-family diagnostic146598 pending; CPUreport146599 verified dependent. Exact gate retained; no scientific pilot. Prior bounded-stop evidence below remains preserved.

# Stage14D1 SAVA — bounded technical stop (2026-10-19)

[Feasibility report](../outputs/stage14d1_sava/reports/feasibility_main.md) · [Package](../outputs/stage14d1_sava/README.md). Exactreplay6/8;R72mainnotrun;0.394722GPUh;allGPUsreleased. Earlierentriespreservedbelow.

# Workflow Report Index

[Stage14D1 SAVA — technical feasibility in progress](../outputs/stage14d1_sava/README.md): source-selectedR72, eight-family smoke, new16GPUhstage ceiling; no oracle inference inputs, six controlled arms.

[Stage14D0 visual difficulty v2 — COMPLETE / STOP](../outputs/stage14d0_visual_difficulty/v2/README.md): R150/986 source annotations, 979 eligible facts, A–G weighted/paired analyses and method-design implications. Optional F deferred; zero new inference/GPU work. Historical audit preserved.

[Stage14D0 — COMPLETE / STOP](../outputs/stage14d0/README.md): 300 paired families / 600 native traces, source-anchored analyses A–F, five figures and [viewer](../outputs/stage14d0/viewer/index.html). Zero new inference/GPU use. Single-AI semantic audit; no independent human reliability. Old Stage14D main remains HOLD.

[Stage14D — preparation complete; main release pending](../outputs/stage14d/reports/stage14d_main_release_review_v1.md): source/anchor QC complete,24technical calls pass,1674eligible main calls frozen;375GPUh proposal and C-Vclosure/waiver await approval. No main inference.

Project: `/data/projects/hyunjin/MLLM/reasoning_steps`

[Stage14C — COMPLETE / STOP](stage14c/index.md): final validation passed; all main and D1 calls complete, all allocations released. Stage14C rows below reflect terminal state; unrelated historical scheduler records are preserved.

[Stage14C-V — R sealed; C underway](stage14cv/index.md): all1800R outputs complete; primary typed-format effect−22.33pp in Instruct; prespecified proseformat benefits both.800Ccalls submitted; reviews/synthesis/closure remain.32GPUh ceiling.

## GPU Jobs

| id | status | exp_id | gpu_type | slurm_job_id | log |
|---|---|---|---|---|---|
| piqd_phase0_env_install | cancelled | piqd_phase0_env_install | a4000 | 85814 | runs/piqd_phase0_env_install/slurm.log |
| piqd_phase0_env_install_uvcache | succeeded | piqd_phase0_env_install_uvcache | a4000 | 85825 | runs/piqd_phase0_env_install_uvcache/slurm.log |
| piqd_phase0_torch_cuda_check | cancelled | piqd_phase0_torch_cuda_check | a6000 | 85829 | runs/piqd_phase0_torch_cuda_check/slurm.log |
| piqd_phase0_torch_cuda_check_a4000 | succeeded | piqd_phase0_torch_cuda_check_a4000 | a4000 | 85830 | runs/piqd_phase0_torch_cuda_check_a4000/slurm.log |
| piqd_phase1_model_load | succeeded | piqd_phase1_model_load | a100 | 85869 | runs/piqd_phase1_model_load/slurm.log |
| piqd_phase1_diag | succeeded | piqd_phase1_diag | a100 | 85874 | runs/piqd_phase1_diag/slurm.log |
| piqd_phase1_smoke_10 | succeeded | piqd_phase1_smoke_10 | a100 | 85876 | runs/piqd_phase1_smoke_10/slurm.log |
| piqd_phase2_diag | succeeded | piqd_phase2_diag | a100 | 85884 | runs/piqd_phase2_diag/slurm.log |
| piqd_phase2_extract_10 | succeeded | piqd_phase2_extract_10 | a100 | 85886 | runs/piqd_phase2_extract_10/slurm.log |
| visual_reasoning_stage0_smoke_3 | cancelled | visual_reasoning_stage0_smoke_3 | a6000 | 104051 | runs/visual_reasoning_stage0_smoke_3/slurm.log |
| visual_reasoning_stage0_smoke_3_a5000 | cancelled | visual_reasoning_stage0_smoke_3_a5000 | a5000 | 104059 | runs/visual_reasoning_stage0_smoke_3_a5000/slurm.log |
| visual_reasoning_stage0_smoke_2048_a5000 | succeeded | visual_reasoning_stage0_smoke_2048_a5000 | a5000 | 104062 | runs/visual_reasoning_stage0_smoke_2048_a5000/slurm.log |
| visual_reasoning_stage0_full_30_a5000 | succeeded | visual_reasoning_stage0_full_30_a5000 | a5000 | 104064 | runs/visual_reasoning_stage0_full_30_a5000/slurm.log |
| visual_reasoning_stage1a_pilot_4096_a6000 | cancelled | visual_reasoning_stage1a_pilot_4096_a6000 | a6000 | 104179 | runs/visual_reasoning_stage1a_pilot_4096_a6000/slurm.log |
| visual_reasoning_stage1a_pilot_4096_a5000 | cancelled | visual_reasoning_stage1a_pilot_4096_a5000 | a5000 | 104180 | runs/visual_reasoning_stage1a_pilot_4096_a5000/slurm.log |
| visual_reasoning_stage1a_pilot_4096_node07_a6000 | succeeded | visual_reasoning_stage1a_pilot_4096_node07_a6000 | a6000 | 104181 | runs/visual_reasoning_stage1a_pilot_4096_node07_a6000/slurm.log |
| visual_reasoning_stage1a_pilot_8192_node07_a6000 | succeeded | visual_reasoning_stage1a_pilot_8192 | a6000 | 104189 | runs/visual_reasoning_stage1a_pilot_8192_node07_a6000/slurm.log |
| visual_reasoning_stage1a2_sampling_smoke_a5000 | succeeded | visual_reasoning_stage1a2_sampling_smoke | a5000 | 104349 | runs/visual_reasoning_stage1a2_sampling_smoke_a5000/slurm.log |
| vr_stage1a2_official_s00_a5000 | succeeded | vr_stage1a2_official_s00 | a5000 | 104350 | runs/vr_stage1a2_official_s00_a5000/slurm.log |
| vr_stage1a2_official_s01_a5000 | succeeded | vr_stage1a2_official_s01 | a5000 | 104351 | runs/vr_stage1a2_official_s01_a5000/slurm.log |
| vr_stage1a2_greedy_completed_a4000 | cancelled | vr_stage1a2_greedy_completed | a4000 | 104352 | runs/vr_stage1a2_greedy_completed_a4000/slurm.log |
| vr_stage1a2_official_s02_a4000 | cancelled | vr_stage1a2_official_s02 | a4000 | 104354 | runs/vr_stage1a2_official_s02_a4000/slurm.log |
| vr_stage1a2_greedy_long23_a4000 | cancelled | vr_stage1a2_greedy_long23 | a4000 | 104353 | runs/vr_stage1a2_greedy_long23_a4000/slurm.log |
| vr_stage1a2_official_s03_a5000 | succeeded | vr_stage1a2_official_s03 | a5000 | 104355 | runs/vr_stage1a2_official_s03_a5000/slurm.log |
| vr_stage1a2_official_s04_a5000 | succeeded | vr_stage1a2_official_s04 | a5000 | 104356 | runs/vr_stage1a2_official_s04_a5000/slurm.log |
| vr_stage1a2_official_s02_retry_a5000 | succeeded | vr_stage1a2_official_s02_retry | a5000 | 104361 | runs/vr_stage1a2_official_s02_retry_a5000/slurm.log |
| vr_stage1a2_greedy_long33_a5000 | succeeded | vr_stage1a2_greedy_long33 | a5000 | 104369 | runs/vr_stage1a2_greedy_long33_a5000/slurm.log |
| vr_stage1a2_greedy_long34_a5000 | succeeded | vr_stage1a2_greedy_long34 | a5000 | 104370 | runs/vr_stage1a2_greedy_long34_a5000/slurm.log |
| vr_stage1a2_greedy_long39_a5000 | succeeded | vr_stage1a2_greedy_long39 | a5000 | 104375 | runs/vr_stage1a2_greedy_long39_a5000/slurm.log |
| vr_stage1a2_greedy_long43_a5000 | succeeded | vr_stage1a2_greedy_long43 | a5000 | 104376 | runs/vr_stage1a2_greedy_long43_a5000/slurm.log |
| vr_stage1a2_greedy_controls_a5000 | cancelled | vr_stage1a2_greedy_controls | a5000 | 104378 | runs/vr_stage1a2_greedy_controls_a5000/slurm.log |
| vr_stage1a2_greedy_long23_a5000 | succeeded | vr_stage1a2_greedy_long23_retry | a5000 | 104412 | runs/vr_stage1a2_greedy_long23_a5000/slurm.log |
| vr_stage1a2_greedy_control44_a5000 | succeeded | vr_stage1a2_greedy_control44 | a5000 | 104413 | runs/vr_stage1a2_greedy_control44_a5000/slurm.log |
| vr_stage1a2_greedy_control48_a5000 | succeeded | vr_stage1a2_greedy_control48 | a5000 | 104414 | runs/vr_stage1a2_greedy_control48_a5000/slurm.log |
| vr_stage1a2_faith_34_a5000 | succeeded | vr_stage1a2_faith_34 | a5000 | 104417 | runs/vr_stage1a2_faith_34_a5000/slurm.log |
| vr_stage1a2_faith_44_a5000 | succeeded | vr_stage1a2_faith_44 | a5000 | 104418 | runs/vr_stage1a2_faith_44_a5000/slurm.log |
| vr_stage1a2_faith_48_a5000 | succeeded | vr_stage1a2_faith_48 | a5000 | 104424 | runs/vr_stage1a2_faith_48_a5000/slurm.log |
| vr_stage1b_discovery_s00_a5000 | cancelled | vr_stage1b_discovery_s00 | a5000 | 104437 | runs/vr_stage1b_discovery_s00_a5000/slurm.log |
| vr_stage1b_discovery_s01_a5000 | cancelled | vr_stage1b_discovery_s01 | a5000 | 104438 | runs/vr_stage1b_discovery_s01_a5000/slurm.log |
| vr_stage1b_discovery_x00_a5000 | succeeded | vr_stage1b_discovery_x00 | a5000 | 104439 | runs/vr_stage1b_discovery_x00_a5000/slurm.log |
| vr_stage1b_discovery_x01_a5000 | succeeded | vr_stage1b_discovery_x01 | a5000 | 104440 | runs/vr_stage1b_discovery_x01_a5000/slurm.log |
| vr_stage1b_discovery_x02_a5000 | succeeded | vr_stage1b_discovery_x02 | a5000 | 104441 | runs/vr_stage1b_discovery_x02_a5000/slurm.log |
| vr_stage1b_discovery_x03_a5000 | succeeded | vr_stage1b_discovery_x03 | a5000 | 104442 | runs/vr_stage1b_discovery_x03_a5000/slurm.log |
| vr_stage1b_discovery_x04_a5000 | succeeded | vr_stage1b_discovery_x04 | a5000 | 104443 | runs/vr_stage1b_discovery_x04_a5000/slurm.log |
| vr_stage1b_discovery_x05_a5000 | succeeded | vr_stage1b_discovery_x05 | a5000 | 104444 | runs/vr_stage1b_discovery_x05_a5000/slurm.log |
| vr_stage1b_discovery_x06_a5000 | succeeded | vr_stage1b_discovery_x06 | a5000 | 104445 | runs/vr_stage1b_discovery_x06_a5000/slurm.log |
| vr_stage2b_pilot_a6000_node06 | cancelled | visual_reasoning_stage2b | a6000 |  | runs/stage2b_a6000_node06/slurm.log |
| vr_stage2b_pilot_a6000_exclude03 | succeeded | visual_reasoning_stage2b | a6000 | 105479 | runs/stage2b_a6000_exclude03/slurm.log |
| vr_stage2c_temporal_audit_a6000_exclude03 | running | visual_reasoning_stage2c | a6000 | 105744 | runs/visual_reasoning_stage2c/slurm.log |
| vr_stage3a_expand_s00_a5000 | running | visual_reasoning_stage3a | a5000 | 106064 | runs/stage3a_expand_s00/slurm.log |
| vr_stage3a_expand_s01_a5000 | running | visual_reasoning_stage3a | a5000 | 106065 | runs/stage3a_expand_s01/slurm.log |
| vr_stage3a_expand_s02_a5000 | running | visual_reasoning_stage3a | a5000 | 106066 | runs/stage3a_expand_s02/slurm.log |
| vr_stage3a_expand_s03_a5000 | running | visual_reasoning_stage3a | a5000 | 106067 | runs/stage3a_expand_s03/slurm.log |
| vr_stage3a_scoring_smoke_119_a5000 | running | visual_reasoning_stage3a | a5000 | 106083 | runs/stage3a_scoring_smoke_119/slurm.log |
| vr_stage3a_expand_backup_a5000 | running | visual_reasoning_stage3a | a5000 | 106084 | runs/stage3a_expand_backup/slurm.log |
| stage3a_r3_gen_s00 | running | stage3a_r3_gen_s00 | a5000 | 106268 | runs/stage3a_r3_gen_s00/slurm.log |
| stage3a_r3_gen_s01 | running | stage3a_r3_gen_s01 | a5000 | 106269 | runs/stage3a_r3_gen_s01/slurm.log |
| stage3a_r3_gen_s02 | running | stage3a_r3_gen_s02 | a5000 | 106270 | runs/stage3a_r3_gen_s02/slurm.log |
| stage3a_r3_gen_s03 | running | stage3a_r3_gen_s03 | a5000 | 106271 | runs/stage3a_r3_gen_s03/slurm.log |
| stage3a_score_s00 | running | stage3a_score_s00 | a5000 | 106319 | runs/stage3a_score_s00/slurm.log |
| stage3a_score_s01 | running | stage3a_score_s01 | a5000 | 106320 | runs/stage3a_score_s01/slurm.log |
| stage3a_score_s02 | running | stage3a_score_s02 | a5000 | 106321 | runs/stage3a_score_s02/slurm.log |
| stage3a_score_s03 | running | stage3a_score_s03 | a5000 | 106322 | runs/stage3a_score_s03/slurm.log |
| stage3a_score_s04 | running | stage3a_score_s04 | a5000 | 106323 | runs/stage3a_score_s04/slurm.log |
| stage3a_score_s05 | running | stage3a_score_s05 | a5000 | 106324 | runs/stage3a_score_s05/slurm.log |
| stage3a_score_s06 | succeeded | stage3a_score_s06 | a5000 | 106325 | runs/stage3a_score_s06/slurm.log |
| stage3a_score_s07 | cancelled | stage3a_score_s07 | a5000 | 106326 | runs/stage3a_score_s07/slurm.log |
| stage3a_hweq_119_a6000 | failed | visual_reasoning_stage3a | a6000 | 106330 | runs/stage3a_hweq_119_a6000/slurm.log |
| stage3a_score_s07_retry | cancelled | stage3a_score_s07 | a5000 | 106333 | runs/stage3a_score_s07_retry/slurm.log |
| stage3a_hweq_119_a6000_exclude03 | cancelled | visual_reasoning_stage3a | a6000 | 106334 | runs/stage3a_hweq_119_a6000_exclude03/slurm.log |
| stage3a_score_s07_retry2 | cancelled | stage3a_score_s07 | a5000 | 106335 | runs/stage3a_score_s07_retry2/slurm.log |
| stage3a_hweq_119_a6000_short | cancelled | visual_reasoning_stage3a | a6000 | 106336 | runs/stage3a_hweq_119_a6000_short/slurm.log |
| stage3a_score_s07_retry3 | cancelled | stage3a_score_s07 | a5000 | 106337 | runs/stage3a_score_s07_retry3/slurm.log |
| stage3a_node03_cuda_diagnostic | succeeded | visual_reasoning_stage3a | a6000 | 106338 | runs/stage3a_node03_cuda_diagnostic/slurm.log |
| stage3a_score_s07_retry4 | running | stage3a_score_s07 | a5000 | 106339 | runs/stage3a_score_s07_retry4/slurm.log |
| stage3b0_smoke_a5000 | succeeded | visual_reasoning_stage3b0_smoke | a5000 | 106387 | runs/stage3b0_smoke/slurm.log |
| stage3b0_cached_parity_119 | succeeded | visual_reasoning_stage3b0_diagnostic | a5000 | 106404 | runs/stage3b0_cached_parity/slurm.log |
| stage3b0_smoke_validated_a5000 | succeeded | visual_reasoning_stage3b0_smoke_validated | a5000 | 106405 | runs/stage3b0_smoke_validated/slurm.log |
| stage3b0_cohort_00_a5000 | succeeded | visual_reasoning_stage3b0_cohort_00 | a5000 | 106408 | runs/stage3b0_cohort/shard_00.log |
| stage3b0_cohort_01_a5000 | succeeded | visual_reasoning_stage3b0_cohort_01 | a5000 | 106409 | runs/stage3b0_cohort/shard_01.log |
| stage3b0_cohort_02_a5000 | succeeded | visual_reasoning_stage3b0_cohort_02 | a5000 | 106410 | runs/stage3b0_cohort/shard_02.log |
| stage3b0_cohort_03_a5000 | succeeded | visual_reasoning_stage3b0_cohort_03 | a5000 | 106411 | runs/stage3b0_cohort/shard_03.log |
| stage3b0_cohort_04_a5000 | succeeded | visual_reasoning_stage3b0_cohort_04 | a5000 | 106412 | runs/stage3b0_cohort/shard_04.log |
| stage3b0_cohort_05_a5000 | succeeded | visual_reasoning_stage3b0_cohort_05 | a5000 | 106413 | runs/stage3b0_cohort/shard_05.log |
| stage3b0_cohort_06_a5000 | succeeded | visual_reasoning_stage3b0_cohort_06 | a5000 | 106414 | runs/stage3b0_cohort/shard_06.log |
| stage3b1_smoke_a6000 | cancelled | visual_reasoning_stage3b1_smoke | a6000 | 106441 | runs/stage3b1_smoke/slurm.log |
| stage3b1_smoke_a5000 | succeeded | visual_reasoning_stage3b1_smoke_a5000 | a5000 | 106449 | runs/stage3b1_smoke_a5000/slurm.log |
| stage3b1_cohort_00_a5000 | cancelled | visual_reasoning_stage3b1_cohort_00 | a5000 |  | runs/stage3b1_cohort/shard_00.log |
| stage3b1_cohort_01_a5000 | cancelled | visual_reasoning_stage3b1_cohort_01 | a5000 |  | runs/stage3b1_cohort/shard_01.log |
| stage3b1_cohort_02_a5000 | cancelled | visual_reasoning_stage3b1_cohort_02 | a5000 |  | runs/stage3b1_cohort/shard_02.log |
| stage3b1_cohort_03_a5000 | cancelled | visual_reasoning_stage3b1_cohort_03 | a5000 |  | runs/stage3b1_cohort/shard_03.log |
| stage3b1_cohort_04_a5000 | cancelled | visual_reasoning_stage3b1_cohort_04 | a5000 |  | runs/stage3b1_cohort/shard_04.log |
| stage3b1_cohort_05_a5000 | cancelled | visual_reasoning_stage3b1_cohort_05 | a5000 |  | runs/stage3b1_cohort/shard_05.log |
| stage3b1_cohort_06_a5000 | cancelled | visual_reasoning_stage3b1_cohort_06 | a5000 |  | runs/stage3b1_cohort/shard_06.log |
| stage3b1_cohort_00_a5000_pending | succeeded | visual_reasoning_stage3b1_cohort_00 | a5000 | 106458 | runs/stage3b1_cohort/shard_00.log |
| stage3b1_cohort_01_a5000_pending | succeeded | visual_reasoning_stage3b1_cohort_01 | a5000 | 106459 | runs/stage3b1_cohort/shard_01.log |
| stage3b1_cohort_02_a5000_pending | succeeded | visual_reasoning_stage3b1_cohort_02 | a5000 | 106460 | runs/stage3b1_cohort/shard_02.log |
| stage3b1_cohort_03_a5000_pending | succeeded | visual_reasoning_stage3b1_cohort_03 | a5000 | 106461 | runs/stage3b1_cohort/shard_03.log |
| stage3b1_cohort_04_a5000_pending | succeeded | visual_reasoning_stage3b1_cohort_04 | a5000 | 106462 | runs/stage3b1_cohort/shard_04.log |
| stage3b1_cohort_05_a5000_pending | succeeded | visual_reasoning_stage3b1_cohort_05 | a5000 | 106463 | runs/stage3b1_cohort/shard_05.log |
| stage3b1_cohort_06_a5000_pending | succeeded | visual_reasoning_stage3b1_cohort_06 | a5000 | 106464 | runs/stage3b1_cohort/shard_06.log |
| stage3b2_smoke_a5000 | failed | stage3b2_smoke_a5000 | a5000 | 106542 | runs/stage3b2_smoke/slurm.log |
| stage3b2_smoke_a5000_resume1 | failed | stage3b2_smoke_a5000_resume1 | a5000 | 106544 | runs/stage3b2_smoke_resume1/slurm.log |
| stage3b2_smoke_eagerfix_a5000 | succeeded | stage3b2_smoke_eagerfix_a5000 | a5000 | 106545 | runs/stage3b2_smoke_eagerfix/slurm.log |
| stage3b2_cohort_00_a5000 | succeeded | stage3b2_cohort_00_a5000 | a5000 | 106546 | runs/stage3b2_cohort/cohort_00/slurm.log |
| stage3b2_cohort_01_a5000 | succeeded | stage3b2_cohort_01_a5000 | a5000 | 106547 | runs/stage3b2_cohort/cohort_01/slurm.log |
| stage3b2_cohort_02_a5000 | succeeded | stage3b2_cohort_02_a5000 | a5000 | 106548 | runs/stage3b2_cohort/cohort_02/slurm.log |
| stage3b2_cohort_03_a5000 | succeeded | stage3b2_cohort_03_a5000 | a5000 | 106549 | runs/stage3b2_cohort/cohort_03/slurm.log |
| stage3b2_cohort_04_a5000 | succeeded | stage3b2_cohort_04_a5000 | a5000 | 106550 | runs/stage3b2_cohort/cohort_04/slurm.log |
| stage3b2_cohort_05_a5000 | succeeded | stage3b2_cohort_05_a5000 | a5000 | 106551 | runs/stage3b2_cohort/cohort_05/slurm.log |
| stage3b2_cohort_06_a5000 | succeeded | stage3b2_cohort_06_a5000 | a5000 | 106552 | runs/stage3b2_cohort/cohort_06/slurm.log |
| stage3b2_rollout_00_a5000 | succeeded | stage3b2_rollout_00_a5000 | a5000 | 106553 | runs/stage3b2_rollouts/cohort_00/slurm.log |
| stage3b2_rollout_01_a5000 | succeeded | stage3b2_rollout_01_a5000 | a5000 | 106554 | runs/stage3b2_rollouts/cohort_01/slurm.log |
| stage3b2_rollout_02_a5000 | succeeded | stage3b2_rollout_02_a5000 | a5000 | 106555 | runs/stage3b2_rollouts/cohort_02/slurm.log |
| stage3b2_rollout_03_a5000 | succeeded | stage3b2_rollout_03_a5000 | a5000 | 106556 | runs/stage3b2_rollouts/cohort_03/slurm.log |
| stage3b2_rollout_04_a5000 | succeeded | stage3b2_rollout_04_a5000 | a5000 | 106557 | runs/stage3b2_rollouts/cohort_04/slurm.log |
| stage3b2_rollout_05_a5000 | succeeded | stage3b2_rollout_05_a5000 | a5000 | 106558 | runs/stage3b2_rollouts/cohort_05/slurm.log |
| stage3b2_rollout_06_a5000 | succeeded | stage3b2_rollout_06_a5000 | a5000 | 106559 | runs/stage3b2_rollouts/cohort_06/slurm.log |
| stage3b3_smoke_a5000 | failed | stage3b3_smoke_a5000 | a5000 | 106613 | runs/stage3b3_smoke_a5000/slurm.log |
| stage3b3_smoke_a5000_retry1 | succeeded | stage3b3_smoke_a5000 | a5000 | 106614 | runs/stage3b3_smoke_a5000_retry1/slurm.log |
| visual_reasoning_stage3b3r_validation_00 | cancelled | visual_reasoning_stage3b3r_validation_00 | a5000 | 106640 | runs/visual_reasoning_stage3b3r_validation_00/slurm.log |
| visual_reasoning_stage3b3r_validation_01 | succeeded | visual_reasoning_stage3b3r_validation_01 | a5000 | 106641 | runs/visual_reasoning_stage3b3r_validation_01/slurm.log |
| visual_reasoning_stage3b3r_validation_02 | succeeded | visual_reasoning_stage3b3r_validation_02 | a5000 | 106642 | runs/visual_reasoning_stage3b3r_validation_02/slurm.log |
| visual_reasoning_stage3b3r_validation_03 | succeeded | visual_reasoning_stage3b3r_validation_03 | a5000 | 106643 | runs/visual_reasoning_stage3b3r_validation_03/slurm.log |
| visual_reasoning_stage3b3r_validation_04 | succeeded | visual_reasoning_stage3b3r_validation_04 | a5000 | 106644 | runs/visual_reasoning_stage3b3r_validation_04/slurm.log |
| visual_reasoning_stage3b3r_validation_05 | succeeded | visual_reasoning_stage3b3r_validation_05 | a5000 | 106645 | runs/visual_reasoning_stage3b3r_validation_05/slurm.log |
| visual_reasoning_stage3b3r_validation_06 | succeeded | visual_reasoning_stage3b3r_validation_06 | a5000 | 106646 | runs/visual_reasoning_stage3b3r_validation_06/slurm.log |
| visual_reasoning_stage3b3r_validation_07 | succeeded | visual_reasoning_stage3b3r_validation_07 | a5000 | 106647 | runs/visual_reasoning_stage3b3r_validation_07/slurm.log |
| visual_reasoning_stage3b3r_hardware_a6000 | succeeded | visual_reasoning_stage3b3r_hardware_a6000 | a6000 | 106648 | runs/visual_reasoning_stage3b3r_hardware_a6000/slurm.log |
| visual_reasoning_stage3b3r_validation_00_retry | succeeded | visual_reasoning_stage3b3r_validation_00 | a5000 | 106649 | runs/visual_reasoning_stage3b3r_validation_00_retry/slurm.log |
| visual_reasoning_stage3b3r_primary_00 | succeeded | visual_reasoning_stage3b3r_primary_00 | a5000 | 106693 | runs/visual_reasoning_stage3b3r_primary_00/slurm.log |
| visual_reasoning_stage3b3r_primary_01 | succeeded | visual_reasoning_stage3b3r_primary_01 | a5000 | 106694 | runs/visual_reasoning_stage3b3r_primary_01/slurm.log |
| visual_reasoning_stage3b3r_primary_02 | succeeded | visual_reasoning_stage3b3r_primary_02 | a5000 | 106695 | runs/visual_reasoning_stage3b3r_primary_02/slurm.log |
| visual_reasoning_stage3b3r_primary_03 | succeeded | visual_reasoning_stage3b3r_primary_03 | a5000 | 106696 | runs/visual_reasoning_stage3b3r_primary_03/slurm.log |
| visual_reasoning_stage3b3r_primary_04 | succeeded | visual_reasoning_stage3b3r_primary_04 | a5000 | 106697 | runs/visual_reasoning_stage3b3r_primary_04/slurm.log |
| visual_reasoning_stage3b3r_primary_05 | succeeded | visual_reasoning_stage3b3r_primary_05 | a5000 | 106698 | runs/visual_reasoning_stage3b3r_primary_05/slurm.log |
| visual_reasoning_stage3b3r_primary_06 | succeeded | visual_reasoning_stage3b3r_primary_06 | a5000 | 106699 | runs/visual_reasoning_stage3b3r_primary_06/slurm.log |
| visual_reasoning_stage3b3r_primary_07 | succeeded | visual_reasoning_stage3b3r_primary_07 | a5000 | 106725 | runs/visual_reasoning_stage3b3r_primary_07/slurm.log |
| visual_reasoning_stage3b3r_node03_check | succeeded | visual_reasoning_stage3b3r_node03_check | a6000 | 106723 | runs/visual_reasoning_stage3b3r_node03_check/slurm.log |
| visual_reasoning_stage3b3r_fine_00 | succeeded | visual_reasoning_stage3b3r_fine_00 | a5000 | 106809 | runs/visual_reasoning_stage3b3r_fine_00/slurm.log |
| visual_reasoning_stage3b3r_fine_01 | succeeded | visual_reasoning_stage3b3r_fine_01 | a5000 | 106810 | runs/visual_reasoning_stage3b3r_fine_01/slurm.log |
| visual_reasoning_stage3b3r_fine_02 | succeeded | visual_reasoning_stage3b3r_fine_02 | a5000 | 106811 | runs/visual_reasoning_stage3b3r_fine_02/slurm.log |
| visual_reasoning_stage3b3r_fine_03 | succeeded | visual_reasoning_stage3b3r_fine_03 | a5000 | 106812 | runs/visual_reasoning_stage3b3r_fine_03/slurm.log |
| visual_reasoning_stage3b3r_fine_04 | succeeded | visual_reasoning_stage3b3r_fine_04 | a5000 | 106813 | runs/visual_reasoning_stage3b3r_fine_04/slurm.log |
| visual_reasoning_stage3b3r_fine_05 | succeeded | visual_reasoning_stage3b3r_fine_05 | a5000 | 106814 | runs/visual_reasoning_stage3b3r_fine_05/slurm.log |
| visual_reasoning_stage3b3r_fine_06 | succeeded | visual_reasoning_stage3b3r_fine_06 | a5000 | 106815 | runs/visual_reasoning_stage3b3r_fine_06/slurm.log |
| visual_reasoning_stage3b3r_fine_07 | succeeded | visual_reasoning_stage3b3r_fine_07 | a5000 | 106816 | runs/visual_reasoning_stage3b3r_fine_07/slurm.log |
| visual_reasoning_stage3b4_validation_00 | succeeded | visual_reasoning_stage3b4_validation_00 | a5000 | 106823 | runs/visual_reasoning_stage3b4_validation_00/slurm.log |
| visual_reasoning_stage3b4_validation_01 | succeeded | visual_reasoning_stage3b4_validation_01 | a5000 | 106824 | runs/visual_reasoning_stage3b4_validation_01/slurm.log |
| visual_reasoning_stage3b4_validation_02 | succeeded | visual_reasoning_stage3b4_validation_02 | a5000 | 106825 | runs/visual_reasoning_stage3b4_validation_02/slurm.log |
| visual_reasoning_stage3b4_validation_03 | succeeded | visual_reasoning_stage3b4_validation_03 | a5000 | 106826 | runs/visual_reasoning_stage3b4_validation_03/slurm.log |
| visual_reasoning_stage3b4_validation_04 | succeeded | visual_reasoning_stage3b4_validation_04 | a5000 | 106827 | runs/visual_reasoning_stage3b4_validation_04/slurm.log |
| visual_reasoning_stage3b4_validation_05 | succeeded | visual_reasoning_stage3b4_validation_05 | a5000 | 106828 | runs/visual_reasoning_stage3b4_validation_05/slurm.log |
| visual_reasoning_stage3b4_validation_06 | succeeded | visual_reasoning_stage3b4_validation_06 | a5000 | 106829 | runs/visual_reasoning_stage3b4_validation_06/slurm.log |
| visual_reasoning_stage3b4_validation_07 | succeeded | visual_reasoning_stage3b4_validation_07 | a5000 | 106830 | runs/visual_reasoning_stage3b4_validation_07/slurm.log |
| visual_reasoning_stage3b4_primary_00 | succeeded | visual_reasoning_stage3b4_primary_00 | a5000 | 106831 | runs/visual_reasoning_stage3b4_primary_00/slurm.log |
| visual_reasoning_stage3b4_primary_01 | succeeded | visual_reasoning_stage3b4_primary_01 | a5000 | 106832 | runs/visual_reasoning_stage3b4_primary_01/slurm.log |
| visual_reasoning_stage3b4_primary_02 | succeeded | visual_reasoning_stage3b4_primary_02 | a5000 | 106833 | runs/visual_reasoning_stage3b4_primary_02/slurm.log |
| visual_reasoning_stage3b4_primary_03 | succeeded | visual_reasoning_stage3b4_primary_03 | a5000 | 106834 | runs/visual_reasoning_stage3b4_primary_03/slurm.log |
| visual_reasoning_stage3b4_primary_04 | succeeded | visual_reasoning_stage3b4_primary_04 | a5000 | 106835 | runs/visual_reasoning_stage3b4_primary_04/slurm.log |
| visual_reasoning_stage3b4_primary_05 | succeeded | visual_reasoning_stage3b4_primary_05 | a5000 | 106836 | runs/visual_reasoning_stage3b4_primary_05/slurm.log |
| visual_reasoning_stage3b4_primary_06 | succeeded | visual_reasoning_stage3b4_primary_06 | a5000 | 106837 | runs/visual_reasoning_stage3b4_primary_06/slurm.log |
| visual_reasoning_stage3b4_primary_07 | succeeded | visual_reasoning_stage3b4_primary_07 | a5000 | 106838 | runs/visual_reasoning_stage3b4_primary_07/slurm.log |
| visual_reasoning_stage3b5_validation_00 | succeeded | visual_reasoning_stage3b5_validation_00 | a5000 | 106912 | runs/visual_reasoning_stage3b5_validation_00/slurm.log |
| visual_reasoning_stage3b5_validation_01 | succeeded | visual_reasoning_stage3b5_validation_01 | a5000 | 106913 | runs/visual_reasoning_stage3b5_validation_01/slurm.log |
| visual_reasoning_stage3b5_validation_02 | succeeded | visual_reasoning_stage3b5_validation_02 | a5000 | 106914 | runs/visual_reasoning_stage3b5_validation_02/slurm.log |
| visual_reasoning_stage3b5_validation_03 | succeeded | visual_reasoning_stage3b5_validation_03 | a5000 | 106915 | runs/visual_reasoning_stage3b5_validation_03/slurm.log |
| visual_reasoning_stage3b5_validation_04 | succeeded | visual_reasoning_stage3b5_validation_04 | a5000 | 106916 | runs/visual_reasoning_stage3b5_validation_04/slurm.log |
| visual_reasoning_stage3b5_validation_05 | succeeded | visual_reasoning_stage3b5_validation_05 | a5000 | 106917 | runs/visual_reasoning_stage3b5_validation_05/slurm.log |
| visual_reasoning_stage3b5_validation_06 | succeeded | visual_reasoning_stage3b5_validation_06 | a5000 | 106918 | runs/visual_reasoning_stage3b5_validation_06/slurm.log |
| visual_reasoning_stage3b5_validation_07 | succeeded | visual_reasoning_stage3b5_validation_07 | a5000 | 106919 | runs/visual_reasoning_stage3b5_validation_07/slurm.log |
| visual_reasoning_stage3b5_primary_00 | succeeded | visual_reasoning_stage3b5_primary_00 | a5000 | 106923 | runs/visual_reasoning_stage3b5_primary_00/slurm.log |
| visual_reasoning_stage3b5_primary_01 | succeeded | visual_reasoning_stage3b5_primary_01 | a5000 | 106924 | runs/visual_reasoning_stage3b5_primary_01/slurm.log |
| visual_reasoning_stage3b5_primary_02 | succeeded | visual_reasoning_stage3b5_primary_02 | a5000 | 106925 | runs/visual_reasoning_stage3b5_primary_02/slurm.log |
| visual_reasoning_stage3b5_primary_03 | succeeded | visual_reasoning_stage3b5_primary_03 | a5000 | 106926 | runs/visual_reasoning_stage3b5_primary_03/slurm.log |
| visual_reasoning_stage3b5_primary_04 | succeeded | visual_reasoning_stage3b5_primary_04 | a5000 | 106927 | runs/visual_reasoning_stage3b5_primary_04/slurm.log |
| visual_reasoning_stage3b5_primary_05 | succeeded | visual_reasoning_stage3b5_primary_05 | a5000 | 106928 | runs/visual_reasoning_stage3b5_primary_05/slurm.log |
| visual_reasoning_stage3b5_primary_06 | succeeded | visual_reasoning_stage3b5_primary_06 | a5000 | 106929 | runs/visual_reasoning_stage3b5_primary_06/slurm.log |
| visual_reasoning_stage3b5_primary_07 | succeeded | visual_reasoning_stage3b5_primary_07 | a5000 | 106930 | runs/visual_reasoning_stage3b5_primary_07/slurm.log |
| visual_reasoning_stage3b6_tmux8 | succeeded | visual_reasoning_stage3b6 | a5000 |  | runs/stage3b6_tmux/pipeline.log |
| visual_reasoning_stage3b7_tmux8 | failed | visual_reasoning_stage3b7 | a5000 |  | runs/stage3b7_tmux/pipeline.log |
| visual_reasoning_stage3b7r_tmux8 | succeeded | visual_reasoning_stage3b7r | a5000 |  | runs/stage3b7r_tmux/generation.log |
| visual_reasoning_stage3b8_tmux8 | succeeded | visual_reasoning_stage3b8 | a5000 |  | runs/stage3b8_tmux/pipeline.log |
| visual_reasoning_stage3b9_generation_tmux8 | succeeded | visual_reasoning_stage3b9_generation | a5000 |  | runs/stage3b9_tmux/prospective_generation.log |
| visual_reasoning_stage3b9_phase_a_full_tmux8 | succeeded | visual_reasoning_stage3b9_phase_a_full | a5000 |  | runs/stage3b9_tmux/phase_a_full.log |
| visual_reasoning_stage3b9_applicability_expansion_generation_tmux8 | succeeded | visual_reasoning_stage3b9_applicability_expansion_generation | a5000 |  | runs/stage3b9_tmux/applicability_expansion_generation.log |
| visual_reasoning_stage3b9_phase_b_full | succeeded | visual_reasoning_stage3b9_phase_b_full | a5000 | 107178 | runs/stage3b9_slurm/phase_b_full_slurm.log |
| visual_reasoning_stage3b9_phase_b_projected | running | visual_reasoning_stage3b9_phase_b_projected | a5000 | 107179 | runs/stage3b9_slurm/phase_b_projected_slurm.log |
| visual_reasoning_stage3b9_phase_a_full_expansion_tmux8 | succeeded | visual_reasoning_stage3b9_phase_a_full_expansion | a5000 |  | runs/stage3b9_tmux/phase_a_full_expansion.log |
| visual_reasoning_stage3b9_phase_a_learned_tmux8 | succeeded | visual_reasoning_stage3b9_phase_a_learned | a5000 |  | runs/stage3b9_tmux/phase_a_learned.log |
| visual_reasoning_stage3b9_phase_a_random_tmux8 | running | visual_reasoning_stage3b9_phase_a_random | a5000 |  | runs/stage3b9_tmux/phase_a_random.log |
| visual_reasoning_stage3c1_smoke_tmux8 | failed | visual_reasoning_stage3c1 | a5000 |  | runs/stage3c1_tmux/smoke.log |
| visual_reasoning_stage3c1_smoke_v2_tmux8 | failed | visual_reasoning_stage3c1 | a5000 |  | runs/stage3c1_tmux/smoke_v2.log |
| visual_reasoning_stage3c1_smoke_v3_tmux8 | succeeded | visual_reasoning_stage3c1 | a5000 |  | runs/stage3c1_tmux/smoke_v3.log |
| visual_reasoning_stage3c1_full_tmux8 | succeeded | visual_reasoning_stage3c1 | a5000 |  | runs/stage3c1_tmux/full.log |
| stage3c2_passive_smoke | succeeded | stage3c2_passive_smoke | a5000 |  | runs/stage3c2_passive_smoke/tmux.log |
| stage3c2_passive_full | succeeded | stage3c2_passive_full | a5000 |  | runs/stage3c2_passive_full/tmux.log |
| stage3c3_query_validation_smoke | failed | stage3c3_q_validation_smoke | a5000 |  | runs/stage3c3/validation_smoke.log |
| stage3c3_query_validation_smoke_v2 | failed | stage3c3_q_validation_smoke_v2 | a5000 |  | runs/stage3c3/validation_smoke.log |
| stage3c3_query_validation_smoke_v3 | succeeded | stage3c3_q_validation_smoke_v3 | a5000 |  | runs/stage3c3/validation_smoke.log |
| stage3c3_query_validation_full | failed | stage3c3_q_validation | a5000 |  | runs/stage3c3/validation.log |
| stage3c3_query_validation_resume | succeeded | stage3c3_q_validation_resume | a5000 |  | runs/stage3c3/validation.log |
| stage3c3_phase_a_primary | succeeded | stage3c3_phase_a | a5000 |  | runs/stage3c3/primary_query.log |
| visual_reasoning_stage3c3r_validation_smoke_tmux8 | failed | visual_reasoning_stage3c3r_validation_smoke | a5000 |  | runs/stage3c3r_tmux/validation_smoke.log |
| visual_reasoning_stage3c3r_validation_smoke_v2_tmux8 | succeeded | visual_reasoning_stage3c3r_validation_smoke_v2 | a5000 |  | runs/stage3c3r_tmux/validation_smoke_v2.log |
| visual_reasoning_stage3c3r_validation_tmux8 | succeeded | visual_reasoning_stage3c3r_validation | a5000 |  | runs/stage3c3r_tmux/validation.log |
| visual_reasoning_stage3c3r_phase_a_tmux8 | succeeded | visual_reasoning_stage3c3r_phase_a | a5000 |  | runs/stage3c3r_tmux/phase_a.log |
| visual_reasoning_stage3c3r_phase_b_tmux8 | succeeded | visual_reasoning_stage3c3r_phase_b | a5000 |  | runs/stage3c3r_tmux/phase_b.log |
| visual_reasoning_stage3c3r_resource_smoke_tmux8 | succeeded | visual_reasoning_stage3c3r_resource_smoke | a5000 |  | runs/stage3c3r_tmux/resource_smoke.log |
| visual_reasoning_stage3c4_validation_smoke_tmux8 | succeeded | visual_reasoning_stage3c4_validation_smoke | a5000 |  | runs/stage3c4_tmux/validation_smoke.log |
| visual_reasoning_stage3c4_validation_tmux8 | succeeded | visual_reasoning_stage3c4_validation | a5000 |  | runs/stage3c4_tmux/validation.log |
| visual_reasoning_stage3c4_phase_a_tmux8 | succeeded | visual_reasoning_stage3c4_phase_a | a5000 |  | runs/stage3c4_tmux/phase_a.log |
| visual_reasoning_stage3c4_phase_b_tmux8 | succeeded | visual_reasoning_stage3c4_phase_b | a5000 |  | runs/stage3c4_tmux/phase_b.log |
| visual_reasoning_stage3c4_phase_c_tmux8 | succeeded | visual_reasoning_stage3c4_phase_c | a5000 |  | runs/stage3c4_tmux/phase_c.log |
| visual_reasoning_stage3c5_phase_a_smoke_tmux8 | succeeded | visual_reasoning_stage3c5_phase_a_smoke | a5000 |  | runs/stage3c5_tmux/phase_a_smoke.log |
| visual_reasoning_stage3c5_phase_a_validation_tmux8 | succeeded | visual_reasoning_stage3c5_phase_a_validation | a5000 |  | runs/stage3c5_tmux/phase_a_validation.log |
| visual_reasoning_stage3c5_phase_a_tmux8 | succeeded | visual_reasoning_stage3c5_phase_a | a5000 |  | runs/stage3c5_tmux/phase_a.log |
| visual_reasoning_stage3c5_phase_b_smoke_tmux8 | succeeded | visual_reasoning_stage3c5_phase_b_smoke | a5000 |  | runs/stage3c5_tmux/phase_b_smoke.log |
| visual_reasoning_stage3c5_phase_b_validation_tmux8 | succeeded | visual_reasoning_stage3c5_phase_b_validation | a5000 |  | runs/stage3c5_tmux/phase_b_validation.log |
| visual_reasoning_stage3c5_phase_b_tmux8 | succeeded | visual_reasoning_stage3c5_phase_b | a5000 |  | runs/stage3c5_tmux/phase_b.log |
| visual_reasoning_stage3c5_phase_b_gated_r_tmux8 | succeeded | visual_reasoning_stage3c5_phase_b_gated_r | a5000 |  | runs/stage3c5_tmux/phase_b_gated_r.log |
| visual_reasoning_stage3c5_controls_tmux8 | succeeded | visual_reasoning_stage3c5_controls | a5000 |  | runs/stage3c5_tmux/controls.log |
| visual_reasoning_stage3c6_phase_a_smoke_tmux8 | succeeded | visual_reasoning_stage3c6_phase_a_smoke | a5000 |  | runs/stage3c6_tmux/phase_a_smoke.log |
| visual_reasoning_stage3c6_phase_a_validation_tmux8 | failed | visual_reasoning_stage3c6_phase_a_validation | a5000 |  | runs/stage3c6_tmux/phase_a_validation.log |
| visual_reasoning_stage3c6_phase_a_validation_v2_tmux8 | succeeded | visual_reasoning_stage3c6_phase_a_validation_v2 | a5000 |  | runs/stage3c6_tmux/phase_a_validation_v2.log |
| visual_reasoning_stage3c6_past_kv_audit_tmux8 | succeeded | visual_reasoning_stage3c6_past_kv_audit | a5000 |  | runs/stage3c6_tmux/past_kv_audit.log |
| visual_reasoning_stage3c6_phase_a_tmux8 | succeeded | visual_reasoning_stage3c6_phase_a | a5000 |  | runs/stage3c6_tmux/phase_a.log |
| visual_reasoning_stage3c6_phase_b_validation_tmux8 | succeeded | visual_reasoning_stage3c6_phase_b_validation | a5000 |  | runs/stage3c6_tmux/phase_b_validation.log |
| visual_reasoning_stage3c6_phase_b_boundary_tmux8 | succeeded | visual_reasoning_stage3c6_phase_b_boundary | a5000 |  | runs/stage3c6_tmux/phase_b_boundary.log |
| visual_reasoning_stage3c6_dose_tmux8 | succeeded | visual_reasoning_stage3c6_dose | a5000 |  | runs/stage3c6_tmux/dose.log |
| visual_reasoning_stage3c6_controls_tmux8 | succeeded | visual_reasoning_stage3c6_controls | a5000 |  | runs/stage3c6_tmux/controls.log |
| visual_reasoning_stage3c7_validation_smoke_tmux8 | failed | visual_reasoning_stage3c7_validation_smoke | a5000 |  | runs/stage3c7_tmux/validation_smoke.log |
| visual_reasoning_stage3c7_validation_smoke_v2_tmux8 | succeeded | visual_reasoning_stage3c7_validation_smoke_v2 | a5000 |  | runs/stage3c7_tmux/validation_smoke_v2.log |
| visual_reasoning_stage3c7_validation_tmux8 | succeeded | visual_reasoning_stage3c7_validation | a5000 |  | runs/stage3c7_tmux/validation.log |
| visual_reasoning_stage3c7_primary_tmux8 | succeeded | visual_reasoning_stage3c7_primary | a5000 |  | runs/stage3c7_tmux/primary.log |
| visual_reasoning_stage3c7_joint_kv_validation_tmux8 | succeeded | visual_reasoning_stage3c7_joint_kv_validation | a5000 |  | runs/stage3c7_tmux/joint_kv_validation.log |
| visual_reasoning_stage3c7_joint_kv_primary_tmux8 | succeeded | visual_reasoning_stage3c7_joint_kv_primary | a5000 |  | runs/stage3c7_tmux/joint_kv_primary.log |
| visual_reasoning_stage3c8_generation_00_tmux8 | succeeded | visual_reasoning_stage3c8_generation_00 | a5000 |  | runs/stage3c8_tmux/generation_00.log |
| visual_reasoning_stage3c8_generation_01_tmux8 | failed | visual_reasoning_stage3c8_generation_01 | a5000 |  | runs/stage3c8_tmux/generation_01.log |
| visual_reasoning_stage3c8_generation_resume | cancelled | visual_reasoning_stage3c8_generation_resume | a5000 | 107836 | runs/stage3c8_slurm/generation_resume.log |
| visual_reasoning_stage3c8_generation_01_repair | succeeded | visual_reasoning_stage3c8_generation_01_repair | a5000 |  | runs/stage3c8_tmux/generation_01_repair.log |
| visual_reasoning_stage3c8_generation_resume2 | cancelled | visual_reasoning_stage3c8_generation_resume2 | a5000 | 107965 | runs/stage3c8_slurm/generation_resume2.log |
| visual_reasoning_stage3c8_tmux_107969 | succeeded | visual_reasoning_stage3c8_generation_resume | a5000 |  | runs/stage3c8_tmux/generation_resume_107969.log |
| visual_reasoning_stage3c9_initial_generation_tmux8 | running | visual_reasoning_stage3c9_initial_generation | a5000 |  | runs/stage3c9_tmux/initial_generation_108041.log |
| stage3c9r_validation_tmux9_108548 | succeeded | stage3c9r_validation | a6000 |  | runs/stage3c9r_validation_108548.log |
| stage3c9r_primary_tmux9_108548 | succeeded | stage3c9r_primary | a6000 |  | runs/stage3c9r_primary_108548.log |
| stage3c9r_followups_tmux9_108548 | succeeded | stage3c9r_followups | a6000 |  | runs/stage3c9r_followups_108548.log |
| stage3c10_validation_tmux9_108548 | succeeded | stage3c10_validation | a6000 |  | runs/stage3c10_validation_108548.log |
| stage3c10_primary_tmux9_108548 | succeeded | stage3c10_primary | a6000 |  | runs/stage3c10_primary_108548.log |
| stage3c10_followups_tmux9_108548 | succeeded | stage3c10_followups | a6000 |  | runs/stage3c10_followups_108548.log |
| stage4a_generation_tmux9_108548 | succeeded | stage4a_generation | a6000 |  | runs/stage4a_generation_108548.log |
| stage4a_validation_tmux9_108548_01 | succeeded | stage4a_validation_01 | a6000 |  | runs/stage4a_validation_01_108548.log |
| stage4a_primary_tmux9_108548_01 | succeeded | stage4a_primary_01 | a6000 |  | runs/stage4a_primary_01_108548.log |
| stage4a_trigger_tmux9_108548_01 | succeeded | stage4a_trigger_01 | a6000 |  | runs/stage4a_trigger_01_108548.log |
| stage4a_semantic_tmux9_108548_01 | succeeded | stage4a_semantic_01 | a6000 |  | runs/stage4a_semantic_01_108548.log |
| stage5a_generation_tmux9_108548 | succeeded | stage5a_generation_initial | a6000 | 108548 | runs/stage5a_generation_108548.log |
| stage5a_validation_01_tmux9_108548 | succeeded | stage5a_validation_01 | a6000 | 108548 | runs/stage5a_validation_01_108548.log |
| stage5a_causal_01_tmux9_108548 | succeeded | stage5a_causal_01 | a6000 | 108548 | runs/stage5a_causal_01_108548.log |
| stage5a_semantic_01_tmux9_108548 | succeeded | stage5a_semantic_01 | a6000 | 108548 | runs/stage5a_semantic_01_108548.log |
| stage5a_passive_01_tmux9_108548 | succeeded | stage5a_passive_01 | a6000 | 108548 | runs/stage5a_passive_01_108548.log |
| stage6a_mechanics | failed | stage6a_mechanics | a6000 | 109385 | runs/stage6a/mechanics.log |
| stage6a_mechanics_v2 | succeeded | stage6a_mechanics_v2 | a6000 | 109385 | runs/stage6a/mechanics_v2.log |
| stage6a_pilot | succeeded | stage6a_pilot | a6000 | 109385 | runs/stage6a/pilot.log |
| stage6a_c4_primary | succeeded | stage6a_c4_primary | a6000 | 109385 | runs/stage6a/c4_primary.log |
| stage6a_c1_stimuli | succeeded | stage6a_c1_stimuli | auto | 109385 | runs/stage6a/c1_stimuli.log |
| stage6a_source_audit | succeeded | stage6a_source_audit | auto | 109385 | runs/stage6a/source_duplicates.log |
| stage6a_c1_final_stimuli | succeeded | stage6a_c1_final_stimuli | a6000 | 109385 | runs/stage6a/c1_final_stimuli.log |
| stage6a_c3_stimuli | succeeded | stage6a_c3_stimuli | a6000 | 109385 | runs/stage6a/c3_stimuli.log |
| stage6a_controlled_intact | succeeded | stage6a_controlled_intact | a6000 | 109385 | runs/stage6a/controlled_intact.log |
| stage6a_annotation_pipeline | succeeded | stage6a_annotation_pipeline | a6000 | 109385 | runs/stage6a/controlled_trace_collection.log |
| stage6a_c4_extension | succeeded | stage6a_c4_extension | a6000 | 109385 | runs/stage6a/c4_extension.log |
| stage6a_c3_stress | succeeded | stage6a_c3_stress | a6000 | 109385 | runs/stage6a/c3_stress.log |
| stage6a_c1_stress | succeeded | stage6a_c1_stress | a6000 | 109385 | runs/stage6a/controlled_stress.log |
| stage6b_c2_mechanics_01 | succeeded | stage6b_c2_mechanics_01 | a6000 | 110860 | runs/stage6b/c2_mechanics_01.log |
| stage6b_c2_discovery_01 | succeeded | stage6b_c2_discovery_01 | a6000 | 110860 | runs/stage6b/c2_discovery_01.log |
| stage6b_c2_confirmation_01 | succeeded | stage6b_c2_confirmation_01 | a6000 | 110860 | runs/stage6b/c2_confirmation_01.log |
| stage6b_c1_mechanics_01 | failed | stage6b_c1_mechanics_01 | a6000 | 110860 | runs/stage6b/c1_mechanics_01.log |
| stage6b_c1_mechanics_02 | succeeded | stage6b_c1_mechanics_02 | a6000 | 110860 | runs/stage6b/c1_mechanics_02.log |
| stage6b_c1_discovery_01 | succeeded | stage6b_c1_discovery_01 | a6000 | 110860 | runs/stage6b/c1_discovery_01.log |
| stage6b_c1_confirmation_01 | succeeded | stage6b_c1_confirmation_01 | a6000 | 110860 | runs/stage6b/c1_confirmation_01.log |
| stage6b_dynamics_mechanics_01 | succeeded | stage6b_dynamics_mechanics_01 | a6000 | 110860 | runs/stage6b/dynamics_mechanics_01.log |
| stage6b_dynamics_discovery_01 | succeeded | stage6b_dynamics_discovery_01 | a6000 | 110860 | runs/stage6b/dynamics_discovery_01.log |
| stage6b_dynamics_confirmation_01 | succeeded | stage6b_dynamics_confirmation_01 | a6000 | 110860 | runs/stage6b/dynamics_confirmation_01.log |
| stage6b_native_mechanics_01 | succeeded | stage6b_native_mechanics_01 | a6000 | 110860 | runs/stage6b/native_mechanics_01.log |
| stage6b_native_primary_01 | failed | stage6b_native_primary_01 | a6000 | 110860 | runs/stage6b/native_primary_01.log |
| stage6b_c3_mechanics_01 | succeeded | stage6b_c3_mechanics_01 | a6000 | 110860 | runs/stage6b/c3_mechanics_01.log |
| stage6b_native_residency_mechanics_01 | failed | stage6b_native_residency_mechanics_01 | a6000 | 110860 | runs/stage6b/native_residency_mechanics_01.log |
| stage6b_c3_discovery_01 | succeeded | stage6b_c3_discovery_01 | a6000 | 110860 | runs/stage6b/c3_discovery_01.log |
| stage6b_native_allocator_diagnostic_01 | succeeded | stage6b_native_allocator_diagnostic_01 | a6000 | 110860 | runs/stage6b/native_allocator_diagnostic_01.log |
| stage6b_native_residency_mechanics_02 | succeeded | stage6b_native_residency_mechanics_02 | a6000 | 110860 | runs/stage6b/native_residency_mechanics_02.log |
| stage6b_c3_confirmation_01 | succeeded | stage6b_c3_confirmation_01 | a6000 | 110860 | runs/stage6b/c3_confirmation_01.log |
| stage6b_c4_native_01 | succeeded | stage6b_c4_native_01 | a6000 | 110860 | runs/stage6b/c4_native_01.log |
| stage6b_native_primary_02 | succeeded | stage6b_native_primary_02 | a6000 | 110860 | runs/stage6b/native_primary_02.log |
| stage7a_mechanics_01 | succeeded | stage7a_mechanics_01 | a6000 | 111485 | runs/stage7a/mechanics_01.log |
| stage7a_objects_01 | succeeded | stage7a_objects_01 | a6000 | 111485 | runs/stage7a/objects_01.log |
| stage7a_generation_mechanics_01 | succeeded | stage7a_generation_mechanics_01 | a6000 | 111485 | runs/stage7a/generation_mechanics_01.log |
| stage7a_cohort_01 | succeeded | stage7a_cohort_01 | a6000 | 111485 | runs/stage7a/cohort_01.log |
| stage7a_native_01 | succeeded | stage7a_native_01 | a6000 | 111485 | runs/stage7a/native_01.log |
| stage7a_fresh_mechanics_01 | succeeded | stage7a_fresh_mechanics_01 | a6000 | 111485 | runs/stage7a/fresh_mechanics_01.log |
| stage7a_discovery_causal_01 | failed | stage7a_discovery_causal_01 | a6000 | 111485 | runs/stage7a/discovery_causal_01.log |
| stage7a_discovery_causal_02 | succeeded | stage7a_discovery_causal_02 | a6000 | 111485 | runs/stage7a/discovery_causal_02.log |
| stage7a_confirmation_causal_01 | succeeded | stage7a_confirmation_causal_01 | a6000 | 111485 | runs/stage7a/confirmation_causal_01.log |
| stage7a_discovery_passive_01 | succeeded | stage7a_discovery_passive_01 | a6000 | 111485 | runs/stage7a/discovery_passive_01.log |
| stage7a_confirmation_passive_01 | succeeded | stage7a_confirmation_passive_01 | a6000 | 111485 | runs/stage7a/confirmation_passive_01.log |
| stage7a_probes_01 | succeeded | stage7a_probes_01 | a6000 | 111485 | runs/stage7a/probes_01.log |
| stage7a_utilization_01 | succeeded | stage7a_utilization_01 | a6000 | 111485 | runs/stage7a/utilization_01.log |
| stage7a_bench_v2_phantom_native_01 | succeeded | stage7a_bench_v2_phantom_native_01 | a6000 | 111485 | runs/stage7a_bench/phantom_native_01.log |
| stage7a_bench_v2_charxiv_native_01 | succeeded | stage7a_bench_v2_charxiv_native_01 | a6000 | 111485 | runs/stage7a_bench/charxiv_native_01.log |
| stage7a_bench_v2_causal_charxiv_causal_mechanics_01 | succeeded | stage7a_bench_v2_causal_charxiv_causal_mechanics_01 | a6000 | 111485 | runs/stage7a_bench/charxiv_causal_mechanics_01.log |
| stage7a_bench_v2_causal_charxiv_causal_pilot_01 | succeeded | stage7a_bench_v2_causal_charxiv_causal_pilot_01 | a6000 | 111485 | runs/stage7a_bench/charxiv_causal_pilot_01.log |
| stage7a_bench_v2_mathvision_wild_native_01 | cancelled | stage7a_bench_v2_mathvision_wild_native_01 | a6000 | 111485 | runs/stage7a_bench/mathvision_wild_native_01.log |
| stage7a_bench_v3_mathvision_wild_native_02 | failed | stage7a_bench_v3_mathvision_wild_native_02 | a6000 | 113280 | runs/stage7a_bench/mathvision_wild_native_02_node02_v3.log |
| stage7a_bench_v3_mmmu_pro_native_01 | failed | stage7a_bench_v3_mmmu_pro_native_01 | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_native_01_node02_v3.log |
| stage7a_bench_v3_mathsight_native_01 | failed | stage7a_bench_v3_mathsight_native_01 | a6000 | 113280 | runs/stage7a_bench/mathsight_native_01_node02_v3.log |
| stage7a_bench_v3_microvqa_native_01 | cancelled | stage7a_bench_v3_microvqa_native_01 | a6000 |  | runs/stage7a_bench/microvqa_native_01_node02_v3.log |
| stage7a_bench_v3_medxpertqa_mm_native_01 | cancelled | stage7a_bench_v3_medxpertqa_mm_native_01 | a6000 |  | runs/stage7a_bench/medxpertqa_mm_native_01_node02_v3.log |
| stage7a_bench_v3_mmlongbench_doc_native_01 | cancelled | stage7a_bench_v3_mmlongbench_doc_native_01 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_native_01_node02_v3.log |
| stage7a_bench_v4_mathvision_wild_native_03 | cancelled | stage7a_bench_v4_mathvision_wild_native_03 | a6000 |  | runs/stage7a_bench/mathvision_wild_native_03_node02_v4.log |
| stage7a_bench_v4_mmmu_pro_native_02 | cancelled | stage7a_bench_v4_mmmu_pro_native_02 | a6000 |  | runs/stage7a_bench/mmmu_pro_native_02_node02_v4.log |
| stage7a_bench_v4_mathsight_native_02 | cancelled | stage7a_bench_v4_mathsight_native_02 | a6000 |  | runs/stage7a_bench/mathsight_native_02_node02_v4.log |
| stage7a_bench_v4_microvqa_native_02 | cancelled | stage7a_bench_v4_microvqa_native_02 | a6000 |  | runs/stage7a_bench/microvqa_native_02_node02_v4.log |
| stage7a_bench_v4_medxpertqa_mm_native_02 | cancelled | stage7a_bench_v4_medxpertqa_mm_native_02 | a6000 |  | runs/stage7a_bench/medxpertqa_mm_native_02_node02_v4.log |
| stage7a_bench_v4_mmlongbench_doc_native_02 | cancelled | stage7a_bench_v4_mmlongbench_doc_native_02 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_native_02_node02_v4.log |
| stage7a_bench_v5_mathwild_gate96_shard0_v5 | succeeded | stage7a_bench_v5_mathwild_gate96_shard0_v5 | a6000 | 113280 | runs/stage7a_bench/mathwild_gate96_shard0_v5.log |
| stage7a_bench_v5_mathwild_gate96_shard1_v5 | succeeded | stage7a_bench_v5_mathwild_gate96_shard1_v5 | a6000 | 113280 | runs/stage7a_bench/mathwild_gate96_shard1_v5.log |
| stage7a_bench_v5_mathwild_gate96_shard2_v5 | succeeded | stage7a_bench_v5_mathwild_gate96_shard2_v5 | a6000 | 113280 | runs/stage7a_bench/mathwild_gate96_shard2_v5.log |
| stage7a_bench_v5_mathwild_gate96_shard3_v5 | succeeded | stage7a_bench_v5_mathwild_gate96_shard3_v5 | a6000 | 113280 | runs/stage7a_bench/mathwild_gate96_shard3_v5.log |
| stage7a_bench_v6_mathwild_remainder_photo_00_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_00_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_00_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_01_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_01_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_01_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_02_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_02_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_02_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_03_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_03_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_03_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_04_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_04_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_04_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_05_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_05_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_05_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_06_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_06_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_06_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_07_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_07_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_07_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_08_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_08_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_08_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_09_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_09_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_09_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_10_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_10_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_10_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_11_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_11_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_11_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_12_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_12_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_12_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_13_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_13_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_13_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_14_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_14_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_14_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_15_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_15_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_15_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_16_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_16_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_16_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_17_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_17_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_17_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_18_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_18_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_18_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_19_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_19_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_19_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_20_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_20_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_20_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_21_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_21_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_21_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_22_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_22_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_22_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_23_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_23_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_23_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_24_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_24_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_24_v6.log |
| stage7a_bench_v6_mathwild_remainder_photo_25_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_photo_25_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_photo_25_v6.log |
| stage7a_bench_v6_mathwild_remainder_screenshot_00_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_screenshot_00_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_screenshot_00_v6.log |
| stage7a_bench_v6_mathwild_remainder_screenshot_01_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_screenshot_01_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_screenshot_01_v6.log |
| stage7a_bench_v6_mathwild_remainder_screenshot_02_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_screenshot_02_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_screenshot_02_v6.log |
| stage7a_bench_v6_mathwild_remainder_screenshot_03_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_screenshot_03_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_screenshot_03_v6.log |
| stage7a_bench_v6_mathwild_remainder_screenshot_04_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_screenshot_04_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_screenshot_04_v6.log |
| stage7a_bench_v6_mathwild_remainder_screenshot_05_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_screenshot_05_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_screenshot_05_v6.log |
| stage7a_bench_v6_mathwild_remainder_screenshot_06_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_screenshot_06_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_screenshot_06_v6.log |
| stage7a_bench_v6_mathwild_remainder_screenshot_07_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_screenshot_07_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_screenshot_07_v6.log |
| stage7a_bench_v6_mathwild_remainder_screenshot_08_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_screenshot_08_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_screenshot_08_v6.log |
| stage7a_bench_v6_mathwild_remainder_screenshot_09_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_screenshot_09_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_screenshot_09_v6.log |
| stage7a_bench_v6_mathwild_remainder_screenshot_10_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_screenshot_10_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_screenshot_10_v6.log |
| stage7a_bench_v6_mathwild_remainder_screenshot_11_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_screenshot_11_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_screenshot_11_v6.log |
| stage7a_bench_v6_mathwild_remainder_screenshot_12_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_screenshot_12_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_screenshot_12_v6.log |
| stage7a_bench_v6_mathwild_remainder_screenshot_13_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_screenshot_13_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_screenshot_13_v6.log |
| stage7a_bench_v6_mathwild_remainder_screenshot_14_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_screenshot_14_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_screenshot_14_v6.log |
| stage7a_bench_v6_mathwild_remainder_screenshot_15_v6 | succeeded | stage7a_bench_v6_mathwild_remainder_screenshot_15_v6 | a6000 | 113280 | runs/stage7a_bench/mathwild_remainder_screenshot_15_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_00_v6 | failed | stage7a_bench_v6_mmmu_pro_image_present_00_v6 | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_00_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_01_v6 | failed | stage7a_bench_v6_mmmu_pro_image_present_01_v6 | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_01_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_02_v6 | failed | stage7a_bench_v6_mmmu_pro_image_present_02_v6 | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_02_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_03_v6 | failed | stage7a_bench_v6_mmmu_pro_image_present_03_v6 | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_03_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_04_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_04_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_04_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_05_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_05_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_05_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_06_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_06_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_06_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_07_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_07_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_07_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_08_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_08_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_08_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_09_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_09_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_09_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_10_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_10_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_10_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_11_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_11_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_11_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_12_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_12_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_12_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_13_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_13_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_13_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_14_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_14_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_14_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_15_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_15_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_15_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_16_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_16_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_16_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_17_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_17_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_17_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_18_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_18_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_18_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_19_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_19_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_19_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_20_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_20_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_20_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_21_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_21_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_21_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_22_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_22_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_22_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_23_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_23_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_23_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_24_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_24_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_24_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_25_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_25_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_25_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_26_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_26_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_26_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_27_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_27_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_27_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_28_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_28_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_28_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_29_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_29_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_29_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_30_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_30_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_30_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_31_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_31_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_31_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_32_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_32_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_32_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_33_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_33_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_33_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_34_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_34_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_34_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_35_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_35_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_35_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_36_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_36_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_36_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_37_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_37_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_37_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_38_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_38_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_38_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_39_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_39_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_39_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_40_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_40_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_40_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_41_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_41_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_41_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_42_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_42_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_42_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_43_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_43_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_43_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_44_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_44_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_44_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_45_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_45_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_45_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_46_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_46_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_46_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_47_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_47_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_47_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_48_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_48_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_48_v6.log |
| stage7a_bench_v6_mmmu_pro_image_present_49_v6 | cancelled | stage7a_bench_v6_mmmu_pro_image_present_49_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_image_present_49_v6.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_00_v6 | cancelled | stage7a_bench_v6_mmmu_pro_silent_no_image_00_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_silent_no_image_00_v6.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_01_v6 | cancelled | stage7a_bench_v6_mmmu_pro_silent_no_image_01_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_silent_no_image_01_v6.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_02_v6 | cancelled | stage7a_bench_v6_mmmu_pro_silent_no_image_02_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_silent_no_image_02_v6.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_03_v6 | cancelled | stage7a_bench_v6_mmmu_pro_silent_no_image_03_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_silent_no_image_03_v6.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_04_v6 | cancelled | stage7a_bench_v6_mmmu_pro_silent_no_image_04_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_silent_no_image_04_v6.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_05_v6 | cancelled | stage7a_bench_v6_mmmu_pro_silent_no_image_05_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_silent_no_image_05_v6.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_06_v6 | cancelled | stage7a_bench_v6_mmmu_pro_silent_no_image_06_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_silent_no_image_06_v6.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_07_v6 | cancelled | stage7a_bench_v6_mmmu_pro_silent_no_image_07_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_silent_no_image_07_v6.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_08_v6 | cancelled | stage7a_bench_v6_mmmu_pro_silent_no_image_08_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_silent_no_image_08_v6.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_09_v6 | cancelled | stage7a_bench_v6_mmmu_pro_silent_no_image_09_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_silent_no_image_09_v6.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_10_v6 | cancelled | stage7a_bench_v6_mmmu_pro_silent_no_image_10_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_silent_no_image_10_v6.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_11_v6 | cancelled | stage7a_bench_v6_mmmu_pro_silent_no_image_11_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_silent_no_image_11_v6.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_12_v6 | cancelled | stage7a_bench_v6_mmmu_pro_silent_no_image_12_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_silent_no_image_12_v6.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_13_v6 | cancelled | stage7a_bench_v6_mmmu_pro_silent_no_image_13_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_silent_no_image_13_v6.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_14_v6 | cancelled | stage7a_bench_v6_mmmu_pro_silent_no_image_14_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_silent_no_image_14_v6.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_15_v6 | cancelled | stage7a_bench_v6_mmmu_pro_silent_no_image_15_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_silent_no_image_15_v6.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_00_v6 | cancelled | stage7a_bench_v6_mmmu_pro_explicit_guess_00_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_explicit_guess_00_v6.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_01_v6 | cancelled | stage7a_bench_v6_mmmu_pro_explicit_guess_01_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_explicit_guess_01_v6.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_02_v6 | cancelled | stage7a_bench_v6_mmmu_pro_explicit_guess_02_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_explicit_guess_02_v6.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_03_v6 | cancelled | stage7a_bench_v6_mmmu_pro_explicit_guess_03_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_explicit_guess_03_v6.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_04_v6 | cancelled | stage7a_bench_v6_mmmu_pro_explicit_guess_04_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_explicit_guess_04_v6.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_05_v6 | cancelled | stage7a_bench_v6_mmmu_pro_explicit_guess_05_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_explicit_guess_05_v6.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_06_v6 | cancelled | stage7a_bench_v6_mmmu_pro_explicit_guess_06_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_explicit_guess_06_v6.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_07_v6 | cancelled | stage7a_bench_v6_mmmu_pro_explicit_guess_07_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_explicit_guess_07_v6.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_08_v6 | cancelled | stage7a_bench_v6_mmmu_pro_explicit_guess_08_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_explicit_guess_08_v6.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_09_v6 | cancelled | stage7a_bench_v6_mmmu_pro_explicit_guess_09_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_explicit_guess_09_v6.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_10_v6 | cancelled | stage7a_bench_v6_mmmu_pro_explicit_guess_10_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_explicit_guess_10_v6.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_11_v6 | cancelled | stage7a_bench_v6_mmmu_pro_explicit_guess_11_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_explicit_guess_11_v6.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_12_v6 | cancelled | stage7a_bench_v6_mmmu_pro_explicit_guess_12_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_explicit_guess_12_v6.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_13_v6 | cancelled | stage7a_bench_v6_mmmu_pro_explicit_guess_13_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_explicit_guess_13_v6.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_14_v6 | cancelled | stage7a_bench_v6_mmmu_pro_explicit_guess_14_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_explicit_guess_14_v6.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_15_v6 | cancelled | stage7a_bench_v6_mmmu_pro_explicit_guess_15_v6 | a6000 |  | runs/stage7a_bench/mmmu_pro_explicit_guess_15_v6.log |
| stage7a_bench_mmmu_attention_parity_diagnostic_v1 | succeeded | stage7a_bench_mmmu_attention_parity_diagnostic_v1 | a6000 | 113280 | runs/stage7a_bench/mmmu_attention_parity_diagnostic_v1.log |
| stage7a_bench_v6_mmmu_pro_image_present_00_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_00_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_00_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_01_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_01_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_01_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_02_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_02_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_02_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_03_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_03_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_03_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_04_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_04_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_04_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_05_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_05_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_05_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_06_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_06_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_06_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_07_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_07_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_07_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_08_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_08_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_08_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_09_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_09_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_09_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_10_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_10_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_10_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_11_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_11_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_11_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_12_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_12_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_12_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_13_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_13_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_13_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_14_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_14_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_14_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_15_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_15_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_15_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_16_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_16_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_16_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_17_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_17_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_17_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_18_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_18_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_18_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_19_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_19_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_19_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_20_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_20_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_20_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_21_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_21_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_21_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_22_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_22_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_22_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_23_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_23_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_23_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_24_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_24_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_24_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_25_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_25_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_25_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_26_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_26_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_26_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_27_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_27_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_27_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_28_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_28_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_28_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_29_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_29_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_29_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_30_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_30_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_30_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_31_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_31_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_31_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_32_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_32_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_32_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_33_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_33_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_33_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_34_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_34_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_34_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_35_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_35_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_35_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_36_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_36_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_36_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_37_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_37_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_37_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_38_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_38_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_38_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_39_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_39_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_39_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_40_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_40_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_40_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_41_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_41_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_41_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_42_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_42_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_42_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_43_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_43_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_43_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_44_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_44_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_44_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_45_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_45_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_45_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_46_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_46_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_46_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_47_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_47_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_47_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_48_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_48_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_48_v6b.log |
| stage7a_bench_v6_mmmu_pro_image_present_49_v6b | succeeded | stage7a_bench_v6_mmmu_pro_image_present_49_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_image_present_49_v6b.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_00_v6b | succeeded | stage7a_bench_v6_mmmu_pro_silent_no_image_00_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_silent_no_image_00_v6b.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_01_v6b | succeeded | stage7a_bench_v6_mmmu_pro_silent_no_image_01_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_silent_no_image_01_v6b.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_02_v6b | succeeded | stage7a_bench_v6_mmmu_pro_silent_no_image_02_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_silent_no_image_02_v6b.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_03_v6b | succeeded | stage7a_bench_v6_mmmu_pro_silent_no_image_03_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_silent_no_image_03_v6b.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_04_v6b | succeeded | stage7a_bench_v6_mmmu_pro_silent_no_image_04_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_silent_no_image_04_v6b.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_05_v6b | succeeded | stage7a_bench_v6_mmmu_pro_silent_no_image_05_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_silent_no_image_05_v6b.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_06_v6b | succeeded | stage7a_bench_v6_mmmu_pro_silent_no_image_06_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_silent_no_image_06_v6b.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_07_v6b | succeeded | stage7a_bench_v6_mmmu_pro_silent_no_image_07_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_silent_no_image_07_v6b.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_08_v6b | succeeded | stage7a_bench_v6_mmmu_pro_silent_no_image_08_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_silent_no_image_08_v6b.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_09_v6b | succeeded | stage7a_bench_v6_mmmu_pro_silent_no_image_09_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_silent_no_image_09_v6b.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_10_v6b | succeeded | stage7a_bench_v6_mmmu_pro_silent_no_image_10_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_silent_no_image_10_v6b.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_11_v6b | succeeded | stage7a_bench_v6_mmmu_pro_silent_no_image_11_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_silent_no_image_11_v6b.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_12_v6b | succeeded | stage7a_bench_v6_mmmu_pro_silent_no_image_12_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_silent_no_image_12_v6b.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_13_v6b | succeeded | stage7a_bench_v6_mmmu_pro_silent_no_image_13_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_silent_no_image_13_v6b.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_14_v6b | succeeded | stage7a_bench_v6_mmmu_pro_silent_no_image_14_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_silent_no_image_14_v6b.log |
| stage7a_bench_v6_mmmu_pro_silent_no_image_15_v6b | succeeded | stage7a_bench_v6_mmmu_pro_silent_no_image_15_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_silent_no_image_15_v6b.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_00_v6b | succeeded | stage7a_bench_v6_mmmu_pro_explicit_guess_00_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_explicit_guess_00_v6b.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_01_v6b | succeeded | stage7a_bench_v6_mmmu_pro_explicit_guess_01_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_explicit_guess_01_v6b.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_02_v6b | succeeded | stage7a_bench_v6_mmmu_pro_explicit_guess_02_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_explicit_guess_02_v6b.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_03_v6b | succeeded | stage7a_bench_v6_mmmu_pro_explicit_guess_03_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_explicit_guess_03_v6b.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_04_v6b | succeeded | stage7a_bench_v6_mmmu_pro_explicit_guess_04_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_explicit_guess_04_v6b.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_05_v6b | succeeded | stage7a_bench_v6_mmmu_pro_explicit_guess_05_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_explicit_guess_05_v6b.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_06_v6b | succeeded | stage7a_bench_v6_mmmu_pro_explicit_guess_06_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_explicit_guess_06_v6b.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_07_v6b | succeeded | stage7a_bench_v6_mmmu_pro_explicit_guess_07_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_explicit_guess_07_v6b.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_08_v6b | succeeded | stage7a_bench_v6_mmmu_pro_explicit_guess_08_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_explicit_guess_08_v6b.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_09_v6b | succeeded | stage7a_bench_v6_mmmu_pro_explicit_guess_09_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_explicit_guess_09_v6b.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_10_v6b | succeeded | stage7a_bench_v6_mmmu_pro_explicit_guess_10_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_explicit_guess_10_v6b.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_11_v6b | succeeded | stage7a_bench_v6_mmmu_pro_explicit_guess_11_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_explicit_guess_11_v6b.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_12_v6b | succeeded | stage7a_bench_v6_mmmu_pro_explicit_guess_12_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_explicit_guess_12_v6b.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_13_v6b | succeeded | stage7a_bench_v6_mmmu_pro_explicit_guess_13_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_explicit_guess_13_v6b.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_14_v6b | succeeded | stage7a_bench_v6_mmmu_pro_explicit_guess_14_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_explicit_guess_14_v6b.log |
| stage7a_bench_v6_mmmu_pro_explicit_guess_15_v6b | succeeded | stage7a_bench_v6_mmmu_pro_explicit_guess_15_v6b | a6000 | 113280 | runs/stage7a_bench/mmmu_pro_explicit_guess_15_v6b.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_00_v6 | failed | stage7a_bench_v6_mmlongbench_doc_image_present_00_v6 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_00_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_01_v6 | failed | stage7a_bench_v6_mmlongbench_doc_image_present_01_v6 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_01_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_02_v6 | failed | stage7a_bench_v6_mmlongbench_doc_image_present_02_v6 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_02_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_03_v6 | failed | stage7a_bench_v6_mmlongbench_doc_image_present_03_v6 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_03_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_04_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_04_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_04_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_05_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_05_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_05_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_06_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_06_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_06_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_07_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_07_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_07_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_08_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_08_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_08_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_09_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_09_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_09_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_10_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_10_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_10_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_11_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_11_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_11_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_12_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_12_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_12_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_13_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_13_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_13_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_14_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_14_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_14_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_15_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_15_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_15_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_16_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_16_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_16_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_17_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_17_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_17_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_18_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_18_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_18_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_19_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_19_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_19_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_20_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_20_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_20_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_21_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_21_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_21_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_22_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_22_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_22_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_23_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_23_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_23_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_24_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_24_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_24_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_25_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_25_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_25_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_26_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_26_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_26_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_27_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_27_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_27_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_28_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_28_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_28_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_29_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_29_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_29_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_30_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_30_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_30_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_31_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_31_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_31_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_32_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_32_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_32_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_33_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_33_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_33_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_34_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_34_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_34_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_35_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_35_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_35_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_36_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_36_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_36_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_37_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_37_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_37_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_38_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_38_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_38_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_39_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_39_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_39_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_40_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_40_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_40_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_41_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_41_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_41_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_42_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_42_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_42_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_43_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_43_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_43_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_44_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_44_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_44_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_45_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_45_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_45_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_46_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_46_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_46_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_47_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_47_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_47_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_48_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_48_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_48_v6.log |
| stage7a_bench_v6_mmlongbench_doc_image_present_49_v6 | cancelled | stage7a_bench_v6_mmlongbench_doc_image_present_49_v6 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_49_v6.log |
| stage7a_bench_document_reference_diagnostic_v7 | failed | stage7a_bench_document_reference_diagnostic_v7 | a6000 | 113280 | runs/stage7a_bench/document_reference_diagnostic_v7.log |
| stage7a_bench_document_reference_diagnostic_v8 | succeeded | stage7a_bench_document_reference_diagnostic_v8 | a6000 | 113280 | runs/stage7a_bench/document_reference_diagnostic_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_00_v8 | failed | stage7a_bench_v8_mmlongbench_doc_image_present_00_v8 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_00_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_01_v8 | succeeded | stage7a_bench_v8_mmlongbench_doc_image_present_01_v8 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_01_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_02_v8 | succeeded | stage7a_bench_v8_mmlongbench_doc_image_present_02_v8 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_02_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_03_v8 | succeeded | stage7a_bench_v8_mmlongbench_doc_image_present_03_v8 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_03_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_04_v8 | succeeded | stage7a_bench_v8_mmlongbench_doc_image_present_04_v8 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_04_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_05_v8 | succeeded | stage7a_bench_v8_mmlongbench_doc_image_present_05_v8 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_05_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_06_v8 | succeeded | stage7a_bench_v8_mmlongbench_doc_image_present_06_v8 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_06_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_07_v8 | succeeded | stage7a_bench_v8_mmlongbench_doc_image_present_07_v8 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_07_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_08_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_08_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_08_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_09_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_09_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_09_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_10_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_10_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_10_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_11_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_11_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_11_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_12_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_12_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_12_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_13_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_13_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_13_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_14_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_14_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_14_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_15_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_15_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_15_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_16_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_16_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_16_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_17_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_17_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_17_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_18_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_18_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_18_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_19_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_19_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_19_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_20_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_20_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_20_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_21_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_21_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_21_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_22_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_22_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_22_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_23_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_23_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_23_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_24_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_24_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_24_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_25_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_25_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_25_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_26_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_26_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_26_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_27_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_27_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_27_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_28_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_28_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_28_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_29_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_29_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_29_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_30_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_30_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_30_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_31_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_31_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_31_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_32_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_32_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_32_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_33_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_33_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_33_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_34_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_34_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_34_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_35_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_35_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_35_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_36_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_36_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_36_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_37_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_37_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_37_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_38_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_38_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_38_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_39_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_39_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_39_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_40_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_40_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_40_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_41_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_41_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_41_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_42_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_42_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_42_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_43_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_43_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_43_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_44_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_44_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_44_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_45_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_45_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_45_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_46_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_46_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_46_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_47_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_47_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_47_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_48_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_48_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_48_v8.log |
| stage7a_bench_v8_mmlongbench_doc_image_present_49_v8 | cancelled | stage7a_bench_v8_mmlongbench_doc_image_present_49_v8 | a6000 |  | runs/stage7a_bench/mmlongbench_doc_image_present_49_v8.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_00_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_00_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_00_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_01_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_01_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_01_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_02_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_02_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_02_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_03_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_03_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_03_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_04_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_04_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_04_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_05_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_05_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_05_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_06_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_06_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_06_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_07_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_07_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_07_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_08_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_08_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_08_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_09_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_09_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_09_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_10_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_10_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_10_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_11_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_11_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_11_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_12_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_12_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_12_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_13_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_13_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_13_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_14_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_14_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_14_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_15_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_15_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_15_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_16_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_16_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_16_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_17_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_17_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_17_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_18_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_18_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_18_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_19_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_19_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_19_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_20_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_20_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_20_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_21_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_21_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_21_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_22_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_22_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_22_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_23_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_23_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_23_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_24_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_24_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_24_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_25_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_25_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_25_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_26_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_26_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_26_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_27_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_27_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_27_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_28_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_28_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_28_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_29_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_29_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_29_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_30_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_30_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_30_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_31_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_31_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_31_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_32_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_32_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_32_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_33_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_33_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_33_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_34_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_34_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_34_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_35_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_35_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_35_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_36_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_36_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_36_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_37_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_37_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_37_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_38_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_38_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_38_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_39_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_39_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_39_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_40_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_40_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_40_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_41_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_41_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_41_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_42_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_42_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_42_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_43_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_43_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_43_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_44_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_44_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_44_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_45_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_45_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_45_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_46_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_46_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_46_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_47_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_47_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_47_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_48_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_48_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_48_v9.log |
| stage7a_bench_v9_mmlongbench_doc_image_present_49_v9 | succeeded | stage7a_bench_v9_mmlongbench_doc_image_present_49_v9 | a6000 | 113280 | runs/stage7a_bench/mmlongbench_doc_image_present_49_v9.log |
| stage7a_bench_v2_causal_mathwild_mechanics_v6_20260915 | failed | stage7a_bench_v2_causal_mathwild_mechanics_v6_20260915 | a6000 | 113280 | runs/stage7a_bench/mathwild_mechanics_v6_20260915.log |
| stage7a_bench_v2_causal_mathwild_mechanics_v6_cpu_20260915 | succeeded | stage7a_bench_v2_causal_mathwild_mechanics_v6_cpu_20260915 | a6000 | 113280 | runs/stage7a_bench/mathwild_mechanics_v6_cpu_20260915.log |
| stage7a_bench_v2_causal_mathwild_causal_v6_20260915 | succeeded | stage7a_bench_v2_causal_mathwild_causal_v6_20260915 | a6000 | 113280 | runs/stage7a_bench/mathwild_causal_v6_20260915.log |
| stage7a_bench_v2_causal_mmmu_mechanics_v10_20260915 | succeeded | stage7a_bench_v2_causal_mmmu_mechanics_v10_20260915 | a6000 | 113280 | runs/stage7a_bench/mmmu_mechanics_v10_20260915.log |
| stage7a_bench_v2_causal_mmmu_causal_v10_20260915 | succeeded | stage7a_bench_v2_causal_mmmu_causal_v10_20260915 | a6000 | 113280 | runs/stage7a_bench/mmmu_causal_v10_20260915.log |
| stage7a_bench_v2_review_maintenance_20260915_0300 | succeeded | stage7a_bench_v2_review_maintenance_20260915_0300 | a6000 | 113280 | runs/stage7a_bench/review_maintenance_20260915_0300.log |
| stage7a_bench_v2_mmlong_node02_2gpu_20260915 | cancelled | stage7a_bench_v2_mmlong_node02_2gpu_20260915 | a6000 | 114451 | runs/stage7a_bench/mmlong_node02_2gpu_20260915/slurm.log |
| stage7a_bench_v2_causal_mmlong_causal_mechanics_v12_20260915 | failed | stage7a_bench_v2_causal_mmlong_causal_mechanics_v12_20260915 | a6000 | 114451 | runs/stage7a_bench/mmlong_causal_mechanics_v12_20260915.log |
| stage7a_bench_v2_gpu_identity_v13 | succeeded | stage7a_bench_v2_gpu_identity_v13 | a6000 | 114451 | runs/stage7a_bench/mmlong_node02_2gpu_20260915/identity.log |
| stage7a_bench_v2_causal_mmlong_causal_mechanics_v13_20260915 | failed | stage7a_bench_v2_causal_mmlong_causal_mechanics_v13_20260915 | a6000 | 114451 | runs/stage7a_bench/mmlong_causal_mechanics_v13_20260915.log |
| stage7a_bench_v2_causal_mmlong_causal_mechanics_v14_20260915 | failed | stage7a_bench_v2_causal_mmlong_causal_mechanics_v14_20260915 | a6000 | 114451 | runs/stage7a_bench/mmlong_causal_mechanics_v14_20260915.log |
| stage7a_bench_v2_causal_mmlong_causal_mechanics_v15_20260915 | succeeded | stage7a_bench_v2_causal_mmlong_causal_mechanics_v15_20260915 | a6000 | 114451 | runs/stage7a_bench/mmlong_causal_mechanics_v15_20260915.log |
| stage7a_bench_v2_causal_mmlong_causal_v15_20260915 | succeeded | stage7a_bench_v2_causal_mmlong_causal_v15_20260915 | a6000 | 114451 | runs/stage7a_bench/mmlong_causal_v15_20260915.log |
| interactive_node03_2gpu_20260916 | completed | interactive_node03_2gpu_20260916 | a6000 | 114923 | runs/allocations/node03_2gpu_20260916/slurm.log |
| stage8a_calibration_native_v1 | failed | stage8a_calibration_native_v1 | a6000 | 114923 | runs/stage8a/calibration_wrapper.log |
| interactive_node02_2gpu_20260916 | cancelled | interactive_node02_2gpu_20260916 | a6000 | 115046 | runs/allocations/node02_2gpu_20260916/slurm.log |
| stage8a_calibration_native_v2 | succeeded | stage8a_calibration_native_v2 | a6000 | 115046 | runs/stage8a/calibration_v2_wrapper.log |
| stage8a_mechanics_v1 | cancelled | stage8a_mechanics_v1 | a6000 | 115046 | runs/stage8a/mechanics_v1_wrapper.log |
| stage8a_mechanics_v2 | succeeded | stage8a_mechanics_v2 | a6000 | 115046 | runs/stage8a/mechanics_v2_wrapper.log |
| stage8a_localization_profile_v1 | succeeded | stage8a_localization_profile_v1 | a6000 | 115046 | runs/stage8a/localization_profile_v1_wrapper.log |
| stage8a_localization_joint_v1 | succeeded | stage8a_localization_joint_v1 | a6000 | 115046 | runs/stage8a/localization_joint_v1_wrapper.log |
| stage8a_main_native_v1 | failed | stage8a_main_native_v1 | a6000 | 115046 | runs/stage8a/main_v1_wrapper.log |
| stage8a_measurement_smoke_v1 | succeeded | stage8a_measurement_smoke_v1 | a6000 | 115046 | runs/stage8a/measurement_smoke_v1_wrapper.log |
| stage8a_measurement_smoke_v2 | succeeded | stage8a_measurement_smoke_v2 | a6000 | 115046 | runs/stage8a/measurement_smoke_v2_wrapper.log |
| stage8a_main_native_tail_v1 | succeeded | stage8a_main_native_tail_v1 | a6000 | 115046 | runs/stage8a/main_native_tail_v1_wrapper.log |
| stage8a_measurement_discovery_v1 | succeeded | stage8a_measurement_discovery_v1 | a6000 | 115046 | runs/stage8a/measurement_discovery_v1_worker_0.log |
| stage8a_measurement_confirmation_v1 | succeeded | stage8a_measurement_confirmation_v1 | a6000 | 115046 | runs/stage8a/measurement_confirmation_v1_worker_0.log |
| stage8a_value_assays_v1 | succeeded | stage8a_value_assays_v1 | a6000 | 115046 | runs/stage8a/value_assays_v1_worker_0.log |
| stage8b_transfer32_v1 | succeeded | stage8b_transfer32_v1 | a6000 | 115741 | runs/stage8b/transfer32_slurm.log |
| stage8b_v2_transfer32_t1_v1 | cancelled | stage8b_v2_transfer32_t1_v1 | a6000 | 116063 | runs/stage8b/v2/slurm.log |
| stage8b_v2_transfer32_node02_single_v1 | cancelled | stage8b_v2_transfer32_node02_single_v1 | a6000 | 116487 | runs/stage8b/v2/node02_single/slurm.log |
| stage8b_v2_transfer32_node02_four_v1 | succeeded | stage8b_v2_transfer32_node02_four_v1 | a6000 | 116610 | runs/stage8b/v2/node02_four/slurm.log |
| stage8b1a_census224_node02_v1 | cancelled | stage8b1a_census224_node02_v1 | a6000 | 116993 | runs/stage8b1a/node02/slurm.log |
| stage8b1a_resume125_node06_v1 | succeeded | stage8b1a_resume125_node06_v1 | a6000 | 117219 | runs/stage8b1a/node06_v1/slurm.log |
| stage8b_block0_node02_v1 | succeeded | stage8b_block0_node02_v1 | a6000 | 117930 | runs/stage8b_block0/slurm.log |
| stage8b_block1_node06_v1 | cancelled | stage8b_block1_node06_v1 | a6000 | 118016 | runs/stage8b_block1/slurm.log |
| stage8b_block1_rank0_split_v2 | cancelled | stage8b_block1_rank0_split_v2 | a6000 | 118034 | runs/stage8b_block1/split_rank0.log |
| stage8b_block1_rank1_split_v2 | succeeded | stage8b_block1_rank1_split_v2 | a6000 | 118035 | runs/stage8b_block1/split_rank1.log |
| stage8b_block1_rank0_node06_v3 | succeeded | stage8b_block1_rank0_node06_v3 | a6000 | 118038 | runs/stage8b_block1/node06_rank0_v3.log |
| stage8b_block1_assemble_node06_v3 | succeeded | stage8b_block1_assemble_node06_v3 | a6000 | 118039 | runs/stage8b_block1/node06_assemble_v3.log |
| stage8b_block2_replay_node06_v1 | succeeded | stage8b_block2_replay_node06_v1 | a6000 | 118076 | runs/stage8b_block2/replay_node06_v1/slurm.log |
| stage8b_block3a_native_replay_node02_v1 | succeeded | stage8b_block3a_native_replay_node02_v1 | a6000 | 118093 | runs/stage8b_block3a/native_replay_v1/slurm.log |
| stage8b_block3a_native_node02_v1 | cancelled | stage8b_block3a_native_node02_v1 | a6000 | 118099 | runs/stage8b_block3a/native_v1/slurm.log |
| stage8b_block3a_native_four_node02_v1 | succeeded | stage8b_block3a_native_four_node02_v1 | a6000 | 118116 | runs/stage8b_block3a/native_resume_four_v1/slurm.log |
| stage8c_v2_technical_v1 | failed | stage8c_v2_technical_v1 | a6000 | 118514 | runs/stage8c_v2/technical_v1/slurm.log |
| stage8c_v2_technical_v2 | failed | stage8c_v2_technical_v2 | a6000 | 118515 | runs/stage8c_v2/technical_v2/slurm.log |
| stage8c_v2_technical_v3 | failed | stage8c_v2_technical_v3 | a6000 | 118518 | runs/stage8c_v2/technical_v3/slurm.log |
| stage8c_repair_forensic_v1 | succeeded | stage8c_repair_forensic_v1 | a6000 | 118525 | runs/stage8c_repair/forensic_v1/slurm.log |
| stage8c_repair_candidate_v1 | succeeded | stage8c_repair_candidate_v1 | a6000 | 118526 | runs/stage8c_repair/candidate_v1/slurm.log |
| stage8c_v3_dev_v1 | cancelled | stage8c_v3_dev_v1 | a6000 | 118529 | runs/stage8c_v3/dev_v1/slurm.log |
| stage8c_v3_dev_four_v1 | succeeded | stage8c_v3_dev_four_v1 | a6000 | 118545 | runs/stage8c_v3/dev_four_v1/slurm.log |
| stage8b_block3b_analysis_v1 | succeeded | stage8b_block3b_analysis_v1 | a6000 | 119818 | runs/stage8b_block3b_v1/analysis_slurm.log |
| stage8b_block3b_analysis_v2 | succeeded | stage8b_block3b_analysis_v2 | a6000 | 119819 | runs/stage8b_block3b_v1/analysis_v2_slurm.log |
| stage9a_preflight_v1 | cancelled | stage9a_preflight_v1 | a6000 |  | runs/stage9a/v1/preflight_slurm.log |
| stage9a_preflight_node07_v1 | cancelled | stage9a_preflight_node07_v1 | a6000 | 120840 | runs/stage9a/v1/preflight_node07_slurm.log |
| stage9a_preflight_recovery_v1 | succeeded | stage9a_preflight_recovery_v1 | a6000 | 120898 | runs/stage9a/v1/stage9a_preflight_recovery_v1_slurm.log |
| stage9a_native_worker0_v1 | succeeded | stage9a_native_worker0_v1 | a6000 | 120903 | runs/stage9a/v1/stage9a_native_worker0_v1_slurm.log |
| stage9a_native_worker1_v1 | succeeded | stage9a_native_worker1_v1 | a6000 | 120904 | runs/stage9a/v1/stage9a_native_worker1_v1_slurm.log |
| stage9a_native_worker2_v1 | succeeded | stage9a_native_worker2_v1 | a6000 | 120905 | runs/stage9a/v1/stage9a_native_worker2_v1_slurm.log |
| stage9a_native_worker3_v1 | succeeded | stage9a_native_worker3_v1 | a6000 | 120906 | runs/stage9a/v1/stage9a_native_worker3_v1_slurm.log |
| stage9a_causal_0 | succeeded | stage9a | a6000 | 121562 | runs/stage9a/v1/stage9a_causal_0.log |
| stage9a_causal_1 | succeeded | stage9a | a6000 | 121563 | runs/stage9a/v1/stage9a_causal_1.log |
| stage9a_causal_2 | succeeded | stage9a | a6000 | 121564 | runs/stage9a/v1/stage9a_causal_2.log |
| stage9a_cpu_extract | cancelled | stage9a | a6000 | 121566 | runs/stage9a/v1/cpu_extract.log |
| stage9a_cpu_analysis_node03 | succeeded | stage9a | a6000 | 121568 | runs/stage9a/v1/cpu_analysis_node03.log |
| stage9a_dynamics_preflight_v1 | succeeded | stage9a_dynamics_preflight_v1 | a6000 | 121689 | runs/stage9a_dynamics/v1/preflight_slurm.log |
| stage9a_dynamics_node07_probe_v1 | succeeded | stage9a_dynamics_node07_probe_v1 | a6000 | 121702 | runs/stage9a_dynamics/v1/node07_probe_slurm.log |
| stage9a_dynamics_worker0_v1 | cancelled | stage9a_dynamics_worker0_v1 | a6000 | 121703 | runs/stage9a_dynamics/v1/stage9a_dynamics_worker0_v1_slurm.log |
| stage9a_dynamics_worker1_v1 | cancelled | stage9a_dynamics_worker1_v1 | a6000 | 121704 | runs/stage9a_dynamics/v1/stage9a_dynamics_worker1_v1_slurm.log |
| stage9a_dynamics_worker2_v1 | cancelled | stage9a_dynamics_worker2_v1 | a6000 | 121705 | runs/stage9a_dynamics/v1/stage9a_dynamics_worker2_v1_slurm.log |
| stage9a_dynamics_worker3_v1 | cancelled | stage9a_dynamics_worker3_v1 | a6000 | 121706 | runs/stage9a_dynamics/v1/stage9a_dynamics_worker3_v1_slurm.log |
| stage9a_dynamics_coordinator_v1 | cancelled | stage9a_dynamics_coordinator_v1 | a6000 | 121713 | runs/stage9a_dynamics/v1/coordinator_slurm.log |
| stage9a_amendment_worker0_v1 | succeeded | stage9a_amendment_worker0_v1 | a6000 | 121805 | runs/stage9a_dynamics/amendment_v1/stage9a_amendment_worker0_v1_slurm.log |
| stage9a_amendment_worker1_v1 | succeeded | stage9a_amendment_worker1_v1 | a6000 | 121806 | runs/stage9a_dynamics/amendment_v1/stage9a_amendment_worker1_v1_slurm.log |
| stage9a_amendment_readout_v1 | succeeded | stage9a_amendment_readout_v1 | a6000 | 121804 | runs/stage9a_dynamics/amendment_v1/stage9a_amendment_readout_v1_slurm.log |
| stage9a_amendment_coordinator_v1 | cancelled | stage9a_amendment_coordinator_v1 | a6000 | 121807 | runs/stage9a_dynamics/amendment_v1/coordinator_slurm.log |
| stage9a_amendment_worker_20260924T082617_0 | succeeded | stage9a_amendment_worker_20260924T082617_0 | a6000 | 121814 | runs/stage9a_dynamics/amendment_v1/stage9a_amendment_worker_20260924T082617_0_slurm.log |
| stage9a_amendment_worker_20260924T120919_1 | succeeded | stage9a_amendment_worker_20260924T120919_1 | a6000 | 121996 | runs/stage9a_dynamics/amendment_v1/stage9a_amendment_worker_20260924T120919_1_slurm.log |
| stage9a_amendment_coordinator_recovery_20260925 | succeeded | stage9a_amendment_coordinator_recovery_20260925 | a6000 | 122749 | runs/stage9a_dynamics/amendment_v1/coordinator_recovery_20260925_slurm.log |
| stage9a_amendment_worker_scale8_20260925_0 | succeeded | stage9a_amendment_worker_scale8_20260925_0 | a6000 | 122753 | runs/stage9a_dynamics/amendment_v1/stage9a_amendment_worker_scale8_20260925_0_slurm.log |
| stage9a_amendment_worker_scale8_20260925_1 | succeeded | stage9a_amendment_worker_scale8_20260925_1 | a6000 | 122754 | runs/stage9a_dynamics/amendment_v1/stage9a_amendment_worker_scale8_20260925_1_slurm.log |
| stage9a_amendment_worker_scale8_20260925_2 | succeeded | stage9a_amendment_worker_scale8_20260925_2 | a6000 | 122755 | runs/stage9a_dynamics/amendment_v1/stage9a_amendment_worker_scale8_20260925_2_slurm.log |
| stage9a_amendment_worker_scale8_20260925_3 | succeeded | stage9a_amendment_worker_scale8_20260925_3 | a6000 | 122756 | runs/stage9a_dynamics/amendment_v1/stage9a_amendment_worker_scale8_20260925_3_slurm.log |
| stage9a_amendment_coordinator_scale8_20260925 | cancelled | stage9a_amendment_coordinator_scale8_20260925 | a6000 | 122752 | runs/stage9a_dynamics/amendment_v1/coordinator_scale8_20260925_slurm.log |
| stage9a_finish_answer_packets_v1 | succeeded | stage9a_finish_answer_packets_v1 | a6000 | 124210 | runs/stage9a_dynamics/amendment_v1/prepare_answers_slurm.log |
| stage9a_finish_main_analysis_v1 | succeeded | stage9a_finish_main_analysis_v1 | a6000 | 124244 | runs/stage9a_dynamics/amendment_v1/main_analysis_slurm.log |
| stage9a_controls_v1_worker0 | succeeded | stage9a_controls_v1_worker0 | a6000 | 124266 | runs/stage9a_dynamics/amendment_v1/controls_worker0.log |
| stage9a_controls_v1_worker1 | cancelled | stage9a_controls_v1_worker1 | a6000 | 124267 | runs/stage9a_dynamics/amendment_v1/controls_worker1.log |
| stage9a_controls_v1_worker2 | cancelled | stage9a_controls_v1_worker2 | a6000 | 124268 | runs/stage9a_dynamics/amendment_v1/controls_worker2.log |
| stage9a_controls_v1_worker3 | succeeded | stage9a_controls_v1_worker3 | a6000 | 124269 | runs/stage9a_dynamics/amendment_v1/controls_worker3.log |
| stage9a_controls_v1_worker4 | cancelled | stage9a_controls_v1_worker4 | a6000 | 124270 | runs/stage9a_dynamics/amendment_v1/controls_worker4.log |
| stage9a_controls_v1_worker5 | cancelled | stage9a_controls_v1_worker5 | a6000 | 124271 | runs/stage9a_dynamics/amendment_v1/controls_worker5.log |
| stage9a_controls_v1_worker6 | cancelled | stage9a_controls_v1_worker6 | a6000 | 124272 | runs/stage9a_dynamics/amendment_v1/controls_worker6.log |
| stage9a_controls_v1_worker7 | succeeded | stage9a_controls_v1_worker7 | a6000 | 124273 | runs/stage9a_dynamics/amendment_v1/controls_worker7.log |
| stage9a3_input_freeze_v1 | succeeded | stage9a3_input_freeze_v1 | a6000 | 124435 | runs/stage9a3/v1/input_freeze.log |
| stage9a3_qwen25_preflight_v1 | cancelled | stage9a3_qwen25_preflight_v1 | a6000 | 124437 | runs/stage9a3/v1/qwen25_preflight.log |
| stage9a3_qwen25_preflight_full_v1 | failed | stage9a3_qwen25_preflight_full_v1 | a6000 | 124438 | runs/stage9a3/v1/qwen25_preflight_full.log |
| stage9a3_qwen25_preflight_full_v2 | succeeded | stage9a3_qwen25_preflight_full_v2 | a6000 | 124439 | runs/stage9a3/v1/qwen25_preflight_full_v2.log |
| stage9a3_qwen25_grid_v1_worker0 | succeeded | stage9a3_qwen25_grid_v1_worker0 | a6000 | 124443 | runs/stage9a3/v1/qwen25_grid_worker0.log |
| stage9a3_qwen25_grid_v1_worker1 | succeeded | stage9a3_qwen25_grid_v1_worker1 | a6000 | 124444 | runs/stage9a3/v1/qwen25_grid_worker1.log |
| stage9a3_qwen25_grid_v1_worker2 | succeeded | stage9a3_qwen25_grid_v1_worker2 | a6000 | 124445 | runs/stage9a3/v1/qwen25_grid_worker2.log |
| stage9a3_design_figure_v1 | succeeded | stage9a3_design_figure_v1 | a6000 | 124446 | runs/stage9a3/v1/design_figure.log |
| stage9a3_design_figure_v2 | succeeded | stage9a3_design_figure_v2 | a6000 | 124447 | runs/stage9a3/v1/design_figure_v2.log |
| stage9a3_qwen25_grid_score_v1 | succeeded | stage9a3_qwen25_grid_score_v1 | a6000 | 124450 | runs/stage9a3/v1/qwen25_grid_score.log |
| stage9a3_qwen25_reserve_full_v1 | succeeded | stage9a3_qwen25_reserve_full_v1 | a6000 | 124451 | runs/stage9a3/v1/qwen25_reserve_full.log |
| stage9a3_qwen25_reserve_grid_v1_worker0 | succeeded | stage9a3_qwen25_reserve_grid_v1_worker0 | a6000 | 124453 | runs/stage9a3/v1/qwen25_reserve_grid_worker0.log |
| stage9a3_qwen25_reserve_grid_v1_worker1 | succeeded | stage9a3_qwen25_reserve_grid_v1_worker1 | a6000 | 124454 | runs/stage9a3/v1/qwen25_reserve_grid_worker1.log |
| stage9a3_qwen25_reserve_grid_v1_worker2 | succeeded | stage9a3_qwen25_reserve_grid_v1_worker2 | a6000 | 124455 | runs/stage9a3/v1/qwen25_reserve_grid_worker2.log |
| stage9a3_qwen25_reserve_grid_v1_worker3 | succeeded | stage9a3_qwen25_reserve_grid_v1_worker3 | a6000 | 124456 | runs/stage9a3/v1/qwen25_reserve_grid_worker3.log |
| stage9a3_qwen25_reserve_score_v1 | succeeded | stage9a3_qwen25_reserve_score_v1 | a6000 | 124457 | runs/stage9a3/v1/qwen25_reserve_score.log |
| stage9a3_qwen25_sink_v1_worker0 | succeeded | stage9a3_qwen25_sink_v1_worker0 | a6000 | 124459 | runs/stage9a3/v1/qwen25_sink_worker0.log |
| stage9a3_qwen25_sink_v1_worker1 | succeeded | stage9a3_qwen25_sink_v1_worker1 | a6000 | 124460 | runs/stage9a3/v1/qwen25_sink_worker1.log |
| stage9a3_qwen25_sink_v1_worker2 | succeeded | stage9a3_qwen25_sink_v1_worker2 | a6000 | 124461 | runs/stage9a3/v1/qwen25_sink_worker2.log |
| stage9a3_qwen3_preflight_full_v1 | succeeded | stage9a3_qwen3_preflight_full_v1 | a6000 | 124462 | runs/stage9a3/v1/qwen3_preflight_full.log |
| stage9a3_qwen25_sink_score_v1 | succeeded | stage9a3_qwen25_sink_score_v1 | a6000 | 124464 | runs/stage9a3/v1/qwen25_sink_score.log |
| stage9a3_finalize_v1 | succeeded | stage9a3_finalize_v1 | a6000 | 124465 | runs/stage9a3/v1/finalize.log |
| stage9a3_final_audit_v1 | succeeded | stage9a3_final_audit_v1 | a6000 | 124466 | runs/stage9a3/v1/final_audit.log |
| stage9a3_stop_figure_v2 | succeeded | stage9a3_stop_figure_v2 | a6000 | 124467 | runs/stage9a3/v1/stop_figure_v2.log |
| stage9a4_prepare | succeeded | stage9a4_prepare | a6000 | 124639 | runs/stage9a4/v1/prepare.log |
| stage9a4_noop | succeeded | stage9a4_noop | a6000 | 124641 | runs/stage9a4/v1/noop.log |
| stage9a4_full_0 | succeeded | stage9a4_full_0 | a6000 | 124642 | runs/stage9a4/v1/full_0.log |
| stage9a4_full_1 | succeeded | stage9a4_full_1 | a6000 | 124643 | runs/stage9a4/v1/full_1.log |
| stage9a4_full_2 | succeeded | stage9a4_full_2 | a6000 | 124644 | runs/stage9a4/v1/full_2.log |
| stage9a4_full_3 | succeeded | stage9a4_full_3 | a6000 | 124645 | runs/stage9a4/v1/full_3.log |
| stage9a4_masks | succeeded | stage9a4_masks | a6000 | 124646 | runs/stage9a4/v1/masks.log |
| stage9a4_r1_0 | succeeded | stage9a4_r1_0 | a6000 | 124647 | runs/stage9a4/v1/r1_0.log |
| stage9a4_r1_1 | succeeded | stage9a4_r1_1 | a6000 | 124648 | runs/stage9a4/v1/r1_1.log |
| stage9a4_r1_2 | succeeded | stage9a4_r1_2 | a6000 | 124649 | runs/stage9a4/v1/r1_2.log |
| stage9a4_r1_3 | succeeded | stage9a4_r1_3 | a6000 | 124650 | runs/stage9a4/v1/r1_3.log |
| stage9a4_score_r1 | succeeded | stage9a4_score_r1 | a6000 | 124652 | runs/stage9a4/v1/score_r1.log |
| stage9a4_t128_0 | succeeded | stage9a4_t128_0 | a6000 | 124653 | runs/stage9a4/v1/t128_0.log |
| stage9a4_t128_1 | succeeded | stage9a4_t128_1 | a6000 | 124654 | runs/stage9a4/v1/t128_1.log |
| stage9a4_t128_2 | succeeded | stage9a4_t128_2 | a6000 | 124655 | runs/stage9a4/v1/t128_2.log |
| stage9a4_t128_3 | succeeded | stage9a4_t128_3 | a6000 | 124656 | runs/stage9a4/v1/t128_3.log |
| stage9a4_score_t128 | succeeded | stage9a4_score_t128 | a6000 | 124657 | runs/stage9a4/v1/score_t128.log |
| stage9a4_sink_0 | succeeded | stage9a4_sink_0 | a6000 | 124658 | runs/stage9a4/v1/sink_0.log |
| stage9a4_sink_1 | succeeded | stage9a4_sink_1 | a6000 | 124659 | runs/stage9a4/v1/sink_1.log |
| stage9a4_sink_2 | succeeded | stage9a4_sink_2 | a6000 | 124660 | runs/stage9a4/v1/sink_2.log |
| stage9a4_sink_3 | succeeded | stage9a4_sink_3 | a6000 | 124661 | runs/stage9a4/v1/sink_3.log |
| stage9a4_compare | succeeded | stage9a4_compare | a6000 | 124662 | runs/stage9a4/v1/compare.log |
| stage9a4_final_analysis | succeeded | stage9a4_final_analysis | a6000 | 124663 | runs/stage9a4/v1/final_analysis.log |
| stage9a5_prepare | succeeded | stage9a5_prepare | a6000 | 124664 | runs/stage9a5/v1/prepare.log |
| stage9a5_noop | succeeded | stage9a5_noop | a6000 | 124665 | runs/stage9a5/v1/noop.log |
| stage9a5_full_0 | succeeded | stage9a5_full_0 | a6000 | 124666 | runs/stage9a5/v1/full_0.log |
| stage9a5_full_1 | succeeded | stage9a5_full_1 | a6000 | 124667 | runs/stage9a5/v1/full_1.log |
| stage9a5_full_2 | succeeded | stage9a5_full_2 | a6000 | 124668 | runs/stage9a5/v1/full_2.log |
| stage9a5_full_3 | succeeded | stage9a5_full_3 | a6000 | 124669 | runs/stage9a5/v1/full_3.log |
| stage9a5_validate | succeeded | stage9a5_validate | a6000 | 124670 | runs/stage9a5/v1/validate.log |
| stage9a5_relative_description | succeeded | stage9a5_relative_description | a4000 | 124671 | runs/stage9a5/v1/relative_description.log |
| stage9a5_manifest_t1 | succeeded | stage9a5_manifest_t1 | a4000 | 124672 | runs/stage9a5/v1/manifest_t1.log |
| stage9a5_t1_0 | succeeded | stage9a5_t1_0 | a6000 | 124673 | runs/stage9a5/v1/t1_0.log |
| stage9a5_t1_1 | succeeded | stage9a5_t1_1 | a6000 | 124674 | runs/stage9a5/v1/t1_1.log |
| stage9a5_t1_2 | succeeded | stage9a5_t1_2 | a6000 | 124675 | runs/stage9a5/v1/t1_2.log |
| stage9a5_t1_3 | succeeded | stage9a5_t1_3 | a6000 | 124676 | runs/stage9a5/v1/t1_3.log |
| stage9a5_score_t1 | succeeded | stage9a5_score_t1 | a4000 | 124677 | runs/stage9a5/v1/score_t1.log |
| stage9a5_manifest_sink | succeeded | stage9a5_manifest_sink | a4000 | 124678 | runs/stage9a5/v1/manifest_sink.log |
| stage9a5_sink_0 | succeeded | stage9a5_sink_0 | a6000 | 124679 | runs/stage9a5/v1/sink_0.log |
| stage9a5_sink_1 | succeeded | stage9a5_sink_1 | a6000 | 124680 | runs/stage9a5/v1/sink_1.log |
| stage9a5_sink_2 | succeeded | stage9a5_sink_2 | a6000 | 124681 | runs/stage9a5/v1/sink_2.log |
| stage9a5_sink_3 | succeeded | stage9a5_sink_3 | a6000 | 124682 | runs/stage9a5/v1/sink_3.log |
| stage9a5_close_cpu | succeeded | stage9a5_close_cpu | a4000 | 124683 | runs/stage9a5/v1/close_cpu.log |
| stage9a5_control_diagnostic | succeeded | stage9a5_control_diagnostic | a4000 | 124684 | runs/stage9a5/v1/control_diagnostic.log |
| stage9a5_presentation | succeeded | stage9a5_presentation | a4000 | 124686 | runs/stage9a5/v1/presentation.log |
| stage9a5_report | succeeded | stage9a5_report | a4000 | 124687 | runs/stage9a5/v1/report.log |
| stage10a_prepare | succeeded | stage10a_prepare | a4000 | 124856 | runs/stage10a/v1/prepare.log |
| stage10a_validate | failed | stage10a_validate | a6000 | 124857 | runs/stage10a/v1/validate.log |
| stage10a_validate_r1 | succeeded | stage10a_validate_r1 | a6000 | 124861 | runs/stage10a/v1/validate_r1.log |
| stage10a_gate_a_0 | succeeded | stage10a_gate_a_0 | a6000 | 124862 | runs/stage10a/v1/gate_a_0.log |
| stage10a_gate_a_1 | succeeded | stage10a_gate_a_1 | a6000 | 124863 | runs/stage10a/v1/gate_a_1.log |
| stage10a_gate_a_2 | succeeded | stage10a_gate_a_2 | a6000 | 124864 | runs/stage10a/v1/gate_a_2.log |
| stage10a_gate_a_3 | succeeded | stage10a_gate_a_3 | a6000 | 124865 | runs/stage10a/v1/gate_a_3.log |
| stage10a_gate_a_4 | succeeded | stage10a_gate_a_4 | a6000 | 124866 | runs/stage10a/v1/gate_a_4.log |
| stage10a_gate_a_5 | succeeded | stage10a_gate_a_5 | a6000 | 124867 | runs/stage10a/v1/gate_a_5.log |
| stage10a_gate_a_6 | succeeded | stage10a_gate_a_6 | a6000 | 124868 | runs/stage10a/v1/gate_a_6.log |
| stage10a_gate_a_7 | succeeded | stage10a_gate_a_7 | a6000 | 124869 | runs/stage10a/v1/gate_a_7.log |
| stage10a_analyze_a | succeeded | stage10a_analyze_a | a4000 | 124870 | runs/stage10a/v1/analyze_a.log |
| stage10a_prepare_edits | succeeded | stage10a_prepare_edits | a4000 | 124872 | runs/stage10a/v1/prepare_edits.log |
| stage10a_gate_b_0 | succeeded | stage10a_gate_b_0 | a6000 | 124874 | runs/stage10a/v1/gate_b_0.log |
| stage10a_gate_b_1 | succeeded | stage10a_gate_b_1 | a6000 | 124875 | runs/stage10a/v1/gate_b_1.log |
| stage10a_gate_b_2 | succeeded | stage10a_gate_b_2 | a6000 | 124876 | runs/stage10a/v1/gate_b_2.log |
| stage10a_gate_b_3 | succeeded | stage10a_gate_b_3 | a6000 | 124877 | runs/stage10a/v1/gate_b_3.log |
| stage10a_analyze_b | succeeded | stage10a_analyze_b | a4000 | 124878 | runs/stage10a/v1/analyze_b.log |
| stage10a_prepare_dominance | succeeded | stage10a_prepare_dominance | a4000 | 124889 | runs/stage10a/v1/prepare_dominance.log |
| stage10a_validate_dominance | succeeded | stage10a_validate_dominance | a6000 | 124890 | runs/stage10a/v1/validate_dominance.log |
| stage10a_source_geometry | succeeded | stage10a_source_geometry | a4000 | 124891 | runs/stage10a/v1/source_geometry.log |
| stage10a_dominance_0 | succeeded | stage10a_dominance_0 | a6000 | 124892 | runs/stage10a/v1/dominance_0.log |
| stage10a_dominance_1 | succeeded | stage10a_dominance_1 | a6000 | 124893 | runs/stage10a/v1/dominance_1.log |
| stage10a_analyze_dominance | succeeded | stage10a_analyze_dominance | a4000 | 124894 | runs/stage10a/v1/analyze_dominance.log |
| stage10a_finalize | succeeded | stage10a_finalize | a4000 | 124895 | runs/stage10a/v1/finalize.log |
| stage10a_final_audit | succeeded | stage10a_final_audit | a4000 | 124896 | runs/stage10a/v1/final_audit.log |
| stage10ar_prepare | succeeded | stage10ar_prepare | a4000 | 124997 | runs/stage10ar/v1/prepare.log |
| stage10ar_validate | succeeded | stage10ar_validate | a6000 | 124998 | runs/stage10ar/v1/validate.log |
| stage10ar_primary_0 | succeeded | stage10ar_primary_0 | a6000 | 125000 | runs/stage10ar/v1/primary_0.log |
| stage10ar_primary_1 | succeeded | stage10ar_primary_1 | a6000 | 125001 | runs/stage10ar/v1/primary_1.log |
| stage10ar_primary_2 | succeeded | stage10ar_primary_2 | a6000 | 125002 | runs/stage10ar/v1/primary_2.log |
| stage10ar_primary_3 | succeeded | stage10ar_primary_3 | a6000 | 125003 | runs/stage10ar/v1/primary_3.log |
| stage10ar_analyze_primary | succeeded | stage10ar_analyze_primary | a4000 | 125016 | runs/stage10ar/v1/analyze_primary.log |
| stage10ar_optional_0 | failed | stage10ar_optional_0 | a6000 | 125017 | runs/stage10ar/v1/optional_0.log |
| stage10ar_optional_1 | failed | stage10ar_optional_1 | a6000 | 125018 | runs/stage10ar/v1/optional_1.log |
| stage10ar_figures | succeeded | stage10ar_figures | a4000 | 125019 | runs/stage10ar/v1/figures.log |
| stage10ar_figures_final | succeeded | stage10ar_figures_final | a4000 | 125020 | runs/stage10ar/v1/figures_final.log |
| stage10ar_optional_resume_0 | succeeded | stage10ar_optional_resume_0 | a6000 | 125021 | runs/stage10ar/v1/optional_resume_0.log |
| stage10ar_optional_resume_1 | succeeded | stage10ar_optional_resume_1 | a6000 | 125022 | runs/stage10ar/v1/optional_resume_1.log |
| stage10ar_analyze_optional | succeeded | stage10ar_analyze_optional | a4000 | 125023 | runs/stage10ar/v1/analyze_optional.log |
| stage10ar_finalize | succeeded | stage10ar_finalize | a4000 | 125024 | runs/stage10ar/v1/finalize.log |
| stage10b_prepare | failed | stage10b_prepare | a4000 | 125161 | runs/stage10b/v1/prepare.log |
| stage10b_prepare_v2 | succeeded | stage10b_prepare_v2 | a4000 | 125167 | runs/stage10b/v1/prepare_v2.log |
| stage10b_reaccess | succeeded | stage10b_reaccess | a4000 | 125271 | runs/stage10b/v1/reaccess.log |
| stage10b_passive_repair | succeeded | stage10b_passive_repair | a6000 | 125272 | runs/stage10b/v1/passive_repair.log |
| stage10b_finalize | succeeded | stage10b_finalize | a4000 | 125277 | runs/stage10b/v1/finalize.log |
| stage10b_presentation | succeeded | stage10b_presentation | a4000 | 125279 | runs/stage10b/v1/presentation.log |
| stage10c_validate | succeeded | stage10c_validate | a6000 | 125309 | runs/stage10c/v1/validate.log |
| stage10c_primary_0 | succeeded | stage10c_primary_0 | a6000 | 125314 | runs/stage10c/v1/primary_0.log |
| stage10c_primary_1 | succeeded | stage10c_primary_1 | a6000 | 125315 | runs/stage10c/v1/primary_1.log |
| stage10c_collect_primary | failed | stage10c_collect_primary | a4000 | 125320 | runs/stage10c/v1/collect_primary.log |
| stage10c_analyze_primary | succeeded | stage10c_analyze_primary | a4000 | 125329 | runs/stage10c/v1/analyze_primary.log |
| stage10c_finalize | succeeded | stage10c_finalize | a4000 | 125332 | runs/stage10c/v1/finalize.log |
| stage10c_figure_finalize | succeeded | stage10c_figure_finalize | a4000 | 125333 | runs/stage10c/v1/figure_finalize.log |
| stage11a_prepare | succeeded | stage11a_prepare | a4000 | 125480 | runs/stage11a/v1/prepare.log |
| stage11a_freeze_native | succeeded | stage11a_freeze_native | a4000 | 125487 | runs/stage11a/v1/freeze_native.log |
| stage11a_probe_instruct_a | failed | stage11a_probe | a6000 | 125488 | runs/stage11a/v1/probe_instruct_a.log |
| stage11a_probe_thinking_a | failed | stage11a_probe | a6000 | 125489 | runs/stage11a/v1/probe_thinking_a.log |
| stage11a_probe_instruct_b | succeeded | stage11a_probe | a6000 | 125491 | runs/stage11a/v1/probe_instruct_b.log |
| stage11a_probe_thinking_b | succeeded | stage11a_probe | a6000 | 125492 | runs/stage11a/v1/probe_thinking_b.log |
| stage11a_probe_review_prep | succeeded | stage11a_probe_review_prep | a4000 | 125531 | runs/stage11a/v1/probe_review_prep/slurm.log |
| stage11a_census_join | succeeded | stage11a_census_join | a4000 | 125532 | runs/stage11a/v1/census_join/slurm.log |
| stage11a_census_analysis | succeeded | stage11a_census_analysis | a4000 | 125533 | runs/stage11a/v1/census_analysis/slurm.log |
| stage11a_final_artifacts | succeeded | stage11a_final_artifacts | a4000 | 125534 | runs/stage11a/v1/final_artifacts/slurm.log |
| stage11b_preflight | failed | stage11b_preflight | a6000 | 125676 | runs/stage11b/v1/preflight/slurm.log |
| stage11b_preflight_repaired | succeeded | stage11b_preflight_repaired | a6000 | 125689 | runs/stage11b/v1/preflight_repaired/slurm.log |
| stage11b_discovery_instruct | cancelled | stage11b_discovery_instruct | a6000 | 125690 | runs/stage11b/v1/discovery_instruct/slurm.log |
| stage11b_discovery_thinking | cancelled | stage11b_discovery_thinking | a6000 | 125691 | runs/stage11b/v1/discovery_thinking/slurm.log |
| stage11b_cache_diagnostic | succeeded | stage11b_cache_diagnostic | a6000 | 125707 | runs/stage11b/v1/cache_diagnostic/slurm.log |
| stage11b_feasible_instruct_0 | succeeded | stage11b_feasible_instruct_0 | a6000 | 125733 | runs/stage11b/v1/feasible_instruct_0/slurm.log |
| stage11b_feasible_thinking_0 | cancelled | stage11b_feasible_thinking_0 | a6000 | 125771 | runs/stage11b/v1/feasible_thinking_0/slurm.log |
| stage11b_feasible_instruct_1 | cancelled | stage11b_feasible_instruct_1 | a6000 | 125772 | runs/stage11b/v1/feasible_instruct_1/slurm.log |
| stage11b_feasible_thinking_1 | cancelled | stage11b_feasible_thinking_1 | a6000 | 125784 | runs/stage11b/v1/feasible_thinking_1/slurm.log |
| stage11b_batch_single_validation | succeeded | stage11b_batch_single_validation | a6000 | 125801 | runs/stage11b/v1/batch_single_validation/slurm.log |
| stage11c_cap_thinking | failed | stage11c_cap_thinking | a6000 | 125937 | runs/stage11c/v1/cap_thinking/slurm.log |
| stage11c_cap_instruct | succeeded | stage11c_cap_instruct | a6000 | 125938 | runs/stage11c/v1/cap_instruct/slurm.log |
| stage11c_calretry1_thinking_0 | succeeded | stage11c_calretry1_thinking_0 | a6000 | 125952 | runs/stage11c/v1/calretry1_thinking_0/slurm.log |
| stage11c_calretry1_thinking_1 | succeeded | stage11c_calretry1_thinking_1 | a6000 | 125953 | runs/stage11c/v1/calretry1_thinking_1/slurm.log |
| stage11c_nativeearly_thinking_0 | succeeded | stage11c_nativeearly_thinking_0 | a6000 | 125982 | runs/stage11c/v1/nativeearly_thinking_0/slurm.log |
| stage11c_nativeearly_thinking_1 | succeeded | stage11c_nativeearly_thinking_1 | a6000 | 125984 | runs/stage11c/v1/nativeearly_thinking_1/slurm.log |
| stage11c_nativeearly_instruct_0 | succeeded | stage11c_nativeearly_instruct_0 | a6000 | 125983 | runs/stage11c/v1/nativeearly_instruct_0/slurm.log |
| stage11c_nativeearly_instruct_1 | succeeded | stage11c_nativeearly_instruct_1 | a6000 | 125985 | runs/stage11c/v1/nativeearly_instruct_1/slurm.log |
| stage11cr_known_good_thinking_0 | succeeded | stage11cr_known_good_thinking_0 | a6000 | 126072 | runs/stage11cr/v1/known_good_thinking_0/slurm.log |
| stage11cr_known_good_thinking_1 | succeeded | stage11cr_known_good_thinking_1 | a6000 | 126073 | runs/stage11cr/v1/known_good_thinking_1/slurm.log |
| stage11cr_known_good_instruct_direct_0 | succeeded | stage11cr_known_good_instruct_direct_0 | a6000 | 126070 | runs/stage11cr/v1/known_good_instruct_direct_0/slurm.log |
| stage11cr_known_good_instruct_direct_1 | succeeded | stage11cr_known_good_instruct_direct_1 | a6000 | 126071 | runs/stage11cr/v1/known_good_instruct_direct_1/slurm.log |
| stage11cr_diagnostic_thinking | succeeded | stage11cr_diagnostic_thinking | a6000 | 126074 | runs/stage11cr/v1/diagnostic_thinking/slurm.log |
| stage11cr_diagnostic_instruct_direct | succeeded | stage11cr_diagnostic_instruct_direct | a6000 | 126075 | runs/stage11cr/v1/diagnostic_instruct_direct/slurm.log |
| stage11cr_nonprimary_thinking_0 | succeeded | stage11cr_nonprimary_thinking_0 | a6000 | 126100 | runs/stage11cr/v1/nonprimary_thinking_0/slurm.log |
| stage11cr_nonprimary_thinking_1 | succeeded | stage11cr_nonprimary_thinking_1 | a6000 | 126101 | runs/stage11cr/v1/nonprimary_thinking_1/slurm.log |
| stage11cr_nonprimary_thinking_2 | succeeded | stage11cr_nonprimary_thinking_2 | a6000 | 126102 | runs/stage11cr/v1/nonprimary_thinking_2/slurm.log |
| stage11cr_nonprimary_thinking_3 | succeeded | stage11cr_nonprimary_thinking_3 | a6000 | 126103 | runs/stage11cr/v1/nonprimary_thinking_3/slurm.log |
| stage11cr_nonprimary_instruct_direct_0 | succeeded | stage11cr_nonprimary_instruct_direct_0 | a6000 | 126098 | runs/stage11cr/v1/nonprimary_instruct_direct_0/slurm.log |
| stage11cr_nonprimary_instruct_direct_1 | succeeded | stage11cr_nonprimary_instruct_direct_1 | a6000 | 126099 | runs/stage11cr/v1/nonprimary_instruct_direct_1/slurm.log |
| stage11cr_nonprimary_instruct_direct_2 | succeeded | stage11cr_nonprimary_instruct_direct_2 | a6000 | 126104 | runs/stage11cr/v1/nonprimary_instruct_direct_2/slurm.log |
| stage11cr_nonprimary_instruct_direct_3 | succeeded | stage11cr_nonprimary_instruct_direct_3 | a6000 | 126105 | runs/stage11cr/v1/nonprimary_instruct_direct_3/slurm.log |
| qwen3official_sanity_official_instruct_direct | failed | qwen3official_sanity_official_instruct_direct | a6000 | 126162 | runs/qwen3vl_official_eval/v1/sanity_official_instruct_direct/slurm.log |
| qwen3official_sanity_official_thinking | failed | qwen3official_sanity_official_thinking | a6000 | 126163 | runs/qwen3vl_official_eval/v1/sanity_official_thinking/slurm.log |
| qwen3official_sanity_retry1_official_instruct_direct | succeeded | qwen3official_sanity_retry1_official_instruct_direct | a6000 | 126167 | runs/qwen3vl_official_eval/v1/sanity_retry1_official_instruct_direct/slurm.log |
| qwen3official_sanity_retry1_official_thinking | succeeded | qwen3official_sanity_retry1_official_thinking | a6000 | 126168 | runs/qwen3vl_official_eval/v1/sanity_retry1_official_thinking/slurm.log |
| stage12a_technical_v1_0 | failed | stage12a_technical_v1_0 | a6000 | 127229 | runs/stage12a/v1/technical_v1_0/slurm.log |
| stage12a_technical_v2_0 | succeeded | stage12a_technical_v2_0 | a6000 | 127259 | runs/stage12a/v1/technical_v2_0/slurm.log |
| stage12ar_development_D_0 | succeeded | stage12ar_development_D_0 | a6000 | 127373 | runs/stage12ar/v1/development_D_0/slurm.log |
| stage12b_technical_0 | succeeded | stage12b_technical_0 | a6000 | 127607 | runs/stage12b/v1/technical_0/slurm.log |
| stage12b_technical_1 | succeeded | stage12b_technical_1 | a6000 | 127608 | runs/stage12b/v1/technical_1/slurm.log |
| stage12br_validation_0 | succeeded | stage12br_validation_0 | a6000 | 127673 | runs/stage12br/v1/validation_0/slurm.log |
| stage12br_validation_1 | succeeded | stage12br_validation_1 | a6000 | 127674 | runs/stage12br/v1/validation_1/slurm.log |
| stage12bs_remaining_0 | succeeded | stage12bs_remaining_0 | a6000 | 127732 | runs/stage12bs/v1/remaining_0/slurm.log |
| stage12bs_remaining_1 | succeeded | stage12bs_remaining_1 | a6000 | 127733 | runs/stage12bs/v1/remaining_1/slurm.log |
| stage12bs_remaining_2 | succeeded | stage12bs_remaining_2 | a6000 | 127734 | runs/stage12bs/v1/remaining_2/slurm.log |
| stage12bs_remaining_3 | succeeded | stage12bs_remaining_3 | a6000 | 127735 | runs/stage12bs/v1/remaining_3/slurm.log |
| stage12c_sanity_0 | succeeded | stage12c_sanity_0 | a6000 | 128009 | runs/stage12c/v1/sanity_0/slurm.log |
| stage12c_sanity_1 | succeeded | stage12c_sanity_1 | a6000 | 128010 | runs/stage12c/v1/sanity_1/slurm.log |
| stage12cr_cot_0 | succeeded | stage12cr_cot_0 | a6000 | 128077 | runs/stage12cr/v1/cot_0/slurm.log |
| stage12cr_cot_1 | succeeded | stage12cr_cot_1 | a6000 | 128078 | runs/stage12cr/v1/cot_1/slurm.log |
| stage12cr_cot_2 | succeeded | stage12cr_cot_2 | a6000 | 128079 | runs/stage12cr/v1/cot_2/slurm.log |
| stage12cr_same12_0 | succeeded | stage12cr_same12_0 | a6000 | 128080 | runs/stage12cr/v1/same12_0/slurm.log |
| stage12cr_fresh12_0 | succeeded | stage12cr_fresh12_0 | a6000 | 128156 | runs/stage12cr/v1/fresh12_0/slurm.log |
| stage12ts_remaining_0 | succeeded | stage12ts_remaining_0 | a6000 | 128758 | runs/stage12ts/v1/remaining_0/slurm.log |
| stage12ts_remaining_1 | succeeded | stage12ts_remaining_1 | a6000 | 128759 | runs/stage12ts/v1/remaining_1/slurm.log |
| stage12ts_remaining_2 | succeeded | stage12ts_remaining_2 | a6000 | 128760 | runs/stage12ts/v1/remaining_2/slurm.log |
| stage12us_technical_0 | succeeded | stage12us_technical_0 | a6000 | 129225 | runs/stage12us/v1/technical_0/slurm.log |
| stage12us_technical_1 | succeeded | stage12us_technical_1 | a6000 | 129226 | runs/stage12us/v1/technical_1/slurm.log |
| stage12us_science_0 | succeeded | stage12us_science_0 | a6000 | 129249 | runs/stage12us/v1/science_0/slurm.log |
| stage12us_science_1 | succeeded | stage12us_science_1 | a6000 | 129250 | runs/stage12us/v1/science_1/slurm.log |
| stage12us_science_2 | succeeded | stage12us_science_2 | a6000 | 129251 | runs/stage12us/v1/science_2/slurm.log |
| stage12us_science_3 | succeeded | stage12us_science_3 | a6000 | 129252 | runs/stage12us/v1/science_3/slurm.log |
| stage12us_science_4 | succeeded | stage12us_science_4 | a6000 | 129253 | runs/stage12us/v1/science_4/slurm.log |
| stage12us_science_5 | succeeded | stage12us_science_5 | a6000 | 129254 | runs/stage12us/v1/science_5/slurm.log |
| stage12uswatch_receipts | succeeded | stage12uswatch_receipts | a6000 | 129255 | runs/stage12us/v1/observer/slurm.log |
| stage12vs_phaseA_0 | succeeded | stage12vs_phaseA_0 | a6000 | 129295 | runs/stage12vs/v1/phaseA_0/slurm.log |
| stage12vs_phaseA_1 | succeeded | stage12vs_phaseA_1 | a6000 | 129296 | runs/stage12vs/v1/phaseA_1/slurm.log |
| stage12vswatch_receipts | cancelled | stage12vswatch_receipts | a6000 | 129297 | runs/stage12vs/v1/observer/slurm.log |
| stage12vswatch_receipts_node03 | cancelled | stage12vswatch_receipts_node03 | a6000 | 129299 | runs/stage12vs/v1/observer_node03/slurm.log |
| stage12vs_phaseB1_0 | succeeded | stage12vs_phaseB1_0 | a6000 | 129427 | runs/stage12vs/v1/phaseB1_0/slurm.log |
| stage12vs_phaseB2_0 | succeeded | stage12vs_phaseB2_0 | a6000 | 129654 | runs/stage12vs/v1/phaseB2_0/slurm.log |
| stage12vswatch_receipts_oct01 | running | stage12vswatch_receipts_oct01 | a6000 | 129656 | runs/stage12vs/v1/observer_oct01/slurm.log |
| stage12vs_phaseB3_0 | succeeded | stage12vs_phaseB3_0 | a6000 | 129672 | runs/stage12vs/v1/phaseB3_0/slurm.log |
| stage12vs_phaseB4_0 | succeeded | stage12vs_phaseB4_0 | a6000 | 129675 | runs/stage12vs/v1/phaseB4_0/slurm.log |
| stage12vs_phaseB5_0 | succeeded | stage12vs_phaseB5_0 | a6000 | 129709 | runs/stage12vs/v1/phaseB5_0/slurm.log |
| stage12vswatch_receipts_oct01_successor | succeeded | stage12vswatch_receipts_oct01_successor | a6000 | 129710 | runs/stage12vs/v1/observer_oct01_successor/slurm.log |
| stage12vs_phaseB6_0 | succeeded | stage12vs_phaseB6_0 | a6000 | 129859 | runs/stage12vs/v1/phaseB6_0/slurm.log |
| stage12vs_phaseB7_0 | succeeded | stage12vs_phaseB7_0 | a6000 | 129870 | runs/stage12vs/v1/phaseB7_0/slurm.log |
| stage12vs_adjacentT_0 | succeeded | stage12vs_adjacentT_0 | a6000 | 129900 | runs/stage12vs/v1/adjacentT_0/slurm.log |
| stage12vs_adjacentT_1 | succeeded | stage12vs_adjacentT_1 | a6000 | 129901 | runs/stage12vs/v1/adjacentT_1/slurm.log |
| stage12vs_contentC_0 | succeeded | stage12vs_contentC_0 | a6000 | 129902 | runs/stage12vs/v1/contentC_0/slurm.log |
| stage12vs_contentC_1 | succeeded | stage12vs_contentC_1 | a6000 | 129903 | runs/stage12vs/v1/contentC_1/slurm.log |
| stage12vswatch_receipts_oct02_successor | cancelled | stage12vswatch_receipts_oct02_successor | a6000 | 129904 | runs/stage12vs/v1/observer_oct02_successor/slurm.log |
| stage12vs_optionalE_0 | succeeded | stage12vs_optionalE_0 | a6000 | 129969 | runs/stage12vs/v1/optionalE_0/slurm.log |
| stage12ws_phaseA_0 | succeeded | stage12ws_phaseA_0 | a6000 | 130059 | runs/stage12ws/v1/phaseA_0/slurm.log |
| stage12ws_phaseA_1 | succeeded | stage12ws_phaseA_1 | a6000 | 130060 | runs/stage12ws/v1/phaseA_1/slurm.log |
| stage12ws_phaseA_2 | succeeded | stage12ws_phaseA_2 | a6000 | 130061 | runs/stage12ws/v1/phaseA_2/slurm.log |
| stage12ws_phaseA_3 | succeeded | stage12ws_phaseA_3 | a6000 | 130062 | runs/stage12ws/v1/phaseA_3/slurm.log |
| stage12wswatch_receipts | failed | stage12wswatch_receipts | a6000 | 130063 | runs/stage12ws/v1/observer/slurm.log |
| stage12ws_phaseB_0 | succeeded | stage12ws_phaseB_0 | a6000 | 130097 | runs/stage12ws/v1/phaseB_0/slurm.log |
| stage12ws_phaseB_1 | succeeded | stage12ws_phaseB_1 | a6000 | 130098 | runs/stage12ws/v1/phaseB_1/slurm.log |
| stage12ws_phaseB_2 | succeeded | stage12ws_phaseB_2 | a6000 | 130099 | runs/stage12ws/v1/phaseB_2/slurm.log |
| stage12ws_phaseB_3 | succeeded | stage12ws_phaseB_3 | a6000 | 130100 | runs/stage12ws/v1/phaseB_3/slurm.log |
| stage12ws_phaseC_0 | succeeded | stage12ws_phaseC_0 | a6000 | 130138 | runs/stage12ws/v1/phaseC_0/slurm.log |
| stage12ws_phaseC_1 | failed | stage12ws_phaseC_1 | a6000 | 130139 | runs/stage12ws/v1/phaseC_1/slurm.log |
| stage12ws_phaseC_2 | failed | stage12ws_phaseC_2 | a6000 | 130140 | runs/stage12ws/v1/phaseC_2/slurm.log |
| stage12ws_phaseC_3 | failed | stage12ws_phaseC_3 | a6000 | 130141 | runs/stage12ws/v1/phaseC_3/slurm.log |
| stage12wshealth_resume1 | succeeded | stage12wshealth_resume1 | a6000 | 130200 | runs/stage12ws/v1/health_resume1/slurm.log |
| stage12ws_resume_C_first_attempts_0 | succeeded | stage12ws_resume_C_first_attempts_0 | a6000 | 130892 | runs/stage12ws/v1/resume_C_first_attempts_0/slurm.log |
| stage12ws_resume_D01_0 | succeeded | stage12ws_resume_D01_0 | a6000 | 130897 | runs/stage12ws/v1/resume_D01_0/slurm.log |
| stage12ws_resume_D02_0 | succeeded | stage12ws_resume_D02_0 | a6000 | 130907 | runs/stage12ws/v1/resume_D02_0/slurm.log |
| stage12ws_resume_D03_0 | succeeded | stage12ws_resume_D03_0 | a6000 | 130909 | runs/stage12ws/v1/resume_D03_0/slurm.log |
| stage12ws_resume_D04_0 | succeeded | stage12ws_resume_D04_0 | a6000 | 130910 | runs/stage12ws/v1/resume_D04_0/slurm.log |
| stage12ws_resume_D05_0 | succeeded | stage12ws_resume_D05_0 | a6000 | 130912 | runs/stage12ws/v1/resume_D05_0/slurm.log |
| stage12ws_resume_D06_0 | succeeded | stage12ws_resume_D06_0 | a6000 | 130915 | runs/stage12ws/v1/resume_D06_0/slurm.log |
| stage12ws_resume_E_0 | succeeded | stage12ws_resume_E_0 | a6000 | 130916 | runs/stage12ws/v1/resume_E_0/slurm.log |
| stage12ws_resume_E_1 | succeeded | stage12ws_resume_E_1 | a6000 | 130917 | runs/stage12ws/v1/resume_E_1/slurm.log |
| stage12ws_resume_F_0 | succeeded | stage12ws_resume_F_0 | a6000 | 130922 | runs/stage12ws/v1/resume_F_0/slurm.log |
| stage12ws_resume_F_1 | succeeded | stage12ws_resume_F_1 | a6000 | 130923 | runs/stage12ws/v1/resume_F_1/slurm.log |
| vr_stage12xs_v2_A_0 | succeeded | vr_stage12xs_v2_A_0 | a6000 | 131777 | runs/stage12xs/v2/A_0/slurm.log |
| vr_stage12xs_v2_A_1 | succeeded | vr_stage12xs_v2_A_1 | a6000 | 131778 | runs/stage12xs/v2/A_1/slurm.log |
| vr_stage12xs_v2_A_2 | succeeded | vr_stage12xs_v2_A_2 | a6000 | 131779 | runs/stage12xs/v2/A_2/slurm.log |
| vr_stage12xs_v2_A_3 | succeeded | vr_stage12xs_v2_A_3 | a6000 | 131780 | runs/stage12xs/v2/A_3/slurm.log |
| vr_stage12xs_v2_B_0 | succeeded | vr_stage12xs_v2_B_0 | a6000 | 132190 | runs/stage12xs/v2/B_0/slurm.log |
| vr_stage12xs_v2_B_1 | succeeded | vr_stage12xs_v2_B_1 | a6000 | 132191 | runs/stage12xs/v2/B_1/slurm.log |
| vr_stage12xs_v2_B_2 | succeeded | vr_stage12xs_v2_B_2 | a6000 | 132192 | runs/stage12xs/v2/B_2/slurm.log |
| vr_stage12xs_v2_B_3 | succeeded | vr_stage12xs_v2_B_3 | a6000 | 132193 | runs/stage12xs/v2/B_3/slurm.log |
| vr_stage12ys_v1_A_0 | succeeded | vr_stage12ys_v1_A_0 | a6000 | 132663 | runs/stage12ys/v1/A_0/slurm.log |
| vr_stage12ys_v1_A_1 | succeeded | vr_stage12ys_v1_A_1 | a6000 | 132664 | runs/stage12ys/v1/A_1/slurm.log |
| vr_stage12ys_v1_A_2 | succeeded | vr_stage12ys_v1_A_2 | a6000 | 132665 | runs/stage12ys/v1/A_2/slurm.log |
| vr_stage12ys_v1_A_3 | succeeded | vr_stage12ys_v1_A_3 | a6000 | 132666 | runs/stage12ys/v1/A_3/slurm.log |
| vr_stage12ys_v1_A_4 | succeeded | vr_stage12ys_v1_A_4 | a6000 | 132667 | runs/stage12ys/v1/A_4/slurm.log |
| vr_stage12ys_v1_A_5 | succeeded | vr_stage12ys_v1_A_5 | a6000 | 132668 | runs/stage12ys/v1/A_5/slurm.log |
| vr_stage12ys_v1_A_6 | succeeded | vr_stage12ys_v1_A_6 | a6000 | 132669 | runs/stage12ys/v1/A_6/slurm.log |
| vr_stage12ys_v1_A_7 | succeeded | vr_stage12ys_v1_A_7 | a6000 | 132670 | runs/stage12ys/v1/A_7/slurm.log |
| vr_stage12ys_v1_B_0 | succeeded | vr_stage12ys_v1_B_0 | a6000 | 132676 | runs/stage12ys/v1/B_0/slurm.log |
| vr_stage12ys_v1_B_1 | succeeded | vr_stage12ys_v1_B_1 | a6000 | 132677 | runs/stage12ys/v1/B_1/slurm.log |
| vr_stage12ys_v1_B_2 | succeeded | vr_stage12ys_v1_B_2 | a6000 | 132678 | runs/stage12ys/v1/B_2/slurm.log |
| vr_stage12ys_v1_B_3 | succeeded | vr_stage12ys_v1_B_3 | a6000 | 132679 | runs/stage12ys/v1/B_3/slurm.log |
| vr_stage12ys_v1_B_4 | succeeded | vr_stage12ys_v1_B_4 | a6000 | 132680 | runs/stage12ys/v1/B_4/slurm.log |
| vr_stage12ys_v1_B_5 | succeeded | vr_stage12ys_v1_B_5 | a6000 | 132681 | runs/stage12ys/v1/B_5/slurm.log |
| vr_stage12ys_v1_B_6 | succeeded | vr_stage12ys_v1_B_6 | a6000 | 132682 | runs/stage12ys/v1/B_6/slurm.log |
| vr_stage12ys_v1_B_7 | succeeded | vr_stage12ys_v1_B_7 | a6000 | 132683 | runs/stage12ys/v1/B_7/slurm.log |
| vr_stage12ys_v1_C_0 | succeeded | vr_stage12ys_v1_C_0 | a6000 | 132745 | runs/stage12ys/v1/C_0/slurm.log |
| vr_stage12ys_v1_C_1 | succeeded | vr_stage12ys_v1_C_1 | a6000 | 132746 | runs/stage12ys/v1/C_1/slurm.log |
| vr_stage12ys_v1_C_2 | succeeded | vr_stage12ys_v1_C_2 | a6000 | 132747 | runs/stage12ys/v1/C_2/slurm.log |
| vr_stage12ys_v1_C_3 | succeeded | vr_stage12ys_v1_C_3 | a6000 | 132748 | runs/stage12ys/v1/C_3/slurm.log |
| vr_stage13a_v1_P_0 | succeeded | vr_stage13a_v1_P_0 | a6000 | 133777 | runs/stage13a/v1/P_0/slurm.log |
| vr_stage13a_v1_P_1 | succeeded | vr_stage13a_v1_P_1 | a6000 | 133778 | runs/stage13a/v1/P_1/slurm.log |
| vr_stage13a_v1_P_2 | succeeded | vr_stage13a_v1_P_2 | a6000 | 133779 | runs/stage13a/v1/P_2/slurm.log |
| vr_stage13a_v1_P_3 | succeeded | vr_stage13a_v1_P_3 | a6000 | 133780 | runs/stage13a/v1/P_3/slurm.log |
| vr_stage13a_v1_P_4 | succeeded | vr_stage13a_v1_P_4 | a6000 | 133781 | runs/stage13a/v1/P_4/slurm.log |
| vr_stage13a_v1_P_5 | failed | vr_stage13a_v1_P_5 | a6000 | 133782 | runs/stage13a/v1/P_5/slurm.log |
| vr_stage13a_v1_P_6 | succeeded | vr_stage13a_v1_P_6 | a6000 | 133783 | runs/stage13a/v1/P_6/slurm.log |
| vr_stage13a_v1_P_7 | succeeded | vr_stage13a_v1_P_7 | a6000 | 133784 | runs/stage13a/v1/P_7/slurm.log |
| vr_stage13a_v1_P_recovery1 | succeeded | vr_stage13a_v1_P_recovery1 | a6000 | 133885 | runs/stage13a/v1/P_recovery1/slurm.log |
| vr_stage13b_v1_technical_2B_I_0 | succeeded | vr_stage13b_v1_technical_2B_I_0 | a6000 | 134496 | runs/stage13b/v1/technical_2B_I_0/slurm.log |
| vr_stage13b_v1_technical_2B_T_0 | succeeded | vr_stage13b_v1_technical_2B_T_0 | a6000 | 134497 | runs/stage13b/v1/technical_2B_T_0/slurm.log |
| vr_stage13b_v1_technical_4B_I_0 | succeeded | vr_stage13b_v1_technical_4B_I_0 | a6000 | 134498 | runs/stage13b/v1/technical_4B_I_0/slurm.log |
| vr_stage13b_v1_technical_4B_T_0 | succeeded | vr_stage13b_v1_technical_4B_T_0 | a6000 | 134499 | runs/stage13b/v1/technical_4B_T_0/slurm.log |
| vr_stage13b_v1_technical_8B_I_0 | succeeded | vr_stage13b_v1_technical_8B_I_0 | a6000 | 134500 | runs/stage13b/v1/technical_8B_I_0/slurm.log |
| vr_stage13b_v1_technical_8B_T_0 | succeeded | vr_stage13b_v1_technical_8B_T_0 | a6000 | 134501 | runs/stage13b/v1/technical_8B_T_0/slurm.log |
| vr_stage13b_v1_equal_initial8_2B_I_0 | succeeded | vr_stage13b_v1_equal_initial8_2B_I_0 | a6000 | 134547 | runs/stage13b/v1/equal_initial8_2B_I_0/slurm.log |
| vr_stage13b_v1_equal_initial8_2B_I_1 | succeeded | vr_stage13b_v1_equal_initial8_2B_I_1 | a6000 | 134548 | runs/stage13b/v1/equal_initial8_2B_I_1/slurm.log |
| vr_stage13b_v1_equal_initial8_2B_T_0 | succeeded | vr_stage13b_v1_equal_initial8_2B_T_0 | a6000 | 134549 | runs/stage13b/v1/equal_initial8_2B_T_0/slurm.log |
| vr_stage13b_v1_equal_initial8_2B_T_1 | succeeded | vr_stage13b_v1_equal_initial8_2B_T_1 | a6000 | 134550 | runs/stage13b/v1/equal_initial8_2B_T_1/slurm.log |
| vr_stage13b_v1_equal_initial8_8B_I_0 | succeeded | vr_stage13b_v1_equal_initial8_8B_I_0 | a6000 | 134551 | runs/stage13b/v1/equal_initial8_8B_I_0/slurm.log |
| vr_stage13b_v1_equal_initial8_8B_I_1 | succeeded | vr_stage13b_v1_equal_initial8_8B_I_1 | a6000 | 134552 | runs/stage13b/v1/equal_initial8_8B_I_1/slurm.log |
| vr_stage13b_v1_equal_initial8_8B_T_0 | cancelled | vr_stage13b_v1_equal_initial8_8B_T_0 | a6000 | 134553 | runs/stage13b/v1/equal_initial8_8B_T_0/slurm.log |
| vr_stage13b_v1_equal_initial8_8B_T_1 | cancelled | vr_stage13b_v1_equal_initial8_8B_T_1 | a6000 | 134554 | runs/stage13b/v1/equal_initial8_8B_T_1/slurm.log |
| vr_stage13c_v1_technical_buffer_T_0 | failed | vr_stage13c_v1_technical_buffer_T_0 | a6000 | 134926 | runs/stage13c/v1/technical_buffer_T_0/slurm.log |
| vr_stage13c_v1_technical_buffer_T_1 | failed | vr_stage13c_v1_technical_buffer_T_1 | a6000 | 134927 | runs/stage13c/v1/technical_buffer_T_1/slurm.log |
| vr_stage13c_v1_technical_buffer_loader_repair_T_0 | cancelled | vr_stage13c_v1_technical_buffer_loader_repair_T_0 | a6000 | 134932 | runs/stage13c/v1/technical_buffer_loader_repair_T_0/slurm.log |
| vr_stage13c_v1_technical_buffer_loader_repair_T_1 | succeeded | vr_stage13c_v1_technical_buffer_loader_repair_T_1 | a6000 | 134933 | runs/stage13c/v1/technical_buffer_loader_repair_T_1/slurm.log |
| vr_stage13d_v1_technical_buffer_T_0 | succeeded | vr_stage13d_v1_technical_buffer_T_0 | a6000 | 134964 | runs/stage13d/v1/technical_buffer_T_0/slurm.log |
| vr_stage13d_v1_semantic_initial8_I_0 | succeeded | vr_stage13d_v1_semantic_initial8_I_0 | a6000 | 134965 | runs/stage13d/v1/semantic_initial8_I_0/slurm.log |
| vr_stage13d_v1_scientific_buffer_T_0 | succeeded | vr_stage13d_v1_scientific_buffer_T_0 | a6000 | 134972 | runs/stage13d/v1/scientific_buffer_T_0/slurm.log |
| vr_stage13d_v1_scientific_buffer_T_1 | succeeded | vr_stage13d_v1_scientific_buffer_T_1 | a6000 | 134973 | runs/stage13d/v1/scientific_buffer_T_1/slurm.log |
| vr_stage13d_v1_semantic_remaining_I_0 | succeeded | vr_stage13d_v1_semantic_remaining_I_0 | a6000 | 135193 | runs/stage13d/v1/semantic_remaining_I_0/slurm.log |
| vr_stage13d_v1_semantic_remaining_I_1 | succeeded | vr_stage13d_v1_semantic_remaining_I_1 | a6000 | 135194 | runs/stage13d/v1/semantic_remaining_I_1/slurm.log |
| vr_stage13d_v1_semantic_remaining_I_2 | succeeded | vr_stage13d_v1_semantic_remaining_I_2 | a6000 | 135195 | runs/stage13d/v1/semantic_remaining_I_2/slurm.log |
| vr_stage13d_v1_semantic_remaining_I_3 | succeeded | vr_stage13d_v1_semantic_remaining_I_3 | a6000 | 135196 | runs/stage13d/v1/semantic_remaining_I_3/slurm.log |
| vr_stage13d_v1_semantic_remaining_I_4 | succeeded | vr_stage13d_v1_semantic_remaining_I_4 | a6000 | 135197 | runs/stage13d/v1/semantic_remaining_I_4/slurm.log |
| vr_stage13d_v1_semantic_remaining_I_5 | succeeded | vr_stage13d_v1_semantic_remaining_I_5 | a6000 | 135198 | runs/stage13d/v1/semantic_remaining_I_5/slurm.log |
| vr_stage13d_v1_semantic_remaining_I_6 | succeeded | vr_stage13d_v1_semantic_remaining_I_6 | a6000 | 135199 | runs/stage13d/v1/semantic_remaining_I_6/slurm.log |
| vr_stage13d_v1_semantic_remaining_I_7 | succeeded | vr_stage13d_v1_semantic_remaining_I_7 | a6000 | 135200 | runs/stage13d/v1/semantic_remaining_I_7/slurm.log |
| stage14a_source_audit | succeeded | stage14a_source_audit | a6000 | 135334 | runs/stage14a/source_audit.log |
| stage14a_history_v2 | succeeded | stage14a_history_v2 | a6000 | 135380 | runs/stage14a/history_v2.log |
| stage14a_final_preservation | succeeded | stage14a_final_preservation | a6000 | 135757 | runs/stage14a/final_preservation.log |
| vr_stage14b_preflight_I_0_20261005T065213 | failed | vr_stage14b_preflight_I_0_20261005T065213 | a6000 | 136000 | runs/stage14b/preflight_I_0_20261005T065213/slurm.log |
| vr_stage14b_preflight_T_0_20261005T065213 | failed | vr_stage14b_preflight_T_0_20261005T065213 | a6000 | 136001 | runs/stage14b/preflight_T_0_20261005T065213/slurm.log |
| vr_stage14b_preflight_I_0_20261005T070009 | succeeded | vr_stage14b_preflight_I_0_20261005T070009 | a6000 | 136015 | runs/stage14b/preflight_I_0_20261005T070009/slurm.log |
| vr_stage14b_preflight_T_0_20261005T070009 | succeeded | vr_stage14b_preflight_T_0_20261005T070009 | a6000 | 136016 | runs/stage14b/preflight_T_0_20261005T070009/slurm.log |
| vr_s14b_controller_20261005 | failed | vr_s14b_controller_20261005 | a6000 | 136019 | runs/stage14b/coordinator/slurm.log |
| vr_stage14b_main_I_0_20261005T083622 | succeeded | vr_stage14b_main_I_0_20261005T083622 | a6000 | 136129 | runs/stage14b/main_I_0_20261005T083622/slurm.log |
| vr_stage14b_main_I_1_20261005T083622 | succeeded | vr_stage14b_main_I_1_20261005T083622 | a6000 | 136130 | runs/stage14b/main_I_1_20261005T083622/slurm.log |
| vr_stage14b_main_I_2_20261005T083622 | succeeded | vr_stage14b_main_I_2_20261005T083622 | a6000 | 136131 | runs/stage14b/main_I_2_20261005T083622/slurm.log |
| vr_stage14b_main_T_0_20261005T083622 | succeeded | vr_stage14b_main_T_0_20261005T083622 | a6000 | 136132 | runs/stage14b/main_T_0_20261005T083622/slurm.log |
| vr_stage14b_main_T_1_20261005T083622 | succeeded | vr_stage14b_main_T_1_20261005T083622 | a6000 | 136133 | runs/stage14b/main_T_1_20261005T083622/slurm.log |
| vr_stage14b_main_T_2_20261005T083622 | succeeded | vr_stage14b_main_T_2_20261005T083622 | a6000 | 136134 | runs/stage14b/main_T_2_20261005T083622/slurm.log |
| vr_stage14b_main_T_3_20261005T083622 | succeeded | vr_stage14b_main_T_3_20261005T083622 | a6000 | 136135 | runs/stage14b/main_T_3_20261005T083622/slurm.log |
| vr_stage14b_main_T_4_20261005T083622 | succeeded | vr_stage14b_main_T_4_20261005T083622 | a6000 | 136136 | runs/stage14b/main_T_4_20261005T083622/slurm.log |
| vr_s14b_main_observer_20261005 | running | vr_s14b_main_observer_20261005 | a6000 | 136145 | runs/stage14b/main_monitor/slurm.log |
| vr_s14b_oom_watch_20261005 | running | vr_s14b_oom_watch_20261005 | a6000 | 136205 | runs/stage14b/oom_watch/slurm.log |
| vr_s14b_oom_watch_node03_20261005 | running | vr_s14b_oom_watch_node03_20261005 | a6000 | 136206 | runs/stage14b/oom_watch_node03/slurm.log |
| vr_s14b_oom_watch_node07_20261005 | running | vr_s14b_oom_watch_node07_20261005 | a6000 | 136212 | runs/stage14b/oom_watch_node07/slurm.log |
| vr_s14b_oom_watch_after3am_20261006 | running | vr_s14b_oom_watch_after3am_20261006 | a6000 | 136370 | runs/stage14b/oom_watch_after3am_20261006/slurm.log |
| vr_s14b_oom_watch_after3am_20261007 | running | vr_s14b_oom_watch_after3am_20261007 | a6000 | 136898 | runs/stage14b/oom_watch_after3am_20261007/slurm.log |
| vr_stage14b_main_freeze_extract_i_20261006 | failed | vr_stage14b_main_freeze_extract_i_20261006 | a6000 | 137127 | runs/stage14b/vr_stage14b_main_freeze_extract_i_20261006/slurm.log |
| vr_stage14b_main_freeze_extract_i_resume_20261006 | succeeded | vr_stage14b_main_freeze_extract_i_resume_20261006 | a6000 | 137135 | runs/stage14b/vr_stage14b_main_freeze_extract_i_resume_20261006/slurm.log |
| vr_stage14b_main_extract_t_20261006a | succeeded | vr_stage14b_main_extract_t_20261006a | a6000 | 137167 | runs/stage14b/vr_stage14b_main_extract_t_20261006a/slurm.log |
| vr_stage14b_primary_20261006T0925 | succeeded | vr_stage14b_primary_20261006T0925 | a6000 | 137172 | runs/stage14b/vr_stage14b_primary_20261006T0925/slurm.log |
| vr_stage14b_secondary_20261006T0927 | succeeded | vr_stage14b_secondary_20261006T0927 | a6000 | 137174 | runs/stage14b/vr_stage14b_secondary_20261006T0927/slurm.log |
| vr_stage14b_confirmatory_I_0_20261006T092824 | succeeded | vr_stage14b_confirmatory_I_0_20261006T092824 | a6000 | 137175 | runs/stage14b/confirmatory_I_0_20261006T092824/slurm.log |
| vr_stage14b_confirmatory_I_1_20261006T092824 | succeeded | vr_stage14b_confirmatory_I_1_20261006T092824 | a6000 | 137176 | runs/stage14b/confirmatory_I_1_20261006T092824/slurm.log |
| vr_stage14b_confirmatory_T_0_20261006T092824 | succeeded | vr_stage14b_confirmatory_T_0_20261006T092824 | a6000 | 137177 | runs/stage14b/confirmatory_T_0_20261006T092824/slurm.log |
| vr_stage14b_confirmatory_T_1_20261006T092824 | succeeded | vr_stage14b_confirmatory_T_1_20261006T092824 | a6000 | 137178 | runs/stage14b/confirmatory_T_1_20261006T092824/slurm.log |
| vr_stage14b_confirmatory_T_2_20261006T092824 | succeeded | vr_stage14b_confirmatory_T_2_20261006T092824 | a6000 | 137179 | runs/stage14b/confirmatory_T_2_20261006T092824/slurm.log |
| vr_stage14b_confirmatory_T_3_20261006T092824 | succeeded | vr_stage14b_confirmatory_T_3_20261006T092824 | a6000 | 137180 | runs/stage14b/confirmatory_T_3_20261006T092824/slurm.log |
| vr_stage14b_confirmatory_T_4_20261006T092824 | succeeded | vr_stage14b_confirmatory_T_4_20261006T092824 | a6000 | 137181 | runs/stage14b/confirmatory_T_4_20261006T092824/slurm.log |
| vr_stage14b_confirmatory_T_5_20261006T092824 | succeeded | vr_stage14b_confirmatory_T_5_20261006T092824 | a6000 | 137182 | runs/stage14b/confirmatory_T_5_20261006T092824/slurm.log |
| vr_stage14b_confirmation_cpu_handoff_v1 | succeeded | vr_stage14b_confirmation_cpu_handoff_v1 | a6000 | 137183 | runs/stage14b/vr_stage14b_confirmation_cpu_handoff_v1/slurm.log |
| vr_stage14b_confirmation_T_review_prepare_v1 | succeeded | vr_stage14b_confirmation_T_review_prepare_v1 | a6000 | 138450 | runs/stage14b/vr_stage14b_confirmation_T_review_prepare_v1/slurm.log |
| vr_stage14b_confirmation_analysis_figures_v1 | succeeded | vr_stage14b_confirmation_analysis_figures_v1 | a6000 | 138468 | runs/stage14b/vr_stage14b_confirmation_analysis_figures_v1/slurm.log |
| vr_stage14b_final_closure_v2 | succeeded | vr_stage14b_final_closure_v2 | a6000 | 138485 | runs/stage14b/vr_stage14b_final_closure_v2/slurm.log |
| stage14c_g1_source_audit_20261009 | succeeded | stage14c_g1_source_audit_20261009 | a6000 | 139089 | runs/stage14c/g1_source_audit.log |
| stage14c_g1_anchor_overlap_20261009 | succeeded | stage14c_g1_anchor_overlap_20261009 | a6000 | 139093 | runs/stage14c/g1_anchor_overlap.log |
| vr_stage14c_preflight_I_0_20261009T032203 | failed | vr_stage14c_preflight_I_0_20261009T032203 | a6000 | 139200 | runs/stage14c/preflight_I_0_20261009T032203/slurm.log |
| vr_stage14c_preflight_T_0_20261009T032203 | failed | vr_stage14c_preflight_T_0_20261009T032203 | a6000 | 139201 | runs/stage14c/preflight_T_0_20261009T032203/slurm.log |
| vr_stage14c_preflight_I_0_20261009T032818 | succeeded | vr_stage14c_preflight_I_0_20261009T032818 | a6000 | 139215 | runs/stage14c/preflight_I_0_20261009T032818/slurm.log |
| vr_stage14c_preflight_T_0_20261009T032818 | succeeded | vr_stage14c_preflight_T_0_20261009T032818 | a6000 | 139216 | runs/stage14c/preflight_T_0_20261009T032818/slurm.log |
| vr_stage14c_fixed_context_replay_v1 | succeeded | vr_stage14c_fixed_context_replay_v1 | a6000 | 139234 | runs/stage14c/fixed_context_replay_v1/slurm.log |
| vr_stage14c_main_I_0_20261009T034729 | succeeded | vr_stage14c_main_I_0_20261009T034729 | a6000 | 139238 | runs/stage14c/main_I_0_20261009T034729/slurm.log |
| vr_stage14c_main_I_1_20261009T034729 | succeeded | vr_stage14c_main_I_1_20261009T034729 | a6000 | 139239 | runs/stage14c/main_I_1_20261009T034729/slurm.log |
| vr_stage14c_main_T_0_20261009T034729 | succeeded | vr_stage14c_main_T_0_20261009T034729 | a6000 | 139240 | runs/stage14c/main_T_0_20261009T034729/slurm.log |
| vr_stage14c_main_T_1_20261009T034729 | succeeded | vr_stage14c_main_T_1_20261009T034729 | a6000 | 139241 | runs/stage14c/main_T_1_20261009T034729/slurm.log |
| vr_stage14c_main_T_2_20261009T034729 | succeeded | vr_stage14c_main_T_2_20261009T034729 | a6000 | 139242 | runs/stage14c/main_T_2_20261009T034729/slurm.log |
| vr_stage14c_main_T_3_20261009T034729 | succeeded | vr_stage14c_main_T_3_20261009T034729 | a6000 | 139243 | runs/stage14c/main_T_3_20261009T034729/slurm.log |
| vr_stage14c_main_T_4_20261009T034729 | succeeded | vr_stage14c_main_T_4_20261009T034729 | a6000 | 139244 | runs/stage14c/main_T_4_20261009T034729/slurm.log |
| vr_stage14c_main_T_5_20261009T034729 | cancelled | vr_stage14c_main_T_5_20261009T034729 | a6000 | 139245 | runs/stage14c/main_T_5_20261009T034729/slurm.log |
| vr_stage14c_main_T5_node06_move_v1 | succeeded | vr_stage14c_main_T5_node06_move_v1 | a6000 | 139246 | runs/stage14c/main_T5_node06_move_v1/slurm.log |

## Run States

| exp_id | status | current_step | log | result |
|---|---|---|---|---|
| interactive_node03_2gpu_20260916 | running | Interactive GPU allocation retained; no research workload started | runs/allocations/node03_2gpu_20260916/slurm.log | runs/allocations/node03_2gpu_20260916/allocation.json |
| piqd_phase0_env_install | running | Running GPU job piqd_phase0_env_install | runs/piqd_phase0_env_install/slurm.log | outputs/piqd/env_install_result.json |
| piqd_phase0_env_install_uvcache | running | Running GPU job piqd_phase0_env_install_uvcache | runs/piqd_phase0_env_install_uvcache/slurm.log | outputs/piqd/env_install_uvcache_result.json |
| piqd_phase0_torch_cuda_check | running | Running GPU job piqd_phase0_torch_cuda_check | runs/piqd_phase0_torch_cuda_check/slurm.log | outputs/piqd/torch_cuda_slurm_check.json |
| piqd_phase0_torch_cuda_check_a4000 | running | Running GPU job piqd_phase0_torch_cuda_check_a4000 | runs/piqd_phase0_torch_cuda_check_a4000/slurm.log | outputs/piqd/torch_cuda_slurm_check.json |
| piqd_phase1_diag | running | Running GPU job piqd_phase1_diag | runs/piqd_phase1_diag/slurm.log | outputs/piqd/phase1_diag/phase1_summary.md |
| piqd_phase1_model_load | running | Running GPU job piqd_phase1_model_load | runs/piqd_phase1_model_load/slurm.log | outputs/piqd/phase1/phase1_model_loading.md |
| piqd_phase1_smoke_10 | running | Running GPU job piqd_phase1_smoke_10 | runs/piqd_phase1_smoke_10/slurm.log | outputs/piqd/phase1/phase1_summary.md |
| piqd_phase2_diag | running | Running GPU job piqd_phase2_diag | runs/piqd_phase2_diag/slurm.log | outputs/piqd/phase2_diag/phase2_summary.md |
| piqd_phase2_extract_10 | running | Running GPU job piqd_phase2_extract_10 | runs/piqd_phase2_extract_10/slurm.log | outputs/piqd/phase2/phase2_summary.md |
| qwen3official_sanity_official_instruct_direct | running | Running GPU job qwen3official_sanity_official_instruct_direct | runs/qwen3vl_official_eval/v1/sanity_official_instruct_direct/slurm.log | outputs/qwen3vl_official_eval/v1 |
| qwen3official_sanity_official_thinking | running | Running GPU job qwen3official_sanity_official_thinking | runs/qwen3vl_official_eval/v1/sanity_official_thinking/slurm.log | outputs/qwen3vl_official_eval/v1 |
| qwen3official_sanity_retry1_official_instruct_direct | running | Running GPU job qwen3official_sanity_retry1_official_instruct_direct | runs/qwen3vl_official_eval/v1/sanity_retry1_official_instruct_direct/slurm.log | outputs/qwen3vl_official_eval/v1 |
| qwen3official_sanity_retry1_official_thinking | running | Running GPU job qwen3official_sanity_retry1_official_thinking | runs/qwen3vl_official_eval/v1/sanity_retry1_official_thinking/slurm.log | outputs/qwen3vl_official_eval/v1 |
| stage10a_analyze_a | running | Running GPU job stage10a_analyze_a | runs/stage10a/v1/analyze_a.log | outputs/stage10a/v1/audit/gate_a_inference.json |
| stage10a_analyze_b | running | Running GPU job stage10a_analyze_b | runs/stage10a/v1/analyze_b.log | outputs/stage10a/v1/audit/gate_b_inference.json |
| stage10a_analyze_dominance | running | Running GPU job stage10a_analyze_dominance | runs/stage10a/v1/analyze_dominance.log | outputs/stage10a/v1/audit/dominance_v2_inference.json |
| stage10a_dominance_0 | running | Running GPU job stage10a_dominance_0 | runs/stage10a/v1/dominance_0.log | outputs/stage10a/v1/dominance/workers |
| stage10a_dominance_1 | running | Running GPU job stage10a_dominance_1 | runs/stage10a/v1/dominance_1.log | outputs/stage10a/v1/dominance/workers |
| stage10a_final_audit | running | Running GPU job stage10a_final_audit | runs/stage10a/v1/final_audit.log | outputs/stage10a/v1/audit/final_validation.json |
| stage10a_finalize | running | Running GPU job stage10a_finalize | runs/stage10a/v1/finalize.log | outputs/stage10a/v1/stage10a_summary.md |
| stage10a_gate_a_0 | running | Running GPU job stage10a_gate_a_0 | runs/stage10a/v1/gate_a_0.log | outputs/stage10a/v1/gate_a/workers |
| stage10a_gate_a_1 | running | Running GPU job stage10a_gate_a_1 | runs/stage10a/v1/gate_a_1.log | outputs/stage10a/v1/gate_a/workers |
| stage10a_gate_a_2 | running | Running GPU job stage10a_gate_a_2 | runs/stage10a/v1/gate_a_2.log | outputs/stage10a/v1/gate_a/workers |
| stage10a_gate_a_3 | running | Running GPU job stage10a_gate_a_3 | runs/stage10a/v1/gate_a_3.log | outputs/stage10a/v1/gate_a/workers |
| stage10a_gate_a_4 | running | Running GPU job stage10a_gate_a_4 | runs/stage10a/v1/gate_a_4.log | outputs/stage10a/v1/gate_a/workers |
| stage10a_gate_a_5 | running | Running GPU job stage10a_gate_a_5 | runs/stage10a/v1/gate_a_5.log | outputs/stage10a/v1/gate_a/workers |
| stage10a_gate_a_6 | running | Running GPU job stage10a_gate_a_6 | runs/stage10a/v1/gate_a_6.log | outputs/stage10a/v1/gate_a/workers |
| stage10a_gate_a_7 | running | Running GPU job stage10a_gate_a_7 | runs/stage10a/v1/gate_a_7.log | outputs/stage10a/v1/gate_a/workers |
| stage10a_gate_b_0 | running | Running GPU job stage10a_gate_b_0 | runs/stage10a/v1/gate_b_0.log | outputs/stage10a/v1/gate_b/workers |
| stage10a_gate_b_1 | running | Running GPU job stage10a_gate_b_1 | runs/stage10a/v1/gate_b_1.log | outputs/stage10a/v1/gate_b/workers |
| stage10a_gate_b_2 | running | Running GPU job stage10a_gate_b_2 | runs/stage10a/v1/gate_b_2.log | outputs/stage10a/v1/gate_b/workers |
| stage10a_gate_b_3 | running | Running GPU job stage10a_gate_b_3 | runs/stage10a/v1/gate_b_3.log | outputs/stage10a/v1/gate_b/workers |
| stage10a_prepare | running | Running GPU job stage10a_prepare | runs/stage10a/v1/prepare.log | outputs/stage10a/v1/config.json |
| stage10a_prepare_dominance | running | Running GPU job stage10a_prepare_dominance | runs/stage10a/v1/prepare_dominance.log | outputs/stage10a/v1/audit/dominance_manifest.json |
| stage10a_prepare_edits | running | Running GPU job stage10a_prepare_edits | runs/stage10a/v1/prepare_edits.log | outputs/stage10a/v1/audit/gate_b_manifest.json |
| stage10a_source_geometry | running | Running GPU job stage10a_source_geometry | runs/stage10a/v1/source_geometry.log | outputs/stage10a/v1/audit/dominance_v2_manifest.json |
| stage10a_validate | running | Running GPU job stage10a_validate | runs/stage10a/v1/validate.log | outputs/stage10a/v1/audit/technical_validation.json |
| stage10a_validate_dominance | running | Running GPU job stage10a_validate_dominance | runs/stage10a/v1/validate_dominance.log | outputs/stage10a/v1/audit/dominance_validation.json |
| stage10a_validate_r1 | running | Running GPU job stage10a_validate_r1 | runs/stage10a/v1/validate_r1.log | outputs/stage10a/v1/audit/technical_validation.json |
| stage10ar_analyze_optional | running | Running GPU job stage10ar_analyze_optional | runs/stage10ar/v1/analyze_optional.log | outputs/stage10ar/v1/stage10ar_a3_text_edit.json |
| stage10ar_analyze_primary | running | Running GPU job stage10ar_analyze_primary | runs/stage10ar/v1/analyze_primary.log | outputs/stage10ar/v1/stage10ar_primary_inference.json |
| stage10ar_figures | running | Running GPU job stage10ar_figures | runs/stage10ar/v1/figures.log | outputs/stage10ar/v1/figures |
| stage10ar_figures_final | running | Running GPU job stage10ar_figures_final | runs/stage10ar/v1/figures_final.log | outputs/stage10ar/v1/figures |
| stage10ar_finalize | running | Running GPU job stage10ar_finalize | runs/stage10ar/v1/finalize.log | outputs/stage10ar/v1/audit/final_audit.json |
| stage10ar_optional_0 | running | Running GPU job stage10ar_optional_0 | runs/stage10ar/v1/optional_0.log | outputs/stage10ar/v1/optional/workers |
| stage10ar_optional_1 | running | Running GPU job stage10ar_optional_1 | runs/stage10ar/v1/optional_1.log | outputs/stage10ar/v1/optional/workers |
| stage10ar_optional_resume_0 | running | Running GPU job stage10ar_optional_resume_0 | runs/stage10ar/v1/optional_resume_0.log | outputs/stage10ar/v1/optional/workers |
| stage10ar_optional_resume_1 | running | Running GPU job stage10ar_optional_resume_1 | runs/stage10ar/v1/optional_resume_1.log | outputs/stage10ar/v1/optional/workers |
| stage10ar_prepare | running | Running GPU job stage10ar_prepare | runs/stage10ar/v1/prepare.log | outputs/stage10ar/v1/config.json |
| stage10ar_primary_0 | running | Running GPU job stage10ar_primary_0 | runs/stage10ar/v1/primary_0.log | outputs/stage10ar/v1/primary/workers |
| stage10ar_primary_1 | running | Running GPU job stage10ar_primary_1 | runs/stage10ar/v1/primary_1.log | outputs/stage10ar/v1/primary/workers |
| stage10ar_primary_2 | running | Running GPU job stage10ar_primary_2 | runs/stage10ar/v1/primary_2.log | outputs/stage10ar/v1/primary/workers |
| stage10ar_primary_3 | running | Running GPU job stage10ar_primary_3 | runs/stage10ar/v1/primary_3.log | outputs/stage10ar/v1/primary/workers |
| stage10ar_validate | running | Running GPU job stage10ar_validate | runs/stage10ar/v1/validate.log | outputs/stage10ar/v1/audit/technical_validation.json |
| stage10b_finalize | running | Running GPU job stage10b_finalize | runs/stage10b/v1/finalize.log | outputs/stage10b/v1/audit/final_audit.json |
| stage10b_passive_repair | running | Running GPU job stage10b_passive_repair | runs/stage10b/v1/passive_repair.log | outputs/stage10b/v1/repair/complete.json |
| stage10b_prepare | running | Running GPU job stage10b_prepare | runs/stage10b/v1/prepare.log | outputs/stage10b/v1/stage10b_corpus_manifest.json |
| stage10b_prepare_v2 | running | Running GPU job stage10b_prepare_v2 | runs/stage10b/v1/prepare_v2.log | outputs/stage10b/v1/stage10b_corpus_manifest.json |
| stage10b_presentation | running | Running GPU job stage10b_presentation | runs/stage10b/v1/presentation.log | outputs/stage10b/v1/audit/final_audit.json |
| stage10b_reaccess | running | Running GPU job stage10b_reaccess | runs/stage10b/v1/reaccess.log | outputs/stage10b/v1/audit/reaccess_historical.json |
| stage10c_analyze_primary | running | Running GPU job stage10c_analyze_primary | runs/stage10c/v1/analyze_primary.log | outputs/stage10c/v1/audit/primary_inference.json |
| stage10c_collect_primary | running | Running GPU job stage10c_collect_primary | runs/stage10c/v1/collect_primary.log | outputs/stage10c/v1/audit/primary_review_packet.json |
| stage10c_figure_finalize | running | Running GPU job stage10c_figure_finalize | runs/stage10c/v1/figure_finalize.log | outputs/stage10c/v1/audit/final_audit.json |
| stage10c_finalize | running | Running GPU job stage10c_finalize | runs/stage10c/v1/finalize.log | outputs/stage10c/v1/audit/final_audit.json |
| stage10c_primary_0 | running | Running GPU job stage10c_primary_0 | runs/stage10c/v1/primary_0.log | outputs/stage10c/v1/primary |
| stage10c_primary_1 | running | Running GPU job stage10c_primary_1 | runs/stage10c/v1/primary_1.log | outputs/stage10c/v1/primary |
| stage10c_validate | running | Running GPU job stage10c_validate | runs/stage10c/v1/validate.log | outputs/stage10c/v1/stage10c_technical_validation.json |
| stage11a_census_analysis | running | Running GPU job stage11a_census_analysis | runs/stage11a/v1/census_analysis/slurm.log | outputs/stage11a/v1/stage11a_go_nogo_decision.json |
| stage11a_census_join | running | Running GPU job stage11a_census_join | runs/stage11a/v1/census_join/slurm.log | outputs/stage11a/v1/audit/census_joined.json |
| stage11a_final_artifacts | running | Running GPU job stage11a_final_artifacts | runs/stage11a/v1/final_artifacts/slurm.log | outputs/stage11a/v1/audit/completion_audit.json |
| stage11a_freeze_native | running | Running GPU job stage11a_freeze_native | runs/stage11a/v1/freeze_native.log | outputs/stage11a/v1/audit/native_key.json |
| stage11a_prepare | running | Running GPU job stage11a_prepare | runs/stage11a/v1/prepare.log | outputs/stage11a/v1/packets/evidence_construction.json |
| stage11a_probe | running | Running GPU job stage11a_probe_thinking_b | runs/stage11a/v1/probe_thinking_b.log | outputs/stage11a/v1/probes |
| stage11a_probe_review_prep | running | Running GPU job stage11a_probe_review_prep | runs/stage11a/v1/probe_review_prep/slurm.log | outputs/stage11a/v1/packets/probe_review.json |
| stage11b_batch_single_validation | running | Running GPU job stage11b_batch_single_validation | runs/stage11b/v1/batch_single_validation/slurm.log | outputs/stage11b/v1/audit/batch_single_validation.json |
| stage11b_cache_diagnostic | running | Running GPU job stage11b_cache_diagnostic | runs/stage11b/v1/cache_diagnostic/slurm.log | outputs/stage11b/v1/audit/cache_diagnostic.json |
| stage11b_discovery_instruct | running | Running GPU job stage11b_discovery_instruct | runs/stage11b/v1/discovery_instruct/slurm.log | outputs/stage11b/v1/discovery |
| stage11b_discovery_thinking | running | Running GPU job stage11b_discovery_thinking | runs/stage11b/v1/discovery_thinking/slurm.log | outputs/stage11b/v1/discovery |
| stage11b_feasible_instruct_0 | running | Running GPU job stage11b_feasible_instruct_0 | runs/stage11b/v1/feasible_instruct_0/slurm.log | outputs/stage11b/v1/source_feasible/results |
| stage11b_feasible_instruct_1 | running | Running GPU job stage11b_feasible_instruct_1 | runs/stage11b/v1/feasible_instruct_1/slurm.log | outputs/stage11b/v1/source_feasible/results |
| stage11b_feasible_thinking_0 | running | Running GPU job stage11b_feasible_thinking_0 | runs/stage11b/v1/feasible_thinking_0/slurm.log | outputs/stage11b/v1/source_feasible/results |
| stage11b_feasible_thinking_1 | running | Running GPU job stage11b_feasible_thinking_1 | runs/stage11b/v1/feasible_thinking_1/slurm.log | outputs/stage11b/v1/source_feasible/results |
| stage11b_preflight | running | Running GPU job stage11b_preflight | runs/stage11b/v1/preflight/slurm.log | outputs/stage11b/v1/audit/technical_preflight.json |
| stage11b_preflight_repaired | running | Running GPU job stage11b_preflight_repaired | runs/stage11b/v1/preflight_repaired/slurm.log | outputs/stage11b/v1/audit/technical_preflight.json |
| stage11c_calretry1_thinking_0 | completed | Finite generation shard complete; Stage11C closed | runs/stage11c/v1/calretry1_thinking_0/slurm.log | outputs/stage11c/v1/calibration_retry1 |
| stage11c_calretry1_thinking_1 | completed | Finite generation shard complete; Stage11C closed | runs/stage11c/v1/calretry1_thinking_1/slurm.log | outputs/stage11c/v1/calibration_retry1 |
| stage11c_cap_instruct | completed | Finite generation shard complete; Stage11C closed | runs/stage11c/v1/cap_instruct/slurm.log | outputs/stage11c/v1/calibration |
| stage11c_cap_thinking | completed | Safe partial calibration shard; remaining9 calls completed separately | runs/stage11c/v1/cap_thinking/slurm.log | outputs/stage11c/v1/calibration |
| stage11c_nativeearly_instruct_0 | completed | Finite generation shard complete; Stage11C closed | runs/stage11c/v1/nativeearly_instruct_0/slurm.log | outputs/stage11c/v1/native_early |
| stage11c_nativeearly_instruct_1 | completed | Finite generation shard complete; Stage11C closed | runs/stage11c/v1/nativeearly_instruct_1/slurm.log | outputs/stage11c/v1/native_early |
| stage11c_nativeearly_thinking_0 | completed | Finite generation shard complete; Stage11C closed | runs/stage11c/v1/nativeearly_thinking_0/slurm.log | outputs/stage11c/v1/native_early |
| stage11c_nativeearly_thinking_1 | completed | Finite generation shard complete; Stage11C closed | runs/stage11c/v1/nativeearly_thinking_1/slurm.log | outputs/stage11c/v1/native_early |
| stage11cr_diagnostic_instruct_direct | completed | Finite technical shard terminal; Stage11C-R closed | runs/stage11cr/v1/diagnostic_instruct_direct/slurm.log | outputs/stage11cr/v1/diagnostic |
| stage11cr_diagnostic_thinking | completed | Finite technical shard terminal; Stage11C-R closed | runs/stage11cr/v1/diagnostic_thinking/slurm.log | outputs/stage11cr/v1/diagnostic |
| stage11cr_known_good_instruct_direct_0 | completed | Finite technical shard terminal; Stage11C-R closed | runs/stage11cr/v1/known_good_instruct_direct_0/slurm.log | outputs/stage11cr/v1/known_good |
| stage11cr_known_good_instruct_direct_1 | completed | Finite technical shard terminal; Stage11C-R closed | runs/stage11cr/v1/known_good_instruct_direct_1/slurm.log | outputs/stage11cr/v1/known_good |
| stage11cr_known_good_thinking_0 | completed | Finite technical shard terminal; Stage11C-R closed | runs/stage11cr/v1/known_good_thinking_0/slurm.log | outputs/stage11cr/v1/known_good |
| stage11cr_known_good_thinking_1 | completed | Finite technical shard terminal; Stage11C-R closed | runs/stage11cr/v1/known_good_thinking_1/slurm.log | outputs/stage11cr/v1/known_good |
| stage11cr_nonprimary_instruct_direct_0 | completed | Finite technical shard terminal; Stage11C-R closed | runs/stage11cr/v1/nonprimary_instruct_direct_0/slurm.log | outputs/stage11cr/v1/nonprimary40960 |
| stage11cr_nonprimary_instruct_direct_1 | completed | Finite technical shard terminal; Stage11C-R closed | runs/stage11cr/v1/nonprimary_instruct_direct_1/slurm.log | outputs/stage11cr/v1/nonprimary40960 |
| stage11cr_nonprimary_instruct_direct_2 | completed | Finite technical shard terminal; Stage11C-R closed | runs/stage11cr/v1/nonprimary_instruct_direct_2/slurm.log | outputs/stage11cr/v1/nonprimary40960 |
| stage11cr_nonprimary_instruct_direct_3 | completed | Finite technical shard terminal; Stage11C-R closed | runs/stage11cr/v1/nonprimary_instruct_direct_3/slurm.log | outputs/stage11cr/v1/nonprimary40960 |
| stage11cr_nonprimary_thinking_0 | completed | Finite technical shard terminal; Stage11C-R closed | runs/stage11cr/v1/nonprimary_thinking_0/slurm.log | outputs/stage11cr/v1/nonprimary40960 |
| stage11cr_nonprimary_thinking_1 | completed | Finite technical shard terminal; Stage11C-R closed | runs/stage11cr/v1/nonprimary_thinking_1/slurm.log | outputs/stage11cr/v1/nonprimary40960 |
| stage11cr_nonprimary_thinking_2 | completed | Finite technical shard terminal; Stage11C-R closed | runs/stage11cr/v1/nonprimary_thinking_2/slurm.log | outputs/stage11cr/v1/nonprimary40960 |
| stage11cr_nonprimary_thinking_3 | completed | Finite technical shard terminal; Stage11C-R closed | runs/stage11cr/v1/nonprimary_thinking_3/slurm.log | outputs/stage11cr/v1/nonprimary40960 |
| stage12a_technical_v1_0 | running | Running GPU job stage12a_technical_v1_0 | runs/stage12a/v1/technical_v1_0/slurm.log | outputs/stage12a/v1 |
| stage12a_technical_v2_0 | running | Running GPU job stage12a_technical_v2_0 | runs/stage12a/v1/technical_v2_0/slurm.log | outputs/stage12a/v1 |
| stage12ar_development_D_0 | running | Running GPU job stage12ar_development_D_0 | runs/stage12ar/v1/development_D_0/slurm.log | outputs/stage12ar/v1 |
| stage12b_technical_0 | running | Running GPU job stage12b_technical_0 | runs/stage12b/v1/technical_0/slurm.log | outputs/stage12b/v1 |
| stage12b_technical_1 | running | Running GPU job stage12b_technical_1 | runs/stage12b/v1/technical_1/slurm.log | outputs/stage12b/v1 |
| stage12br_validation_0 | running | Running GPU job stage12br_validation_0 | runs/stage12br/v1/validation_0/slurm.log | outputs/stage12br/v1 |
| stage12br_validation_1 | running | Running GPU job stage12br_validation_1 | runs/stage12br/v1/validation_1/slurm.log | outputs/stage12br/v1 |
| stage12bs_remaining_0 | completed | Generation completed; Stage12B-S PROFILE_INFORMATIVE | runs/stage12bs/v1/remaining_0/slurm.log | outputs/stage12bs/v1/stage12bs_summary.md |
| stage12bs_remaining_1 | completed | Generation completed; Stage12B-S PROFILE_INFORMATIVE | runs/stage12bs/v1/remaining_1/slurm.log | outputs/stage12bs/v1/stage12bs_summary.md |
| stage12bs_remaining_2 | completed | Generation completed; Stage12B-S PROFILE_INFORMATIVE | runs/stage12bs/v1/remaining_2/slurm.log | outputs/stage12bs/v1/stage12bs_summary.md |
| stage12bs_remaining_3 | completed | Generation completed; Stage12B-S PROFILE_INFORMATIVE | runs/stage12bs/v1/remaining_3/slurm.log | outputs/stage12bs/v1/stage12bs_summary.md |
| stage12c_sanity_0 | running | Running GPU job stage12c_sanity_0 | runs/stage12c/v1/sanity_0/slurm.log | outputs/stage12c/v1 |
| stage12c_sanity_1 | running | Running GPU job stage12c_sanity_1 | runs/stage12c/v1/sanity_1/slurm.log | outputs/stage12c/v1 |
| stage12cr_cot_0 | completed | Finite generation complete; reviewed and archived | runs/stage12cr/v1/cot_0/slurm.log | outputs/stage12cr/v1 |
| stage12cr_cot_1 | completed | Finite generation complete; reviewed and archived | runs/stage12cr/v1/cot_1/slurm.log | outputs/stage12cr/v1 |
| stage12cr_cot_2 | completed | Finite generation complete; reviewed and archived | runs/stage12cr/v1/cot_2/slurm.log | outputs/stage12cr/v1 |
| stage12cr_fresh12_0 | completed | Finite generation complete; reviewed and archived | runs/stage12cr/v1/fresh12_0/slurm.log | outputs/stage12cr/v1 |
| stage12cr_same12_0 | completed | Finite generation complete; reviewed and archived | runs/stage12cr/v1/same12_0/slurm.log | outputs/stage12cr/v1 |
| stage12ts_remaining_0 | running | Running GPU job stage12ts_remaining_0 | runs/stage12ts/v1/remaining_0/slurm.log | outputs/stage12ts/v1 |
| stage12ts_remaining_1 | running | Running GPU job stage12ts_remaining_1 | runs/stage12ts/v1/remaining_1/slurm.log | outputs/stage12ts/v1 |
| stage12ts_remaining_2 | running | Running GPU job stage12ts_remaining_2 | runs/stage12ts/v1/remaining_2/slurm.log | outputs/stage12ts/v1 |
| stage12us_science_0 | running | Running GPU job stage12us_science_0 | runs/stage12us/v1/science_0/slurm.log | outputs/stage12us/v1 |
| stage12us_science_1 | running | Running GPU job stage12us_science_1 | runs/stage12us/v1/science_1/slurm.log | outputs/stage12us/v1 |
| stage12us_science_2 | running | Running GPU job stage12us_science_2 | runs/stage12us/v1/science_2/slurm.log | outputs/stage12us/v1 |
| stage12us_science_3 | running | Running GPU job stage12us_science_3 | runs/stage12us/v1/science_3/slurm.log | outputs/stage12us/v1 |
| stage12us_science_4 | running | Running GPU job stage12us_science_4 | runs/stage12us/v1/science_4/slurm.log | outputs/stage12us/v1 |
| stage12us_science_5 | running | Running GPU job stage12us_science_5 | runs/stage12us/v1/science_5/slurm.log | outputs/stage12us/v1 |
| stage12us_technical_0 | running | Running GPU job stage12us_technical_0 | runs/stage12us/v1/technical_0/slurm.log | outputs/stage12us/v1 |
| stage12us_technical_1 | running | Running GPU job stage12us_technical_1 | runs/stage12us/v1/technical_1/slurm.log | outputs/stage12us/v1 |
| stage12uswatch_receipts | running | Running GPU job stage12uswatch_receipts | runs/stage12us/v1/observer/slurm.log | outputs/stage12us/v1/audit/generation_collection_complete.json |
| stage12vs_adjacentT_0 | running | Running GPU job stage12vs_adjacentT_0 | runs/stage12vs/v1/adjacentT_0/slurm.log | outputs/stage12vs/v1 |
| stage12vs_adjacentT_1 | running | Running GPU job stage12vs_adjacentT_1 | runs/stage12vs/v1/adjacentT_1/slurm.log | outputs/stage12vs/v1 |
| stage12vs_contentC_0 | running | Running GPU job stage12vs_contentC_0 | runs/stage12vs/v1/contentC_0/slurm.log | outputs/stage12vs/v1 |
| stage12vs_contentC_1 | running | Running GPU job stage12vs_contentC_1 | runs/stage12vs/v1/contentC_1/slurm.log | outputs/stage12vs/v1 |
| stage12vs_optionalE_0 | running | Running GPU job stage12vs_optionalE_0 | runs/stage12vs/v1/optionalE_0/slurm.log | outputs/stage12vs/v1 |
| stage12vs_phaseA_0 | running | Running GPU job stage12vs_phaseA_0 | runs/stage12vs/v1/phaseA_0/slurm.log | outputs/stage12vs/v1 |
| stage12vs_phaseA_1 | running | Running GPU job stage12vs_phaseA_1 | runs/stage12vs/v1/phaseA_1/slurm.log | outputs/stage12vs/v1 |
| stage12vs_phaseB1_0 | running | Running GPU job stage12vs_phaseB1_0 | runs/stage12vs/v1/phaseB1_0/slurm.log | outputs/stage12vs/v1 |
| stage12vs_phaseB2_0 | running | Running GPU job stage12vs_phaseB2_0 | runs/stage12vs/v1/phaseB2_0/slurm.log | outputs/stage12vs/v1 |
| stage12vs_phaseB3_0 | running | Running GPU job stage12vs_phaseB3_0 | runs/stage12vs/v1/phaseB3_0/slurm.log | outputs/stage12vs/v1 |
| stage12vs_phaseB4_0 | running | Running GPU job stage12vs_phaseB4_0 | runs/stage12vs/v1/phaseB4_0/slurm.log | outputs/stage12vs/v1 |
| stage12vs_phaseB5_0 | running | Running GPU job stage12vs_phaseB5_0 | runs/stage12vs/v1/phaseB5_0/slurm.log | outputs/stage12vs/v1 |
| stage12vs_phaseB6_0 | running | Running GPU job stage12vs_phaseB6_0 | runs/stage12vs/v1/phaseB6_0/slurm.log | outputs/stage12vs/v1 |
| stage12vs_phaseB7_0 | running | Running GPU job stage12vs_phaseB7_0 | runs/stage12vs/v1/phaseB7_0/slurm.log | outputs/stage12vs/v1 |
| stage12vswatch_receipts | running | Running GPU job stage12vswatch_receipts | runs/stage12vs/v1/observer/slurm.log | outputs/stage12vs/v1/audit/observer_exit.json |
| stage12vswatch_receipts_node03 | running | Running GPU job stage12vswatch_receipts_node03 | runs/stage12vs/v1/observer_node03/slurm.log | outputs/stage12vs/v1/audit/observer_exit.json |
| stage12vswatch_receipts_oct01 | running | Running GPU job stage12vswatch_receipts_oct01 | runs/stage12vs/v1/observer_oct01/slurm.log | outputs/stage12vs/v1/audit/observer_exit.json |
| stage12vswatch_receipts_oct01_successor | running | Running GPU job stage12vswatch_receipts_oct01_successor | runs/stage12vs/v1/observer_oct01_successor/slurm.log | outputs/stage12vs/v1/audit/observer_exit.json |
| stage12vswatch_receipts_oct02_successor | running | Running GPU job stage12vswatch_receipts_oct02_successor | runs/stage12vs/v1/observer_oct02_successor/slurm.log | outputs/stage12vs/v1/audit/observer_exit.json |
| stage12ws_phaseA_0 | succeeded | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/phaseA_0/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12ws_phaseA_1 | succeeded | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/phaseA_1/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12ws_phaseA_2 | succeeded | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/phaseA_2/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12ws_phaseA_3 | succeeded | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/phaseA_3/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12ws_phaseB_0 | succeeded | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/phaseB_0/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12ws_phaseB_1 | succeeded | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/phaseB_1/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12ws_phaseB_2 | succeeded | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/phaseB_2/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12ws_phaseB_3 | succeeded | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/phaseB_3/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12ws_phaseC_0 | succeeded | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/phaseC_0/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12ws_phaseC_1 | failed | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/phaseC_1/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12ws_phaseC_2 | failed | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/phaseC_2/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12ws_phaseC_3 | failed | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/phaseC_3/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12ws_resume_C_first_attempts_0 | succeeded | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/resume_C_first_attempts_0/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12ws_resume_D01_0 | succeeded | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/resume_D01_0/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12ws_resume_D02_0 | succeeded | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/resume_D02_0/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12ws_resume_D03_0 | succeeded | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/resume_D03_0/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12ws_resume_D04_0 | succeeded | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/resume_D04_0/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12ws_resume_D05_0 | succeeded | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/resume_D05_0/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12ws_resume_D06_0 | succeeded | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/resume_D06_0/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12ws_resume_E_0 | succeeded | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/resume_E_0/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12ws_resume_E_1 | succeeded | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/resume_E_1/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12ws_resume_F_0 | succeeded | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/resume_F_0/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12ws_resume_F_1 | succeeded | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/resume_F_1/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12wshealth_resume1 | succeeded | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/health_resume1/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage12wswatch_receipts | failed | Closed; Stage12WS complete, no relaunch | runs/stage12ws/v1/observer/slurm.log | outputs/stage12ws/v1/stage12ws_summary.md |
| stage14a_final_preservation | running | Running GPU job stage14a_final_preservation | runs/stage14a/final_preservation.log | outputs/stage14a/v1/audit/final_input_preservation_verification.json |
| stage14a_history_v2 | running | Running GPU job stage14a_history_v2 | runs/stage14a/history_v2.log | outputs/stage14a/v1/audit/history_v2/historical_identity_scan.json |
| stage14a_source_audit | running | Running GPU job stage14a_source_audit | runs/stage14a/source_audit.log | outputs/stage14a/v1/audit/historical_identity_scan.json |
| stage14c_g1_anchor_overlap_20261009 | succeeded | Stage14C terminal: succeeded; see final audit receipts | runs/stage14c/g1_anchor_overlap.log | outputs/stage14c/source/anchor_phash_candidates_v1.json |
| stage14c_g1_source_audit_20261009 | succeeded | Stage14C terminal: succeeded; see final audit receipts | runs/stage14c/g1_source_audit.log | outputs/stage14c/source/source_identity_inventory_v1.json |
| stage3a_r3_gen_s00 | running | Running GPU job stage3a_r3_gen_s00 | runs/stage3a_r3_gen_s00/slurm.log | outputs/stage3a/cohort_expansion/round3/shards/shard_00/result.json |
| stage3a_r3_gen_s01 | running | Running GPU job stage3a_r3_gen_s01 | runs/stage3a_r3_gen_s01/slurm.log | outputs/stage3a/cohort_expansion/round3/shards/shard_01/result.json |
| stage3a_r3_gen_s02 | running | Running GPU job stage3a_r3_gen_s02 | runs/stage3a_r3_gen_s02/slurm.log | outputs/stage3a/cohort_expansion/round3/shards/shard_02/result.json |
| stage3a_r3_gen_s03 | running | Running GPU job stage3a_r3_gen_s03 | runs/stage3a_r3_gen_s03/slurm.log | outputs/stage3a/cohort_expansion/round3/shards/shard_03/result.json |
| stage3a_score_s00 | running | Running GPU job stage3a_score_s00 | runs/stage3a_score_s00/slurm.log | outputs/stage3a/scoring/shards/primary_00/result.json |
| stage3a_score_s01 | running | Running GPU job stage3a_score_s01 | runs/stage3a_score_s01/slurm.log | outputs/stage3a/scoring/shards/primary_01/result.json |
| stage3a_score_s02 | running | Running GPU job stage3a_score_s02 | runs/stage3a_score_s02/slurm.log | outputs/stage3a/scoring/shards/primary_02/result.json |
| stage3a_score_s03 | running | Running GPU job stage3a_score_s03 | runs/stage3a_score_s03/slurm.log | outputs/stage3a/scoring/shards/primary_03/result.json |
| stage3a_score_s04 | running | Running GPU job stage3a_score_s04 | runs/stage3a_score_s04/slurm.log | outputs/stage3a/scoring/shards/primary_04/result.json |
| stage3a_score_s05 | running | Running GPU job stage3a_score_s05 | runs/stage3a_score_s05/slurm.log | outputs/stage3a/scoring/shards/primary_05/result.json |
| stage3a_score_s06 | running | Running GPU job stage3a_score_s06 | runs/stage3a_score_s06/slurm.log | outputs/stage3a/scoring/shards/primary_06/result.json |
| stage3a_score_s07 | running | Running GPU job stage3a_score_s07_retry4 | runs/stage3a_score_s07_retry4/slurm.log | outputs/stage3a/scoring/shards/primary_07/result.json |
| stage3b2_cohort_00_a5000 | running | Running GPU job stage3b2_cohort_00_a5000 | runs/stage3b2_cohort/cohort_00/slurm.log | outputs/stage3b2/raw/shards/cohort_00/result.json |
| stage3b2_cohort_01_a5000 | running | Running GPU job stage3b2_cohort_01_a5000 | runs/stage3b2_cohort/cohort_01/slurm.log | outputs/stage3b2/raw/shards/cohort_01/result.json |
| stage3b2_cohort_02_a5000 | running | Running GPU job stage3b2_cohort_02_a5000 | runs/stage3b2_cohort/cohort_02/slurm.log | outputs/stage3b2/raw/shards/cohort_02/result.json |
| stage3b2_cohort_03_a5000 | running | Running GPU job stage3b2_cohort_03_a5000 | runs/stage3b2_cohort/cohort_03/slurm.log | outputs/stage3b2/raw/shards/cohort_03/result.json |
| stage3b2_cohort_04_a5000 | running | Running GPU job stage3b2_cohort_04_a5000 | runs/stage3b2_cohort/cohort_04/slurm.log | outputs/stage3b2/raw/shards/cohort_04/result.json |
| stage3b2_cohort_05_a5000 | running | Running GPU job stage3b2_cohort_05_a5000 | runs/stage3b2_cohort/cohort_05/slurm.log | outputs/stage3b2/raw/shards/cohort_05/result.json |
| stage3b2_cohort_06_a5000 | running | Running GPU job stage3b2_cohort_06_a5000 | runs/stage3b2_cohort/cohort_06/slurm.log | outputs/stage3b2/raw/shards/cohort_06/result.json |
| stage3b2_rollout_00_a5000 | running | Running GPU job stage3b2_rollout_00_a5000 | runs/stage3b2_rollouts/cohort_00/slurm.log | outputs/stage3b2/raw/rollouts/cohort_00/result.json |
| stage3b2_rollout_01_a5000 | running | Running GPU job stage3b2_rollout_01_a5000 | runs/stage3b2_rollouts/cohort_01/slurm.log | outputs/stage3b2/raw/rollouts/cohort_01/result.json |
| stage3b2_rollout_02_a5000 | running | Running GPU job stage3b2_rollout_02_a5000 | runs/stage3b2_rollouts/cohort_02/slurm.log | outputs/stage3b2/raw/rollouts/cohort_02/result.json |
| stage3b2_rollout_03_a5000 | running | Running GPU job stage3b2_rollout_03_a5000 | runs/stage3b2_rollouts/cohort_03/slurm.log | outputs/stage3b2/raw/rollouts/cohort_03/result.json |
| stage3b2_rollout_04_a5000 | running | Running GPU job stage3b2_rollout_04_a5000 | runs/stage3b2_rollouts/cohort_04/slurm.log | outputs/stage3b2/raw/rollouts/cohort_04/result.json |
| stage3b2_rollout_05_a5000 | running | Running GPU job stage3b2_rollout_05_a5000 | runs/stage3b2_rollouts/cohort_05/slurm.log | outputs/stage3b2/raw/rollouts/cohort_05/result.json |
| stage3b2_rollout_06_a5000 | running | Running GPU job stage3b2_rollout_06_a5000 | runs/stage3b2_rollouts/cohort_06/slurm.log | outputs/stage3b2/raw/rollouts/cohort_06/result.json |
| stage3b2_smoke_a5000 | running | Running GPU job stage3b2_smoke_a5000 | runs/stage3b2_smoke/slurm.log | outputs/stage3b2/raw/smoke/three_base/result.json |
| stage3b2_smoke_a5000_resume1 | running | Running GPU job stage3b2_smoke_a5000_resume1 | runs/stage3b2_smoke_resume1/slurm.log | outputs/stage3b2/raw/smoke/three_base/result.json |
| stage3b2_smoke_eagerfix_a5000 | running | Running GPU job stage3b2_smoke_eagerfix_a5000 | runs/stage3b2_smoke_eagerfix/slurm.log | outputs/stage3b2/raw/smoke/eager_fix/result.json |
| stage3b3_smoke_a5000 | running | Running GPU job stage3b3_smoke_a5000_retry1 | runs/stage3b3_smoke_a5000_retry1/slurm.log | outputs/stage3b3/raw/coarse/smoke/result.json |
| stage7a_bench_v2_mmlong_node02_2gpu_20260915 | cancelled | Allocation cancelled at user request; replaced by114923/node03 |  |  |
| stage8b1a_census224_node02_v1 | cancelled | Paused at user request; await instruction to resume | runs/stage8b1a/node02/slurm.log | outputs/stage8b1a/audit/user_cancelled_20260918T060535Z.json |
| stage8b1a_resume125_node06_v1 | succeeded | Native125 continuation complete; cohort256 verified; analysis remains | runs/stage8b1a/node06_v1/slurm.log | outputs/stage8b1a/native/resume125_node06_v1/wrapper.json |
| stage8b_block0_node02_v1 | running | Running GPU job stage8b_block0_node02_v1 | runs/stage8b_block0/slurm.log | outputs/stage8b_block0/v1/wrapper.json |
| stage8b_block1_assemble_node06_v3 | running | Running GPU job stage8b_block1_assemble_node06_v3 | runs/stage8b_block1/node06_assemble_v3.log | outputs/stage8b_block1/v1/wrapper.json |
| stage8b_block1_node06_v1 | running | Running GPU job stage8b_block1_node06_v1 | runs/stage8b_block1/slurm.log | outputs/stage8b_block1/v1/wrapper.json |
| stage8b_block1_rank0_node06_v3 | running | Running GPU job stage8b_block1_rank0_node06_v3 | runs/stage8b_block1/node06_rank0_v3.log | outputs/stage8b_block1/v1/workers/rank0/slurm_wrapper_v3.json |
| stage8b_block1_rank0_split_v2 | running | Running GPU job stage8b_block1_rank0_split_v2 | runs/stage8b_block1/split_rank0.log | outputs/stage8b_block1/v1/workers/rank0/slurm_wrapper_v2.json |
| stage8b_block1_rank1_split_v2 | running | Running GPU job stage8b_block1_rank1_split_v2 | runs/stage8b_block1/split_rank1.log | outputs/stage8b_block1/v1/workers/rank1/slurm_wrapper_v2.json |
| stage8b_block2_replay_node06_v1 | running | Running GPU job stage8b_block2_replay_node06_v1 | runs/stage8b_block2/replay_node06_v1/slurm.log | outputs/stage8b_block2/v1/replay/worker0/completed.json |
| stage8b_block3a_native_four_node02_v1 | running | Running GPU job stage8b_block3a_native_four_node02_v1 | runs/stage8b_block3a/native_resume_four_v1/slurm.log | outputs/stage8b_block3a/v1/audit/native_completion.json |
| stage8b_block3a_native_node02_v1 | running | Running GPU job stage8b_block3a_native_node02_v1 | runs/stage8b_block3a/native_v1/slurm.log | outputs/stage8b_block3a/v1/native/completed.json |
| stage8b_block3a_native_replay_node02_v1 | running | Running GPU job stage8b_block3a_native_replay_node02_v1 | runs/stage8b_block3a/native_replay_v1/slurm.log | outputs/stage8b_block3a/v1/native_replay/worker0/completed.json |
| stage8b_block3b_analysis_v1 | completed | Completed CPU-only Block3B analysis; STOP | runs/stage8b_block3b_v1/analysis_slurm.log | outputs/stage8b_block3b/v1/audit/analysis_complete.json |
| stage8b_block3b_analysis_v2 | completed | Completed CPU-only Block3B analysis; STOP | runs/stage8b_block3b_v1/analysis_v2_slurm.log | outputs/stage8b_block3b/v1/audit/analysis_complete.json |
| stage8b_block3b_v1 | completed | Completed CPU-only Block3B analysis; STOP | runs/stage8b_block3b_v1/analysis_v2_slurm.log | outputs/stage8b_block3b/v1/stage8b_block3b_summary.md |
| stage8b_transfer32_v1 | running | Running GPU job stage8b_transfer32_v1 | runs/stage8b/transfer32_slurm.log | outputs/stage8b/native/transfer32_v1/wrapper.json |
| stage8b_v2_transfer32_node02_four_v1 | running | Running GPU job stage8b_v2_transfer32_node02_four_v1 | runs/stage8b/v2/node02_four/slurm.log | outputs/stage8b/v2/native/transfer32_t1_node02_four_v1/wrapper.json |
| stage8b_v2_transfer32_node02_single_v1 | running | Running GPU job stage8b_v2_transfer32_node02_single_v1 | runs/stage8b/v2/node02_single/slurm.log | outputs/stage8b/v2/native/transfer32_t1_node02_single_v1/wrapper.json |
| stage8b_v2_transfer32_t1_v1 | running | Running GPU job stage8b_v2_transfer32_t1_v1 | runs/stage8b/v2/slurm.log | outputs/stage8b/v2/native/transfer32_t1_v1/wrapper.json |
| stage8c_repair_candidate_v1 | completed | Diagnostics complete; V3 repair failed, intervention branch stopped | runs/stage8c_repair/candidate_v1/slurm.log | outputs/stage8c_repair/v1/stage8c_repair_summary.md |
| stage8c_repair_forensic_v1 | completed | Diagnostics complete; V3 repair failed, intervention branch stopped | runs/stage8c_repair/forensic_v1/slurm.log | outputs/stage8c_repair/v1/stage8c_repair_summary.md |
| stage8c_v2_technical_v1 | failed | stopped:validation onset-coverage harness | runs/stage8c_v2/technical_v1/slurm.log | outputs/stage8c_v2/v1/stage8c_v2_technical_validation.json |
| stage8c_v2_technical_v2 | failed | stopped:manual validation position IDs | runs/stage8c_v2/technical_v2/slurm.log | outputs/stage8c_v2/v1/stage8c_v2_technical_validation.json |
| stage8c_v2_technical_v3 | failed | STOP:required V3 numerical reconstruction failure | runs/stage8c_v2/technical_v3/slurm.log | outputs/stage8c_v2/v1/stage8c_v2_technical_validation.json |
| stage8c_v3_dev_four_v1 | completed | Stage8C v3 complete: development no-go; no held-out launch; GPUs released | runs/stage8c_v3/dev_four_v1/slurm.log | outputs/stage8c_v3/v1/stage8c_v3_summary.md |
| stage8c_v3_dev_v1 | cancelled | Cancelled at user request; four-GPU resume prepared | runs/stage8c_v3/dev_v1/slurm.log | outputs/stage8c_v3/v1/stage8c_v3_summary.md |
| stage9a | completed | Stage9A complete; negative advancement gate; STOP | runs/stage9a/v1/cpu_analysis_node03.log | outputs/stage9a/v1/stage9a_summary.md |
| stage9a3_design_figure_v1 | running | Running GPU job stage9a3_design_figure_v1 | runs/stage9a3/v1/design_figure.log | outputs/stage9a3/v1/figures/figure1_intervention_rectangle.pdf |
| stage9a3_design_figure_v2 | running | Running GPU job stage9a3_design_figure_v2 | runs/stage9a3/v1/design_figure_v2.log | outputs/stage9a3/v1/figures/figure1_intervention_rectangle.pdf |
| stage9a3_final_audit_v1 | running | Running GPU job stage9a3_final_audit_v1 | runs/stage9a3/v1/final_audit.log | outputs/stage9a3/v1/audit/final_validation.json |
| stage9a3_finalize_v1 | running | Running GPU job stage9a3_finalize_v1 | runs/stage9a3/v1/finalize.log | outputs/stage9a3/v1/stage9a3_resource_accounting.json |
| stage9a3_input_freeze_v1 | running | Running GPU job stage9a3_input_freeze_v1 | runs/stage9a3/v1/input_freeze.log | outputs/stage9a3/v1/audit/input_freeze.json |
| stage9a3_qwen25_grid_score_v1 | running | Running GPU job stage9a3_qwen25_grid_score_v1 | runs/stage9a3/v1/qwen25_grid_score.log | outputs/stage9a3/v1/audit/qwen25_primary_calibration_result.json |
| stage9a3_qwen25_grid_v1_worker0 | running | Running GPU job stage9a3_qwen25_grid_v1_worker0 | runs/stage9a3/v1/qwen25_grid_worker0.log | outputs/stage9a3/v1/qwen25/grid_primary/workers |
| stage9a3_qwen25_grid_v1_worker1 | running | Running GPU job stage9a3_qwen25_grid_v1_worker1 | runs/stage9a3/v1/qwen25_grid_worker1.log | outputs/stage9a3/v1/qwen25/grid_primary/workers |
| stage9a3_qwen25_grid_v1_worker2 | running | Running GPU job stage9a3_qwen25_grid_v1_worker2 | runs/stage9a3/v1/qwen25_grid_worker2.log | outputs/stage9a3/v1/qwen25/grid_primary/workers |
| stage9a3_qwen25_preflight_full_v1 | running | Running GPU job stage9a3_qwen25_preflight_full_v1 | runs/stage9a3/v1/qwen25_preflight_full.log | outputs/stage9a3/v1/stage9a3_mask_validation_qwen25.json |
| stage9a3_qwen25_preflight_full_v2 | running | Running GPU job stage9a3_qwen25_preflight_full_v2 | runs/stage9a3/v1/qwen25_preflight_full_v2.log | outputs/stage9a3/v1/stage9a3_mask_validation_qwen25.json |
| stage9a3_qwen25_preflight_v1 | running | Running GPU job stage9a3_qwen25_preflight_v1 | runs/stage9a3/v1/qwen25_preflight.log | outputs/stage9a3/v1/stage9a3_mask_validation_qwen25.json |
| stage9a3_qwen25_reserve_full_v1 | running | Running GPU job stage9a3_qwen25_reserve_full_v1 | runs/stage9a3/v1/qwen25_reserve_full.log | outputs/stage9a3/v1/qwen25/full_reserve/workers |
| stage9a3_qwen25_reserve_grid_v1_worker0 | running | Running GPU job stage9a3_qwen25_reserve_grid_v1_worker0 | runs/stage9a3/v1/qwen25_reserve_grid_worker0.log | outputs/stage9a3/v1/qwen25/grid_reserve/workers |
| stage9a3_qwen25_reserve_grid_v1_worker1 | running | Running GPU job stage9a3_qwen25_reserve_grid_v1_worker1 | runs/stage9a3/v1/qwen25_reserve_grid_worker1.log | outputs/stage9a3/v1/qwen25/grid_reserve/workers |
| stage9a3_qwen25_reserve_grid_v1_worker2 | running | Running GPU job stage9a3_qwen25_reserve_grid_v1_worker2 | runs/stage9a3/v1/qwen25_reserve_grid_worker2.log | outputs/stage9a3/v1/qwen25/grid_reserve/workers |
| stage9a3_qwen25_reserve_grid_v1_worker3 | running | Running GPU job stage9a3_qwen25_reserve_grid_v1_worker3 | runs/stage9a3/v1/qwen25_reserve_grid_worker3.log | outputs/stage9a3/v1/qwen25/grid_reserve/workers |
| stage9a3_qwen25_reserve_score_v1 | running | Running GPU job stage9a3_qwen25_reserve_score_v1 | runs/stage9a3/v1/qwen25_reserve_score.log | outputs/stage9a3/v1/stage9a3_qwen25_positive_control.json |
| stage9a3_qwen25_sink_score_v1 | running | Running GPU job stage9a3_qwen25_sink_score_v1 | runs/stage9a3/v1/qwen25_sink_score.log | outputs/stage9a3/v1/audit/qwen25_bounded_sink_result.json |
| stage9a3_qwen25_sink_v1_worker0 | running | Running GPU job stage9a3_qwen25_sink_v1_worker0 | runs/stage9a3/v1/qwen25_sink_worker0.log | outputs/stage9a3/v1/qwen25/sink_primary/workers |
| stage9a3_qwen25_sink_v1_worker1 | running | Running GPU job stage9a3_qwen25_sink_v1_worker1 | runs/stage9a3/v1/qwen25_sink_worker1.log | outputs/stage9a3/v1/qwen25/sink_primary/workers |
| stage9a3_qwen25_sink_v1_worker2 | running | Running GPU job stage9a3_qwen25_sink_v1_worker2 | runs/stage9a3/v1/qwen25_sink_worker2.log | outputs/stage9a3/v1/qwen25/sink_primary/workers |
| stage9a3_qwen3_preflight_full_v1 | running | Running GPU job stage9a3_qwen3_preflight_full_v1 | runs/stage9a3/v1/qwen3_preflight_full.log | outputs/stage9a3/v1/stage9a3_mask_validation_qwen3.json |
| stage9a3_stop_figure_v2 | running | Running GPU job stage9a3_stop_figure_v2 | runs/stage9a3/v1/stop_figure_v2.log | outputs/stage9a3/v1/figures/figure3_qwen3_validity_stop.pdf |
| stage9a4_compare | running | Running GPU job stage9a4_compare | runs/stage9a4/v1/compare.log | outputs/stage9a4/v1/stage9a4_qwen25_qwen3_comparison.json |
| stage9a4_final_analysis | running | Running GPU job stage9a4_final_analysis | runs/stage9a4/v1/final_analysis.log | outputs/stage9a4/v1/audit/final_validation.json |
| stage9a4_full_0 | running | Running GPU job stage9a4_full_0 | runs/stage9a4/v1/full_0.log | outputs/stage9a4/v1/full |
| stage9a4_full_1 | running | Running GPU job stage9a4_full_1 | runs/stage9a4/v1/full_1.log | outputs/stage9a4/v1/full |
| stage9a4_full_2 | running | Running GPU job stage9a4_full_2 | runs/stage9a4/v1/full_2.log | outputs/stage9a4/v1/full |
| stage9a4_full_3 | running | Running GPU job stage9a4_full_3 | runs/stage9a4/v1/full_3.log | outputs/stage9a4/v1/full |
| stage9a4_masks | running | Running GPU job stage9a4_masks | runs/stage9a4/v1/masks.log | outputs/stage9a4/v1/stage9a4_qwen3_4b_mask_validation.json |
| stage9a4_noop | running | Running GPU job stage9a4_noop | runs/stage9a4/v1/noop.log | outputs/stage9a4/v1/audit/full_noop_validation.json |
| stage9a4_prepare | running | Running GPU job stage9a4_prepare | runs/stage9a4/v1/prepare.log | outputs/stage9a4/v1/config.json |
| stage9a4_r1_0 | running | Running GPU job stage9a4_r1_0 | runs/stage9a4/v1/r1_0.log | outputs/stage9a4/v1/r1 |
| stage9a4_r1_1 | running | Running GPU job stage9a4_r1_1 | runs/stage9a4/v1/r1_1.log | outputs/stage9a4/v1/r1 |
| stage9a4_r1_2 | running | Running GPU job stage9a4_r1_2 | runs/stage9a4/v1/r1_2.log | outputs/stage9a4/v1/r1 |
| stage9a4_r1_3 | running | Running GPU job stage9a4_r1_3 | runs/stage9a4/v1/r1_3.log | outputs/stage9a4/v1/r1 |
| stage9a4_score_r1 | running | Running GPU job stage9a4_score_r1 | runs/stage9a4/v1/score_r1.log | outputs/stage9a4/v1/audit/r1_decision.json |
| stage9a4_score_t128 | running | Running GPU job stage9a4_score_t128 | runs/stage9a4/v1/score_t128.log | outputs/stage9a4/v1/audit/t128_decision.json |
| stage9a4_sink_0 | running | Running GPU job stage9a4_sink_0 | runs/stage9a4/v1/sink_0.log | outputs/stage9a4/v1/sink |
| stage9a4_sink_1 | running | Running GPU job stage9a4_sink_1 | runs/stage9a4/v1/sink_1.log | outputs/stage9a4/v1/sink |
| stage9a4_sink_2 | running | Running GPU job stage9a4_sink_2 | runs/stage9a4/v1/sink_2.log | outputs/stage9a4/v1/sink |
| stage9a4_sink_3 | running | Running GPU job stage9a4_sink_3 | runs/stage9a4/v1/sink_3.log | outputs/stage9a4/v1/sink |
| stage9a4_t128_0 | running | Running GPU job stage9a4_t128_0 | runs/stage9a4/v1/t128_0.log | outputs/stage9a4/v1/t128 |
| stage9a4_t128_1 | running | Running GPU job stage9a4_t128_1 | runs/stage9a4/v1/t128_1.log | outputs/stage9a4/v1/t128 |
| stage9a4_t128_2 | running | Running GPU job stage9a4_t128_2 | runs/stage9a4/v1/t128_2.log | outputs/stage9a4/v1/t128 |
| stage9a4_t128_3 | running | Running GPU job stage9a4_t128_3 | runs/stage9a4/v1/t128_3.log | outputs/stage9a4/v1/t128 |
| stage9a5_close_cpu | running | Running GPU job stage9a5_close_cpu | runs/stage9a5/v1/close_cpu.log | outputs/stage9a5/v1/audit/final_validation.json |
| stage9a5_control_diagnostic | running | Running GPU job stage9a5_control_diagnostic | runs/stage9a5/v1/control_diagnostic.log | outputs/stage9a5/v1/audit/control_completion_diagnostic.json |
| stage9a5_full_0 | running | Running GPU job stage9a5_full_0 | runs/stage9a5/v1/full_0.log | outputs/stage9a5/v1/full |
| stage9a5_full_1 | running | Running GPU job stage9a5_full_1 | runs/stage9a5/v1/full_1.log | outputs/stage9a5/v1/full |
| stage9a5_full_2 | running | Running GPU job stage9a5_full_2 | runs/stage9a5/v1/full_2.log | outputs/stage9a5/v1/full |
| stage9a5_full_3 | running | Running GPU job stage9a5_full_3 | runs/stage9a5/v1/full_3.log | outputs/stage9a5/v1/full |
| stage9a5_manifest_sink | running | Running GPU job stage9a5_manifest_sink | runs/stage9a5/v1/manifest_sink.log | outputs/stage9a5/v1/audit/sink_manifest.json |
| stage9a5_manifest_t1 | running | Running GPU job stage9a5_manifest_t1 | runs/stage9a5/v1/manifest_t1.log | outputs/stage9a5/v1/audit/t1_manifest.json |
| stage9a5_noop | running | Running GPU job stage9a5_noop | runs/stage9a5/v1/noop.log | outputs/stage9a5/v1/audit/full_noop_validation.json |
| stage9a5_prepare | running | Running GPU job stage9a5_prepare | runs/stage9a5/v1/prepare.log | outputs/stage9a5/v1/config.json |
| stage9a5_presentation | running | Running GPU job stage9a5_presentation | runs/stage9a5/v1/presentation.log | outputs/stage9a5/v1/stage9a5_cot_vs_thinking_inference.json |
| stage9a5_relative_description | running | Running GPU job stage9a5_relative_description | runs/stage9a5/v1/relative_description.log | outputs/stage9a5/v1/stage9a5_relative_time_analysis.json |
| stage9a5_report | running | Running GPU job stage9a5_report | runs/stage9a5/v1/report.log | outputs/stage9a5/v1/stage9a5_summary.md |
| stage9a5_score_t1 | running | Running GPU job stage9a5_score_t1 | runs/stage9a5/v1/score_t1.log | outputs/stage9a5/v1/audit/t1_decision.json |
| stage9a5_sink_0 | running | Running GPU job stage9a5_sink_0 | runs/stage9a5/v1/sink_0.log | outputs/stage9a5/v1/sink/workers |
| stage9a5_sink_1 | running | Running GPU job stage9a5_sink_1 | runs/stage9a5/v1/sink_1.log | outputs/stage9a5/v1/sink/workers |
| stage9a5_sink_2 | running | Running GPU job stage9a5_sink_2 | runs/stage9a5/v1/sink_2.log | outputs/stage9a5/v1/sink/workers |
| stage9a5_sink_3 | running | Running GPU job stage9a5_sink_3 | runs/stage9a5/v1/sink_3.log | outputs/stage9a5/v1/sink/workers |
| stage9a5_t1_0 | running | Running GPU job stage9a5_t1_0 | runs/stage9a5/v1/t1_0.log | outputs/stage9a5/v1/t1/workers |
| stage9a5_t1_1 | running | Running GPU job stage9a5_t1_1 | runs/stage9a5/v1/t1_1.log | outputs/stage9a5/v1/t1/workers |
| stage9a5_t1_2 | running | Running GPU job stage9a5_t1_2 | runs/stage9a5/v1/t1_2.log | outputs/stage9a5/v1/t1/workers |
| stage9a5_t1_3 | running | Running GPU job stage9a5_t1_3 | runs/stage9a5/v1/t1_3.log | outputs/stage9a5/v1/t1/workers |
| stage9a5_validate | running | Running GPU job stage9a5_validate | runs/stage9a5/v1/validate.log | outputs/stage9a5/v1/stage9a5_thinking_mask_validation.json |
| stage9a_amendment_coordinator_recovery_20260925 | running | Running GPU job stage9a_amendment_coordinator_recovery_20260925 | runs/stage9a_dynamics/amendment_v1/coordinator_recovery_20260925_slurm.log | outputs/stage9a_dynamics/amendment_v1/audit/dispatcher_status.json |
| stage9a_amendment_coordinator_scale8_20260925 | running | Running GPU job stage9a_amendment_coordinator_scale8_20260925 | runs/stage9a_dynamics/amendment_v1/coordinator_scale8_20260925_slurm.log | outputs/stage9a_dynamics/amendment_v1/audit/dispatcher_status.json |
| stage9a_amendment_coordinator_v1 | running | Running GPU job stage9a_amendment_coordinator_v1 | runs/stage9a_dynamics/amendment_v1/coordinator_slurm.log | outputs/stage9a_dynamics/amendment_v1/audit/dispatcher_status.json |
| stage9a_amendment_readout_v1 | running | Running GPU job stage9a_amendment_readout_v1 | runs/stage9a_dynamics/amendment_v1/stage9a_amendment_readout_v1_slurm.log | outputs/stage9a_dynamics/v1/readouts |
| stage9a_amendment_v1 | running | Main generation complete; masked extraction review and primary inference pending |  | outputs/stage9a_dynamics/amendment_v1/stage9a_summary.md |
| stage9a_amendment_worker0_v1 | running | Running GPU job stage9a_amendment_worker0_v1 | runs/stage9a_dynamics/amendment_v1/stage9a_amendment_worker0_v1_slurm.log | outputs/stage9a_dynamics/amendment_v1/rollouts |
| stage9a_amendment_worker1_v1 | running | Running GPU job stage9a_amendment_worker1_v1 | runs/stage9a_dynamics/amendment_v1/stage9a_amendment_worker1_v1_slurm.log | outputs/stage9a_dynamics/amendment_v1/rollouts |
| stage9a_amendment_worker_20260924T082617_0 | running | Running GPU job stage9a_amendment_worker_20260924T082617_0 | runs/stage9a_dynamics/amendment_v1/stage9a_amendment_worker_20260924T082617_0_slurm.log | outputs/stage9a_dynamics/amendment_v1/rollouts |
| stage9a_amendment_worker_20260924T120919_1 | running | Running GPU job stage9a_amendment_worker_20260924T120919_1 | runs/stage9a_dynamics/amendment_v1/stage9a_amendment_worker_20260924T120919_1_slurm.log | outputs/stage9a_dynamics/amendment_v1/rollouts |
| stage9a_amendment_worker_scale8_20260925_0 | running | Running GPU job stage9a_amendment_worker_scale8_20260925_0 | runs/stage9a_dynamics/amendment_v1/stage9a_amendment_worker_scale8_20260925_0_slurm.log | outputs/stage9a_dynamics/amendment_v1/rollouts |
| stage9a_amendment_worker_scale8_20260925_1 | running | Running GPU job stage9a_amendment_worker_scale8_20260925_1 | runs/stage9a_dynamics/amendment_v1/stage9a_amendment_worker_scale8_20260925_1_slurm.log | outputs/stage9a_dynamics/amendment_v1/rollouts |
| stage9a_amendment_worker_scale8_20260925_2 | running | Running GPU job stage9a_amendment_worker_scale8_20260925_2 | runs/stage9a_dynamics/amendment_v1/stage9a_amendment_worker_scale8_20260925_2_slurm.log | outputs/stage9a_dynamics/amendment_v1/rollouts |
| stage9a_amendment_worker_scale8_20260925_3 | running | Running GPU job stage9a_amendment_worker_scale8_20260925_3 | runs/stage9a_dynamics/amendment_v1/stage9a_amendment_worker_scale8_20260925_3_slurm.log | outputs/stage9a_dynamics/amendment_v1/rollouts |
| stage9a_controls_v1_worker0 | running | Running GPU job stage9a_controls_v1_worker0 | runs/stage9a_dynamics/amendment_v1/controls_worker0.log | outputs/stage9a_dynamics/amendment_v1/controls_v1/rollouts/workers |
| stage9a_controls_v1_worker1 | running | Running GPU job stage9a_controls_v1_worker1 | runs/stage9a_dynamics/amendment_v1/controls_worker1.log | outputs/stage9a_dynamics/amendment_v1/controls_v1/rollouts/workers |
| stage9a_controls_v1_worker2 | running | Running GPU job stage9a_controls_v1_worker2 | runs/stage9a_dynamics/amendment_v1/controls_worker2.log | outputs/stage9a_dynamics/amendment_v1/controls_v1/rollouts/workers |
| stage9a_controls_v1_worker3 | running | Running GPU job stage9a_controls_v1_worker3 | runs/stage9a_dynamics/amendment_v1/controls_worker3.log | outputs/stage9a_dynamics/amendment_v1/controls_v1/rollouts/workers |
| stage9a_controls_v1_worker4 | running | Running GPU job stage9a_controls_v1_worker4 | runs/stage9a_dynamics/amendment_v1/controls_worker4.log | outputs/stage9a_dynamics/amendment_v1/controls_v1/rollouts/workers |
| stage9a_controls_v1_worker5 | running | Running GPU job stage9a_controls_v1_worker5 | runs/stage9a_dynamics/amendment_v1/controls_worker5.log | outputs/stage9a_dynamics/amendment_v1/controls_v1/rollouts/workers |
| stage9a_controls_v1_worker6 | running | Running GPU job stage9a_controls_v1_worker6 | runs/stage9a_dynamics/amendment_v1/controls_worker6.log | outputs/stage9a_dynamics/amendment_v1/controls_v1/rollouts/workers |
| stage9a_controls_v1_worker7 | running | Running GPU job stage9a_controls_v1_worker7 | runs/stage9a_dynamics/amendment_v1/controls_worker7.log | outputs/stage9a_dynamics/amendment_v1/controls_v1/rollouts/workers |
| stage9a_dynamics_coordinator_v1 | cancelled | User compute amendment: safely stopped and superseded; all completed evidence preserved | runs/stage9a_dynamics/v1/coordinator_slurm.log | outputs/stage9a_dynamics/v1/audit/dispatcher_status.json |
| stage9a_dynamics_node07_probe_v1 | running | Running GPU job stage9a_dynamics_node07_probe_v1 | runs/stage9a_dynamics/v1/node07_probe_slurm.log | outputs/stage9a_dynamics/v1/audit/node07_probe.json |
| stage9a_dynamics_preflight_v1 | running | Running GPU job stage9a_dynamics_preflight_v1 | runs/stage9a_dynamics/v1/preflight_slurm.log | outputs/stage9a_dynamics/v1/stage9a_mask_backend_validation.json |
| stage9a_dynamics_v1 | running | Main generation complete; masked extraction review and primary inference pending |  | outputs/stage9a_dynamics/amendment_v1/stage9a_summary.md |
| stage9a_dynamics_worker0_v1 | cancelled | User compute amendment: safely stopped and superseded; all completed evidence preserved | runs/stage9a_dynamics/v1/stage9a_dynamics_worker0_v1_slurm.log | outputs/stage9a_dynamics/v1/rollouts |
| stage9a_dynamics_worker1_v1 | cancelled | User compute amendment: safely stopped and superseded; all completed evidence preserved | runs/stage9a_dynamics/v1/stage9a_dynamics_worker1_v1_slurm.log | outputs/stage9a_dynamics/v1/rollouts |
| stage9a_dynamics_worker2_v1 | cancelled | User compute amendment: safely stopped and superseded; all completed evidence preserved | runs/stage9a_dynamics/v1/stage9a_dynamics_worker2_v1_slurm.log | outputs/stage9a_dynamics/v1/rollouts |
| stage9a_dynamics_worker3_v1 | cancelled | User compute amendment: safely stopped and superseded; all completed evidence preserved | runs/stage9a_dynamics/v1/stage9a_dynamics_worker3_v1_slurm.log | outputs/stage9a_dynamics/v1/rollouts |
| stage9a_finish_answer_packets_v1 | running | Running GPU job stage9a_finish_answer_packets_v1 | runs/stage9a_dynamics/amendment_v1/prepare_answers_slurm.log | outputs/stage9a_dynamics/amendment_v1/annotations/answer_preparation.json |
| stage9a_finish_main_analysis_v1 | running | Running GPU job stage9a_finish_main_analysis_v1 | runs/stage9a_dynamics/amendment_v1/main_analysis_slurm.log | outputs/stage9a_dynamics/amendment_v1/audit/main_analysis_ready.json |
| stage9a_native_worker0_v1 | completed | Completion receipt verified; allocation released. | runs/stage9a/v1/stage9a_native_worker0_v1_slurm.log | outputs/stage9a/v1/audit/native_complete.json |
| stage9a_native_worker1_v1 | completed | Completion receipt verified; allocation released. | runs/stage9a/v1/stage9a_native_worker1_v1_slurm.log | outputs/stage9a/v1/audit/native_complete.json |
| stage9a_native_worker2_v1 | completed | Completion receipt verified; allocation released. | runs/stage9a/v1/stage9a_native_worker2_v1_slurm.log | outputs/stage9a/v1/audit/native_complete.json |
| stage9a_native_worker3_v1 | completed | Completion receipt verified; allocation released. | runs/stage9a/v1/stage9a_native_worker3_v1_slurm.log | outputs/stage9a/v1/audit/native_complete.json |
| stage9a_preflight_node07_v1 | cancelled | Cancelled idle preflight: Python startup blocked in RPC/filesystem I/O, no model loaded/checks/trajectories. Node07 diagnostic preserved. Underlying service cause unknown. | runs/stage9a/v1/preflight_node07_slurm.log | outputs/stage9a/v1/audit/preflight/complete.json |
| stage9a_preflight_recovery_v1 | completed | Completion receipt verified; allocation released. | runs/stage9a/v1/stage9a_preflight_recovery_v1_slurm.log | outputs/stage9a/v1/audit/preflight/complete.json |
| stage9a_v1 | completed | Stage9A complete; negative advancement gate; STOP | runs/stage9a/v1/dispatcher.log | outputs/stage9a/v1/stage9a_summary.md |
| visual_reasoning_stage0_full_30_a5000 | succeeded | Completed and independently validated the 30-example Stage 0 run | runs/visual_reasoning_stage0_full_30_a5000/slurm.log | outputs/stage0/summaries/stage0_summary.json |
| visual_reasoning_stage0_smoke_2048_a5000 | succeeded | Completed and validated the 3-example Stage 0 smoke gate | runs/visual_reasoning_stage0_smoke_2048_a5000/slurm.log | outputs/stage0_smoke_2048/summaries/stage0_summary.json |
| visual_reasoning_stage0_smoke_3 | running | Running GPU job visual_reasoning_stage0_smoke_3 | runs/visual_reasoning_stage0_smoke_3/slurm.log | outputs/stage0_smoke/summaries/stage0_summary.json |
| visual_reasoning_stage0_smoke_3_a5000 | running | Running GPU job visual_reasoning_stage0_smoke_3_a5000 | runs/visual_reasoning_stage0_smoke_3_a5000/slurm.log | outputs/stage0_smoke/summaries/stage0_summary.json |
| visual_reasoning_stage1a2_sampling_smoke | running | Running GPU job visual_reasoning_stage1a2_sampling_smoke_a5000 | runs/visual_reasoning_stage1a2_sampling_smoke_a5000/slurm.log | outputs/stage1/protocol_pilot/runtime_smoke_40960.json |
| visual_reasoning_stage1a_pilot_4096_a5000 | running | Running GPU job visual_reasoning_stage1a_pilot_4096_a5000 | runs/visual_reasoning_stage1a_pilot_4096_a5000/slurm.log | outputs/stage1/protocol_pilot/run_4096/run_summary.json |
| visual_reasoning_stage1a_pilot_4096_a6000 | running | Running GPU job visual_reasoning_stage1a_pilot_4096_a6000 | runs/visual_reasoning_stage1a_pilot_4096_a6000/slurm.log | outputs/stage1/protocol_pilot/run_4096/run_summary.json |
| visual_reasoning_stage1a_pilot_4096_node07_a6000 | succeeded | Completed and independently validated fixed 4096-token pilot | runs/visual_reasoning_stage1a_pilot_4096_node07_a6000/slurm.log | outputs/stage1/protocol_pilot/run_4096/run_summary.json |
| visual_reasoning_stage1a_pilot_8192 | succeeded | Completed and independently validated conditional 8192-token pilot | runs/visual_reasoning_stage1a_pilot_8192_node07_a6000/slurm.log | outputs/stage1/protocol_pilot/run_8192/run_summary.json |
| visual_reasoning_stage2b | running | Running GPU job vr_stage2b_pilot_a6000_exclude03 | runs/stage2b_a6000_exclude03/slurm.log | outputs/stage2b/summaries/stage2b_acceptance.json |
| visual_reasoning_stage2c | running | Running GPU job vr_stage2c_temporal_audit_a6000_exclude03 | runs/visual_reasoning_stage2c/slurm.log | outputs/stage2c/summaries/stage2c_acceptance.json |
| visual_reasoning_stage3a | running | Running GPU job stage3a_node03_cuda_diagnostic | runs/stage3a_node03_cuda_diagnostic/slurm.log | outputs/stage3a/scoring/node03_cuda_diagnostic.json |
| visual_reasoning_stage3b0_cohort_00 | running | Running GPU job stage3b0_cohort_00_a5000 | runs/stage3b0_cohort/shard_00.log | outputs/stage3b0/raw/shards/cohort_00/result.json |
| visual_reasoning_stage3b0_cohort_01 | running | Running GPU job stage3b0_cohort_01_a5000 | runs/stage3b0_cohort/shard_01.log | outputs/stage3b0/raw/shards/cohort_01/result.json |
| visual_reasoning_stage3b0_cohort_02 | running | Running GPU job stage3b0_cohort_02_a5000 | runs/stage3b0_cohort/shard_02.log | outputs/stage3b0/raw/shards/cohort_02/result.json |
| visual_reasoning_stage3b0_cohort_03 | running | Running GPU job stage3b0_cohort_03_a5000 | runs/stage3b0_cohort/shard_03.log | outputs/stage3b0/raw/shards/cohort_03/result.json |
| visual_reasoning_stage3b0_cohort_04 | running | Running GPU job stage3b0_cohort_04_a5000 | runs/stage3b0_cohort/shard_04.log | outputs/stage3b0/raw/shards/cohort_04/result.json |
| visual_reasoning_stage3b0_cohort_05 | running | Running GPU job stage3b0_cohort_05_a5000 | runs/stage3b0_cohort/shard_05.log | outputs/stage3b0/raw/shards/cohort_05/result.json |
| visual_reasoning_stage3b0_cohort_06 | running | Running GPU job stage3b0_cohort_06_a5000 | runs/stage3b0_cohort/shard_06.log | outputs/stage3b0/raw/shards/cohort_06/result.json |
| visual_reasoning_stage3b0_diagnostic | running | Running GPU job stage3b0_cached_parity_119 | runs/stage3b0_cached_parity/slurm.log | outputs/stage3b0/smoke/cached_full_parity_diagnostic.json |
| visual_reasoning_stage3b0_smoke | running | Running GPU job stage3b0_smoke_a5000 | runs/stage3b0_smoke/slurm.log | outputs/stage3b0/raw/smoke/three_base/result.json |
| visual_reasoning_stage3b0_smoke_validated | running | Running GPU job stage3b0_smoke_validated_a5000 | runs/stage3b0_smoke_validated/slurm.log | outputs/stage3b0/raw/smoke/validated/result.json |
| visual_reasoning_stage3b1_cohort_00 | running | Running GPU job stage3b1_cohort_00_a5000_pending | runs/stage3b1_cohort/shard_00.log | outputs/stage3b1/raw/shards/cohort_00/result.json |
| visual_reasoning_stage3b1_cohort_01 | running | Running GPU job stage3b1_cohort_01_a5000_pending | runs/stage3b1_cohort/shard_01.log | outputs/stage3b1/raw/shards/cohort_01/result.json |
| visual_reasoning_stage3b1_cohort_02 | running | Running GPU job stage3b1_cohort_02_a5000_pending | runs/stage3b1_cohort/shard_02.log | outputs/stage3b1/raw/shards/cohort_02/result.json |
| visual_reasoning_stage3b1_cohort_03 | running | Running GPU job stage3b1_cohort_03_a5000_pending | runs/stage3b1_cohort/shard_03.log | outputs/stage3b1/raw/shards/cohort_03/result.json |
| visual_reasoning_stage3b1_cohort_04 | running | Running GPU job stage3b1_cohort_04_a5000_pending | runs/stage3b1_cohort/shard_04.log | outputs/stage3b1/raw/shards/cohort_04/result.json |
| visual_reasoning_stage3b1_cohort_05 | running | Running GPU job stage3b1_cohort_05_a5000_pending | runs/stage3b1_cohort/shard_05.log | outputs/stage3b1/raw/shards/cohort_05/result.json |
| visual_reasoning_stage3b1_cohort_06 | running | Running GPU job stage3b1_cohort_06_a5000_pending | runs/stage3b1_cohort/shard_06.log | outputs/stage3b1/raw/shards/cohort_06/result.json |
| visual_reasoning_stage3b1_smoke | running | Running GPU job stage3b1_smoke_a6000 | runs/stage3b1_smoke/slurm.log | outputs/stage3b1/raw/smoke/validated/result.json |
| visual_reasoning_stage3b1_smoke_a5000 | running | Running GPU job stage3b1_smoke_a5000 | runs/stage3b1_smoke_a5000/slurm.log | outputs/stage3b1/raw/smoke/validated/result.json |
| visual_reasoning_stage3b3r_fine_00 | running | Running GPU job visual_reasoning_stage3b3r_fine_00 | runs/visual_reasoning_stage3b3r_fine_00/slurm.log | outputs/stage3b3_redesign/primary/raw/fine/fine_00/result.json |
| visual_reasoning_stage3b3r_fine_01 | running | Running GPU job visual_reasoning_stage3b3r_fine_01 | runs/visual_reasoning_stage3b3r_fine_01/slurm.log | outputs/stage3b3_redesign/primary/raw/fine/fine_01/result.json |
| visual_reasoning_stage3b3r_fine_02 | running | Running GPU job visual_reasoning_stage3b3r_fine_02 | runs/visual_reasoning_stage3b3r_fine_02/slurm.log | outputs/stage3b3_redesign/primary/raw/fine/fine_02/result.json |
| visual_reasoning_stage3b3r_fine_03 | running | Running GPU job visual_reasoning_stage3b3r_fine_03 | runs/visual_reasoning_stage3b3r_fine_03/slurm.log | outputs/stage3b3_redesign/primary/raw/fine/fine_03/result.json |
| visual_reasoning_stage3b3r_fine_04 | running | Running GPU job visual_reasoning_stage3b3r_fine_04 | runs/visual_reasoning_stage3b3r_fine_04/slurm.log | outputs/stage3b3_redesign/primary/raw/fine/fine_04/result.json |
| visual_reasoning_stage3b3r_fine_05 | running | Running GPU job visual_reasoning_stage3b3r_fine_05 | runs/visual_reasoning_stage3b3r_fine_05/slurm.log | outputs/stage3b3_redesign/primary/raw/fine/fine_05/result.json |
| visual_reasoning_stage3b3r_fine_06 | running | Running GPU job visual_reasoning_stage3b3r_fine_06 | runs/visual_reasoning_stage3b3r_fine_06/slurm.log | outputs/stage3b3_redesign/primary/raw/fine/fine_06/result.json |
| visual_reasoning_stage3b3r_fine_07 | running | Running GPU job visual_reasoning_stage3b3r_fine_07 | runs/visual_reasoning_stage3b3r_fine_07/slurm.log | outputs/stage3b3_redesign/primary/raw/fine/fine_07/result.json |
| visual_reasoning_stage3b3r_hardware_a6000 | running | Running GPU job visual_reasoning_stage3b3r_hardware_a6000 | runs/visual_reasoning_stage3b3r_hardware_a6000/slurm.log | outputs/stage3b3_redesign/validation/raw/hardware_a6000/result.json |
| visual_reasoning_stage3b3r_node03_check | running | Running GPU job visual_reasoning_stage3b3r_node03_check | runs/visual_reasoning_stage3b3r_node03_check/slurm.log | outputs/stage3b3_redesign/validation/raw/node03_a6000/result.json |
| visual_reasoning_stage3b3r_primary_00 | running | Running GPU job visual_reasoning_stage3b3r_primary_00 | runs/visual_reasoning_stage3b3r_primary_00/slurm.log | outputs/stage3b3_redesign/primary/raw/shards/primary_00/result.json |
| visual_reasoning_stage3b3r_primary_01 | running | Running GPU job visual_reasoning_stage3b3r_primary_01 | runs/visual_reasoning_stage3b3r_primary_01/slurm.log | outputs/stage3b3_redesign/primary/raw/shards/primary_01/result.json |
| visual_reasoning_stage3b3r_primary_02 | running | Running GPU job visual_reasoning_stage3b3r_primary_02 | runs/visual_reasoning_stage3b3r_primary_02/slurm.log | outputs/stage3b3_redesign/primary/raw/shards/primary_02/result.json |
| visual_reasoning_stage3b3r_primary_03 | running | Running GPU job visual_reasoning_stage3b3r_primary_03 | runs/visual_reasoning_stage3b3r_primary_03/slurm.log | outputs/stage3b3_redesign/primary/raw/shards/primary_03/result.json |
| visual_reasoning_stage3b3r_primary_04 | running | Running GPU job visual_reasoning_stage3b3r_primary_04 | runs/visual_reasoning_stage3b3r_primary_04/slurm.log | outputs/stage3b3_redesign/primary/raw/shards/primary_04/result.json |
| visual_reasoning_stage3b3r_primary_05 | running | Running GPU job visual_reasoning_stage3b3r_primary_05 | runs/visual_reasoning_stage3b3r_primary_05/slurm.log | outputs/stage3b3_redesign/primary/raw/shards/primary_05/result.json |
| visual_reasoning_stage3b3r_primary_06 | running | Running GPU job visual_reasoning_stage3b3r_primary_06 | runs/visual_reasoning_stage3b3r_primary_06/slurm.log | outputs/stage3b3_redesign/primary/raw/shards/primary_06/result.json |
| visual_reasoning_stage3b3r_primary_07 | running | Running GPU job visual_reasoning_stage3b3r_primary_07 | runs/visual_reasoning_stage3b3r_primary_07/slurm.log | outputs/stage3b3_redesign/primary/raw/shards/primary_07/result.json |
| visual_reasoning_stage3b3r_validation_00 | running | Running GPU job visual_reasoning_stage3b3r_validation_00_retry | runs/visual_reasoning_stage3b3r_validation_00_retry/slurm.log | outputs/stage3b3_redesign/validation/raw/shards/validation_00/result.json |
| visual_reasoning_stage3b3r_validation_01 | running | Running GPU job visual_reasoning_stage3b3r_validation_01 | runs/visual_reasoning_stage3b3r_validation_01/slurm.log | outputs/stage3b3_redesign/validation/raw/shards/validation_01/result.json |
| visual_reasoning_stage3b3r_validation_02 | running | Running GPU job visual_reasoning_stage3b3r_validation_02 | runs/visual_reasoning_stage3b3r_validation_02/slurm.log | outputs/stage3b3_redesign/validation/raw/shards/validation_02/result.json |
| visual_reasoning_stage3b3r_validation_03 | running | Running GPU job visual_reasoning_stage3b3r_validation_03 | runs/visual_reasoning_stage3b3r_validation_03/slurm.log | outputs/stage3b3_redesign/validation/raw/shards/validation_03/result.json |
| visual_reasoning_stage3b3r_validation_04 | running | Running GPU job visual_reasoning_stage3b3r_validation_04 | runs/visual_reasoning_stage3b3r_validation_04/slurm.log | outputs/stage3b3_redesign/validation/raw/shards/validation_04/result.json |
| visual_reasoning_stage3b3r_validation_05 | running | Running GPU job visual_reasoning_stage3b3r_validation_05 | runs/visual_reasoning_stage3b3r_validation_05/slurm.log | outputs/stage3b3_redesign/validation/raw/shards/validation_05/result.json |
| visual_reasoning_stage3b3r_validation_06 | running | Running GPU job visual_reasoning_stage3b3r_validation_06 | runs/visual_reasoning_stage3b3r_validation_06/slurm.log | outputs/stage3b3_redesign/validation/raw/shards/validation_06/result.json |
| visual_reasoning_stage3b3r_validation_07 | running | Running GPU job visual_reasoning_stage3b3r_validation_07 | runs/visual_reasoning_stage3b3r_validation_07/slurm.log | outputs/stage3b3_redesign/validation/raw/shards/validation_07/result.json |
| visual_reasoning_stage3b4_primary_00 | running | Running GPU job visual_reasoning_stage3b4_primary_00 | runs/visual_reasoning_stage3b4_primary_00/slurm.log | outputs/stage3b4/scoring/raw/primary_00/result.json |
| visual_reasoning_stage3b4_primary_01 | running | Running GPU job visual_reasoning_stage3b4_primary_01 | runs/visual_reasoning_stage3b4_primary_01/slurm.log | outputs/stage3b4/scoring/raw/primary_01/result.json |
| visual_reasoning_stage3b4_primary_02 | running | Running GPU job visual_reasoning_stage3b4_primary_02 | runs/visual_reasoning_stage3b4_primary_02/slurm.log | outputs/stage3b4/scoring/raw/primary_02/result.json |
| visual_reasoning_stage3b4_primary_03 | running | Running GPU job visual_reasoning_stage3b4_primary_03 | runs/visual_reasoning_stage3b4_primary_03/slurm.log | outputs/stage3b4/scoring/raw/primary_03/result.json |
| visual_reasoning_stage3b4_primary_04 | running | Running GPU job visual_reasoning_stage3b4_primary_04 | runs/visual_reasoning_stage3b4_primary_04/slurm.log | outputs/stage3b4/scoring/raw/primary_04/result.json |
| visual_reasoning_stage3b4_primary_05 | running | Running GPU job visual_reasoning_stage3b4_primary_05 | runs/visual_reasoning_stage3b4_primary_05/slurm.log | outputs/stage3b4/scoring/raw/primary_05/result.json |
| visual_reasoning_stage3b4_primary_06 | running | Running GPU job visual_reasoning_stage3b4_primary_06 | runs/visual_reasoning_stage3b4_primary_06/slurm.log | outputs/stage3b4/scoring/raw/primary_06/result.json |
| visual_reasoning_stage3b4_primary_07 | running | Running GPU job visual_reasoning_stage3b4_primary_07 | runs/visual_reasoning_stage3b4_primary_07/slurm.log | outputs/stage3b4/scoring/raw/primary_07/result.json |
| visual_reasoning_stage3b4_validation_00 | running | Running GPU job visual_reasoning_stage3b4_validation_00 | runs/visual_reasoning_stage3b4_validation_00/slurm.log | outputs/stage3b4/validation/raw/validation_00/result.json |
| visual_reasoning_stage3b4_validation_01 | running | Running GPU job visual_reasoning_stage3b4_validation_01 | runs/visual_reasoning_stage3b4_validation_01/slurm.log | outputs/stage3b4/validation/raw/validation_01/result.json |
| visual_reasoning_stage3b4_validation_02 | running | Running GPU job visual_reasoning_stage3b4_validation_02 | runs/visual_reasoning_stage3b4_validation_02/slurm.log | outputs/stage3b4/validation/raw/validation_02/result.json |
| visual_reasoning_stage3b4_validation_03 | running | Running GPU job visual_reasoning_stage3b4_validation_03 | runs/visual_reasoning_stage3b4_validation_03/slurm.log | outputs/stage3b4/validation/raw/validation_03/result.json |
| visual_reasoning_stage3b4_validation_04 | running | Running GPU job visual_reasoning_stage3b4_validation_04 | runs/visual_reasoning_stage3b4_validation_04/slurm.log | outputs/stage3b4/validation/raw/validation_04/result.json |
| visual_reasoning_stage3b4_validation_05 | running | Running GPU job visual_reasoning_stage3b4_validation_05 | runs/visual_reasoning_stage3b4_validation_05/slurm.log | outputs/stage3b4/validation/raw/validation_05/result.json |
| visual_reasoning_stage3b4_validation_06 | running | Running GPU job visual_reasoning_stage3b4_validation_06 | runs/visual_reasoning_stage3b4_validation_06/slurm.log | outputs/stage3b4/validation/raw/validation_06/result.json |
| visual_reasoning_stage3b4_validation_07 | running | Running GPU job visual_reasoning_stage3b4_validation_07 | runs/visual_reasoning_stage3b4_validation_07/slurm.log | outputs/stage3b4/validation/raw/validation_07/result.json |
| visual_reasoning_stage3b5_primary_00 | running | Running GPU job visual_reasoning_stage3b5_primary_00 | runs/visual_reasoning_stage3b5_primary_00/slurm.log | outputs/stage3b5/scoring/raw/primary_00/result.json |
| visual_reasoning_stage3b5_primary_01 | running | Running GPU job visual_reasoning_stage3b5_primary_01 | runs/visual_reasoning_stage3b5_primary_01/slurm.log | outputs/stage3b5/scoring/raw/primary_01/result.json |
| visual_reasoning_stage3b5_primary_02 | running | Running GPU job visual_reasoning_stage3b5_primary_02 | runs/visual_reasoning_stage3b5_primary_02/slurm.log | outputs/stage3b5/scoring/raw/primary_02/result.json |
| visual_reasoning_stage3b5_primary_03 | running | Running GPU job visual_reasoning_stage3b5_primary_03 | runs/visual_reasoning_stage3b5_primary_03/slurm.log | outputs/stage3b5/scoring/raw/primary_03/result.json |
| visual_reasoning_stage3b5_primary_04 | running | Running GPU job visual_reasoning_stage3b5_primary_04 | runs/visual_reasoning_stage3b5_primary_04/slurm.log | outputs/stage3b5/scoring/raw/primary_04/result.json |
| visual_reasoning_stage3b5_primary_05 | running | Running GPU job visual_reasoning_stage3b5_primary_05 | runs/visual_reasoning_stage3b5_primary_05/slurm.log | outputs/stage3b5/scoring/raw/primary_05/result.json |
| visual_reasoning_stage3b5_primary_06 | running | Running GPU job visual_reasoning_stage3b5_primary_06 | runs/visual_reasoning_stage3b5_primary_06/slurm.log | outputs/stage3b5/scoring/raw/primary_06/result.json |
| visual_reasoning_stage3b5_primary_07 | running | Running GPU job visual_reasoning_stage3b5_primary_07 | runs/visual_reasoning_stage3b5_primary_07/slurm.log | outputs/stage3b5/scoring/raw/primary_07/result.json |
| visual_reasoning_stage3b5_validation_00 | running | Running GPU job visual_reasoning_stage3b5_validation_00 | runs/visual_reasoning_stage3b5_validation_00/slurm.log | outputs/stage3b5/validation/raw/validation_00/result.json |
| visual_reasoning_stage3b5_validation_01 | running | Running GPU job visual_reasoning_stage3b5_validation_01 | runs/visual_reasoning_stage3b5_validation_01/slurm.log | outputs/stage3b5/validation/raw/validation_01/result.json |
| visual_reasoning_stage3b5_validation_02 | running | Running GPU job visual_reasoning_stage3b5_validation_02 | runs/visual_reasoning_stage3b5_validation_02/slurm.log | outputs/stage3b5/validation/raw/validation_02/result.json |
| visual_reasoning_stage3b5_validation_03 | running | Running GPU job visual_reasoning_stage3b5_validation_03 | runs/visual_reasoning_stage3b5_validation_03/slurm.log | outputs/stage3b5/validation/raw/validation_03/result.json |
| visual_reasoning_stage3b5_validation_04 | running | Running GPU job visual_reasoning_stage3b5_validation_04 | runs/visual_reasoning_stage3b5_validation_04/slurm.log | outputs/stage3b5/validation/raw/validation_04/result.json |
| visual_reasoning_stage3b5_validation_05 | running | Running GPU job visual_reasoning_stage3b5_validation_05 | runs/visual_reasoning_stage3b5_validation_05/slurm.log | outputs/stage3b5/validation/raw/validation_05/result.json |
| visual_reasoning_stage3b5_validation_06 | running | Running GPU job visual_reasoning_stage3b5_validation_06 | runs/visual_reasoning_stage3b5_validation_06/slurm.log | outputs/stage3b5/validation/raw/validation_06/result.json |
| visual_reasoning_stage3b5_validation_07 | running | Running GPU job visual_reasoning_stage3b5_validation_07 | runs/visual_reasoning_stage3b5_validation_07/slurm.log | outputs/stage3b5/validation/raw/validation_07/result.json |
| visual_reasoning_stage3b9_phase_b_full | running | Running GPU job visual_reasoning_stage3b9_phase_b_full | runs/stage3b9_slurm/phase_b_full_slurm.log | outputs/stage3b9/phase_b_local/scoring/raw/phase_b_full_00/result.json |
| visual_reasoning_stage3b9_phase_b_projected | running | Running GPU job visual_reasoning_stage3b9_phase_b_projected | runs/stage3b9_slurm/phase_b_projected_slurm.log | outputs/stage3b9/phase_b_local/scoring/raw/phase_b_projected_00/result.json |
| visual_reasoning_stage3c8_generation_resume | running | Running GPU job visual_reasoning_stage3c8_generation_resume | runs/stage3c8_slurm/generation_resume.log | outputs/stage3c8/prospective_generation/raw/shard_00/result.json |
| visual_reasoning_stage3c8_generation_resume2 | running | Running GPU job visual_reasoning_stage3c8_generation_resume2 | runs/stage3c8_slurm/generation_resume2.log | outputs/stage3c8/prospective_generation/raw/shard_00/result.json |
| vr_s14b_controller_20261005 | running | Running GPU job vr_s14b_controller_20261005 | runs/stage14b/coordinator/slurm.log | outputs/stage14b/audit/coordinator |
| vr_s14b_main_observer_20261005 | running | Running GPU job vr_s14b_main_observer_20261005 | runs/stage14b/main_monitor/slurm.log | outputs/stage14b/audit/main_monitor |
| vr_s14b_oom_watch_20261005 | running | Running GPU job vr_s14b_oom_watch_20261005 | runs/stage14b/oom_watch/slurm.log | outputs/stage14b/audit/oom_watch |
| vr_s14b_oom_watch_after3am_20261006 | running | Running GPU job vr_s14b_oom_watch_after3am_20261006 | runs/stage14b/oom_watch_after3am_20261006/slurm.log | outputs/stage14b/audit/oom_watch |
| vr_s14b_oom_watch_after3am_20261007 | running | Running GPU job vr_s14b_oom_watch_after3am_20261007 | runs/stage14b/oom_watch_after3am_20261007/slurm.log | outputs/stage14b/audit/oom_watch |
| vr_s14b_oom_watch_node03_20261005 | running | Running GPU job vr_s14b_oom_watch_node03_20261005 | runs/stage14b/oom_watch_node03/slurm.log | outputs/stage14b/audit/oom_watch |
| vr_s14b_oom_watch_node07_20261005 | running | Running GPU job vr_s14b_oom_watch_node07_20261005 | runs/stage14b/oom_watch_node07/slurm.log | outputs/stage14b/audit/oom_watch |
| vr_stage12xs_v2_A_0 | running | Running GPU job vr_stage12xs_v2_A_0 | runs/stage12xs/v2/A_0/slurm.log | outputs/stage12xs/v2 |
| vr_stage12xs_v2_A_1 | running | Running GPU job vr_stage12xs_v2_A_1 | runs/stage12xs/v2/A_1/slurm.log | outputs/stage12xs/v2 |
| vr_stage12xs_v2_A_2 | running | Running GPU job vr_stage12xs_v2_A_2 | runs/stage12xs/v2/A_2/slurm.log | outputs/stage12xs/v2 |
| vr_stage12xs_v2_A_3 | running | Running GPU job vr_stage12xs_v2_A_3 | runs/stage12xs/v2/A_3/slurm.log | outputs/stage12xs/v2 |
| vr_stage12xs_v2_B_0 | running | Running GPU job vr_stage12xs_v2_B_0 | runs/stage12xs/v2/B_0/slurm.log | outputs/stage12xs/v2 |
| vr_stage12xs_v2_B_1 | running | Running GPU job vr_stage12xs_v2_B_1 | runs/stage12xs/v2/B_1/slurm.log | outputs/stage12xs/v2 |
| vr_stage12xs_v2_B_2 | running | Running GPU job vr_stage12xs_v2_B_2 | runs/stage12xs/v2/B_2/slurm.log | outputs/stage12xs/v2 |
| vr_stage12xs_v2_B_3 | running | Running GPU job vr_stage12xs_v2_B_3 | runs/stage12xs/v2/B_3/slurm.log | outputs/stage12xs/v2 |
| vr_stage12ys_v1_A_0 | running | Running GPU job vr_stage12ys_v1_A_0 | runs/stage12ys/v1/A_0/slurm.log | outputs/stage12ys/v1 |
| vr_stage12ys_v1_A_1 | running | Running GPU job vr_stage12ys_v1_A_1 | runs/stage12ys/v1/A_1/slurm.log | outputs/stage12ys/v1 |
| vr_stage12ys_v1_A_2 | running | Running GPU job vr_stage12ys_v1_A_2 | runs/stage12ys/v1/A_2/slurm.log | outputs/stage12ys/v1 |
| vr_stage12ys_v1_A_3 | running | Running GPU job vr_stage12ys_v1_A_3 | runs/stage12ys/v1/A_3/slurm.log | outputs/stage12ys/v1 |
| vr_stage12ys_v1_A_4 | running | Running GPU job vr_stage12ys_v1_A_4 | runs/stage12ys/v1/A_4/slurm.log | outputs/stage12ys/v1 |
| vr_stage12ys_v1_A_5 | running | Running GPU job vr_stage12ys_v1_A_5 | runs/stage12ys/v1/A_5/slurm.log | outputs/stage12ys/v1 |
| vr_stage12ys_v1_A_6 | running | Running GPU job vr_stage12ys_v1_A_6 | runs/stage12ys/v1/A_6/slurm.log | outputs/stage12ys/v1 |
| vr_stage12ys_v1_A_7 | running | Running GPU job vr_stage12ys_v1_A_7 | runs/stage12ys/v1/A_7/slurm.log | outputs/stage12ys/v1 |
| vr_stage12ys_v1_B_0 | running | Running GPU job vr_stage12ys_v1_B_0 | runs/stage12ys/v1/B_0/slurm.log | outputs/stage12ys/v1 |
| vr_stage12ys_v1_B_1 | running | Running GPU job vr_stage12ys_v1_B_1 | runs/stage12ys/v1/B_1/slurm.log | outputs/stage12ys/v1 |
| vr_stage12ys_v1_B_2 | running | Running GPU job vr_stage12ys_v1_B_2 | runs/stage12ys/v1/B_2/slurm.log | outputs/stage12ys/v1 |
| vr_stage12ys_v1_B_3 | running | Running GPU job vr_stage12ys_v1_B_3 | runs/stage12ys/v1/B_3/slurm.log | outputs/stage12ys/v1 |
| vr_stage12ys_v1_B_4 | running | Running GPU job vr_stage12ys_v1_B_4 | runs/stage12ys/v1/B_4/slurm.log | outputs/stage12ys/v1 |
| vr_stage12ys_v1_B_5 | running | Running GPU job vr_stage12ys_v1_B_5 | runs/stage12ys/v1/B_5/slurm.log | outputs/stage12ys/v1 |
| vr_stage12ys_v1_B_6 | running | Running GPU job vr_stage12ys_v1_B_6 | runs/stage12ys/v1/B_6/slurm.log | outputs/stage12ys/v1 |
| vr_stage12ys_v1_B_7 | running | Running GPU job vr_stage12ys_v1_B_7 | runs/stage12ys/v1/B_7/slurm.log | outputs/stage12ys/v1 |
| vr_stage12ys_v1_C_0 | running | Running GPU job vr_stage12ys_v1_C_0 | runs/stage12ys/v1/C_0/slurm.log | outputs/stage12ys/v1 |
| vr_stage12ys_v1_C_1 | running | Running GPU job vr_stage12ys_v1_C_1 | runs/stage12ys/v1/C_1/slurm.log | outputs/stage12ys/v1 |
| vr_stage12ys_v1_C_2 | running | Running GPU job vr_stage12ys_v1_C_2 | runs/stage12ys/v1/C_2/slurm.log | outputs/stage12ys/v1 |
| vr_stage12ys_v1_C_3 | running | Running GPU job vr_stage12ys_v1_C_3 | runs/stage12ys/v1/C_3/slurm.log | outputs/stage12ys/v1 |
| vr_stage13a_v1_P_0 | running | Running GPU job vr_stage13a_v1_P_0 | runs/stage13a/v1/P_0/slurm.log | outputs/stage13a/v1 |
| vr_stage13a_v1_P_1 | running | Running GPU job vr_stage13a_v1_P_1 | runs/stage13a/v1/P_1/slurm.log | outputs/stage13a/v1 |
| vr_stage13a_v1_P_2 | running | Running GPU job vr_stage13a_v1_P_2 | runs/stage13a/v1/P_2/slurm.log | outputs/stage13a/v1 |
| vr_stage13a_v1_P_3 | running | Running GPU job vr_stage13a_v1_P_3 | runs/stage13a/v1/P_3/slurm.log | outputs/stage13a/v1 |
| vr_stage13a_v1_P_4 | running | Running GPU job vr_stage13a_v1_P_4 | runs/stage13a/v1/P_4/slurm.log | outputs/stage13a/v1 |
| vr_stage13a_v1_P_5 | running | Running GPU job vr_stage13a_v1_P_5 | runs/stage13a/v1/P_5/slurm.log | outputs/stage13a/v1 |
| vr_stage13a_v1_P_6 | running | Running GPU job vr_stage13a_v1_P_6 | runs/stage13a/v1/P_6/slurm.log | outputs/stage13a/v1 |
| vr_stage13a_v1_P_7 | running | Running GPU job vr_stage13a_v1_P_7 | runs/stage13a/v1/P_7/slurm.log | outputs/stage13a/v1 |
| vr_stage13a_v1_P_recovery1 | running | Running GPU job vr_stage13a_v1_P_recovery1 | runs/stage13a/v1/P_recovery1/slurm.log | outputs/stage13a/v1 |
| vr_stage13b_v1_equal_initial8_2B_I_0 | succeeded | Finite worker completed; Stage13B scientific execution stopped at the initial-eight validity gate. | runs/stage13b/v1/equal_initial8_2B_I_0/slurm.log | outputs/stage13b/v1 |
| vr_stage13b_v1_equal_initial8_2B_I_1 | succeeded | Finite worker completed; Stage13B scientific execution stopped at the initial-eight validity gate. | runs/stage13b/v1/equal_initial8_2B_I_1/slurm.log | outputs/stage13b/v1 |
| vr_stage13b_v1_equal_initial8_2B_T_0 | succeeded | Finite worker completed; Stage13B scientific execution stopped at the initial-eight validity gate. | runs/stage13b/v1/equal_initial8_2B_T_0/slurm.log | outputs/stage13b/v1 |
| vr_stage13b_v1_equal_initial8_2B_T_1 | succeeded | Finite worker completed; Stage13B scientific execution stopped at the initial-eight validity gate. | runs/stage13b/v1/equal_initial8_2B_T_1/slurm.log | outputs/stage13b/v1 |
| vr_stage13b_v1_equal_initial8_8B_I_0 | succeeded | Finite worker completed; Stage13B scientific execution stopped at the initial-eight validity gate. | runs/stage13b/v1/equal_initial8_8B_I_0/slurm.log | outputs/stage13b/v1 |
| vr_stage13b_v1_equal_initial8_8B_I_1 | succeeded | Finite worker completed; Stage13B scientific execution stopped at the initial-eight validity gate. | runs/stage13b/v1/equal_initial8_8B_I_1/slurm.log | outputs/stage13b/v1 |
| vr_stage13b_v1_equal_initial8_8B_T_0 | cancelled | Cancelled before allocation at the mandatory Stage13B technical stop. | runs/stage13b/v1/equal_initial8_8B_T_0/slurm.log | outputs/stage13b/v1 |
| vr_stage13b_v1_equal_initial8_8B_T_1 | cancelled | Cancelled before allocation at the mandatory Stage13B technical stop. | runs/stage13b/v1/equal_initial8_8B_T_1/slurm.log | outputs/stage13b/v1 |
| vr_stage13b_v1_technical_2B_I_0 | succeeded | Finite worker completed; Stage13B scientific execution stopped at the initial-eight validity gate. | runs/stage13b/v1/technical_2B_I_0/slurm.log | outputs/stage13b/v1 |
| vr_stage13b_v1_technical_2B_T_0 | succeeded | Finite worker completed; Stage13B scientific execution stopped at the initial-eight validity gate. | runs/stage13b/v1/technical_2B_T_0/slurm.log | outputs/stage13b/v1 |
| vr_stage13b_v1_technical_4B_I_0 | succeeded | Finite worker completed; Stage13B scientific execution stopped at the initial-eight validity gate. | runs/stage13b/v1/technical_4B_I_0/slurm.log | outputs/stage13b/v1 |
| vr_stage13b_v1_technical_4B_T_0 | succeeded | Finite worker completed; Stage13B scientific execution stopped at the initial-eight validity gate. | runs/stage13b/v1/technical_4B_T_0/slurm.log | outputs/stage13b/v1 |
| vr_stage13b_v1_technical_8B_I_0 | succeeded | Finite worker completed; Stage13B scientific execution stopped at the initial-eight validity gate. | runs/stage13b/v1/technical_8B_I_0/slurm.log | outputs/stage13b/v1 |
| vr_stage13b_v1_technical_8B_T_0 | succeeded | Finite worker completed; Stage13B scientific execution stopped at the initial-eight validity gate. | runs/stage13b/v1/technical_8B_T_0/slurm.log | outputs/stage13b/v1 |
| vr_stage13c_v1_technical_buffer_T_0 | failed | Stage13C closed at forced-trace contract gate; no scientific generation. FAILED. | runs/stage13c/v1/technical_buffer_T_0/slurm.log | outputs/stage13c/v1 |
| vr_stage13c_v1_technical_buffer_T_1 | failed | Stage13C closed at forced-trace contract gate; no scientific generation. FAILED. | runs/stage13c/v1/technical_buffer_T_1/slurm.log | outputs/stage13c/v1 |
| vr_stage13c_v1_technical_buffer_loader_repair_T_0 | cancelled | Stage13C closed at forced-trace contract gate; no scientific generation. CANCELLED. | runs/stage13c/v1/technical_buffer_loader_repair_T_0/slurm.log | outputs/stage13c/v1 |
| vr_stage13c_v1_technical_buffer_loader_repair_T_1 | succeeded | Stage13C closed at forced-trace contract gate; no scientific generation. COMPLETED. | runs/stage13c/v1/technical_buffer_loader_repair_T_1/slurm.log | outputs/stage13c/v1 |
| vr_stage13d_v1_scientific_buffer_T_0 | succeeded | Stage13D complete: POST_EVIDENCE_MECHANISM_PARTIAL. COMPLETED. | runs/stage13d/v1/scientific_buffer_T_0/slurm.log | outputs/stage13d/v1 |
| vr_stage13d_v1_scientific_buffer_T_1 | succeeded | Stage13D complete: POST_EVIDENCE_MECHANISM_PARTIAL. COMPLETED. | runs/stage13d/v1/scientific_buffer_T_1/slurm.log | outputs/stage13d/v1 |
| vr_stage13d_v1_semantic_initial8_I_0 | succeeded | Stage13D complete: POST_EVIDENCE_MECHANISM_PARTIAL. COMPLETED. | runs/stage13d/v1/semantic_initial8_I_0/slurm.log | outputs/stage13d/v1 |
| vr_stage13d_v1_semantic_remaining_I_0 | succeeded | Stage13D complete: POST_EVIDENCE_MECHANISM_PARTIAL. COMPLETED. | runs/stage13d/v1/semantic_remaining_I_0/slurm.log | outputs/stage13d/v1 |
| vr_stage13d_v1_semantic_remaining_I_1 | succeeded | Stage13D complete: POST_EVIDENCE_MECHANISM_PARTIAL. COMPLETED. | runs/stage13d/v1/semantic_remaining_I_1/slurm.log | outputs/stage13d/v1 |
| vr_stage13d_v1_semantic_remaining_I_2 | succeeded | Stage13D complete: POST_EVIDENCE_MECHANISM_PARTIAL. COMPLETED. | runs/stage13d/v1/semantic_remaining_I_2/slurm.log | outputs/stage13d/v1 |
| vr_stage13d_v1_semantic_remaining_I_3 | succeeded | Stage13D complete: POST_EVIDENCE_MECHANISM_PARTIAL. COMPLETED. | runs/stage13d/v1/semantic_remaining_I_3/slurm.log | outputs/stage13d/v1 |
| vr_stage13d_v1_semantic_remaining_I_4 | succeeded | Stage13D complete: POST_EVIDENCE_MECHANISM_PARTIAL. COMPLETED. | runs/stage13d/v1/semantic_remaining_I_4/slurm.log | outputs/stage13d/v1 |
| vr_stage13d_v1_semantic_remaining_I_5 | succeeded | Stage13D complete: POST_EVIDENCE_MECHANISM_PARTIAL. COMPLETED. | runs/stage13d/v1/semantic_remaining_I_5/slurm.log | outputs/stage13d/v1 |
| vr_stage13d_v1_semantic_remaining_I_6 | succeeded | Stage13D complete: POST_EVIDENCE_MECHANISM_PARTIAL. COMPLETED. | runs/stage13d/v1/semantic_remaining_I_6/slurm.log | outputs/stage13d/v1 |
| vr_stage13d_v1_semantic_remaining_I_7 | succeeded | Stage13D complete: POST_EVIDENCE_MECHANISM_PARTIAL. COMPLETED. | runs/stage13d/v1/semantic_remaining_I_7/slurm.log | outputs/stage13d/v1 |
| vr_stage13d_v1_technical_buffer_T_0 | succeeded | Stage13D complete: POST_EVIDENCE_MECHANISM_PARTIAL. COMPLETED. | runs/stage13d/v1/technical_buffer_T_0/slurm.log | outputs/stage13d/v1 |
| vr_stage14b_confirmation_T_review_prepare_v1 | succeeded | terminal_reconciled | runs/stage14b/vr_stage14b_confirmation_T_review_prepare_v1/slurm.log | outputs/stage14b |
| vr_stage14b_confirmation_analysis_figures_v1 | succeeded | terminal_reconciled | runs/stage14b/vr_stage14b_confirmation_analysis_figures_v1/slurm.log | outputs/stage14b |
| vr_stage14b_confirmation_cpu_handoff_v1 | succeeded | terminal_reconciled | runs/stage14b/vr_stage14b_confirmation_cpu_handoff_v1/slurm.log | outputs/stage14b |
| vr_stage14b_confirmatory_I_0_20261006T092824 | succeeded | terminal_reconciled | runs/stage14b/confirmatory_I_0_20261006T092824/slurm.log | outputs/stage14b |
| vr_stage14b_confirmatory_I_1_20261006T092824 | succeeded | terminal_reconciled | runs/stage14b/confirmatory_I_1_20261006T092824/slurm.log | outputs/stage14b |
| vr_stage14b_confirmatory_T_0_20261006T092824 | succeeded | terminal_reconciled | runs/stage14b/confirmatory_T_0_20261006T092824/slurm.log | outputs/stage14b |
| vr_stage14b_confirmatory_T_1_20261006T092824 | succeeded | terminal_reconciled | runs/stage14b/confirmatory_T_1_20261006T092824/slurm.log | outputs/stage14b |
| vr_stage14b_confirmatory_T_2_20261006T092824 | succeeded | terminal_reconciled | runs/stage14b/confirmatory_T_2_20261006T092824/slurm.log | outputs/stage14b |
| vr_stage14b_confirmatory_T_3_20261006T092824 | succeeded | terminal_reconciled | runs/stage14b/confirmatory_T_3_20261006T092824/slurm.log | outputs/stage14b |
| vr_stage14b_confirmatory_T_4_20261006T092824 | succeeded | terminal_reconciled | runs/stage14b/confirmatory_T_4_20261006T092824/slurm.log | outputs/stage14b |
| vr_stage14b_confirmatory_T_5_20261006T092824 | succeeded | terminal_reconciled | runs/stage14b/confirmatory_T_5_20261006T092824/slurm.log | outputs/stage14b |
| vr_stage14b_final_closure_v2 | succeeded | complete_stop | runs/stage14b/vr_stage14b_final_closure_v2/slurm.log | outputs/stage14b |
| vr_stage14b_main_I_0_20261005T083622 | succeeded | terminal_reconciled | runs/stage14b/main_I_0_20261005T083622/slurm.log | outputs/stage14b |
| vr_stage14b_main_I_1_20261005T083622 | succeeded | terminal_reconciled | runs/stage14b/main_I_1_20261005T083622/slurm.log | outputs/stage14b |
| vr_stage14b_main_I_2_20261005T083622 | succeeded | terminal_reconciled | runs/stage14b/main_I_2_20261005T083622/slurm.log | outputs/stage14b |
| vr_stage14b_main_T_0_20261005T083622 | succeeded | terminal_reconciled | runs/stage14b/main_T_0_20261005T083622/slurm.log | outputs/stage14b |
| vr_stage14b_main_T_1_20261005T083622 | succeeded | terminal_reconciled | runs/stage14b/main_T_1_20261005T083622/slurm.log | outputs/stage14b |
| vr_stage14b_main_T_2_20261005T083622 | succeeded | terminal_reconciled | runs/stage14b/main_T_2_20261005T083622/slurm.log | outputs/stage14b |
| vr_stage14b_main_T_3_20261005T083622 | succeeded | terminal_reconciled | runs/stage14b/main_T_3_20261005T083622/slurm.log | outputs/stage14b |
| vr_stage14b_main_T_4_20261005T083622 | succeeded | terminal_reconciled | runs/stage14b/main_T_4_20261005T083622/slurm.log | outputs/stage14b |
| vr_stage14b_main_extract_t_20261006a | succeeded | terminal_reconciled | runs/stage14b/vr_stage14b_main_extract_t_20261006a/slurm.log | outputs/stage14b |
| vr_stage14b_main_freeze_extract_i_20261006 | failed | terminal_reconciled | runs/stage14b/vr_stage14b_main_freeze_extract_i_20261006/slurm.log | outputs/stage14b/audit/main_raw_seal.json |
| vr_stage14b_main_freeze_extract_i_resume_20261006 | succeeded | terminal_reconciled | runs/stage14b/vr_stage14b_main_freeze_extract_i_resume_20261006/slurm.log | outputs/stage14b/audit/main_raw_seal.json |
| vr_stage14b_preflight_I_0_20261005T065213 | running | Running GPU job vr_stage14b_preflight_I_0_20261005T065213 | runs/stage14b/preflight_I_0_20261005T065213/slurm.log | outputs/stage14b |
| vr_stage14b_preflight_I_0_20261005T070009 | running | Running GPU job vr_stage14b_preflight_I_0_20261005T070009 | runs/stage14b/preflight_I_0_20261005T070009/slurm.log | outputs/stage14b |
| vr_stage14b_preflight_T_0_20261005T065213 | running | Running GPU job vr_stage14b_preflight_T_0_20261005T065213 | runs/stage14b/preflight_T_0_20261005T065213/slurm.log | outputs/stage14b |
| vr_stage14b_preflight_T_0_20261005T070009 | running | Running GPU job vr_stage14b_preflight_T_0_20261005T070009 | runs/stage14b/preflight_T_0_20261005T070009/slurm.log | outputs/stage14b |
| vr_stage14b_primary_20261006T0925 | succeeded | terminal_reconciled | runs/stage14b/vr_stage14b_primary_20261006T0925/slurm.log | outputs/stage14b |
| vr_stage14b_secondary_20261006T0927 | succeeded | terminal_reconciled | runs/stage14b/vr_stage14b_secondary_20261006T0927/slurm.log | outputs/stage14b |
| vr_stage14c_fixed_context_replay_v1 | succeeded | Stage14C terminal: succeeded; see final audit receipts | runs/stage14c/fixed_context_replay_v1/slurm.log | outputs/stage14c/audit/g2_fixed_context_replay_repair_v1.json |
| vr_stage14c_main_I_0_20261009T034729 | succeeded | Stage14C terminal: succeeded; see final audit receipts | runs/stage14c/main_I_0_20261009T034729/slurm.log | outputs/stage14c |
| vr_stage14c_main_I_1_20261009T034729 | succeeded | Stage14C terminal: succeeded; see final audit receipts | runs/stage14c/main_I_1_20261009T034729/slurm.log | outputs/stage14c |
| vr_stage14c_main_T5_node06_move_v1 | succeeded | Stage14C terminal: succeeded; see final audit receipts | runs/stage14c/main_T5_node06_move_v1/slurm.log | outputs/stage14c |
| vr_stage14c_main_T_0_20261009T034729 | succeeded | Stage14C terminal: succeeded; see final audit receipts | runs/stage14c/main_T_0_20261009T034729/slurm.log | outputs/stage14c |
| vr_stage14c_main_T_1_20261009T034729 | succeeded | Stage14C terminal: succeeded; see final audit receipts | runs/stage14c/main_T_1_20261009T034729/slurm.log | outputs/stage14c |
| vr_stage14c_main_T_2_20261009T034729 | succeeded | Stage14C terminal: succeeded; see final audit receipts | runs/stage14c/main_T_2_20261009T034729/slurm.log | outputs/stage14c |
| vr_stage14c_main_T_3_20261009T034729 | succeeded | Stage14C terminal: succeeded; see final audit receipts | runs/stage14c/main_T_3_20261009T034729/slurm.log | outputs/stage14c |
| vr_stage14c_main_T_4_20261009T034729 | succeeded | Stage14C terminal: succeeded; see final audit receipts | runs/stage14c/main_T_4_20261009T034729/slurm.log | outputs/stage14c |
| vr_stage14c_main_T_5_20261009T034729 | cancelled | Stage14C terminal: cancelled; see final audit receipts | runs/stage14c/main_T_5_20261009T034729/slurm.log | outputs/stage14c |
| vr_stage14c_preflight_I_0_20261009T032203 | failed | Stage14C terminal: failed; see final audit receipts | runs/stage14c/preflight_I_0_20261009T032203/slurm.log | outputs/stage14c |
| vr_stage14c_preflight_I_0_20261009T032818 | succeeded | Stage14C terminal: succeeded; see final audit receipts | runs/stage14c/preflight_I_0_20261009T032818/slurm.log | outputs/stage14c |
| vr_stage14c_preflight_T_0_20261009T032203 | failed | Stage14C terminal: failed; see final audit receipts | runs/stage14c/preflight_T_0_20261009T032203/slurm.log | outputs/stage14c |
| vr_stage14c_preflight_T_0_20261009T032818 | succeeded | Stage14C terminal: succeeded; see final audit receipts | runs/stage14c/preflight_T_0_20261009T032818/slurm.log | outputs/stage14c |
| vr_stage1a2_faith_34 | running | Running GPU job vr_stage1a2_faith_34_a5000 | runs/vr_stage1a2_faith_34_a5000/slurm.log | outputs/stage1/protocol_pilot/faithfulness_40960/shards/example_34/run_summary.json |
| vr_stage1a2_faith_44 | running | Running GPU job vr_stage1a2_faith_44_a5000 | runs/vr_stage1a2_faith_44_a5000/slurm.log | outputs/stage1/protocol_pilot/faithfulness_40960/shards/example_44/run_summary.json |
| vr_stage1a2_faith_48 | running | Running GPU job vr_stage1a2_faith_48_a5000 | runs/vr_stage1a2_faith_48_a5000/slurm.log | outputs/stage1/protocol_pilot/faithfulness_40960/shards/example_48/run_summary.json |
| vr_stage1a2_greedy_completed | running | Running GPU job vr_stage1a2_greedy_completed_a4000 | runs/vr_stage1a2_greedy_completed_a4000/slurm.log | outputs/stage1/protocol_pilot/run_40960_greedy/shards/shard_completed/run_summary.json |
| vr_stage1a2_greedy_control44 | running | Running GPU job vr_stage1a2_greedy_control44_a5000 | runs/vr_stage1a2_greedy_control44_a5000/slurm.log | outputs/stage1/protocol_pilot/run_40960_greedy/shards/shard_control_44/run_summary.json |
| vr_stage1a2_greedy_control48 | running | Running GPU job vr_stage1a2_greedy_control48_a5000 | runs/vr_stage1a2_greedy_control48_a5000/slurm.log | outputs/stage1/protocol_pilot/run_40960_greedy/shards/shard_control_48/run_summary.json |
| vr_stage1a2_greedy_controls | running | Running GPU job vr_stage1a2_greedy_controls_a5000 | runs/vr_stage1a2_greedy_controls_a5000/slurm.log | outputs/stage1/protocol_pilot/run_40960_greedy/shards/shard_completed/run_summary.json |
| vr_stage1a2_greedy_long23 | running | Running GPU job vr_stage1a2_greedy_long23_a4000 | runs/vr_stage1a2_greedy_long23_a4000/slurm.log | outputs/stage1/protocol_pilot/run_40960_greedy/shards/shard_long_23/run_summary.json |
| vr_stage1a2_greedy_long23_retry | running | Running GPU job vr_stage1a2_greedy_long23_a5000 | runs/vr_stage1a2_greedy_long23_a5000/slurm.log | outputs/stage1/protocol_pilot/run_40960_greedy/shards/shard_long_23/run_summary.json |
| vr_stage1a2_greedy_long33 | running | Running GPU job vr_stage1a2_greedy_long33_a5000 | runs/vr_stage1a2_greedy_long33_a5000/slurm.log | outputs/stage1/protocol_pilot/run_40960_greedy/shards/shard_long_33/run_summary.json |
| vr_stage1a2_greedy_long34 | running | Running GPU job vr_stage1a2_greedy_long34_a5000 | runs/vr_stage1a2_greedy_long34_a5000/slurm.log | outputs/stage1/protocol_pilot/run_40960_greedy/shards/shard_long_34/run_summary.json |
| vr_stage1a2_greedy_long39 | running | Running GPU job vr_stage1a2_greedy_long39_a5000 | runs/vr_stage1a2_greedy_long39_a5000/slurm.log | outputs/stage1/protocol_pilot/run_40960_greedy/shards/shard_long_39/run_summary.json |
| vr_stage1a2_greedy_long43 | running | Running GPU job vr_stage1a2_greedy_long43_a5000 | runs/vr_stage1a2_greedy_long43_a5000/slurm.log | outputs/stage1/protocol_pilot/run_40960_greedy/shards/shard_long_43/run_summary.json |
| vr_stage1a2_official_s00 | running | Running GPU job vr_stage1a2_official_s00_a5000 | runs/vr_stage1a2_official_s00_a5000/slurm.log | outputs/stage1/protocol_pilot/run_40960_official/shards/shard_00/run_summary.json |
| vr_stage1a2_official_s01 | running | Running GPU job vr_stage1a2_official_s01_a5000 | runs/vr_stage1a2_official_s01_a5000/slurm.log | outputs/stage1/protocol_pilot/run_40960_official/shards/shard_01/run_summary.json |
| vr_stage1a2_official_s02 | running | Running GPU job vr_stage1a2_official_s02_a4000 | runs/vr_stage1a2_official_s02_a4000/slurm.log | outputs/stage1/protocol_pilot/run_40960_official/shards/shard_02/run_summary.json |
| vr_stage1a2_official_s02_retry | running | Running GPU job vr_stage1a2_official_s02_retry_a5000 | runs/vr_stage1a2_official_s02_retry_a5000/slurm.log | outputs/stage1/protocol_pilot/run_40960_official/shards/shard_02/run_summary.json |
| vr_stage1a2_official_s03 | running | Running GPU job vr_stage1a2_official_s03_a5000 | runs/vr_stage1a2_official_s03_a5000/slurm.log | outputs/stage1/protocol_pilot/run_40960_official/shards/shard_03/run_summary.json |
| vr_stage1a2_official_s04 | running | Running GPU job vr_stage1a2_official_s04_a5000 | runs/vr_stage1a2_official_s04_a5000/slurm.log | outputs/stage1/protocol_pilot/run_40960_official/shards/shard_04/run_summary.json |
| vr_stage1b_discovery_s00 | running | Running GPU job vr_stage1b_discovery_s00_a5000 | runs/vr_stage1b_discovery_s00_a5000/slurm.log | outputs/stage1/discovery/shards/shard_00/run_summary.json |
| vr_stage1b_discovery_s01 | running | Running GPU job vr_stage1b_discovery_s01_a5000 | runs/vr_stage1b_discovery_s01_a5000/slurm.log | outputs/stage1/discovery/shards/shard_01/run_summary.json |
| vr_stage1b_discovery_x00 | running | Running GPU job vr_stage1b_discovery_x00_a5000 | runs/vr_stage1b_discovery_x00_a5000/slurm.log | outputs/stage1/discovery/shards_07/shard_00/run_summary.json |
| vr_stage1b_discovery_x01 | running | Running GPU job vr_stage1b_discovery_x01_a5000 | runs/vr_stage1b_discovery_x01_a5000/slurm.log | outputs/stage1/discovery/shards_07/shard_01/run_summary.json |
| vr_stage1b_discovery_x02 | running | Running GPU job vr_stage1b_discovery_x02_a5000 | runs/vr_stage1b_discovery_x02_a5000/slurm.log | outputs/stage1/discovery/shards_07/shard_02/run_summary.json |
| vr_stage1b_discovery_x03 | running | Running GPU job vr_stage1b_discovery_x03_a5000 | runs/vr_stage1b_discovery_x03_a5000/slurm.log | outputs/stage1/discovery/shards_07/shard_03/run_summary.json |
| vr_stage1b_discovery_x04 | running | Running GPU job vr_stage1b_discovery_x04_a5000 | runs/vr_stage1b_discovery_x04_a5000/slurm.log | outputs/stage1/discovery/shards_07/shard_04/run_summary.json |
| vr_stage1b_discovery_x05 | running | Running GPU job vr_stage1b_discovery_x05_a5000 | runs/vr_stage1b_discovery_x05_a5000/slurm.log | outputs/stage1/discovery/shards_07/shard_05/run_summary.json |
| vr_stage1b_discovery_x06 | running | Running GPU job vr_stage1b_discovery_x06_a5000 | runs/vr_stage1b_discovery_x06_a5000/slurm.log | outputs/stage1/discovery/shards_07/shard_06/run_summary.json |



## Stage14D — G0 preparation / no generation (2026-10-10T15:44:07.579363+00:00)
[Concrete review package](../outputs/stage14d/reports/stage14d_g0_review_package.md) · [Stage index](stage14d/index.md) · [Phase](../workspace/phase_memory/phase_14d_causal_evidence_acquisition.md). Proposed300Thinking/120Instruct diagnostic IDs,17CPUchecks; awaiting explicit technical-budget release and remaining prerequisite/source/backend gates.
