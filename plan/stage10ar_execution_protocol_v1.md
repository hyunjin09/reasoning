# Stage10AR prospective execution definitions

Authority: stage10ar_causal_phase_transition_localization_plan.md; persistent
user authorization of up to8 GPUs. Freeze before any Stage10AR intervention.

## Cohort and semantic annotation

Use only32 existing primary images and64 native Stage9A.5 FULL trajectories.
Prefer color on even image IDs and shape on odd; use the other query if FULL is
incorrect/invalid or the required semantic progression is unavailable. Correct
FULL is explicitly authorized eligibility. Do not use Stage10A intervention
effects to choose queries or anchors. Prior stage aggregate conclusions are
known, but no new outcome or prior per-item intervention result selects this design.

Select12 color and12 shape by SHA256("stage10ar-v1-920260927:"+image_id) within
attribute. Freeze remaining8 as reserve in the same hash order. No replacement
after intervention outcomes. This estimates successful-reasoning computation,
not population accuracy or prevalence.

A0: empty generated reasoning prefix after unchanged multimodal prefill.
A1: first explicit task-relevant visual observation; positive identification or
attribute-based exclusion of an object both qualify. A definition of a shape or
question repetition does not. The answer must remain underdetermined.
A2: earliest clearly separable second distinct evidence unit while the answer
remains underdetermined. Positive and negative attribute observations count;
repeated descriptions of the same object do not. Mark unavailable if the second
unit closes the inventory or no intermediate accumulation point exists.
A3: first closed, source-correct textual evidence sufficient to determine the
answer: an explicitly scoped target inventory, a closed full-scene enumeration
introduced as checking/listing all shapes, an exhaustive remainder exclusion,
or a correct aggregate fact. Do not assume unmentioned objects absent merely
because a partial list already matches the true count. Tentative questions and
unresolved contradictions do not close evidence. Explain the prefix-only
inference and why the preceding candidate remains incomplete for each image.
A4: first asserted task-critical aggregate fact/count, including explicit
singleton/only-one statements. Exclude ordinals, open enumeration subtotals,
questions and metalinguistic definitions. A3 may equal A4; do not force a gap.

Seal exact native character/token boundaries, source fact, rationale, evidence
units and A2 missingness. A1/A2 prefixes may include the immediately following
comma/conjunction that visibly keeps an enumeration open; never include the
next object's content. Snap only through whitespace at native token boundaries.
Check A0<A1<A3<=A4, and A1<A2<A3 whenever A2 exists. If this taxonomy cannot be
annotated honestly for a preferred query, assess its alternate before selection.

## Runtime and reuse

Same pinned Qwen3-VL-4B-Thinking, BF16, TF32 off, greedy, native Thinking,
DeepStack, eager-language/SDPA-vision, original preprocessing and512 total
generated-token budget. No prompt or cap change. Native final-channel scoring
only; missing final is incorrect. Review ambiguous finals before joining gold.

For n>0, reproduce the exact native prefix, preserve its cache, and mask future
generated-query image keys in all36 layers at cutoff n-1 (first query P+n-1).
A0 preserves prefill, whose logits supply the first output token. Block all
subsequent generated-token queries at absolute P onward, matching the existing
Stage9A.5 ZERO intervention. This is not removal of image input or prefill-derived
state, and does not erase the first-token prediction. Fresh A0 text replay has
the original question/options and native Thinking template, with no generated
prefix and no image or copied state.

Reuse already completed outputs only after cohort/anchors are sealed and exact
model/prompt/token-prefix/backend/cap/mask semantics match. Internal equal-anchor
aliases execute once. Reuse Stage9A.5 ZERO for A0 image-off where exact; reuse
Stage10A text-only/image-off anchor rows where identical. Preserve originals,
receipts and hashes; normalize schemas only in new provenance-linked artifacts.
Do not rerun the prior full text-edit panel.

## Primary inference and gates

Image is the independent unit, one query/image, equal weight,4,000 paired
bootstrap draws, seed920260927. P1=image-off(A4)-image-off(A0);
P2=text-only(A4)-text-only(A0); P3=image-off(A3)-image-off(A1);
P4=text-only(A3)-text-only(A1). Report ordinary95% intervals plus Bonferroni
family-wise95% intervals across four endpoints: each98.75% percentile interval
uses quantiles .00625 and .99375. The latter govern primary uncertainty.

Main gate: all four points>0; P1 and P2 adjusted lower bounds>0; all four
directions>0 in both color and shape; no direction flips to<=0 after deleting
one image or one predeclared small source-count/attribute-target group (group
sizes2–6). Report these robustness checks rather than selecting exclusions.
Existing Stage10A causal-text influence applies to the same native4B aggregate
count regime; explicitly report cohort/query overlap and correct-fact evidence.
No new primary endpoint is introduced after outcomes.

A2 analyses are secondary and use only complete A2 images for paired contrasts;
the central plot labels per-anchor denominators and includes a complete-anchor
sensitivity. H is the first available anchor with both assays correct. Report
later reversals, missing H and distance from A3; do not infer continuity between
untested anchors.

## Optional work and stop

Interpret section20's specific reserve rule as the narrow exception to section19's
ordinary STOP: only all four positive points, unresolved adjusted uncertainty,
both-attribute and leave-out direction robustness, and no validity failure can
trigger the frozen8 reserve. A directional failure stops immediately. Run the
same conditions and combine all32 equally; no further extension or anchor search.

The optional A3 edit requires the final main gate plus A3 strictly before A4 in
at least half the primary cohort and12 prospectively eligible evidence edits.
Select those12 during L0 by semantic edit clarity then fixed hash (balance when
feasible), freeze original/CF/sham text before outcomes. If fewer than12 valid
minimal edits exist, record not feasible, without inventing an edit. This is
optional and does not gate the main localization claim.

Outcome A requires the entire main gate. Otherwise report which visual/text
contrasts fail or remain uncertain, map B/C/D transparently, and give the plan's
single non-A recommendation. A positive early-to-late pair alone cannot override
failed evidence-resolution endpoints. No automatic next stage.

## Compute

At most240 primary logical continuations; fewer with unavailable A2 or aliases.
Up to8 available authorized A6000 GPUs, one finite worker/GPU,4CPU/30G each,
project scheduler and Slurm only. Target<3 GPUh; projected>5 before optional
work requires stop/simplification. Reuse exact evidence; preserve failures and
account allocated GPU time, including startup and validation. Release GPUs as
soon as queues finish. CPU analysis and figures use CPU Slurm if substantial.
