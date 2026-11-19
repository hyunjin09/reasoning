# Phase10C: causal visual reopening

## Current Objective
Test whether new B demand increases direct all-image necessity over PRE and has
source-specific causal dependence, on the frozen natural Stage10B candidates.

## Active Constraints
- Approved16 primary/8 reserve; no candidate/anchor tuning after interventions.
- Native2B Thinking, BF16, TF32 off, greedy local88-token assay;24-token masks.
- All28 decoder layers standard image-key mask; prior cache retained.
- Local B correctness + frozen native-span NLL; no final-answer primary metric.
- Slurm only, up to8 available GPUs; total<4GPUh. Follow-on requires new instruction.

## Current State
- Done: policies, active plan, D110–D112, Stage10B evidence and existing runtime read.
- Done: exact24 sensitivity events and deterministic16/8 split frozen;4 protocol tests.
- Done: all24 image-grounded gold/control rules sealed before interventions.
- Done: three technical cases pass all10 checks,88-token no-op logits/tokens exact.
- Done: all16 primary cases (80 free branches and80 paired NLL rows), GPU jobs125314/125315 COMPLETED on node07 and released.
- Done:80 condition-blinded local ratings sealed with exact quotes and identical-text consistency.
- Done: CPU paired inference; Outcome D/full gate fails. P1+0.125, P2+0.39957, P3+0.0625, P4+0.17718; only P2 adjusted interval excludes0.
- Dataset P1/P3: MathVision+0.375/+0.25, MathVerse−0.125/−0.125. Historical-faithful P3=0.
- COMPLETE / STOP: reserve/optional gates fail; no further GPU work. Eleven mandatory artifacts and four PNG/PDF figure pairs audited, all visualizations inspected.
- Resources:0.120833 allocated GPUh, peak2 GPUs; all Slurm jobs terminal and GPUs released.
- Native greedy local B correctness3/16 versus historical sampled8/16: limited local resolution is an explicit interpretation constraint.
- Seven focused protocol/statistical tests pass; labels sealed before condition keys/NLL were opened.
- Blocked: none.
- Observation: original traces sampled; Stage10C explicitly greedy. New local greedy
  baseline required; historical sampled suffix cannot be claimed an exact reuse.

## Evidence That Matters
| Evidence | Source | Why it matters | Status |
|---|---|---|---|
|26 candidates,24 gap sensitivity | Stage10B inference | exact pool, no outcome-driven additions | confirmed |
|Single transition supported | D110 | reopening needs new causal contrast | confirmed |
|Positive P2, failed behavioral gates | stage10c_primary_inference.json | native-span support is not sufficient for causal reopening claim | confirmed |
|3/16 greedy B resolutions;8/16 historical | stage10c_summary.md | fixed local endpoint constrains negative inference | confirmed |
|Standard/null-sink differed | D107/Stage9A.5 | intervention-specific claim; cache retained | confirmed |

## Failed Attempts and Lessons
CPU collector125320 ran without its intended dependency and failed before review/analysis. Primary jobs are unaffected. Preserve `audit/collector_failure_125320.json`; collect only after verified terminal GPU status rather than retrying the ignored dependency mechanism. Seven focused protocol/statistical tests pass.

## Open Candidates
Only approved local PRE/POST and source masks, paired native-span NLL; reserve and
optional blocks conditional on frozen gates.

## Next-Step Decision
- Bottleneck: four positive aggregate directions do not survive the frozen dataset/faithful/deletion gates.
- Memory used: D112 passive candidates do not prove necessity; D110 cache/budget limits.
- Completed action: preserve mixed primary evidence; no reserve or optional controls. Required artifacts, accounting and audit complete. STOP; no next experiment authorized.
- Why: required behavioral checks are directionally inconsistent, not merely imprecise. Native-span NLL support alone cannot establish local-correctness reopening.
- Do not repeat: using final accuracy as local correctness or sampled suffix as greedy.
- Stop condition: audited Stage10C result, exactly one recommendation; no follow-on.

## Completion
2026-09-27T16:34:52.824632+00:00 — Outcome D. Exactly one recommendation: stop the reopening branch and finalize the paper around the established visual-to-text transition plus dynamic source retargeting as a separate phenomenon. Cause of failed behavioral convergence is unresolved. No new anchors, windows, model, reserve or follow-on. Evidence: outputs/stage10c/v1/stage10c_summary.md and audit/final_audit.json.
