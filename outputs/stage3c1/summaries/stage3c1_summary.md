# Stage 3C.1 Summary — Causally Anchored Retrieval-Attention Phenotype

## Outcome

**Technical result: PASS (20/20).** The exact historical 37-base paired-semantic numeric cohort was characterized at the two independently causal-localized late-W4 retrieval targets. The dominant descriptive result is a **high-attention, ROI-selective retrieval phenotype with strong temporal QK-cosine sharpening**, accompanied by large target αV and post-`W_O` contributions. This does not show that attention magnitude causes retrieval.

No attention, Q, K, V, routing probability, source state, or residual state was manipulated. No Stage 3C.2, Stage 4, sink knockout, rerouting, `h_pre` patch, or failure experiment was started.

## Frozen protocol and cohort

- Cohort: 37 unique `base_problem_id` values, all `tier1_local_numeric_label`, using the frozen O/O_sham/C/C_sham images, `E_d`, and Stage 3B.7 target/complement/irrelevant ROI token mappings.
- Target A: `E_d`, W4, layer 29, heads `[11, 6, 15, 12]`.
- Target B: `E_d-1`, W4, layer 28, heads `[16, 0, 3, 6]`.
- Temporal grid: `E_d-16, -8, -4, -2, -1, 0` when history existed; 35 bases supported `-16`, and all 37 supported the remaining checkpoints.
- Noncausal controls were frozen without attention: A `[0,1,2,3]`; B `[1,2,4,5]`.
- W5 controls remained restricted to A at `E_d`/layer 32 and the secondary `E_d-1`/layer-32/head-10 comparator.
- Execution: Slurm allocation `106936`, node04, two NVIDIA RTX A5000 GPUs, tmux session 8. Summed per-base runtime was 248.2 seconds across parallel shards.

## Exact implementation audit

- Full-shape eager-Attention probability reconstruction max error: `0.0`.
- Full-shape pre-`W_O` head-output reconstruction max error: `0.0`.
- Instrumented versus uninstrumented next-token logits: max error `0.0` on both smoke bases.
- Repeated extraction: bitwise exact on both smoke bases.
- Maximum BF16 source-mass closure error: `0.002551`, below the frozen `0.005` representation tolerance.
- αV partition reconstruction max error: `2.86e-06`.
- Exact per-head `W_O`-slice partition reconstruction max error: `1.19e-06`.
- All 14,820 per-head/time/condition rows were finite; all 37 four-condition token/ROI layouts matched exactly.

The first row-only reconstruction smoke was rejected because changing GEMM/softmax tensor shape induced BF16 kernel drift. Recomputing the installed full tensor shape gave exact equality. A separate sink-class bookkeeping error (image placeholders are tokenizer-special IDs) was corrected offline without changing inference or any attention/QK/Value measurement; see `audit/sink_definition_correction.json`.

## Primary ROI phenotype

Values below first average frozen causal heads and all four conditions within base, then summarize 37 independent bases.

| Quantity | Target A | Target B |
|---|---:|---:|
| Median target-ROI attention mass | 0.3965 | 0.3191 |
| Median target-ROI density | 0.1057 | 0.0690 |
| Median irrelevant-ROI density | 0.001211 | 0.000422 |
| Median target/irrelevant density ratio | 69.2× | 134.5× |
| Target density > irrelevant | 97.3% | 100.0% |
| Median target share of visual attention | 0.609 | 0.540 |
| Median target αV norm (mean across heads) | 7.9892 | 5.0808 |
| Median target post-`W_O` frozen-set sum norm | 20.5274 | 15.3299 |

Target ROI density also exceeded prospectively frozen noncausal heads by median `0.0524` for A (36/37 positive) and `0.0599` for B (37/37 positive). These comparisons are descriptive because the heads and coordinates were selected causally in prior stages, not by Stage 3C.1 attention.

## Temporal and QK decomposition

The phenotype sharpens close to the causal coordinate rather than remaining constant:

- A at `E_d` versus `E_d-16`: target-density median difference `0.0987`, target-QK cosine `0.2491`, scaled target logit `4.0465`, and target αV norm `7.8004`.
- B at `E_d-1` versus `E_d-16`: corresponding differences `0.0657`, `0.1980`, `3.4847`, and `4.9610`.
- Every frozen target-density retrieval-versus-earlier contrast survived Holm correction. The nearest comparisons were A versus `E_d-1` (median `0.0500`) and B versus `E_d-2` (median `0.0302`).

Target visual K norms are invariant across query times within a layer, as expected for fixed prompt positions. Q norms did not show a consistent retrieval-time increase. In contrast, QK cosine and final logits rose sharply. At the retrieval coordinate, target minus irrelevant median QK cosine was `0.2472` for A and `0.1847` for B; target minus irrelevant K norm was smaller (`0.8614`, `1.3115`), while the scaled-logit gaps were `5.0573` and `4.2270`. The strongest routing signature is therefore directional QK compatibility plus softmax competition, not a simple Q- or K-norm surge.

## Controls, source mass, and head heterogeneity

- Target A's W4 target-ROI post-`W_O` set contribution exceeded the frozen W5 upstream-state control by median `2.6133` (bootstrap 95% CI `0.8181` to `5.8249`; 29/37 positive). This is a descriptive comparison of natural contributions, not a new intervention.
- Mean source-mass composition at A retrieval was visual `0.631`, question `0.076`, previous reasoning `0.042`, special/other `0.251`. At B it was `0.465`, `0.109`, `0.113`, `0.313`. Thus these frozen heads remain substantially visual at the causal coordinates, but nonvisual mass is not absent.
- A head 11 showed the strongest median target density (`0.167`); all four A heads were elevated.
- B was heterogeneous: heads 16, 0, and 3 had median target densities `0.113`, `0.101`, and `0.065`, while shared head 6 was only `0.000371` despite membership in the independently causal Top-4 ensemble. This is direct evidence that natural attention magnitude is not a sufficient per-head causal score.

## Condition and artifact controls

Target-density sham shifts were small relative to the primary densities: A O−O_sham median `-0.000428` and C−C_sham `-0.000819`; B values were `0.001083` and `-0.000258`. All four frozen semantic/render conditions were retained.

## Candidate sink phenotype

The first prompt token is token 151644, `<|im_start|>`. Across base-aggregated causal heads, times, and conditions, its median attention mass was `0.399` and it was the top-attended position in a median `75.5%` of rows. Its median absolute O/C mass difference was `0.020`. This makes it a strong **candidate sink**, not evidence that it is causally useless or safe to remove.

## Relation to prior causal effects

Natural target density correlated with the Stage 3B.7-R ROI causal effect for A (`Spearman ρ=0.536`, `p=0.000627`) but not B (`ρ=0.199`, `p=0.238`). A target mass/αV/post-`W_O` correlation with causal restoration was strong; B's corresponding correlations were weak. This target-dependent split is a central caution: even at causally anchored cells, larger raw attention is not a universal quantitative proxy for causal influence.

## Interpretation and limitations

Stage 3C.1 supports phenotype P1—high-attention causal retrieval—at the frozen head-set level, with a cosine/competition-driven routing signature and substantial target Value influx. It does **not** establish that increasing attention will change the represented fact, that QK routing triggers retrieval, or that `<|im_start|>` is dispensable. The cohort is limited to 37 localized numeric-label edits, teacher-forced pre-divergence histories, one model, and two late-W4 targets. Head-level heterogeneity and the A/B correlation split argue against treating attention as causal evidence by itself.

**Attention remains descriptive evidence, not causal evidence.**

## Decision

Exactly one review-only recommendation is recorded in `next_stage_recommendation.md`: **GO — Relevant-vs-distractor routing causality**. No such experiment has been started.
