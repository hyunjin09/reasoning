# Stage 3C.9 Implementation Plan — Dedicated Long-Horizon Causal Checkpoints

## Scope and observable success

Execute `plan/stage3c9_plan.md` as one bounded research action. Success means: cohort and event rules freeze before causal scores; the prospective screen retains at least 40 valid unique long-horizon bases plus eight disjoint validation bases; all 16 mechanical checks pass; Phases A--C complete on the frozen primary cohort; Phase D follows its 16-base repeated-checkpoint gate; required analyses, figures, and reports independently validate; exactly one next-stage recommendation is written; and no prohibited follow-on starts.

If fewer than 40 valid bases remain after the full prospective screen, stop before primary causal scoring and report cohort feasibility. A technical pass does not require a positive repeated-checkpoint or route result.

## Frozen design decisions

- Runtime: Qwen3-VL-4B-Thinking with the locked official Thinking protocol (`do_sample=true`, temperature `0.6`, top-p `0.95`, top-k `20`, presence penalty `0.0`, `max_new_tokens=40960`, seed `1234`), native eager language attention, project `.venv`, and the existing Slurm allocation in tmux session 8 on three A5000 GPUs. Do not request more GPUs. Causal scoring advances frozen prefixes with native DynamicCache in bounded 128-query chunks to avoid constructing one quadratic eager-attention matrix over an entire long trajectory; exact cached-vs-full local-prefix parity is a mechanical validation requirement.
- Initial screening: 600 unique Vision Dominant trajectories. Rank using only frozen dataset text/metadata: presence of a Text-Dominant-to-Vision-Dominant localized numeric-fact candidate, descending static Vision-Dominant question length, source name, and base ID. No prior generation outcome, attention, or carrier score enters the order.
- Reserve screening: predeclare up to 1,000 total rows. After the 788 unique Vision Dominant bases, add Vision Intensive rows in the same frozen base order until 1,000. Retain at most one primary trajectory per `base_problem_id`, taking the first fully eligible row in frozen order.
- Cohort gate: target 48, minimum 40 primary bases; eight additional eligible bases are assigned to validation by frozen screen order and remain disjoint. Do not relax the ten inclusion criteria.
- Event annotation: three or more semantic/subgoal segments and three or more independently text-defined candidate events, including two separated by at least 24 generated tokens. First assign matched controls while excluding every text-defined event candidate; for bounded, non-effect-selected scoring, freeze exactly the first, midpoint-nearest, and last control-eligible event by annotation order. Spans are 1--8 tokenizer positions and are selected from text/semantics only. Every local-use readout is 1--32 tokenizer positions after its span; the automated numeric anchor leaves at least one downstream bridge token between the checkpoint-span end and the candidate readout. Local-use and final-use readouts freeze before any causal score.
- Evidence/editing: reuse the validated Stage 3B.9/3C.8 localized semantic quartet and ROI construction, but revalidate every retained Stage 3C.9 item. Exact prompt/image-token layout is mandatory.
- Phase A: target-ROI contribution suppression over both prospective W8 and W16 acquisition windows, all 36 language layers and all logical heads. Local-use loss is primary; final-use loss is secondary.
- Phase B: within-condition native event-span K+V rescue into the matching source-deficient recipient, followed by exhaustive constituent-token localization and predeclared same-length neighboring controls. Visual caches are never donor-patched.
- Checkpoint rule: C2/C3 requires an evaluable local source deficit and robust positive event-span rescue. Matched neighboring spans have the same tokenizer-position count, lie within ±8 generated positions, do not overlap any frozen event, and also leave at least one downstream bridge token before the local evidence readout. Negligible source loss is source-insensitive under the tested window, not evidence of non-visuality. Rescue ratios remain unclipped.
- Coordinate convention: persisted generated-token indices and half-open span bounds are zero-based. Runtime absolute positions are `prompt_length + generated_index`; reused Stage 3C.4 query-window APIs receive their required one-based generated coordinates only at the adapter boundary.
- Phase C: lifetime readouts use only independently annotated semantic downstream coordinates. C3 persistence requires final `E_d` to be a distinct downstream coordinate from the checkpoint's local-use readout; an identical local/final coordinate is preserved descriptively but cannot establish persistence. `REPEATED_CHECKPOINT` requires at least two non-overlapping C2/C3 spans separated by at least 24 tokens.
- Phase D: run only if at least 16 primary bases have two confirmed separated checkpoints; freeze the first eligible pair by annotation order. Compare direct W8, prior checkpoint, fixed checkpoint-through-next-8 history, and joint routes without path-fraction claims.
- Phase E: enrichment is post-checkpoint and controls distance, progress, span length, local density, and boundary position. Attention/QK/sink overlay is optional descriptive analysis only and is omitted unless all primary causal outputs have frozen.

## Ordered thin slices

1. **Freeze protocol and screening manifests.** Add tested deterministic selection/gate helpers, write create-once config/taxonomy/window/route files, and shard the first 600 rows across three ranks. Verify counts, hashes, unique-base coverage, and zero outcome/attention provenance.
2. **Generate and account for the initial screen.** Run three resumable baseline-generation shards under the locked protocol, preserve all raw outcomes, and verify 600 completed trajectory records. Extend only if the cohort yield requires it.
3. **Draft and manually audit candidates.** From completed-correct trajectories, construct text-semantic segments, candidate events, local/final readouts, localized evidence edits, ROIs, and review sheets. Manually validate trace alignment and each O/O_sham/C/C_sham edit before freezing eight validation plus 48 target primary bases.
4. **Implement causal primitives test-first.** Extend validated Stage 3C.4/3C.7 mechanics for event-local W8/W16 suppression, multi-token K+V rescue, matched neighbors, lifetime readouts, and gated route intervention. Add RED tests before each behavior.
5. **Mechanical validation.** Run all 16 plan checks on eight disjoint bases, including route ordering on at least three eligible examples. Stop and surgically repair any failed mechanism before primary scoring.
6. **Phases A and B.** Score W8/W16 source sensitivity, then event-span/single-token/neighbor rescue for every frozen event. Freeze checkpoint classes without changing spans.
7. **Phase C and gated D.** Evaluate semantic lifetime coordinates and repeated-checkpoint status. Run route decomposition only if at least 16 bases pass the repeated-checkpoint gate.
8. **Phase E, analysis, validation, and report.** Aggregate by base, make the 15 required figure families (plus route figures only if gated in), independently rederive metrics/invariants, update compact state, issue exactly one recommendation, and stop.

## Risks and guardrails

| Risk | Consequence | Guardrail |
|---|---|---|
| Initial 600 yield fewer than 40 valid bases | Primary inference cannot start | Use the prospectively frozen reserve up to 1,000; never relax inclusion rules. |
| Automated segmentation mistakes | Invalid checkpoint coordinates | Manually inspect every retained and validation trajectory and preserve review decisions. |
| Static complexity ranking changes evidence mix | Limited generality | Report source/evidence distributions and all exclusions; never select on causal scores. |
| Span rescue reflects recency | False checkpoint identity | Use same-length neighboring spans within ±8 tokens and base-level paired inference. |
| Weak source deficit | Rescue denominator is uninterpretable | Classify C0 and exclude from checkpoint claims rather than treating it as a negative rescue. |
| Compute exceeds the current allocation | Partial stage | Use resumable rank-disjoint shards and record every run; do not request extra GPUs. |

## Stop boundary

Stop after the Stage 3C.9 reports and exactly one recommendation. Do not start sink causality, residual/subspace learning, an unconstrained history search, Stage 4, multi-evidence refresh, or failure analysis.
