# Phase 3C.8: Token-Type Carrier Atlas

## Current Objective

Execute the user-approved `plan/stage3c8_plan.md` as one bounded action: construct a fresh causal carrier cohort, characterize natural `t_pre`, recent-reasoning, and prompt/question token-cache carriers, run the gated long-horizon checkpoint extension only if eligible, issue one recommendation, and stop.

## Active Constraints

- Preserve all Stage 3C.7 and earlier artifacts.
- Use eight mechanical-validation bases, exact 24 historical anchors, and 64 target / 56 minimum fresh unique bases.
- Select and annotate without attention or Stage 3C.8 carrier outcomes; freeze taxonomy, spans, ROIs, `E_d`, and families before scoring.
- Keep Phase A, B, C, and gated D references separate; use `base_problem_id` as the independent unit.
- Use A5000, seed 1234, eager attention, native GQA K/V, and exact inherited P4/T16/cutoff semantics.
- Do not manipulate sink probability, run an unconstrained whole-history search, learn residual features, start Stage 4, or analyze failures.

## Current State

- Done: Stage 3C.7 passed 20/20 with complete tested `t_pre` K+V rescue for both targets and target-heterogeneous joint rescue.
- Done: Stage 3C.8 plan read completely and implementation decisions frozen in `workspace/stage3c8_implementation_plan.md`.
- Done: prospective 240-base screen, 8-base validation set, exact 24 historical anchors, taxonomy, span rules, and primary families were frozen before carrier scoring.
- Done: the prospective screen stopped when the first 64 fully qualified fresh bases were resolved. It preserved 105 raw outcomes (82 correct, 23 wrong), manually reviewed 82 trace-aligned proposals, constructed 75 edit candidates, rejected 11 construction attempts, and froze exactly 64 semantic/edit/ROI-valid bases without attention or carrier outcomes.
- Done: the 96-base disjoint validation/historical/fresh visual-entity lexicon and token/span annotations were frozen before scoring (31,682 token rows; 29,077 spans).
- Done: the required eight-base Phase A/B/C mechanical validation passed every planned check, including exact self patches/repeats, cache-position selectivity, T16 and cutoff semantics, visual-cache invariance, and finite scores.
- Done: Phase A scored all 24 historical anchors and 64 fresh bases. Historical reproduction was exact. Fresh full-KV rescue was robust at both coordinates (`a_like`: 64/64 positive, median 1.125; `b_like`: 57/64 positive, median 0.151). V-only rescue was broadly positive; K-only rescue was weak or negative overall.
- Done: Phase B scored all 24 historical anchors and 64 fresh bases. Rescue was strongly recency-localized (robust mainly at distance 1 and sometimes 2; little signal at 4--16). Later-coordinate visual-entity and target-aligned effects survived matched recency controls; earlier-coordinate function-word groups were also robust.
- Done/gated off: the Phase A/B carrier gate opened Phase D, but only 15 fresh bases met the independently frozen long-horizon eligibility rule, below the minimum 28. Phase D causal scoring, necessity, and route controls therefore remain unrun with explicit empty artifacts.
- Done: Phase C scored all 24 historical anchors and 64 fresh bases. Full-Q transfer was robust (61/64 positive; median 0.624). `NUMERIC_LITERAL` and `PUNCTUATION` passed the frozen K+V gate, and the authorized K/V decomposition completed on all 64 fresh bases.
- Done: cross-phase analyses, all 22 figures, the 25/25 acceptance report, 16/16 independent artifact audit, and 37/37 focused tests passed.
- Blocked: project-local `research-control` skill is not installed; the explicit user-approved plan governs this action directly.
- Most recent useful observation: carrier structure is globally recency-dominant but phase- and coordinate-specific; only 15 fresh traces met the frozen long-horizon Phase-D rule, so checkpoint lifecycle inference remains infeasible rather than negative.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Exact prior-cache rescue | `outputs/stage3c7/analysis/two_query_classification.json` | Establishes the historical anchor mechanism | confirmed |
| Exact P4 mechanics | `outputs/stage3c7/audit/artifact_validation.json` | Provides validated K/V capture and rescue semantics | confirmed |
| T16 semantics | `outputs/stage3c4/` | Defines the Phase-B deficit | confirmed |
| Generation-start cutoff/Q patch | `outputs/stage3b0/`; `code/visual_reasoning/stage3b0/` | Defines Phase-C residual and transfer | confirmed |
| Existing edit/evaluator pipeline | `outputs/stage3b9/`; `scripts/stage3b9/` | Provides validated prospective generation, numeric evaluation, and local-edit patterns | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Stage 3C.7 first smoke | inherited two Slurm tasks wrote one target | supported launch configuration error | explicitly set one task per one-GPU shard | do not rely on inherited allocation task count |
| Cross-image carrier rescue | state mismatch weakened interpretability | supported design limitation | use within-condition native/suppressed donors | do not make cross-image transplantation primary |
| Unscoped pytest | collected vendored/cache tests | supported collection-scope error | run repository tests under `tests/` with importlib | do not treat third-party collection as project regression |
| Parallel scheduler-record mutation | one of two newly added queue records disappeared | supported shared-state update race: sequential re-add restored both records before launch | mutate `gpu_scheduler.py` queue state sequentially | do not run concurrent scheduler add/update commands |
| Two independent overlapping `srun` steps | both generation shards were bound to physical GPU 0 and shard 01 OOMed | supported by the OOM process accounting plus Slurm step behavior | launch one two-task step and select CUDA from `SLURM_LOCALID` | do not assume separate overlapping one-task steps consume distinct GPUs |
| Resume dispatcher on allocation 107969 | both tasks exited before model load because the dispatcher queried expired allocation 106936 with `check=True` | supported by `generation_resume_107969.log` and a failing regression test | remove the obsolete allocation-specific wait; allocation lifecycle is now controlled by tmux/Slurm | do not hard-code a prior Slurm job ID in a reusable dispatcher |
| First cohort freeze attempt | one correct base that completed during shutdown had not entered the earlier proposal snapshot | supported by the independent screen-prefix validator naming base 191 | regenerate proposals from the final raw manifest and resolve every correct base before the retained cutoff | do not freeze from a proposal snapshot taken while generation is still writing |
| Annotation preparation | the extra held-out base 3 lacks historical `state_pairs` | supported by `KeyError: state_pairs` and its Stage 3A manifest schema | use frozen `E_d`/`E_d-1` A-like/B-like coordinates for validation rows without state pairs | do not assume every validation source has the Stage 3C.7 schema |
| First atlas validation launch | rank 1 selected CUDA ordinal 1 even though each Slurm task saw one local device | supported by the invalid-device exception and a regression test | map each task to local ordinal 0 when `CUDA_VISIBLE_DEVICES` exposes one device | do not equate `SLURM_LOCALID` with a visible CUDA ordinal after per-task GPU binding |
| First Phase-B launch | command used a stale model snapshot path and failed before inference | supported by the Hugging Face path validation traceback and zero Phase-B results | resolve the checkpoint from frozen `stage3c8_config.json`; corrected launch loaded both ranks | do not hand-copy model snapshot hashes into launch commands |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Visual-entity carrier bias | entity-aligned tokens may consolidate evidence | Phase A/B matched type analyses | open |
| Boundary integration | punctuation/span ends may integrate state | matched structural controls | open |
| Recency-dominant carriage | `t_pre` may be special mainly by distance | exhaustive Phase-B profile | open |
| Distributed token cache | groups may rescue when single positions do not | type/all-recent/full-Q group references | open |
| Phase-specific taxonomy | prompt and late carriers may differ | separate Phase B/C comparison | open |
| Repeated dynamic checkpoints | long reasoning may contain multiple functional anchors | gated Phase D source-deficit plus future-use rescue | open |

## Next-Step Decision

- Current bottleneck: the frozen Phase-D long-horizon cohort has only 15 eligible fresh bases versus the minimum 28.
- Relevant memory item used: Phases A--C establish strong but phase-specific token-cache carriage; the missing result is repeated long-horizon causal checkpoint support, not another token-type atlas.
- Chosen next action: none. Stop for user review with one conditional recommendation; do not recursively construct or run the recommended cohort.
- Why this action: Stage 3C.8 satisfied its technical and scientific scope, while the remaining question requires a separately reviewed cohort design.
- What not to repeat: do not compare raw CRR values across Phase A/B/C as if their deficits and references shared a denominator, and do not interpret Phase-D infeasibility as a null.
- Stop condition: met; all required artifacts, figures, reports, tests, and validation are complete.

### Step Result

- Action taken: completed and independently validated the eight-base mechanics gate, then scored and analyzed Phase A on the exact 24 historical anchors and frozen 64-base fresh cohort.
- Result: all mechanical checks passed; all 24 historical anchors reproduced exactly. Fresh full-KV rescue was robust at `a_like` (mean 1.669, median 1.125, 64/64 positive, bootstrap 95% CI [1.225, 2.171]) and `b_like` (mean 0.278, median 0.151, 57/64 positive, CI [0.190, 0.381]). V restoration carried most positive rescue, whereas K alone did not show a robust positive overall effect.
- Evidence saved: `outputs/stage3c8/audit/mechanical_validation.json`, `outputs/stage3c8/raw/phase_a/`, `outputs/stage3c8/phase_a_tpre/`, `outputs/stage3c8/analysis/historical_vs_fresh_replication.json`, and `runs/stage3c8_tmux/phase_a_107969.log`.
- Failure or issue: the first atlas validation launch used an invalid per-task CUDA ordinal; the first Phase-B command used a stale snapshot path. Both failed before producing primary scores and were repaired mechanically with the frozen protocol unchanged.
- Lesson learned: under `--gpus-per-task=1`, local CUDA ordinal must be resolved against the process-visible device count, and all launches should read/copy the checkpoint from the frozen configuration rather than reconstructing it.
- Next implication: finish Phase B and apply its prospective gate; Phase A alone is insufficient for token-type claims because recency/position controls are mandatory.

### Phase-B Boundary Result

- Action taken: completed the exhaustive recent-position, fixed-distance K/V, span, type-group, cumulative-width, and matched-recency Phase-B analyses on all 88 primary/anchor bases.
- Result: at `a_like`, distance-1 KV rescue was robust (median 2.382; 64/64 positive) and distance-2 KV remained robust (median 0.125; 56/64 positive), while distances 4--16 were null. At `b_like`, distance-1 KV was robust (median 0.296; 60/64 positive); distance-2 V was robust but distance-2 KV missed the 75% directionality rule; distances 4--16 were null. `VISUAL_ENTITY` and `TARGET_ALIGNED` survived matched recency controls at `b_like`; `FUNCTION_WORD` was the robust matched lexical class at `a_like`. The all-recent median RR was 0.478, below its 0.50 sub-gate.
- Evidence saved: `outputs/stage3c8/raw/phase_b/`, `outputs/stage3c8/phase_b_recent/`, `outputs/stage3c8/analysis/position_vs_type_analysis.json`, `outputs/stage3c8/analysis/sparse_vs_distributed_analysis.json`, and `runs/stage3c8_tmux/phase_b_107969_retry.log`.
- Gate result: Phase D's carrier gate opened because Phase A was robust, but the frozen long-horizon cohort gate closed with only 15/28 minimum eligible fresh bases. No Phase D score exists; all gated outputs are explicitly empty.
- Next implication: Phase C must determine whether prompt/question carriers show a distinct prefill taxonomy; long-horizon checkpoint claims are not supported because the planned cohort was infeasible.

### Final Stage Result

- Action taken: completed Phase C on 24 historical and 64 fresh bases, applied its frozen type-group gate, ran the authorized two-class K/V decomposition, assembled cross-phase analyses and figures, independently validated artifacts, and wrote exactly one recommendation.
- Result: full-Q transfer was robust (61/64 positive; median 0.624). `NUMERIC_LITERAL` K+V transfer was primarily K-associated; `PUNCTUATION` K+V was primarily V-associated, but punctuation underperformed nearest matched prompt controls. Together with Phase B, the defensible outcome is O4 recency-dominant plus O6 phase-specific carrier structure, with a narrower later-coordinate visual-entity effect.
- Evidence saved: `outputs/stage3c8/phase_c_prompt/`, `outputs/stage3c8/analysis/`, `outputs/stage3c8/audit/artifact_validation.json`, and `outputs/stage3c8/summaries/`.
- Gate result: Phase D remained unrun because only 15/28 minimum fresh bases met its independently frozen long-horizon rule. This is infeasibility, not a negative checkpoint result.
- Verification: Stage acceptance 25/25 PASS, independent artifact audit 16/16 PASS, 37/37 focused tests PASS, and 22/22 figures present.
- Next implication: sole review-only recommendation is **CONDITIONAL GO — Dedicated Long-Horizon Causal-Checkpoint Cohort**. No later experiment has started.
