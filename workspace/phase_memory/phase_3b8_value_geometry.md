# Phase 3B.8: Causal Value Geometry

## Current Objective

Record the completed user-approved Stage 3B.8 action: causal Value dose-response, discovery-only shared-subspace fitting, untouched 37-base confirmation, frozen controls, and one final recommendation.

## Active Constraints

- Preserve Stage 3B.7-R and all earlier artifacts unchanged.
- Freeze exactly Target A `E_d/W4/Top_4=[11,6,15,12]` and Target B `E_d-1/W4/Top_4=[16,0,3,6]`.
- Use `base_problem_id` as the statistical unit.
- Keep the 37 primary bases out of discovery fitting and rank selection.
- Obtain 16--20 fresh discovery bases disjoint from the primary 37, Stage 3B.7-R validation 13, and original Stage 3B.7 validation 8.
- Selection may not use attention, Stage 3B.8 outcomes, or fit quality.
- Stop if ROI-derived Value reconstruction fails or Phase-A dose-response is mechanically/semantically unstable.
- Attention and optional probes are secondary and post-freeze only.
- Do not start vision-encoder/projector localization, multi-evidence refresh, Q/R lifecycle, MLP-feature/neuron, or failure analysis.

## Current State

- Done: Stage 3B.7-R finished with both targets ROI-Local and Value-Dominant on the untouched 37-base primary cohort.
- Done: the complete Stage 3B.8 plan, machine-local access/GPU rules, current research state, and promoted Stage 3B.7-R decision were reviewed.
- Done: 11 disjoint, manually edit-valid, outcome-blind contingency candidates from Stage 3B.7-R remain ungenerated: `302,303,309,312,314,319,322,324,325,332,334`.
- Done: the two frozen target definitions, 37-base primary shards, discovery/confirmation protections, and 512-dimensional pre-`W_O` representation protocol are frozen.
- Done: prospective discovery generation batch 1 completed with 8 correct and 3 wrong outcomes; all raw outcomes are preserved.
- Done: 20 additional attention/outcome-blind numeric edits passed manual v4 review; 16 are active and 4 are prospectively held as a contingency.
- Done: the real-model representation smoke passed after an audited BF16 numerical-equivalence repair; both Stage 3B.7-R V-only endpoints reproduce with exactly zero `D` error and repeated vectors/results are exact.
- Done: the 37-base primary Value dose-response passed the frozen Phase-B gate for both targets with exact endpoints and required mechanics.
- Done: Phase A passed its frozen dose-response gate for both targets on all 37 primary bases.
- Done: a 20-base fresh discovery cohort was frozen after 27 prospective raw outcomes (22 effective completed-correct), strict-E_d review, and manual ROI review.
- Done: discovery-only uncentered SVD and the frozen causal rank sweep selected rank 8 for both targets.
- Done: untouched primary confirmation completed with exact mechanics, but rank-8 compression did not generalize at the discovery strength: projected/full medians were 0.368 (Target A) and 0.532 (Target B-R), with complement/full 0.472 and 0.348.
- Done: all 100 same-rank random-subspace controls per target completed on all 37 primary bases; the learned basis exceeded every random draw for both targets (percentile 1.0; empirical one-sided `p=0.0099`).
- Done: sham-derived, orthogonal-complement, and secondary cross-target controls completed. Cross-target medians were 0.0040 into Target A and 0.0017 into Target B-R, far below the corresponding own-basis effects.
- Done: post-freeze attention comparison remained secondary and showed heterogeneous target-specific correlations.
- Done: Stage 3B.8 passed all 20/20 technical acceptance criteria. The shared rank-8 low-dimensional causal-subspace claim is not supported on primary confirmation; the single recommendation is **GO — Distributed Value geometry** for review only.
- Blocked: none.
- Most recent useful observation: Value transport is graded and the discovery-learned geometry is more specific than random or sham-derived rank-8 bases, but it captures only 0.368/0.532 median projected/full restoration on untouched primary confirmation and leaves 0.472/0.348 in the orthogonal complement.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Both frozen W4 targets are ROI-Local and Value-Dominant | `outputs/stage3b7r/analysis/spatial_localization_analysis.json`; `outputs/stage3b7r/analysis/kv_decomposition_statistics.json` | Defines the only authorized Stage 3B.8 causal targets and representation path | confirmed |
| K+V exactly reproduces target-ROI restoration and K-only is nonrobust | `outputs/stage3b7r/analysis/kv_decomposition_statistics.json` | Supports studying Value-content rather than attention routing | confirmed |
| The primary cohort contains 37 independent numeric bases | `outputs/stage3b7/config/cohort_manifest.jsonl` | Defines the untouched confirmation set | confirmed |
| Eleven manually edit-valid contingency examples were frozen before their generation outcomes existed | `outputs/stage3b7r/config/batch3_edit_validation_freeze.json` | Supplies the first discovery-generation batch without outcome or attention selection | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Original Stage 3B.7 Top-2 target | Failed its frozen sham-relative gate | supported semantic-strength/control failure | Preserve the failure; Stage 3B.8 uses only revalidated Top-4 targets | Do not reinterpret or reuse Top-2 |
| Stage 3B.7-R first-pass edit construction | Most automatic masks damaged geometry or undercovered text | supported by manual audits | Exact component bounds plus manual line-clearance validation are required | Do not infer on unreviewed edits |
| Stage 3B.7-R aggregation metadata joins | Evidence type and historical unit matching were initially implicit | supported schema mismatch | Require explicit frozen metadata joins and exact target identity | Do not silently fall back across units |
| Stage 3B.8 representation smoke v1/v2 | Local mechanics passed but Stage 3B.7-R V-only endpoint errors were 0.1196/0.1422 D | supported BF16 reduction/round-trip mismatch; CPU BF16 diagnostic showed up to 0.015625 coordinate error | Use exact full-source eager recomposition and direct composed-head assignment at lambda=1 | Do not reconstruct an exact BF16 endpoint with ROI-only reduction or `native+(composed-native)` |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Fresh discovery cohort | Required for leakage-free fitting | Outcome-blind screening, locked generation, strict `E_d`, and manual ROI audit | completed with 20 valid disjoint bases |
| Low-dimensional shared Value subspace | Stage 3B.7-R shows robust ROI-local V-only restoration | Discovery-only SVD/rank selection followed by untouched primary confirmation and controls | not supported at rank 8 on primary confirmation |
| Broader, sample-conditioned, or nonlinear Value geometry | Graded Value causality survived while shared rank-8 compression did not | Requires a separately reviewed and authorized plan | recommended for review; not started |

## Next-Step Decision

- Current bottleneck: none within the authorized action; Stage 3B.8 is complete and stopped pending joint review.
- Relevant memory item used: random and sham specificity passed, but untouched primary compression failed and cross-target transfer was weak.
- Chosen next action: no experiment. Return **GO — Distributed Value geometry** as the single review recommendation.
- Why this action: the causal Value effect is robust and graded, yet a shared rank-8 basis does not recover most of the untouched primary effect; upstream-origin localization would therefore overstate the supported geometry.
- What not to repeat: do not use attention or causal results for selection, learn a subspace on the primary 37, add ranks after confirmation, or use mismatched historical target metadata.
- Stop condition: achieved. Do not start vision-encoder/projector localization, multi-evidence refresh, Q/R lifecycle, MLP-feature/neuron, failure analysis, or another Value-geometry experiment without a new reviewed plan and explicit authorization.

### Step Result

- Action taken: completed the audited representation, 20-base discovery cohort, 37-base dose response, discovery-only SVD/rank selection, untouched primary projection/complement confirmation, 100 random controls per target, sham-derived control, cross-target transfer, and post-freeze attention comparison.
- Result: technical PASS (20/20). Dose response passed both targets; learned rank 8 beat random and sham controls but failed the primary 80%/30% compression rule for both targets. Cross-target transfer was weak.
- Evidence saved: `outputs/stage3b8/summaries/stage3b8_summary.md`, `outputs/stage3b8/summaries/stage3b8_acceptance.json`, `outputs/stage3b8/analysis/artifact_validation.json`, and the complete Stage 3B.8 raw/control trees.
- Failure or issue: the low-dimensional shared-subspace hypothesis did not generalize at the frozen rank despite clean mechanics and specificity controls; diagnosis remains unknown.
- Lesson learned: a direction can be causally specific relative to random/sham controls without capturing most of the causal effect across untouched examples.
- Next implication: review broader, sample-conditioned, or nonlinear Value geometry as a possible next question; no next experiment is authorized.
