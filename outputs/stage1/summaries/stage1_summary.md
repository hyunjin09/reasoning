# Stage 1 Summary — Baseline Visual–Reasoning Dynamics

## Outcome

Stage 1A.2 locked the official-style Qwen Thinking protocol, and Stage 1B completed with the predeclared reduced cohort. From 200 prospectively frozen MathVerse attempts, 82 were completed-correct, 116 were wrong, 2 reached the 40,960-token safety ceiling, and none were invalid. The target of 100 was not reached, but the minimum of 80 was met without weakening eligibility.

Stage 1 is therefore complete. Every result below is descriptive. Raw attention and candidate attention peaks are not causal evidence of visual use, evidence acquisition, memory, or discrete reasoning modes.

## Locked generation protocol

The same ten prior pilot examples were compared on NVIDIA RTX A5000 GPUs.

| Condition | Normal EOS | Cap hits | Correct / wrong | Median tokens | p90 tokens |
|---|---:|---:|---:|---:|---:|
| Greedy | 8/10 | 2/10 | 5 / 3 among completed | 11,239 | 40,960 |
| Official-style sampling | 10/10 | 0/10 | 3 / 7 | 8,476.5 | 16,167.6 |

The two greedy cap cases were extreme repetitive loops, and greedy p90 generation latency was 62.37 minutes. Official-style sampling was selected because it matches Qwen's evaluation-reproduction recipe, achieved 100% normal termination, avoided safety-ceiling loops, and was operationally feasible—not merely because it was shorter. Its longest traces were still frequently meandering or pathological, so the lock does not certify reasoning quality.

The locked parameters are `do_sample=true`, temperature 0.6, top-p 0.95, top-k 20, repetition penalty 1.0, presence penalty 0.0, seed 1,234 reset per example, EOS as the intended stop, and `max_new_tokens=40960` as a safety ceiling. On three full-length examples (18,081, 15,955, and 6,135 tokens), instrumented and matched uninstrumented generations were identical token-for-token: **3/3 PASS**.

Full protocol evidence is in `outputs/stage1/protocol_pilot/protocol_40960_report.md`.

## Discovery cohort

The attempt manifest was frozen before outcomes. It contains 100 MathVerse base problems, each with one Vision Intensive and one Vision Dominant variant. Selection prioritized these visually intensive paired variants but did not use correctness, trace length, or observed attention patterns.

| Outcome | Count | Fraction |
|---|---:|---:|
| Completed-correct | 82 | 41.0% |
| Completed-wrong | 116 | 58.0% |
| Truncated / cap-hit | 2 | 1.0% |
| Invalid | 0 | 0.0% |

All 200 raw bundles and outcomes are preserved. The primary dynamics analysis uses only the 82 completed-correct traces. The two cap-hit traces contain extreme repetition and have reproducible lightweight repetition diagnostics.

Across all attempts, generated length had median 3,960.5 tokens, p90 12,113.8, and maximum 40,960. In the completed-correct cohort, median was 3,122.5, p90 10,377, and maximum 22,334. Median latency was 220.9 seconds, p90 761.8 seconds, and maximum 4,624.9 seconds. Peak GPU allocation was 14.63 GiB. The 200 artifacts occupy 4.74 GB; median per-example size was 15.89 MB, p90 44.52 MB, and maximum 266.58 MB.

## Reproducible representation and signals

Every token retains decoded text, modality-attention summaries, predictive entropy, top-1 probability, and top-1/top-2 margin. Each trace is deterministically segmented into contiguous, gap-free spans with `span_id`, token bounds, text, and a coarse semantic label. `VISUAL_READ` is assigned from text semantics and never from attention.

For every token and span, the artifacts preserve visual, prompt/question, and prior-reasoning attention as both total source mass and source-token-count-normalized density. Visual-focus distributions support similarity to the prefill focus, similarity/overlap with the previous span, spatial entropy, and turnover. Per-example timeline data and plots use proportional generated-token time rather than equal-width span indices.

Twenty length-stratified segmentations and twelve representative trajectories were manually reviewed. Coverage is reproducible, but equations, decimals, markup, and control suffixes can fragment into short spans; mixed-purpose spans receive a single label; and lexical `VISUAL_READ` rules are imperfect. Across 29,769 spans, median length was 11 tokens and 8.21% contained at most two tokens. Broad temporal aggregation is defensible, while fine-grained semantic event claims are not.

## Descriptive dynamics

### Allocation over source types

Across the 82 eligible trajectories, the mean trajectory-level visual mass was 0.0496 (bootstrap 95% CI 0.0475–0.0514), prompt/question mass was 0.4028, and prior-reasoning mass was 0.5476. Corresponding mean normalized densities were 0.000456, 0.003002, and 0.001168. These mass and density values answer different descriptive questions because source-set sizes differ substantially.

Visual engagement was heterogeneous. The fraction of spans above the pooled visual-mass 75th percentile had p10 0.0557, median 0.1855, and p90 0.4246 across trajectories. Mean early-minus-late visual mass was positive (0.0114; p10 0.0009, p90 0.0246), indicating an average early-heavy tendency, but representative traces also showed persistent, recurrent, and nearly vision-light patterns.

Visual-focus similarity to the prefill distribution was generally high (median trajectory mean 0.9556). Median mean turnover was 0.00169, while the maximum trajectory mean was 0.1970 and the largest single-span turnover was 0.7821. This heavy-tailed behavior is why mean variant differences in turnover are not treated as robust evidence without paired analysis.

### Candidate visual-attention peaks

The exploratory semantic-span detector uses three-span `[0.25, 0.5, 0.25]` smoothing, per-example prominence equal to 0.5 standard deviations, and a two-span minimum distance. It found a median of 23 peaks per trajectory and a median rate of 7.45 per 1,000 generated tokens. Peak positions were distributed throughout normalized reasoning time rather than being confined to the beginning.

Raw peak count is dominated by opportunity: trace length and count had Spearman rho 0.964. Length correlated negatively with rate per 1,000 tokens (rho -0.322). Exact counts therefore should not be compared without exposure normalization.

Because semantic-span fragmentation could inflate recurrence, a decision-changing robustness analysis repeated detection on fixed 32-, 64-, and 128-token windows. The fraction with at least two peaks was 100%, 85.37%, and 59.76%, respectively; normalized positions remained broadly distributed through the trace. Thus recurrent descriptive modulation is a robust broad pattern, but exact event count, rate, and timing are scale-dependent.

### Exploratory WHEN/WHY alignment

Candidate peaks had only weak pooled associations with semantic `VISUAL_READ` spans (odds ratio 1.19) and visual-reference language (odds ratio 1.17). They were slightly less frequent at automatically labeled semantic transitions (odds ratio 0.88). `COMPUTE` spans had the largest mean visual mass and peak fraction, whereas `VISUAL_READ` did not. Manual review indicates that label noise and mathematical fragmentation are credible alternative explanations.

The uncertainty result ran opposite to a simple high-uncertainty account: span visual mass and entropy had Spearman rho -0.287; mean entropy was 0.313 at candidate peaks versus 0.421 elsewhere; and mean entropy change at peaks was -0.055. These pooled, non-independent associations do not identify a trigger or direction of influence.

Focus turnover differed little at peaks versus non-peaks in the pooled mean (0.00571 versus 0.00536) and was highly outlier-sensitive. Median elapsed distance between candidate peaks was 120 generated tokens, or 0.017 of normalized trajectory time.

## Qualitative patterns

Twelve completed-correct trajectories were selected for diversity rather than hypothesis support. Their reviewed timelines include short coherent early-heavy examples, long recurrent and persistent examples, stable vision-light examples, and both small- and large-focus-shift cases. Several long traces were meandering, assumption-dependent, or internally inconsistent despite a correct final answer. Correctness therefore identifies the requested successful outcome cohort, not uniformly sound reasoning.

Selected overlays were spatially aligned with their source images and ranged from concentration near labels/curves to diffuse or border-focused distributions. No overlay is interpreted as proof that a region supplied causally necessary evidence.

## Paired-variant preparation

All 100 base problems have a reliable Vision Intensive/Vision Dominant pair in the manifest. Vision Intensive terminated normally on 100/100 attempts and was correct on 42%; Vision Dominant terminated on 98/100 and was correct on 40%. Median raw lengths were 3,794 and 4,015 tokens, respectively.

Within the eligible outcome-selected subset, the variants had nearly identical mean visual mass (0.0498 versus 0.0493), peak count (33.6 versus 36.3), and reasoning length (4,788 versus 4,995); unpaired screening found no clear difference. The apparent focus-turnover difference is driven by an extreme Vision Dominant outlier. These are descriptive availability checks, not the paired causal experiment.

## Limitations

- Only 82 rather than the target 100 trajectories met completed-correct eligibility.
- The discovery cohort intentionally covers only Vision Intensive and Vision Dominant variants and contains paired, non-independent observations.
- Sampling uses one fixed seed; stochastic within-item variability is not estimated.
- Long-trace correctness can coexist with repetitive, speculative, or incoherent reasoning.
- Automatic semantic labels are useful for broad screening but noisy for precise event interpretation.
- Candidate-peak counts depend on segmentation scale and strongly on trajectory length.
- Pooled span-level tests violate independence; reported p-values are exploratory screens.
- Attention allocation and visual-focus distributions remain descriptive measurements, not causal visual usage.

## Final boundary and stop

Stage 1 characterizes temporal attention, focus, and uncertainty patterns under one locked intended-use protocol. It does not establish fresh visual access, stored visual memory, re-grounding, or discrete LOOK/THINK states. No attention knockout, image intervention, cache patching, routing manipulation, or other Stage 2 experiment was performed.

## Acceptance criteria

Independent validation recomputed all 200 bundle invariants and found no failures. The machine-readable record is `outputs/stage1/summaries/stage1_acceptance.json`.

| # | Status | Criterion | Evidence |
|---:|:---:|---|---|
| 1 | PASS | Final generation cap prospectively selected | Official-style protocol locked with a 40,960 safety ceiling. |
| 2 | PASS | Selected-pilot truncation at most 10% | 10/10 normal EOS terminations, 0 cap hits. |
| 3 | PASS | Instrumentation faithfulness 3/3 | Exact generated-token equality on 3/3 full-length pairs. |
| 4 | PASS | At least 80 completed-correct trajectories | 82 eligible trajectories. |
| 5 | PASS | All raw outcomes preserved separately | 200 raw rows: 82 correct, 116 wrong, 2 truncated, 0 invalid. |
| 6 | PASS | Reproducible token/span timelines | Independent recomputation passed for 200/200 bundles. |
| 7 | PASS | Source mass and normalized density available | Visual, prompt, and prior-reasoning mass/density distributions saved. |
| 8 | PASS | Visual focus and uncertainty available | Token/span arrays and aggregate statistics independently validated. |
| 9 | PASS | Dataset temporal statistics computed | Peaks, temporal positions, focus, semantic, uncertainty, and variant summaries saved. |
| 10 | PASS | At least 10 representatives manually inspected | 12 representative trajectories plus 20 segmentation reviews. |
| 11 | PASS | Paired variants reliably aligned | 100 complete Vision Intensive/Vision Dominant base-problem pairs. |
| 12 | PASS | No attention-only causal result | Reports maintain the descriptive-evidence boundary. |
| 13 | PASS | No Stage 2 experiment started | No Stage 2 output or intervention exists. |

Stage 1 ends here pending review of these descriptive results.
