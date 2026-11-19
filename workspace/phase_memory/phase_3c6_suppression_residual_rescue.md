# Phase 3C.6: Suppression-to-Residual Rescue

## Current Objective

Execute the user-approved `plan/stage3c6_plan.md` as one bounded causal action: reproduce the exact Stage 3C.5 P4 `t_pre` deficit, scan all 36 current-position `h_pre(t*)` boundaries for within-condition native-state rescue, run only prospectively gated within-block/dose/control analyses, issue one recommendation, and stop.

## Active Constraints

- Preserve Stage 0--3C.5 artifacts and reuse the exact 7/24 validation/primary split, Target A/B coordinates, T/M/I ROIs, P4 layers 16--35, all logical heads, seed 1234, and A5000 runtime.
- Primary comparisons are within O and within C. Sign-align C so positive always means preference for that condition's native fact; report O and C separately before averaging them within each base.
- Patch only the current position at `t*`; leave the suppressed recipient's past-token K/V and visual K/V native. Use unnormalized rescue gain as primary and leave rescue ratios unclipped.
- Scan all 36 `h_pre` layers. Phase B is independently gated per target and uses the prospectively frozen candidate-region rule; M/I controls cannot select a layer.
- Do not run token-type carriers, sink manipulation, earlier-history search, learned residual features/subspaces, Stage 4, multi-evidence refresh, or failure analysis.

## Current State

- Done: Stage 3C.6 completed on the exact 7/24 validation/primary split and passed all 20 technical acceptance criteria plus 20/20 independent artifact checks.
- Done: exact Stage 3C.5 P4 scores reproduced on 48/48 target/base cells; all 36 `h_pre` layers were scanned separately for Target A and B.
- Done: Target-A-only Phase B, dose, and M/I controls ran after the frozen gate and four-layer region selection; Target B had no valid four-layer region.
- Blocked: none.
- Most recent useful observation: rescue was late and incomplete. Target A first robustly crossed RR 0.20 at layer 34 and Target B at layer 35; neither reached a robust RR 0.50 crossing.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| P4 target-ROI deficit | `outputs/stage3c5/analysis/necessary_window_analysis.json` | Defines the exact deficit that Stage 3C.6 must reproduce and rescue | confirmed |
| Current-residual heterogeneity | `outputs/stage3c5/analysis/target_heterogeneity.json` | Requires separate Target A/B gates and interpretations | confirmed |
| Contribution mechanics | `code/visual_reasoning/stage3c4/runtime.py` | Supplies validated FP32 source-contribution suppression | confirmed |
| Boundary mechanics | `code/visual_reasoning/stage3b5/boundaries.py` | Supplies exact current-position boundary capture/patch behavior | confirmed |
| Frozen cohort and ROIs | `outputs/stage3c5/cohort/`; `outputs/stage3c5/config/frozen_targets.json` | Prevents outcome- or attention-guided reselection | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Stage 3C.3-R v1 bookkeeping | BF16 endpoint/partition drift | supported | retain FP32 contribution bookkeeping and exact endpoints | do not reintroduce BF16 contribution arithmetic |
| Stage 3C.5 semantic carrier search | all tested carriers significant but pooled CRR remained below 0.20 | confirmed | rescue the demonstrated within-condition suppression deficit directly | do not infer mediation from cross-image semantic patching alone |
| Stage 3C.6 first smoke launch | a newly created tmux window reported no CUDA before model load | supported: new window was outside allocation; allocation-backed pane uses `srun --jobid=106936 --overlap` | launch unchanged work through an overlapping Slurm step from the existing pane | do not assume new tmux windows inherit the Slurm device context |
| Stage 3C.6 allocation-backed smoke setup | validation base 141 was absent from the primary-only Stage 3C.5 raw resolver | supported by exact raw path; validation data are under `raw/phase_a_validation` | resolve prior reproduction from the disjoint primary or validation family and regression-test it | do not assume validation bases live in the primary raw family |
| Stage 3C.6 validation reproduction lookup | Stage 3C.5 validation stored only P0/P5, not P4 | supported by direct validation/primary schema comparison | validation reproduces all historically available scores; exact P4 reproduction remains mandatory on the primary cohort before analysis | do not require a historical arm that the source validation protocol never ran |
| Stage 3C.6 first seven-base validation audit | 12/14 checks passed; candidate h_pre states were not always bit-identical across differently sized candidate suffix forwards, and residual width was 2560 rather than validator-assumed 3584 | supported by direct tensor inspection | retain and patch candidate-specific donors separately and derive layout from the frozen model width | do not collapse candidate states or hard-code an unverified residual width |
| Stage 3C.6 first primary aggregation | SciPy returned a non-finite one-sided Wilcoxon p-value for an all-zero rescue vector, so Holm correction stopped before any gate was written | supported by the all-zero layer vector and a failing regression test | map an exactly all-zero signed-effect vector to null evidence (`p=1`) before multiplicity correction | do not pass non-finite p-values into Holm correction |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Progressive current-residual integration | broad `t_pre` acquisition may enter `t*` residual across depth | 36-layer `h_pre` rescue curve | not supported under the frozen robust-crossing rule |
| Boundary-specific integration | prior semantic restoration implicated Attention boundaries | gated `h_pre`/`h_post_attn`/`h_post_block` scan | not supported; no transition increment was robust |
| Residual insufficiency/transience | suppressed prior-token state may reintroduce the deficit | late-layer rescue and downstream decay | supported as O4 residual insufficiency |
| Target-heterogeneous handoff | Stage 3C.5 Target A/B differed sharply | separate target gates and statistics | retained descriptively; only Target A had a valid detailed region |

## Next-Step Decision

- Current bottleneck: current-position residual state recovers only a late, incomplete portion of the actual P4 `t_pre` deficit; the remaining dependence could involve suppressed prior caches or a distributed two-query interaction.
- Relevant memory item used: Target-A/Target-B first robust RR 0.20 crossings occur only at layers 34/35, with no robust RR 0.50 crossing; Target A has target-specific, dose-responsive rescue at L33 `h_post_attn` but no robust within-block transition increment.
- Chosen next action: none. Stage 3C.6 is complete and stopped for review.
- Review-only recommendation: **GO — Prior-Cache / Two-Query Interaction** under the prospectively frozen decision rule.
- What not to repeat: do not equate the late Target-A rescue with full current-residual mediation, infer a unique residual fraction from RR, or use attention to choose a cache interaction.
- Stop condition: satisfied. No token-type, sink, prior-cache, Stage 4, multi-evidence, or failure experiment has started.

### Prospectively Frozen Quantitative Rules

- Primary unit: `base_problem_id`; O and C are sign-aligned and averaged within base only after separate reporting.
- Broad family: 36 one-sided `G(l)>0` Wilcoxon tests per target with Holm correction; bootstrap mean CI uses 10,000 base resamples and seed 20260904.
- Robust layer: Holm `p<0.05`, bootstrap mean CI lower bound `>0`, and at least 18/24 positive base gains.
- Thresholds: first robust layer with median unclipped RR at least 0.20/0.50/0.80.
- Phase-B target gate: at least one robust layer with median RR at least 0.20.
- Candidate region: among contiguous four-layer windows containing at least one adjacent pair of Holm-significant positive layers, choose the window with the largest positive adjacent-layer median-rescue slope; break ties by earliest start. If none exists, do not run that target.
- Phase-B families: all 12 layer×boundary rescue tests in the frozen four-layer region form the primary Holm family per target; four Attention and four MLP transition increments form a separate secondary eight-test Holm family per target.
- Dose: if a target passes Phase B, run lambda 0/0.25/0.50/0.75/1 at its strongest confirmed boundary; do not extrapolate. Optional O/C sham reruns are prospectively omitted.
- Recommendation: call residual rescue strong if at least one target has a robust first_50 crossing; call it broad if a strong target has at least eight robust layers with median RR at least 0.50. Strong+broad selects Residual Feature/Subspace; strong but not broad selects Token-Type Atlas; absent or transient strong rescue selects Prior-Cache/Two-Query. Sink is not selected while residual/cache ambiguity remains.

### Step Result

- Action taken: exact P4 deficit reproduction; 36-layer within-condition current-residual rescue; gated Target-A boundary/dose/control analysis; frozen classification and independent validation.
- Result: technical PASS 20/20 and independent artifact PASS 20/20. Scientific outcome **O4 — Residual Insufficiency**.
- Evidence saved: `outputs/stage3c6/`, especially `phase_a_hpre_scan/threshold_crossings.json`, `phase_b_boundary/boundary_statistics.json`, `controls/control_statistics.json`, `analysis/current_residual_classification.json`, and `summaries/stage3c6_summary.md`.
- Failure or issue: two validation assumptions were corrected before primary scoring; the first primary aggregation hit an all-zero Wilcoxon edge case and was repaired before any gate was produced. Raw GPU scores were unchanged.
- Lesson learned: the actual preceding-query causal deficit becomes partly recoverable only at very late current-token residual boundaries; current residual alone does not robustly recover half the deficit on either target. Target-A rescue is target-specific and dose-responsive, but no within-block transition increment is robust.
- Next implication: the sole review-only recommendation is **GO — Prior-Cache / Two-Query Interaction**. It is not authorized for execution; Stage 3C.6 stops here.
