# Phase 2B: evidence-specific causal pilot

## Current Objective

Run the authorized five-example ROI-attention-knockout feasibility pilot and decide whether evidence-specific temporal crossover warrants later scaling.

## Active Constraints

- Use only frozen examples `699`, `739`, `2799`, `3044`, and `3764`.
- Do not modify Stage 0, Stage 1, or Stage 2A artifacts or annotations.
- Use one A6000 through Slurm on node02, node06, or node07; never node03.
- Apply masks only to generated-query to selected visual-key edges in all language layers during frozen windows.
- Run one-example smoke validation before the five-example pilot; stop the job if smoke fails.
- This action ends after Stage 2B reporting; do not expand the cohort or start another experiment.

## Current State

- Done: Stage 2A passed and issued a conditional Stage 2B handoff with five high-confidence examples.
- In progress: Slurm job `105479` is pending; its gated runner will stop before the five-example pilot if the smoke validation fails.
- Blocked: All currently available A6000 capacity is on forbidden node03; Slurm reports job `105479` pending for priority/resources.
- Most recent useful observation: The submitted job has `ReqNodeList=(null)` and `ExcNodeList=node03`, so Slurm may place it only on node02, node06, or node07.

## Evidence That Matters

| Evidence | Source / Path | Why It Matters | Status |
|---|---|---|---|
| Stage 2A acceptance passed and recommends a five-example causal pilot only | `outputs/stage2a/summaries/stage2a_acceptance.json` | Defines the authorized scope | confirmed |
| Five examples have frozen A/B ROIs and candidate acquisition windows | `outputs/stage2a/evidence_subset/examples/<id>/` | Provides outcome-independent intervention targets | confirmed |
| Existing attention instrumentation covers all 36 language layers under eager attention | `code/visual_reasoning/stage0/attention.py` | Supports an additive-mask intervention without changing model weights | confirmed |
| Installed Transformers eager attention adds `attention_mask` to logits before softmax | `.venv/lib/python3.12/site-packages/transformers/models/qwen3_vl/modeling_qwen3_vl.py` | Establishes the exact intervention seam | confirmed |
| Node03 is explicitly forbidden by the user | current Stage 2B request | Restricts scheduler targets | confirmed |

## Failed Attempts and Lessons

| Attempt | Failure / Symptom | Diagnosis | Lesson | Do Not Repeat |
|---|---|---|---|---|
| Node06-specific first submission attempt | The node06 slot disappeared before launch, so the project scheduler kept the job locally queued | supported by live scheduler status | Submit to Slurm without a nodelist and explicitly exclude node03 | Do not pin the job to a currently full allowed node |

## Open Candidates

| Candidate | Why Plausible | How to Test | Status |
|---|---|---|---|
| Evidence-specific temporal crossover | Stage 2A found descriptive A-to-B focus alignment in the frozen subset | Compare target, wrong-evidence, and irrelevant ROI knockouts in both windows | open |
| General visual fragility | Any large visual mask may disrupt continuation similarly | Compare target effects against within-window irrelevant controls | open |
| Persistent rather than stage-specific evidence dependence | The same ROI may matter in both A and B windows | Compare A-ROI and B-ROI effects across both timings | open |

## Next-Step Decision

- Current bottleneck: The ROI intervention has not yet been technically validated against the installed Qwen3-VL attention and KV-cache generation path.
- Relevant memory item used: Stage 2A provides only five high-confidence examples and explicitly recommends a feasibility pilot rather than expansion.
- Chosen next action: Implement and smoke-test one all-layer additive attention-mask hook, then automatically run the frozen five-example pilot only if all smoke criteria pass.
- Why this action: It is the smallest causal action that directly tests the Stage 2A handoff while preserving target, timing, and control definitions.
- What not to repeat: Do not choose windows, ROIs, controls, or evaluation horizons after inspecting causal outputs.
- Stop condition: Stop after the smoke failure report, or after all five examples and the Stage 2B GO/CONDITIONAL GO/NO-GO report are complete.

### Step Result

- Action taken: Froze the five-example configuration, implemented/tested the all-layer ROI mask and gated runner, and submitted one A6000 Slurm job without a fixed node while excluding node03.
- Result: Job `105479` accepted by Slurm in `PENDING (Priority)` state; smoke and causal results are not available yet.
- Evidence saved: `outputs/stage2b/config/`, `state/gpu_experiment_queue.json`, and `runs/stage2b_a6000_exclude03/slurm.log` (when execution starts).
- Failure or issue: Allowed A6000 nodes are currently full; node03 has free GPUs but is excluded as required.
- Lesson learned: The machine-local scheduler now supports explicit opt-in Slurm-pending submission plus node exclusions, with unit coverage.
- Next implication: When Slurm starts the job, inspect the smoke gate first; proceed to/interpret the five-example pilot only if smoke passes.
