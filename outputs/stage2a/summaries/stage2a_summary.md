# Stage 2A Summary

## Outcome

Stage 2A is complete. The Stage 2B recommendation is **CONDITIONAL GO** for a five-example controlled pilot only. No new model inference and no causal intervention were run.

## Paired VI/VD discovery

The 36 both-correct VI/VD pairs do not form one uniform manipulation:

- 13 clear text-to-image information shifts;
- 22 no effective visual-information shifts;
- 1 mixed redistribution.

The 13 clear pairs were analyzed as the primary within-problem stratum with 20-bin normalized token progress, early/middle/late windows, token-weighted semantic aggregation, paired bootstrap intervals, paired effect sizes, Wilcoxon tests, and Holm adjustment.

The main result is mostly null and heterogeneous. VD did not show a reliable global change in visual mass (`+0.000711`, 95% CI `[-0.005901,+0.005797]`), visual density (`-0.0000452`, CI crossing zero), previous-reasoning density, entropy, peak rate, or trace length. A prompt-density increase is largely denominator-sensitive because VD removes prompt tokens when facts move into images; total prompt mass was not reliably different.

Visual-focus turnover was directionally higher in VD (`+0.01833`, Holm-adjusted `p=0.0269`) but strongly dominated by base problem `139`; excluding it reduces the mean to `+0.00186`. This is a suggestive spatial redistribution statistic, not causal evidence of visual use.

## Evidence-ROI discovery

Thirty completed-correct trajectories were screened without attention. Twenty were accepted and annotated with two spatial evidence items, reasoning-demand spans, mapped visual tokens, and candidate future windows. The 40 ROIs contain 2–70 merged visual tokens (median 15). All 20 mapping overlays passed manual inspection.

Descriptive density alignment in the frozen subset was:

- 10 expected A→B-like shifts;
- 6 persistent B;
- 1 persistent A;
- 3 no clear selectivity;
- 0 simultaneous and 0 reverse under the documented threshold.

Five expected-shift examples also have high-confidence semantic/ROI annotations: `699, 739, 2799, 3044, 3764`. These are the only examples recommended for an initial later causal pilot. Negative and ambiguous patterns were retained rather than filtered away.

## Scientific interpretation

The paired analysis does not support a simple model-wide increase in visual allocation when facts become image-only. The evidence-ROI analysis does show that some individual trajectories have spatial focus differences aligned with manually annotated evidence stages, but this pattern is not universal and can coexist with persistent or diffuse focus.

These results motivate a narrow test of evidence-identity-specific dependence, with same-size irrelevant-ROI, evidence-identity, timing, and no-intervention controls. They do not establish that an attention rise is fresh evidence acquisition, that low attention reflects stored visual memory, or that the model enters causal LOOK/THINK states.

## Deliverables

- [`manual_pair_audit.md`](../manual_pair_audit.md)
- [`paired_analysis.md`](../paired_analysis/paired_analysis.md)
- [`paired_statistics.json`](../paired_analysis/paired_statistics.json)
- [`evidence_annotations.jsonl`](../evidence_subset/evidence_annotations.jsonl)
- [`evidence_subset_report.md`](../evidence_subset/evidence_subset_report.md)
- per-example ROI maps, curves, timelines, and candidate windows in [`evidence_subset/examples/`](../evidence_subset/examples/)
- [`stage2b_recommendation.md`](stage2b_recommendation.md)
- [`stage2a_acceptance.json`](stage2a_acceptance.json)

## Boundary

Raw attention and ROI focus remain descriptive evidence. Stage 2B was not started.
