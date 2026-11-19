# Stage12Y-S Thinking role decomposition

Decision: **ROLE_DECOMPOSITION_UNRESOLVED**.
Confirmed role signals: access=False; equal-evidence reasoning=False; state construction=False.

Exact Stage12X-S source-frozen96 reused. This is a paired role-decomposition study, not a new held-out replication. Instruct historical single runs remain screens; all confirmatory calls use fresh frozen seeds.

| Screen arm | Correct / scoreable | Technical missing |
|---|---:|---:|
| E_I | 37/94 | 2 |
| E_T | 43/96 | 0 |
| I_img | 45/87 | 9 |
| T_img | 54/96 | 0 |
| I_E | 61/93 | 3 |
| T_E | 76/96 | 0 |

| Paired descriptive contrast | Estimate | Family bootstrap95% | Common families |
|---|---:|---|---:|
| G_img | 0.034482758620689655 | [-0.05747126436781609, 0.12643678160919541] | 87 |
| G_E | 0.13978494623655913 | [0.06451612903225806, 0.22580645161290322] | 93 |
| G_access | 0.05319148936170213 | [-0.031914893617021274, 0.13829787234042554] | 94 |
| A_evidence | -0.08139534883720931 | [-0.19767441860465115, 0.03488372093023256] | 86 |

Attenuation uses the common four-task denominator; pair-specific gaps can have different denominators. These are descriptive contrasts, not formal causal mediation.
Native Thinking-only transitions: {"A_COLLAPSE": 5, "B_PERSIST": 2, "C_BOTH_FAIL": 2}.

| Fresh confirmation | Supported / frozen candidates | Unresolved |
|---|---:|---:|
| Access | 1/5 | 0 |
| Equal-evidence downstream | 8/15 | 1 |

Phase C: COMPLETE; 2/8 state-construction support; 6 families with resolved baseline/shuffle controls. All source/replay inputs are identical Q+E* without images; first successful source replicate and maximal answer-safe prefix were frozen before replay.

Majorities use2/3 in confirmation and3/5 in replay. Missing runs remain unknown if they can change a majority. All-seed counts, exact descriptive family intervals and missingness bounds are retained. No best-of selection or seed/prefix search.

Evidence-probe success requires every frozen atom and structured subfield. E− denotes incomplete or incorrect demonstrated reporting, not absent latent visual access. Historical E_I used256tokens; new Instruct probes use the plan's32768-token recipe; Thinking81920. Model checkpoints/recipes/budgets differ, so no pure Thinking-switch inference is justified.

Arm-separated scoring and ambiguity/random second passes were conducted by the same agent, not independent human raters. Source-eligible MathVision families do not establish benchmark-wide or other-domain prevalence. Text portability does not identify the complete neural mechanism.

Resources: 640 new calls; 10.915 allocated GPU-hours (hard16). All jobs released. 11478 historical files and source/QC seals verified unchanged. Five PNG/PDF figure pairs saved under figures/.

Exactly one recommendation: Stop role-mechanism expansion and retain the narrower supported claims about evidence bottlenecks and developmental state portability.

STOP. Recommendation not launched.
