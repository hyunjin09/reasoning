# Stage10AR — Causal phase-transition localization

Completed 2026-09-27T12:22:54.654526+00:00. **Outcome A: the prospectively frozen main localization gate passes. STOP.**

Within24 selected successful Qwen3-VL-4B-Thinking counting trajectories, direct
image-token access becomes less necessary while the generated text becomes more
sufficient as the annotated evidence is resolved. This is a paired, bounded
functional result under the frozen512-token budget, not a universal token boundary,
benchmark-population estimate, or proof that every trajectory passes through a
visual-dependent state.

## Design and execution

- Same controlled32-image corpus and64 native FULL traces; no regenerated baseline.
-24 primary independent images,12 color/12 shape, one correct native FULL query/image.
  Parity-preferred query with correctness/semantic eligibility fallback; fixed
  SHA256("stage10ar-v1-920260927:"+image_id) order within attribute.
- Eight reserve images remain unused. Correct-FULL conditioning was explicitly
  authorized for this study; it differs from Stage10A's earlier cohort.
- A0 empty reasoning; A1 first observation; A2 partial accumulation; A3 first complete
  textual evidence; A4 explicit aggregate count. All32 annotations, source facts,
  exact token boundaries and12 optional edits were sealed before new intervention
  outputs. A2 is unavailable on image006_color and image024_color:22 complete cases.
- A3 strictly precedes A4 on21/24; they coincide on image000_color, image007_shape,
  and image024_color. Equal-anchor aliases are not additional observations.
-236 logical primary assays,230 distinct continuations:166 new,64 exact old reuses,
  six aliases. Optional36 logical assays reuse12 primary originals and run24 edits.
  Total190 new scientific continuations. All historical receipts remain immutable.
- Native4B Thinking revision1de27d8c51f12e819435303b9e84c4e25ba8401e; BF16, TF32 off,
  greedy, DeepStack, eager language/SDPA vision,512 total generated tokens.

Image-off preserves exact native prefix/cache and masks future generated queries
to image keys in all36 layers. At A0, multimodal prefill and its first-token prediction
remain intact, matching Stage9A.5 ZERO. Fresh text replay uses only the original
question/options and native reasoning prefix, with no image, original K/V or copied
hidden state. Later anchors consume part of the same512-token budget.

Three disjoint A0 validation cases passed exact prefill/logit/first-token parity,
ZERO-versus-cached-resume equivalence and clean image-free A0 replay. Eight earlier
positive-prefix validations were hash-verified and reused. Every newly reconstructed
native prefix matched its frozen token IDs. See [validation](audit/technical_validation.json),
[manifest](audit/primary_manifest.json) and [specification](stage10ar_phase_localization_spec.md).

## Primary inference

Image-equal paired inference,4,000 bootstrap draws, fixed seed920260927. Four primary
contrasts use98.75% marginal percentile intervals (Bonferroni family-wise95%). The
ordinary95% intervals are also retained. Positive/negative counts are paired images.

| Endpoint | Effect (pp) | Ordinary95% CI | Family-wise95% CI | Positive / negative / tied |
|---|---:|---|---|---|
| P1: image-off A4−A0 (necessity decrease) | +29.17 | [12.50, 45.83] | [8.33, 54.17] | 7 / 0 / 17 |
| P2: text-only A4−A0 | +95.83 | [87.50, 100.00] | [83.33, 100.00] | 23 / 0 / 1 |
| P3: image-off A3−A1 | +41.67 | [20.83, 62.50] | [16.67, 66.67] | 10 / 0 / 14 |
| P4: text-only A3−A1 | +45.83 | [20.83, 66.67] | [12.50, 75.00] | 12 / 1 / 11 |

All four points and adjusted lower bounds are positive. Both attribute subsets
have all four directions positive; no direction disappears when deleting a single
image or a predeclared small source-count/attribute-target group of2–6 images.
Subgroup intervals remain wide and are not each separately significant. Complete-A2
sensitivity preserves all four adjusted-positive contrasts; literal raw extraction
and sealed review give identical primary correctness.

| Attribute | n | P1 (pp) | P2 (pp) | P3 (pp) | P4 (pp) |
|---|---:|---:|---:|---:|---:|
| color | 12 | 33.33 | 100.00 | 50.00 | 58.33 |
| shape | 12 | 25.00 | 91.67 | 33.33 | 33.33 |

## Anchor profiles and completion behavior

FULL is correct for all24 selected images. Nᵥ=1−image-off accuracy; Sₜ=text-only
accuracy. Missing finals are incorrect under the frozen extraction/cap policy.

| Anchor | n | Image-off correct | Nᵥ (%) | Text-only correct / Sₜ (%) | Empty final: image-off / text-only |
|---|---:|---:|---:|---:|---:|
| A0 | 24 | 17/24 | 29.17 | 0/24 / 0.00 | 3 / 24 |
| A1 | 24 | 13/24 | 45.83 | 8/24 / 33.33 | 8 / 2 |
| A2 | 22 | 13/22 | 40.91 | 9/22 / 40.91 | 9 / 0 |
| A3 | 24 | 23/24 | 4.17 | 19/24 / 79.17 | 1 / 2 |
| A4 | 24 | 24/24 | 0.00 | 23/24 / 95.83 | 0 / 1 |

The population profile is not globally monotonic: necessity rises from A0 to A1
before falling sharply by A3/A4. The frozen early/late and evidence-resolution
contrasts, rather than an assumed monotone curve, define success. The A2→A3 secondary
paired shifts on22 images are visual +36.36pp
[18.18, 59.09] and text +36.36pp
[13.64, 59.09] (ordinary95% intervals).

All24 fresh A0 runs have empty finals at512 tokens; P2 therefore includes the
ability to finish, not just correctness conditional on completion. Fifty logical
primary rows have no final answer; all were reviewed before source gold was joined
for scoring. Another image-off A4 run emits a correct final at the cap without EOS.
No answer was rescued from an unfinished scratchpad. Censoring and evidence loss
cannot be separated by these primary assays; no longer-cap repair was authorized.

![Central joint profile](figures/figure2_phase_transition.png)

## Per-image state

An earliest jointly correct state H exists for23/24 images.
Distribution: A0=0, A1=4,
A2=3, A3=13, A4=3.
Nineteen/24 images (19/23 identifiable) have H at A2–A4, at/adjacent to A3.
Image013 has H=A1 but reverses at A2 and A3 before recovering at A4. Image017
has no joint-success H. These secondary states do not establish a continuous or
permanently stable phase between measured anchors.

## Optional earlier text-carrier check

The main gate passed and21/24 A3 anchors precede A4, opening the prospectively sealed
12-image subset (5 color/7 shape). Original A3 continuations were reused exactly;
minimal CF/sham edits were retokenized before primary outcomes. The CF adds one
asked-class object; sham preserves the evidence semantics. All conditions are
fresh image-free continuations with the same total budget.

Secondary signed score is+1 for following the edited count,−1 for following the
original count,0 otherwise (including no final). Paired image-bootstrap effects:
CF−original **1.000 [0.333, 1.583]**;
CF−sham **1.333 [0.833, 1.750]** (ordinary95% intervals).

| Condition | n | Follows original | Follows counterfactual | No final |
|---|---:|---:|---:|---:|
| original | 12 | 8 | 3 | 1 |
| counterfactual | 12 | 2 | 9 | 1 |
| sham | 12 | 10 | 1 | 1 |

This optional result is secondary and does not revise the primary gate. Edits are
local: earlier repetitions/subtotals remain and can conflict with the changed
inventory clause, so this is not a fully globally consistent rewritten prefix.
It is bounded evidence about causal use of the selected complete inventories,
not a new full text-edit/deletion panel or a text-versus-image dominance test.
The edited count is followed on9/12 CF runs, versus3/12 originals and1/12 shams;
the positive paired contrasts support causal usability of the earlier evidence
text. Both attribute strata have positive point estimates, with wide intervals
(color CF−original includes zero). Baseline mistakes matching the CF count remain
in the comparison and are not relabeled as intervention effects.

## Interpretation with prior evidence

Stage10A independently established causal influence of emitted counts, including
the20 correctly emitted-fact stratum. Sixteen/24 current queries overlap its primary
panel; its result applies at the same model/aggregate-count regime but is not a
new per-item certificate for every selected query. Stage10A's zero pre→post
necessity contrast remains unchanged. This study authorizes earlier prospective
anchors and a correct-FULL cohort; it does not prove that the old null was caused
solely by a late pre anchor.

Stage4A supplies source A→B→A dependence/re-engagement (36/48 bases in its dynamic
criterion), not a fully identified new-demand trigger/Q-mediated chain. Stage9A.3–5
provide finite-access context; Stage9A.5's null-sink control failed preservation.
This stage uses the unchanged standard masking path and supplies no new null-sink
replication. Conclusions are intervention-specific. The full V_A→T₁→V_B→T₂→V_A
cycle is an integration framework, not a newly measured recurrent cycle here.

The supported claim is a **population-level functional shift in successful,
controlled counting trajectories under the tested access mask and token budget**.
Prefill-derived image information and text-token K/V can remain during image-off;
17/24 already succeed at A0. Explicit text sufficiency is a distinct fresh-run
result. Neither demonstrates that all image information vanished or that textual
reasoning is the unique downstream carrier. Annotation is single main-agent manual
source/text review, not independent human inter-rater validation.

## Resources, artifacts and closure

Allocated GPU time: **0.552778 GPU-hours**, including
model loading, technical validation and all finite workers. Peak concurrency
4/8 authorized GPUs; peak reserved VRAM
8.605GiB. All GPU jobs are terminal and released;
no tmux allocation, keepalive, download, install or follow-on stage. Primary target
<3 GPU-hours and optional target<1 were respected. Slurm terminal snapshots preserve
accounting even after controller record expiry.

Two first optional workers failed a prefix-display assertion after12 completed
runs. The manifest display used pre-snap text without trailing newlines for two
queries; the already-frozen token IDs and tokenized condition text were correct.
A focused CPU diagnostic checked all36 roundtrips. The versioned resume preserved
completed results and ran only12 unfinished rows with unchanged IDs/runtime. Both
failure receipts and allocation time are retained. This was a metadata consistency
repair before affected generation, not a post-outcome anchor/edit change.

All11 requested artifacts are present, with an explicit unused-reserve record.
Four figures have PNG/PDF exports: semantic progression, joint profile, item states,
and conceptual dynamic re-access. Six focused unit tests passed; the separate
artifact audit checks source/receipt hashes, native-prefix identity, clean text
inputs, exact reuse, paired statistics, exports and resource limits. This is a
main-agent arithmetic/provenance audit, not an independent scientific reviewer.

- [Primary inference](stage10ar_primary_inference.json)
- [Transition states](stage10ar_item_transition_states.json)
- [Optional A3 edits](stage10ar_a3_text_edit.json)
- [Resource accounting](stage10ar_resource_accounting.json)
- [Final audit](audit/final_audit.json)
- [Figure1](figures/figure1_semantic_progression.pdf), [Figure2](figures/figure2_phase_transition.pdf),
  [Figure3](figures/figure3_item_transition_states.pdf), [Figure4](figures/figure4_dynamic_reaccess_integration.pdf)

## Exactly one recommendation

Promote phase-structured multimodal reasoning to the main paper framework, scoped
to this functional evidence, and next test whether a new visual demand causally
reopens the perceptual-access regime in a controlled recurrent-demand task.
**Do not launch that next experiment. Stage10AR is complete; STOP.**
