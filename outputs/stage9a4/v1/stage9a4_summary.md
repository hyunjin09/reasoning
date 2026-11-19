# Stage 9A.4 — Qwen3-4B finite-access result

Completed 2026-09-27T03:43:24.929944+00:00. Outcome **B**. The authorized sequence is complete; all GPU allocations are released.

**Main result:** under the frozen 5 percentage-point criterion, Qwen3-VL-4B prompted CoT preserves performance with direct image-key access through token 128. Token64 is insufficient. This supports finite access at a later tested budget than the calibrated Qwen2.5 result.

The repaired Qwen3-VL-4B-Instruct FULL baseline is valid on the original 32 synthetic images/64 queries: 45/64 correct (70.31%), 64/64 genuine intermediate reasoning, 60/64 valid final options and normal EOS, 4/64 capped. All five gates pass. All eight actual-model V1–V6 checks pass, including exact FULL no-op, unchanged prefill, all 36 layers, 64/128/256 transitions, cache validity and no-redistribution checks.

Primary 32-image results (two queries per independent image; 95% paired image-bootstrap intervals):

| Access condition | Accuracy | Damage vs FULL | 95% interval (pp) |
|---|---:|---:|---:|
| full | 70.31% | 0.00 pp | [0.00, 0.00] |
| t0 | 43.75% | 26.56 pp | [10.94, 42.19] |
| t64 | 57.81% | 12.50 pp | [3.12, 21.88] |
| t128 | 71.88% | -1.56 pp | [-4.69, 0.00] |

ZERO establishes useful generated-token direct access. Token64 damage is 12.50pp, exceeding the 5 pp criterion; the approved sequential rule was followed. The first point-preserving cutoff was **128 tokens**.

The reserve precision gate was not triggered; no reserve generation was performed.

Bounded null-sink control on the primary 32 images: ZERO damage **37.50pp [21.88, 53.12]**; token 128 damage **3.12pp [0.00, 7.81]**. Damage at ZERO and point preservation at the finite cutoff survive without redistributing removed image probability.
The control's finite-cutoff preservation probability is 86.48%; its interval crosses 5 pp, so redistribution-independent preservation remains uncertain at that tolerance.

At token 64, the descriptive shift relative to frozen Qwen2.5's 48-image −1.04pp result is **13.54pp**. That headline uses unequal cohort sizes. The genuinely paired primary 32-image comparison gives **15.62pp [4.69, 26.56]**. The Qwen2.5 baseline uses 256 tokens and 3B parameters; Qwen3 uses 512 and 4B. This supports a checkpoint/generation access-regime difference candidate, without isolating capacity, training, architecture or DeepStack.

The study uses the original images, prompts/options, preprocessing, greedy BF16/eager-language backend and seed 920260927. DeepStack is unchanged. Restrictions affect generated queries to cached image keys; prefill and image-derived cached state remain. There are 4,000 family-equal image bootstrap draws. Queries, tokens and conditions are not independent samples. Point preservation is not proof of equivalence; intervals and actual mask exposure are retained in the analysis artifacts. Literal final-answer review is sealed before gold joins, with raw strict-format sensitivity alongside it.

The mask is reached in 63/64 token 64 trajectories and 43/64 token 128 trajectories; the remaining 21 token 128 queries are exact FULL identities. Capped counts are FULL 4, ZERO 9, token 64 7 and token 128 4; unscorable counts are 4/8/7/4. Thus final-performance effects include completion failures and are not isolated local visual-decoding errors. Raw strict-format scoring yields the same primary accuracies and decision.

Compute: **0.562 allocation GPU-hours**, 341 new scientific generations, at most 4 GPUs. Generation time itself is 0.428 GPU-hours. All jobs used the project scheduler/Slurm; no downloads, tmux or keepalive. Nine focused CPU tests and 7 final audit groups passed. Reused Stage9A.3 artifacts are verified byte-identical.

Four figures (PNG/PDF): [baseline validity](figures/figure1_baseline_validity.pdf), [temporal access](figures/figure2_temporal_finite_access.pdf), [same token64](figures/figure3_same_token64.pdf), and [null-sink robustness](figures/figure4_null_sink_robustness.pdf). [Artifact index](stage9a4_artifact_index.json).

**Exactly one recommendation:** Characterize the Qwen2.5→Qwen3 access-regime shift before attributing any difference to Thinking specialization.

**STOP. The recommendation has not been launched.**
