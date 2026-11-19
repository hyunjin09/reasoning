# Stage 3B.3 — Layer-wise Visual-to-Reasoning Transfer Localization

Overall status: **STOPPED AT SMOKE GATE / TECHNICAL FAIL**

Decision: **REDESIGN**

## What was frozen

Before scoring, Stage 3B.3 froze the exact 49-base Stage 3A/3B.2 cohort, `E_d-1` and `E_d` coordinates, six 6-layer windows, cumulative lower-prefix and upper-suffix sets, six current-position residual boundaries, a two-layer refinement rule, and attention-independent selection. The validated RTX A5000 eager-attention path and seed 1234 were retained.

## Smoke execution

The mandatory three-numeric-base smoke used bases 118, 148, and 113.

- Slurm 106613 stopped on a mechanical runner error before any per-base result was saved: the residual scorer received the per-layer state dictionary rather than the selected boundary tensor.
- The indexing error was repaired without changing the scientific configuration.
- Slurm 106614 completed all three bases. Peak GPU allocation was 9,450,177,536 bytes.
- All-layer visual-source switching and no-switch scoring exactly reproduced Stage 3B.2, including candidate token log-probability arrays.
- Self replacement was exactly transparent across all tested layer sets.
- Layer/query boundaries, visual positions, nonvisual K/V invariance, restoration complements, current-position-only residual replacement, reciprocal sign conventions, finite scores, and cross-run determinism all passed.

Eleven of twelve smoke criteria passed. The prospectively frozen restoration sham criterion failed:

| Control | Sham/target ratio | Frozen maximum | Status |
|---|---:|---:|---|
| All-layer switching | 0.003517 | 0.25 | PASS |
| Selective coarse-window switching | 0.170285 | 0.25 | PASS |
| Coarse-window restoration | 0.314949 | 0.25 | **FAIL** |

The one allowed diagnostic found median absolute target restoration 0.134651 and median absolute sham restoration 0.042408. Thus the failure is not attributable only to division by an effectively zero target effect. Its mechanistic cause remains unknown.

## Scientific interpretation

The smoke confirms that the selective visual-source and current-position residual implementations are mechanically surgical and that the all-layer positive control remains exact. It does **not** validate the planned window-restoration intervention as sufficiently evidence-specific under the frozen sham gate.

No coarse cohort result, causal layer atlas, cumulative cohort curve, fine localization, exact-baseline cohort robustness result, or Stage 3B.3 mechanistic localization claim exists. Smoke target effects are validation evidence only.

## Stop decision

`plan/stage3b3_plan.md` requires stopping when smoke fails. Therefore the 49-base jobs were not submitted, the fine gate was not applied to cohort results, and none of the nine cohort figures was produced.

Attention was not used for candidate or window selection. No attention-vs-MLP, head/path, ROI-specific, Q/R-carrier, multi-evidence, failure-analysis, or later-stage experiment was started.

The required next decision is a reviewed redesign of the restoration sham/control protocol. That redesign is not authorized or executed here.
