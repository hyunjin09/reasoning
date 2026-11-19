# Stage 3B.0 summary — Prefill visual-to-language transfer

## Outcome

**Technical status: PASS (15/15 acceptance criteria).**

**Recommendation: REDIRECT — Post-prefill acquisition timing.**

Stage 3B.0 found a widespread but small prefill-carried visual residual. Generation-start visual cutoff left raw CE positive in **42/49** bases and sham-controlled CE positive in **44/49**, but retained only **14.5% on average** and **6.1% at the median** of Stage 3A's full-vision CE. Mean cutoff CE was **0.4731** (95% bootstrap CI [0.3148, 0.6471]); sham shift remained near zero.

All-layer `P_post-image` KV patching transferred the residual exactly in both directions for 49/49. Q-only patching captured nearly all of that residual at the median (**0.9884**) and was source-consistent in both directions for **46/49**. T-only patching was weak. Thus Q cached states are a major carrier of the residual, but prefill carriage does not explain most of the Stage 3A effect.

## Cohort and protocol

- Primary unit: 49 frozen unique Stage 3A `base_problem_id` values (45 numeric-label edits; 4 structural edits).
- Selection: no attention-based selection or patch targeting.
- Prefill: normal multimodal processing.
- Cutoff: every generated-token query from `y_0` onward blocked from every visual key, across all 36 language layers and all 32 logical query heads.
- Patching: post-RoPE K and V at identical sequence positions, all layers, bidirectional; self and sham controls included.
- Primary cutoff score: full-sequence Stage 3A-compatible eager path.
- Patch baseline: matched deterministic cached path, avoiding a measured BF16 full/cached kernel-path discrepancy.

## Validation

The three-base smoke gate passed exact Stage 3A reproduction, hook no-op transparency, query/key-edge audit, causal-order audit, condition alignment, `[1,8,S,128]` GQA cache validation across 36 layers, exact self patches, deterministic cached scoring, and finite outputs. Cohort aggregation independently verified **49 cutoff rows, 1,176 patch rows, 147 rollouts, and 9 figures**. GPU work ran through Slurm on RTX A5000 devices (validated smoke job 106405; cohort jobs 106408–106414); maximum reported cohort allocation was **9.63 GB (8.97 GiB)**.

## Main results

1. **RQ1 — Prefill sufficiency:** evidence direction often survived, but magnitude retention was weak (mean 14.5%; median 6.1%). Prefill alone is insufficient for most of the full effect.
2. **RQ2 — Broad prefix carrier:** `P_post-image` produced exact source-like transfer in both directions for every base, validating that the accessible nonvisual post-image cache carries the cutoff residual.
3. **RQ3 — Q carrier:** Q recovered a median 0.9884 of that residual; mean unnormalized source-oriented shift was 0.4787, compared with 0.4844 for broad P and 0.0390 absolute shift for Q sham patches.
4. **Controls:** every self patch had zero shift. T recovery was near zero at the median; Q+T did not improve consistency over Q.
5. **Heterogeneity:** numeric mean retention was 12.8%; structural mean was 33.2%, but structural N=4 is too small for a firm comparison. Prefix length had no detectable rank association with retention.

## Limitations

- Cutoff retention is not a direct estimate of a unique information fraction; distributed/redundant representations and nonlinear effects remain possible.
- Broad-P exact recovery is partly structural to the intervention: with V inaccessible and pre-image tokens condition-invariant, P contains all accessible image-conditioned prompt states.
- Raw normalized recovery is unstable for small cutoff denominators (12/49 below 0.05; one approximately zero). Values were not clipped or dropped; median recovery and unnormalized shifts are emphasized.
- The 128-token rollout validation was usually too short to reach an explicit fact and is inconclusive.
- Four structural examples are insufficient for a stable evidence-type comparison.
- No layer, head, module, Q→R path, or post-prefill timing boundary was localized.

## Scientific boundary

This stage provides causal evidence about image-content sensitivity under a generated-query visual cutoff and causal transfer via cached prefix states. It does **not** use attention as the primary measure of visual acquisition, and it does not claim that attention marks LOOK/THINK states. Stage 3B.1 and every prohibited layer-wise, carrier-localization, timing-sweep, or Q→R experiment remain unstarted.

## Key artifacts

- `cutoff/cutoff_statistics.json` and `cutoff/per_problem_cutoff_results.jsonl`
- `patching/patch_statistics.json`, `patching/broad_prefix_patch_results.jsonl`, `patching/question_patch_results.jsonl`
- `layout_audit/`, `smoke/`, and `analysis/figures/`
- `summaries/stage3b0_acceptance.json`
- `summaries/stage3b1_recommendation.md`
