# Stage 2C Summary

## Outcome

Stage 2C is complete as an artifact-only temporal measurement audit. It used 50 completed-correct examples and 70 localized evidence events; no model inference, causal intervention, counterfactual edit, activation patching, or Stage 3 experiment was run.

Recommendation: **GO — Counterfactual content sensitivity**, subject to manual validation of each future edit. This recommendation is not executed here.

## Measurement convention

Stored attention row `t` is the row whose logits predict generated token `y_t`; for `t>0`, its query token is `y_(t-1)`. The primary acquisition-timing view is prediction-aligned (`row t -> y_t`). The semantic-alignment audit separately uses the processed-token shift (`y_t -> row t+1`). Historical arrays were not changed.

The primary signal is attention mass summed over a manually mapped ROI and divided by the number of ROI visual tokens. Raw ROI mass and ROI share conditional on total visual attention are also retained. Fixed E0/E1/E2 windows are ±64 tokens.

## Cohort and annotation

The cohort combines all 20 manually accepted Stage 2A examples with 30 additional completed-correct examples screened without viewing ROI attention. Three pre-attention exclusions are preserved. E0 is the first relevant entity span, E1 the completion token of the earliest semantic span making the fact explicit, and E2 the first downstream span using it. All 70 ROI mappings passed manual overlay review.

## Descriptive temporal results

Timing categories: `T1_pre_mention_lead=3, T2_mention_centered=58, T3_post_mention_lag=2, T4_repeated_mention_locked=4, T6_no_clear_temporal_structure=3`.

Mean ROI-density by region: PRE `0.000374443`, ENTITY `0.000764329`, FACT `0.000861118`, POST `0.000328887`, USE `0.000206652`. Bootstrap intervals and full distributions are in `event_aligned_statistics.json`.

The event-balanced semantic audit contains `67` evidence items with later references. Later-reference and matched-nearby processed-token means are `0.00039406320994986055` and `0.000251627615974662` respectively. These are descriptive alignment checks, not interventions.

## Stage 2B temporal re-audit

`8/10` target A/B intervention windows began after the corresponding E1. Those windows tested direct visual re-access after the fact was already explicit in the CoT, not initial evidence acquisition. This materially narrows the interpretation of the Stage 2B null result.

## Counterfactual readiness

The best-effort pool contains `38` evidence items across `26` examples, exceeding the target of 20. No edited image was generated. A later Stage 3A would still require manual edit validation, same-text controls, and a separately approved plan.

## Limitations

E0/E1 are semantic-span annotations and can be wider than a single word. The stored visual-focus tensor is averaged across language layers and heads, so Stage 2C cannot localize layer/head timing. Attention can reflect acquisition, lexical/semantic alignment, persistent routing, or other processes. Correlation and temporal precedence do not establish causal visual use, handoff, or memory.

## Scientific boundary

**Attention is descriptive evidence, not causal evidence.** Low ROI attention does not prove visual memory; high or early ROI attention does not prove fresh evidence acquisition. Stage 2C stops here.
