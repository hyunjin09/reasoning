# Phase 2A: Paired Descriptive Analysis and Evidence-ROI Discovery

## Current Objective

Using only immutable Stage 1 artifacts, determine whether VI/VD paired dynamics and a clean multi-evidence ROI subset provide a defensible, preregisterable target for a later causal Stage 2B experiment.

## Active Constraints

- Run no model inference, generation, CUDA validation, image counterfactual, knockout, activation/KV intervention, attention manipulation, or method-development experiment.
- Do not modify Stage 0 or Stage 1 artifacts; write new results only under `outputs/stage2a` and compact state under `workspace`.
- Audit at least 10 randomly selected both-correct pairs before running the full paired analysis.
- Use within-base-problem paired statistics on the 36 both-correct pairs; do not treat variants as independent samples.
- Normalize unequal reasoning lengths by fixed progress bins and separately report noisy coarse semantic-label alignment.
- Treat raw attention and ROI focus as descriptive, never as causal visual usage or evidence acquisition.
- Target 20–30 clean A/B evidence examples, permit a documented conditional result for 10–19, and issue NO-GO below 10 or when ROI/stage identity is unreliable.
- Stop after Stage 2A reports; do not execute Stage 2B.
- The project-local `research-control` skill is absent, and external installed skill paths are outside `ACCESS_POLICY.md`; follow the repository research-action rules directly.

## Current State

- Done: Stage 1 passed all 13 acceptance criteria with 200 validated discovery bundles, 82 completed-correct trajectories, and 100 VI/VD base-problem pairs.
- Done: Stage 1 retained token-level visual focus over individual visual tokens plus exact spatial mapping metadata, sufficient for aggregate descriptive ROI analysis.
- Done: Ten seeded-random both-correct VI/VD pairs were manually audited.
- Done: All 36 both-correct pairs were classified as 13 clear information shifts, 22 no-effective-shift controls, and 1 mixed redistribution; within-problem paired analysis is complete.
- Done: Thirty trajectories were screened without attention, 20 A/B evidence examples were annotated, all 20 ROI maps passed manual inspection, and token/span curves plus candidate future windows were generated.
- Done: All 12 Stage 2A acceptance criteria pass (criterion 7 with a documented confidence caveat); deterministic validation passes 32 checks.
- Recommendation: CONDITIONAL GO for a later five-example controlled Stage 2B pilot (`699, 739, 2799, 3044, 3764`) only after review and explicit authorization.
- Blocked: None.
- Most recent useful observation: Clear VI/VD shifts show no robust global visual-mass/density change, while 10/20 frozen ROI examples show descriptive A→B alignment and only 5 combine that pattern with high-confidence annotation.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| There are 36 both-correct VI/VD pairs. | `outputs/stage1/discovery/paired_variants/pairing_manifest.jsonl` | Defines the primary within-problem paired cohort. | confirmed |
| VI and VD share underlying question text but use distinct image versions and example IDs. | `outputs/stage1/summaries/stage1_artifact_inventory.md` | Requires manual audit of what information actually moved across modalities. | confirmed |
| Token-level `visual_focus[T,V]` and span-level focus distributions retain individual visual-token positions only after layer/head aggregation. | `outputs/stage1/summaries/stage1_artifact_inventory.md` | Supports descriptive ROI curves but not layer/head-specific or causal inference. | confirmed |
| Candidate attention peaks are recurrent but segmentation-scale-sensitive and weakly aligned with semantic labels. | `outputs/stage1/summaries/stage1_statistics.json`, `peak_segmentation_robustness.json` | Intervention windows must be evidence/semantics anchored rather than peak-selected. | confirmed |
| Many long correct trajectories are meandering or internally weak. | `outputs/stage1/discovery/manual_review/segmentation_review.json` | Evidence subset screening must include reasoning interpretability. | confirmed |
| VI/VD is not a uniform manipulation: only 13/36 both-correct pairs are clear information shifts. | `outputs/stage2a/manual_pair_audit.md`, `paired_analysis/both_correct_pair_manifest.jsonl` | Primary paired inference must use the verified clear-shift stratum. | confirmed |
| Clear-shift pairs have null/heterogeneous global visual allocation effects; focus-turnover magnitude is influence-sensitive. | `outputs/stage2a/paired_analysis/paired_statistics.json` | A broad VI/VD visual-reliance claim is not supported. | confirmed |
| Ten of 20 frozen evidence examples show descriptive A→B density alignment; five are high-confidence candidates. | `outputs/stage2a/evidence_subset/evidence_subset_statistics.json` | Supports only a narrow future controlled pilot. | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Stage 1 pooled semantic/peak alignment | Weak associations and span fragmentation. | supported by manual review and fixed-window diagnostic | Use manual evidence demand and paired normalized-time summaries. | Do not define evidence windows from automatic peaks alone. |
| Stage 1 unpaired VI/VD screen | Nearly identical aggregate visual mass/peak count; turnover was outlier-sensitive. | supported by Stage 1 statistics | Preserve pairing and report effect sizes/CIs, including null results. | Do not pool variants as independent observations or chase p-values. |
| Treat all VI/VD pairs as one manipulation | 22/36 are effectively unchanged and one redistributes information in both directions. | supported by full manual input classification | Verify information movement per pair and retain unchanged pairs as controls. | Do not interpret dataset variant labels as an exchangeable treatment. |
| Require every clean ROI example to show A→B focus | Only 10/20 frozen examples show that pattern; persistent and unclear patterns remain common. | supported by post-selection ROI curves | Preserve negative patterns and constrain later intervention targets by annotation confidence. | Do not attention-select a favorable subset after curves are visible. |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| VI/VD is an interpretable modality-information manipulation. | Only a verified 13-pair clear-shift subset is interpretable; 22 pairs are controls and 1 is mixed. | Completed manual audit and full classification. | resolved: subset only |
| Both-correct pairs differ in late/recurrent visual allocation despite similar global means. | Paired temporal effects are heterogeneous and CIs generally cross zero. | Completed 20-bin and early/middle/late comparison. | resolved: no robust general effect |
| Existing artifacts contain at least 20 clean multi-evidence ROI examples. | Twenty were accepted, but 9 carry medium-confidence caveats. | Completed attention-blind screen and 20/20 mapping review. | resolved: minimum met with caveat |

## Next-Step Decision

- Current bottleneck: Stage 2A is complete; any causal test requires explicit Stage 2B authorization and a fresh intervention-faithfulness plan.
- Relevant memory item used: Five high-confidence examples combine manually separable evidence with descriptive A→B alignment, while the paired global result is mostly null and VI/VD is nonuniform.
- Chosen next action: Stop and request review. If later authorized, preregister a five-example evidence-B ROI pilot with no-intervention, same-size irrelevant ROI, evidence-identity, and timing controls.
- Why this action: It tests the narrowest evidence-specific hypothesis supported by the data without converting attention alignment into a causal claim.
- What not to repeat: Do not expand to all 20 examples, use automatic peaks as targets, or execute a broad intervention sweep before controlled pilot evidence.
- Stop condition: Already reached. No Stage 2B action is authorized in this phase.

### Step Result

- Action taken: Inspected questions, answers, metadata, and both source images for 10 seeded-random both-correct pairs.
- Result: Conditional pass: 6 clear text-to-image evidence shifts, 1 mixed redistribution, and 3 no-change pairs.
- Evidence saved: `outputs/stage2a/manual_pair_audit.md`.
- Failure or issue: The VI/VD label is not a uniform manipulation; several pairs are byte-identical in both question and image.
- Lesson learned: Pair eligibility must be based on verified information movement, not the dataset variant label alone.
- Next implication: Freeze and analyze a clear-shift stratum; treat unchanged pairs as controls and the mixed pair separately.

### Final Step Result

- Action taken: Completed full paired analysis, attention-blind evidence screening, manual ROI/stage annotation, ROI curves, candidate future windows, reports, and independent validation.
- Result: Stage 2A PASS; Stage 2B CONDITIONAL GO for five high-confidence examples only.
- Evidence saved: `outputs/stage2a/paired_analysis/`, `outputs/stage2a/evidence_subset/`, `outputs/stage2a/summaries/`.
- Failure or issue: VI/VD is not a uniform manipulation; global paired attention effects are mostly null; only half of ROI examples show the expected descriptive alignment.
- Lesson learned: The defensible causal target is evidence identity at manually anchored spans, not global attention allocation or attention-defined peaks.
- Next implication: Stop before Stage 2B and obtain review/authorization for any intervention.
