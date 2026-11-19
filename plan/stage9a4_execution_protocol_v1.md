# Stage9A.4 frozen execution definitions

Approved scope: stage9a4_qwen3vl4b_vab_baseline_repair_finite_access_plan.md.
Freeze before any new model inference. The original user plan remains authoritative.

- Reuse Stage9A.3's exact 32 primary, 16 reserve and four technical images,
  query IDs, options, prompts, preprocessing and seed 920260927. No regeneration.
- Qwen3-VL-4B-Instruct pinned local revision ebb281ec70b05090aa6165b016eac8ec08e71b17;
  36 language layers, native DeepStack unchanged. BF16, TF32 off, eager language,
  SDPA vision, greedy/native EOS, max_new_tokens=512 throughout this stage.
- FULL/no-intervention equality on eight technical queries precedes R0. Only
  FULL runs on the 64 primary queries until sealed answer/CoT review passes G1-G5.
  Then eight technical V1-V6 tests exercise ZERO and transitions 64/128/256,
  including null-sink, before scientific masking. No scientific technical scores.
- Generated query index t=absolute_position-prompt_length+1; image/question
  prefill is unchanged. Image keys are blocked for t>cutoff in every decoder layer.
  The prefill-predicted first token and cached image-derived state remain native.
- G1 accuracy>=.60; G2 genuine intermediate reasoning>=.90; G3 extractable final
  option>=.90; G4 cap rate<=.10 OR every capped trace has a valid final option;
  G5 exact same-backend FULL no-op. Missing final options receive no credit.
  Record EOS, cap, raw extraction, generation lengths and unscorable counts.
- Review all FULL traces for actual enumeration, identification, calculation or
  counting before final answer. Intent-only/answer-only is not CoT. Factual
  correctness is irrelevant to the CoT label. Seal literal final labels and CoT
  before joining answer keys; never infer the intended answer from prose/counts.
  Reuse Stage9A.3 terminal-label adapter and manual exception review. Preserve
  raw strict {A} extraction sensitivity.
- R1 exactly ZERO and64. If ZERO damage<=.05, stop necessity interpretation.
  Otherwise select64 when damage<=.05; else run128, then256 only as required,
  selecting the first point-preserving cutoff. Tolerance comparisons use1e-12
  for floating arithmetic. No statistical-significance gate replaces plan rules.
- Image is independent: average both queries equally, pair conditions within
  images, 4,000 bootstrap draws and95% percentile intervals, seed920260927.
  Report preservation probability and uncertainty without turning point-based
  selection into proof of equivalence. No dense grid or depth truncation.
- Optional reserve is triggered when a finite cutoff was selected, primary FULL
  and technical gates pass, abs(selected damage)<=.10 and its95% interval spans
  .05 (strictly on both sides). Freeze selected cutoff before reserve outputs;
  run only FULL/ZERO/selected on all16 reserve images. Combine48 with equal image
  weight, keep primary result separate, no retrospective cutoff change. If no
  cutoff is selected, reserve is not used. Changed combined evidence is reported.
- Null-sink after selection: primary32 only FULL/ZERO/selected. FULL and any
  normally-ended trajectory with N-1<=cutoff are exact identity reuses; capped
  trajectories are never aliased as normal endings. No non-image renormalization.
- P3 headline is Q3 damage64 minus frozen Q2.5 combined48 damage64 (-1/96).
  The two cohort sizes differ; additionally report a paired primary32 image
  difference using existing Q2.5 primary outputs. Do not call unequal-cohort P3
  paired. Never recompute Q2.5 or attribute effects to architecture/capacity.
- Up to four currently available A6000 GPUs on node02/03/06/07 via project
  scheduler, one process per GPU,4CPU/30G per worker. No tmux/keepalive. Workers
  end with finite queues; no follow-on launches. CPU hashing/bootstrap scheduled.
- Projected primary science target<15GPUh; >25GPUh before reserve/control stops.
  Initial conservative .06s/token ×512 ceiling: R0 .55h; R1 1.10h; worst R2
  1.10h; reserve .82h; null-sink1.10h plus startup/validation. Update throughput.
- Required report/artifacts distinguish conditional not-run from measured null.
  Exactly one outcome-appropriate recommendation, then STOP without launching it.

Implementation checkpoints: (1) freeze/reuse and gate tests; (2) FULL no-op/R0
review and gates; (3) conditional actual-mask validation/R1/sequential analysis;
(4) conditional reserve/control; (5) independent audit, figures, accounting, stop.
Git metadata is absent; source hashes and immutable receipts provide save points.
