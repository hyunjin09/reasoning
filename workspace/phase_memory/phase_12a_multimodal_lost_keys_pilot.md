# Phase12A: multimodal Lost-Keys pilot

## Current Objective
Execute the approved61-family same-checkpoint E/D/C pilot to test evidence recoverability, Answer-Only failure, and selective reasoning rescue. Development evidence only.

## Active Constraints
- Reuse all61 frozen Stage11A families and157 E* facts unchanged.
- Qwen3-VL-2B-Instruct only; official Instruct sampling .7/.8/top20/repetition1/presence1.5; same runtime/seed policy.
- E128/D16/C8192 caps;12 deterministic format-only technical cases; one bounded wording repair if needed before full-cohort correctness.
- Target<2.5/hard4 allocated GPUh, Slurm/project scheduler, standing up-to8 GPUs on nodes02/03/06/07.
- No native Thinking, oracle, new benchmark, automatic recommendation execution.

## Current State
- Done: prospective native-output clarification preserved; initial36 technical calls and the single permitted24-call D/C wording-repair round complete.
- Done: final gate E PASS, D FAIL, C FAIL; all60 raw outputs preserved and60 output-only reviews sealed.
- Done: required artifacts and three explicitly NOT_ESTIMATED scientific figure panels; all61 families/157 frozen facts retained.
- In progress: none; authorized stage closes at the prescribed technical stop.
- Scientific outcome: unresolved. Correctness not opened; P1–P4/GO/NO-GO not evaluable; remaining49 families not generated.
- Resources:0.500278 allocated GPUh across127229(TIMEOUT after all36 outputs) and127259(COMPLETED); all released.

## Evidence That Matters
| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
|61 families,157 frozen visual facts|outputs/stage12a/v1/stage12a_frozen_e_star_manifest.json|Reuse unchanged inputs|confirmed|
|37 open-ended questions|outputs/stage12a/v1/audit/source_preflight.json|Letter-only output contract undefined for majority|confirmed|
|Official Instruct5/12 caps/loops despite presence1.5|D125|Require prompt-format gate; no post-hoc cap expansion|confirmed|
|Historical probes were budget sensitive|phase_11a_visual_evidence_bottleneck_census.md|Do not equate failed probes with absent encoding|confirmed|

## Failed Attempts and Lessons
Initial36 calls preserved; technical D/C failures recorded below. All36 finished before Slurm127229 timeout during shutdown. Long startup exceeded the original margin; cause of startup delay unknown. Do not repeat15-minute wall allowance; repaired wave has30 minutes, unchanged runtime. Keep project TMPDIR short.

## Open Candidates
No further execution is authorized by this result. Exactly one recommendation: hold expansion/interpretation until a separately approved technical repair validates Answer-Only and reasoning completion on the frozen cases. No new repair, native Thinking, oracle or cohort launched.

## Next-Step Decision — 2026-09-29T06:54:37.096473+00:00
- Current bottleneck: valid D/C output contract for37 original open-ended problems.
- Relevant memory used: prior format/completion failures cannot be interpreted as mechanism evidence.
- Chosen action: freeze unchanged evidence and source hashes; request native-answer-format clarification before generation.
- Why: inventing choices or dropping37 families would silently change the study.
- What not to repeat: treating undefined output formats as model failures or selecting examples by accuracy.
- Stop condition: wait for required clarification; no dependent GPU work while pending.

### Step Result
Source preflight and evidence manifest sealed. No GPUs allocated, no new outputs or correctness opened.

## Next-Step Decision — 2026-09-29T07:07:33.872924+00:00
User explicitly approved output-contract clarification, preserving61 families,157 facts,caps,12 technical IDs and numerical gates. Original plan/spec and clarification versioned in audit/spec_versions; execution spec, all183 prospective tasks,36 technical calls and runtime/scoring hashes sealed before any generation. Eight output-contract/gate checks pass. Run exactly36 technical calls on one finite15-minute authorized A6000 allocation. Review format/completion only; apply plan's one bounded wording repair only if needed. Do not open correctness or launch remainder before technical pass.

## Next-Step Decision — 2026-09-29T07:27:34.623997+00:00
- Initial36 calls all committed and hash-verified; Slurm127229 timed out during shutdown after long startup,0.251944GPUh. No retry needed.
- Output-only gate: E11/12 schema passes; D1/12 strict answers and9 intermediate-reasoning cap hits fails; C7/12 committed finals,4 caps,7 semantic repetitive cycles fails. Correctness remains unopened.
- Execute exactly one plan-section9 bounded wording repair on D/C,24 calls on the same12 IDs; E remains unchanged. Appended strict answer-only/conclusion wording is frozen in output_contract_v3_bounded_repair.json. This is distinct from the prospectively approved initial clarification.
- Use30-minute finite allocation to cover observed startup; no model/runtime/seed/cap change. If repaired technical gate fails, stop full-cohort generation and science interpretation.

### Step Result — 2026-09-29T07:45:21.991573+00:00
- Confirmed: bounded wording repair improves D format1/12→9/12 and removes9 cap hits, but3 intermediate calculations violate the fixed gate; C finals7/12→8/12, caps remain4/12, severe cycles7/12→6/12. E11/12 passes unchanged.
- Evidence: outputs/stage12a/v1/stage12a_technical_prompt_validation.json; audit/technical_v1_review.json; audit/technical_v2_review.json. Actual saved input prompts/image receipts match all frozen tasks. Root cause remains unknown.
- Consequence: stop before full61-family execution or correctness scoring. This is technical noncompliance, not evidence against the Lost-Keys hypothesis.
- Artifacts: outputs/stage12a/v1/stage12a_summary.md and reports/stage12a/v1/index.md; all required artifacts and raw versions preserved.
- All GPUs released; no recommendation executed.
