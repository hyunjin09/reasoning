# Stage 3C.10 implementation and artifact review

Reviewed by the main agent under the repository's default single-agent workflow.
No independent-review trigger or strategic experiment selection was introduced.

- Scope: additive stage3c10 modules/scripts only. Historical scoring, manifests,
  target heads/ROIs and token annotations are imported/copied without mutation.
- Coordinates: tests cover one-based historical to zero-based current conversion,
  no current-token inclusion, no prompt spill, missing E16 and short early M.
- Arithmetic: a single-source deletion returns the inherited T0 result exactly;
  joint disjoint sources are computed from the same native alpha/V, removed in
  FP32 and written once in BF16. No attention renormalization occurs.
- Actual GPU mechanics: seven bases and517 arms pass15 gates, including exact
  native/no-op/self-Q, replay, old cached T0 semantics, current-only changes,
  FP32 partition tolerance and full-past cache equality at all 36 layers.
- Scientific inference: each base is one independent unit; original eight-test
  per-target Holm family retains unrun rescue slots at primary freeze. All
  primary formulas, Wilcoxon p values, Holm values, medians and positive counts
  independently recompute. B gates never loosen after mediation results.
- Follow-ups: all phase coverage and gates checked; R1 equals the independent
  position1 scan exactly. Q head scopes and native recipient K/V are verified;
  h_pre exact current-state copy is directly audited.
- Negative evidence: Q and h_pre do not robustly rescue VSD. Preserve O1/M2,
  not O2. Noncausal routing and generic language changes are reported. k80=16
  is threshold-adjacent and does not identify a unique 16-token span.
- Artifacts:21 independent artifact checks across412 files/5121 arms/207811
  source-layer calls, plus4 statistical/mediation crosschecks.45 tests pass.
- Figures: visually inspected temporal profile, VSD rescue and causal diagram.
  Diagram marks the late-Q behavioral mediation link unestablished while keeping
  the direct recent-state/VSD effect distinct. Sixteen PNG/PDF pairs produced.
- Repair: initial report formatter iterated target keys as records. Corrected to
  values; preserved `runs/stage3c10_report_finalization.log` and reran formatting
  only in `runs/stage3c10_report_finalization_v2.log`. No experiment rerun.

No unresolved implementation blocker. Scientific mediator remains unknown.
