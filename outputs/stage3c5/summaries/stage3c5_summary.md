# Stage 3C.5 summary

## Result

Stage 3C.5 is a **technical PASS (20/20)** with scientific outcome **O5 — No Clean Carrier** and one review-only recommendation:

> **GO — Current-Residual Mechanism**

The immediately preceding reasoning query is behaviorally relevant, but its necessary target-ROI contribution is broad-depth rather than W4/W5-local. At `t_pre=t*-1`, all-layer P5 suppression reduced the base-aggregated evidence score by median `0.4979` and was positive on `24/24` bases. The smallest frozen scope reaching 80% of P5 was P4 (layers 16–35), with median loss `0.5172`. P0 (W4), P1 (W5), and P2 (W4+W5) produced only `0.0292`, `0.0200`, and `0.0631` median loss.

Phase B found reproducible semantic transfer through all three prespecified candidates, but no base-aggregated candidate met the frozen median `CRR >= 0.20` rule. `h_pre(t*)` was strongest: median BCR `2.4347`, positive on `24/24` bases, median CRR `0.1832`, and semantic/sham ratio `27.53`. `R_last1` had median BCR `0.8463`, CRR `0.0719`, and semantic/sham ratio `11.12`; Q had median BCR `0.1451`, CRR `0.0109`, and ratio `2.07`. All three effects were Holm-significant in the frozen 15-test family, but all failed only the magnitude threshold.

The result is highly target-dependent. For `h_pre`, Target A median CRR was `0.3226`, while Target B was `0.0205`. That heterogeneity prevents a clean pooled carrier claim. The recommendation prioritizes the strongest mechanistic lead; it does not retrospectively override the frozen classification.

## Frozen design and validation

- Model/condition: Qwen3-VL-4B-Thinking with the exact Stage 3C.4 A5000 protocol and seed 1234.
- Validation cohort: exact seven disjoint Stage 3C.4 validation bases.
- Primary cohort: exact 24 Stage 3C.3/3C.3-R/3C.4 primary bases; no exclusions.
- Targets: Target A at `E_d`, historical layer 29; Target B at `E_d-1`, historical layer 28.
- Source: exact attention-independent Stage 3B.7-R target ROI T.
- Phase-A intervention: remove `c_T(t_pre,l,h)=sum_j alpha(t_pre,l,h,j)V(l,h,j)` in FP32 after Attention and before `W_O`, leaving direct Q/K/V, probabilities, non-target contributions, and all other queries native.
- Frozen scopes: P0 28–29, P1 32–33, P2 28–33, P3 24–35, P4 16–35, P5 0–35.
- Phase-B cache carriers: post-RoPE K/V at exact R or Stage 3B.0 Q positions in the Phase-A-selected P4 layers. No visual or current-query K/V was replaced.
- Phase-B current-state carrier: raw `h_pre(t*)` at the frozen historical target layer with downstream computation rerun naturally.
- Patch directions: self O→O/C→C, semantic O→C/C→O, and both directions within O/O_sham and C/C_sham.

The Phase-A seven-base validation passed 12/12 checks; maximum FP32 partition error was `4.77e-7`. Phase-B validation passed 10/10 checks across 672 candidate-level patches. Self patches and deterministic repeats were token-exact, cache positions matched Stage 3B.0, and all outputs were finite.

## Phase A — necessary visual window at t_pre

Base-aggregated results were:

| Scope | Layers | Median evidence loss | Median retention | Positive bases |
|---|---|---:|---:|---:|
| P0 | 28–29 | 0.0292 | 0.9948 | 18/24 |
| P1 | 32–33 | 0.0200 | 0.9963 | 16/24 |
| P2 | 28–33 | 0.0631 | 0.9917 | 23/24 |
| P3 | 24–35 | 0.2412 | 0.9675 | 24/24 |
| P4 | 16–35 | 0.5172 | 0.9272 | 23/24 |
| P5 | 0–35 | 0.4979 | 0.9250 | 24/24 |

P4 was selected prospectively as the smallest passing scope with at least 80% of P5 median loss. P4 and P5 are not strictly monotonic in median effect, so P4 should be interpreted as a broad necessary window, not a uniquely minimal layer set.

The frozen baselines reproduced Stage 3C.4 exactly on all 48 target/base cells:

| Baseline | Median loss | Median retention |
|---|---:|---:|
| A1 current-only | 1.3096 | 0.8436 |
| A2 t_pre-only | 0.4979 | 0.9250 |
| A3 joint `[t_pre,t*]` | 2.4658 | 0.6515 |

The joint loss is larger than either isolated loss and is not treated as an additive unique fraction. Target A was more sensitive than Target B: P5 median retention `0.8971` versus `0.9649`.

## Phase B — state handoff

| Carrier | Median BCR | Positive bases | Median CRR | Median sham shift | Semantic/sham ratio | Frozen robust? |
|---|---:|---:|---:|---:|---:|---|
| R_last1 K/V | 0.8463 | 24/24 | 0.0719 | 0.0788 | 11.12 | No |
| Q K/V | 0.1451 | 21/24 | 0.0109 | 0.0620 | 2.07 | No |
| h_pre(t*) | 2.4347 | 24/24 | 0.1832 | 0.0795 | 27.53 | No |

The gated recent-reasoning family remained small: R_last2 median CRR `0.0749` and R_last4 `0.0810`. Relative to R_last1, the gains were only `0.0030` and `0.0091`, below the frozen `0.05` rule. Therefore the result is not classified as short recent-history accumulation.

Every self patch was exact. Sham edits used the same carrier patch mechanics and stayed much smaller than semantic transfer. This supports semantic sensitivity of the patches but does not imply a unique information fraction or a clean carrier.

## Target specificity and continuity

At the selected P4 `t_pre` window, median loss was `0.5172` for T, `-0.0208` for M, and `-0.0020` for I. T exceeded M and I on `23/24` bases in each comparison. All 48 rerun T scores exactly reproduced Phase A.

P4 suppression at `t_pre` produced median relative state deltas of `0.0732` at `h_pre(t*)` and `0.0729` after Attention. Native O/C `h_pre` states differed by median `0.2078`, compared with `0.0484` for paired shams. These are descriptive raw-state continuity measures; no probe or subspace was fitted.

## Prior retrieval phenotype overlap

The necessary P4 scope contains the historical layers 28–29, but Stage 3C.2 measurements at `t_pre` weakly predicted P4 causal loss: Spearman rho was `0.223` for QK cosine, `0.198` for target attention density, `0.129` for target alphaV, and `0.223` for candidate-sink release. None was significant (`p >= 0.29`). This is descriptive triangulation only. Candidate sink was not manipulated.

## Compute and artifacts

GPU work ran inside Slurm allocation 106936 on node04 with two NVIDIA RTX A5000 GPUs through tmux session 8. The maximum observed allocation was `9.53 GB` (`8.87 GiB`) and reservation `9.74 GB` (`9.07 GiB`). The slower shards took approximately 54 s for Phase A, 166 s for initial carrier scoring, 131 s for gated R scoring, and 26 s for controls after model load. Raw scores, state readouts, audits, statistics, and all 13 required figures are under `outputs/stage3c5/`.

## Scientific boundary

Stage 3C.5 establishes broad-depth target-ROI necessity at `t_pre` and partial semantic transfer through R, Q, and especially Target-A `h_pre`. It does not establish a clean universal carrier, a unique causal fraction, sink function, whole-history lifecycle, vision-encoder origin, multi-evidence refresh, failure mechanism, or discrete LOOK/THINK state.

Attention/QK/alphaV are secondary descriptive overlap measures. The behavioral evidence is the frozen evidence-preference change under source contribution deletion or state transfer.

## Recommendation

**GO — Current-Residual Mechanism**, for review only. `h_pre` is the strongest and most target-heterogeneous candidate, while R and Q recover little of the full semantic gap. A future plan should explain the Target-A current-residual effect and Target-B robustness without assuming one shared carrier. No follow-on experiment was started.

