# Block 0 execution protocol v1

Approved scope: `stage8b_block0_compute_once_shared_dataset_plan.md`, user request
2026-09-19. Exactly the existing 256 trajectories; four GPUs on node02 through
the project scheduler and Slurm. No generation, model replay, causal work,
semantic annotation, or outcome-stratified comparison.

## Definitions frozen before constructing outcomes

- Preserve native zero-based token indices and predictive-observation alignment.
  Reasoning comprises complete tokens before the first `</think>` marker,
  using the existing `transfer.reasoning_length`; absent marker means the whole
  generated sequence. Post-think length excludes the delimiter itself and
  includes subsequent generated special tokens, which remain identifiable.
- Normalized position is zero-based `t / reasoning_length`. Phase intervals
  are [0,.25), [.25,.5), [.5,.75), [.75,1]. Episode phase uses its onset;
  middle-review selection uses its midpoint. Boundaries are never rounded.
- Load native R unchanged; verify against the frozen Stage8A model (absolute
  tolerance 1e-12 for batched floating-point evaluation). Tau is exactly
  0.5478025980771918. Preserve all eight native passive features.
- Primary gap=4 means up to four **inactive intervening tokens**, inclusive
  endpoints. A missing R breaks an episode. Cache gap=0 and gap=8 separately.
  Duration includes merged inactive gaps; mean R includes them; AUC is the
  discrete sum of max(R-tau,0). Preceding/following gaps count intervening
  tokens; endpoint gaps with no adjacent episode are null. No boundary gap is
  treated as an inter-episode recurrence.
- Per-trajectory late fractions are episodes whose onset is strictly after
  .25/.5/.75/.9 divided by episode count. No episodes means undefined/null.
  Gap CV uses population standard deviation/mean with at least two gaps.
- Feature vector order: [native R, qk_visual_nonvisual, visual_mass,
  1-visual_entropy]. The last component complements the native max-over-heads
  normalized visual entropy; it does not estimate source-specific attention.
  Native qk_visual_reasoning and all other recorder features are also retained.
- Standardize each dimension using finite reasoning-token values pooled across
  **all 256 trajectories**, population mean/variance, without labels. A constant
  dimension has scale 1. Missing values remain missing with validity masks;
  first-token R is undefined, never zero-imputed.
- Geometry uses float64, both raw and standardized feature spaces, and only
  adjacent pairs with fully finite endpoints. Do not bridge missing tokens.
  Displacement uses first/last fully valid vectors (record their indices).
  Store unnormalized and valid-transition-normalized path length. Tortuosity
  epsilon=1e-12. Angular change is optional and is not computed. Per-phase
  movement uses transitions whose two endpoints belong to that phase.
- Review selection is earliest, nearest midpoint .5 (earlier episode wins a
  tie), and latest; deduplicate in episode order, keep all when <=3. No minimum
  duration/separation constraints. Membership is sealed before outcome join.
- Semantic placeholders are null. ROI feasibility records structural native
  image/patch-map availability; actual target/alternative/value/edit/replay
  feasibility remains explicitly unreviewed when semantic source identification
  is needed. Unknown is never encoded as a negative feasibility result.
- Preserve the 32 previously reviewed outcome records. For new cases use the
  frozen local adapter; freeze automatic extraction and ground-truth-excluded
  manual extraction separately before grading. Unsupported equivalence remains
  unresolved; no external judge. Cap is independent of correctness.
- Completion priority: cap -> capped; otherwise EOS -> normal completed;
  otherwise other abnormal stop. Preserve raw flags/subtype and raw helper label.

## Execution checklist

- [ ] Verify cohort/provenance, focused deterministic tests, source freeze.
- [ ] Freeze extraction provenance and score all 256 with the existing adapter.
- [ ] Four independent Slurm workers validate and construct cached features;
      outcome-blind pooled standardization; GPU geometry; deterministic merge.
- [ ] Verify first samples, observed GPU bindings, progress and measured ETA.
- [ ] Verify all 12 required artifacts, hashes, membership, completion and indices.
- [ ] Release allocation at batch exit; record checkpoint/freeze and report.

Resource estimate before measurement: 4 GPUs, 16 CPUs, 64G host RAM, 2h maximum;
cached-data preprocessing expected to be dominated by reading/hashing native
artifacts and writing tables. Replace this estimate with measured sample rates.
The GPU job terminates after preprocessing; unresolved manual extraction does
not hold GPUs. Input and native source files remain unchanged.
