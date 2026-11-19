# Stage 3C.6 summary

## Result

Stage 3C.6 is a **technical PASS (20/20)** with primary scientific outcome **O4 — Residual Insufficiency** and one review-only recommendation:

> **GO — Prior-Cache / Two-Query Interaction**

This stage asked whether the actual evidence-preference deficit caused by deleting Target-ROI contribution at the preceding query (`t_pre=t*-1`) is recoverable from the native current-position residual at `t*`. It did not search for token-type carriers or manipulate the attention sink.

The exact Stage 3C.5 P4 suppression effect reproduced on all 48 target/base cells (maximum absolute score delta 0.0). Rescue was evaluated within O and C separately, with C sign-flipped only before within-base aggregation. Unnormalized rescue gain is primary; RR is descriptive, unclipped, and is not a unique causal fraction.

## Frozen design and validation

- Model/protocol: Qwen3-VL-4B-Thinking, exact Stage 3C.5 A5000 protocol, seed 1234.
- Cohorts: seven disjoint validation bases and 24 frozen primary base problems; no exclusions.
- Suppression: exact Stage 3C.5 P4 source-contribution deletion, layers 16–35, all 32 logical heads, Target ROI T, only at `t_pre`.
- Rescue: candidate-specific native `h_pre(t*)` patched into the matching suppressed-recipient continuation at one layer; all past-token and visual K/V remained recipient-native.
- Broad family: 36 `h_pre` layers per target, Holm-corrected separately for Target A and B.
- Detailed family: `h_pre`, `h_post_attn`, and `h_post_block` in each frozen four-layer gated region.
- Controls: M and I deficit/rescue at the frozen strongest target boundary. Optional O/C sham rescue was prospectively skipped.

Phase-A validation passed 14/14 checks across seven bases. Maximum FP32 partition error was 2.38e-07; boundary-equivalence error was 0. Phase-B validation passed 11/11 checks. The separate exact post-RoPE past-K/V replay audit reports status `PASS` and maximum absolute delta 0.0.

## Phase A — broad current-residual rescue

| Target | Median P4 suppression loss | Positive bases | First RR≥.20 | First RR≥.50 | First RR≥.80 | Peak RR layer/value | Frozen profile |
|---|---:|---:|---:|---:|---:|---:|---|
| Target A | 0.5528 | 24/24 | 34 | None | None | L35 / 0.6035 | R3_late_only_rescue |
| Target B | 0.3035 | 22/24 | 35 | None | None | L35 / 0.3410 | R3_late_only_rescue |

A threshold crossing requires the median RR threshold, a bootstrap mean-gain CI strictly above zero, at least 18/24 positive base effects, and a Holm-adjusted one-sided p-value below .05 in that target's 36-layer family. A/B results are not pooled.

The semantic conditions are also retained separately before within-base averaging:

| Target | Condition | Median sign-aligned P4 loss | Positive bases | Bootstrap mean CI95 |
|---|---|---:|---:|---|
| Target A | O | 0.5339 | 23/24 | [0.49843009634699387, 0.9942053979970763] |
| Target A | C | 0.5050 | 24/24 | [0.4701301497412537, 0.7831800815581998] |
| Target B | O | 0.3271 | 21/24 | [0.23315755154363668, 0.6362330577127893] |
| Target B | C | 0.2188 | 22/24 | [0.1821569050800626, 0.4010823462561937] |

## Phase B — gated within-block decomposition

| Target | Frozen region | Strongest confirmed boundary | Median gain | Median RR | Boundary outcome |
|---|---|---|---:|---:|---|
| Target A | [31, 32, 33, 34] | L33 h_post_attn | 0.2014 | 0.4162 | B_Upstream_state |

Phase B was gated entirely from the frozen Phase-A tables. Neither boundary outcomes nor controls influenced the region choice.
Target B crossed the robust RR 0.20 threshold only at layer 35, but the deterministic four-layer selection rule found no qualifying region; no Target-B Phase-B scores were run.

At the selected boundary, the condition-specific effects were:

| Target | Condition | Median sign-aligned gain | Median unclipped RR |
|---|---|---:|---:|
| Target A | O | 0.1751 | 0.3328 |
| Target A | C | 0.2083 | 0.4121 |

## Dose and target-specificity controls

| Target | T rescue gain | M rescue gain | I rescue gain |
|---|---:|---:|---:|
| Target A | 0.2014 | -0.0018 | -0.0000 |

| Target | Dose-slope median | Positive bases | Bootstrap mean CI95 |
|---|---:|---:|---|
| Target A | 0.1712 | 22/24 | [0.010440696627691358, 0.3554039952586211] |

The dose arm interpolated only the frozen current-position residual difference. Lambda zero exactly reproduced the suppressed state. Control comparisons are target-specificity diagnostics, not selectors.

## Relation to Stage 3C.5

| Target | Stage 3C.5 semantic h_pre CRR | Stage 3C.6 suppression-rescue RR | Per-base Spearman rho |
|---|---:|---:|---:|
| Target A | 0.3226 | 0.4162 | 0.13565217391304346 |

Cross-image semantic transfer and within-condition suppression rescue answer different causal questions. Their ratios therefore should not be equated.

## Compute and artifacts

GPU work ran inside Slurm allocation 106936 on node04 with two NVIDIA RTX A5000 GPUs through tmux session/window 8. Maximum observed allocation was 9,399,767,552 bytes (8.75 GiB), and maximum reservation was 9,533,652,992 bytes (8.88 GiB). The complete Stage 3C.6 artifact tree occupies 1.10 GiB.

## Scientific boundary

Stage 3C.6 establishes whether, where, and at which current-token block boundary the behaviorally necessary consequence of preceding-query Target-ROI contribution is recoverable from `h(t*)`. It does not identify a token-type carrier, a unique information fraction, the upstream retrieval trigger, attention-sink function, whole-history lifecycle, a vision-encoder origin, multi-evidence refresh, or failure mechanisms.

Attention/QK/alphaV overlap analyses are secondary and descriptive. No attention-guided cohort or rescue-region selection occurred.

## Artifacts and recommendation

All raw scores, candidate-specific FP32 residual tensors, audits, per-base tables, aggregate statistics, controls, secondary comparisons, and 14 required figures are under `outputs/stage3c6/`. Independent artifact validation: **PASS 20/20**.

The sole review-only recommendation is **GO — Prior-Cache / Two-Query Interaction**. No follow-on experiment was started.
