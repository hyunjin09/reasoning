# Stage 3C.9R — Same-path validity repair

Technical **PASS**: 20/20 acceptance criteria; 15/15 mechanical gates. Scientific outcome **R1**.

The long-horizon sparse semantic-checkpoint hypothesis is not supported under the tested W8/W16 event-span assay.

On the unchanged 48-base, 144-event cohort, 33 events were source-sensitive in at least one frozen window. There were **10 distinct C2/C3 checkpoints** and **0/48 repeated-checkpoint bases**. Classes: {'C0': 111, 'C1': 23, 'C2': 9, 'C3': 1}.

## Frozen assay and repair

All 288 mechanically valid W8/W16 event-window pairs received native, suppressed, event-span rescue and equal-width neighbor rescue in O/O_sham/C/C_sham before classification (576 raw condition files). No cohort, span, ROI, candidate suffix or readout changed.

Each arm used BF16 eager language attention / SDPA vision attention with 2048-token maximum chunks, allocator release and the same union of frozen event/neighbor token-end barriers. Event and neighbor rescues fork exact cache copies from the actual suppressed execution. One persisted suppressed score supplies every source-loss and rescue-gain denominator. All sham source effects were also recomputed on this path. Original Stage 3C.9 scores enter descriptive comparisons only.

The original source directionality/sham criterion, reciprocal positive rescue, 0.05 mean effect floor, median unclipped RR >=0.25, matched-neighbor superiority, distinct-final C3 rule and >=24-token repeated-pair separation are unchanged.

## Primary and threshold results

The continuous profile contains 37 source-sensitive event-window pairs: 13 W8 and 24 W16. Of these, 26 do not pass the complete span-rescue rule. Descriptive high/low L/G quadrants are {'D': 182, 'B': 31, 'C': 26, 'A': 49}; quadrant membership alone does not establish a checkpoint.

| Effect floor | C2/C3 events | Repeated bases | Bases with 0 / 1 / 2 / 3 checkpoints |
|---:|---:|---:|---|
| 0.025 | 12 | 0/48 | 36 / 12 / 0 / 0 |
| 0.050 (primary) | 10 | 0/48 | 38 / 10 / 0 / 0 |
| 0.100 | 6 | 0/48 | 42 / 6 / 0 / 0 |
| 0.150 | 3 | 0/48 | 45 / 3 / 0 / 0 |

Sensitivity changes only the effect floor after the primary result freeze. Windows within an event never count as separate checkpoints. The combined C2/C3 counts are unaffected by final-readout upgrades. RR is descriptive and unclipped; a near-zero per-condition source loss can produce a very large ratio, so it is not a unique information fraction. Absolute source/rescue effects and their controls remain the primary evidence.

| Per-base statistic | Mean | Median | Bootstrap 95% CI for mean | Positive fraction |
|---|---:|---:|---|---:|
| source sensitive event count | 0.68750 | 0.00000 | [0.45833, 0.91667] | 0.479 |
| checkpoint count | 0.20833 | 0.00000 | [0.10417, 0.33333] | 0.208 |
| repeated checkpoint | 0.00000 | 0.00000 | [0.00000, 0.00000] | 0.000 |
| median source loss | 0.00132 | 0.00125 | [-0.01468, 0.01584] | 0.583 |
| median event rescue | -0.00115 | -0.00350 | [-0.01428, 0.01120] | 0.438 |
| median event minus neighbor | 0.00559 | 0.00448 | [-0.00550, 0.01721] | 0.604 |

The independent unit is base_problem_id. Each base contributes its event/window summary once; bootstrap sampling draws whole bases (10,000 draws, seed 12348). Event scatter plots are descriptive. A degenerate bootstrap CI for an all-zero count is an empirical resampling result and does not establish zero population prevalence.

## Numerical comparison with the original experiment

| Legacy path | Matched O/C cells | Median absolute source-loss difference | Gate agreement | Source-loss sign agreement |
|---|---:|---:|---:|---:|
| Phase A | 576 | 0.071071 | 232/288 | 0.516 |
| Phase B | 66 | 0.000000 | 29/33 | 1.000 |

Original Phase B was pre-gated and retained Phase-A sham effects. Its gate comparison therefore includes that legacy mismatch. The repair uses its own quartet scores throughout. Mechanical validation found exact native/self-suppressed controls, deterministic replay and inherited-path comparisons; threshold sensitivity describes scientific cutoff dependence, not replay randomness.

## Lifetime and frozen base-38 reference

Lifetime counts: {'L-Short': 5, 'RIGHT-CENSORED': 3, 'L-Persistent': 2}. A checkpoint with no distinct later/final readout is explicitly RIGHT-CENSORED. L-Short retains the original readout-based label; it does not establish a 16–32-token decay time when no probe exists there. L-Persistent uses the original mean-gain criterion at a distant or final probe; C3 additionally requires positive final rescue in both O and C, so those counts can differ.

| Base / event | Window | Local G | Distinct downstream observations: distance → G | Lifetime |
|---|---|---:|---|---|
| 78 / 24 | W16 | 0.124948 | 1315 → 0.000013 (final) | L-Short |
| 97 / 72 | W8 | 0.094199 | none | RIGHT-CENSORED |
| 97 / 72 | W16 | 0.113670 | none | RIGHT-CENSORED |
| 187 / 8 | W16 | 0.136570 | 390 → -0.015067 (final) | L-Short |
| 193 / 33 | W16 | 0.156251 | 7643 → 0.000000 (final) | L-Short |
| 672 / 0 | W16 | 0.312500 | 870 → 0.187500 (next); 2063 → 0.062500 (final) | L-Persistent |
| 189 / 51 | W8 | 0.125000 | none | RIGHT-CENSORED |
| 254 / 26 | W16 | 0.093750 | 3276 → -0.093750 (final) | L-Short |
| 38 / 0 | W16 | 0.186937 | 2342 → -0.031645 (next); 4715 → -0.093745 (final) | L-Short |
| 71 / 23 | W16 | 0.105136 | 2956 → 0.064869 (final) | L-Persistent |
| 129 / 4 | W16 | 0.187500 | none | RIGHT-CENSORED |

Base 38's frozen first event now classifies **C2**. Its same-path W8/W16 source losses are 0.094092 / 0.218551, and event gains are 0.093699 / 0.186937. Its survival was never a technical PASS condition.

Original base-38 local G was 0.186937; its independently annotated readout 2342 tokens later had G=0.030947, and final G=-0.093745. Full repair details are in [base38_reference.json](../analysis/base38_reference.json).

## Gates and interpretation

Optional necessity: NOT RUN; 3 robust events versus 4 required. Robustness was prospectively operationalized as retaining C2/C3 at 0.15. Route decomposition: **NOT RUN**; 0 eligible repeated bases versus 16 required.

Source-sensitive nonrescued windows establish local visual dependence without sufficient sparse-span rescue; distributed state, direct refresh and redundant carriage remain alternatives.

The assay tests frozen sparse semantic K/V spans under W8/W16. A negative result does not establish that visual processing or reasoning-side propagation is absent. Other acquisition windows, broader recent-token/residual state and semantic misalignment remain unresolved.

**Sole recommendation: GO — Retrieval Trigger.** This is for review only. Stage 3C.9R stops here; no cohort expansion, Retrieval Trigger, sink intervention or Stage 4 experiment was started.

## Execution and evidence

Used only the four user-provided A6000 GPUs in tmux 9 / Slurm 108548 on node07. No additional allocation was requested. Peak per-rank allocated/reserved GPU memory was 20.28/23.37 GiB. Commands, versions, timing and rank assignment are saved in the raw directories and [resource_summary.json](../audit/resource_summary.json).

The independent audit rederived all scientific gates from raw scores and verified 4751 immutable original artifact hashes. Focused regression evidence: `runs/stage3c9r_regression_tests.log`.

- [Acceptance](stage3c9r_acceptance.json)
- [Independent raw-score audit](../audit/independent_artifact_validation.json)
- [Primary freeze](../analysis/primary_freeze.json)
- [Continuous source/rescue profile](../analysis/source_vs_rescue_2d.json)
- [All 15 figures (PNG/PDF)](../analysis/figures/index.json)
