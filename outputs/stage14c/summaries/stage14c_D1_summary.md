# Stage14C bounded D1 evidence-elicitation diagnostic

All 600 frozen calls and 1,200 explicit same-agent source/response reviews are complete. The 100 families per task were selected by the frozen source-only hash before new outcomes. This is a descriptive secondary assay, opened after the primary summary was sealed. No prompt, target, membership or generation recipe was tuned after seeing responses.

Instruct is scored on its committed response; Thinking on the committed body after the last `</think>`. Recall requires the frozen value, source identity, relation and qualifiers. Correct answers alone receive no evidence credit. Exact atom recovery requires all of its source units. Accurate partial observations are retained among accurate unmatched assertions, but do not receive full-unit credit. Source unit maps are identical across variants.

| Task/model | Scored / selected | Full E* recovery | Exact atom recall macro % | Subfact recall macro % | Full recovery bounds over 100 % |
|---|---:|---:|---:|---:|---|
| math/I | 97/100 | 20 | 24.48 | 35.11 | [20.00, 23.00] |
| math/T | 100/100 | 31 | 34.83 | 45.86 | [31.00, 31.00] |
| MMStar/I | 96/100 | 38 | 39.58 | 46.90 | [38.00, 42.00] |
| MMStar/T | 99/100 | 53 | 53.54 | 63.55 | [53.00, 54.00] |
| BlindTest/I | 100/100 | 0 | 0.00 | 0.00 | [0.00, 0.00] |
| BlindTest/T | 100/100 | 0 | 0.00 | 0.00 | [0.00, 0.00] |

Macro means weight families equally; these are descriptive point estimates, with no confirmatory significance claim. The bounds treat unresolved probes as no/full recovery without changing their recorded status.

| Task/model | Exact atoms / atoms (micro) | Recovered units / units (micro) | Structured-unit recall macro / micro % | Targeted precision macro % (families with assertions) | Targeted precision micro |
|---|---:|---:|---|---|---|
| math/I | 36/140 | 238/779 | 36.22 / 30.53 | 30.53 (93) | 238/663 = 35.90% |
| math/T | 48/143 | 344/804 | 44.21 / 42.52 | 46.29 (99) | 344/589 = 58.40% |
| MMStar/I | 46/118 | 218/605 | 44.03 / 34.62 | 62.02 (77) | 218/409 = 53.30% |
| MMStar/T | 61/121 | 344/631 | 61.43 / 53.68 | 63.93 (98) | 344/471 = 73.04% |
| BlindTest/I | 0/100 | 0/500 | 0.00 / 0.00 | undefined (0) | 0/0 = undefined% |
| BlindTest/T | 0/100 | 0/500 | 0.00 / 0.00 | 0.00 (9) | 0/24 = 0.00% |

Targeted precision is the fraction of asserted direct-image facts matching complete required units. It is not ordinary factual accuracy: accurate irrelevant or partial facts remain in its denominator; derived statements and marked uncertainty are excluded. An empty assertion denominator stays undefined. Conjunction granularity and strict compound-unit matching limit comparability across tasks.

## Recovery and main native-to-E* transitions

| Task/model | Probe recovery | Correct→correct | Correct→wrong | Wrong→correct | Wrong→wrong | Main pair unresolved | Total |
|---|---|---:|---:|---:|---:|---:|---:|
| math/I | FULL | 14 | 2 | 1 | 1 | 2 | 20 |
| math/I | PARTIAL | 9 | 3 | 10 | 3 | 6 | 31 |
| math/I | NONE | 16 | 1 | 16 | 9 | 4 | 46 |
| math/I | UNRESOLVED | 0 | 0 | 1 | 1 | 1 | 3 |
| math/T | FULL | 24 | 1 | 5 | 1 | 0 | 31 |
| math/T | PARTIAL | 16 | 0 | 17 | 2 | 0 | 35 |
| math/T | NONE | 17 | 2 | 12 | 3 | 0 | 34 |
| MMStar/I | FULL | 33 | 2 | 0 | 1 | 2 | 38 |
| MMStar/I | PARTIAL | 13 | 2 | 4 | 0 | 0 | 19 |
| MMStar/I | NONE | 27 | 3 | 6 | 2 | 1 | 39 |
| MMStar/I | UNRESOLVED | 1 | 0 | 2 | 0 | 1 | 4 |
| MMStar/T | FULL | 47 | 2 | 1 | 3 | 0 | 53 |
| MMStar/T | PARTIAL | 17 | 1 | 4 | 2 | 0 | 24 |
| MMStar/T | NONE | 14 | 2 | 6 | 0 | 0 | 22 |
| MMStar/T | UNRESOLVED | 1 | 0 | 0 | 0 | 0 | 1 |
| BlindTest/I | NONE | 51 | 34 | 12 | 3 | 0 | 100 |
| BlindTest/T | NONE | 42 | 29 | 18 | 11 | 0 | 100 |

Examples of the assay distinction: math Instruct has 16 native-wrong→E*-correct families with no complete probe unit, but also one with full probe recovery; math Thinking has five rescues with full probe recovery. These are associations across separately prompted calls. They do not show what the original native solver internally knew. Full unit recovery is also not equivalent to a sufficient or correct mathematical solution.

## Validity limits and preserved negative evidence

- BlindTest: 100/100 Instruct committed bodies are bare brace-enclosed answers. Thinking has 91/100 bare answers and nine prose responses. None recovers a complete frozen geometry unit. Eleven correct partial assertions and 13 contradictory assertions remain in the Thinking review records. This is failure of demonstrated recovery under this elicitation/scoring contract, not evidence of zero internal visual knowledge. The unchanged native question includes an answer-only instruction after the evidence-probe instruction; this conflict is a plausible elicitation contributor, not a tested cause. No repair or rerun was performed.
- Six Instruct probes hit the frozen cap (three math, three MMStar) and remain unresolved; no Thinking probe hits its cap. MMStar:997 contributes an additional source-QC unresolved probe for each model, because the frozen plant/horse arrow was reversed. Targets and main results were not rewritten.
- Numerical chart approximations that lack the frozen target precision, counts without spatial locations, and partial object descriptions remain explicit partial observations. Low complete-unit recall cannot by itself establish an acquisition failure.
- Same-agent two-pass review is auditable but does not provide independent inter-rater reliability. Review-pass differences and original judgments remain preserved. Source-only two-pass QC is not infallible.
- No D2/D3, hidden-state probe, source-grounded decoding, lookback intervention or new benchmark was run.

Raw outputs: `../raw/optional_diagnostics/`; per-response annotations: `../scoring/D1_pass1/` and `../scoring/D1_pass2/`; complete metrics and crosstabs: `../analysis/optional_diagnostics.json`; joined rows: `../analysis/D1_joined_outcomes.jsonl`; seals: `../audit/D1_scoring_seal.json` and `../audit/D1_analysis_seal.json`.
