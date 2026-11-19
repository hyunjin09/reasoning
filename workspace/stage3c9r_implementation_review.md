# Stage 3C.9R implementation review

Review of the additive repair against `plan/stage3c9r_plan.md`.

- Correctness: source and both rescue effects share one persisted suppressed
  score. Both rescue branches start from exact cache copies captured during
  that suppressed execution. Frozen event/neighbor boundary unions also apply
  to native and all sham conditions. All primary event windows precede any
  scientific gate. Original source/sham, reciprocal rescue, RR, neighbor and
  separated-event rules are reused, then independently rederived for acceptance.
- Mechanics: all 192 validation window/condition families passed self and replay
  controls. Actual before/after tensors confirm GQA layout, selected values,
  visual invariance and untouched cache positions. All 16 inherited-path
  comparisons reproduce exact scores. Candidate suffixes retain the original
  token-normalized raw-model scoring, and patches leave a downstream bridge.
- Readability/scope: new code lives under `stage3c9r`; original Stage 3C.9 code
  and artifacts remain unchanged. No new model, library, dataset or scientific
  intervention family was introduced. Existing helpers own cache and attention
  mechanics; the new scorer owns only shared execution and state forks.
- Performance: immutable fork states are copied to CPU with no dtype conversion
  so only the active cache continuation uses GPU memory. This avoids retaining
  several long GPU caches at once. Per-condition atomic files support exact
  resume, and shard configs reject a changed scoring implementation.
- Access/compute: paths remain inside policy roots. The model/dataset are local;
  no downloads or global installations occurred. All GPU work uses scheduler
  records and the existing Slurm 108548 shell in tmux 9, with Slurm-owned device
  visibility and four disjoint ranks. No new allocation is submitted.
- Interpretation: C3 requires a distinct final probe; no later probe means
  RIGHT-CENSORED. Distant failed probes do not resolve a 16–32-token decay time.
  Reports regenerate these qualifications from authoritative new artifacts.
- Final verification: 86 focused/new and inherited tests pass; all new Python
  files parse; mechanical validation passes 15/15 and acceptance passes 20/20.
  Independent formulas agree in 2,000 signed/sham/threshold test cases. Actual
  execution traces pass for all 576 primary and 18 lifetime files; scientific
  gates/counts are independently rederived and 4,751 original hashes unchanged.
- Report review corrected two presentation issues before completion: base-38
  lifetime is drawn only at observed probes (no interpolation over unobserved
  intervals), and GPU peaks are aggregated over every saved condition because
  the inherited prefill resets peak counters. No inference rerun was needed.

No blocking implementation finding was identified. This is a main-agent code
review under the repository's default single-agent workflow, not an independent
scientific review or authorization for a follow-on experiment.
