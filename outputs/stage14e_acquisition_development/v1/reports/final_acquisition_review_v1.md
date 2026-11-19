# Final32-family evidence-acquisition evaluation

The Source-Premise Ledger did **not demonstrate improved acquisition** on the frozen32-family evaluation. Method selection was frozen before these outputs, and the96logical source judgments were sealed before opening new solver finals. This is the completed acquisition endpoint; downstream accuracy is reported separately after all solvers finish.

| Acquisition outcome | Original SAVA-style S | Ledger M | Same M target, no fresh helper image |
|---|---:|---:|---:|
| Assigned families |32|32|32|
| Accepted query / reader attempt |28|17|17|
| Useful new fact or valid reinspection |1|0|0|
| Already correctly established / given |14|10|7|
| Explicitly wrong task-critical statement |0|4|2|
| Unknown, ambiguous or incomplete |11|1|7|
| Irrelevant or mathematical rather than visual |2|2|1|
| No reader attempt |4|15|15|

Primary M−S = **−3.125 percentage points**, source-stratified paired family-bootstrap95%CI **[−9.375,0]**,4000draws,seed20261022. There are0paired gains and1loss. Useful yield conditional on an attempt is0/17 for M versus1/28 for S; assigned-family rates remain the primary denominator. The sole success is S family1277: partial reinspection of T's position on the bottom line where the small semicircles meet, addressing conflicting statements in the prefix. Neither condition recovered a complete previously unresolved source structure. No-image output is not genuine visual acquisition.

The0/32 method bootstrap interval[0,0] is degenerate and does not establish a zero population success rate. For scale only, the unstratified two-sided95%Clopper–Pearson upper bound at0/32 is10.89%; this is descriptive and does not replace the frozen source-stratified paired analysis. Unknown/absent statements were not labeled explicit visual errors.

## Stage-specific observations

**Demand and target selection.** Of S's28accepted targets,4were judged fully task-relevant,5partially relevant and19known, nonvisual or unhelpful. Of M's17accepted targets,0were fully relevant,9partially relevant and8unhelpful. These are condition-visible qualitative judgments, not an independently validated target-selection classifier. Object nouns and broad properties often omitted the binding needed to resolve the current problem: family865 needs disjoint corner overlaps and the exterior boundary of the rectangle union, not simply top-left vertex A; family869 needs actual graph edges, not a generic definition of connected component; family1486 needs the shaded boundary but the reader declared the supplied image unavailable.

**Transport.** S has2invalid targets and2legitimate NONE decisions, both consistent with already-established premises. M has12invalid ledgers,3legitimate NONE decisions, and17accepted queries. Two M NONE decisions are useful abstentions (2584,2885);1277 misses an unsettled premise. Invalid fallbacks are not useful abstentions. Seven rejected ledgers have a valid first eligible entry but another entry violates the whole-ledger contract. No alternative target was executed, so this cannot establish that weakening validation would improve acquisition. Five failures concern unsupported numbers; seven concern an ASSERTED_IN_PREFIX obligation citing no prefix span. Exact entries/reasons are in the transport audit.

**Source reading.** M's four explicit errors concern943(tape counts/ranges),62(all rows asserted to have five bricks),784(the horizontal5 rebound to a vertical segment), and1829(column/supporting relation errors despite a correct addition headline). Correct-looking read_value alone is insufficient when its supporting task-critical binding is wrong. All17 M reads used the actual full original image; no crop/localization operation is part of this selected method. It is therefore inappropriate to describe these outcomes as failed ROI localization.

**Timing and source opportunity.** Source-only QC classified9prefixes as already established,13as tentative and10as unresolved. M recovered useful evidence in0/9,0/13 and0/10respectively; S's1success is within the tentative13. The fixed512checkpoint sometimes precedes a concrete obligation and sometimes follows sufficient evidence. Timing was not experimentally varied, so no causal timing effect is identified. A textual mention remains distinct from confirmed acquisition.

## Interpretation and limits

The development signal (3/24partial useful reinspections versus0/24matched initial candidate) did not reproduce on this separate32-family evaluation. The observations support a bottleneck in obtaining a precise, task-critical source binding and then reading it reliably. They do not establish a single cause: target relevance, whole-ledger rejection, reader errors and checkpoint opportunity all contribute to observed attrition.

This is a one-shot method evaluation, not untouched benchmark confirmation. Families exclude all300Stage14D-0audited families and all72SAVA families but have prior benchmark exposure.32unique conservative image families were selected source-only in frozen hash order and answer-format×structured-source strata. One AI reviewer inspected original pixels and offline source references; no independent human annotation. Source-reference uncertainty, partial coverage and condition visibility remain limitations. Final-answer changes cannot be interpreted as acquisition improvements without corresponding source-level evidence.

Exact artifacts: annotations/evaluation_source_review_v1.json, annotations/evaluation_labels_v1.tsv, analysis/evaluation_acquisition_results_v1.json, analysis/evaluation_transport_diagnostics_v1.json. All previous failures, outputs, labels and selection records are preserved. No method revision or additional test cohort follows this result.
