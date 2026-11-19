# Phase 3C.3: Relevant-vs-Distractor Routing Causality

## Current Objective

Execute the user-approved `plan/stage3c3_plan.md` as one bounded causal action: test whether selected-head query routing controls target-ROI Value influx and evidence preference, run current-position `h_pre` patching only if the frozen Phase-A gate passes, write exactly one review-only recommendation, and stop.

## Active Constraints

- Preserve Stage 0--3C.2 artifacts unchanged.
- Reuse the exact Stage 3C.2 T/M/I definitions, Target A/B layers and causal/noncausal heads.
- Select validation/primary cohorts and M/R states without Stage 3C.3 outcomes or attention.
- Use seven disjoint validation bases and the remaining 24 bases as the primary statistical cohort.
- Compare direct post-RoPE query substitution with donor content-space Q under recipient-position RoPE; select by mechanics, not effect magnitude.
- Keep all visual and nonvisual K/V recipient-native during Phase A.
- Gate Phase B prospectively; do not use `h_pre` or optional alpha interventions to rescue a failed query result.
- Observe candidate-sink quantities only; never manipulate sink mass.
- Do not start Stage 3C.4, Stage 4, multi-evidence refresh, or failure analysis.

## Current State

- Done: Stage 3C.2 completed with 20/20 technical PASS and 12/12 independent artifact checks.
- Done: the Stage 3C.3 plan, access/GPU policy, environment, prior phase memory, and promoted lessons were reviewed.
- Done: the project-local `research-control` skill is absent; the explicit plan and repository rules govern this action.
- Done: seven disjoint validation bases and 24 primary bases were frozen without attention or Stage 3C.3 outcomes.
- Done: both RoPE formulations passed mechanics; `content_recipient_rope` was frozen before primary scoring by the prospective mechanics-only rule.
- Done: all 24 primary bases completed with exact self, recipient-K/V, and non-target-head controls.
- Done: query substitution changed routing and target alpha-V bidirectionally on 24/24 bases for both targets, but neither target passed reciprocal evidence-preference requirements.
- Done: Phase B and optional alpha intervention were not run because the frozen Phase-A gate failed.
- Done: 21/21 independent artifact checks passed; the sole recommendation is `REDIRECT — Routing Intervention Not Behavioral`.
- Blocked: none.
- Most recent useful observation: routing redistribution is causally controllable at the selected query heads, but this did not yield reciprocal evidence-specific behavioral control.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Frozen T/M/I and state pairs | `outputs/stage3c2/annotations/`; `outputs/stage3c2/cohort/primary_dissociation_manifest.jsonl` | Defines an attention-blind intervention cohort and donor/recipient states | confirmed |
| Frozen causal/noncausal heads | `outputs/stage3c2/config/frozen_targets.json`; `outputs/stage3c2/config/stage3c2_config.json` | Prevents Stage 3C.3 outcome-based target selection | confirmed |
| Exact eager reconstruction | `outputs/stage3c2/audit/attention_reconstruction_audit.json` | Supplies the validated full-shape attention path | confirmed |
| ROI-local Value transport | `outputs/stage3b7r/analysis/roi_path_statistics.json`; `outputs/stage3b7r/analysis/kv_decomposition_statistics.json` | Establishes T as independently causal and Value-dominant | confirmed |
| Query-form validation | `outputs/stage3c3/validation/validation_summary.json`; `outputs/stage3c3/audit/` | Both forms exact; content/recipient-RoPE form frozen before primary | confirmed |
| Phase-A primary result | `outputs/stage3c3/analysis/query_causality_statistics.json`; `outputs/stage3c3/phase_a_query/phase_a_gate.json` | Large reciprocal routing/alpha-V effects but failed reciprocal evidence gate | confirmed |
| Independent validation | `outputs/stage3c3/summaries/artifact_validation.json` | Recomputes cohort, mechanics, metrics, stop boundary, and 14 figures | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Stage 3C.2 descriptive routing | Natural QK/attention covaried with retrieval | supported as description only | Q must be intervened on while K/V stay recipient-native | Do not infer causal routing from attention |
| Stage 3C.1 row-only reconstruction | BF16 drift from a changed tensor shape | supported | Preserve the installed full tensor shape | Do not use row-shaped recomputation |
| Stage 3C.3 smoke v1 | Routing summary compared a causal attention row with unsliced future suffix K/V | supported by traceback and tensor layout | Slice stored K/V to the row's causally visible source width for routing summaries | Do not equate stored full-sequence K/V width with current-row visibility |
| Stage 3C.3 smoke v2 | Prefix-only donor capture and full-candidate scoring used different BF16 matrix shapes, making self patch nontransparent | supported by nonzero self shifts and large K/V deltas | Capture donor and recipient states in the exact candidate-scoring pass; all captured states remain before the suffix | Do not compare low-precision states across different full tensor shapes when exact self is required |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Query-mediated routing | Query substitution caused 24/24 expected-direction RDS and alpha-V shifts | Reciprocal selected-head Q_M/Q_R substitution | supported for routing/Value influx only |
| Broader state control | Evidence preference may depend on state beyond selected Q heads | Would require a separately approved design; gated h_pre was prohibited here after Phase-A failure | unresolved |
| Routing without evidence control | Neither target passed reciprocal evidence-preference requirements despite strong routing effects | Joint routing/Value/evidence chain | supported under the tested intervention |

## Next-Step Decision

- Current bottleneck: Stage 3C.3 is complete; the unresolved question is why strong selected-head routing/Value changes fail to control evidence preference reciprocally.
- Relevant memory item used: causal intermediate readouts do not by themselves establish behavioral evidence control.
- Chosen next action: stop and return `REDIRECT — Routing Intervention Not Behavioral` for review.
- Why this action: both targets failed the frozen Phase-A evidence gate, so Phase B and alpha manipulation cannot be used as rescue analyses.
- What not to repeat: do not reinterpret 24/24 RDS/alpha-V directionality as a complete reasoning-to-evidence causal chain.
- Stop condition: met; no Stage 3C.4, Stage 4, multi-evidence, failure, h_pre, alpha, or sink intervention was started.

### Step Result

- Action taken: completed the frozen validation and 24-base primary selected-head query intervention.
- Result: technical PASS / scientific-gate FAIL. Target A evidence medians were -0.00113 necessity and +0.00282 sufficiency; Target B was +0.11865 necessity and -0.00579 sufficiency. Both targets had 24/24 expected RDS and alpha-V directions, exact self controls, and positive causal-minus-noncausal median RDS effects.
- Evidence saved: `outputs/stage3c3/phase_a_query/`, `outputs/stage3c3/analysis/`, `outputs/stage3c3/audit/`, and `outputs/stage3c3/summaries/`.
- Failure or issue: reciprocal evidence preference was absent at both targets; cause remains unknown.
- Lesson learned: selected causal-head queries can control where attention and Value influx are allocated without establishing control of the downstream evidence decision.
- Next implication: stop under the plan's R4 outcome and review the REDIRECT recommendation before authorizing any follow-up.
