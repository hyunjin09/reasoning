# Stage 3C.2 Summary: Semantic Alignment, Retrieval Demand, and Sink Dynamics

## Outcome

**Technical PASS (20/20).** Stage 3C.2 retained **31 unique base problems**, completed the exact passive four-condition extraction, produced all 14 required figures, and did not manipulate attention, Q, K, Value routing, sink states, `h_pre`, or any source state.

The main descriptive result is an **alignment-then-retrieval / retrieval-only mixture**. At the frozen retrieval coordinate, task ROI T exceeded distinct mention ROI M for all 62 target/base events in attention density, QK cosine, alpha-V norm, and post-`W_O` norm. Across target/base events, 40/62 (64.5%) were alignment-then-retrieval and 22/62 (35.5%) were retrieval-only.

This is descriptive evidence that lexical/semantic alignment alone is insufficient to explain the observed routing pattern. It is **not** evidence that attention is itself the causal acquisition mechanism.

## Protocol and cohort

- Model/conditions: frozen Qwen3-VL-4B-Thinking context under O, O_sham, C, and C_sham.
- Frozen targets: Target A = E_d/W4/layer 29/heads [11,6,15,12]; Target B = E_d-1/W4/layer 28/heads [16,0,3,6].
- Frozen controls: Target A heads [0,1,2,3]; Target B heads [1,2,4,5].
- Temporal grids: [-16,-8,-4,-2,-1,0] relative to each target's own coordinate.
- Cohort: 37 screened, 31 retained, 6 excluded; no attention used for selection or annotation.
- Measurements: **11,904 per-head rows** and **2,976 head-set rows**, with individual-source-position tensors preserved under `outputs/stage3c2/extraction/raw_tensors/`.

## Frozen primary contrasts

All seven contrasts use base problem as the independent unit and Holm correction across the prospective family.

| Contrast | Mean | Median | Positive fraction | Bootstrap mean 95% CI | Holm p |
|---|---:|---:|---:|---:|---:|
| T-M retrieval attention density | 0.0925 | 0.0872 | 1.0000 | [0.0783, 0.1070] | 6.52e-09 |
| Retrieval-minus-mention QK_T | 0.2050 | 0.2130 | 0.9677 | [0.1758, 0.2330] | 6.52e-09 |
| Retrieval-minus-mention A_T density | 0.0916 | 0.0870 | 1.0000 | [0.0776, 0.1057] | 6.52e-09 |
| Retrieval-minus-mention alphaV_T norm | 6.5911 | 6.7202 | 1.0000 | [5.7276, 7.4259] | 6.52e-09 |
| Retrieval-minus-mention sink mass | -0.2142 | -0.2166 | 0.0645 | [-0.2635, -0.1604] | 3.46e-07 |
| T-M temporal crossover | 0.0947 | 0.0879 | 1.0000 | [0.0803, 0.1095] | 6.52e-09 |
| Causal-vs-noncausal crossover enrichment | 0.0657 | 0.0574 | 1.0000 | [0.0546, 0.0774] | 6.52e-09 |

At retrieval, event-level median T-M differences were 0.0868 attention density, 0.2043 QK cosine, 6.0976 alpha-V norm, and 7.0147 post-`W_O` norm.

## Attention-budget and candidate-sink observations

From the paired mention-only to retrieval states, target attention mass rose by a median 0.3397, while first-token candidate-sink mass changed by a median -0.2052. Target gain and negative sink change had Spearman rho=0.362 (p=0.003813). Under the documented exploratory threshold, 46/62 events were sink-release, 13/62 persistent-sink, and 3/62 non-sink-reallocation. The largest losing class was the candidate sink in 32/62 events, previous reasoning in 12, other visual in 11, prompt/question in 6, and M in 1.

These values show natural probability reallocation only. `<|im_start|>` remains a **candidate sink**, not a proven useless or causal reservoir.

## Controls and head heterogeneity

At retrieval, the base-level median signed O-O_sham difference was 0.0032 for target mass and 0.0016 for sink mass; the median absolute differences were 0.0289 and 0.0085. The O-C median absolute differences were 0.0434 and 0.0132. Thus the primary natural O-only dissociation is not defined from condition differences, and sham variation remains a limitation for fine semantic comparisons.

Target-B head 6 retained its low-attention phenotype: median target density=0.000337, QK_T=0.0415, and alphaV_T=0.0177. Other causal heads carried much larger target routing. Head averaging would conceal this heterogeneity.

## Technical validation

- Exact full-shape eager reconstruction: probability error 0; head-output error 0.
- Instrumentation smoke: 2/2 zero logit drift; exact deterministic repeats.
- Maximum eight-way source-partition closure error: 0.002774 < 0.005.
- All T/M/I/sink sets were mutually audited; all values were finite.
- Four image conditions used identical token/visual layouts per base.
- No intervention was executed.

## Limitations

- The retrieval coordinates are inherited teacher-forced discriminative coordinates; temporal association does not prove fresh evidence acquisition.
- The cohort is restricted to numeric-label problems with clean counterfactual ROIs and deliberately distinct mention entities; generalization beyond this phenotype is unknown.
- M annotations vary in spatial extent, so both mass and per-token density are reported; the primary T-vs-M attention contrast uses density.
- A0 was absent by design, and the within-problem semantic pairs are not exact lexical matches.
- Sham image rerendering causes measurable attention variation, especially in O-O_sham absolute target-mass differences.
- QK, attention, alpha-V, post-`W_O`, and candidate-sink quantities remain descriptive measurements. None was manipulated in Stage 3C.2.

## Scientific boundary

The defensible conclusion is: **natural routing to independently causal T sharpens near the frozen retrieval coordinate and frequently follows earlier M dominance; semantic mention alignment alone is insufficient to explain this pattern.** It is not defensible to claim that QK sharpening causes retrieval, that attention mass is an information fraction, that sink mass is dispensable, or that these traces prove LOOK/THINK states.
