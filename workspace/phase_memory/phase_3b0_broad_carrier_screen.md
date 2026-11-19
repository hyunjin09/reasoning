# Phase 3B.0: broad post-image carrier screen

## Current Objective

Determine whether Stage 3A pre-E0 visual-content sensitivity survives a generation-start visual cutoff and whether bidirectional post-prefill KV patching of broad nonvisual prompt groups (`P_post-image` and `Q`) recovers evidence preference.

## Active Constraints

- The 49 frozen Stage 3A `base_problem_id` values are the independent cohort; selection and grouping may not use attention or Stage 3B.0 outcomes.
- Preserve Stage 3A and all earlier artifacts.
- Run the mandatory three-example technical smoke gate before cohort scoring.
- Use the exact strict pre-E0 prefix and evidence-specific continuations frozen in Stage 3A.
- Stop after Stage 3B.0; do not start layer-wise localization, carrier tracing, or any Stage 3B.1 experiment.
- GPU execution must use the machine-local scheduler wrapper and Slurm; node03 is excluded because its CUDA stack is currently broken.

## Current State

- Done: Stage 3A established positive counterfactual content sensitivity on 49/49 unique bases with a small sham effect.
- Done: Stage 3B.0 attempted all 49 frozen bases and passed all 15 technical acceptance criteria.
- Done: generation-start cutoff, broad/Q/T/Q+T bidirectional patches, self/sham controls, short rollouts, cohort statistics, figures, and the recommendation are complete.
- Blocked: None.
- Most recent useful observation: cutoff retained 14.5% mean / 6.1% median raw Stage 3A CE; Q carries nearly all of that surviving residual, but the residual is too small to explain most of Stage 3A.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| 49 frozen unique bases; 49/49 positive CE; mean sham-controlled CE 3.1864 | `outputs/stage3a/analysis/primary_statistics.json` | Supplies the frozen causal cohort and full-vision baseline | confirmed |
| All Stage 3A prefixes are strict pre-E0 with frozen hashes | `outputs/stage3a/cohort/primary_manifest.jsonl` | Prevents carrier analysis from leaking the target fact | confirmed |
| Stage 2C attention was predominantly mention-centered | `outputs/stage2c/summaries/stage2c_summary.md` | Motivates a content-causal screen independent of attention | confirmed |
| Node03 failed CUDA initialization | `outputs/stage3a/scoring/node03_cuda_diagnostic.json` | Prevents repeating a known infrastructure failure | confirmed |
| Cutoff CE positive in 42/49; mean/median raw retention 14.5%/6.1% | `outputs/stage3b0/cutoff/cutoff_statistics.json` | Prefill preserves a widespread but small residual | confirmed |
| P recovery 1.0; Q median recovery 0.9884; Q both-direction consistency 46/49 | `outputs/stage3b0/patching/patch_statistics.json` | Q is a major carrier of the cutoff residual | confirmed |
| Technical PASS 15/15; Stage 3B.1 not started | `outputs/stage3b0/summaries/stage3b0_acceptance.json` | Closes the authorized stage at its stop boundary | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Stage 3A node03 execution | CUDA initialization failed despite visible devices | supported by saved diagnostic | Exclude node03 until administrator repair | Do not submit Stage 3B.0 to node03 |
| Initial cached/full cutoff comparison | Up to 0.110 nats/token deterministic disagreement | supported as a full-vs-cached BF16 computation-path difference; exact kernel cause unresolved | Use full-sequence Stage 3A-compatible scores for RQ1 and matched cached baselines for patch contrasts | Do not mix full-sequence and cached paths inside one causal contrast |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Evidence remains available after generated-query-to-visual cutoff | Prompt prefill can distribute visual content into nonvisual states | Compare `CE_cut` with frozen Stage 3A `CE_full` | supported only as a small residual |
| Broad post-image prompt cache carries evidence | Prefill may write visual information into question/template positions | Bidirectional all-layer KV patch of frozen `P_post-image` positions under cutoff | supported for the residual |
| Question content specifically carries evidence | Question tokens are a semantically meaningful subset of post-image prompt state | Bidirectional all-layer KV patch of frozen `Q` positions under cutoff | supported for the residual |

## Next-Step Decision

- Current bottleneck: selecting or designing a post-prefill acquisition-timing experiment requires review of the completed Stage 3B.0 result.
- Relevant memory item used: the cutoff destroys most Stage 3A CE even though Q robustly transfers the residual that remains.
- Chosen next action: stop at the Stage 3B.0 review boundary and return **REDIRECT — Post-prefill acquisition timing**.
- Why this action: the predeclared Pattern D applies; immediate layer-wise prefill localization would explain only a small residual rather than the dominant Stage 3A effect.
- What not to repeat: do not interpret Q recovery as recovery of the full Stage 3A effect, and do not use the unstable mean normalized recovery when cutoff denominators approach zero.
- Stop condition: satisfied. Do not start Stage 3B.1, timing sweeps, Q→R patching, or module/head/path analysis without a new reviewed plan.

### Step Result

- Action taken: Froze the 49-base design, passed the three-base smoke gate, ran seven A5000 cohort shards, aggregated cutoff/patch/rollout results, manually audited rollout hits, and produced the required reports and figures.
- Result: Technical PASS (15/15). Cutoff CE was positive in 42/49 but retained 14.5% mean / 6.1% median raw full-vision CE. Broad P transferred the residual exactly; Q median recovery was 0.9884 with both-direction source consistency in 46/49; T was weak.
- Evidence saved: `outputs/stage3b0/summaries/stage3b0_summary.md`, `outputs/stage3b0/summaries/stage3b0_acceptance.json`, `outputs/stage3b0/cutoff/cutoff_statistics.json`, `outputs/stage3b0/patching/patch_statistics.json`, and the raw shard bundles under `outputs/stage3b0/raw/shards/`.
- Failure or issue: Cached and full-sequence eager scoring differed deterministically by up to 0.110 nats/token in smoke; matched-path contrasts resolve this. Normalized Q recovery has one extreme outlier because its denominator is approximately zero. Saved aggregate hook audits omit the explicit key-index list, but frozen layouts, exact modified-entry counts, and the mask unit test independently verify the intended key set.
- Lesson learned: A real Q-carried prefill residual exists, but prefill alone is not sufficient for most strict pre-E0 sensitivity; future review should prioritize post-prefill acquisition timing rather than prefill-layer localization.
- Next implication: Return `REDIRECT — Post-prefill acquisition timing` and stop before Stage 3B.1.
