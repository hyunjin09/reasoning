# Phase 3B.4: Restoration-controlled module localization

## Current Objective

Determine whether the late evidence-specific current-position transfer at the frozen `E_d-1`/`E_d` decisions and retained F28_29/F32_33 layer windows is implemented primarily by self-attention output, MLP output, their joint contribution, or the full block state.

## Active Constraints

- Reuse the frozen 41-base Stage 3B.3-R primary cohort; paired semantic restoration uses the 37 numeric O/O_sham/C/C_sham bases.
- Use the eight disjoint Stage 3B.3-R validation bases before touching the primary cohort.
- Load retained windows from frozen artifacts: W4/F28_29 = layers 28--29 and W5/F32_33 = layers 32--33.
- Patch only the current evidence-decision position at frozen `E_d-1` and `E_d` coordinates.
- Primary evidence is paired semantic restoration. Knockout/zeroing is not a primary causal measure and is omitted unless separately justified.
- Preserve the A5000 eager-attention path; attention magnitude does not select examples, layers, or modules.
- Stop before head/path/ROI/Q-R/multi-evidence/failure experiments.

## Current State

- Done: Stage 3B.3-R passed 16/16 criteria on 41 primary bases and recommended module/path localization for review.
- Done: the user explicitly authorized `plan/stage3b4_plan.md` on 2026-09-01.
- Done: installed Qwen3-VL block ordering and exact hook surfaces were audited read-only before implementation.
- Done: Stage 3B.4 configuration, hook contracts, the 16-test primary family, and decision rules were frozen before validation outcomes were inspected.
- Done: all eight independent A5000 validation bases passed baseline reproduction, exact hook/current-position audits, self transparency, finite output, deterministic replication, sham/render, and full-block bridge gates.
- Done: the prospectively authorized 37-base paired primary family and all fixed statistics/figures/reports are complete; the four structural bases remain manifest-only because no matched C_sham exists.
- Blocked: none.
- Most recent useful observation: the only retained fine windows inside W4/W5 are F28_29 and F32_33; the eight validation bases are disjoint from all 41 primary bases.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| W4/F28_29 and W5/F32_33 retain paired effects at both coordinates | `outputs/stage3b3_redesign/analysis/fine_layer_statistics.json` | Freezes the only Stage 3B.4 layer targets | confirmed |
| W4 paired restoration is bidirectional for 37/37 primary numeric bases | `outputs/stage3b3_redesign/analysis/semantic_restoration_statistics.json` | Justifies restoration-controlled module decomposition | confirmed |
| Eight validation bases are disjoint from 41 primary bases | `outputs/stage3b3_redesign/config/validation_manifest.jsonl`; `outputs/stage3b3_redesign/primary/primary_41_manifest.jsonl` | Enables a genuine pre-primary module-hook gate | confirmed |
| Qwen text block is pre-norm attention, residual add, pre-norm MLP, residual add | `.venv/lib/python3.12/site-packages/transformers/models/qwen3_vl/modeling_qwen3_vl.py` | Defines exact attention/MLP/block hook locations | confirmed |
| A6000 drift is comparable to weak/fine effects | `outputs/stage3b3_redesign/config/node03_drift_analysis.json` | Requires a single A5000 scientific path | confirmed |
| Eight-base Stage 3B.4 method gate passed | `outputs/stage3b4/validation/validation_results.json` | Prospectively authorizes primary scoring | confirmed |
| Full block is robust in 4/4 cells but no component-attribution rule passes | `outputs/stage3b4/analysis/decision_rule_evaluation.json` | Redirects interpretation toward unresolved distributed/sequential block computation | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Original Stage 3B.3 restoration smoke | Sham/target ratio 0.314949 exceeded 0.25 | unknown | Module claims require paired semantic restoration | Do not infer identity carriage from damage or unpaired patches |
| Stage 3B.3-R node03 A6000 check | Bit-exact baseline/all-layer reproduction failed | supported hardware numerical drift | Keep primary and validation on A5000 | Do not mix A5000 and A6000 module scores |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Attention-mediated transfer | Visual-source K/V switching localized to late layers | Paired current-position attention-output restoration | open |
| MLP-mediated construction | Current-position residual identity emerges sharply after late blocks | Paired current-position MLP-output restoration | open |
| Attention-to-MLP cascade | Attention may route identity that MLP transforms | Compare attention, MLP, joint, and block restoration | open |
| Distributed block interaction | Singles may be weak while full block is strong | Preserve full-block bridge and interaction statistic | open |

## Next-Step Decision

- Current bottleneck: Stage 3B.4 is complete; review is required before selecting any later research action.
- Relevant memory item used: D-022 localizes transfer to W4/W5 while explicitly leaving module implementation unresolved; D-020 forbids returning to uncontrolled restoration.
- Chosen next action: stop after reporting the frozen Stage 3B.4 result and its distributed-block redirect.
- Why this action: it is the smallest causal decomposition that distinguishes the four mechanisms allowed by the handoff while preserving paired render controls.
- What not to repeat: do not use attention magnitude, ablation damage, new layer search, or post-outcome cohort/module expansion as primary evidence.
- Stop condition: after validation, conditionally authorized primary scoring, fixed-family statistics, figures, acceptance, and one recommendation, stop before all head/path/ROI/Q-R/later experiments.

### Step Result

- Action taken: froze and implemented the module family, passed the eight-base independent A5000 validation, then scored and aggregated 37 paired primary bases.
- Result: technical PASS (16/16) and **REDIRECT — Distributed block computation**. Block restoration was robust in 4/4 cells; 14/16 total cells were robust, but Attention/Block medians were 0.137--0.411, MLP/Block 0.040--0.143, and Joint/Block 0.329--0.539, so no frozen component category passed.
- Evidence saved: `outputs/stage3b4/validation/validation_results.json`, `outputs/stage3b4/analysis/module_restoration_statistics.json`, `outputs/stage3b4/analysis/decision_rule_evaluation.json`, and `outputs/stage3b4/summaries/stage3b4_acceptance.json`.
- Failure or issue: none.
- Lesson learned: current-position module capture/restoration is mechanically transparent on the frozen A5000 path; isolated component restoration does not explain the full late-block effect at the prespecified thresholds.
- Next implication: preserve sequential block interactions, normalization/residual effects, and restoration non-additivity as alternatives. No later experiment is authorized.
