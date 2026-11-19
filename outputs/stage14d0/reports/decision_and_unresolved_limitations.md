# Stage14D-0 decision and unresolved limitations

**COMPLETE / STOP.** All six authorized audit phases are complete. No model inference, GPU allocation, LLM judge, external annotator, new dataset, or E*-conditioned reasoning read was used. The old Stage14D 1,674 continuations and 375 GPU-hour proposal remain on hold. This audit does not close Stage14C-V.

## What the evidence changes

The paired source-selected estimate does not establish a Thinking advantage in explicitly stated source-fact fidelity: T−I error rate −3.60 percentage points, 95% family-bootstrap interval [−7.86, +0.40], 131 eligible paired families. The audit finds entity-binding and structural errors in both models, alongside correct facts that do not lead to a valid solution. It therefore supports testing evidence verification and subsequent premise use together. It does not justify an acquisition-only explanation or the old exhaustive continuation grid.

Exactly one recommendation is documented in the [bounded D1 proposal](stage14d1_bounded_feasibility_proposal.md). That study has not been launched. There is no additional autonomous action after this report.

## Reliability and chronology

- One main AI reviewer authored semantic source/trace judgments. There were zero independent human reviewers and no second independent semantic rating. Agreement and human reliability are unavailable. Automated span, join and arithmetic checks do not validate semantic judgments.
- Display masking is not independent blinding. Earlier project work, recognizable trace style and same-agent memory may reveal model identity, source facts or outcomes. The original annotation filename `passA_native_claims_blinded.jsonl` is inherited from the plan; it must not be read as an independence certificate.
- Source-before-persistence exceptions concern 2961 T, 2006, 2714 and 2390. The last 732 characters of 1841 T were read and saved in the same execution step. No pristine blinded sequence is claimed for these records. Source inspection corrected the initial Pass A suspicion about printed labels 1, 3 and 9 in 2547; the original note remains preserved.
- All native strings were reviewed, using lossless repeated-paragraph reconstruction for some cap tails. The 2,061 selected excerpts are not an exhaustive utterance inventory. Broad excerpts can contain several source facts and derived statements.
- Unicode character offsets and quoted text are authoritative. Token offsets are missing. First-use offsets are absent for 1,735 I and 1,739 T subfacts out of 1,883 valid references. A qualitative use judgment does not certify the earliest use. Missing events are unobserved, not time zero.
- Three Thinking correction candidates lack an ordered explicit before/after span pair and are excluded from the anchored correction count. Even anchored correction is text-visible revision, not independently verified visual reacquisition.
- Primary states summarize the last observable assertion in the whole response, including final exposition. Thinking tag boundaries are exact; Instruct answer regions are less uniform and capped uncommitted responses have no invented final boundary. The pre-answer-anchor sensitivity is not an exhaustive reannotation of all pre-answer text.

## Reference and sampling limitations

- Source-reference problems in 604, 2869 and 276 withhold four subfacts from model correctness denominators. These are separate D0 annotations; historical E*, source files, scores and headline results remain unchanged. See the [closure QC ledger](../inventory/source_QC_and_Estar_version_ledger_closure_v1.jsonl).
- Source-faithful text can expose a structure or task-relevant count more explicitly than the image. It does not establish answer-safety, task equivalence, or absence of a representation effect. Minimal E* need not exhaust relevant visual truth.
- R comprises 150 source-stratified families from the 1,000 eligible frame, with documented inclusion weights. Its interpretation is restricted to that eligible frame. F comprises 150 outcome-enriched discovery families. Pooled counts are not population prevalence.
- Families 751 and 1744 have geometry-equivalent source content. Their frozen IDs remain intact; a merged-cluster sensitivity is supplied. Do not claim 300 independently distinct geometries.
- Required parents, subfacts, selected claim spans and families are different units. Evidence types overlap. Intervals cluster by family and do not account for semantic annotation error.
- Source-QC-valid references can still have ambiguous native matches. NOT_STATED and VAGUE_OR_UNMATCHABLE are neither incorrect evidence nor absent internal knowledge. Nineteen paired both-wrong subfacts have unresolved wrong-identity comparisons.

## Interpretation bounds

Different checkpoints, sampling recipes, caps and trace lengths prevent a causal equal-compute attribution to Thinking. A correct assertion may be inferred rather than visually retrieved. E* rescue is an association with a changed input representation, not mediation. The 15 I and 20 T native-wrong cases with all required facts last stated correctly are coverage flags, not automatically pure downstream failures. Other visual claims can still be wrong.

The audit is a completed, retrospective, single-AI analysis made inspectable through original images, full native traces and exact annotation provenance. Strong mechanistic claims require independent source/semantic checking and a separately authorized causal experiment.

**STOP — no follow-on experiment executed.**
