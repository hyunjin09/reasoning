# Phase 6A: Dedicated alignment / mirage / retrieval-dynamics cohort

## Current Objective

The approved Stage6A cohort construction and audited release are complete on 2026-09-09. Stop at the sole GO — Natural Failure Extension recommendation; another research action is not authorized.

## Active Constraints

Stage6A used only the existing four RTX A6000 GPUs in Slurm109385/node03/tmux9. No new allocation or dataset download was requested. Native generation used the frozen BF16 Qwen3-VL-4B-Thinking settings, seed1234, temperature .6, top-p .95, top-k20 and 40,960-token natural-EOS cap. Capped responses were retained without reruns.

Cohort membership, source/template splits, annotation truth/unknowns and the 10-pair C4 atlas remain frozen. Semantic source utterances/refreshes do not establish causal evidence use. A recommendation is not authorization for another research action.

## Current State

The release contains 2,983 events from 1,276 bases: C1 109 bases/1,199 events; C2 31 families/124 events; C3 136 families/660 events; C4 1,000 images/events.

All 109 C1 numeric-source prefixes are reviewed: 1,766 spans and 235 secondary ROIs. The controlled annotation audit passes 1,992 events/160,285 reasoning spans, preserving all 105 baseline claims inside prefixes. Remaining geometry retains explicit unknowns. All C3 responses and the C4 labels/matched controls have the recorded manual reviews.

C1/C2/C3 construction gates pass. C4 has 10 confirmed, 50 unresolved and 940 no-detected whole-trace object-error labels in the fixed 1,000-image sample. The frozen atlas has 10 matched pairs, below the 60-pair minimum. The 1–6% protocol identification range is not a confidence interval.

Physical acquisition saved 3,182 terminal records (20 incomplete) and 13 replay generations, totaling 117.4163 measured device-hours. The primary release has 2,968 natural-EOS traces; terminal capped variants remain in its condition accounting. Device-hours are not elapsed wall time.

Summary and all 18 tables: `outputs/stage6a/summaries/stage6a_cohort_summary.md`. Release, annotation, ROI, manipulation, split, selection and resource audits are complete.

Five C1 intact cap incompletes and the four events of invalid C2 family docvqa56412 remain raw and outside the primary release. Availability gates and native-EOS feasibility are reported separately. There are no pending Stage6A acquisition or annotation tasks.

The full pre-closeout state, including chronology, annotation repairs, test evidence and acquisition checkpoints, is preserved in `outputs/stage6a/audit/workspace_state_before_closeout/phase_6a_dedicated_alignment_mirage_retrieval_dynamics_cohort.md`.

## Evidence That Matters

Paths in this section are relative to `outputs/stage6a/` unless stated otherwise.

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Core datasets reused after ordered lookup; no downloads | `cohort/dataset_inventory.json`, `cohort/download_manifest.json`; `workspace/dataset_inventory.md` | Satisfies machine-local access policy | confirmed |
| Controlled baseline review and C1 eligibility complete | `audit/controlled_baseline_review_completion.json`, `cohort/c1_membership_freeze.json` | Freeze depends on completion/interpretability, not correctness | confirmed |
| C2 series mapping revalidated across all 32 families | `audit/c2_source_mapping_revalidation.json`, `cohort/c2_semantic_release_exclusions.jsonl` | Only docvqa56412 excluded, all four cells together | confirmed |
| C3 five paired present-object conditions reviewed | `audit/c3_paired_native_response_review.json` | Yes counts: intact61, strong50, mask41, sham60, sham_strong61 out of63 | confirmed response frequencies only |
| All 136 C3 unrelated finals reviewed | `audit/c3_unrelated_native_response_review.json` | 133no/3yes; car/pickup and bowl/bucket unresolved; lamp→plant one confirmed object error | confirmed, no causal inference |
| C4 fixed yield and separate atlas complete | `c4_natural_failure/unbiased_prevalence.json`, `matching_diagnostics.json`, `matched_control_review.json` | No more C4 acquisition in Stage6A; atlas size gate unmet | confirmed |
| Exact spans, source claims and temporal roles audited | `audit/controlled_annotation_integrity.json`, `traces/c1_manual_semantic_prefix.jsonl` | Unknown coverage preserved; refresh requires intervening known demand excluding that source | confirmed within stated scope |
| All physical compute stays in one allocation, BF16 | `audit/resource_summary.json`, `native/*/shard_*/environment.json`; `workspace/env_state.md` | Refresh resource totals only after final acquisition | complete; final totals |

Important interpretation limits:

- C1 correct numerals can have wrong geometric roles or wrong finals (D-054).
  Recent counterfactuals:638 AB19/final134.83 correct;707 top8 correct/final200
  wrong;709 height8 correct/final384 wrong. Strong638 binds diagonalz to AB17;
  strong709 explicitly guesses height8 instead of source6. The latter is an
  unsupported reasoning assumption, not a claimed successful visual readout.
- C2 docvqa56412 ROI300 is SalaryContribution, whereas AR names SCNDirect210.
  Correct raw AR answer210 remains correct to its literal prompt; this does not
  rescue the invalid factorial family. Retrieval-only prompts retain semantic
  spatial/ordinal cues; T/X field lengths and wording are not perfectly matched.
- C3 fixed reference disagreements retain local category ambiguity: truck/van,
  cup/glass, chair/stool, mattress/bed; unrelated car/pickup and bowl/bucket.
  Opaque target masks can preserve silhouettes/context; masked yes is not
  automatically hallucination. Translated sham shapes are sometimes described
  as extra silhouettes, despite unchanged target pixels. No-image no plus
  missing-image acknowledgement is distinct from visually verified absence;
  repeated identical questions are shared controls, not independent evidence.
- C4 is a frozen conservative COCO80/CHAIR-compatible presence protocol, not
  unmodified official CHAIR or exhaustive caption accuracy. The 1–6% protocol
  identification range is not a confidence interval or universal hallucination
  bound. Controls contain out-of-scope errors (14352 sink called bathtub;
  208566 Crisco read Riso). Approximate matching and weak pairs are retained.
- Source/template folds group shared images, flagged perceptual matches, source
  documents and declared geometry/task families. C3/C4 shared COCO images stay
  grouped. No unseen generic-task-template or exhaustive historical-template
  claim. Historical Stage5A HMR/HSC evidence remains a separate secondary catalog.

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson / Do Not Repeat |
|---|---|---|---|
| Mechanics v1 | Three C1 sham stimuli overwritten by ROI masks | supported: `audit/asset_collision_diagnostic.json` | Separate `condition__` and `roi_mask__` namespaces; v1 preserved, corrected assets versioned; reuse only hash-validated unchanged conditions |
| C2 initial crop/source review | Numeric ROI correct but AR entity/series mismatched | supported: `audit/c2_series_prompt_roi_mismatch.json` | Full prompt/entity/row-column equivalence required (D-055); exclude entire invalid family without outcome-based replacement |
| Early semantic bookkeeping | Formula mentions treated as prior access; AT→A wrongly called refresh; cross-span claims dropped; unresolved truth aggregated as correct | supported: `audit/semantic_prior_access_diagnostic.json`, `joint_source_refresh_diagnostic.json`, `claim_span_completion_diagnostic.json`, `reviewed_unknown_aggregation_diagnostic.json` | Only reviewed source utterances establish access; per-source temporal history, exact completion-span claim joins, explicit unknowns; regression checks pass |
| Boundary and document parsers | Sentence-final numeric punctuation rejected; document phone parsed as subtraction | supported: `audit/readout_sentence_boundary_diagnostic.json`, `document_arithmetic_comparison_diagnostic.json` | Exact native boundaries; no arithmetic normalization for structured DocVQA fields; manual truth authoritative; 65 focused tests pass |
| Historical exclusion metadata | Three priority phrases parsed as IDs | supported: `audit/historical_exclusion_metadata_diagnostic.json` | Exact numeric prior IDs only; 544 real exclusions and seven secondary artifact references exported without reshuffling |
| C4 one and C1 five baseline responses | 40,960-token cap without EOS | cause unknown; immutable native results | Preserve incompletes and fixed eligibility, no rerun or generation-policy change |
| Draft acceptance reporting | Native EOS substituted for available stress assets in C1/C3 gates | supported: `audit/acceptance_availability_vs_completion_diagnostic.json` | Section53/frozen rules gate validated availability; report EOS feasibility separately. No membership, sampling, acquisition or source-truth change. Diagnostic preceded any C1 stress cap; 67 tests pass |
| C4 fixed 1,000-image yield | Only 10 eligible natural cases, below60 | observed yield confirmed; no general causal diagnosis | Preserve frozen labels, uncertainty and all matches; no ontology/prompt changes or extra samples to chase positives |

## Open Candidates

Sole recommendation: **GO — Natural Failure Extension**. This recommends a separately approved plan; no further acquisition, Stage6B, attention/PCA/causal trajectory analysis or rescue was executed.

There is no authorized open execution task. Preserve the negative natural-case yield and the annotation limits when reviewing a future plan.

## Next-Step Decision

- Completed action: the explicitly approved Stage6A cohort construction, acquisition, annotation, freeze and audited release.
- Decision evidence: controlled gates pass, but the fixed natural sample yields only 10 matched case/control pairs; its 60-pair minimum is unmet.
- Recommendation: GO — Natural Failure Extension; no execution is authorized by this recommendation.
- Stop condition reached: every fixed terminal record, required output, 18 tables and the final acceptance report are saved. No further research action was selected.

### Step Result

The release is complete with controlled gates passing and the natural atlas size gate unmet. The summary is `outputs/stage6a/summaries/stage6a_cohort_summary.md`. No next stage was executed.

The deterministic closeout audit is `outputs/stage6a/audit/workspace_state_closeout.json`. Human-readable templates and the prescribed branch were reviewed before completion; the final exact counts, files, tables and hashes were then checked programmatically.
