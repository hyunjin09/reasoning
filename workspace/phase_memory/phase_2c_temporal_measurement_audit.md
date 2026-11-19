# Phase 2C: temporal measurement audit

## Current Objective

Complete the artifact-only Stage 2C temporal audit on 40-50 completed-correct Stage 1B trajectories, determine the exact predictive alignment of retained attention rows, and prepare a clean pre-E1 candidate pool without starting a causal experiment.

## Active Constraints

- Do not modify historical Stage 1, Stage 2A, or Stage 2B artifacts.
- Select examples and annotate evidence without inspecting ROI-attention patterns.
- Use the retained Stage 1 arrays only; no new model inference is authorized or scientifically needed.
- Treat all attention results as descriptive and keep semantic alignment as a competing explanation.
- Try the bounded analysis job on two A6000 GPUs on node03 once; if it fails, submit without a node constraint and exclude node03.
- Stop after the Stage 2C audit, candidate pool, summary, acceptance report, and next-stage recommendation.

## Current State

- Done: Stage 2B technical validation passed 12/12, but its frozen scientific rule produced a NO-GO (`0/5` P1, `1/5` P2, median target-minus-irrelevant delta-NLL `0.0022` nats/token).
- Done: The artifact-only analysis targets 50 completed-correct examples, retains 70 evidence events, and produces all required timing/semantic-alignment/re-audit/candidate outputs.
- Pending: Slurm job `105744` is waiting for two A6000s on any A6000 node except node03; this is the user-authorized fallback after node03 had only one free GPU.
- Blocked: Final scheduled A6000 reproduction is resource-pending, but the bounded CPU dry run and independent output validator pass.
- Most recent useful observation: `OnlineAttentionRecorder` retains the final query row from each generation forward. Retained row `t` produces logits for generated token `y_t`; row 0 queries the final prompt token, while row `t>0` queries `y_(t-1)`. Historical token labels therefore describe the next token predicted, not the token supplying the query.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Stage 2B did not support attention-guided ROI causality under the frozen rule | `outputs/stage2b/summaries/stage2b_summary.md` | Motivates a timing/measurement audit instead of another intervention | confirmed |
| Stage 1 retains token-level, layer/head-aggregated focus over every visual-token position | `outputs/stage1/discovery/examples/<id>/attention_summary.npz` | Enables ROI/event analysis without rerunning inference | confirmed |
| Recorder stores final query row and key lengths advance from prompt length | `code/visual_reasoning/stage0/attention.py`; example 699 arrays | Resolves the predictive versus processed-token alignment | confirmed |
| Twenty Stage 2A examples already have manually passed ROI mappings | `outputs/stage2a/evidence_subset/manual_roi_mapping_review.json` | These mappings can be reused unchanged | confirmed |
| Most ROI timing is mention-centered | `outputs/stage2c/analysis/event_aligned_statistics.json` | 58/70 events are T2; raw timing primarily tracks explicit semantic spans rather than clear pre-mention leads | confirmed |
| Most Stage 2B windows were post-explicit | `outputs/stage2c/stage2ab_reaudit/stage2b_window_timing.json` | 8/10 target windows begin after E1 and therefore did not test initial acquisition | confirmed |
| Clean counterfactual pool is feasible | `outputs/stage2c/candidates/counterfactual_ready_candidates.jsonl` | 38 evidence items across 26 examples pass the best-effort leakage/editability/mapping screen | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Stage 2B ROI-edge masking during annotated windows | No strong A/B crossover in any of five examples | Direct observation is supported; whether timing, carrier transfer, or semantic alignment explains it remains unknown | Audit E0/E1/E2 timing before selecting another causal test | Do not reinterpret high ROI attention as acquisition or repeat the same intervention family |
| Generic Stage 2A event-use selection for example 2749 | No A+B span followed the first automatically selected evidence groups | Supported annotation edge case, not an inference failure | Freeze explicit span overrides for 2749 A/B and retain the correction in the preparation script | Do not silently force a nonexistent generic A+B use |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Prediction-aligned ROI attention leads E1 | Retained rows predict the labeled next token | Fixed +/-64-token event analysis around E0/E1/E2 | open |
| Peaks are mention/semantic-alignment effects | A generated entity token becomes the next query one row later | Compare predictive and processed-token views at first and repeated mentions | open |
| Clean pre-E1 counterfactual candidates exist | Stage 2A already localized 40 facts across 20 examples | Attention-blind annotation and leakage/editability screening | open |

## Next-Step Decision

- Current bottleneck: The complete artifact analysis awaits its scheduled two-A6000 reproduction because non-node03 A6000 capacity is currently full.
- Relevant memory item used: Stage 2B was a scientific NO-GO despite technical validity, and the retained attention row is prediction-aligned to `y_t` while querying the preceding context token.
- Chosen next action: Wait for Slurm job `105744`; after it runs, inspect the runtime record/log and final acceptance report. Do not select or execute another research experiment.
- Why this action: The audit itself is complete, and the remaining work is only the explicitly requested A6000 reproduction/verification.
- What not to repeat: No new model inference, ROI masking, carrier patching, counterfactual image creation, or causal interpretation of attention.
- Stop condition: Required Stage 2C outputs and acceptance checks are complete, or fewer than 40 valid attention-blind examples can be annotated reliably.

### Step Result

- Action taken: Froze an attention-blind 50-example cohort; reviewed 70 E0/E1/E2/ROI annotations; resolved the stored-attention convention; computed fixed +/-64 token- and span-level ROI timing; audited repeated mentions; re-audited Stage 2B and reinterpreted Stage 2A; produced 38 future candidates; submitted the requested fallback A6000 job.
- Result: The bounded dry run passes all 15 Stage 2C acceptance criteria. Categories are T1=3, T2=58, T3=2, T4=4, T5=0, T6=3. Eight of ten Stage 2B target windows begin after E1. Slurm job `105744` remains pending.
- Evidence saved: `outputs/stage2c/summaries/stage2c_summary.md`, `outputs/stage2c/analysis/event_aligned_statistics.json`, `outputs/stage2c/stage2ab_reaudit/`, `outputs/stage2c/candidates/`, and `outputs/stage2c/summaries/slurm_submission.json`.
- Failure or issue: Node03 had only one live free A6000 rather than the two requested, so the bounded node03 run was not possible. The approved fallback excludes node03 and is waiting for capacity.
- Lesson learned: ROI attention is overwhelmingly mention-centered in this audit, and Stage 2B mostly intervened after explicit scratchpad availability; neither observation is causal evidence.
- Next implication: If job `105744` succeeds, retain the GO recommendation for a separately approved counterfactual-content pilot; if it fails for a node/runtime reason, diagnose only that bounded reproduction. In all cases stop before Stage 3 pending review.
