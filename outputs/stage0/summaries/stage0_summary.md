# Stage 0 Summary

- Mode: `full`
- Examples processed: 30
- Stage 0 pass: `true`
- Stage 1 started: `false`
- Correct: 4
- Wrong: 0
- Invalid: 0
- Truncated: 26
- Average generated tokens: 1987.97
- Median generated tokens: 2048.00

## Acceptance criteria

| ID | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | Deterministic faithfulness | PASS | exact generated-token and final-answer equality on smoke examples |
| 2 | Correct visual-token mapping | PASS | placeholder count equals processor grid-derived merged token count |
| 3 | Token/span alignment works | PASS | token, score, attention, decode, and span-range checks |
| 4 | Required descriptive signals recorded | PASS | modality mass, uncertainty, selected heads, and visual focus present |
| 5 | Resource use manageable | PASS | per-example output <= 134217728 bytes and requested run completed |
| 6 | Outputs reproducible and traceable | PASS | structured per-example inputs, generations, tokens, spans, arrays, validation, and config |
| 7 | MathVerse paired variants accessible | PASS | 788/788 complete problem groups |
| 8 | Qualitative timelines inspectable | PASS | diagnostic plots for 5 examples with spatial snapshots |

## Qualitative observations / hypotheses for later causal analysis

- Mean descriptive visual-attention mass was 0.0602 in the first generated-token quartile and 0.0461 in the last quartile.
- 30/30 examples contained at least two within-trajectory visual-attention peaks under the provisional mean-plus-standard-deviation diagnostic.
- The example-mean token-level correlation between visual-attention mass and entropy was -0.2232.

These are descriptive Stage 0 observations, not established mechanisms.

## Promising Stage 1 hypotheses

- Test whether early-versus-late descriptive differences survive causal visual-evidence interventions.
- Test whether repeated descriptive peaks align with changes in evidence demand rather than lexical visual-reference cues.
- Disentangle predictive uncertainty from evidence demand with controlled causal comparisons.

## Known limitations

- Eager language attention is required to observe exact attention probabilities.
- Attention summaries are descriptive, not causal visual-usage measurements.
- Reasoning spans are provisional rule-based segments.
- The selected 30–50 examples are an instrumentation subset, not a benchmark estimate.
- A 2,048-token safety cap can truncate repetitive trajectories; these are retained and reported rather than silently discarded.

Stage 0 stops here. Stage 1 was not started automatically.
