# Stage 3C.9R implementation and execution

Authorized by the user on 2026-09-06: execute `plan/stage3c9r_plan.md` using
only the four GPUs already in tmux 9. Live allocation: Slurm 108548, node07;
108085 is historical. No new Slurm allocation will be requested.

## Fixed implementation choices before scores

- Copy the 48 primary and eight validation manifests byte for byte and hash
  their referenced tokens, edits, images, ROI mappings and original artifacts.
- Reuse BF16 eager language attention, SDPA vision attention, seed 1234,
  calibration-v2 P2 streaming, chunk maximum 2048 and allocator release.
- Use the original Phase-B union of every event/neighbor token-end boundary
  for **all** conditions, including O_sham/C_sham. This union is determined
  only by frozen coordinates. No constituent-token experiment is added.
- Compute native and suppressed trajectories once per event/window/condition.
  Save exact CPU copies of cache states at the event and neighbor patch ends;
  each rescue forks the corresponding saved suppressed execution. CPU copies
  preserve BF16 tensors exactly and bound GPU memory; no model computation,
  dtype conversion, or alternative query partition is introduced by copying.
- Use a single persisted suppressed score as the denominator for source loss,
  event rescue and neighbor rescue. All four image conditions receive all arms.
- Validate all three events on every validation base, including actual tensor
  invariance, native/native and suppressed/suppressed controls, deterministic
  replay, and equivalence to the inherited streaming implementation.
- Score all mechanically valid W8/W16 pairs on all 144 primary events before
  classification. The sham gate and C0-C3 rules are imported unchanged.
- Freeze primary local checkpoint classification before the sensitivity grid.
  Score distinct final and next annotated downstream readouts for confirmed
  checkpoints. C3 upgrades do not alter checkpoint or repeated counts.
- RIGHT-CENSORED requires no distinct later readout. Preserve original lifetime
  labels elsewhere with explicit observed distances/interval uncertainty;
  a distant failed readout does not identify a 16-32-token decay time.
- Define optional necessity's "robust" gate prospectively as at least four
  unique C2/C3 events that also pass at the strictest frozen floor 0.15. Run
  the inverse cache patch on those events only if that gate passes. This
  operationalizes the plan's otherwise unspecified robustness qualifier.
- Preserve the >=16 repeated-base route gate; no route scoring below it.
- Report base-clustered uncertainty, all 15 figures, exactly one recommendation,
  independent raw-score acceptance checks, and stop. No follow-on experiment.

## Slices and verification

1. Freeze inputs and implement tested shared-path scoring/cache forks.
2. Run eight-base mechanical validation across all four allocated GPUs.
3. Run complete frozen primary scoring; classify from new scores only.
4. Run gated lifetime/necessity/routes, summarize and audit artifacts.
5. Update phase memory/dashboard/environment and return the complete result.

The project-local research-control skill remains absent. This is execution of
an explicit, fully specified approved validity repair, not selection of a new
research direction. No independent research reviewer is required. The checkout
has no `.git`; changes remain additive and original Stage 3C.9 code/artifacts
are preserved. Regression tests live in the allowed `scripts/stage3c9r/tests/`.
