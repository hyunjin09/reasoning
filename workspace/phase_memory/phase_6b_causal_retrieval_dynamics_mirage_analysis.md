# Phase 6B: Causal retrieval dynamics and mirage analysis

## Current Objective

Stage6B completed and stopped on 2026-09-10 KST. All 21 technical criteria pass.
Exactly one next-stage recommendation was produced; no next-stage experiment
was started or authorized.

## Active Constraints

- Slurm110860 / node03 / tmux9:1 / pane%20: two A6000 GPUs, four CPUs, 90G RAM.
  No new allocation or CUDA_VISIBLE_DEVICES assignment. Dataset/model data are local.
- Preserve Stage6A membership, splits, truth reviews, capped traces and unknowns.
- BF16; maximum2,048-token generated chunks, fixed cache-release boundaries,
  eight matched single-query barriers; all36layers/32heads source suppression.
- No rescue, training, representation substitution, new head search, sink
  intervention, causal-state surrogate or natural-cohort extension.
- Updated AGENTS.md makes missing optional skills nonblocking; execute the
  approved plan directly. One main agent; no independent reviewer was needed.

## Current State

All phases are complete. C2: 124 events / 31 families. C1 fixed-prefix: 1,199
condition events / 109 bases. Dynamics: 78 exact anchors / 20 bases. C3: 660
events / 136 families. C4: 20 traces / 358 endpoints, including 45 wrong-claim
anchors. Native primary02 completed all 1,199 manifest entries / 14,906 endpoints.
Geometry, sink synthesis, all 24 figure categories, final audits and reporting
are complete. All 24 CPU tests and 59 Python syntax checks pass.

Authoritative outputs: summaries/stage6b_summary.md, stage6b_acceptance.json,
next_stage_recommendation.md, and audit/causal_score_replay.json under
outputs/stage6b. All 21 technical criteria pass; positive scientific gates are
not required for technical acceptance.

## Evidence That Matters

- C2 confirmation focal-demand W2median1.42576,18/19positive,Holmp=.000793;
  W8median1.06250,17/19positive,p=.001099. Disjoint sensitivity14/14positive.
  Alignment attention/QK each14/19positive, below75%, and not Holm-significant.
  High-attention matching yields only1confirmation pair (minimum8). All cells
  need some visual source. Strong dissociation gate FALSE.
- C1 strong/mask sham-controlled VSD medians1.6875/2.71875;57/62 and58/62positive;
  both full grounding gates pass. Counterfactual validation62/62. Nine strict
  held-out candidates across8bases/7sourcegroups, all9alsoW8collapse;4benign and
  5error-associated fixed-prefix candidate preferences. They are not newly
  generated native hallucinations. Broad mirage gate FALSE: continuous attention,
  QK and alphaV divergence fail the full75%positive-base rule.
- Grounding losses pass every leave-one-dataset-out check. Attention divergence
  passes the MathVision subgroup gate (19/21positive,13groups,Holmp=.0281), but
  not MathVerse/MathVista or any leave-one-dataset-out gate. Keep this heterogeneity.
- Dynamics:34primary transitions,0matched holds,19selected refreshes,78anchors.
  Frozen dominance margin=.3125004463, floor=.05. Confirmation selected pairs:
  9demand-aligned switches,7mixed; no strict fixation, no wandering estimate.
  One semantic-only diagnostic found181valid numeric anchors,69transition and
  4hold intervals before sampling/matching. Aggregate multi-source spans do not
  resolve a strict single-source subgoal. No numeric assay establishes causation
  of a geometric-role error. Selected refreshes:15observed successes,4unresolved.
  First observed dominance is not acquisition time; censoring is not failure.
- C3 confirmation:4mirage-like candidates (3answers differ from both references),
  but no robust aggregate grounding/divergence replication. Strong/mask VSD
  contrasts positive25/41, with mean CIs crossing zero. One absent-reference yes,
  pope_204100_chair, is already UNRESOLVED_CATEGORY_BOUNDARY (stools/chairs).
  Neither tested distractor shows the joint error-promoting direction. Do not
  count this as confirmed objective hallucination; mask+yes is not automatic error.
- C4: among5confirmation pairs, visual-mass/sink/entropy directions match the
  controlled discovery descriptor in1/5,2/5,3/5pairs. All mean-effect CIs cross
  zero. Passive descriptors and wrong-claim next-token probabilities do not
  provide missing exact causal source states. No natural extension is selected.

- Native/PCA: 666 manual intact discovery endpoints / 47 bases / nine source
  groups fit the fixed 11-dimensional normalization and PCA. PC1/PC2 explain
  36.06% / 19.61%. All 1,100 manual confirmation endpoints are projection-only.
  Across all native conditions, 12,868 endpoints project and 2,038 lack required
  visual components. The 292 zero-endpoint traces and 125,216 unresolved,
  unreviewed spans remain explicit. No causal state is imputed. No dense endpoint
  coincides with an exact scored candidate readout under the same native prefix;
  the 78 exact anchors retain their measured native candidate margins separately.
- Sink: strict confirmation candidates have lower sink mass than intact across
  eight bases / seven source groups: mean -0.08421, CI[-0.11477,-0.04709]. After
  the declared generic-attention control: mean -0.06283, CI[-0.08831,-0.03163].
  These selected-case passive associations do not identify mediation or a causal
  behavioral prediction. The future-sink gate remains closed.

## Failed Attempts and Lessons

| Attempt | Direct observation / diagnosis | Selected repair / evidence |
|---|---|---|
| Optional skill preflight |Old AGENTS required unavailable research-control |Updated AGENTS explicitly resolves blocker; policy_resolution.json |
| c1_mechanics_01 |Text-only prefill returned rope_deltas=None; image controls passed |Stage6Bidentity-offset adapter independently matches native implicit positions; c1_mechanics_02PASS |
| native_primary_01 |CUDA OOM in a long partial chunk with duplicate GPU caches |Inactive checkpoint moved to host RAM; original code/results preserved |
| native_residency_mechanics_01 |Second OOM in a full2048chunk with one long GPU cache |Stopped local retries; one focused two-device allocator diagnostic |
| native_allocator_diagnostic_01 |Default fails at38912tokens with11.37GBinactive splits; expandable reaches40905, zero inactive splits;18common logits exact |Supported fragmentation diagnosis; expandable segments fixed before mechanics02 |
| native_residency_mechanics_02 |10long-context endpoints on both GPUs match fresh canonical roots and every cached layer |PASS; maximum reused prefix38912; full native restart authorized by this repair |

Historical kernels and the original dense worker remain unchanged. The failed
v2 worker source is preserved with its recorded hash in audit/failed_worker_versions/.
Evidence: native_dense_oom_repair_decision.json, native_allocator_diagnostic.json,
native_dense_residency_mechanics.json and original runs/stage6b logs.

Early Matplotlib imports may have used the default external cache. No forbidden
cache was inspected or cleaned; all subsequent plotting explicitly sets the
project cache. A final check also confirmed that pytest updated the project-root
cache, outside the allowed write list. Its node IDs were verified read-only;
the existing cache was not moved or cleaned. Future test commands explicitly use
outputs/stage6b/audit/pytest_cache. See audit/cache_configuration.json.
No dataset was downloaded.

## Open Candidates

Only one future action is recommended: **GO — Cohort/Assay Repair**. The primary
dynamic panel lacks matched holds and an explicit geometric-error contrast.
Rescue lacks 24 qualified native error-linked confirmation events and a matched
intervention/control prediction. C2 does not establish its strong dissociation
gate. Controlled signatures are too weak for natural sample size to be the main
remaining gap. A mixed C1/C2 result alone does not justify repairing a valid assay.

## Next-Step Decision

- Completed action: execute the full approved Stage6B plan, finish native
  primary02, geometry, sink, figures, audits, synthesis and state updates.
- Decision: STOP. The recommendation is not authorization to execute Stage6C
  or any other next-stage work. Await the user's next instruction.
- Preserve the existing cohorts, splits, negative evidence and frozen rules.
  Already inspected traces can support repair; subsequent confirmation must
  remain independent of repair decisions and tuning.
- Relevant lessons: D049/D051 matched paths; D053 necessity versus acquisition;
  D054 error-oriented readouts; D055 prompt/source equivalence; D056 yield versus
  evidence; D057 joint readout and matched-hold eligibility.

## Step Result

C2 mechanics/primary replay: 40 arms; C1 fixed: 36; dynamics: 29; C3: 24.
Native primary02 exactly matches all 100 initial mechanics endpoints and all
10 repaired long-context controls. The allocator diagnostic matched 18 common
prefix logits. All native/no-op/passive checks pass. Twenty GPU job records
remain: 17 succeeded, three failed attempts preserved. Maximum observed allocated
GPU memory across runs was 39.19 GiB; no new allocation or dataset download.

The full primary native manifest, worker/runtime hashes, Stage6A release and
splits are preserved. Technical acceptance is 21/21 PASS. The stage produced
one Cohort/Assay Repair recommendation and stopped. Historical state checkpoints
remain under audit/state_checkpoint_backups/.
