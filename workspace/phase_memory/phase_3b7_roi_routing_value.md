# Phase 3B.7: ROI-specific visual path and routing-versus-value decomposition

## Current Objective

Determine whether the two robust Stage 3B.6 W4 visual-source pathways draw evidence identity from the exact Stage 3A edited visual-token ROI or a distributed visual field, and only for ROI-qualified targets distinguish routing-side K effects from transmitted V-content effects.

## Active Constraints

- Preserve the exact 37 paired numeric primary bases and disjoint eight validation bases from Stage 3B.6; `base_problem_id` is the statistical unit.
- Freeze `E_d/W4/Top_4` (heads 11, 6, 15, 12; layer 29) and `E_d-1/W4/Top_2` (heads 16, 0; layer 28) as the only primary targets.
- Keep `E_d-1/W5/head_10` exploratory and score it only after primary results freeze, if at all. Do not use `E_d/W5` as a primary target.
- Define `V_target` from the exact Stage 3A edited-pixel support mapped through the reproduced merged visual grid, never from attention. Freeze a one-cell Chebyshev ring and a disjoint, cardinality-matched low-ink irrelevant region before causal scoring.
- Manually inspect all validation and primary ROI-token overlays before scoring. A pixel-local edit localizes visual-token source positions, not the causal vision-encoder feature itself.
- Phase A primary arms are all-V, target ROI, visual complement, and matched irrelevant; target+one-cell-ring is secondary. All swaps retain recipient Q/current state, splice only frozen logical query-head outputs before `W_O`, and naturally recompute downstream layers.
- Phase A robustness reuses the paired-control standard: Holm-adjusted one-sided p < 0.05, bootstrap median CI low > 0, bidirectional fraction >= 0.70, median sham/semantic ratio < 0.25, exact self controls, and finite mechanically isolated scores.
- The Phase A to B gate additionally requires target-minus-irrelevant median bootstrap CI low > 0, target greater than irrelevant on >=70% of bases, and median target or target+ring PRR >= 0.50.
- Phase B runs only after that gate and uses recipient-native Q, K-only, V-only, and K+V at the frozen ROI/ring positions inside the query-head-selective hybrid computation. K+V must reproduce the Phase A ROI arm within 1e-6 in every preference score.
- Mechanism classes use unclipped ratios: Value-Dominant requires robust V, median KVR_V >= 0.75, and KVR_K < 0.50; Routing-Dominant is symmetric; Routing+Value requires robust K and V, both KVR >= 0.25, and a positive bootstrap lower bound for joint-minus-max-single.
- Raw attention is secondary and inspected only after primary ROI/KV results freeze.
- Use only active Slurm job 106936 through `tmux` session 8 on node04 A5000 x2; submit no new job and do not terminate the user's allocation.
- Stop before vision-encoder feature localization, query/key features, value subspaces, MLP features, Q/R lifecycle, multi-evidence refresh, failure analysis, or any later stage.

## Current State

- Done: Stage 3B.6 passed 17/17 criteria and independently validated 20/20 artifact checks.
- Done: the user explicitly authorized `plan/stage3b7_plan.md` and directed GPU work to active `tmux` session 8.
- Done: session 8 is verified as Slurm job 106936 on node04 with two A5000 GPUs.
- Done: all 45 edit-derived target/complement/ring/irrelevant ROI maps passed exact layout checks and manual overlay review before any Stage 3B.7 score; selection used no attention.
- Done: K-only, V-only, and K+V logical-query-head mechanics pass 14 focused CPU tests, including component isolation and exact self restoration.
- Done: the disjoint eight-base Phase-A validation run completed in `tmux` 8. All mechanical, legacy-equivalence, self, finite-score, and deterministic-repeat checks passed.
- Failed gate: `E_d-1/W4/Top_2` median all-V sham/semantic was 0.269893, above the frozen `<0.25` maximum. `E_d/W4/Top_4` passed at 0.114337.
- Stopped: no Stage 3B.7 primary base was scored; Phase B and all secondary/later analyses were not run.
- Blocked: any redesign or altered target/control threshold requires a new reviewed plan and user approval.
- Most recent useful observation: the failed target has modest median absolute sham shift (0.059710) but low median semantic restoration (0.213821), including near-zero effects on bases 83 and 101. This is a supported sham-relative validation limitation, not an implementation failure.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Two robust visual-dominant W4 targets | `outputs/stage3b6/analysis/source_path_statistics.json` | Freezes the only primary target cells/head sets | confirmed |
| Exact 37/8 primary-validation split | `outputs/stage3b6/config/discovery_primary_split.json` | Prevents outcome-dependent cohort changes | confirmed |
| Query-head-selective GQA hybrid intervention passed mechanics | `outputs/stage3b6/validation/head_intervention_validation.json` | Supplies the intervention surface Stage 3B.7 must preserve | confirmed |
| Stage 3A edits differ only inside frozen target ROIs | `outputs/stage3a/counterfactuals/*/edit_metadata.json`; `outputs/stage3b3_redesign/counterfactual_shams/*/edit_metadata.json` | Supplies attention-independent ROI masks and paired semantic controls | confirmed |
| W5/head-10 V source fails sham control | `outputs/stage3b6/analysis/source_path_statistics.json` | Requires exploratory-only handling | confirmed |
| Forty-five attention-independent ROI maps manually pass | `outputs/stage3b7/roi_audit/roi_token_mapping.jsonl`; `outputs/stage3b7/roi_audit/roi_mapping_report.md` | Validates the spatial intervention definitions before scoring | confirmed |
| Stage 3B.7 Phase-A validation gate fails one target | `outputs/stage3b7/validation/roi_path_validation.json`; `outputs/stage3b7/validation/validation_failure_diagnostic.json` | Prohibits the 37-base primary run under the frozen protocol | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Raw attention as acquisition/localization evidence | Attention was largely mention-centered and did not positively track Stage 3B.6 restoration | supported | Define ROIs from edits and use attention only after causal results freeze | Do not select ROIs or mechanisms by attention |
| Shared KV-group patch as logical-head attribution | GQA shares one KV group across four query heads | architectural | Recompute donor K/V but splice only selected logical query-head outputs | Do not globally alter a KV group's non-target query heads |
| High W5 visual PRR without adequate sham separation | V PRR was 0.989 but sham/semantic was 0.436 | supported | High ratios cannot override paired artifact controls | Do not promote W5/head-10 into the primary family |
| Stage 3B.7 disjoint Phase-A validation | `E_d-1/W4/Top_2` median sham/semantic was 0.269893 versus frozen `<0.25`; every mechanical check passed | supported | A previously robust primary-cohort V path need not satisfy sham-relative transfer on a disjoint method-validation cohort | Do not relax the ratio, repeat deterministic inference, or launch the primary cohort without a new approved protocol |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| ROI-local visual source | Edits are localized numeric labels and Stage 3B.6 V dominates | Target ROI vs complement and matched irrelevant swaps | open |
| Local-plus-context source | Vision encoding may spread evidence to neighboring merged tokens | Fixed one-cell target ring | open |
| Distributed visual representation | Vision self-attention may diffuse localized pixels across visual tokens | Complement restoration and low target/all-V recovery | open |
| Value-mediated transport | Raw attention was not a positive proxy for causal restoration | V-only vs K-only vs K+V within qualified ROI | gated |
| Routing-mediated transport | Donor semantic K can change source selection even with recipient V | K-only vs V-only vs K+V within qualified ROI | gated |

## Next-Step Decision

- Current bottleneck: one of the two prospectively frozen targets does not meet the disjoint sham-relative semantic validation standard.
- Relevant memory item used: paired artifact controls take precedence over high recovery ratios; Stage 3B.7 froze `<0.25` before any score was computed.
- Chosen next action: stop Stage 3B.7 at validation and return the failure for review.
- Why this action: every implementation check passes, but the plan explicitly prohibits primary scoring until all validation requirements pass. Retrospective target removal or threshold adjustment would change the confirmatory protocol after outcomes were observed.
- What not to repeat: do not rerun deterministic validation, silently remove `E_d-1/W4/Top_2`, relax the sham threshold, or use the untouched primary cohort to tune a redesign.
- Stop condition: satisfied at the failed pre-primary validation gate.

### Step Result

- Action taken: froze/audited all ROI maps, implemented/tested ROI and K/V mechanics, and ran the authorized disjoint Phase-A validation only.
- Result: FAIL before primary; 7/8 validation requirements pass and the all-V sham-small requirement fails for one target.
- Evidence saved: `outputs/stage3b7/validation/roi_path_validation.json`, `outputs/stage3b7/validation/validation_failure_diagnostic.json`, `outputs/stage3b7/summaries/stage3b7_summary.md`, and `outputs/stage3b7/summaries/stage3b7_acceptance.json`.
- Failure or issue: `E_d-1/W4/Top_2` median sham/semantic 0.269893 exceeds `<0.25`.
- Lesson learned: primary-cohort V dominance from Stage 3B.6 did not guarantee clean transfer on the disjoint validation split, even with exact intervention mechanics.
- Next implication: review a genuinely prospective redesign; no current Stage 3B.7 localization or K/V scientific result exists.
