# Stage 12T-S — Thinking scientific rescue on the frozen MathVision cohort

Status: **DRAFT — separate user authorization required before execution.**
Created 2026-09-29 UTC after Stage12T-R returned `THINKING_REGIME_VALIDATED`,
as required by Stage12C-R section27. Creation of this plan is not execution
authorization or an additional scientific recommendation.

## Objective and evidence boundary

Estimate Thinking rescue of the frozen native failure strata B1 and B4, with
paired prompted-CoT versus Thinking transitions. Preserve the Stage12B-S main
Claim1 and the sparse CoT result. Completion validation is not evidence of
Thinking accuracy or rescue.

Stage12T-R at81920 tokens yielded12/12 scoreable on the original validation set
and11/12 on the prospectively selected fresh set, with one pre-outcome cap.
Severe repetition remains present. Nine original trajectories match exactly;
both previously capped trajectories and item2864 diverged before their old
endpoints. Do not claim a pure budget explanation for prior noncompletion.

## Frozen cohort and inputs

- Exactly the existing61 independent MathVision families and157 E* facts.
- Preserve Stage12B-S E/N/O outputs, correctness, B1–B4 assignments, subtypes,
  technical missingness and R1–R5 annotations.
- Preserve Stage12C/12C-R CoT outputs, scores and trace annotations.
- Same original image/question, preprocessing, chat template and family seeds.
- No new benchmark, reserve expansion, model, prompt, penalty or cap search.

The source manifests and provenance are under `outputs/stage12cr/v1/`,
including `stage12tr_same12_manifest.json`, `stage12tr_fresh12_manifest.json`,
the two completion decisions and the prospective preservation records.

## Validated Thinking condition

Qwen3-VL-4B-Thinking revision `1de27d8c51f12e819435303b9e84c4e25ba8401e`.
Original image/question without a CoT suffix; temperature1.0, top-p0.95,
top-k20, repetition penalty1.0, presence penalty0, max output81920.
Reuse the pinned BF16/vLLM runtime, max model length128000, preprocessing and
family seed policy. Record actual batch membership; stochastic prefix identity
is diagnostic, not a completion prerequisite.

## Execution, if separately approved

1. Read access/GPU policies and phase memory. Freeze source hashes, the61-family
   manifest, analysis rules and exact37 missing generation calls before any new
   generation or Thinking correctness scoring.
2. Reuse all24 Stage12T-R outputs unchanged, including the capped case. Generate
   only the remaining37 families once. Do not mix old40960-token responses into
   the81920 condition. No retries chosen by technical behavior or correctness.
3. Verify input receipts and annotate scoreability, pre-outcome truncation,
   normal stop, closed thinking/final channels and frozen R1–R5 behavior for
   all61. Reuse the24 existing technical reviews. Seal denominators first.
4. Use `INPUT_VALID and SCOREABLE and not TRUNCATED_BEFORE_OUTCOME` for analysis.
   Repetition, reopening, nonconvergence and long advancing computation are
   behaviors, not automatic exclusions. Never count technical missingness as
   wrong. Report frozen and scoreable denominators plus missingness bounds.
5. Before correctness, annotate all26 complete-profile native-failure Thinking
   traces against E* in packets without correctness or B1–B4 labels, using
   FULL/PARTIAL/WRONG_OR_CONFLICTING/NOT_EXTERNALIZED. Retain review coverage;
   absence from a visible trace is not internal evidence absence.
6. Score T-only packets using the frozen MathVision equivalence policy, without
   E/N/O/C outcomes or stratum labels. Apply ambiguity-triggered second review
   plus the inherited deterministic20% unambiguous audit. Seal scores before
   joining frozen strata or C outcomes. Describe reviewer independence honestly.
7. Complete the predefined analyses and resource/preservation checks, then stop.

No new aggregate technical threshold is selected after outcomes. Any technical
issue preventing the frozen validity/scoring rules from being applied must be
reported without decoding search or replacement cases.

## Analyses frozen before correctness

Primary: `P(T+ | B1)` and `P(T+ | B4)`, with exact counts, Wilson95% intervals,
and their difference with4000 family-bootstrap draws using the inherited fixed
seed120220260929. Family-equal weighting; strata B1/B4, no token independence.
Use careful B1 wording: incomplete demonstrated recovery of task-critical
visual evidence. Preserve the7explicit-wrong/4unresolved-only distinction.

Report paired C/T correct-to-wrong and wrong-to-correct transitions, both
correct, both wrong and missing pairs; B2(n1)/B3(n3) are descriptive only.
Relate B1 rescue to visible TRACE_E_FULL and B4 rescue to R1–R3 transitions
descriptively. These associations do not establish hidden-state mechanisms.

Native Thinking versus prompted CoT compares model variants under their
validated native recipes and budgets. It is not an isolated checkpoint effect
under identical decoding. Do not select protocols by accuracy.

## Resources and deliverables

No GPU job is authorized by the creation of this draft. If approved, use the
project scheduler/Slurm and machine-local policy, at most the user-authorized
eight GPUs on allowed nodes. Prefer sufficient batching and finite workers;
release each allocation immediately on completion.

Planning estimate: Stage12T-R used about1.72 allocatedGPUh for24 calls, suggesting
about2.65GPUh for37 additional calls by simple proportional scaling. Lengths
vary greatly; freeze a target below3.5 and hard stop5 allocatedGPUh for new work,
including startup, before launch. Do not exceed it without authorization.

Save a scientific specification, immutable manifests/input receipts, raw
outputs/token IDs, technical labels, blinded scores/reviews, trace labels,
family-level results, inference/decision JSON, resource accounting, figures,
summary and preservation verification under a new Stage12T-S output version.
Distinguish24 reused calls from37 new calls and account for new compute only.

## Stop

Complete the61-family analysis if technically interpretable; preserve sparse,
negative or unresolved evidence. Report exactly one evidence-based scientific
recommendation without executing it. No further budget extension, causal
interventions, oracle runs, model changes or new research stage automatically.
