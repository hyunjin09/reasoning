# Stage 3B.4 — Restoration-Controlled Module Localization

## Decision

Technical status: **PASS (16/16)**.

Scientific recommendation: **REDIRECT — Distributed block computation**.

Full-block restoration was robust in all four fixed coordinate/window cells, but none of the prospectively defined Attention-dominant, MLP-dominant, or Attention→MLP-cascade rules passed in at least two cells. This is a redirect for review, not evidence that one uniquely identified distributed mechanism has been established.

## Cohort and validation

The primary inference contains 37 unique numeric-label `base_problem_id`s with complete paired `O/O_sham/C/C_sham` controls. Four structural bases remain in the frozen 41-base cohort manifest but were not substituted into an uncontrolled analysis because no matched `C_sham` exists.

Before primary scoring, eight disjoint A5000 validation bases passed every frozen gate:

- exact Stage 3B.3-R token-log-probability reproduction;
- exact capture and current-position patch audits;
- exact O and C self restoration;
- finite outputs and exact end-to-end deterministic replication;
- full-block activity and bidirectional source consistency in 8/8 bases;
- median full-block render/semantic ratio 0.02151 and render/all-layer ratio 0.01206;
- pooled all-module render/all-layer ratio 0.00647.

## Primary result

All 592 expected rows were recovered: 37 bases × 2 coordinates × 2 retained windows × 4 modules. Baselines reproduced exactly, self restoration was exactly transparent, all patch audits were valid, and all scores were finite.

Median unnormalized paired semantic module restoration (BMR) was:

| Coordinate | Window | Attention | MLP | Joint | Block |
|---|---:|---:|---:|---:|---:|
| `E_d-1` | W4/F28_29 | 0.467 | 0.071 | 0.551 | 0.997 |
| `E_d-1` | W5/F32_33 | 0.141 | 0.191 | 0.381 | 1.372 |
| `E_d` | W4/F28_29 | 1.967 | 0.211 | 3.063 | 6.064 |
| `E_d` | W5/F32_33 | 1.314 | 1.406 | 4.059 | 9.173 |

Fourteen of 16 cells met the frozen robustness rule after Holm correction. The two exceptions were MLP/W4: at `E_d-1`, render/semantic was 0.545; at `E_d`, bidirectional consistency was 0.568 and render/semantic was 0.273. These failures are retained rather than relaxed post hoc.

Despite many positive component effects, their block-relative magnitudes did not meet the attribution rules. Median Attention/Block ratios ranged from 0.137 to 0.411, MLP/Block from 0.040 to 0.143, and Joint/Block from 0.329 to 0.539. The frozen dominance threshold was 0.50 for a single module and 0.70 for joint restoration. Therefore no Attention, MLP, or cascade category passed in two cells, while Block was robust in 4/4.

Restoration was stronger at `E_d` than `E_d-1` for every module/window contrast; all eight bootstrap median-difference intervals were above zero. At `E_d`, W5 exceeded W4 clearly for MLP, Joint, and Block, while the Attention W5-minus-W4 interval included zero.

## Interpretation and limits

The result supports a narrow statement: under paired semantic restoration at the current token, neither isolated Attention output nor isolated MLP output, nor their joint output replacement, accounts for the robust full-block effect at the prespecified level. This is consistent with distributed or sequential block computation, but could also reflect normalization/residual interactions, cross-layer dependence, or non-additivity of the restoration surfaces.

This stage does not identify attention heads, a visual ROI or path, Q/R carriers, LOOK/THINK states, multi-evidence refresh, or failure mechanisms. Attention magnitude was not used for selection, and the optional attention-moderator and necessity analyses were not run.

Complete statistics and nine reviewed figures are under `outputs/stage3b4/analysis/`. No later experiment was started.
