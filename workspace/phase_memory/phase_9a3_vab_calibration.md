# Phase9A.3: bounded Qwen2.5 → Qwen3 VAB calibration

## Current Objective

Execute the user-approved small synthetic positive-control assay in Qwen2.5 CoT;
only if calibrated, test the identical frozen assay in Qwen3 CoT.

## Active Constraints

- Plan: plan/stage9a3_bounded_vab_calibration_qwen25_vs_qwen3_cot_plan.md.
- Execution definitions: plan/stage9a3_execution_protocol_v1.md.
-32 primary images/64 queries,16 frozen reserve,4 technical images/8 queries.
- Model-wide depth/time rectangle, greedy short cap, unchanged prompt/grid after freeze.
- Existing MathVision evidence immutable; its remaining controls safely drain per§27.
- Phase A gate required before any Qwen3 inference. No Thinking or Stage9B.
- Local .venv and data/models; scheduler-only GPU, four stage workers at most,
  combined old/new ceiling8, authorized node02/03/06/07.

## Current State

- Complete at the mandatory Qwen3 baseline-validity stop; no external blocker.
- Qwen2.5:32 primary +16 frozen reserve images,96 queries; calibration passes at all layers/token64. FULL68/96, zero-access damage21.875pp, finite damage−1.0417pp;99.35% joint bootstrap stability.
- Bounded null-sink on primary32: zero damage15.625pp; token64 damage−1.5625pp. Pattern survives this control.
- Qwen3:8 technical checks pass; FULL20/64 correct,56/64 CoT,46/64 valid/EOS,18 capped. No masked grid or Qwen3 controls run.
- All Stage9A.3 GPUs released; approximately1.88GPUh total,1.81PhaseA. No next action launched.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
|No supported Thinking-specific late necessity|workspace/decision_log.md D-100|Preserve negative prior; do not reinterpret as VAB failure|confirmed|
|Prior cancelled prototype supports only Qwen3/28 layers|code/visual_reasoning/stage9a_vab/access.py|Need actual Qwen2.5/36-layer validation|confirmed|
|New plan explicitly redirects remaining controls|plan/stage9a3_bounded_vab_calibration_qwen25_vs_qwen3_cot_plan.md §27|Safe stop authorized; immutable receipts preserved|confirmed|

## Failed Attempts and Lessons

Technical validator124438 incorrectly assumed every technical native output has8tokens. Six passed; image051_color ended earlier. Receipt/audit at outputs/stage9a3/v1/audit/qwen25_preflight/failure_124438.json. Supported diagnostic: validation-only length assertion. Repair extends only teacher-forced probes with fixed neutral tokens, never forces native generation or resumes after EOS;3 CPU tests pass. All8 revalidate in v2 namespace under124439. No primary masked science yet.

## Open Candidates

Only the approved bounded calibration action. No grid/prompt/dataset search.

## Next-Step Decision

- Current bottleneck: generation comparison is underidentified because Qwen3 FULL is invalid.
- Relevant evidence: Qwen2.5 positive control passes; Qwen3 accuracy31.25% and CoT87.5% fail mandatory floors. Even all18 unscorable answers correct would give only59.375% accuracy.
- Chosen action: close this approved stage, preserve all evidence and STOP before Qwen3 masked science or any rescue.
- Exactly one recommendation: separately approve bounded repair/validation of the Qwen3 FULL-access baseline before a generation-level access conclusion.
- Do not execute that recommendation automatically. No more reserve, prompt/grid/cap tuning, Thinking or Stage9B.

### Step Result

Technical instrument valid after bounded validator repair;74 completed old controls preserved after drain, all prior GPUs released. FULL gates passed after64 gold-free manual reviews were sealed. Fixed grid remains0/16/64/FULL with normalized depths0/.5/.75/1. Exact reuse69 canonical rows leaves571 new continuations. Expected primary+bounded-control generation1.045GPUh, all-cap2.336GPUh; excludes startup/hashing and optional reserve. No prompt/grid tuning.


## Primary calibration boundary

571 masked runs/1024 logical rows complete, all provenance checks pass. Zero damage20.3125pp,95%CI7.8125–32.8125pp. Frozen smallest point-preserving candidate(.75L,64) damage4.6875pp with wide CI−6.25–15.625pp; joint stability56.125% misses90% threshold. Broader(L,64) is robustly preserving (damage−3.125pp). Do not hide this positive finite-access evidence or relax the selected-cutoff stability rule after outcomes.

Historical Next-Step Decision (executed and superseded by final closeout): activate the exact16 frozen reserve images under predeclared precision rule; same grid/prompt/cap, no tuning. Evaluate48 once, then apply gate and bounded controls. Qwen3 remains unlaunched.


## Final closeout — 2026-09-26T17:10:02.265640+00:00

All15 artifact slots documented, including an explicitly empty Qwen3 grid schema and unmeasured comparison. Four PNG/PDF figure sets include primary/extended Qwen2.5 surfaces and a Qwen3 validity diagnostic; transfer-effect figures are not estimable.26 focused CPU tests and seven independent final audit groups passed. Prior main report and74 controls byte-identical.

Frozen shared256 cap is a limitation: Qwen3 technical max235 would suggest512 under a per-model length rule, but no alternative was run. The low-accuracy cause is unknown; no architecture/model-generation claim. Report: outputs/stage9a3/v1/stage9a3_summary.md; final audit: outputs/stage9a3/v1/audit/final_validation.json.
