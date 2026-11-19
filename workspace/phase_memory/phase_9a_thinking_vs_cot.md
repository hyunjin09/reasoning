# Phase 9A: Thinking vs prompted CoT visual access

## Current Objective
Execute the approved128-item, three-arm native regime comparison; distinguish recurrent demand-aligned access from generation length and detector calibration.

## Active Constraints
- Plan: `plan/stage9a_thinking_vs_cot_visual_access_regimes_plan.md`; frozen definitions: `plan/stage9a_execution_protocol_v1.md`.
- Existing local MathVision and pinned2B Instruct/Thinking; BF16 native protocol, max40960, no Stage8 changes.
- Scheduler/Slurm only; available node02/node03/node06/node07 (user amendment); maximum4 GPUs total. No tmux or keepalive.
- Outcome-masked semantic demand review before retrieval/accuracy/causal results; family statistical units; no later-stage launch.

## Current State
- Complete: all384 native trajectories;700 semantic nominations (539 accepted,126 rejected,35 unknown); 610 source/readout and384 answer reviews;50 frozen causal events.
- Complete: all13 artifacts and5 figures, frozen primary/matched/adjusted analyses, secondary accuracy,18 focused tests.
- Result:0/4 positive primary Thinking−CoT contrasts; density2.437 versus5.122 episodes/1k tokens. Only9 matched-length families; causal16/16/18 below arm inference threshold. No equivalence claim.
- All50 native-prefix/capture/self-sham checks pass; all native artifact hashes verified. All allocations released. No blocked or pending work for Stage9A.
- Evidence: `outputs/stage9a/v1/stage9a_summary.md` and `outputs/stage9a/v1/audit/final_validation.json`.

## Evidence That Matters
| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
|1507 unused representatives|outputs/stage8c_v2/v1/audit/remaining_family_representatives.json|Avoid prior intervention-development and held-out families|confirmed|
|Conditional sparse lineage in Block3B|workspace/decision_log.md D-093|Unknown semantic coverage cannot become zero|confirmed|
|Identical architecture, different native templates|pinned model configs/templates in Stage9A config|Architecture-matched observations; preserve template contrast|confirmed|

## Failed Attempts and Lessons
Node07 preflight stalled in startup RPC/filesystem I/O before inference; underlying cause unknown. Cancelled and recovered on authorized node06 with the same frozen science. No repeated node07 trial.

The proposed positive regime gate was not met. Total episode count, per-token density, paired demand support and secondary accuracy must stay distinct. Source/length eligibility shortfalls remain uncertainty, not zero or equivalence.

## Open Candidates
None selected. Stage9A is complete; later stages or rescue experiments require a new user instruction.

## Next-Step Decision
- Current bottleneck: no authorized work remains.
- Evidence used: frozen primary effects, nine matched families,50 causal checks and final integrity/release audit.
- Exactly one recommendation: stop the Stage9 bottleneck/bypass branch and retain the existing reasoning-conditioned dynamic visual-retrieval framing.
- No new action selected or executed. Do not widen the caliper, tune prompts/thresholds, replace the cohort or launch same-prefix/bypass work to rescue this result.
- Stop condition met:13 outputs,5 figures,one recommendation,all GPUs released.

### Step Result
Completed 2026-09-24T06:07:45.492795+00:00. The primary hypothesis is unsupported in this native comparison; matched/causal precision limits prevent an equivalence claim. Historical execution observations follow.

Resource update: initial node02 capacity was consumed before submission; no Slurm job launched. User adds node07; five free GPUs observed. Preflight moves to node07, unchanged native/analysis protocol.

### Startup observation (Slurm120840, node07)
GPU-bound NVML query reports allocated GPU0 healthy/idle (2MiB,0%); preflight has no initial model/arm output after6min.60s process-state step and20s SSH probe did not return. Cause unknown; no inference or OOM has been observed. One extended180s process-state diagnostic pending because the successful GPU-status step also had substantial launch latency. No production jobs requested pending parity gate. Earlier --gres=none NVML check returned no devices as expected for an unbound step and is not hardware-failure evidence.

### Recovery decision and resource boundary
- Direct evidence: `outputs/stage9a/v1/audit/node07_startup_diagnostic.json`. Python was in D/rpc_wait_bit_killable; underlying filesystem/service cause unknown. GPU itself responds; no OOM/model inference observed.
- Slurm120840 cancelled, all GPU resources released; zero trajectories or preflight checks. Remote probe descendants cleaned up.
- Do not retry node07 without evidence its startup-access condition changed. User permission to use node07 remains valid.
- Chosen repair: same frozen preflight on the first available node02/node03/node06, then up to4 workers; resource choice only, no scientific change.
- Low-frequency coordinator runs for at most72h, stops on failure or after native export, never launches later research. Evidence: audit/dispatcher_launch.json and audit/dispatcher_status.json.
- Native384 completion does not complete Stage9A: masked review, eligible causal pilot and all required analyses/figures remain.

Progress check 2026-09-23T11:08:15.601863+00:00: `outputs/stage9a/v1/audit/progress_20260923T110815Z.json`. Reviews, causal validation and final analysis have not been completed.

Native completion verified 2026-09-24T04:42:48.908068+00:00: `outputs/stage9a/v1/audit/native_verified_20260924T044159Z.json`. Three table hashes match,128 distinct families per arm,384 task receipts and packets; referenced raw artifacts exist. Full raw-feature rehash not performed in this bounded status check. Empty live Slurm queue confirms GPU release. Next: complete masked annotations before opening routing/accuracy/causal comparisons.

Completion action resumed: preserve all384 native outputs; review the frozen700 nominations and128 source images, seal semantic/source/readout eligibility before routing/accuracy/causal outcomes, then run only the approved bounded causal validation and final analysis. No generation rerun or follow-on stage.

### Masked semantic review, 2026-09-24
All700 frozen nominations explicitly reviewed by the main Codex annotator:539 accepted,126 rejected,35 unknown across102 accepted-event image families. No detector/raw-routing, accuracy or causal results opened for review. Evidence: `outputs/stage9a/v1/annotations/semantic_review_complete.json`. No-candidate packets remain unobserved, not negative. Next: source/ROI/local-readout and donor feasibility review, then immutable causal selection and planned replay/analysis. Single-agent annotations are not independent human review.

### Causal selection sealed, 2026-09-24T05:22:01.830392+00:00
610 masked source/readout nominations reviewed;50 distinct family/arm events frozen (Direct16, CoT16, Thinking18). Source glyph/color, donor and irrelevant token crops inspected; coordinate/word-boundary repairs preserved before outcome access. Below24-per-arm feasibility goal: report limitation, never unknown-as-zero. Execute only frozen fixed-history native/target/irrelevant/self-Value validation and planned family/length analysis. Evidence: `outputs/stage9a/v1/annotations/causal_selection_frozen.json`.

### Analysis execution checkpoint
All384 masked answer extractions reviewed and sealed before gold comparison; raw-adapter and reviewed accuracy preserved separately. GPU121562–121564/node06 perform50 frozen causal events with exact native-feature, capture and self/sham gates; initial25 all exact. CPU-only121568/node03 verifies all native artifact hashes and executes frozen primary/matched/adjusted analyses. No next-stage action selected.

### Final aggregation repair
The first deterministic merge incorrectly demanded bit-exact zero from derived FP64 JS. All50 raw-logit/self-score gates remained exact. Supported roundoff diagnosis and narrowly scoped CPU parser repair: `outputs/stage9a/v1/audit/causal_aggregation_roundoff_repair.json`. No raw evidence changed or GPU experiment repeated.

### Final closure — 2026-09-24T06:07:45.492795+00:00
Stage 9A COMPLETE / STOP. All 384 native trajectories, 700 semantic reviews, 610 source/readout reviews, 384 answer reviews and 50 causal checks complete; 13 artifacts, five figures and 18 focused tests verified. Zero of four primary contrasts supports the proposed positive Thinking-specific regime; nine length-matched families and causal samples 16/16/18 limit inference. Exactly one recommendation: stop the Stage 9 bottleneck/bypass branch and retain reasoning-conditioned dynamic visual retrieval. All GPUs released; no follow-on launched.
