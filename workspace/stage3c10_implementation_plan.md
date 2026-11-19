# Stage 3C.10 execution

User-authorized plan: `plan/stage3c10_retrieval_trigger_plan.md`. Reuse only
Slurm 108548 / tmux 9 / node07 / four A6000 GPUs; no allocation requests.

1. Freeze exact Stage 3C.3 7/24 manifests, M/T coordinates, RDS implementation,
   historical question-text Q group, ROI groups, statistical family and paths.
2. Implement/test current-query-only source deletion with simultaneous disjoint
   trigger/ROI subtraction, cached routing capture, same-state native-Q rescue.
3. Validate all seven bases, both states/targets: exact no-op/replay, past-cache
   invariance, native recipient K/V under Q rescue, isolated T0 semantics,
   FP32 partition <= 1e-5. Stop for any validity failure before primary.
4. Score all 24 bases: N/R16/E16/Q crossed with no/target/irrelevant suppression,
   M and T separately. Freeze primary results before follow-up gates.
5. Temporal localization if routing OR VSD robust; layers only if complete
   behavioral trigger gate passes. All-head and historical-head Q rescue at T
   for both targets; optional h_pre only for strong VSD with routing-only rescue.
6. After primary freeze, annotate last16 and scan last8 per-position M/T;
   analyze distance before token type. No attention selection or sink mutation.
7. Validate artifacts, produce 16 figures, assessment, one recommendation, update
   compact memory and stop. No broader-history search, new cohort or Stage 4.

Prospective operational details (before any Stage 3C.10 scores):
- Historical state indices are one-based counts; current zero-based index=t-1.
  Rk is the intersection of the preceding k positions with generated history;
  retain and flag short R16 at early M. E16 requires all32 predecessors.
- Q is the inherited exact question-content span, excluding structural tokens.
- Use one common per-base partition with barriers before/after every frozen M/T
  query, max2048, all arms/bridges/candidate scores identical. Current query is
  a single-token step. Score historical divergent suffixes at E_d on O images.
- Reuse `summarize_routing_state` unchanged; primary RDS_T_vs_M on causal heads.
- All36 layers/32heads T0 uses inherited contribution arithmetic. Joint disjoint
  sources each evaluated from native alpha/V and subtracted together in FP32
  with one BF16 write. No renormalization, cache replacement, or sink deletion.
- Per-target eight-test Holm family, two-sided Wilcoxon, 10k base bootstrap seed
  12348; unrun rescue slots p=1 for primary gating. Robust positive: corrected
  p<.05, mean CI lower>0, positive fraction>=.75, median>0. Complete trigger
  requires first five contrasts robust; R16-vs-Q comparison remains separately
  visible and cannot be used to hide prompt dominance. E16 uses available paired
  bases only, explicit denominator, no substituted window.
- Prompt dominance: robust Q T-VSD plus robust Q-minus-R16 effect under same
  fixed family and median Q effect >=1.5 times positive R16 median (or R16<=0).
- Q rescue is ungated in the plan and runs for both targets. Strong rescue uses
  same robust-positive criteria; report unnormalized gains and unclipped ratios.
  Optional h_pre requires primary R16 VSD robust, Q routing rescue robust, and
  Q VSD rescue not robust. B/C/D gates stay frozen from pre-mediation analysis.
- Phase F has only the post-primary-freeze gate; run all retained bases/states,
  at most8 available positions. Type comparisons are descriptive distance-matched
  within target/state/distance, aggregated once per base; no universal-type claim.
- No local research-control SKILL.md exists (prior scoped search); explicit plan
  supplies the selected bounded action. Single main agent, no delegated review.
