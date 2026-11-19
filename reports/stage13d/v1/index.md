# Stage13D — POST_EVIDENCE_MECHANISM_PARTIAL

**Neither mechanism met its confirmation gate.** The prospectively defined `PARTIAL` label reflects a positive but subthreshold semantic point estimate, not a confirmed mechanism. Derived content did not outperform the fresh baseline. Stage13A remains unchanged.

The approved study is complete. Exact24 scientific families and disjointtechnical4
were inherited from Stage13C. Source-only QC sealed23safe derived states and excluded
936 from semantic calls; it remains in the11-family MC buffer panel. Stage13A's
confirmed deployed4B post-evidence advantage is unchanged.

Semantic arm: 460 calls, 13/23 fully resolved families,
five fresh seeds per condition. Correctness rates below use the same complete-family
denominator. Technical missingness remains separate from errors; repetition is retained.

| Arm | Accuracy | Scoreable calls | Technical missing |
|---|---:|---:|---:|
| I_BASE | 86.15% | 113 | 2 |
| I_DUMMY | 83.08% | 106 | 9 |
| I_SHUFFLED | 81.54% | 109 | 6 |
| I_DERIVED | 84.62% | 110 | 5 |

Paired family contrasts (10,000 bootstrap draws; seed120220260929):

- Derived minus base: -1.54pp,95%CI[-16.92,+9.23]; positive/zero/negative families 3/9/1. Missingness bounds[-1.74,+4.35]pp.
- Derived minus dummy: +1.54pp,95%CI[-13.85,+13.85]; positive/zero/negative families 4/8/1. Missingness bounds[-3.48,+8.70]pp.
- Derived minus shuffle: +3.08pp,95%CI[-13.85,+18.46]; positive/zero/negative families 3/9/1. Missingness bounds[+0.00,+9.57]pp.

Semantic confirmation: **False**. Historical I−/T+ secondary overlaps:2; trace-specific derived rescues:0. Unresolved selected families:2. These were opened only after the primary inference seal.


Missingness bounds use all 23 safe families and assign missing calls their worst/best possible outcomes. They are finite-cohort bounds, not confidence intervals for the 13-family complete-case estimand. The 22 missing calls cluster across 10 families. Both selected historical overlaps are unresolved for the complete-case rescue criterion; zero confirmed rescues is not evidence of two failed rescues. All 13 complete families have verified-correct derived states, so the flawed-state comparison is not estimable.

Derived-correctness strata are descriptive, not causal error-propagation claims:

- ALL_VERIFIED_CORRECT: {'n_complete': 13, 'derived_accuracy': 0.8461538461538461, 'delta_dummy': 0.015384615384615385, 'interpretation': 'Descriptive, not causal error propagation'}.
- HAS_VERIFIED_ERROR: {'n_complete': 0, 'derived_accuracy': None, 'delta_dummy': None, 'interpretation': 'Descriptive, not causal error propagation'}.
- MIXED_OR_UNCLEAR: {'n_complete': 0, 'derived_accuracy': None, 'delta_dummy': None, 'interpretation': 'Descriptive, not causal error propagation'}.

Immediate buffer: 11 MC pairs; mean long−short gold margin -0.3438 nats/token,95%CI[-0.8068,+0.1222]. Positive families:3/11 (27.3%); top1 gold short:3/11,long:3/11. Signal confirmed:**False**.

Buffer validation passes12technical requests, including exact16/sourceL autoregressive
forced counts, native close and identical answer prefix, zero free tokens, no images,
and exact repeatability on all4short probes. Scientific MC letters are singleton
tokens scored from the same raw next-token logits, before temperature or penalties;
the physically forced first letter is bookkeeping, not a model prediction. Margins
were independently recomputed from saved token-level probabilities. Open-ended
technical probes never enter the scientific buffer denominator.

Source deductions are compact, source-grounded extractions, not exhaustive trace
annotation. Source errors are retained and labeled. Same-agent semantic/QC review
is not independent-rater reliability. The portability assay and same-checkpoint
buffer assay identify possible contributors; they do not fully decompose a hybrid
Thinking ON/OFF effect or establish that these mechanisms exhaust the advantage.

Resources:4.783333 allocatedGPUh; all allocations
released. No follow-on experiment launched. All prior Stage12/13 artifacts checked
against the prospective preservation manifest.

Exactly one recommendation: Preserve the supported component as secondary mechanism evidence and stop additional decomposition unless a cleaner hybrid ON/OFF model becomes available.

STOP.

[Full responses](responses.md)

- [stage13d_1_derived_state_priming](../../../outputs/stage13d/v1/figures/stage13d_1_derived_state_priming.png)
- [stage13d_2_family_semantic_effects](../../../outputs/stage13d/v1/figures/stage13d_2_family_semantic_effects.png)
- [stage13d_3_selected_rescue](../../../outputs/stage13d/v1/figures/stage13d_3_selected_rescue.png)
- [stage13d_4_buffer_margin](../../../outputs/stage13d/v1/figures/stage13d_4_buffer_margin.png)
- [stage13d_5_buffer_effect_distribution](../../../outputs/stage13d/v1/figures/stage13d_5_buffer_effect_distribution.png)
