# Phase 3C.10: Reasoning-state retrieval trigger

## Current Objective

Complete the user-approved retrieval-trigger plan, assess its causal contribution,
produce one recommendation, and stop. Objective achieved; no follow-on started.

## Active Constraints

- Exact historical31 bases,7/24 split, M/T states, A/B layers and causal heads.
- Canonical A6000 BF16 cached path, <=2048 chunks, shared arm partitions.
- Used only tmux 9 / Slurm 108548 / node07 / four A6000 GPUs; no new requests.
- No sink intervention, new cohort, wider-history search or Stage 4 execution.

## Current State

- Done: frozen historical inputs;45 focused/new and inherited tests passed.
- Done:15/15 mechanics across7 bases,28 state files and517 arms. Native/no-op,
  replay, self-Q and inherited cached T0 are exact; all past K/V unchanged.
- Done:96 primary state files on 24 bases frozen before gates. Both targets pass
  all five trigger-gate contrasts and R16-versus-Q after per-target Holm.
- Done: temporal, layers, all-/selected-head Q rescue, gated h_pre, and763
  permitted last 8 position effects;16 figures, independent audits and report.
- In progress: none; completed and stopped for review.
- Blocked: none. Local research-control skill absent; explicit plan governed
  this bounded action. No new research action was autonomously selected.
- Most recent useful observation: recent input affects target VSD at T, but late
  native Q restores routing only; h_pre also fails robust VSD rescue.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Both target trigger gates pass | `outputs/stage3c10/phase_b_primary/primary_statistics.json` | New upstream recent-input/VSD link | confirmed |
| A/B median TE_VSD .793223/.651588; positive20/24 and24/24 | same primary statistics | Behavioral evidence beyond routing | confirmed |
| M/E16/I/Q comparisons pass | same primary statistics | Retrieval-specific controls | confirmed |
| k80=16 both; only layers 16–23 robust | `outputs/stage3c10/phase_c_temporal/k80.json`, `phase_d_layers/layer_profile.json` | Broader tested recent influence than1–2-token carriage | confirmed, threshold-qualified |
| Q restores RDS exactly24/24 both, VSD nonrobust | `outputs/stage3c10/phase_e_mediation/mediation_statistics.json` | O1/M2; stronger O2 not supported | confirmed |
| h_pre VSD nonrobust both | `outputs/stage3c10/phase_e_mediation/hpre_statistics.json` | No clean late broad-state rescue | confirmed |
|21 artifact+4 crosschecks,45 tests,20/20 acceptance | `outputs/stage3c10/audit/`, `summaries/stage3c10_acceptance.json` | Same-path and inference validity | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| All-head Q behavioral mediation | Median VSD gain A-.000843/B.046476;12/24 and13/24 positive | cause unknown; exact routing and recipient-K/V checks pass | Routing rescue does not identify behavioral mediation | No broader Q search without approved plan |
| Optional late h_pre | A median-.224981; B.067817, neither robust positive | cause unknown; exact copy audit passes | Native h_pre can include upstream visual evidence; VSD is not a guaranteed upper bound | Do not call this clean broad-state rescue |
| Prior3C.9 mixed paths | Sham/source effects moved | supported | Compare every arm on one partition | No legacy denominators |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Recent reasoning trigger | Full frozen specificity gate passed both targets | Completed R16/M/E16/I/Q assay | supported within assay |
| Late Q as behavioral mediator | Natural/causal routing geometry | Completed same-state Q rescue | not supported by VSD rescue |
| Earlier/multiple/distributed state paths | Late rescue insufficiency and previous redundancy | Requires separately reviewed plan | unresolved; no new test chosen |
| Multi-evidence generality | Local causal links established; broader paper relevance | Separately approve Stage 4 plan | sole recommendation, not started |

## Next-Step Decision

- Current bottleneck: behavioral mediation of recent-input effect and generality
  beyond one frozen local evidence contrast remain unresolved.
- Relevant memory item used: D-051 same-path control lesson; prior routing/behavior
  dissociation plus current exact Q routing/nonrobust VSD rescue.
- Chosen next action: none. Sole recommendation **GO — Stage 4 Multi-Evidence
  Retrieval/Refresh**, review only. No implementation or execution authorized.
- Why stop: all prescribed Stage 3C.10 phases and conditional h_pre gate complete;
  another local mediator/sink search is not automatically warranted.
- What not to repeat: no O2 claim, unique 16-token span claim, historical-four-head
  exclusivity, mixed-path controls, or treating generic computation as untouched.
- Stop condition: satisfied; full report,20/20 acceptance,16 figures and one recommendation.

### Step Result

- Action taken: complete bounded Stage 3C.10 with existing four GPUs.
- Result: O1 — Reasoning-State Retrieval Trigger and M2 — Routing mediation only,
  both A/B. All primary controls pass. k80=16 near80% cutoff; layer16–23 robust.
- Evidence saved: `outputs/stage3c10/summaries/stage3c10_summary.md` and raw phases.
- Failure or issue: scientific Q/h_pre mediation nulls preserved; no mechanical
  experiment failure. Report formatter fixed without rerunning scientific scores.
- Lesson learned: recent-input/VSD control can coexist with exact late-Q routing
  rescue and failed behavioral rescue; do not conflate the two causal links.
- Next implication: review one Stage 4 recommendation; mediator remains unknown.
