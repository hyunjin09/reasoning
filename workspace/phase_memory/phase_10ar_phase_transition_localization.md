# Phase 10A-R: causal phase-transition localization

## Current Objective
COMPLETE / STOP. Approved bounded localization study:24 successful independent-image
trajectories, prospective A0–A4 anchors, necessity/sufficiency assays, one decision.

## Active Constraints
- Same native4B Thinking, BF16, TF32 off, greedy, DeepStack,512 total-token budget.
- Existing32 images/64 FULL traces only;24 primary,8 frozen reserve; one query/image.
- Correct FULL is now an explicit eligibility criterion, unlike Stage10A.
- No Stage10AR intervention output may inform cohort/anchor annotation.
- No full text-edit panel rerun; up to8 authorized Slurm GPUs, nodes02/03/06/07.
- Primary target<3 GPUh; projected>5 before optional work requires stop.

## Current State
- Done: plan, policies, prior phase/D-108; existing model, corpus and environment found.
- Done: L0 sealed32 native annotations,24 primary/8 reserve and12 prospective optional A3 edits.
- Done:236 logical assays; three A0 technical cases pass, eight prior validations reused.
- Done: L1 complete166 new/64 reused/6 aliases =236 logical assays; all4 workers COMPLETED0:0 and GPUs released.
- Done: final review sealed;50 logical runs have empty finals at512 tokens, retained as unscorable/incorrect.
- Done: L2 OutcomeA; P1/P2/P3/P4=+29.17/+95.83/+41.67/+45.83pp; all adjusted intervals above0 and robustness gates pass.
- Done: optional12-image A3 text-edit assay,24 new/12 exact reused; reserve closed.
- Done: CF follows edited count9/12 versus3/12 original and1/12 sham; paired effects positive.
- Done:11 artifacts/four figures, six tests, separate arithmetic/provenance audit and accounting.
- Complete:190 new continuations,0.552778 GPUh; all GPUs released, no follow-on launched.
- Blocked: none.
- Most recent useful observation: every original image has a correct FULL query.

## Evidence That Matters
| Evidence | Source | Why it matters | Status |
|---|---|---|---|
| Stage10A H1=0, H2 positive, H3 positive | D-108 / Stage10A report | Prospective earlier localization now explicitly authorized | confirmed |
| Native FULL58/64; all32 images have a correct query | Stage9A.5 baseline | No baseline generation or dataset expansion needed | confirmed |
| Generated-query mask preserves prefill | stage9a3/access.py | A0 retains prefill-derived first-token prediction and latent state | confirmed |

## Failed Attempts and Lessons
Optional workers125017/125018 failed a decode/display equality assertion after12
combined complete runs. Supported cause: optional manifest used unsnapped annotation
display text rather than authoritative L0 tokenized text; two queries differ only
by trailing newlines. Frozen IDs/conditions unchanged; save focused roundtrip
diagnostic and versioned resume for12 unfinished rows, preserving failures/results.
Do not confuse missing finals with local read errors or alter cap/anchors afterward.

## Open Candidates
None authorized. The single recurrent-demand recommendation requires a new task.

## Next-Step Decision
- Evidence: primary OutcomeA, all4 adjusted-positive contrasts and robust attribute
  directions; secondary A3 signed CF−original1.00 [0.333,1.583], CF−sham1.333 [0.833,1.750].
- Decision: authorized action complete; STOP. Recommend promoting the bounded
  functional phase framework and next testing controlled recurrent demand, without launching it.
- Limits: successful controlled cohort; A0 prefill remains,17/24 already image-off
  correct; all fresh A0 finals are missing at512; population curves nonmonotonic;
  standard mask only, prior null-sink limitation retained; no universal/text-dominance claim.
- Evidence paths: outputs/stage10ar/v1/stage10ar_summary.md, stage10ar_primary_inference.json,
  stage10ar_a3_text_edit.json, stage10ar_resource_accounting.json, audit/final_audit.json.
