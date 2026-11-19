# Stage 3B.9 — Distributed Value Geometry

## Outcome

Stage 3B.9 technical status is **PASS**. The frozen joint classification is **G1 — Shared higher-dimensional**. Final recommendation: **GO — Multi-Evidence Causal Refresh**.

This stage asks whether the already-established late-W4 ROI→Value→head mechanism is shared at higher rank, compact only within a problem, a shared/private mixture, or distributed at both tested scales. Ratios are unclipped causal restoration ratios, not additive information fractions.

## Frozen design

- Target A: `E_d / W4 / layer 29 / heads [11,6,15,12]`.
- Target B-R: `E_d-1 / W4 / layer 28 / heads [16,0,3,6]`.
- Representation: exact Stage 3B.8 v3, 512D selected-head pre-`W_O` eager-Attention recomposition effect vector.
- Shared bases were fit only on the 57 historical Stage 3B.8 bases; all fresh bases were excluded.
- Frozen shared ranks: `1,2,4,8,16,24,32,48`; local ranks: `1,2,3`; 100 random controls per target/rank.

## Prospective cohorts

- Locked generation initially produced 44 correct and 31 wrong Phase-A/Phase-B outcomes combined; the blind gate-repair expansion added 5 correct and 2 wrong, with no truncation/invalid trace.
- Phase A froze 24/32 both-target-applicable fresh bases; N=24 is disjoint from every historical/protected base and Phase B.
- Phase B froze 15 separate five-value bases; usable full-V bases are 14 for Target A and 14 for Target B-R.
- All strict-E_d, edit, ROI, value, and applicability decisions were frozen without attention or projected-rank outcomes.

## Phase A — fresh shared-rank confirmation

| Target | rank | learned BVR | median SR | median CR | sham BVR | learned random percentile | bidirectional | passes all |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| target_a | 1 | 0.0474 | 0.0889 | 0.8312 | 0.0106 | 1.0000 | 0.4583 | False |
| target_a | 2 | 0.0757 | 0.1913 | 0.7509 | 0.0224 | 1.0000 | 0.7083 | False |
| target_a | 4 | 0.1450 | 0.4476 | 0.4037 | 0.0312 | 1.0000 | 0.8333 | False |
| target_a | 8 | 0.2970 | 0.7252 | 0.1792 | 0.0586 | 1.0000 | 1.0000 | False |
| target_a | 16 | 0.3369 | 0.7949 | 0.1222 | 0.1027 | 1.0000 | 1.0000 | False |
| target_a | 24 | 0.3522 | 0.8108 | 0.0599 | 0.1342 | 1.0000 | 1.0000 | True |
| target_a | 32 | 0.4257 | 0.9629 | 0.0855 | 0.1729 | 1.0000 | 1.0000 | True |
| target_a | 48 | 0.4818 | 1.0139 | 0.0428 | 0.2355 | 1.0000 | 1.0000 | True |
| target_b_r | 1 | 0.0195 | 0.0885 | 0.8865 | -0.0001 | 1.0000 | 0.4583 | False |
| target_b_r | 2 | 0.0375 | 0.2794 | 0.6986 | 0.0148 | 1.0000 | 0.5833 | False |
| target_b_r | 4 | 0.0500 | 0.2897 | 0.5398 | 0.0155 | 1.0000 | 0.5833 | False |
| target_b_r | 8 | 0.0967 | 0.6352 | 0.4773 | 0.0339 | 1.0000 | 0.9167 | False |
| target_b_r | 16 | 0.1384 | 0.8829 | 0.2210 | 0.0497 | 1.0000 | 1.0000 | True |
| target_b_r | 24 | 0.1413 | 0.8916 | 0.1636 | 0.0565 | 1.0000 | 0.9583 | True |
| target_b_r | 32 | 0.1341 | 0.8781 | 0.0579 | 0.0733 | 1.0000 | 0.9583 | True |
| target_b_r | 48 | 0.1289 | 0.8782 | 0.0652 | 0.0950 | 1.0000 | 0.9583 | True |

A shared geometry is supported only at the smallest rank satisfying all six prospectively frozen checks; no passing rank is upgraded post hoc.

## Phase B — held-out within-problem geometry

| Target | local rank | eligible bases | local BVR | Local SR | Local CR | matched-global SR | local random percentile | bidirectional | passes all |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| target_a | 1 | 14 | 0.2078 | 0.3650 | 0.4624 | 0.0266 | 1.0000 | 0.7976 | False |
| target_a | 2 | 14 | 0.1842 | 0.3772 | 0.4189 | 0.1035 | 1.0000 | 0.8333 | False |
| target_a | 3 | 14 | 0.1915 | 0.3811 | 0.4448 | 0.1183 | 1.0000 | 0.8155 | False |
| target_b_r | 1 | 14 | 0.0810 | 0.4257 | 0.6125 | 0.0877 | 1.0000 | 0.8036 | False |
| target_b_r | 2 | 14 | 0.0836 | 0.4699 | 0.4636 | 0.2525 | 1.0000 | 0.8214 | False |
| target_b_r | 3 | 14 | 0.0750 | 0.4778 | 0.4557 | 0.1397 | 1.0000 | 0.8155 | False |

Each fold learns from three alternative semantic values and tests the fourth; folds are aggregated within base before dataset-level statistics. Rank 3 is reported but cannot establish the frozen strong compact-code criterion.

## Joint interpretation

- `target_a`: Shared-Moderate-Dimensional; shared `k_shared`=`24`, local rank-1/2 pass=`False`.
- `target_b_r`: Shared-Moderate-Dimensional; shared `k_shared`=`16`, local rank-1/2 pass=`False`.

Joint outcome: **G1 — Shared higher-dimensional**. Target-specific differences are retained rather than hidden by pooling.

## Secondary diagnostics

Pairwise rank-2 principal angles/projector similarities and frozen format strata were computed only after both primary analyses existed. Clustering was not used for a causal mixture claim. Attention was analyzed only as a post-freeze descriptor; it did not select bases, ranks, values, or the geometry label.

## Scientific boundaries and limitations

- Full-V applicability enriches the primary analyses for bases where the tested pathway has an interpretable positive bidirectional effect.
- SR/CR can be unstable when full effects are small; unnormalized BVR and per-base distributions are preserved.
- Geometry is conditional on two frozen late-W4 targets, one model, localized numeric labels, and MathVerse Vision-Dominant problems.
- Shared bases are linear; failure does not rule out nonlinear or context-conditioned structure.
- Raw attention is descriptive and is not causal visual usage.
- No vision-encoder, projector-feature, MLP, Q/R lifecycle, failure, or multi-evidence experiment was started.

Stage 3B.9 stops here.
