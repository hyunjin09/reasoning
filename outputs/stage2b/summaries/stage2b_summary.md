# Stage 2B Summary

Technical acceptance: **PASS**. Project decision: **NO-GO**.

## Intervention

Across all Qwen3-VL language layers and heads, an additive mask blocked only generated-query → selected visual-ROI key edges during the frozen acquisition window. Model weights, visual embeddings, other visual keys, prompt keys, reasoning keys, and the KV cache were unchanged.

## Frozen pilot

Examples: `699, 739, 2799, 3044, 3764`.

Windows: 699: A=[583, 598], B=[561, 583]; 739: A=[190, 218], B=[218, 263]; 2799: A=[140, 211], B=[303, 349]; 3044: A=[593, 614], B=[614, 630]; 3764: A=[420, 475], B=[533, 627].

Target/irrelevant visual-token counts: 699: A=4/4, B=16/16; 739: A=6/6, B=20/20; 2799: A=6/6, B=15/15; 3044: A=12/12, B=6/6; 3764: A=20/20, B=42/42.

The local metric used 32 clean tokens beginning at each frozen window start; the intervention ended at the frozen window boundary. Free rollouts used the Stage 1 official Thinking protocol with seed 1234 and EOS as the normal stop.

## Smoke validation

The gated smoke test **passed** on `699`. Paired A6000 hook transparency was `True`; exact deterministic local replication was `True`; cached generation was `True`. The A5000 historical trace comparison is reported separately and is not used to infer hook invasiveness across hardware.

## Local clean-token effects

ΔNLL values are nats/token relative to the no-intervention baseline in the same window.

| Example | A@Awin | B@Awin | Irr@Awin | A@Bwin | B@Bwin | Irr@Bwin | Category |
|---|---:|---:|---:|---:|---:|---:|---|
| 699 | -0.0004 | 0.0027 | -0.0009 | 0.0030 | 0.0264 | -0.0046 | P5 |
| 739 | 0.0118 | 0.1161 | 0.0145 | 0.0030 | 0.0617 | -0.0012 | P4 |
| 2799 | -0.0002 | -0.0015 | 0.0004 | 0.0043 | -0.0021 | 0.0058 | P5 |
| 3044 | 0.0055 | 0.0034 | 0.0058 | 0.0018 | 0.0051 | -0.0007 | P5 |
| 3764 | 0.0174 | 0.0057 | 0.0135 | -0.0089 | 0.9463 | 0.0060 | P2 |

Strong crossover count: `0/5`; partial-specificity count: `1/5`; median target-minus-irrelevant margin: `0.0022` nats/token.

## Free-rollout behavior

All eight window-matched rollouts per example were persisted with full continuations, answers, correctness, lengths, first token divergence, and simple evidence-number mention diagnostics. A single matched stochastic seed makes these qualitative paired outcomes, not frequency estimates.

## Controls and limitations

Wrong-evidence controls mask the other frozen evidence ROI. Irrelevant controls are disjoint from A and B and match target token count within one token. For 3764/B, the 42-token target occupies a large fraction of the 105 visual tokens, so its disjoint exact-size control necessarily spans most remaining non-evidence locations and is a weak spatial control.

This five-example pilot tests causal dependence on the intervened attention edges. It does not by itself prove fresh visual evidence acquisition, visual-memory handoff, a LOOK/THINK state, or a dataset-wide mechanism. ROI-size and off-manifold masking effects remain alternative explanations.

## Decision

**NO-GO** under the frozen rule. Abandon attention-guided ROI causality as the main route and redesign the measurement strategy.

Stage 2B stops here. The recommendation has not been executed.
