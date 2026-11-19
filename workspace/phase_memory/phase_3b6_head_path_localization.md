# Phase 3B.6: Restoration-controlled attention-head and source-path localization

## Current Objective

Identify which logical query-head computations account for the three frozen Stage 3B.5 post-Attention gains and, only after a head-level gate passes, whether their evidence-specific input comes primarily from visual (`V`), eligible nonvisual prefix (`P`), or prior reasoning (`R`) token states.

## Active Constraints

- Preserve exactly the Stage 3B.5 qualifying cells `E_d-1/W4`, `E_d-1/W5`, and `E_d/W4`, plus `E_d/W5` as an upstream-state control.
- Load exact layer roles from frozen Stage 3B.5 artifacts: layer 28, layer 32, and layer 29 respectively; use layer 32 for the upstream control.
- Use the eight disjoint Stage 3B.5 validation bases for all-head discovery and the exact 37 paired numeric bases for confirmation.
- Select heads only by paired causal restoration, never by raw attention.
- Keep O/O_sham/C/C_sham, reciprocal O↔C restoration, exact self controls, current-position query-head selectivity, and base-level statistics.
- Freeze discovery and confirmation rules before reading Stage 3B.6 scores. Discovery robustness requires median BHR > 0, at least 7/8 bidirectionally consistent bases, median sham/semantic ratio <= 0.25, exact self controls, and median recovery relative to the frozen Stage 3B.5 Attention gain >= 0.10. Confirmation requires Holm-adjusted p < 0.05, median bootstrap CI low > 0, bidirectional fraction >= 0.70, median sham/semantic ratio < 0.25, exact self controls, and median recovery relative to the frozen Attention gain >= 0.25.
- Run source-path decomposition only when at least one frozen single head or cumulative Top-k set passes confirmation; freeze the minimal passing unit per cell before path scoring.
- Classify cumulative recovery prospectively at 75% of the frozen Attention gain: Top-1/2=sparse, first Top-4=small ensemble, first Top-8/All-robust=distributed; classify a source as dominant only when its median PRR is at least 0.75 and every other single-source PRR is below 0.50.
- Apply the frozen recommendation hierarchy: no confirmed head→REDIRECT; otherwise visual-dominant→ROI GO, P/R-dominant→language-side GO, distributed heads or mixed/redundant paths→multi-head GO, and unresolved partial recovery→REDIRECT.
- Use the user-provided active Slurm allocation in `tmux` session 8 only after verifying A5000×2 provenance and recording it in the project scheduler state. Submit no new Slurm job.
- Stop before ROI, K-vs-V, pattern/value, MLP feature, Q/R lifecycle, multi-evidence, failure, or any later-stage experiment.

## Current State

- Done: Stage 3B.5 passed 17/17 criteria and independently validated all 1,480 paired metrics.
- Done: the user explicitly authorized `plan/stage3b6_plan.md` on 2026-09-01.
- Done: `tmux` session 8 was verified as an interactive shell under active Slurm job 106936 on node04 with two A5000 GPUs; the project scheduler sees the two-user-GPU allocation.
- Done: the protocol, GQA mapping, discovery/primary split, candidate rules, source classes, and recommendation hierarchy were frozen before scores were read.
- Done: the discovery screen, 37-base confirmation, upstream control, gated V/P/R source decomposition, secondary triangulation, and independent artifact validation completed in `tmux` session 8.
- Done: Stage 3B.6 passes 17/17 technical criteria and 20/20 independent artifact checks.
- Stopped: the recommendation is **GO — ROI-specific visual path + pattern/value decomposition** for review only; no follow-on experiment was started.
- Blocked: none.
- Most recent useful observation: two independently frozen targets have robust V-dominant source restoration (`E_d/W4` Top-4 V PRR 0.979; `E_d-1/W4` Top-2 V PRR 0.885), while the high `E_d-1/W5` head-10 V point estimate fails the frozen sham-control gate and remains inconclusive.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Three post-Attention cells qualify and `E_d/W5` is upstream-only | `outputs/stage3b5/analysis/decision_rule_evaluation.json` | Fixes the cells and exact layer roles without reopening selection | confirmed |
| Stage 3B.5 raw residual restoration plus downstream recompute is validated | `outputs/stage3b5/validation/validation_results.json` | Supplies the causal boundary effect that head restoration must recover | confirmed |
| Qwen text Attention has 32 query heads, 8 K/V heads, and 128-dimensional heads | `outputs/stage3b0/layout_audit/cache_shape_diagnostics.json`; installed Qwen implementation | Requires query-head intervention after GQA expansion rather than one shared-K/V-head replacement | confirmed |
| Paired O/O_sham/C/C_sham controls separate semantic from render effects | `code/visual_reasoning/stage3b3_redesign/metrics.py` | Defines the validated restoration contrast for head and path scoring | confirmed |
| Active A5000 allocation is Slurm job 106936 in `tmux` 8 | live `squeue`, scheduler status, and tmux pane audit | Authorizes the requested execution shell without a new submission | confirmed |
| Ten of fourteen frozen head/set tests pass confirmation | `outputs/stage3b6/analysis/head_restoration_statistics.json` | Establishes causal head localization in all three qualifying cells | confirmed |
| Two minimal targets have robust V-dominant paths | `outputs/stage3b6/analysis/source_path_statistics.json` | Supports a reviewed ROI/pattern-value follow-on without treating attention weights as causal evidence | confirmed |
| `E_d-1/W5` V-only recovery fails the sham gate | `outputs/stage3b6/analysis/source_path_statistics.json` | Prevents overclaiming a third V-dominant result | confirmed |
| All required artifacts validate independently | `outputs/stage3b6/analysis/artifact_validation.json` | Confirms 20/20 schema, metric, cohort, freeze, and stop-boundary checks | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Raw attention as acquisition timing | 58/70 Stage 2C events were mention-centered | supported | Attention magnitude is secondary, not a selection criterion | Do not rank heads by attention |
| Shared K/V-head replacement as logical head attribution | One K/V head serves four query heads under GQA | architectural | Recompute swapped K/V attention and splice only selected logical query-head outputs before `W_O` | Do not equate a K/V group with a query head |
| Stage 3B.4 precomputed module output restoration | It under-recovered robust block effects | unresolved by that design | Keep recipient query, recompute semantic attention from source K/V, and allow natural downstream recomputation | Do not use a precomputed output patch as the primary arm |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Sparse head mechanism | A late post-Attention gain may be carried by one or two query heads | All-32 discovery then frozen Top-1/2 confirmation | supported in `E_d-1/W4`; not universal |
| Small or distributed head ensemble | Output projection can combine multiple weak head contributions | Frozen Top-4/8 and all-robust cumulative restoration | supported in `E_d/W4`; not universal |
| Direct visual source path | Stage 3B.1 and 3B.2 show persistent evidence-specific visual dependence | V-only versus P-only/R-only semantic K/V swaps in confirmed heads | supported in two cells |
| Language-side source path | Earlier stages found a small Q-carried prefill residual | P-only and R-only swaps under the same causal head intervention | not supported at the three frozen minimal targets |
| ROI and K-versus-V/pattern-value localization | Two cells pass the robust V-dominance rule | Requires a new prospective, separately authorized experiment | recommended for review only |

## Next-Step Decision

- Current bottleneck: Stage 3B.6 identifies robust visual-source restoration in selected late Attention heads but does not identify the responsible ROI or separate K/source-pattern effects from V/content effects.
- Relevant memory item used: V alone passed the frozen robust-dominance rule in two cells; the third high-PRR V arm failed the sham gate, and raw attention magnitude was not used for selection.
- Chosen next action: stop and return the Stage 3B.6 evidence for joint review. The prospective recommendation is ROI-specific visual path plus pattern/value decomposition, but it is not authorized here.
- Why this action: the bounded Stage 3B.6 action is complete, and the plan explicitly prohibits beginning ROI or K-vs-V/pattern-value work.
- What not to repeat: no attention-based selection, unpaired shams, shared-K/V-head attribution, A6000/A5000 mixing, or promotion of a high PRR that fails the sham-control gate.
- Stop condition: satisfied; final recommendation, 17/17 acceptance, and 20/20 independent validation are written.

### Step Result

- Action taken: screened all 32 logical query heads on eight frozen discovery bases; froze candidates; confirmed 14 tests on 37 bases; evaluated the `E_d/W5` control; and decomposed all/V/P/R sources for the three minimal passing targets.
- Result: 10/14 head/set tests confirmed. `E_d-1/W4` is H-Sparse, while `E_d/W4` and `E_d-1/W5` are H-Partial-Recovery. V is robustly dominant for `E_d/W4` Top-4 and `E_d-1/W4` Top-2. The `E_d-1/W5` head-10 V arm has PRR 0.989 but a sham/semantic ratio of 0.436 and is therefore inconclusive under the frozen rule.
- Evidence saved: `outputs/stage3b6/analysis/head_restoration_statistics.json`, `source_path_statistics.json`, `upstream_control_statistics.json`, `artifact_validation.json`, and `outputs/stage3b6/summaries/stage3b6_summary.md`.
- Failure or issue: no technical failure. The secondary cutoff association is unclear, and the third source-path attribution is limited by its sham control.
- Lesson learned: causal head/source restoration and raw attention magnitude are distinct; robust visual-source attribution requires paired semantic effects to exceed render/sham artifacts.
- Next implication: **GO — ROI-specific visual path + pattern/value decomposition** for review only. No later-stage work has begun.
