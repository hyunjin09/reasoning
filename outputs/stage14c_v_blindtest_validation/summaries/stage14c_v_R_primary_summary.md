# Stage14C-V R panel — reviewed primary result

All1,800 planned generations are saved and hash-verified. There are no technical missing outcomes. Response-only adjudication and fixed/flagged scoring QC cover198 outputs; two Instruct R2 cap-hit responses remain unscorable. Review was performed by the same agent and does not establish independent inter-rater reliability.

| Frozen evidence format | Instruct accuracy | Thinking accuracy |
|---|---:|---:|
| R0: original format |190/300 =63.33%|191/300 =63.67%|
| R1: typed structured fields |123/300 =41.00%|177/300 =59.00%|
| R2: entity-explicit prose |245/298 =82.21%|277/300 =92.33%|

The preregistered primary Instruct R1−R0 effect is−22.33percentage points (95%CI−30.33to−14.33):49families improve and116regress. Structured formatting worsens performance, opposite the predicted clarity benefit. Among254native-correct families, regression increases17.32points (CI8.66to25.98); rescue among46native-wrong families falls50.00points (CI−69.57to−30.43).

The separately preregistered secondary prose format improves Instruct by18.46points on298common scored pairs (CI13.76to23.49;58improve,3regress). All300-family unresolved-outcome effect bounds are18.33to19.00points. Thinking R2−R0 improves28.67points (CI23.00to34.33;91improve,5regress). Thinking R1−R0 is−4.67points (CI−12.00to2.67).

| Model/format | Native-wrong → correct | Native-correct → wrong | Unscorable |
|---|---:|---:|---:|
| Instruct R0 |39|103|0|
| Instruct R1 |16|147|0|
| Instruct R2 |39|46|2|
| Thinking R0 |49|68|0|
| Thinking R1 |47|80|0|
| Thinking R2 |82|15|0|

R2 reduces supply-induced regression, but Instruct still has more scored regressions than rescues. Relative to native performance, its paired net effect is−2.35points on298scored families (CI−8.39to3.69), with planned300-family bounds−3.00to−2.33points. Thinking R2 has net+22.33points (CI16.67to28.00).

All intervals use10,000 paired-family bootstrap draws, frozen seed20261009; they are unadjusted95% intervals, not simultaneous intervals. Instruct R2's marginal accuracy excludes its two unscorable responses; its300-family accuracy bounds are81.67–82.33%.

Fresh R0 agrees with historical correctness on299/300Instruct and238/300Thinking families, with net accuracy changes+0.33and−0.67points. Historical native and original supplied-evidence outcomes remain immutable contextual references. The old104Instruct regressions are not relabelled as the new103.

These results support strong representation/interface sensitivity for this selected line-intersection cohort: equivalent formats can help or harm. They do not isolate naming, length, salience, or elicited reasoning as the cause, and do not establish a general cross-task mechanism. R2 also changes response behavior: Instruct strict native answer-only formatting is185/300versus300/300inR0/R1. This is a format-package effect, not a pure formatting-component mechanism. No diagnostic cases were selected before sealing the R primary and companions.

Operational provenance: recovered R2 tail calls used fresh engines after the approved timeout repair and subsequent user-requested parallelization; frozen wave membership, prompts, caps, seeds and model recipes were preserved. Eight completed primary anchor responses were retained and their context replays excluded. Prefix replay validation does not establish full-sequence bitwise identity.

R is complete; C and final cross-experiment closure remain. C tests a separate elicitation contract and cannot establish mediation of R effects. Its prompts and scoring remain frozen.

[Primary analysis](../analysis/representation_primary.json) · [Native transitions](../analysis/r_native_transition_tables.json) · [Primary seal](../audit/R_primary_seal_v1.json)
