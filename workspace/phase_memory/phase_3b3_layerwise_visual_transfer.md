# Phase 3B.3: Layer-wise visual-to-reasoning transfer

## Current Objective

Localize across the 36 language layers where counterfactual visual-source identity causally influences the frozen evidence decision and where that identity becomes causally present in the current query-position residual.

## Active Constraints

- Use the exact frozen 49-base Stage 3A/3B.2 cohort; `base_problem_id` is the statistical unit.
- Analyze both `E_d-1` and `E_d` with six prospectively frozen 6-layer windows.
- Combine selective sufficiency, restoration necessity, cumulative lower/suffix switching, and current-position residual patching.
- Freeze the fine-localization rule before the coarse cohort and refine only qualifying/adjacent regions with 2-layer windows.
- Use the validated A5000 eager-attention path so the all-layer control can reproduce Stage 3B.2.
- Attention is not used for cohort/window selection. Stop before module/head/path/Q-R/ROI-specific or later experiments.

## Current State

- Done: Stage 3B.2 passed 16/16 criteria; 49/49 bases were bidirectionally source-consistent at `E_d-1` and `E_d`.
- Done: the Stage 3B.3 configuration, coarse/cumulative windows, residual boundaries, fine rule, decision rules, and smoke thresholds were frozen before scoring.
- Stopped: the mandatory three-base smoke passed 11/12 checks but failed the frozen restoration sham/target ratio gate (0.314949 > 0.25).
- Preserved as unrun: the original failed-protocol 49-base Stage 3B.3 cohort. Its separately authorized paired-restoration redesign is completed below; all later experiments remain unrun.
- Most recent useful observation: all-layer/no-switch reproduction and intervention mechanics are exact, but window restoration is not sufficiently evidence-specific under the frozen sham gate.
- Stage 3B.3-R progress: the seed-20260901 8/41 split, semantic restoration estimand, base-aggregated gates, and paired-source stop controls are frozen. The validation bases are `6, 83, 93, 96, 101, 126, 136, 148`; five use exact baseline tokens.
- Stage 3B.3-R image controls: all eight numeric O/O_sham/C/C_sham quartets pass automatic pixel checks and manual full-image/5x-ROI inspection before scoring. Structural restoration was prospectively omitted as allowed by the plan.
- Stage 3B.3-R validation execution: eight one-base A5000 jobs (`106641`--`106647`, `106649`) completed before the reserved 41 bases were authorized or scored.
- Hardware feasibility diagnostic: one prespecified technical-only A6000 check was mechanically valid and finite but failed bit-exact no-switch/all-layer reproduction, so A6000 was rejected without inspecting redesign effects. Evidence: `outputs/stage3b3_redesign/config/hardware_fallback_decision.json`.
- Stage 3B.3-R validation result: **PASS**. All mechanical, paired all-layer, paired selective-window, and restoration Gates A--D pass on 8/8 independent bases. All eight bases are active and bidirectionally source-consistent; restoration median render/semantic ratio is 0.031422 and render/all-layer ratio is 0.013610.
- Primary authorization: the untouched 41-base layer-localization run is now authorized with paired restoration. The primary protocol must be frozen before its C_shams or scores are produced; structural cases remain excluded from restoration only.
- Primary freeze: `primary_protocol.json` and the 41-base manifest were frozen before primary scoring. All 37 numeric C_shams pass automatic pixel validation and outcome-blind manual four-image inspection; no primary scores existed during review. The four structural bases remain prospectively excluded only from restoration.
- Stage 3B.3-R primary execution: complete on the required A5000 path. All 41 independent bases, 37 paired-restoration bases, and all expected coarse/cumulative/current-position rows passed mechanical validation.
- Frozen fine gate: primary-only W3, W4, and W5 qualified; all 12 prospective adjacent two-layer windows were then scored on the same 41 bases and passed aggregation.
- Final result: **PASS** with **GO — Module/path localization** as a recommendation for review only. The largest coarse effects occur at W4 (layers 24--29): median normalized BWS 0.6107 and paired BSRC 0.6531 at `E_d-1`. Fine effects retain at F28_29, with a secondary retained region at F32_33. No later experiment has started.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Median normalized BRI is 0.9703 at E_d-1 and 0.8022 at E_d, bidirectional 49/49 | `outputs/stage3b2/analysis/bidirectional_retrieval_statistics.json` | Supplies the required all-layer positive control and justifies layer localization | confirmed |
| Twelve exact-baseline-token cases retain late source control | `outputs/stage3b2/analysis/evidence_type_analysis.json` | Requires a dedicated natural-token robustness stratum | confirmed |
| Thirty-seven E_d cases use semantic teacher-forced leads | `outputs/stage3b2/annotations/annotation_audit.md` | Limits natural-trajectory timing claims | confirmed |
| A new attention-implementation name changed the causal-mask path in the first Stage 3B.2 smoke | `outputs/stage3b2/raw/smoke/three_base/` | Requires preserving the validated eager configuration | confirmed |
| Stage 3B.3 smoke passed 11/12 checks; restoration sham/target was 0.314949 | `outputs/stage3b3/smoke/layer_switch_validation.json` | Triggers the prospective stop before cohort execution | confirmed |
| Median absolute target restoration was 0.134651 and sham restoration 0.042408 | `outputs/stage3b3/smoke/restoration_sham_diagnostic.json` | Shows the failed ratio is not solely a zero-denominator artifact | confirmed |
| Primary W4 median normalized BWS/BSRC is 0.6107/0.6531 at `E_d-1` | `outputs/stage3b3_redesign/analysis/layer_statistics.json` | Localizes the strongest paired sufficiency/restoration effect to layers 24--29 | confirmed |
| F28_29 retains median normalized BWS/BSRC of 0.2617/0.3245 at `E_d-1` | `outputs/stage3b3_redesign/analysis/fine_layer_statistics.json` | Refines the strongest late-layer effect to layers 28--29 | confirmed |
| Current-position median normalized transfer rises from 0.0318 after layer 23 to 0.6694 after layer 29 | `outputs/stage3b3_redesign/analysis/layer_statistics.json` | Supports late emergence of transferable source identity at the tested current position | confirmed |
| Stage 3B.3-R passes 16/16 acceptance criteria | `outputs/stage3b3_redesign/summaries/stage3b3_redesign_acceptance.json` | Completes the approved redesign while preserving the stop boundary | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Initial Stage 3B.2 custom attention interface | No-switch scoring changed | New implementation name selected a different mask path | Override the existing eager operation locally | Do not rename the attention implementation |
| Stage 3B.1 all-visual cutoff | Strong damage without evidence identity | Intervention removed both target evidence and generic visual support | Use donor identity and reciprocal controls | Do not treat cutoff damage as layer-specific transfer |
| First Stage 3B.3 smoke submission (Slurm 106613) | Residual scorer received a dictionary instead of the selected boundary tensor | Supported by traceback; one boundary-index selection was missing | Select the donor state by candidate and layer before patching | Do not pass nested residual-state dictionaries to a single-boundary patch |
| Corrected Stage 3B.3 smoke (Slurm 106614) | Restoration sham/target ratio 0.314949 exceeded frozen 0.25 maximum | Direct observation confirmed; mechanistic cause unknown | Stop before the cohort and redesign the restoration control/estimand prospectively | Do not weaken or redefine the gate after inspecting smoke outcomes |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Module/path localization within late layers | Paired sufficiency and restoration converge at W4/F28_29, with secondary retention at F32_33 | Requires a separate prospective plan with module/path controls | recommended for review; not authorized |
| Exact-token replication expansion | The untouched exact-baseline robustness stratum is only N=7 (pooled secondary N=12) | Expand only under a separately approved replication plan | optional; not authorized |

## Next-Step Decision

- Current bottleneck: the original single-class restoration sham is semantically matched to the intended restoration, so the failed ratio does not separate semantic evidence identity from render variation.
- Relevant memory item used: D-020 preserves the 0.314949 failure and prohibits weakening that gate after outcome inspection.
- Chosen next action: execute only the explicitly approved `plan/stage3b3_redesign_plan.md` action. Freeze an independent 8-base, seed-20260901 method-validation split; construct paired O/O_sham/C/C_sham controls; apply the prospective semantic-restoration gates; and touch the remaining 41 bases only if the validation decision authorizes it.
- Prospective operationalization: use `base_problem_id` as the independent gate unit. A base is active when at least one window satisfies `|BSRC| >= 0.10 * |BRI_all-layer|`. Gate A requires at least 7/8 bases active and bidirectionally source-consistent at the base-level median (equivalently a one-sided exact binomial test against 0.5 with p < 0.05), with positive cohort-median BSRC. Gates C and D use the median, across active bases, of each base's median active-window render metric or ratio. No gate may be revised after validation scores are inspected.
- Why this action: paired semantic classes directly test the diagnosis in the approved redesign while reserving 41 untouched problems for scientific testing.
- Stop condition: after the frozen validation decision and any conditionally authorized 41-base analysis, produce the Stage 3B.3-R reports and stop before module/head/path/Q-R/ROI-specific or later experiments.

#### Post-validation decision

- Relevant evidence: `outputs/stage3b3_redesign/validation/validation_decision.json` records PASS under all frozen gates.
- Chosen next action: freeze and execute the authorized 41-base primary protocol with six selective windows, paired restoration for numeric-label bases, cumulative lower/suffix switching, and current-position residual patching; then apply the original prospective fine-localization rule.
- Primary restriction: no validation result may select a scientific layer/window. Fine selection uses only the frozen rule applied after the 41-base coarse result; validation bases enter only the later pooled exact-token robustness analysis.
- Immediate execution: submit eight balanced A5000 Slurm shards for the frozen 41-base coarse/selective, paired-restoration, cumulative, and residual arms. Resume only incomplete shards if external capacity or runtime interrupts them.
- Submission status: primary shards are Slurm jobs `106693`--`106700`. All eight are pending on node04 priority/capacity; no primary result bundle or score exists yet. The tested aggregation, primary-only fine gate, fine runner, and final reporting path are ready for the completed artifacts.
- Node03 diagnostic: user-requested Slurm job `106723` ran successfully on node03's RTX A6000, with exact layout, valid captures/audits, and finite scores, but failed both no-switch and all-layer bit-exact Stage 3B.2 reproduction. Node03 is rejected for primary scoring; A5000 remains required and shard 07 is restored to the pending queue.
- Node03 drift magnitude: on base 126 across eight matched control/coordinate comparisons, median absolute `D` drift was 0.1250 (maximum 0.2500), corresponding to median 1.12% and maximum 1.85% of the A5000 all-layer BRI. This is small for the strong all-layer effect but comparable to render-artifact terms and potentially material for weak/fine-window effects; it does not justify mixing hardware within the frozen protocol.

#### Final decision

- Relevant evidence: `outputs/stage3b3_redesign/analysis/decision_rule_evaluation.json` and `outputs/stage3b3_redesign/summaries/stage3b3_redesign_acceptance.json` record PASS under all frozen technical and scientific rules.
- Result-changing observation: W4 passes paired sufficiency/restoration at both `E_d-1` and `E_d`, and the effect survives prospective two-layer refinement. W5 also passes with a smaller retained F32_33 effect; the frozen distributed-coordinate rule does not pass.
- Decision: Stage 3B.3-R is complete. Return **GO — Module/path localization** for review, but do not execute it without a new approved plan.
- Stop boundary: no attention-versus-MLP, module/head/path, ROI-specific, Q/R-carrier, multi-evidence, or failure-analysis experiment has started.

### Stage 3B.3-R Completion Result

- Action taken: completed independent method validation, froze the authorized 41-base protocol, ran coarse/selective, paired-restoration, cumulative, current-position, and prospectively gated fine scoring on A5000s, and applied the frozen decision rules.
- Result: validation PASS; primary and fine aggregation PASS; final acceptance PASS (16/16); recommendation **GO — Module/path localization**.
- Primary evidence: N=41 for sufficiency/cumulative/current-position analyses and N=37 for paired semantic restoration. W4 is the strongest coarse window, F28_29 the strongest fine window, and F32_33 a secondary retained fine region.
- Controls: all mechanical controls pass; W4 bidirectional restoration consistency is 37/37 at both coordinates; median restoration render/semantic ratios are 0.0129 (`E_d-1`) and 0.0231 (`E_d`).
- Next implication: review the result before authorizing any new localization plan. Stage 3B.3-R itself is stopped and complete.

### Original Stage 3B.3 Step Result

- Action taken: froze and implemented Stage 3B.3, then ran the mandatory three-base smoke on the validated A5000 eager path.
- Result: 11/12 smoke checks passed; restoration sham evidence-specificity failed (0.314949 > 0.25). Overall Stage 3B.3 acceptance is FAIL and recommendation is REDESIGN.
- Evidence saved: `outputs/stage3b3/smoke/` and `outputs/stage3b3/summaries/`.
- Failure or issue: the first submission had a mechanical residual-state indexing bug and saved no per-base result; the corrected run passed all mechanical checks. The remaining sham-control failure is a valid protocol gate failure, not a runtime error.
- Lesson learned: layer-window restoration can expose sham edit sensitivity even when the all-layer sham effect is small; its cause is unresolved and must not be assumed.
- Next implication: review and prospectively redesign the restoration sham/control estimand before authorizing any cohort rerun.
