# Phase 3C.1: Causally Anchored Retrieval-Attention Phenotype

## Current Objective

Execute the user-approved Stage 3C.1 measurement action: characterize QK routing, attention probability, Value influx, post-`W_O` residual contribution, source-mass allocation, and candidate sink behavior at the two previously causal-localized late-W4 retrieval targets, then issue exactly one review-only recommendation and stop.

## Active Constraints

- Preserve all Stage 0--3B.9 artifacts unchanged.
- Reuse exactly Target A `E_d/W4/layer29/heads=[11,6,15,12]` and Target B `E_d-1/W4/layer28/heads=[16,0,3,6]`.
- Reuse the exact historical 37-base paired-semantic numeric cohort and Stage 3B.7-R target/complement/irrelevant ROI mappings.
- Freeze the primary temporal grid at `E_d-16,-8,-4,-2,-1,0`; do not add `E_d+1`.
- Freeze matched-size noncausal controls by an attention-independent rule: the lowest logical query-head indices not in the corresponding causal set, giving Target A `[0,1,2,3]` and Target B `[1,2,4,5]`.
- Keep `E_d/W5` as an upstream-state control and `E_d-1/W5/head_10` as a secondary comparator only.
- Do not select any ROI, head, layer, time, example, or distractor from Stage 3C.1 attention values.
- Do not manipulate attention, queries, keys, routing, or source states.
- Use both A5000s in the existing Slurm allocation `106936` through tmux session `8`; submit no new job and do not terminate the allocation.
- Use `base_problem_id` as the statistical unit and keep causal-effect triangulation post-extraction and descriptive.
- Stop before Stage 3C.2, Stage 4, failure analysis, or any causal routing/sink intervention.

## Current State

- Done: Stage 3B.9 completed with 20/20 technical PASS and shared moderate-dimensional late Value geometry at rank 24/16.
- Done: `plan/stage3c1_plan.md`, machine-local access/GPU policy, environment state, Phase 3B.9 handoff, and promoted decisions were reviewed.
- Done: the existing node04 A5000x2 allocation and tmux session `8` were verified alive and idle for Stage 3C.1.
- Done: the project-local `research-control` skill remains absent; this explicit user-approved plan is the sole bounded action and `AGENTS.md` supplies the fallback discipline.
- Done: the exact full-shape eager-Attention smoke gate passed with zero probability/head-output reconstruction error, zero instrumentation logit drift, and bitwise-exact repeat extraction.
- Done: the frozen 37-base, four-condition cohort was extracted on both A5000s in allocation `106936`/tmux `8`; 14,820 per-head rows and 444 raw tensor archives were persisted.
- Done: temporal, ROI-selectivity, QK, competition, entropy, alpha-V, post-`W_O`, source-mass, candidate-sink, per-head, and prior-causal-effect analyses were completed.
- Done: Stage 3C.1 passes 20/20 acceptance criteria; the independent persisted-artifact audit passes 8/8 aggregate checks.
- Done: exactly one review-only recommendation was written, and execution stopped before Stage 3C.2 or Stage 4.
- Blocked: none.
- Most recent useful observation: prior causal experiments localize evidence transport to exact edited visual ROIs through Value content in small late-W4 head ensembles, while raw attention remained an unreliable standalone proxy.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Exact causal ROI and Value-dominant targets | `outputs/stage3b7r/analysis/roi_path_statistics.json`; `outputs/stage3b7r/analysis/kv_decomposition_statistics.json` | Anchors attention phenotype to independently causal-localized retrieval | confirmed |
| Frozen target heads and W5 control | `outputs/stage3b6/analysis/head_restoration_statistics.json`; `outputs/stage3b6/analysis/upstream_control_statistics.json` | Defines primary and comparator cells without Stage 3C.1 attention selection | confirmed |
| Exact v3 Value endpoint mechanics | `outputs/stage3b8/audit/reconstruction_validation.json` | Supplies validated tensor conventions and reconstruction precedent | confirmed |
| Stage 3B.9 moderate shared geometry | `outputs/stage3b9/summaries/stage3b9_acceptance.json` | Completes the single-evidence causal handoff but does not define attention phenotype | confirmed |
| Exact Stage 3C.1 instrumentation | `outputs/stage3c1/audit/reconstruction_check.json`; `outputs/stage3c1/audit/instrumentation_faithfulness.json` | Establishes exact eager reconstruction and non-invasive capture | confirmed |
| Frozen 37-base phenotype extraction | `outputs/stage3c1/analysis/full_extraction_validation.json` | Validates cohort, conditions, row counts, numerical closure, and no manipulation | confirmed |
| High-attention ROI-selective phenotype | `outputs/stage3c1/analysis/roi_selectivity_statistics.json`; `outputs/stage3c1/analysis/retrieval_time_contrasts.json` | Shows strong target-vs-irrelevant selectivity and time-local QK sharpening at prior causal coordinates | confirmed/descriptive |
| Independent final artifact audit | `outputs/stage3c1/summaries/artifact_validation.json` | Verifies required tables, raw tensors, figures, acceptance, and stop boundary | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Stage 2 attention-only localization | Mention-centered and heterogeneous ROI attention | supported by Stage 2C timing audit | Attention is descriptive unless anchored to independent causal evidence | Do not label high-attention positions as causal retrieval |
| Stage 3B.8 v1/v2 endpoint | Numerical mismatch from reduction/BF16 round trip | supported | Reuse exact eager tensors and direct reconstruction conventions | Do not use approximate ROI reduction or subtract/add endpoint reconstruction |
| Stage 3C.1 smoke v1 | Source-class alias mismatch (`visual` vs `all_visual`) | supported by `runs/stage3c1_tmux/smoke.log` | Validate frozen naming at the extraction boundary | Do not launch cohort extraction before smoke schema validation |
| Stage 3C.1 smoke v2 | Row-only recomputation changed BF16 GEMM/softmax reduction shape | supported by `runs/stage3c1_tmux/smoke_v2.log` and exact v3 result | Numerical faithfulness requires recomputing the installed full tensor shape | Do not treat a mathematically equivalent row-shaped recomputation as numerically exact |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Relevant-vs-distractor routing causality | Both frozen targets show strong ROI-selective, time-local routing, but attention-to-causal-effect coupling differs across targets | Future controlled rerouting with Value content and non-target paths fixed | review-only; not authorized |
| Candidate sink causality | `<|im_start|>` has persistent high mass, but usefulness is unknown | A separately preregistered causal control would be required | descriptive only; not recommended as the next action |

## Next-Step Decision

- Current bottleneck: no technical bottleneck remains; the project is waiting for review of Stage 3C.1 before any next experiment is authorized.
- Relevant memory item used: the target-A/target-B split in attention-to-causal-effect correlation and head-6 heterogeneity prevent treating raw attention magnitude as a universal causal proxy.
- Chosen next action: stop. Preserve **GO — Relevant-vs-distractor routing causality** as the sole review-only recommendation.
- Why this action: the approved Stage 3C.1 measurement is complete, while the proposed next question is causal and requires a separate prospective plan.
- What not to repeat: do not infer causal routing from the descriptive phenotype or promote the candidate sink into an intervention target from mass alone.
- Stop condition: met with 20/20 acceptance, 14 required figures, and one recommendation.

### Step Result

- Action taken: exact passive attention/QK/Value/`W_O` extraction and frozen cohort analysis at two previously causal-localized W4 targets.
- Result: technical PASS 20/20. Target ROI density exceeded irrelevant density in 36/37 bases for A and 37/37 for B, with retrieval-time QK cosine/logit sharpening and substantial alpha-V/post-`W_O` contributions.
- Evidence saved: `outputs/stage3c1/` including exact audits, 14,820-row metric tables, 444 raw tensors, control tables, statistics, 17 figures, summary, acceptance, and independent artifact validation.
- Failure or issue: two pre-cohort smoke attempts were rejected and preserved; the final full-shape method passed exactly. Natural attention correlates with prior causal effect for A but not B, and B head 6 has near-zero ROI attention despite causal ensemble membership.
- Lesson learned: causally anchored retrieval can have a clear ROI-selective routing phenotype, but attention magnitude remains head- and target-dependent rather than a universal causal score.
- Next implication: review the sole routing-causality recommendation; no next experiment has been started.
