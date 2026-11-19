# Stage10A — causal perceptual-to-textual handoff

Completed / STOP at 2026-09-27T10:42:57.654662+00:00. **Outcome C: causal text influence, without a demonstrated perceptual handoff or phase termination.**

Changing the emitted count redirects13/24 fresh image-free continuations toward the edited value, compared with0/24 original and sham continuations. Text-only sufficiency improves, but visual-access necessity does not decrease across the frozen anchors. Thus the full handoff claim fails, regardless of the downstream2×2 result.

## Frozen design and execution

Reuse all32 source images and64 native Stage9A.5 FULL traces unchanged. Gold-free semantic review sealed32 eligible events; deterministic hash selection retained24 independent images (12 color/12 shape) and8 reserve. First explicit count, pre/emit/post anchors and analysis rules were frozen before interventions. Correctness did not select the primary cohort; 20/24 emitted facts are source-correct. The20 correct-fact stratum is reported separately.

Qwen3-VL-4B-Thinking revision1de27d8c51f12e819435303b9e84c4e25ba8401e; BF16, TF32 off, greedy, native Thinking template/DeepStack,512 total generated tokens including replayed prefix. Fresh text-only replay copies no image/cache/hidden state. Image-off preserves the original prefix/cache and masks future generated-query→image-key access in all36 decoder layers, beginning with the correct first future query. All24 native prefixes match saved tokens.

Gate A:144 continuations. Gate B:96 logical conditions,72 new and24 exact original reuses. Post2×2:48 new continuations on12 correct-fact/no-option-binding images (six per attribute), selected without intervention-effect ranking. Total:288 logical rows,264 unique new scientific continuations. Independent unit=image; equal weight;4,000 paired bootstrap draws, seed920260927. All intervals below are95% percentile intervals.

## Sufficiency and necessity

| Anchor | Text-only correct | Image-off correct | Text-only no final | Image-off no final |
|---|---:|---:|---:|---:|
| pre | 16/24 | 20/24 | 3/24 | 1/24 |
| emit | 19/24 | 20/24 | 1/24 | 0/24 |
| post | 20/24 | 20/24 | 0/24 | 0/24 |

Selected native FULL accuracy:20/24. **H2 post−pre: 16.67 [4.17, 33.33] percentage points. H1 necessity decrease: 0.00 [0.00, 0.00] percentage points.** Gate A opens via H2 alone under the frozen "if neither" rule. H1 is unsupported.

The four H2 gains comprise 2 cases improving from a missing pre final and 2 from a valid wrong pre final. This is bounded final-answer performance, not a pure local visual-read accuracy measure. Excluding the10 post anchors with option binding leaves14 images: H2 14.29 [0.00, 35.71]pp. Color H2 8.33 [0.00, 25.00]pp; shape H2 25.00 [0.00, 50.00]pp. The descriptive subgroup intervals do not establish an attribute difference.

Pre-text already contains object inventories, and image-off retains prior image-derived state. Zero necessity decrease therefore does not rule out an earlier or latent transfer. No anchor was moved after this result.

## Emission-anchor text causality

Original is an exact reuse. Counterfactual changes only the selected count to the next valid1–5 value. Deletion removes that fact clause; sham preserves its meaning. Earlier inventories/arithmetic remain unchanged, even when they contradict the changed count. Singleton edits include documented grammatical agreement.

| Condition | Follow original count | Follow edited count | Source-correct | No final |
|---|---:|---:|---:|---:|
| original | 23 | 0 | 19 | 1 |
| counterfactual | 2 | 13 | 3 | 8 |
| delete | 18 | 3 | 15 | 3 |
| sham | 23 | 0 | 19 | 1 |

Signed semantic score: +1 for the edited count, −1 for the original emitted count,0 for other/missing answers. These contrasts are **score units, not accuracy percentage points**:

- CF−original: 1.42 [1.12, 1.67].
- CF−sham: 1.42 [1.12, 1.67].
- CF−delete: 1.08 [0.62, 1.50].
- Delete−sham source accuracy: -16.67 [-33.33, -4.17]pp.

Both directional thresholds, perturbation-noise contrast, deletion criterion and attribute-direction checks pass. Correct-fact stratum (20 images), CF−sham: 1.45 [1.10, 1.75]. Color: 1.75 [1.33, 2.00]; shape: 1.08 [0.75, 1.42]. H3 and Gate B pass. Eight CF outputs fail to close reasoning at512; actual13/24 edited-count answers establish directional following separately from that completion loss. No scratchpad candidate was promoted into the final channel and no cap was increased.

## Post-anchor image × text dominance

Fresh multimodal caches are recomputed consistently for all four conditions. I1 changes one source object's asked attribute, and T1 edits only the first selected fact. Later native recounts retain their original values. All original rerenders are pixel-identical. Twelve sources and48 conditions were frozen before2×2 science. A pre-science geometry review corrected image007's square-orientation candidate; v1 images/manifests and the unchanged-runtime technical checks remain preserved, with v2 linkage recorded.

| Condition | Follow original count | Follow edited count | Correct for current image | No final |
|---|---:|---:|---:|---:|
| I0T0 | 12 | 0 | 12 | 0 |
| I1T0 | 9 | 2 | 2 | 0 |
| I0T1 | 11 | 0 | 11 | 1 |
| I1T1 | 2 | 8 | 8 | 2 |

Factorial average text effect: **0.58 [0.33, 0.83]**. Image effect: **0.92 [0.54, 1.29]**. Text−image: **-0.33 [-0.83, 0.08]**. Frozen post-text-dominance criterion: **NOT SUPPORTED**. Later unchanged recounts limit this to the selected first fact within the post prefix; it does not compare all textual carriers jointly against vision.

No pre2×2 was run because the selected fact did not yet exist in pre text. No dominance reversal is measured. No downstream log-prob assay was collected; the selected primary answer-following endpoint and deletion/sham controls are complete.

## Validation, resources and stop

Sixteen focused CPU tests pass. Eight actual-model Gate-A validation cases pass after one text-processor schema repair; two disjoint image+prefix cases exactly match cached native continuations. The geometry repair reuses these technical results because runtime and technical inputs are unchanged. Raw final-answer review was sealed before joining source gold; 21 logical ambiguous/unclosed outputs received manual decisions. Literal/raw extraction sensitivities are retained in inference JSON. The independent audit checks coverage, all source and receipt hashes, paired arithmetic/bootstrap, image-free versus cached state semantics, and native final-channel scoring.

Actual Slurm allocation: **0.402 GPU-hours**, including technical work, one failed preflight, hashing/loading and workers that found no remaining bundles; continuation generation 0.193 GPU-hours. Peak concurrent GPUs:8, authorized ceiling8. All GPU jobs are terminal and resources released. Source annotations:32 native events,24 text edits,12 source edits; human/agent annotation wall time was not timed. No new dataset/model download.

The8-image precision reserve and MathVision bridge were **not run**: H1 is zero, so their gates fail. No CoT comparison, Stage10B, new anchor, new fact search, cap rescue or next experiment was launched.

**One recommendation:** Retain causal text-carrier influence as a bounded result alongside native visual-use findings; do not promote a perceptual-to-textual phase-handoff claim.

## Evidence and figures

- [Primary inference](stage10a_primary_inference.json), [resource accounting](stage10a_resource_accounting.json), [event selection](stage10a_event_selection.json).
- [Gate A](audit/gate_a_inference.json), [Gate B](audit/gate_b_inference.json), [post2×2](audit/dominance_v2_inference.json), [source repair](audit/source_geometry_repair.json).
- [Independent final audit](audit/final_validation.json); all11 requested artifacts are present, with explicit optional-not-run records.
- [Figure1: tested pathway](figures/figure1_handoff_schematic.png); [Figure2: necessity/sufficiency](figures/figure2_necessity_sufficiency.png); [Figure3: text control](figures/figure3_counterfactual_text_control.png); [Figure4: post dominance](figures/figure4_image_text_dominance.png). PDF companions are included.
