# Phase 3A: counterfactual visual-content sensitivity

## Current Objective

Test whether changing one localized visual fact causally shifts Qwen3-VL-4B-Thinking's evidence-specific predictions under an identical reasoning prefix ending strictly before E0, using base problem as the independent unit.

## Active Constraints

- Target 40 and require at least 30 manually validated unique base problems; do not lower edit-quality standards to meet scale.
- Select and construct edits without inspecting Stage 2C attention timing or Stage 3A model outcomes.
- Use one primary evidence item per base problem, exact same pre-E0 token prefix across conditions, prospective original/counterfactual continuations, and a sham control for every primary item.
- Keep question text, image dimensions/crop, prompt format, preprocessing, and unrelated task-relevant content fixed.
- Use the locked Qwen official-style Thinking protocol for any new generation and run all GPU work through the project scheduler/Slurm.
- Stop after Stage 3A reports. Do not start carrier patching, V/Q/R tracing, cutoff/reveal, or Stage 3B.

## Current State

- Done: Stage 2C technically passed 15/15 and identified 38 edit candidates across 26 examples but only 18 unique base problems.
- Done: Attention-blind screening froze 57 unique candidate bases: 18 Stage 2C candidates, 8 additional Stage 1B candidates, and 31 prospective unseen Vision Dominant examples.
- Done: 59 C0/C1/C2 edit triplets were constructed and manually inspected. Thirty-eight pass visual review: 14 already completed-correct bases, 19 first-round prospective bases, and 5 second-round prospective bases. Twenty-one edits were rejected rather than repaired beyond one logged pre-outcome construction retry.
- Done: A second outcome-blind screen was frozen because the first accepted-edit pool could contain at most 33 eligible bases, below the 40-base target. Five of eight backup edits passed and only those five were submitted for generation.
- Done: The 36 prospective locked-protocol generations completed: 28 correct and 8 wrong, with no truncations or invalid cases. Sixteen of the 24 manually valid prospective edits are completed-correct.
- Done: The provisional pool now contains exactly 30 potential unique bases (14 existing plus 16 prospective), pending a score-blind strict pre-E0 audit.
- Done: The base-119 scoring smoke validated the implementation and exact prefix identity on one example only; it is not treated as a scientific result.
- Done: All 30 provisional bases passed a score-blind strict pre-E0 audit; exact `y_<E0` token prefixes and hashes are frozen in `outputs/stage3a/cohort/strict_pre_e0_audit.jsonl`.
- Done: All 20 remaining Stage 1B completed-correct bases were screened without attention; none supported a clean localized, prompt-independent counterfactual.
- Done: A third prospective screen froze 30 unseen Vision Dominant problems before outcomes. Twenty-three C0/C1/C2 triplets passed automatic and manual edit review after one logged pre-outcome construction repair; seven ambiguous edits were rejected.
- Done: Locked-protocol round-3 generation completed for all 23 edit-valid problems: 19 correct, 4 wrong, 0 truncated, and 0 invalid. All raw outcomes are preserved.
- Done: All 19 completed-correct additions passed strict manual pre-E0 review. The final primary cohort is frozen at 49 unique base problems (45 local numeric edits, 4 structural edits), with one evidence item per base.
- Done: Eight frozen-manifest A5000 scoring shards completed for all 49 bases. The merged artifacts contain 49 fact-preference rows, 313 temporal rows, and 147 matched-seed rollout rows; every frozen prefix hash matches across C0/C1/C2.
- Done: Primary CE and sham-controlled CE are positive in 49/49 bases. Mean controlled CE is 3.1864 nats/candidate-token (95% bootstrap CI 2.8688--3.4988), while mean sham shift is 0.0392 (0.0094--0.0738).
- Done: All 46 bases with an available E0-8 checkpoint satisfy the frozen early-sensitivity rule. Three bases have E0 before token 8 and are correctly marked not evaluable for that rule.
- Done: Twenty-two automatically ambiguous rollouts and two targeted false positives were manually audited. Counterfactual rollouts state the exact changed fact in 46/49 cases plus one directionally changed but inexact reading; original/sham predominantly retain the original fact.
- Done: Stage 3A technically passes all 15 acceptance checks and issues **GO** as a recommendation for later review. No Stage 3B or carrier experiment was started.
- Most recent useful observation: Visual-content changes have a large evidence-specific effect before explicit E0 mention, whereas the matched redraw sham is small. This establishes pre-verbal causal content sensitivity but not its V/Q/R carrier.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Stage 2C timing is predominantly mention-centered | `outputs/stage2c/analysis/event_aligned_statistics.json` | Cohort selection must not use attention peaks | confirmed |
| Only one clean counterfactual-ready item is also T1 | `outputs/stage2c/candidates/counterfactual_ready_candidates.jsonl` | Stage 3A must test content, not select on a rare attention pattern | confirmed |
| Eight of ten Stage 2B target windows were post-E1 | `outputs/stage2c/stage2ab_reaudit/stage2b_window_timing.json` | Initial acquisition remains untested | confirmed |
| Existing Stage 1B eligible set spans 46 base problems | `outputs/stage1/discovery/cohort_manifest.jsonl` | Existing artifacts can contribute at most 46 independent primary units | confirmed |
| Candidate screen was frozen without attention or new outcomes | `outputs/stage3a/cohort/candidate_screening.jsonl` | Prevents attention- and outcome-based cohort selection | confirmed |
| 38 image edits pass manual review, 21 fail | `outputs/stage3a/counterfactuals/*/validation.md` and `outputs/stage3a/cohort/*manual_edit_exclusions.jsonl` | Establishes the current edit-quality ceiling before new generation outcomes | confirmed |
| Expansion inference completed with 28/36 correct | `outputs/stage3a/cohort_expansion/` and Slurm logs for jobs 106064--106067 and 106084 | Sixteen edit-valid prospective bases can enter strict pre-E0 audit | confirmed |
| One-example scoring smoke passed exact-prefix and behavioral checks | `outputs/stage3a/scoring/shards/smoke_119/` | Validates implementation only; it must not influence cohort selection or count as a Stage 3A result | confirmed |
| Provisional strict audit passed 30/30 | `outputs/stage3a/cohort/strict_pre_e0_audit.jsonl` | Every current prefix is exact `y_<E0` and evidence-neutral | confirmed |
| Round-3 candidate/edit gates were frozen before outcomes | `outputs/stage3a/cohort/round3_candidate_screening.jsonl` and `round3_valid_generation_manifest.jsonl` | Provides up to 23 clean unseen additions without attention- or outcome-based selection | confirmed |
| Round-3 generation yielded 19/23 eligible additions | `outputs/stage3a/cohort_expansion/round3/collection_summary.json` | Raises the final cohort to 49 unique completed-correct, edit-valid, strict-prefix bases | confirmed |
| Final cohort membership and hashes are frozen | `outputs/stage3a/cohort/primary_manifest.jsonl` | Full scoring cannot affect inclusion, wording, or prefix boundaries | confirmed |
| Primary content effect is positive for 49/49 bases | `outputs/stage3a/analysis/primary_statistics.json` | Target edits shift fact preference much more than matched shams | confirmed |
| Strict early sensitivity passes for 46/46 evaluable bases | `outputs/stage3a/analysis/temporal_sensitivity_statistics.json` | Visual content affects evidence preference before explicit E0 mention | confirmed with fixed-checkpoint caveat |
| Short rollouts track edited content | `outputs/stage3a/analysis/rollout_manual_audit.md` | Qualitatively validates the probability result under one matched seed | confirmed; not a frequency estimate |
| Attention moderator overlap is only nine T2 cases | `outputs/stage3a/analysis/attention_moderator_analysis.json` | Attention timing cannot explain or gate the primary result | underpowered secondary analysis |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Stage 2B ROI-edge blocking | 0/5 strong crossovers; 1/5 partial-specificity | Most target windows were later shown to be post-E1 | Change visual content under a strict pre-E0 prefix before tracing carriers | Do not repeat attention-guided edge masking as the main test |
| Curve and overlapping-label edits | Visible line/grid damage or duplicate source labels in sham/target renderings | Target glyphs overlap task-relevant geometry in these images | Reject ambiguous edits; do not lower the visual-validity threshold | Do not use the rejected v1/v2 renderings for inference |
| Node03 A6000 equivalence attempt | CUDA initialization failed before scoring; `nvidia-smi` could not obtain the assigned device handle | Node03 exposed zero usable CUDA devices despite a nominal Slurm GPU allocation | Keep the validated A5000 scoring run; preserve the machine failure separately from science | Do not use node03 for this phase without administrator repair |
| First aggregate-render pass | Temporal figure expected CI fields at the wrong schema level | Plot-only consumer bug; raw scores and computed statistics were intact | Test the nested bootstrap schema, fix only the renderer, and rerun from immutable shards | Do not alter scores or cohort to repair a presentation failure |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Stage 3B carrier tracing | Stage 3A establishes robust pre-E0 content sensitivity but not the carrier | Review jointly with Stages 2A--2C and design only after explicit approval | recommended GO; not started |

## Next-Step Decision

- Current bottleneck: Stage 3A is complete; the project now awaits joint scientific review before any carrier-tracing plan is authorized.
- Relevant memory item used: The Stage 2C handoff required content intervention rather than attention timing as the primary causal handle. The frozen Stage 3A contract required exact `y_<E0` prefixes and base-problem bootstrap units.
- Chosen next action: Stop and return the complete Stage 3A result for review.
- Why this action: The authorized research action is complete and the user explicitly prohibited starting Stage 3B in this task.
- What not to repeat: Do not infer V/Q/R carrier identity, visual memory, or attention-based acquisition from the Stage 3A content effect.
- Stop condition: Satisfied. Stage 3B remains unstarted.

### Step Result

- Action taken: Scored the frozen 49-base manifest under C0/C1/C2, computed fixed temporal checkpoints and matched rollouts, audited rollout text, ran the post-freeze attention moderator, and wrote the final reports.
- Result: Technical PASS and scientific **GO** recommendation. Controlled CE is positive in 49/49 bases; 46/46 early-evaluable bases meet the fixed pre-E0 rule.
- Evidence saved: `outputs/stage3a/scoring/`, `outputs/stage3a/analysis/`, and `outputs/stage3a/summaries/`.
- Failure or issue: No clean C3 was available; earlier checkpoints are matched forced fact probes and may be less locally grammatical. The attention moderator has only nine exact Stage 2C matches.
- Lesson learned: Counterfactual content edits reveal robust pre-verbal evidence sensitivity even where attention timing was mention-centered; attention timing is not a prerequisite for the causal content effect.
- Next implication: A carrier-tracing study is scientifically motivated, but its design and authorization belong to a separate reviewed stage.
